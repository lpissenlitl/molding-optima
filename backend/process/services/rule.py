"""
molding-optima 规则管理 service

提供 RuleKeyword / RuleLibrary / RuleMethod / ExpertRule 的 CRUD + 列表查询。
RuleFlowDoc（MongoDB 流程图）相关功能暂不引入。
"""
import logging
import re

from django.db import transaction, models as db_models

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_DATA_FOUND, ERROR_ILLEGAL_ARGUMENT, ERROR_ACCESS_LIMIT
from process.models import RuleKeyword, RuleLibrary, RuleMethod, ExpertRule
from utils.db import paginate_queryset, parse_ordering

_logger = logging.getLogger(__name__)


# ============================================================================
# RuleMethod 缺陷识别辅助
# ============================================================================

# 匹配规则描述中的前置条件 token
# token 形如：kw=10 / kw>5 / kw<3 / kw>=8 / kw<=2 / kw!=0
_PRECOND_TOKEN_RE = re.compile(
    r'^([A-Za-z_][A-Za-z0-9_]*?)(>=|<=|>|<|=|!=)(.+)$'
)


def _extract_precondition_keywords(rule_description: str) -> list:
    """从规则描述字符串中提取所有前置条件的 keyword_name

    规则描述格式：
        IF kw1 op1 v1 AND kw2 op2 v2 THEN ...

    返回：['kw1', 'kw2', ...]
    """
    if not rule_description:
        return []
    m = re.search(r'\bIF\s+(.+?)\s+THEN\b', rule_description, re.IGNORECASE)
    if not m:
        return []
    cond_part = m.group(1)
    keywords = []
    for token in cond_part.split(' AND '):
        token = token.strip()
        m_kw = _PRECOND_TOKEN_RE.match(token)
        if m_kw:
            keywords.append(m_kw.group(1))
    return keywords


def _auto_extract_defect(rule_description: str, company_id: int):
    """从规则描述中自动识别缺陷关键词

    业务说明：
      defect_label / defect_code 是索引字段（用于列表查询过滤），
      意义在于快速锁定“这条规则属于哪个缺陷”，不参与决策逻辑。
      为避免手填错乱/与前置条件不一致，保存前自动从 preconditions 提取。

    策略：
      1. 解析 rule_description，提取所有前置条件 keyword_name
      2. 在 RuleKeyword 表中查 category='defect' 的第一个命中
      3. 命中：写入 alias -> defect_label, name -> defect_code
         未命中：两个字段均为空字符串（不强约束，允许“不属于任何缺陷”的规则）

    返回：(defect_label, defect_code)，都可能为空字符串
    """
    keywords = _extract_precondition_keywords(rule_description)
    if not keywords:
        return '', ''
    kw = RuleKeyword.objects.filter(
        company_id=company_id,
        keyword_name__in=keywords,
        category='defect',
        is_deleted=False,
    ).first()
    if not kw:
        return '', ''
    return kw.keyword_alias or '', kw.keyword_name or ''


# ==================== RuleKeyword ====================

# 允许写入的模糊档位（与 RuleKeyword.FUZZY_LEVELS 一致，
# 也与前端 types/rule.ts::FuzzyLevel 同集合：3 | 5 | 7）。
# ⚠️ Django 的 choices **不会在 save 时自动校验**（create_with_check 只过滤
#    未知字段名），所以必须在 service 层显式拦，否则 API 客户端仍能写入
#    非法档位（如 9），而内核会把该字段当无效论域直接跳过。
_VALID_FUZZY_LEVELS = (3, 5, 7)


def _validate_fuzzy_level(params):
    """校验并归一化写入的模糊档位（合法时原样返回，非法时抛 400）。"""
    if 'fuzzy_level' not in params or params['fuzzy_level'] is None:
        return
    value = params['fuzzy_level']
    try:
        level = int(value)
    except (TypeError, ValueError):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"模糊级别必须是整数: {value!r}")
    if level not in _VALID_FUZZY_LEVELS:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            f"不支持的模糊级别: {level}（可选 {', '.join(str(i) for i in _VALID_FUZZY_LEVELS)}）",
        )
    params['fuzzy_level'] = level


