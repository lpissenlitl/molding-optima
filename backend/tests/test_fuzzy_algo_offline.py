r"""模糊推理算法「脱离前端 + 脱离数据库 + 脱离 Django」的独立自检（L1 离线层）。

定位
----
证明模糊推理算法**不依赖前端页面、不依赖数据库**也能完整跑通，
并对「推荐值 / 置信度 / 方向」给出**精确可断言**的结果。

与既有脚本的分工
----------------
- ``tests/fuzzy_kernel/_snapshot_core.py``  ：**回归护栏**（证明「输出没变」）
- ``tests/verify_fuzzy_algo_db.py``        ：**规则层复验**（连 DB，止步 ``build_rule_objects``）
- 本文件                                 ：**功能自检**（证明「算法能工作」）

参照系（关键：不引用任何被测实现函数）
--------------------------------------
本文件的期望值全部由**数学口径**手算，写在下面的常量与注释里：

1. 分桶：``bucket_centers([min,max], lvl)`` = 端点 + 等分位点
   （lvl=3 & [0,100] ⇒ [0, 50, 100]；lvl=5 & [0,1] ⇒ [0, .25, .5, .75, 1]）
2. 隶属度：高斯 ``μ(x, center) = exp(-0.5·((x-center)/σ)²)``，
   ``σ = span / (2·(lvl-1))`` ⇒ **输入落在桶中心时 μ 恰为 1.0**
3. 激活度 ``a = Π 前件隶属度``
4. 组内占比 ``w = (a·priority·spec_weight) / Σ同组``；
   特异级权重 ``spec_weight = 0.5^d``（d: 精确 0 / 部分 1 / 通用 2）
   ⇒ 特异级 1/2/3/4 对应 1.0 / 0.5 / 0.5 / 0.25
5. ``delta = 结论值 · w``；同参数多条 ⇒ 裸累加（= 组内加权平均）
6. ``recommended_value = current_value + delta``
   ``confidence = min(Σa / 规则数, 1)``（同参数命中规则的平均原始激活度）

⇒ 把输入值取在**桶中心**即可让激活度精确等于 1.0 ⇒ 推荐值可精确断言。

【注意】断言分两类，docstring 里用前缀区分：
- ``业务口径`` —— 期望值来自上面的数学口径（改实现 ⇒ 断言失败 = 暴露了变化）
- ``实现语义`` —— 钉住当前**已确认的行为**（如「档位衰减不改幅度、只改置信度」），
  变更前需业务确认，不是「数学上必须如此」

【注意】**零依赖不变量改用子进程验证**：原脚本跑在独立解释器里，可以直接断言
「``django`` 不在 ``sys.modules``」；但 pytest 是单进程会话（同一会话里别的测试模块
已经 ``django.setup()``），直接在进程内断言必然失败 ⇒ 该断言改为**新起子进程**
导入算法层后检查 —— 验证的仍然是同一件事（算法层不拖 Django / ORM 进来）。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_fuzzy_algo_offline.py -q
"""

import math
import os
import subprocess
import sys

import pytest

# =============================================================================
# 参照系常量（全部手算，不从被测实现里取）
# =============================================================================

MIN_ACTIVATION_THRESHOLD = 0.01001   # 过弱的规则不产出结论
SPEC_DECAY = 0.5                     # 特异级权重 ρ
GATE_TAU = 0.1353352832366127        # M-1 门控：未命中门限 = exp(-2)
BETA_MIN = 0.20                      # M-1 门控：归属不一致（档位不符）时的降权下限

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
    RuleProfile,
)

