"""内核输入契约 —— KeywordProfile / RuleProfile。

**层定位**：`fuzzy_core` 的**输入契约层**。这两个类是模糊推理内核
（`fuzzy_core.models.nets`）**唯一**接受的输入对象，由**数据来源适配层**
构造（依赖方向：外层 → 内核，内核不反向引用外层模块）。

**为什么契约归内核所有**：内核是算法资产，它的输入格式应由它自己定义，
外部层遵守，而不是反过来。

**命名**：`Profile` = 档案（一个工艺参数的档案 / 一条规则的档案）。
刻意避开三处同名物：

- ORM 模型：`RuleKeyword` / `RuleMethod`（数据来源侧）
- 内核内部产物：`FuzzyFeature`（论域实例）/ `FuzzyRule` / `NumTskRule`（规则串解析产物）
- 项目既有约定：`specs` 专指**对外接口**契约（`fuzzy/specs.py`，与 expert 包同名同层），
  本模块是**内核输入**，方向相反，不复用 `spec` 词根

**与内核内部产物的分工**：

| 对象 | 角色 |
|---|---|
| `KeywordProfile` | **字段元数据**（一个工艺参数：名字 / 档位数 / 论域 / 步长） |
| `FuzzyFeature` | **论域实例**（某个具体变量的隶属度表示，由 Profile 派生） |
| `RuleProfile` | **规则档案**（规则串 + 优先级 + 结论形态 + 特异级 + 溯源） |
| `NumTskRule` / `FuzzyRule` | **规则串解析产物**（由 RuleProfile 派生） |

一个字段会派生**两个** `FuzzyFeature`（输入侧论域 / 输出侧论域），
所以 Profile 与 FuzzyFeature 不是一对一 —— 前者是字段级，后者是论域实例级。

**零外部依赖**：本模块不 import Django、不 import ORM，
可直接 `python profiles.py` 自检，也可被任何数据来源实现方安全 import。
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


__all__ = [
    'KeywordProfile',
    'RuleProfile',
    'keyword_profile_issues',
    'rule_profile_issues',
    'validate_keyword_profiles',
    'validate_rule_profiles',
]


# 内核支持的模糊等级数（与 RuleKeyword.FUZZY_LEVELS、macros.LEVEL_WORDS_BY_LVL 的键一致）
VALID_LVL = (3, 5, 7)

# 结论形态（按结论形态分流：能不能算出数值；不是规则库的组织维度）
VALID_CONCLUSION_KINDS = ('numeric', 'advisory')

# 特异级 1~4（1=精确 / 2=部分polymer / 3=部分product / 4=默认）
VALID_SPECIFICITY = (1, 2, 3, 4)


# ============================================================================
# KeywordProfile: 算法侧关键字档案（论域元数据）
# ============================================================================

@dataclass
class KeywordProfile:
    """算法侧关键字（论域元数据）档案。

    内核 net 的论域输入对象。

    Attributes
    ----------
    keyword : str
        参数名（**算法命名空间**，如 'IV0'；不是业务字段名）。
    lvl : int
        模糊等级数，取 3 / 5 / 7 / 9。
    min_val : float
        论域下界。
    max_val : float
        论域上界（须 > `min_val`）。
    step : float
        模糊步长（去模糊化输出的粒度，须 > 0）。
    meta_source : str
        元数据来源标记（可选）。`'guessed'` 表示该论域是按实时值**推测**的，
        不是权威参数元数据；空串 = 权威来源。内核不读此字段，仅供上层分流。
    """

    keyword: str
    lvl: int = 3
    min_val: float = 0.0
    max_val: float = 1.0
    step: float = 1.0
    meta_source: str = ''


# ============================================================================
# RuleProfile: 算法侧规则档案
# ============================================================================

@dataclass
class RuleProfile:
    """算法侧规则档案。

    内核 net 的规则输入对象。

    Attributes
    ----------
    rule_description : str
        规则串，格式 `IF {defect}_{level} AND ... THEN {param}_{action}_{value}`。
        这是**规则内容的唯一权威载体** —— 数据来源只需保证这一份正确。
    priority : float
        规则优先级（数值越大越优先）。
    conclusion_kind : str
        结论形态：`'numeric'`（数值结论）/ `'advisory'`（提示类结论）。
        按**结论形态**判定（能不能算出数值），不是规则库的组织维度。
    specificity : int
        特异级 1~4（1=精确 / 2=部分polymer / 3=部分product / 4=默认）。
    source_ref : str
        溯源标识（可选）：数据库主键 / 文件路径 + 行号等。
        **不参与算法**，仅用于「这条建议来自哪条规则」这类排查与展示。
        ⚠️ 这里放**字符串**而不是数据源对象 —— 放对象就等于把来源焊回契约
        （旧实现里的 `method` 字段装 ORM 实例，正是这个问题）。
    parsed : dict | None
        规则串的**拆解产物**（`fuzzy_core.parsing.parse_rule` 的返回值：
        ``{'preconditions': [...], 'solutions': [...]}``）。

        ⚠️ **为什么装在契约里**：同一条规则串在整条链路上会被拆**三次**
        （来源适配层判结论形态 / 编排层判缺陷名 / 内核第 4 层建对象），
        1646 条规则 ⇒ 约 5000 次重复拆解。拆解是**纯函数**且结果只与规则串有关，
        因此「拆一次、带着走」是唯一无损的收敛方式（缓存也有同样的效果，
        但缓存的键/失效时机得额外维护）。

        ⚠️ **可选**（默认 `None`）：为 `None` 时下游（`fuzzy_core.rules_filter`）
        会自行拆解 ⇒ 直接构造 `RuleProfile` 的调用方（测试替身 / 离线脚本 /
        demo 案例）**不必关心本字段**。

        ⚠️ **必须与 `rule_description` 同源**：由来源适配层用**同一个**规则串
        解析一次产出。若二者不一致，下游用的是 `parsed` 而非重新拆解 ⇒ 会静默错位。
    """

    rule_description: str
    priority: float = 1.0
    conclusion_kind: str = 'numeric'
    specificity: int = 4
    source_ref: str = ''
    parsed: Optional[Dict[str, List[Dict[str, str]]]] = None


# ============================================================================
# 校验：数据来源的产出必须过这道关口
# ============================================================================

def keyword_profile_issues(p: KeywordProfile) -> List[str]:
    """单条关键字档案的问题清单（**空列表 = 合法**）。

    与 `validate_keyword_profiles` **同口径**，但不抛异常 ——
    供「逐条校验、跳过坏的、保住好的」场景使用
    （见 `library/repository.py` 的两个出库点）。

    ⚠️ 为什么需要单条版：整批版语义是「任一条不合法即抛 ValueError」，
    适合需要 fail-fast 的调用方；而生产路径要求的是**一条脏档案只废掉自己**，
    不能让整次调优塌成空推荐（`engine.recommend` 的兜底会把异常吞成空推荐）。
    """
    issues: List[str] = []
    if not str(p.keyword or '').strip():
        issues.append('keyword 不能为空')
    if p.lvl not in VALID_LVL:
        issues.append(f'lvl={p.lvl!r} 非法（合法值 {VALID_LVL}）')
    if not (p.min_val < p.max_val):
        issues.append(f'min_val({p.min_val}) 必须 < max_val({p.max_val})')
    if not (p.step > 0):
        issues.append(f'step({p.step}) 必须 > 0')
    return issues


def rule_profile_issues(p: RuleProfile) -> List[str]:
    """单条规则档案的问题清单（**空列表 = 合法**）。

    与 `validate_rule_profiles` 同口径，但不抛异常（理由同
    `keyword_profile_issues`）。
    """
    issues: List[str] = []
    if not str(p.rule_description or '').strip():
        issues.append('rule_description 不能为空')
    try:
        float(p.priority)
    except (TypeError, ValueError):
        issues.append(f'priority={p.priority!r} 不是数值')
    if p.conclusion_kind not in VALID_CONCLUSION_KINDS:
        issues.append(
            f'conclusion_kind={p.conclusion_kind!r} 非法'
            f'（合法值 {VALID_CONCLUSION_KINDS}）')
    if p.specificity not in VALID_SPECIFICITY:
        issues.append(f'specificity={p.specificity!r} 非法'
                      f'（合法值 {VALID_SPECIFICITY}）')
    return issues


def validate_keyword_profiles(profiles: Iterable[KeywordProfile]) -> None:
    """校验关键字档案；任一条不合法即抛 `ValueError`（一次列全所有问题）。

    这是"数据来源可插拔"的前提：来源可能是数据库、也可能是本地文件，
    解析出的档案必须**先过校验**才能进入构建层 ⇒ 脏数据在边界被拦下，
    而不是等到内核算隶属度时才抛异常。

    ⚠️ 生产路径（`library/repository.py`）用的是**单条版**
    `keyword_profile_issues` —— 逐条跳过坏的、保住好的，而不是整批抛：
    一条脏档案只废掉自己，不能让整次调优塌成空推荐。
    """
    errors = []
    for idx, p in enumerate(profiles):
        where = f'keyword_profiles[{idx}]'
        errors.extend(f'{where}: {msg}' for msg in keyword_profile_issues(p))
    if errors:
        raise ValueError('关键字档案校验失败:\n  ' + '\n  '.join(errors))


def validate_rule_profiles(profiles: Iterable[RuleProfile]) -> None:
    """校验规则档案；任一条不合法即抛 `ValueError`（一次列全所有问题）。"""
    errors = []
    for idx, p in enumerate(profiles):
        where = f'rule_profiles[{idx}]'
        errors.extend(f'{where}: {msg}' for msg in rule_profile_issues(p))
    if errors:
        raise ValueError('规则档案校验失败:\n  ' + '\n  '.join(errors))


# ============================================================================
# 模块自检
# ============================================================================

if __name__ == '__main__':
    print('profiles 模块结构正常加载')
    print('  KeywordProfile 字段:', list(KeywordProfile.__dataclass_fields__))
    print('  RuleProfile 字段:   ', list(RuleProfile.__dataclass_fields__))

    kw = KeywordProfile(keyword='IV0', lvl=3, min_val=0.0, max_val=100.0, step=1.0)
    kw_guessed = KeywordProfile(
        keyword='IV1', lvl=3, min_val=0.0, max_val=20.0, step=1.0,
        meta_source='guessed')
    rules = [
        RuleProfile(rule_description='IF SHORTSHOT_low AND IV0_low THEN IV0_add_2',
                    priority=1.0, conclusion_kind='numeric', specificity=4,
                    source_ref='db:123'),
        RuleProfile(rule_description='IF SHORTSHOT_high AND IV0_high THEN IV0_reduce_5%',
                    priority=0.8, conclusion_kind='advisory', specificity=2,
                    source_ref='db:456'),
    ]

    # 校验：合法通过
    validate_keyword_profiles([kw, kw_guessed])
    validate_rule_profiles(rules)
    print('  校验：合法档案通过')

    # 校验：非法被拦下（对照）
    try:
        validate_keyword_profiles([KeywordProfile(keyword='', lvl=4, min_val=10, max_val=1, step=0)])
        print('  [FAIL] 非法档案竟然通过了')
    except ValueError as e:
        print('  校验：非法档案被拦下 ->', str(e).splitlines()[0])
        print('         实际问题数:', len(str(e).splitlines()) - 1)

    try:
        validate_rule_profiles([RuleProfile(rule_description='', conclusion_kind='oops',
                                           specificity=9)])
        print('  [FAIL] 非法规则档案竟然通过了')
    except ValueError as e:
        print('  校验：非法规则档案被拦下 ->', str(e).splitlines()[0])
        print('         实际问题数:', len(str(e).splitlines()) - 1)