def get_rule_keyword(rule_keyword_id):
    """获取规则关键字详情"""
    rule = RuleKeyword.objects.filter(
        id=rule_keyword_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该关键字不存在")
    return rule.to_dict()


@transaction.atomic
def add_rule_keyword(company_id, organization_id, **params):
    """新增规则关键字"""
    _validate_fuzzy_level(params)
    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id
    return RuleKeyword.create_with_check(**params).to_dict()


@transaction.atomic
def update_rule_keyword(rule_keyword_id, **params):
    """更新规则关键字"""
    _validate_fuzzy_level(params)
    rule = RuleKeyword.objects.filter(
        id=rule_keyword_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该关键字不存在")
    rule.update_info(**params)
    return rule.to_dict()


@transaction.atomic
def delete_rule_keyword(rule_keyword_id):
    """删除规则关键字（软删除）"""
    rule = RuleKeyword.objects.filter(
        id=rule_keyword_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该关键字不存在")
    rule.soft_delete()


def get_list_of_rule_keyword(
    name=None,
    keyword_type=None,
    company_id=None,
    is_superuser=False,
    page_no=1,
    page_size=30,
    sort="-id",
):
    """获取规则关键字列表

    隔离逻辑：
    - is_superuser=True 且未接管（company_id=None） → 看全部（平台超管视角）
    - 接管后或租户用户 → 看当前 company 的关键字 + 系统演示公司的关键字

    筛选参数（与 `RuleKeywordListSchema` 字段一一对应）：
    - name：模糊匹配 **关键词名称 / 别名**（前端参数名沿用 `name`）
    - keyword_type：参数类型（pressure / speed / time / temperature / position / force / length / weight）
    """
    from identity.models.company import Company
    from identity.const import SYSTEM_DEMO_COMPANY_CODE

    qs = RuleKeyword.objects.filter(is_deleted=False)

    is_platform_admin_view = is_superuser and company_id is None

    if not is_platform_admin_view and company_id is not None:
        system_company = Company.objects.filter(code=SYSTEM_DEMO_COMPANY_CODE).first()
        system_company_ids = [system_company.id] if system_company else []
        visible_company_ids = [company_id] + [
            cid for cid in system_company_ids if cid != company_id
        ]
        qs = qs.filter(company_id__in=visible_company_ids)

    if name:
        # 前端参数名 `name` ⇒ 模型上落到「关键词名称 / 别名」两列
        qs = qs.filter(
            db_models.Q(keyword_name__icontains=name)
            | db_models.Q(keyword_alias__icontains=name)
        )
    if keyword_type:
        qs = qs.filter(keyword_type=keyword_type)

    qs = qs.order_by(*parse_ordering(sort or "-id"))
    pagination = paginate_queryset(qs, page_no, page_size)
    items = [item.to_dict() for item in pagination["items"]]

    return {
        "total": pagination["total_count"],
        "items": items,
    }


# ==================== RuleMethod ====================

def get_rule_method(rule_method_id):
    """获取规则方法详情"""
    rule = RuleMethod.objects.filter(
        id=rule_method_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则方法不存在")
    return rule.to_dict()


@transaction.atomic
def add_rule_method(company_id, organization_id, **params):
    """新增规则方法（仅模糊规则库允许）"""
    # 库存在性 + 类型校验
    lib_id = params.get("rule_library_id")
    if not lib_id:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "缺少必填字段: rule_library_id")
    lib = RuleLibrary.objects.filter(id=lib_id, is_deleted=False).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "所属规则库不存在")
    if lib.library_type != "fuzzy":
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            "只能向模糊规则库（library_type='fuzzy'）添加规则方法",
        )

    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id

    # 自动识别缺陷信息：覆盖前端传入的 defect_label / defect_code
    # （前端表单不填这两个字段，后端始终以 rule_description 为唯一来源）
    defect_label, defect_code = _auto_extract_defect(
        params.get("rule_description", ""),
        company_id,
    )
    params["defect_label"] = defect_label or None
    params["defect_code"] = defect_code or None

    return RuleMethod.create_with_check(**params).to_dict()


@transaction.atomic
def update_rule_method(rule_method_id, **params):
    """更新规则方法"""
    rule = RuleMethod.objects.filter(
        id=rule_method_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则方法不存在")

    # 自动识别缺陷信息：同上，保存前覆盖
    if "rule_description" in params:
        defect_label, defect_code = _auto_extract_defect(
            params.get("rule_description", "") or "",
            rule.company_id,
        )
        params["defect_label"] = defect_label or None
        params["defect_code"] = defect_code or None

    rule.update_info(**params)
    return rule.to_dict()


@transaction.atomic
def delete_rule_method(rule_method_id):
    """删除规则方法（软删除）"""
    rule = RuleMethod.objects.filter(
        id=rule_method_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则方法不存在")
    rule.soft_delete()


def get_list_of_rule_method(
    defect_label=None,
    defect_code=None,
    is_active=None,
    rule_library_id=None,
    page_no=1,
    page_size=30,
    sort="-priority",
):
    """获取规则方法列表"""
    qs = RuleMethod.objects.filter(is_deleted=False)

    if defect_label:
        qs = qs.filter(defect_label__icontains=defect_label)
    if defect_code:
        qs = qs.filter(defect_code__icontains=defect_code)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if rule_library_id is not None:
        qs = qs.filter(rule_library_id=rule_library_id)

    qs = qs.order_by(*parse_ordering(sort or "-priority"))
    pagination = paginate_queryset(qs, page_no, page_size)
    items = [item.to_dict() for item in pagination["items"]]

    return {
        "total": pagination["total_count"],
        "items": items,
    }


# ==================== RuleLibrary ====================

def _visible_library_company_ids(company_id, is_superuser):
    """规则库可见的归属公司 id 集合（列表与详情**共用同一口径**）。

    - 平台超管未接管（`company_id=None`）⇒ 返回 `None`（不限归属，看全部）
    - 其余 ⇒ 当前公司 + 系统演示公司（系统级库对所有租户可见）

    ⚠️ 系统演示公司必须通过 **code 反查**，不能硬编码 id（演示 / 生产环境 id 不同）。
    """
    from identity.const import SYSTEM_DEMO_COMPANY_CODE
    from identity.models.company import Company

    if is_superuser and company_id is None:
        return None

    ids = []
    if company_id is not None:
        ids.append(company_id)
    system_company = Company.objects.filter(code=SYSTEM_DEMO_COMPANY_CODE).first()
    if system_company and system_company.id not in ids:
        ids.append(system_company.id)
    return ids


def get_rule_library(rule_library_id, company_id=None, is_superuser=False):
    """获取规则库详情（带规则数量统计）

    ⚠️ **归属校验**：可见性口径与列表一致（见 `_visible_library_company_ids`）——
    租户只能读自己的库 + 系统级库；读他人租户私库一律拒绝
    （否则登录用户可按 id 遍历越权读取其它租户的规则库）。
    """
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则库不存在")

    visible_company_ids = _visible_library_company_ids(company_id, is_superuser)
    if visible_company_ids is not None and lib.company_id not in visible_company_ids:
        raise BizException(ERROR_ACCESS_LIMIT, "无权访问该规则库")

    data = lib.to_dict()
    # 附加统计：规则方法数量、专家规则数量
    data["method_count"] = RuleMethod.objects.filter(
        rule_library_id=rule_library_id, is_deleted=False,
    ).count()
    data["expert_rule_count"] = ExpertRule.objects.filter(
        rule_library_id=rule_library_id, is_deleted=False,
    ).count()
    return data


@transaction.atomic
def add_rule_library(company_id, organization_id, is_superuser=False,
                     target_company_id=None, **params):
    """新增规则库

    `target_company_id`（**仅超管**）= **代办建库**：把库直接建到指定租户名下。
    - 不传 ⇒ 库建在调用者自己公司名下（租户自建 / 超管自建系统库）；
    - 传了 ⇒ 库建在 `target_company_id` 名下，且**只能是租户级库**
      （系统级库归平台，走「不传」路径即可）。

    ⚠️ **代办是必要的**：不传时 `company_id` 强制 = 调用者公司，
    超管建出来的 `owner_type='tenant'` 库会落在超管的公司（系统演示）名下，
    对目标租户**永远不生效**（静默失效）。
    """
    # 必填校验
    for field in ("library_code", "library_name", "owner_type", "library_type"):
        if not params.get(field):
            raise BizException(ERROR_ILLEGAL_ARGUMENT, f"缺少必填字段: {field}")

    # owner_type 合法性校验
    if params["owner_type"] not in ("system", "tenant"):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "owner_type 必须为 system 或 tenant")

    # library_type 合法性校验
    if params["library_type"] not in ("expert", "fuzzy"):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "library_type 必须为 expert 或 fuzzy")

    # --- 归属公司：默认调用者公司；超管可代办到指定租户 ---
    if target_company_id:
        if not is_superuser:
            raise BizException(
                ERROR_ACCESS_LIMIT, "仅平台超管可为指定租户创建规则库"
            )
        if params["owner_type"] != "tenant":
            raise BizException(
                ERROR_ILLEGAL_ARGUMENT,
                "代办建库仅限租户级规则库（系统级库归平台，不指定归属租户）",
            )
        owner_company_id = target_company_id
    else:
        owner_company_id = company_id

    # 唯一性校验：同一公司内 library_code 不可重复
    exists = RuleLibrary.objects.filter(
        company_id=owner_company_id,
        library_code=params["library_code"],
        is_deleted=False,
    ).exists()
    if exists:
        raise BizException(ERROR_DATA_FOUND, f"规则库编码已存在: {params['library_code']}")

    params["company_id"] = owner_company_id
    if organization_id:
        params["organization_id"] = organization_id
    return RuleLibrary.create_with_check(**params).to_dict()


@transaction.atomic
def update_rule_library(rule_library_id, company_id, is_superuser=False, **params):
    """更新规则库（含归属校验：系统库仅平台超管可改）"""
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则库不存在")

    # 跨租户隔离：不能改其他公司的库（超管不受限 —— 平台资产维护者）
    if not is_superuser and lib.company_id and lib.company_id != company_id:
        raise BizException(ERROR_ACCESS_LIMIT, "无权操作该规则库")

    # 系统库（平台公共大库）：**仅超管可改** —— 租户不得自助改公共资产
    if lib.owner_type == "system" and not is_superuser:
        raise BizException(ERROR_ACCESS_LIMIT, "系统级规则库仅平台超管可修改")

    # library_type 不可修改（类型决定库下数据语义：ExpertRule / RuleMethod）
    if "library_type" in params and params["library_type"] != lib.library_type:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            "库类型不可修改（决定库内允许的规则种类）",
        )
    params.pop("library_type", None)

    # library_code 不可修改
    if "library_code" in params and params["library_code"] != lib.library_code:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "库编码不可修改")
    params.pop("library_code", None)

    lib.update_info(**params)
    return lib.to_dict()