# 论域元数据（模拟 RuleKeyword 出库结果）
KW = {
    # 缺陷维度：5 档 [0,1] ⇒ 桶中心 [0, .25, .5, .75, 1]
    'SHORTSHOT': KeywordProfile(keyword='SHORTSHOT', lvl=5,
                                min_val=0.0, max_val=1.0, step=0.25),
    'UNDERSIZE': KeywordProfile(keyword='UNDERSIZE', lvl=5,
                                min_val=0.0, max_val=1.0, step=0.25),
    'DLUNDERSIZE1': KeywordProfile(keyword='DLUNDERSIZE1', lvl=5,
                                   min_val=0.0, max_val=1.0, step=0.25),
    # 工艺参数维度
    'IV0': KeywordProfile(keyword='IV0', lvl=3,
                          min_val=0.0, max_val=100.0, step=1.0),
    'inj_pres_1': KeywordProfile(keyword='inj_pres_1', lvl=5,
                                  min_val=0.0, max_val=200.0, step=5.0),
    'PP0': KeywordProfile(keyword='PP0', lvl=5,
                           min_val=0.0, max_val=140.0, step=5.0),
}


def _gauss(x, center, span, lvl):
    """高斯隶属度（参照系实现，不引用被测 memberships 模块）。

    σ = span / (2·(lvl-1))；μ(center) = 1.0。
    """
    sigma = span / (2.0 * (lvl - 1))
    return math.exp(-0.5 * ((x - center) / sigma) ** 2)


# 缺陷维度 SHORTSHOT（lvl=5, [0,1]）的桶中心：[0, .25, .5, .75, 1]
# 规则前件写 SHORTSHOT_low（桶 1 ⇒ 中心 0.25）
_SH_BUCKETS = [0.0, 0.25, 0.5, 0.75, 1.0]
_SH_LOW_CENTER = _SH_BUCKETS[1]      # 0.25
_SH_MEDIUM_CENTER = _SH_BUCKETS[2]   # 0.5
_SH_HIGH_CENTER = _SH_BUCKETS[3]     # 0.75

# 期望的激活度（手算）
_MU_SAME_LEVEL = 1.0                                   # 档位完全相同
_MU_ONE_BUCKET = _gauss(_SH_MEDIUM_CENTER, _SH_LOW_CENTER, 1.0, 5)   # 相邻档
_MU_TWO_BUCKET = _gauss(_SH_HIGH_CENTER, _SH_LOW_CENTER, 1.0, 5)     # 相隔两档


# =============================================================================
# 离线仓库（只负责「数据从哪来」；其余逻辑走生产实现）
# =============================================================================

class OfflineRepository:
    """完全离线的规则仓库（不 import ORM、不连 DB）。

    实现契约 ``library/contracts.py::AlgorithmResourceRepository`` 的两个方法：

    - ``get_rules``：**只做缺陷名闸门**（业务口径：规则库约定缺陷一定是第一个
      前件，``IF {defect}_{level} AND ...``）。
      【注意】档位**不过滤** —— 生产侧已把缺陷程度改成「算法输入」进推理网络，
      由隶属度表达「越严重越激进」（见 ``RuleService.match_defect_name`` docstring）。
      这里复刻的是**业务口径**（3 行、可对着规则串逐条核对），不是被测实现。
    - ``get_keywords_by_names``：返回内置元数据。

    其余三个方法**故意做成一旦被调用就炸** —— 让「引擎又自己分流了」这类
    架构回退立刻暴露，而不是静默走老路。
    """

    def __init__(self, rules=None, boom=False):
        self._rules = list(rules or [])
        self._boom = boom
        self.calls = []

    # —— 契约方法 ——
    def get_rules(self, context):
        self.calls.append(('get_rules', context.defect_name))
        if self._boom:
            raise RuntimeError('模拟规则库不可用')
        out = []
        for profile in self._rules:
            pre = parse_rule(profile.rule_description)['preconditions']
            if pre and pre[0].get('name') != context.defect_name:
                continue          # 缺陷名闸门：确定不该参与
            out.append(profile)
        return out

    def get_keywords_by_names(self, names):
        self.calls.append(('get_keywords_by_names', tuple(sorted(names))))
        wanted = set(names)
        return [kw for kw in KW.values() if kw.keyword in wanted]

    # —— 以下三个方法在「第 4 层 filter」下沉之后**不该再被引擎调用** ——
    def split_by_conclusion_kind(self, rules):
        raise AssertionError('引擎不应再自己分流（分流已下沉到第 4 层 filter）')

    def to_rule_array(self, rules):
        raise AssertionError('引擎不应再自己数组化规则（已下沉到第 4 层 filter）')

    def get_priority_array(self, rules):
        raise AssertionError('引擎不应再单独取优先级数组（优先级已随规则档案走）')


