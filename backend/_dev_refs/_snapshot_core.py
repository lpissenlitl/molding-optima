"""快照生成器：把「数值面 + 推理链路面 + 反模糊化面」固化成 JSON。

**跨轮次通用工具**（E24 起固化）：用于「改前副本 / 改后」同脚本对跑的
等价性证明 —— 同一个脚本在两个 backend 副本里各跑一次，输出 JSON 必须逐条相等。

用法（必须在某个 backend 副本根目录下运行）：
    ..\\.venv\\Scripts\\python.exe _dev_refs\\_snapshot_core.py <输出json路径>

设计要点：
  - 覆盖 gauss_mf 的**全部**数值路径：所有档位数 × 所有论域 × 所有桶 × 21 个采样点
  - 覆盖完整推理链路：FakeRepository 注入 → FuzzyEngine.recommend() 的最终推荐
  - 覆盖 centroid / defuzz
  - 全部用 repr(float) 序列化，浮点尾数可逐位比对
"""
import inspect  # noqa: E402
import json
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BACKEND)
sys.path.insert(0, BACKEND)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django  # noqa: E402

django.setup()

import numpy as np  # noqa: E402

from process.algorithms.fuzzy.fuzzy_core.models.features import FuzzyFeature  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.defuzz import (  # noqa: E402
    centroid,
    defuzz,
)
from process.algorithms.fuzzy.fuzzy_core.memberships import (  # noqa: E402
    gaussian_mf as gauss_mf,     # 新签名 (x, center, width)：width = 2σ
    triangular_mf as tri_mf,     # 新签名 (x, center, width)
)
from process.algorithms.fuzzy.fuzzy_core.models.rules import NumTskRule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import RuleProfile  # noqa: E402
from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.library.rules import RuleService  # noqa: E402

OUT = sys.argv[1]
snap = {}

# ⚠️ 口径适配：E24-4 删掉了 `f_name` 位置参数（只写不读的假契约），
#    而基线副本跑的是**改前**版本（签名多一个 f_name）。
#    这里按实际签名选择调用形式 —— 被测对象的数值产出必须两版完全一致，
#    该一致性由「三方对拍」单独断言。
_FF_PARAMS = inspect.signature(FuzzyFeature.__init__).parameters
_HAS_F_NAME = 'f_name' in _FF_PARAMS


def _make_feature(interval, lvl):
    if _HAS_F_NAME:
        return FuzzyFeature('X', list(interval), f_level=lvl)
    return FuzzyFeature(list(interval), f_level=lvl)


def put(key, value):
    snap[key] = value


# ---------------- 1. gauss 隶属度数值面（推理链路真正依赖的函数） ----------------
gauss_face = {}
for lvl in (3, 5, 7, 9):
    for interval in ([0.0, 100.0], [-50.0, 50.0], [0.0, 1.0], [10.0, 30.0]):
        feat = _make_feature(interval, lvl)
        for x in np.linspace(interval[0], interval[1], 21):
            for d in range(lvl):
                k = 'lvl%d|%.4f|%.4f|%d|%.6f' % (lvl, interval[0], interval[1], d, x)
                gauss_face[k] = repr(float(feat.get_value_by_level(float(x), d)))
        # 论域参数本身（桶中心 / sigma）也要进快照
        for d in range(lvl):
            put('params|lvl%d|%.4f|%.4f|%d' % (lvl, interval[0], interval[1], d),
                [repr(v) for v in feat.membership_dict['degree_%d' % d]])
put('gauss_face_count', len(gauss_face))
put('gauss_face', gauss_face)

# ---------------- 2. tri_mf 数值面（三角隶属度本体，非 features 的 tri 分支） ----------
tri_face = {}
for a, b, c in ((0.0, 5.0, 10.0), (-10.0, 0.0, 10.0), (0.0, 0.0, 1.0)):
    for x in np.linspace(a - 1, c + 1, 21):
        # 旧 tri_mf(x, a, b, c) = 顶点 b / 底边 [a, c]
        # ⇒ 新签名 (x, center, width)：center = b，width = c - a
        tri_face['%.4f|%.4f|%.4f|%.6f' % (a, b, c, x)] = repr(
            float(tri_mf(float(x), b, c - a)))
put('tri_face_count', len(tri_face))
put('tri_face', tri_face)

# ---------------- 3. 反模糊化面 ----------------
defz = {}
for mode in ('centroid',):
    for a, b, c in ((0.0, 5.0, 10.0), (0.0, 1.0, 2.0)):
        xs = np.linspace(a, c, 41)
        for peak in (0.0, 0.5, 1.0):
            # 旧 gauss_mf(xs, mean, σ) ⇒ 新签名 (x, center, width)：width = 2σ
            mfx = gauss_mf(xs, b, (c - a) / 2.0) * peak
            tag = '%s|%.4f|%.4f|%.4f|%.2f' % (mode, a, b, c, peak)
            ctag = 'direct_centroid|%.4f|%.4f|%.4f|%.2f' % (a, b, c, peak)
            try:
                defz[tag] = repr(float(defuzz(xs, mfx, mode=mode)))
            except Exception as e:
                defz[tag] = 'RAISE %s: %s' % (type(e).__name__, e)
            try:
                defz[ctag] = repr(float(centroid(xs, mfx)))
            except Exception as e:
                defz[ctag] = 'RAISE %s: %s' % (type(e).__name__, e)