@transaction.atomic
def delete_rule_library(rule_library_id, company_id, is_superuser=False):
    """删除规则库（软删除）
    ⚠️ 系统级库（平台公共大库）**仅超管可删** —— 删了全平台就失去该库。
    """
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则库不存在")

    if not is_superuser and lib.company_id and lib.company_id != company_id:
        raise BizException(ERROR_ACCESS_LIMIT, "无权操作该规则库")

    if lib.owner_type == "system" and not is_superuser:
        raise BizException(ERROR_ACCESS_LIMIT, "系统级规则库仅平台超管可删除")

    # 级联软删除：库下所有规则方法 + 专家规则
    with transaction.atomic():
        RuleMethod.objects.filter(
            rule_library_id=rule_library_id, is_deleted=False,
        ).update(is_deleted=True, deleted_at=db_models.F("updated_at"))
        ExpertRule.objects.filter(
            rule_library_id=rule_library_id, is_deleted=False,
        ).update(is_deleted=True, deleted_at=db_models.F("updated_at"))
        lib.soft_delete()


def get_list_of_rule_library(
    library_name=None,
    library_code=None,
    owner_type=None,
    library_type=None,
    is_active=None,
    company_id=None,
    is_superuser=False,
    page_no=1,
    page_size=30,
    sort="-priority",
):
    """获取规则库列表（带规则数量统计）

    隔离逻辑：
    - is_superuser=True 且未接管（company_id=None） → 看全部（平台超管视角）
    - 接管后或租户用户 → 看当前 company 的库 + 系统演示公司的库（system 库共享）

    筛选参数（**均与 `RuleLibraryListSchema` 字段一一对应**）：
    - library_name / library_code：模糊匹配
    - owner_type：system / tenant
    - library_type：expert / fuzzy（⚠️ 决定库内允许的规则种类，租户建库时选定）
    - is_active：启用状态
    """
    qs = RuleLibrary.objects.filter(is_deleted=False)

    # 可见性：与详情共用同一口径（见 `_visible_library_company_ids`）
    # - 平台超管未接管 → 看全部（平台级视角）
    # - 接管后 / 租户用户 → 当前公司 + 系统演示公司（system 库共享）
    visible_company_ids = _visible_library_company_ids(company_id, is_superuser)
    if visible_company_ids is not None:
        qs = qs.filter(company_id__in=visible_company_ids)

    if library_name:
        qs = qs.filter(library_name__icontains=library_name)
    if library_code:
        qs = qs.filter(library_code__icontains=library_code)
    if owner_type:
        qs = qs.filter(owner_type=owner_type)
    if library_type:
        qs = qs.filter(library_type=library_type)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    qs = qs.order_by(*parse_ordering(sort or "-priority"))
    pagination = paginate_queryset(qs, page_no, page_size)

    # 批量统计 rule count（N+1 优化：1 次查询出所有库的规则数）
    items = pagination["items"]
    lib_ids = [item.id for item in items]

    method_counts = dict(
        RuleMethod.objects.filter(
            rule_library_id__in=lib_ids, is_deleted=False,
        ).values_list("rule_library_id").annotate(c=db_models.Count("id"))
    )
    expert_counts = dict(
        ExpertRule.objects.filter(
            rule_library_id__in=lib_ids, is_deleted=False,
        ).values_list("rule_library_id").annotate(c=db_models.Count("id"))
    )

    result_items = []
    for item in items:
        d = item.to_dict()
        d["method_count"] = method_counts.get(item.id, 0)
        d["expert_rule_count"] = expert_counts.get(item.id, 0)
        result_items.append(d)

    return {
        "total": pagination["total_count"],
        "items": result_items,
    }