def rule(rule_str, specificity=4, priority=1.0, kind='numeric'):
    """构造规则档案（字段口径见 ``fuzzy_core/profiles.py::RuleProfile``）。"""
    return RuleProfile(
        rule_description=rule_str,
        priority=priority,
        conclusion_kind=kind,
        specificity=specificity,
        source_ref='offline:%s' % rule_str,
    )


def ctx(defect_name='SHORTSHOT', level='low', position=None, params=None):
    """构造引擎上下文（口径见 ``engine.recommend`` docstring）。"""
    defect = {'keyword_name': defect_name, 'level': level}
    if position is not None:
        defect['position'] = position
    return {
        'feedback': {'defects': [defect]},
        'process_parameter': dict(params or {}),
    }


def run(rules, context, boom=False):
    """跑一次引擎，返回推荐列表。"""
    repo = OfflineRepository(rules, boom=boom)
    engine = FuzzyEngine(repository=repo)
    # 缺陷选取在调用方收敛一次（引擎只读结果，不再各自挑缺陷）
    from process.services.optimize_chain.defect_selection import select_defect
    context['feedback'] = select_defect(context.get('feedback') or {})
    return engine.recommend(context), engine


GOOD_RULE = 'IF SHORTSHOT_low THEN IV0_add_2'
DIRTY_RULE = 'IF SHORTSHOT_low THEN IV0_add_2 AND IV0_add_low'


# =============================================================================
# S1 单规则命中 —— 推荐值精确等于「当前值 + 规则串写死的结论值」
# =============================================================================