put('defuzz_face_count', len(defz))
put('defuzz_face', defz)

# ---------------- 4. 完整推理链路 ----------------
class Kw(dict):
    """既能当 dict 用（`kw['keyword']`，旧内核契约），也能当契约对象用
    （`kw.keyword`，新内核契约）。

    本快照要在**改造前 / 改造后**跑**同一份脚本** ⇒ 仓库返回值必须同时
    满足两侧的读法。
    """

    def __init__(self, keyword, lvl, min_val, max_val, step):
        super().__init__(keyword=keyword, lvl=lvl, min_val=min_val,
                         max_val=max_val, step=step)

    @property
    def keyword(self):
        return self['keyword']

    @property
    def lvl(self):
        return self['lvl']

    @property
    def min_val(self):
        return self['min_val']

    @property
    def max_val(self):
        return self['max_val']

    @property
    def step(self):
        return self['step']


KEYWORDS = [
    Kw('IV0', 3, 0.0, 100.0, 1.0),
    Kw('inj_pres_1', 5, 0.0, 200.0, 5.0),
    Kw('SHORTSHOT', 3, 0.0, 10.0, 1.0),
]


class FakeRepo:
    """完全离线的规则仓库（不 import ORM，不连 DB）。"""

    def __init__(self, rules, boom=False):
        self._rules = rules
        self._boom = boom
        self.calls = []

    def get_rules(self, context):
        self.calls.append(('get_rules', context.defect_name))
        if self._boom:
            raise RuntimeError('模拟 DB 不可用')
        return self._rules

    def split_by_conclusion_kind(self, rules):
        return {'numeric': list(rules), 'advisory': []}

    def to_rule_array(self, rules):
        return [{'rule_description': r.rule_description} for r in rules]

    def get_priority_array(self, rules):
        return [r.priority for r in rules]

    def get_keywords_by_names(self, names):
        self.calls.append(('get_keywords_by_names', tuple(sorted(names))))
        return [k for k in KEYWORDS if k['keyword'] in set(names)]


def mk(rule_str, priority=1.0, kind=None):
    """构造规则档案。

    `kind=None` 时按**结论形态自动判定**（与来源层 `RuleService` 同一口径）——
    之前硬编码 'numeric' 是失真：`IF IV0_low THEN IV0_add_low` 明明是 advisory，
    硬编码会让它进数值层，与真实链路不符。
    """
    if kind is None:
        kind = RuleService.classify_conclusion_kind(rule_str)
    return RuleProfile(rule_description=rule_str, specificity=4,
                       conclusion_kind=kind, priority=priority)


SCENARIOS = [
    ('basic', ['IF SHORTSHOT_low AND IV0_low THEN IV0_add_2']),
    ('multi', [
        'IF inj_pres_1_high THEN inj_pres_1_add_5',
        'IF inj_pres_1_low AND IV0_medium THEN IV0_add_10',
        'IF SHORTSHOT_high THEN IV0_add_3',
        'IF IV0_low THEN IV0_add_low',
    ]),
    ('five_level', [
        'IF inj_pres_1_very_low THEN inj_pres_1_add_5',
        'IF inj_pres_1_low THEN inj_pres_1_add_5',
        'IF inj_pres_1_medium THEN inj_pres_1_add_5',
        'IF inj_pres_1_high THEN inj_pres_1_add_5',
        'IF inj_pres_1_very_high THEN inj_pres_1_add_5',
    ]),
    ('level_number', [
        'IF inj_pres_1_level1 THEN inj_pres_1_add_5',
        'IF inj_pres_1_level3 THEN inj_pres_1_add_5',
        'IF inj_pres_1_level5 THEN inj_pres_1_add_5',
    ]),
    ('mixed', [
        'IF SHORTSHOT_low AND IV0_low THEN IV0_add_2',
        'IF SHORTSHOT_high THEN inj_pres_1_add_5',
    ]),
    # ---- 提示层（advisory）场景：之前完全没覆盖 ----
    ('advisory_adjust', [
        'IF SHORTSHOT_low THEN IV0_adjust_请检查锁模力是否不合理',
    ]),
    ('advisory_popup', [
        'IF SHORTSHOT_low THEN IV0_popup_建议检查模具温度',
    ]),
    ('advisory_level', [
        'IF IV0_low THEN IV0_add_low',
    ]),
]

