"""
模糊推理算法「脱离前端 + 脱离数据库 + 脱离 Django」的独立自检流程（L1 离线层）。

定位
----
证明模糊推理算法**不依赖前端页面、不依赖数据库**也能完整跑通，
并对「推荐值 / 置信度 / 方向」给出**精确可断言**的结果。

与既有脚本的分工
----------------
- ``tests/fuzzy_kernel/_snapshot_core.py``  ：**回归护栏**（证明「输出没变」）
- ``tests/_verify_e2e_db.py``  ：**规则层复验**（连 DB，止步 ``build_rule_objects``）
- 本脚本                          ：**功能自检**（证明「算法能工作」）
  —— 有独立参照系 + PASS/FAIL 逐项 + 非零 exit code

参照系（关键：不引用任何被测实现函数）
--------------------------------------
本脚本的期望值全部由**数学口径**手算，写在下面的常量与注释里：

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

⚠️ 断言分两类，脚本里用前缀区分：
- ``业务口径`` —— 期望值来自上面的数学口径（改实现 ⇒ 断言失败 = 暴露了变化）
- ``实现语义`` —— 钉住当前**已确认的行为**（如「档位衰减不改幅度、只改置信度」），
  变更前需业务确认，不是「数学上必须如此」

运行：cd backend; ..\\.venv\\Scripts\\python.exe tests\\verify_fuzzy_algo_offline.py
"""

import math
import os
import sys

# ⚠️ 本脚本**刻意不 import django、不设 DJANGO_SETTINGS_MODULE、不 django.setup()**
#    —— 「脱离 Django 运行」是这一层的核心卖点，必须由下面的 S16 自证。
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
    RuleProfile,
)

# =============================================================================
# 参照系常量（全部手算，不从被测实现里取）
# =============================================================================

MIN_ACTIVATION_THRESHOLD = 0.01001   # 过弱的规则不产出结论
SPEC_DECAY = 0.5                     # 特异级权重 ρ
GATE_TAU = 0.1353352832366127        # M-1 门控：未命中门限 = exp(-2)
BETA_MIN = 0.20                      # M-1 门控：归属不一致（档位不符）时的降权下限

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
      ⚠️ 档位**不过滤** —— 生产侧已把缺陷程度改成「算法输入」进推理网络，
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
        'feedback': {'defect': [defect]},
        'process_parameter': dict(params or {}),
    }


def run(rules, context, boom=False):
    """跑一次引擎，返回推荐列表。"""
    repo = OfflineRepository(rules, boom=boom)
    engine = FuzzyEngine(repository=repo)
    return engine.recommend(context), engine


# =============================================================================
# 断言工具
# =============================================================================

failures = []
_passed = 0


def check(name, cond, detail=''):
    global _passed
    if cond:
        _passed += 1
        print('[PASS] %s' % name)
    else:
        print('[FAIL] %s  %s' % (name, detail))
        failures.append(name)


def check_float(name, got, want, tol=1e-9):
    ok = got is not None and abs(got - want) <= tol
    check(name, ok, '期望 %r，实际 %r' % (want, got))


# =============================================================================
# S1 单规则命中 —— 推荐值精确等于「当前值 + 规则串写死的结论值」
# =============================================================================
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_2')],
               ctx(params={'IV0': 50.0}))
check('[业务口径] S1 单规则命中产出 1 条推荐', len(recs) == 1, '实际 %d 条' % len(recs))
if recs:
    r = recs[0]
    check('[业务口径] S1 推荐参数是 IV0', r.param_name == 'IV0', r.param_name)
    check_float('[业务口径] S1 当前值 = 50.0', r.current_value, 50.0)
    # 激活度 = 1.0（缺陷档位与规则档位相同、IV0 取桶中心 50.0）
    #   ⇒ 组内独占 ⇒ w = 1.0 ⇒ delta = 2.0 ⇒ 推荐值 = 52.0
    check_float('[业务口径] S1 推荐值 = 50.0 + 2.0 = 52.0', r.recommended_value, 52.0)
    check('[业务口径] S1 方向 = increase', r.direction == 'increase', r.direction)
    check_float('[业务口径] S1 置信度 = 1.0（完美命中）', r.confidence, 1.0)


# =============================================================================
# S2 档位相邻 —— 衰减但仍命中（幅度不变、置信度下降）
# =============================================================================
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_2')],
               ctx(level='medium', params={'IV0': 50.0}))