# ==================== ExpertRule ====================

def get_expert_rule(expert_rule_id):
    """获取专家规则详情"""
    rule = ExpertRule.objects.filter(
        id=expert_rule_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该专家规则不存在")
    return rule.to_dict()


@transaction.atomic
def add_expert_rule(company_id, organization_id, rule_library_id,
                    is_superuser=False, **params):
    """新增专家规则（仅专家规则库允许）

    ⚠️ **系统级库（平台公共大库）** 的专家规则 **仅平台超管可维护** ——
    公共大库是平台资产，由超管维护（租户不得自助塞入）。
    """
    if not rule_library_id:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "缺少必填字段: rule_library_id")

    # 库存在性 + 类型校验
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "所属规则库不存在")
    if lib.owner_type == "system" and not is_superuser:
        raise BizException(
            ERROR_ACCESS_LIMIT, "系统级规则库下的专家规则仅平台超管可维护"
        )
    if lib.library_type != "expert":
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            "只能向专家规则库（library_type='expert'）添加专家规则",
        )

    # 唯一性：同一库内 rule_code 不可重复
    if ExpertRule.objects.filter(
        rule_library_id=rule_library_id,
        rule_code=params.get("rule_code"),
        is_deleted=False,
    ).exists():
        raise BizException(ERROR_DATA_FOUND, f"专家规则编码已存在: {params.get('rule_code')}")

    params["rule_library_id"] = rule_library_id
    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id
    return ExpertRule.create_with_check(**params).to_dict()


