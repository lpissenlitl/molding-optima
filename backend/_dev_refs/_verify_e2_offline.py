"""E2 离线验证（临时脚本，验完即删）：证明编排层可脱离数据库运行。

三个验证点：
  V1  FakeRepository 注入后，recommend() 完全不碰 DB
  V2  条目级隔离：一条脏规则（混合结论）被跳过，其余规则照常产出推荐
  V3  第 0 层边界：规则库查询抛异常时，recommend() 降级为空推荐而不冒泡

运行：cd backend; ../.venv/Scripts/python.exe _dev_refs/_verify_e2_offline.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django  # noqa: E402

django.setup()

from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    KeywordProfile,
    RuleProfile,
)


GOOD_RULE = 'IF SHORTSHOT_low AND IV0_low THEN IV0_add_2'
# 混合结论：add_2 是数字、add_low 不是 ⇒ classify_conclusion_kind 判为 numeric，
# 但 nets.py 的 float('low') 会抛 ValueError ⇒ 现状是整层归零。
DIRTY_RULE = 'IF SHORTSHOT_low AND IV0_low THEN IV0_add_2 AND IV0_add_low'

KEYWORDS = [
    KeywordProfile(keyword='IV0', lvl=3, min_val=0.0, max_val=100.0, step=1.0),
]


class FakeRepo:
    """完全离线的规则仓库（不 import ORM，不连 DB）。

    ⚠️ 契约（`library/contracts.py`）：`get_rules` → `List[RuleProfile]`，
    `get_keywords_by_names` → `List[KeywordProfile]`。
    """

    def __init__(self, rules, boom=False):
        self._rules = rules
        self._boom = boom
        self.calls = []

    def get_rules(self, context):
        self.calls.append(('get_rules', context.defect_name))
        if self._boom:
            raise RuntimeError('模拟 DB 不可用')
        return self._rules

    # —— 以下三个方法在「第 4 层 filter」下沉之后**不该再被引擎调用** ——
    #    分流 / 数组化 / 优先级数组都已由 fuzzy_core.rules_filter 接管。
    #    这里故意做成「一旦被调用就炸」，让回归立刻暴露，而不是静默走老路。
    def split_by_conclusion_kind(self, rules):
        raise AssertionError('引擎不应再自己分流（分流已下沉到第 4 层 filter）')

    def to_rule_array(self, rules):
        raise AssertionError('引擎不应再自己数组化规则（已下沉到第 4 层 filter）')

    def get_priority_array(self, rules):
        raise AssertionError('引擎不应再单独取优先级数组（优先级已随规则档案走）')

    def get_keywords_by_names(self, names):
        self.calls.append(('get_keywords_by_names', tuple(sorted(names))))
        return [k for k in KEYWORDS if k.keyword in set(names)]


def make_rule(rule_str):
    return RuleProfile(
        rule_description=rule_str,
        specificity=4,
        conclusion_kind='numeric',
        priority=1.0,
    )


CONTEXT = {
    'feedback': {'defect': [{'keyword_name': 'SHORTSHOT', 'level': 'low'}]},
    'process_parameter': {'IV0': 10.0},
    'iteration_trend': {'trend': 'stable'},
}

failures = []


def check(name, cond, detail=''):
    if cond:
        print(f'[PASS] {name}')
    else:
        print(f'[FAIL] {name}  {detail}')
        failures.append(name)


# ---------------------------------------------------------------- V1
repo = FakeRepo([make_rule(GOOD_RULE)])
engine = FuzzyEngine(repository=repo)
recs = engine.recommend(CONTEXT)
check('V1 注入 FakeRepository 后 recommend 可离线跑通',
      len(recs) == 1, f'实际 recs={recs}')
check('V1 产出的是 IV0 且方向为 increase',
      bool(recs) and recs[0].param_name == 'IV0' and recs[0].direction == 'increase',
      f'实际 recs={recs}')
check('V1 确实调用了注入的仓库（未被真实实现顶替）',
      any(c[0] == 'get_rules' for c in repo.calls), f'实际 calls={repo.calls}')

# ---------------------------------------------------------------- V2
repo2 = FakeRepo([make_rule(GOOD_RULE), make_rule(DIRTY_RULE)])
engine2 = FuzzyEngine(repository=repo2)
recs2 = engine2.recommend(CONTEXT)
check('V2 脏规则未拖垮整层（其余规则照常产出推荐）',
      len(recs2) == 1, f'实际 recs={recs2}')
check('V2 脏规则被记入诊断清单',
      bool(engine2._diagnostics)
      and engine2._diagnostics[0]['skipped'][0]['rule'] == DIRTY_RULE,
      f'实际 diagnostics={engine2._diagnostics}')

# 对照：若不做预检，脏规则会让整层归零
# （新契约：net 吃【规则对象 + KeywordProfile】；这里手工把脏规则塞进去）
from process.algorithms.fuzzy.fuzzy_core.models.nets import NumTskRuleNet  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.models.rules import NumTskRule  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule  # noqa: E402

try:
    NumTskRuleNet(
        [NumTskRule(make_rule(s), parse_rule(s))
         for s in (GOOD_RULE, DIRTY_RULE)],
        list(KEYWORDS),
    )
    check('V2 对照组：裸构造含脏规则的网络会抛异常', False, '竟然没抛')
except Exception as e:
    check('V2 对照组：裸构造含脏规则的网络会抛异常（证明预检的必要性）',
          True, str(e))

# ---------------------------------------------------------------- V3
repo3 = FakeRepo([], boom=True)
engine3 = FuzzyEngine(repository=repo3)
try:
    recs3 = engine3.recommend(CONTEXT)
    check('V3 规则库查询异常时降级为空推荐（不冒泡）',
          recs3 == [], f'实际 recs={recs3}')
except Exception as e:
    check('V3 规则库查询异常时降级为空推荐（不冒泡）', False, f'冒泡了: {e}')

print()
if failures:
    print(f'[FAIL] {len(failures)} 项未通过: {failures}')
    sys.exit(1)
print('[PASS] E2 离线验证全部通过')