check('[实现语义] S2 档位相邻仍产出 1 条推荐', len(recs) == 1, '实际 %d 条' % len(recs))
if recs:
    r = recs[0]
    # μ(medium 中心 0.5, low 中心 0.25) = exp(-0.5·((0.25)/0.125)²) = exp(-2)
    check_float('[实现语义] S2 幅度不变（delta 不含激活度）⇒ 推荐值仍 52.0',
                r.recommended_value, 52.0)
    # ⚠️ **M-1 落地后的口径变更**（2026-10-28，批 M-1）：
    #   档位相邻 ⇒ 归属不一致（competition = μ_used − μ_alt = exp(−2) − 1.0 < 0）
    #   ⇒ β_p = clamp(competition/ε, β_min, 1) = β_min = 0.20
    #   ⇒ `raw_activation`（= activation × β）= exp(−2) × 0.20
    #   ⇒ 置信度从 exp(−2) 降到 exp(−2) × β_min（**降幅 80%**，
    #      与 review §25.3 预测的「不符权重降幅 80.00%」一致）。
    check_float('[实现语义] S2 置信度衰减为 exp(-2)×β_min（M-1 降权）',
                r.confidence, _MU_ONE_BUCKET * BETA_MIN)
    check('[实现语义] S2 相邻档 μ 恰好 = τ ⇒ 不满足「< τ」⇒ 仍命中',
          _MU_ONE_BUCKET >= GATE_TAU,
          'μ=%r τ=%r' % (_MU_ONE_BUCKET, GATE_TAU))


# =============================================================================
# S2b 疗效量化 —— 档位不符的规则被压到 β_min（错配残留降幅）
# =============================================================================
# 构造：同一输出参数组内放两条规则（工况 = medium）
#   A: IF SHORTSHOT_low    THEN IV0_add_4   ← 档位不符（错配）
#   B: IF SHORTSHOT_medium THEN IV0_add_6   ← 档位相符
#   A: activation = exp(−2)，β = β_min ⇒ raw ∝ exp(−2)·0.20
#   B: activation = 1.0，   β = 1     ⇒ raw ∝ 1.0
#   ⇒ 组内占比 A ≈ 0.026354、B ≈ 0.973646
#   ⇒ delta = 4×0.026354 + 6×0.973646 ≈ 5.947291 ⇒ 推荐值 ≈ 55.947291
#
# ⚠️ 错配侧的贡献（单独看）：
#   有 M-1：4 × 0.026354 = 0.105418
#   无 M-1：4 × (exp(−2)/(1+exp(−2))) = 4 × 0.119184 = 0.476738
#   ⇒ **错配残留降幅 ≈ 77.9%**（真实库口径为 80.00%，见 review §25.3；
#      本构造只含 1 条错配 vs 1 条相符，故与全库口径略有差异）
_MU_ADJ = _MU_ONE_BUCKET
_RAW_MISMATCH = _MU_ADJ * BETA_MIN
_SHARE_MISMATCH = _RAW_MISMATCH / (1.0 + _RAW_MISMATCH)
_DELTA_MISMATCH = 4.0 * _SHARE_MISMATCH
_DELTA_MATCH = 6.0 * (1.0 - _SHARE_MISMATCH)
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_4'),
                rule('IF SHORTSHOT_medium THEN IV0_add_6')],
               ctx(level='medium', params={'IV0': 50.0}))
check('[业务口径] S2b 档位不符 + 档位相符 ⇒ 产出 1 条推荐',
      len(recs) == 1, '实际 %d 条' % len(recs))
if recs:
    check_float('[业务口径] S2b 错配规则压到 β_min 后推荐值 = 55.947291',
                recs[0].recommended_value, 50.0 + _DELTA_MISMATCH + _DELTA_MATCH)
    _DROP = 1.0 - (_DELTA_MISMATCH / (4.0 * (_MU_ADJ / (1.0 + _MU_ADJ))))
    check('[业务口径] S2b 错配残留降幅 ≈ 78%（M-1 疗效生效）',
          0.70 <= _DROP <= 0.85, '实际降幅 %.4f' % _DROP)


# =============================================================================
# S3 档位相隔两档 —— 过弱 ⇒ 整条规则被丢（空推荐）
# =============================================================================
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_2')],
               ctx(level='high', params={'IV0': 50.0}))
check('[业务口径] S3 档位相隔两档 ⇒ 激活度过弱 ⇒ 空推荐', len(recs) == 0,
      '实际 %d 条：%s' % (len(recs), recs))
check('[业务口径] S3 手算 μ(exp(-8)) 确实低于阈值',
      _MU_TWO_BUCKET < MIN_ACTIVATION_THRESHOLD,
      'μ=%r 阈值=%r' % (_MU_TWO_BUCKET, MIN_ACTIVATION_THRESHOLD))


# =============================================================================
# S4 缺陷名不匹配 —— 规则被闸门拦下
# =============================================================================
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_2')],
               ctx(defect_name='FLASH', params={'IV0': 50.0}))