CONTEXTS = [
    ('ctx_low', {'feedback': {'defect': [{'keyword_name': 'SHORTSHOT', 'level': 'low'}]},
                 'process_parameter': {'IV0': 10.0, 'inj_pres_1': 20.0},
                 'iteration_trend': {'trend': 'stable'}}),
    ('ctx_high', {'feedback': {'defect': [{'keyword_name': 'SHORTSHOT', 'level': 'high'}]},
                  'process_parameter': {'IV0': 90.0, 'inj_pres_1': 180.0},
                  'iteration_trend': {'trend': 'stable'}}),
    ('ctx_mid', {'feedback': {'defect': [{'keyword_name': 'SHORTSHOT', 'level': 'medium'}]},
                 'process_parameter': {'IV0': 50.0, 'inj_pres_1': 100.0},
                 'iteration_trend': {'trend': 'stable'}}),
]

infer = {}
for sname, rules in SCENARIOS:
    for cname, ctx in CONTEXTS:
        repo = FakeRepo([mk(r) for r in rules])
        engine = FuzzyEngine(repository=repo)
        recs = engine.recommend(ctx)
        key = '%s|%s' % (sname, cname)
        infer[key] = {
            'recs': [
                {
                    'param_name': r.param_name,
                    'direction': r.direction,
                    'value': repr(getattr(r, 'value', None)),
                    'level': getattr(r, 'level', None),
                    'reason': getattr(r, 'reason', None),
                    'rule': getattr(r, 'rule', None),
                }
                for r in recs
            ],
            'diagnostics': repr(getattr(engine, '_diagnostics', None)),
            'calls': repr(repo.calls),
        }
put('infer', infer)

# 逐规则激活度（tsk_inference 返回 (results, extra_dict)，
# results 元素 = (rule_str, weighted_activation, {param: value})）
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet  # noqa: E402

# net 签名自适应：改造前是 (rule_array, keyword_array, priority_array)，
# 改造后是 (rules: List[NumTskRule], keywords: List[KeywordProfile])。
# 快照必须在**同一份脚本**里跑改造前后两侧 ⇒ 按签名探测分支。
_NET_HAS_PRIORITY_ARG = (
    len(inspect.signature(NumTskRuleNet.__init__).parameters) >= 4)


def _has_check_conclusion(rule_str: str) -> bool:
    """规则结论里有没有检查/弹窗类（`X_adjust_提示语` / `X_popup_xxx`）。

    ⚠️ 这道闸在**生产路径**上由分类层负责：
      - 改造前：数值层网络自己挡（`NumTskRuleNet._is_check_rule`）
      - 改造后：第 4 层 filter 判为提示类，根本不进数值层

    本探针是**直接构造 net**（绕过了分类层）⇒ 必须自己复刻这道闸，
    否则测的是「net 收到了非法输入」—— 那是分类层的职责，不是 net 的。

    ⚠️ 该闸在**改造前**是 net 内部行为，对 net 的可见效果与「提前挡掉」完全
    一致（不占下标、不进矩阵、不进 extra_dict）⇒ 两侧探针同口径。
    """
    for sol in parse_rule(rule_str)['solutions']:
        if sol.get('action') in ('adjust', 'popup'):
            return True
    return False


def make_numtsk_net(rule_strs, keywords, priorities):
    """按当前 net 的签名构造数值层网络（两侧通用，语义一致）。

    ⚠️ 只喂「数值层该收」的规则（见 `_has_check_conclusion`）。
    """
    kept = [(s, p) for s, p in zip(rule_strs, priorities)
            if not _has_check_conclusion(s)]
    kept_strs = [s for s, _ in kept]
    kept_prios = [p for _, p in kept]
    if _NET_HAS_PRIORITY_ARG:
        # 旧签名：优先级走外部数组
        return NumTskRuleNet(
            [{'rule_description': s} for s in kept_strs],
            [dict(k) for k in keywords],
            list(kept_prios),
        )
    # 新签名：优先级走规则档案（rule.profile.priority）
    rules = [
        NumTskRule(RuleProfile(rule_description=s, priority=p), parse_rule(s))
        for s, p in zip(kept_strs, kept_prios)
    ]
    return NumTskRuleNet(rules, list(keywords))


act = {}
for sname, rules in SCENARIOS:
    for pri in (1.0, 3.0, 10.0):
        for cname, ctx in CONTEXTS:
            key = '%s|%.1f|%s' % (sname, pri, cname)
            try:
                net = make_numtsk_net(rules, KEYWORDS, [pri] * len(rules))
                results, extra = net.tsk_inference(ctx['process_parameter'])
                act[key] = {
                    'results': [(str(r[0]), repr(r[1]), repr(r[2])) for r in results],
                    'extra': repr(extra),
                }
            except Exception as e:
                act[key] = '%s: %s' % (type(e).__name__, e)
put('activations', act)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(snap, f, ensure_ascii=False, sort_keys=True, indent=1)

print('快照已生成: %s' % OUT)
print('  gauss_face  = %d 项' % snap['gauss_face_count'])
print('  tri_face    = %d 项' % snap['tri_face_count'])
print('  defuzz_face = %d 项' % snap['defuzz_face_count'])
print('  infer       = %d 个场景' % len(snap['infer']))
print('  activations = %d 组' % len(snap['activations']))