@transaction.atomic
def update_expert_rule(expert_rule_id, company_id, is_superuser=False, **params):
    """更新专家规则（系统级库下仅平台超管可改）"""
    rule = ExpertRule.objects.filter(
        id=expert_rule_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该专家规则不存在")

    # 通过 rule_library 反查归属
    lib = RuleLibrary.objects.filter(id=rule.rule_library_id).first()
    if lib and lib.owner_type == "system" and not is_superuser:
        raise BizException(
            ERROR_ACCESS_LIMIT, "系统级规则库下的专家规则仅平台超管可修改"
        )

    rule.update_info(**params)
    return rule.to_dict()


@transaction.atomic
def delete_expert_rule(expert_rule_id, company_id, is_superuser=False):
    """删除专家规则（软删除；系统级库下仅平台超管可删）"""
    rule = ExpertRule.objects.filter(
        id=expert_rule_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该专家规则不存在")

    lib = RuleLibrary.objects.filter(id=rule.rule_library_id).first()
    if lib and lib.owner_type == "system" and not is_superuser:
        raise BizException(
            ERROR_ACCESS_LIMIT, "系统级规则库下的专家规则仅平台超管可删除"
        )

    rule.soft_delete()


def get_list_of_expert_rule(
    rule_library_id=None,
    rule_code=None,
    is_active=None,
    page_no=1,
    page_size=30,
    sort="priority",
):
    """获取专家规则列表"""
    qs = ExpertRule.objects.filter(is_deleted=False)

    if rule_library_id is not None:
        qs = qs.filter(rule_library_id=rule_library_id)
    if rule_code:
        qs = qs.filter(rule_code__icontains=rule_code)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    qs = qs.order_by(*parse_ordering(sort or "priority"))
    pagination = paginate_queryset(qs, page_no, page_size)
    items = [item.to_dict() for item in pagination["items"]]

    return {
        "total": pagination["total_count"],
        "items": items,
    }