check('[业务口径] S4 缺陷名不匹配 ⇒ 空推荐', len(recs) == 0, '实际 %d 条' % len(recs))


# =============================================================================
# S5 同参数多条规则 —— 组内归一化 ⇒ 加权平均
# =============================================================================
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_4'),
                rule('IF SHORTSHOT_low THEN IV0_add_6')],
               ctx(params={'IV0': 50.0}))
check('[业务口径] S5 同参数多规则产出 1 条推荐', len(recs) == 1, '实际 %d 条' % len(recs))
if recs:
    r = recs[0]
    # 两条 raw 相同（激活度/priority/特异级全同）⇒ 各占 0.5
    #   ⇒ delta = 4×0.5 + 6×0.5 = 5.0 ⇒ 推荐值 55.0
    check_float('[业务口径] S5 推荐值 = 50.0 + (4+6)/2 = 55.0', r.recommended_value, 55.0)
    check_float('[业务口径] S5 置信度 = 平均激活度 = 1.0', r.confidence, 1.0)


# =============================================================================
# S6 特异级加权 —— 手算 ρ=0.5 的组内占比
# =============================================================================
_spec_rules = [
    rule('IF SHORTSHOT_low THEN IV0_add_2', specificity=1),
    rule('IF SHORTSHOT_low THEN IV0_add_4', specificity=2),
    rule('IF SHORTSHOT_low THEN IV0_add_6', specificity=3),
    rule('IF SHORTSHOT_low THEN IV0_add_8', specificity=4),
]
recs, _ = run(_spec_rules, ctx(params={'IV0': 50.0}))
check('[业务口径] S6 特异级加权产出 1 条推荐', len(recs) == 1, '实际 %d 条' % len(recs))
if recs:
    r = recs[0]
    # spec 权重 = 0.5^d（d=0/1/1/2）⇒ [1.0, 0.5, 0.5, 0.25]，和 = 2.25
    #   占比 = [4/9, 2/9, 2/9, 1/9]
    #   delta = 2×4/9 + 4×2/9 + 6×2/9 + 8×1/9 = (8+8+12+8)/9 = 4.0
    _w = [SPEC_DECAY ** 0, SPEC_DECAY ** 1, SPEC_DECAY ** 1, SPEC_DECAY ** 2]
    _sum = sum(_w)
    _expect_delta = sum(c * w / _sum for c, w in zip((2, 4, 6, 8), _w))
    check_float('[业务口径] S6 推荐值 = 50.0 + 4.0 = 54.0',
                r.recommended_value, 50.0 + _expect_delta)


# =============================================================================
# S7 跨参数 —— 各自独占组，互不稀释
# =============================================================================
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_add_4'),
                rule('IF SHORTSHOT_low THEN inj_pres_1_add_10')],
               ctx(params={'IV0': 50.0, 'inj_pres_1': 100.0}))
check('[业务口径] S7 跨参数产出 2 条推荐', len(recs) == 2, '实际 %d 条' % len(recs))
_by_param = {r.param_name: r for r in recs}
if 'IV0' in _by_param and 'inj_pres_1' in _by_param:
    check_float('[业务口径] S7 IV0 推荐值 = 54.0（不被另一参数稀释）',
                _by_param['IV0'].recommended_value, 54.0)
    check_float('[业务口径] S7 inj_pres_1 推荐值 = 110.0',
                _by_param['inj_pres_1'].recommended_value, 110.0)


# =============================================================================
# S8 提示层（文本建议）—— 不产出数值
# =============================================================================
recs, _ = run([rule('IF SHORTSHOT_low THEN IV0_adjust_请检查锁模力是否不合理',
                    kind='advisory')],
               ctx(params={'IV0': 50.0}))
check('[业务口径] S8 提示层产出 1 条建议', len(recs) == 1, '实际 %d 条' % len(recs))
if recs:
    r = recs[0]
    check('[业务口径] S8 建议不给数值（recommended_value 为 None）',
          r.recommended_value is None, repr(r.recommended_value))
    check('[业务口径] S8 建议方向为 check', r.direction == 'check', r.direction)
    check('[业务口径] S8 建议来源为 fuzzy.check', r.source == 'fuzzy.check', r.source)


# =============================================================================
# S9 缺陷位置维度（DL 前缀）—— 走缺陷通道，能命中
# =============================================================================
recs, _ = run([rule('IF UNDERSIZE_low AND DLUNDERSIZE1_high THEN PP0_add_5')],
               ctx(defect_name='UNDERSIZE', level='low', position='DLUNDERSIZE1',
                   params={'PP0': 35.0}))
