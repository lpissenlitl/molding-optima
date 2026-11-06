"""候选规则落地 —— 把审核通过的候选规则翻译成 RuleMethod（生效规则）。

⚠️ **为什么落地是「翻译」而不是「直接写」**
    挖掘内核产出的是**统计关联**（「缺陷 + 参数变更 ⇒ 结果」），
    而 `RuleMethod.rule_description` 是**模糊规则的语法**
    （`IF <条件> THEN <动作>`）—— 两者结构不同：

    ==================================  ==================================
    挖掘规则（统计）                     RuleMethod（模糊语法）
    ==================================  ==================================
    前件缺陷 ``SHORTSHOT``               条件 ``SHORTSHOT_medium``
    前件变更 ``inj_pres_1:increase``     条件 ``IP0_low`` + 动作 ``IP0_add_10``
    后件 ``improved``                    ——（后件不写进规则，只进 confidence）
    ==================================  ==================================

    翻译要解决三件事：
    1. **命名空间**：业务字段名 → 算法字段名（``inj_pres_1`` → ``IP0``，
       走 `fuzzy.field_names.to_algo_name`）
    2. **档位**：变更**前**的参数值落在哪一档 —— 用 `RuleKeyword` 的量程
       （range_min/range_max）与该字段自己的档位词表算，不做
       「increase ⇒ 偏低」的反推假设（反推会把「已经很高还在调高」
       这类无意义规则也放行）
    3. **动作量**：调整多少 —— 用证据样本的平均幅度，并受
       `RuleKeyword.action_max_val`（最大调整值）与 `step`（模糊步长）约束

⚠️ **只落地「正向 + 有动作」的规则**
    - 后件必须是 `qualified` / `improved`（正向信号）
      —— `unqualified` / `worse` 是**反面经验**，RuleMethod 的语法只能表达
      「建议这样调」，写进去等于建议一个已知有害的操作 ⇒ 只留在候选表里
    - 必须有参数变更 —— 没有变更就没有可建议的动作
      —— 形如「有短射 ⇒ 会改善」这种规则没有可落地的动作

⚠️ **一条候选规则可落地成多条 RuleMethod**
    候选规则的前件可能含多个变更（如「同时调高注射压力1 与降保压压力1」），
    而模糊规则的 THEN 只表达**一个**动作 ⇒ 每个变更各出一条规则，
    条件部分相同、动作部分不同。

⚠️ **落在专用规则库里**
    公司目前没有「主模糊规则库」，挖掘规则与专家维护的规则混在一起会互相污染
    ⇒ 每公司一个专用模糊库（`library_code='rule_miner'`），不存在则建。
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from process.algorithms.fuzzy.field_names import to_algo_name
from process.algorithms.fuzzy.fuzzy_core.macros import LEVEL_WORDS_BY_LVL
from process.algorithms.mining.contracts import defect_level, defect_name
from process.models import RuleKeyword, RuleLibrary, RuleMethod


_logger = logging.getLogger(__name__)


#: 挖掘规则专用规则库的编码
MINING_LIBRARY_CODE = 'rule_miner'

#: 挖掘规则专用规则库的名称
MINING_LIBRARY_NAME = '规则挖掘库'

#: 公共挖掘规则库的编码（**全平台唯一** —— 全局只有一条同码记录）
PUBLIC_MINING_LIBRARY_CODE = 'rule_miner_public'

#: 公共挖掘规则库的名称
PUBLIC_MINING_LIBRARY_NAME = '公共规则挖掘库'

#: 正向后件标签（与 `mining.contracts.POSITIVE_LABELS` 一致）
POSITIVE_CONSEQUENTS = ('qualified', 'improved')

#: 方向 → 模糊动作词
ACTION_BY_DIRECTION = {
    'increase': 'add',
    'decrease': 'reduce',
}


@dataclass
class LandingPlan:
    """一条候选规则的落地计划。

    Attributes
    ----------
    landing_rules : List[Dict]
        可落地的 RuleMethod 内容（每项含 ``rule_description`` 等字段）。
    skipped : List[Dict]
        跳过的项与原因（``{'reason': str, 'detail': str}``），
        让审核人知道「为什么这条规则没有变成生效规则」。
    """

    landing_rules: List[Dict] = field(default_factory=list)
    skipped: List[Dict] = field(default_factory=list)

    @property
    def landable(self) -> bool:
        """是否有可落地的规则。"""
        return bool(self.landing_rules)


# ============================================================================
# 档位换算
# ============================================================================

def resolve_level_word(keyword: RuleKeyword, value: float) -> Optional[str]:
    """参数值 → 该字段自己的档位词。

    ⚠️ **档位词表由字段的 `fuzzy_level` 决定**（3 档 low/medium/high、
       5 档 very_low…very_high、7 档 extremely_low…）——
       同一个 ``low`` 在 3 档字段是桶 0、在 5 档字段是桶 1 ⇒ 必须按字段自己的
       词表定位，不能用全局静态表（见 `fuzzy_core.macros`）。

    Args:
        keyword: 参数的 `RuleKeyword`（提供 range 与 fuzzy_level）。
        value: 参数值（变更前的值）。

    Returns:
        档位词；量程非法 / 词表缺失时返回 None。
    """
    words = LEVEL_WORDS_BY_LVL.get(keyword.fuzzy_level)
    if not words:
        return None

    span = keyword.range_max - keyword.range_min
    if span <= 0:
        return None

    ratio = (float(value) - keyword.range_min) / span
    ratio = min(max(ratio, 0.0), 0.999999)
    return words[int(ratio * len(words))]


def _is_direction_sane(
    level_index: int,
    direction: str,
    level_count: int,
) -> bool:
    """动作方向与当前档位是否相容。

    「调高」只应在**不高**的档位发生，「调低」只应在**不低**的档位发生 ——
    否则就是「已经很高还要再调高」这种无工艺意义的规则，
    不该进生效规则库去污染推理。

    中位桶取 ``(level_count - 1) // 2``（3 档 ⇒ 1，5 档 ⇒ 2，7 档 ⇒ 3），
    「调高」允许 ``<= 中位``，「调低」允许 ``>= 中位``。
    """
    middle = (level_count - 1) // 2
    if direction == 'increase':
        return level_index <= middle
    if direction == 'decrease':
        return level_index >= middle
    return False


def _format_delta(delta: float) -> str:
    """动作量的文本形态（整数不带小数，小数保留一位）。"""
    rounded = round(float(delta), 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return f'{rounded:g}'


# ============================================================================
# 计划生成
# ============================================================================

def build_landing_plan(mining_rule, company_id: int) -> LandingPlan:
    """生成一条候选规则的落地计划（不写库）。

    Args:
        mining_rule: 候选规则（`MiningRule` 实例）。
        company_id: 公司 id（用于查 `RuleKeyword`）。

    Returns:
        `LandingPlan`（含可落地项与跳过项）。
    """
    plan = LandingPlan()

    # --- 1. 后件必须是正向 ---
    consequent = mining_rule.consequent
    if consequent not in POSITIVE_CONSEQUENTS:
        plan.skipped.append({
            'reason': '非正向后件',
            'detail': (
                f'后件为 {consequent}（unqualified / worse 是反面经验，'
                f'RuleMethod 只能表达「建议这样调」，写进去等于建议一个'
                f'已知有害的操作）'
            ),
        })
        return plan

    # --- 2. 必须有参数变更 ---
    changes = [c for c in (mining_rule.changes or []) if c.get('param')]
    if not changes:
        plan.skipped.append({
            'reason': '无可建议的动作',
            'detail': '该规则没有参数变更 ⇒ 翻译不出 THEN 动作，只能作为统计事实参考',
        })
        return plan

    # --- 3. 缺陷条件（可选）---
    defect_conditions, defect_skips = _build_defect_conditions(
        mining_rule, company_id,
    )
    plan.skipped.extend(defect_skips)

    # --- 4. 每个变更生成一条规则 ---
    for change in changes:
        rule, skip = _build_one_rule(
            mining_rule, change, defect_conditions, company_id,
        )
        if rule is not None:
            plan.landing_rules.append(rule)
        elif skip is not None:
            plan.skipped.append(skip)

    return plan


def _build_defect_conditions(
    mining_rule,
    company_id: int,
) -> Tuple[List[str], List[Dict]]:
    """缺陷条件词（``SHORTSHOT_medium``）。

    等级取自候选规则的 `defects[].level`（证据样本众数）。
    ⚠️ 等级若不在该缺陷字段自己的档位词表里（缺陷多为 5 档，
    现网数据出现 ``very_low``），引擎会因「合法档位词但该字段档数不够」
    把**整条规则**作废 ⇒ 这里直接剔除该条件并说明原因。
    """
    conditions: List[str] = []
    skipped: List[Dict] = []

    for item in (mining_rule.defects or []):
        defect = defect_name(item)
        if not defect:
            continue
        level = defect_level(item)
        if not level:
            skipped.append({
                'reason': '缺陷等级未知',
                'detail': f'缺陷 {defect} 在证据样本里没有等级记录，该条件已剔除',
            })
            continue

        keyword = RuleKeyword.objects.filter(
            company_id=company_id,
            keyword_name=defect,
            category='defect',
            is_deleted=False,
        ).first()
        if keyword is None:
            skipped.append({
                'reason': '缺陷未登记',
                'detail': f'缺陷 {defect} 在规则关键词里没有登记，该条件已剔除',
            })
            continue

        words = LEVEL_WORDS_BY_LVL.get(keyword.fuzzy_level) or ()
        if level not in words:
            skipped.append({
                'reason': '缺陷等级与字段档数不匹配',
                'detail': (
                    f'缺陷 {defect} 的档位词表为 {list(words)}，'
                    f'证据里的等级「{level}」不在其中，该条件已剔除'
                ),
            })
            continue

        conditions.append(f'{defect}_{level}')

    return conditions, skipped


def _build_one_rule(
    mining_rule,
    change: Dict,
    defect_conditions: List[str],
    company_id: int,
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """一条变更 → 一条 RuleMethod 内容。

    Returns:
        ``(rule, skip)`` —— 成功时 ``rule`` 有值；失败时 ``skip`` 有值。
    """
    param = change.get('param')
    direction = change.get('direction')
    action = ACTION_BY_DIRECTION.get(direction)
    if action is None:
        return None, {
            'reason': '变更方向不支持',
            'detail': f'参数 {param} 的方向「{direction}」没有对应的模糊动作词',
        }

    # --- 参数命名空间：业务字段名 → 算法字段名 ---
    algo_name = to_algo_name(param)
    if not algo_name:
        return None, {
            'reason': '参数无算法命名空间',
            'detail': (
                f'参数 {param} 在模糊规则命名空间里没有对应字段名'
                f'（`fuzzy.field_names` 未收录），无法生成条件与动作'
            ),
        }

    keyword = RuleKeyword.objects.filter(
        company_id=company_id,
        # ⚠️ **按算法字段名查**：`RuleKeyword.keyword_name` 存的是**算法命名空间**
        #    （`IP0` / `PP0` / `BT1`），不是业务字段名（`inj_pres_1`）——
        #    用业务名查会一条都查不到 ⇒ 每条规则都会被误判为「参数未登记」。
        keyword_name=algo_name,
        category='parameter',
        is_deleted=False,
    ).first()
    if keyword is None:
        return None, {
            'reason': '参数未登记',
            'detail': (
                f'参数 {param}（算法名 {algo_name}）在规则关键词里没有登记，'
                f'无法计算档位'
            ),
        }

    # --- 档位：用变更前的值算 ---
    before = change.get('before')
    if not isinstance(before, (int, float)):
        return None, {
            'reason': '缺少变更前数值',
            'detail': f'参数 {param} 的证据样本没有 before 值，无法判断所处档位',
        }

    level_word = resolve_level_word(keyword, float(before))
    if level_word is None:
        return None, {
            'reason': '无法计算档位',
            'detail': (
                f'参数 {param} 的量程（{keyword.range_min}~{keyword.range_max}）'
                f'或档位词表不可用'
            ),
        }

    words = LEVEL_WORDS_BY_LVL.get(keyword.fuzzy_level) or ()
    level_index = words.index(level_word)
    if not _is_direction_sane(level_index, direction, len(words)):
        return None, {
            'reason': '动作方向与当前档位相悖',
            'detail': (
                f'参数 {param} 变更前处于「{level_word}」档，'
                f'却是「{direction}」方向 —— 该规则无工艺意义，已跳过'
            ),
        }

    # --- 动作量：证据样本的平均幅度 ---
    after = change.get('after')
    if not isinstance(after, (int, float)):
        return None, {
            'reason': '缺少变更后数值',
            'detail': f'参数 {param} 的证据样本没有 after 值，无法计算调整量',
        }

    delta = abs(float(after) - float(before))
    if delta <= 0:
        return None, {
            'reason': '调整量为零',
            'detail': f'参数 {param} 的证据样本调整幅度为 0，无法生成动作',
        }

    # 受最大调整值约束
    if keyword.action_max_val:
        delta = min(delta, float(keyword.action_max_val))
    # 与模糊步长对齐（推理输出会取整到 step 的整数倍）
    if keyword.step and keyword.step > 0:
        delta = round(delta / keyword.step) * keyword.step

    # --- 组装规则文本 ---
    conditions = list(defect_conditions) + [f'{algo_name}_{level_word}']
    description = (
        f"IF {' AND '.join(conditions)} THEN {algo_name}_{action}_{_format_delta(delta)}"
    )

    defect_code = defect_label = None
    first_defect = defect_name(mining_rule.defects[0]) if mining_rule.defects else ''
    if first_defect:
        defect_code = first_defect
        defect_kw = RuleKeyword.objects.filter(
            company_id=company_id,
            keyword_name=defect_code,
            category='defect',
            is_deleted=False,
        ).first()
        defect_label = defect_kw.keyword_alias if defect_kw else None

    return {
        'rule_description': description,
        'rule_explanation': _build_explanation(
            mining_rule, param, level_word, delta, action,
        ),
        'defect_label': defect_label,
        'defect_code': defect_code,
        'confidence': float(mining_rule.confidence or 0.0),
        'priority': 1,
        'is_active': True,
    }, None


def _build_explanation(
    mining_rule,
    param: str,
    level_word: str,
    delta: float,
    action: str,
) -> str:
    """生成中文规则解释（说明这条规则是怎么从统计里来的）。"""
    defects = '、'.join(
        defect_name(d) for d in (mining_rule.defects or [])
    ) or '无缺陷'
    verb = '增加' if action == 'add' else '减少'
    return (
        f'规则挖掘产出（证据 {mining_rule.sample_count} 条，'
        f'置信度 {mining_rule.confidence:.2f}）：'
        f'出现 {defects} 时，{param} 处于 {level_word} 档，'
        f'将其{verb} {_format_delta(delta)}，试模结果变好。'
    )


# ============================================================================
# 规则库与写入
# ============================================================================

def ensure_mining_library(company_id: int) -> RuleLibrary:
    """取（或建）该公司的挖掘规则专用模糊规则库。

    ⚠️ 挖掘规则与专家维护的规则混在一起会互相污染（优先级语义不同、
       维护节奏不同）⇒ 单独建库。
    """
    library = RuleLibrary.objects.filter(
        company_id=company_id,
        library_code=MINING_LIBRARY_CODE,
        library_type='fuzzy',
        is_deleted=False,
    ).first()
    if library is not None:
        return library

    return RuleLibrary.objects.create(
        company_id=company_id,
        library_code=MINING_LIBRARY_CODE,
        library_no=_next_library_no(),
        library_name=MINING_LIBRARY_NAME,
        description='规则挖掘产出的生效规则（经管理员审核通过）',
        library_type='fuzzy',
        owner_type='tenant',
        priority=0,
        is_active=True,
    )


def ensure_public_mining_library() -> RuleLibrary:
    """取（或建）**全平台公用**的公共挖掘规则库。

    ⚠️ **与 `ensure_mining_library` 是两件事**：
       - `ensure_mining_library` 建的是**租户私库**（`owner_type='tenant'`，
         归属该租户）—— 挖掘审核通过后先落在租户自己的库里，
         只有该租户看得见；
       - 本函数建的是**系统库**（`owner_type='system'`，归属系统演示公司）——
         平台超管把验证过的经验**晋升**到这里后，**所有租户**都能用。

    ⚠️ **系统公司必须通过 code 反查，不能硬编码 id**：
       `identity.const.SYSTEM_DEMO_COMPANY_CODE` 是全库唯一的约定，
       硬编码 id 会在不同环境（演示 / 生产）指向不存在的公司。

    ⚠️ **公共库的 `library_code` 必须全局唯一**：
       算法侧取库索引时同编码只保留**第一条**（`library/rules.py::
       get_library_index` 用 `setdefault`）⇒ 公共库若与租户私库同码，
       就会被静默挤掉 ⇒ 公共库用独立编码 `rule_miner_public`。
    """
    from identity.const import SYSTEM_DEMO_COMPANY_CODE
    from identity.models.company import Company

    system_company = Company.objects.filter(
        code=SYSTEM_DEMO_COMPANY_CODE,
    ).first()
    if system_company is None:
        raise RuntimeError(
            f'系统演示公司（code={SYSTEM_DEMO_COMPANY_CODE}）不存在，'
            f'无法创建公共规则库（请先执行 init_platform）'
        )

    library = RuleLibrary.objects.filter(
        company_id=system_company.id,
        library_code=PUBLIC_MINING_LIBRARY_CODE,
        library_type='fuzzy',
        is_deleted=False,
    ).first()
    if library is not None:
        return library

    return RuleLibrary.objects.create(
        company_id=system_company.id,
        library_code=PUBLIC_MINING_LIBRARY_CODE,
        library_no=_next_library_no(),
        library_name=PUBLIC_MINING_LIBRARY_NAME,
        description='经平台超管晋升的公共挖掘规则（全平台公用）',
        library_type='fuzzy',
        owner_type='system',
        priority=0,
        is_active=True,
    )


def _next_library_no() -> str:
    """规则库编号（`RL-{YYYYMM}-{NNNNN}`）。"""
    prefix = f'RL-{datetime.now().strftime("%Y%m")}-'
    taken = set(
        RuleLibrary.objects.filter(
            library_no__startswith=prefix,
        ).values_list('library_no', flat=True)
    )
    for seq in range(1, 100000):
        code = f'{prefix}{seq:05d}'
        if code not in taken:
            return code
    raise RuntimeError('规则库编号已耗尽，无法继续生成')


def _next_rule_no(company_id: int) -> str:
    """规则方法编号（`RM-{YYYYMM}-{NNNNN}`）。"""
    prefix = f'RM-{datetime.now().strftime("%Y%m")}-'
    taken = set(
        RuleMethod.objects.filter(
            company_id=company_id, rule_no__startswith=prefix,
        ).values_list('rule_no', flat=True)
    )
    for seq in range(1, 100000):
        code = f'{prefix}{seq:05d}'
        if code not in taken:
            return code
    raise RuntimeError('规则方法编号已耗尽，无法继续生成')


def land_mining_rule(
    mining_rule,
    company_id: int,
    library: Optional[RuleLibrary] = None,
) -> Tuple[List[RuleMethod], LandingPlan]:
    """把候选规则落地为 RuleMethod。

    Args:
        mining_rule: 候选规则。
        company_id: 公司 id。
        library: 目标规则库；None 时取（或建）该公司的挖掘专用库。

    Returns:
        ``(created_rules, plan)`` —— 已写入的规则方法与落地计划
        （含被跳过的项与原因）。
    """
    plan = build_landing_plan(mining_rule, company_id)
    if not plan.landing_rules:
        return [], plan

    if library is None:
        library = ensure_mining_library(company_id)

    created: List[RuleMethod] = []
    for content in plan.landing_rules:
        created.append(RuleMethod.objects.create(
            company_id=company_id,
            rule_library=library,
            rule_no=_next_rule_no(company_id),
            source='rule_miner',
            **content,
        ))
    return created, plan


__all__ = [
    'LandingPlan',
    'MINING_LIBRARY_CODE',
    'MINING_LIBRARY_NAME',
    'POSITIVE_CONSEQUENTS',
    'PUBLIC_MINING_LIBRARY_CODE',
    'PUBLIC_MINING_LIBRARY_NAME',
    'build_landing_plan',
    'ensure_mining_library',
    'ensure_public_mining_library',
    'land_mining_rule',
    'resolve_level_word',
]
