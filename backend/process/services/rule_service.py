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
    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id
    return RuleKeyword.create_with_check(**params).to_dict()


@transaction.atomic
def update_rule_keyword(rule_keyword_id, **params):
    """更新规则关键字"""
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
    show_on_page=None,
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
        qs = qs.filter(name__icontains=name)
    if keyword_type:
        qs = qs.filter(keyword_type=keyword_type)
    if show_on_page is not None:
        qs = qs.filter(show_on_page=show_on_page)

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
    # （前端表单不再手填这两个字段，后端始终以 rule_description 为唯一来源）
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


def get_rules_by_defect(defect_code):
    """根据缺陷 code 获取所有启用的规则（按优先级排序）

    使用 `defect_code` 字段（机器可读标识，如 "SHORTSHOT"），
    不使用 `defect_label`（中文名称，如 "短射"）。
    原因：
    1. code 不依赖语言，国际化友好
    2. 与 FuzzyEngine 使用的英文 defect_name 对齐（SHORTSHOT/SINK_MARK 等）
    3. 同一 code 可以对应多个中文译名，不会因译名变动失效
    """
    rules = RuleMethod.objects.filter(
        defect_code=defect_code,
        is_active=True,
        is_deleted=False,
    ).order_by("-priority")
    return [r.to_dict() for r in rules]


# ==================== RuleLibrary ====================

def get_rule_library(rule_library_id):
    """获取规则库详情（带规则数量统计）"""
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则库不存在")

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
def add_rule_library(company_id, organization_id, **params):
    """新增规则库"""
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

    # 唯一性校验：同一公司内 library_code 不可重复
    exists = RuleLibrary.objects.filter(
        company_id=company_id,
        library_code=params["library_code"],
        is_deleted=False,
    ).exists()
    if exists:
        raise BizException(ERROR_DATA_FOUND, f"规则库编码已存在: {params['library_code']}")

    params["company_id"] = company_id
    if organization_id:
        params["organization_id"] = organization_id
    return RuleLibrary.create_with_check(**params).to_dict()


@transaction.atomic
def update_rule_library(rule_library_id, company_id, **params):
    """更新规则库（含归属校验：系统库仅平台可改）"""
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则库不存在")

    # 跨租户隔离：不能改其他公司的库
    if lib.company_id and lib.company_id != company_id:
        raise BizException(ERROR_ACCESS_LIMIT, "无权操作该规则库")

    # 系统库默认不允许租户修改
    if lib.owner_type == "system":
        raise BizException(ERROR_ACCESS_LIMIT, "系统级规则库不可修改")

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
def delete_rule_library(rule_library_id, company_id):
    """删除规则库（软删除）"""
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "该规则库不存在")

    if lib.owner_type == "system":
        raise BizException(ERROR_ACCESS_LIMIT, "系统级规则库不可删除")

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
    """
    from identity.models.company import Company
    from identity.const import SYSTEM_DEMO_COMPANY_CODE

    qs = RuleLibrary.objects.filter(is_deleted=False)

    # 超管未接管 → 看全部（仅平台级视角）
    is_platform_admin_view = is_superuser and company_id is None

    if not is_platform_admin_view and company_id is not None:
        # 租户视角：本租户 + 系统演示公司（system 库共享给所有租户）
        # 注意：通过 code 反查 system 公司的 id，不能硬编码
        system_company = Company.objects.filter(code=SYSTEM_DEMO_COMPANY_CODE).first()
        system_company_ids = [system_company.id] if system_company else []
        visible_company_ids = [company_id] + [
            cid for cid in system_company_ids if cid != company_id
        ]
        qs = qs.filter(company_id__in=visible_company_ids)
    # 超管未接管：不过滤 company，看全部

    if library_name:
        qs = qs.filter(library_name__icontains=library_name)
    if library_code:
        qs = qs.filter(library_code__icontains=library_code)
    if owner_type:
        qs = qs.filter(owner_type=owner_type)
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
def add_expert_rule(company_id, organization_id, rule_library_id, **params):
    """新增专家规则（仅专家规则库允许）"""
    if not rule_library_id:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "缺少必填字段: rule_library_id")

    # 库存在性 + 类型校验
    lib = RuleLibrary.objects.filter(
        id=rule_library_id, is_deleted=False,
    ).first()
    if not lib:
        raise BizException(ERROR_DATA_NOT_FOUND, "所属规则库不存在")
    if lib.owner_type == "system":
        raise BizException(ERROR_ACCESS_LIMIT, "系统级规则库不可新增专家规则")
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
def update_expert_rule(expert_rule_id, company_id, **params):
    """更新专家规则"""
    rule = ExpertRule.objects.filter(
        id=expert_rule_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该专家规则不存在")

    # 通过 rule_library 反查归属
    lib = RuleLibrary.objects.filter(id=rule.rule_library_id).first()
    if lib and lib.owner_type == "system":
        raise BizException(ERROR_ACCESS_LIMIT, "系统级规则库下的专家规则不可修改")

    rule.update_info(**params)
    return rule.to_dict()


@transaction.atomic
def delete_expert_rule(expert_rule_id, company_id):
    """删除专家规则（软删除）"""
    rule = ExpertRule.objects.filter(
        id=expert_rule_id, is_deleted=False,
    ).first()
    if not rule:
        raise BizException(ERROR_DATA_NOT_FOUND, "该专家规则不存在")

    lib = RuleLibrary.objects.filter(id=rule.rule_library_id).first()
    if lib and lib.owner_type == "system":
        raise BizException(ERROR_ACCESS_LIMIT, "系统级规则库下的专家规则不可删除")

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