check('[业务口径] S9 缺陷位置维度参与推理并命中', len(recs) == 1, '实际 %d 条' % len(recs))
if recs:
    r = recs[0]
    # UNDERSIZE: 档位 low(桶1 中心 .25) 对前件 low(桶1) ⇒ μ=1
    # DLUNDERSIZE1: 引擎取 high 档(桶3 中心 .75) 对前件 high(桶3) ⇒ μ=1
    #   ⇒ 激活度 = 1.0 ⇒ delta = 5.0 ⇒ 推荐值 40.0
    check_float('[业务口径] S9 PP0 推荐值 = 35.0 + 5.0 = 40.0', r.recommended_value, 40.0)
    check_float('[业务口径] S9 置信度 = 1.0', r.confidence, 1.0)


# =============================================================================
# S10~S12 门控三条路径（分界是「档案是否进了 net」，不是「有没有值」）
# =============================================================================

# S10 路径①：前件是**不可判级**词（worse）⇒ 该前件不作门控 ⇒ 规则仍命中
recs, _ = run([rule('IF SHORTSHOT_low AND IV0_worse THEN IV0_add_2')],
               ctx(params={'IV0': 50.0}))
check('[业务口径] S10 不可判级前件不作门控 ⇒ 规则仍命中', len(recs) == 1,
      '实际 %d 条' % len(recs))
if recs:
    check_float('[业务口径] S10 推荐值仍 = 52.0', recs[0].recommended_value, 52.0)

# S11 路径②：档案（RuleKeyword）不在 ⇒ 该前件不作门控 ⇒ 规则仍命中
recs, _ = run([rule('IF SHORTSHOT_low AND ZZUNKNOWN_low THEN IV0_add_2')],
               ctx(params={'IV0': 50.0}))
check('[业务口径] S11 档案不在 ⇒ 前件不作门控 ⇒ 规则仍命中', len(recs) == 1,
      '实际 %d 条' % len(recs))
if recs:
    check_float('[业务口径] S11 推荐值仍 = 52.0', recs[0].recommended_value, 52.0)

# S12 路径③：档案在（IV0 是结论参数，元数据会被拉取）但**输入里没值**
#      ⇒ membership 兜底 ⇒ 激活度低于阈值 ⇒ **整条规则被丢**
recs, _ = run([rule('IF SHORTSHOT_low AND IV0_low THEN IV0_add_2')],
               ctx(params={}))          # 故意不给 IV0
check('[业务口径] S12 档案在但输入无值 ⇒ 整条规则被丢 ⇒ 空推荐', len(recs) == 0,
      '实际 %d 条：%s' % (len(recs), recs))


# =============================================================================
# S13 脏规则条目级隔离（一条坏规则只废掉自己）
# =============================================================================
GOOD_RULE = 'IF SHORTSHOT_low THEN IV0_add_2'
DIRTY_RULE = 'IF SHORTSHOT_low THEN IV0_add_2 AND IV0_add_low'
recs, engine = run([rule(GOOD_RULE), rule(DIRTY_RULE)], ctx(params={'IV0': 50.0}))
check('[业务口径] S13 脏规则未拖垮整层', len(recs) == 1, '实际 %d 条' % len(recs))
check('[业务口径] S13 脏规则被记入诊断清单',
      bool(engine._diagnostics)
      and engine._diagnostics[0]['skipped'][0]['rule'] == DIRTY_RULE,
      '实际 diagnostics=%s' % (engine._diagnostics,))


# =============================================================================
# S14 规则库异常 ⇒ 降级为空推荐，不冒泡
# =============================================================================
try:
    recs, _ = run([rule(GOOD_RULE)], ctx(params={'IV0': 50.0}), boom=True)
    check('[业务口径] S14 规则库异常降级为空推荐（不冒泡）', recs == [],
          '实际 %s' % (recs,))
except Exception as exc:  # noqa: BLE001
    check('[业务口径] S14 规则库异常降级为空推荐（不冒泡）', False, '冒泡了: %s' % exc)


# =============================================================================
# S15 零依赖 —— 本脚本全程未 import django
# =============================================================================
check('[业务口径] S15 全程未加载 Django ORM', 'django' not in sys.modules,
      'sys.modules 里出现了 django')
check('[业务口径] S15 全程未加载 process.models', 'process.models' not in sys.modules,
      'sys.modules 里出现了 process.models')


# =============================================================================
# 汇总
# =============================================================================
print()
print('=' * 68)
if failures:
    print('[FAIL] %d 项未通过（共 %d 项）：' % (len(failures), _passed + len(failures)))
    for name in failures:
        print('     [FAIL] %s' % name)
    sys.exit(1)
print('[PASS] 模糊推理算法离线自检全部通过（%d 项）' % _passed)
sys.exit(0)