def test_single_rule_hit_produces_exact_recommendation():
    """业务口径：单规则命中 ⇒ 推荐值 = 当前值 + 规则串写死的结论值。

    激活度 = 1.0（缺陷档位与规则档位相同、IV0 取桶中心 50.0）
    ⇒ 组内独占 ⇒ w = 1.0 ⇒ delta = 2.0 ⇒ 推荐值 = 52.0
    """
    recs, _ = run([rule(GOOD_RULE)], ctx(params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    r = recs[0]
    assert r.param_name == 'inj_spd_1', r.param_name
    assert r.current_value == pytest.approx(50.0)
    assert r.recommended_value == pytest.approx(52.0)
    assert r.direction == 'increase', r.direction
    assert r.confidence == pytest.approx(1.0)


# =============================================================================
# S2 档位相邻 —— 衰减但仍命中（幅度不变、置信度下降）
# =============================================================================

def test_adjacent_level_attenuates_confidence_only():
    """实现语义：档位相邻仍命中，**幅度不变**，只有置信度衰减。

    【注意】**M-1 门控后的口径变更**：
      档位相邻 ⇒ 归属不一致（competition = μ_used − μ_alt = exp(−2) − 1.0 < 0）
      ⇒ β_p = clamp(competition/ε, β_min, 1) = β_min = 0.20
      ⇒ `raw_activation`（= activation × β）= exp(−2) × 0.20
      ⇒ 置信度从 exp(−2) 降到 exp(−2) × β_min（**降幅 80%**，
         与评审文档预测的「不符权重降幅 80.00%」一致）。
    """
    recs, _ = run([rule(GOOD_RULE)], ctx(level='medium', params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    r = recs[0]
    assert r.recommended_value == pytest.approx(52.0)
    assert r.confidence == pytest.approx(_MU_ONE_BUCKET * BETA_MIN)
    # 相邻档 μ 恰好 = τ ⇒ 不满足「< τ」⇒ 仍命中
    assert _MU_ONE_BUCKET >= GATE_TAU, 'μ=%r τ=%r' % (_MU_ONE_BUCKET, GATE_TAU)


# =============================================================================
# S2b 疗效量化 —— 档位不符的规则被压到 β_min（错配残留降幅）
# =============================================================================

def test_mismatched_level_is_downweighted_to_beta_min():
    """业务口径：档位不符 + 档位相符 ⇒ 组内错配侧被压到 β_min。

    构造：同一输出参数组内放两条规则（工况 = medium）
      A: IF SHORTSHOT_low    THEN IV0_add_4   ← 档位不符（错配）
      B: IF SHORTSHOT_medium THEN IV0_add_6   ← 档位相符
      A: activation = exp(−2)，β = β_min ⇒ raw ∝ exp(−2)·0.20
      B: activation = 1.0，   β = 1     ⇒ raw ∝ 1.0
      ⇒ 组内占比 A ≈ 0.026354、B ≈ 0.973646
      ⇒ delta = 4×0.026354 + 6×0.973646 ≈ 5.947291 ⇒ 推荐值 ≈ 55.947291

    【注意】错配侧的贡献（单独看）：
      有 M-1：4 × 0.026354 = 0.105418
      无 M-1：4 × (exp(−2)/(1+exp(−2))) = 4 × 0.119184 = 0.476738
      ⇒ **错配残留降幅 ≈ 77.9%**（真实库口径为 80.00%，见评审文档；
         本构造只含 1 条错配 vs 1 条相符，故与全库口径略有差异）
    """
    mu_adj = _MU_ONE_BUCKET
    raw_mismatch = mu_adj * BETA_MIN
    share_mismatch = raw_mismatch / (1.0 + raw_mismatch)
    delta_mismatch = 4.0 * share_mismatch
    delta_match = 6.0 * (1.0 - share_mismatch)

    recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_4'),
                    rule('IF SHORTSHOT_medium THEN IV0_add_6')],
                   ctx(level='medium', params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    assert recs[0].recommended_value == pytest.approx(50.0 + delta_mismatch + delta_match)
    drop = 1.0 - (delta_mismatch / (4.0 * (mu_adj / (1.0 + mu_adj))))
    assert 0.70 <= drop <= 0.85, '实际降幅 %.4f' % drop


# =============================================================================
# S3 档位相隔两档 —— 过弱 ⇒ 整条规则被丢（空推荐）
# =============================================================================

def test_two_levels_apart_is_dropped():
    """业务口径：档位相隔两档 ⇒ 激活度过弱 ⇒ 整条规则被丢（空推荐）。"""
    recs, _ = run([rule(GOOD_RULE)], ctx(level='high', params={'inj_spd_1': 50.0}))

    assert len(recs) == 0, '实际 %d 条：%s' % (len(recs), recs)
    # 手算 μ(exp(-8)) 确实低于阈值
    assert _MU_TWO_BUCKET < MIN_ACTIVATION_THRESHOLD, (
        'μ=%r 阈值=%r' % (_MU_TWO_BUCKET, MIN_ACTIVATION_THRESHOLD)
    )


# =============================================================================
# S4 缺陷名不匹配 —— 规则被闸门拦下
# =============================================================================

def test_defect_name_gate_blocks_foreign_rules():
    """业务口径：缺陷名不匹配 ⇒ 规则被闸门拦下（空推荐）。"""
    recs, _ = run([rule(GOOD_RULE)], ctx(defect_name='FLASH', params={'inj_spd_1': 50.0}))

    assert len(recs) == 0, '实际 %d 条' % len(recs)


# =============================================================================
# S5 同参数多条规则 —— 组内归一化 ⇒ 加权平均
# =============================================================================

def test_multiple_rules_for_same_param_are_averaged():
    """业务口径：同参数多规则在组内归一化 ⇒ 加权平均。

    两条 raw 相同（激活度/priority/特异级全同）⇒ 各占 0.5
    ⇒ delta = 4×0.5 + 6×0.5 = 5.0 ⇒ 推荐值 55.0
    """
    recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_4'),
                   rule('IF SHORTSHOT_low THEN IV0_add_6')],
                  ctx(params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    r = recs[0]
    assert r.recommended_value == pytest.approx(55.0)
    assert r.confidence == pytest.approx(1.0)


# =============================================================================
# S6 特异级加权 —— 手算 ρ=0.5 的组内占比
# =============================================================================

def test_specificity_weighting_applies():
    """业务口径：特异级权重 ρ=0.5 ⇒ 组内占比按 0.5^d 加权。

    spec 权重 = 0.5^d（d=0/1/1/2）⇒ [1.0, 0.5, 0.5, 0.25]，和 = 2.25
      占比 = [4/9, 2/9, 2/9, 1/9]
      delta = 2×4/9 + 4×2/9 + 6×2/9 + 8×1/9 = (8+8+12+8)/9 = 4.0
    """
    spec_rules = [
        rule('IF SHORTSHOT_low THEN IV0_add_2', specificity=1),
        rule('IF SHORTSHOT_low THEN IV0_add_4', specificity=2),
        rule('IF SHORTSHOT_low THEN IV0_add_6', specificity=3),
        rule('IF SHORTSHOT_low THEN IV0_add_8', specificity=4),
    ]

    recs, _ = run(spec_rules, ctx(params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    weights = [SPEC_DECAY ** 0, SPEC_DECAY ** 1, SPEC_DECAY ** 1, SPEC_DECAY ** 2]
    total = sum(weights)
    expect_delta = sum(c * w / total for c, w in zip((2, 4, 6, 8), weights))
    assert recs[0].recommended_value == pytest.approx(50.0 + expect_delta)


# =============================================================================
# S7 跨参数 —— 各自独占组，互不稀释
# =============================================================================

def test_cross_param_groups_do_not_dilute():
    """业务口径：跨参数的规则各自独占组，互不稀释。

    【注意】规则里的参数名用**算法命名空间**（``IV0`` / ``IP0``）⇒ 与真实规则库
    一致；context 里的工艺参数用**业务字段名**（``inj_spd_1`` / ``inj_pres_1``）
    ⇒ 引擎内部自己翻译（算法名不外传、也不进 context）。
    """
    recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_4'),
                    rule('IF SHORTSHOT_low THEN IP0_add_10')],
                   ctx(params={'inj_spd_1': 50.0, 'inj_pres_1': 100.0}))

    assert len(recs) == 2, '实际 %d 条' % len(recs)
    by_param = {r.param_name: r for r in recs}
    assert by_param['inj_spd_1'].recommended_value == pytest.approx(54.0)
    assert by_param['inj_pres_1'].recommended_value == pytest.approx(110.0)


# =============================================================================
# S8 提示层（文本建议）—— 不产出数值
# =============================================================================

def test_advisory_layer_produces_no_numeric_value():
    """业务口径：提示层产出的是文本建议，不给数值。"""
    recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_adjust_请检查锁模力是否不合理',
                        kind='advisory')],
                   ctx(params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    r = recs[0]
    assert r.recommended_value is None, repr(r.recommended_value)
    assert r.direction == 'check', r.direction
    assert r.source == 'fuzzy.check', r.source


# =============================================================================
# S9 缺陷位置维度（DL 前缀）—— 走缺陷通道，能命中
# =============================================================================

def test_defect_position_dimension_participates():
    """业务口径：缺陷位置维度参与推理并命中。

    UNDERSIZE: 档位 low(桶1 中心 .25) 对前件 low(桶1) ⇒ μ=1
    DLUNDERSIZE1: 引擎取 high 档(桶3 中心 .75) 对前件 high(桶3) ⇒ μ=1
      ⇒ 激活度 = 1.0 ⇒ delta = 5.0 ⇒ 推荐值 40.0
    """
    recs, _ = run([rule('IF UNDERSIZE_low AND DLUNDERSIZE1_high THEN PP0_add_5')],
                  ctx(defect_name='UNDERSIZE', level='low', position='DLUNDERSIZE1',
                      params={'hold_pres_1': 35.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    r = recs[0]
    assert r.recommended_value == pytest.approx(40.0)
    assert r.confidence == pytest.approx(1.0)


# =============================================================================
# S10~S12 门控三条路径（分界是「档案是否进了 net」，不是「有没有值」）
# =============================================================================

def test_non_judgeable_precondition_is_not_a_gate():
    """业务口径：前件是**不可判级**词（worse）⇒ 该前件不作门控 ⇒ 规则仍命中。"""
    recs, _ = run([rule('IF SHORTSHOT_low AND IV0_worse THEN IV0_add_2')],
                   ctx(params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    assert recs[0].recommended_value == pytest.approx(52.0)


def test_unknown_keyword_profile_is_not_a_gate():
    """业务口径：档案（RuleKeyword）不在 ⇒ 该前件不作门控 ⇒ 规则仍命中。"""
    recs, _ = run([rule('IF SHORTSHOT_low AND ZZUNKNOWN_low THEN IV0_add_2')],
                   ctx(params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    assert recs[0].recommended_value == pytest.approx(52.0)


def test_profile_present_but_no_value_drops_rule():
    """业务口径：档案在（结论参数的元数据会被拉取）但**输入里没值**
    ⇒ membership 兜底 ⇒ 激活度低于阈值 ⇒ **整条规则被丢**。"""
    recs, _ = run([rule('IF SHORTSHOT_low AND IV0_low THEN IV0_add_2')],
                   ctx(params={}))          # 故意不给注射速度

    assert len(recs) == 0, '实际 %d 条：%s' % (len(recs), recs)


# =============================================================================
# S13 脏规则条目级隔离（一条坏规则只废掉自己）
# =============================================================================

def test_dirty_rule_is_isolated():
    """业务口径：一条脏规则只废掉自己，不拖垮整层。"""
    recs, engine = run([rule(GOOD_RULE), rule(DIRTY_RULE)], ctx(params={'inj_spd_1': 50.0}))

    assert len(recs) == 1, '实际 %d 条' % len(recs)
    assert bool(engine._diagnostics), '实际 diagnostics=%s' % (engine._diagnostics,)
    assert engine._diagnostics[0]['skipped'][0]['rule'] == DIRTY_RULE


# =============================================================================
# S14 规则库异常 ⇒ 降级为空推荐，不冒泡
# =============================================================================

def test_repository_failure_degrades_to_empty():
    """业务口径：规则库异常 ⇒ 降级为空推荐，**不冒泡**。"""
    try:
        recs, _ = run([rule(GOOD_RULE)], ctx(params={'inj_spd_1': 50.0}), boom=True)
    except Exception as exc:  # noqa: BLE001 - 这里就是要断言「不冒泡」
        pytest.fail('规则库异常冒泡了: %s' % exc)
    assert recs == [], '实际 %s' % (recs,)


# =============================================================================
# S15 零依赖 —— 算法层不拖 Django / ORM 进来（子进程验证）
# =============================================================================

def test_algorithm_layer_has_no_django_dependency():
    """业务口径（零依赖不变量）：算法层脱离 Django 也能 import。

    【注意】必须在**子进程**里验证：pytest 是单进程会话，同会话内别的测试模块
    已经 ``django.setup()`` ⇒ 进程内直接断言 ``'django' not in sys.modules``
    必然失败。新起解释器导入算法层后再检查，验证的是同一件事。
    """
    code = (
        "import sys;"
        "from process.algorithms.fuzzy.engine import FuzzyEngine;"
        "from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule;"
        "from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile, RuleProfile;"
        "from process.services.optimize_chain.defect_selection import select_defect;"
        "assert 'django' not in sys.modules, 'django 被加载了';"
        "assert 'process.models' not in sys.modules, 'process.models 被加载了';"
        "print('OK')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=_BACKEND, capture_output=True, text=True,
    )

    assert proc.returncode == 0, proc.stderr or proc.stdout


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_fuzzy_algo_offline``。"""
    import inspect

    cases = [
        fn for name, fn in sorted(globals().items())
        if name.startswith('test_') and inspect.isfunction(fn)
    ]
    failed = []
    for fn in cases:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - 独立跑法需要汇总全部失败
            print(f'[FAIL] {fn.__name__}: {exc}')
            failed.append(fn.__name__)
    print('\n' + '=' * 60)
    if failed:
        print(f'[FAIL] {len(failed)}/{len(cases)} 个用例失败：{failed}')
        return 1
    print(f'[PASS] {len(cases)}/{len(cases)} 个用例通过')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())