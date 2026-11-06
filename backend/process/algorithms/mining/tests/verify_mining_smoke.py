"""规则挖掘内核 smoke test（独立运行，不依赖 Django 配置）

覆盖范围：
  场景 A - 关联规则产出与指标（12 条构造样本，期望值手算）
  场景 B - 阈值过滤（min_confidence / min_support / min_lift）
  场景 C - 不可用样本过滤（pending / 无缺陷 / 无变更）
  场景 D - 双标签方向（target_label=None 时挖 unqualified 方向）
  场景 E - 文件样本仓库（JSONL 往返 / 增量游标 / id 字典序可比）
  场景 F - 引擎外壳（is_available 阈值 / evaluate_rule 复核）
  场景 G - 零 ORM 约束（全程 0 次 SQL 执行）

运行：
  cd backend
  python process/algorithms/mining/tests/verify_mining_smoke.py

注：本文件是独立运行脚本（`verify_` 前缀 ⇒ 不被 pytest 收集）；
    断言走 `_failures` 收集器 + 退出码，不依赖 pytest 断言。

⚠️ 构造样本（12 条，手算基准）：
    A 组 6 条：SHORTSHOT + inj_pres_1:increase  → qualified
    B 组 3 条：FLASH     + hold_pres_1:decrease  → qualified
    C 组 3 条：SHORTSHOT + hold_pres_1:decrease  → unqualified

  由此推出：
    support(L:qualified)        = 9/12 = 0.75
    support(SHORTSHOT)          = 9/12 = 0.75
    support(inj_pres_1:inc)     = 6/12 = 0.50
    support(FLASH)              = 3/12 = 0.25
    support(hold_pres_1:dec)    = 6/12 = 0.50
  ⇒ 规则 1 前件{SHORTSHOT,inj_pres_1:inc}：conf = 6/6 = 1.0，lift = 1.0/0.75 = 4/3
  ⇒ 规则 2 前件{FLASH,hold_pres_1:dec}：      conf = 3/3 = 1.0，lift = 1.0/0.75 = 4/3
  ⇒ 规则 3 前件{FLASH}：                      conf = 3/3 = 1.0，lift = 1.0/0.75 = 4/3
  ⇒ 规则 4 前件{inj_pres_1:inc}：            conf = 6/6 = 1.0，lift = 1.0/0.75 = 4/3
  ⇒ 前件{SHORTSHOT}：conf = 6/9 = 0.667 < 0.7 ⇒ 被置信度阈值过滤
  ⇒ 前件{hold_pres_1:dec}：conf = 3/6 = 0.5 < 0.7 ⇒ 被置信度阈值过滤
  ⇒ 共 4 条规则
"""

import os
import sys
import tempfile

# 让 process 作为顶层 package 可被发现
HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))  # backend/
sys.path.insert(0, BACKEND_ROOT)

# 控制台默认 GBK，输出被重定向（管道 / 文件）时遇到 ⇒ ≈ 等字符会抛
# UnicodeEncodeError ⇒ 统一转 UTF-8 并对不可编码字符降级
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure'):
        _stream.reconfigure(encoding='utf-8', errors='replace')

PASS = '\033[92m'
FAIL = '\033[91m'
NC = '\033[0m'

_failures = []
_passes = []


def _assert_eq(actual, expected, label):
    if actual == expected:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual} == {expected}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected={expected}, actual={actual}"
        )


def _assert_close(actual, expected, label, eps=1e-6):
    if abs(actual - expected) <= eps:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: {actual:.6f} ≈ {expected}")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: expected≈{expected}, actual={actual:.6f}"
        )


def _assert_in(member, container, label):
    if member in container:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: 命中")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: 未命中（实际集合={container}）"
        )


def _assert_not_in(member, container, label):
    if member not in container:
        _passes.append(f"  {PASS}[PASS]{NC} {label}: 正确排除")
    else:
        _failures.append(
            f"  {FAIL}[FAIL]{NC} {label}: 应当排除但仍存在"
        )


# ========== 零 ORM 护栏：拦截一切 SQL ==========

def _install_sql_guard():
    """把 CursorWrapper.execute 换成会抛异常的版本 —— 链路上出现一次 SQL 就炸。"""
    from django.db.backends.utils import CursorWrapper

    original = CursorWrapper.execute

    def _boom(*args, **kwargs):
        raise AssertionError('挖掘内核触发了 SQL —— 违反「零 ORM」契约')

    CursorWrapper.execute = _boom
    return original


_SQL_ORIGINAL = _install_sql_guard()

# 导入放在护栏之后：import 链里若藏着 DB 访问会当场暴露
from process.algorithms.mining.contracts import SampleRecord  # noqa: E402
from process.algorithms.mining.core import mine_association_rules  # noqa: E402
from process.algorithms.mining.rule_miner import RuleMinerEngine  # noqa: E402
from process.algorithms.mining.samples import (  # noqa: E402
    FileSampleRepository,
    format_sample_id,
)


# ========== 构造样本 ==========

def _sample(sample_id, defects, changes, label, polymer='PP'):
    return SampleRecord(
        sample_id=sample_id,
        defects=list(defects),
        changes=[dict(c) for c in changes],
        label=label,
        context={'polymer': polymer},
        source_ref=f'tuning_record:{sample_id}',
    )


def _change(param, direction, before, after):
    return {'param': param, 'direction': direction, 'before': before, 'after': after}


def _base_samples():
    """12 条构造样本（A 6 + B 3 + C 3）。"""
    samples = []
    for i in range(6):
        samples.append(_sample(
            f's{i:03d}', ['SHORTSHOT'],
            [_change('inj_pres_1', 'increase', 50, 60)], 'qualified',
        ))
    for i in range(6, 9):
        samples.append(_sample(
            f's{i:03d}', ['FLASH'],
            [_change('hold_pres_1', 'decrease', 40, 35)], 'qualified',
            polymer='ABS',
        ))
    for i in range(9, 12):
        samples.append(_sample(
            f's{i:03d}', ['SHORTSHOT'],
            [_change('hold_pres_1', 'decrease', 40, 35)], 'unqualified',
        ))
    return samples


def _rule_key(rule):
    """规则的稳定标识（不依赖输出顺序）。"""
    defects = tuple(sorted(rule.defects))
    changes = tuple(sorted(
        (c.get('param'), c.get('direction')) for c in rule.changes
    ))
    return (defects, changes, rule.consequent)


# ========== 场景 A：关联规则产出与指标 ==========

def test_scenario_a_rules_and_metrics():
    print("\n[场景 A] 关联规则产出与指标（12 条构造样本）")
    rules = mine_association_rules(
        _base_samples(),
        min_support=0.05,
        min_confidence=0.7,
        min_lift=1.0,
        max_len=4,
    )
    _assert_eq(len(rules), 4, 'A 规则条数')

    keys = {_rule_key(r) for r in rules}
    _assert_in(
        (('SHORTSHOT',), (('inj_pres_1', 'increase'),), 'qualified'),
        keys, 'A 规则1 {SHORTSHOT, inj_pres_1:increase}',
    )
    _assert_in(
        (('FLASH',), (('hold_pres_1', 'decrease'),), 'qualified'),
        keys, 'A 规则2 {FLASH, hold_pres_1:decrease}',
    )
    _assert_in(
        (('FLASH',), (), 'qualified'),
        keys, 'A 规则3 {FLASH}',
    )
    _assert_in(
        ((), (('inj_pres_1', 'increase'),), 'qualified'),
        keys, 'A 规则4 {inj_pres_1:increase}',
    )
    # 被置信度阈值过滤的前件不应出现
    _assert_not_in(
        (('SHORTSHOT',), (), 'qualified'),
        keys, 'A {SHORTSHOT} 前件应被置信度过滤',
    )
    _assert_not_in(
        ((), (('hold_pres_1', 'decrease'),), 'qualified'),
        keys, 'A {hold_pres_1:decrease} 前件应被置信度过滤',
    )

    by_key = {_rule_key(r): r for r in rules}
    r1 = by_key[(('SHORTSHOT',), (('inj_pres_1', 'increase'),), 'qualified')]
    _assert_close(r1.support, 0.5, 'A 规则1 support = 6/12')
    _assert_close(r1.confidence, 1.0, 'A 规则1 confidence = 6/6')
    _assert_close(r1.lift, 4.0 / 3.0, 'A 规则1 lift = 1.0/0.75')
    _assert_eq(len(r1.evidence), 6, 'A 规则1 证据条数')
    _assert_eq(r1.consequent, 'qualified', 'A 规则1 后件')

    r3 = by_key[(('FLASH',), (), 'qualified')]
    _assert_close(r3.support, 0.25, 'A 规则3 support = 3/12')
    _assert_close(r3.confidence, 1.0, 'A 规则3 confidence = 3/3')
    _assert_eq(len(r3.evidence), 3, 'A 规则3 证据条数')


# ========== 场景 B：阈值过滤 ==========

def test_scenario_b_thresholds():
    print("\n[场景 B] 阈值过滤（min_confidence / min_support / min_lift）")

    strict_lift = mine_association_rules(
        _base_samples(), min_support=0.05, min_confidence=0.7, min_lift=1.5,
    )
    _assert_eq(len(strict_lift), 0, 'B min_lift=1.5 ⇒ 全部 lift=4/3 被过滤')

    strict_conf = mine_association_rules(
        _base_samples(), min_support=0.05, min_confidence=0.8, min_lift=1.0,
    )
    _assert_eq(len(strict_conf), 4, 'B min_confidence=0.8 ⇒ conf=1.0 的 4 条保留')

    strict_support = mine_association_rules(
        _base_samples(), min_support=0.3, min_confidence=0.7, min_lift=1.0,
    )
    _assert_eq(len(strict_support), 2, 'B min_support=0.3 ⇒ 仅剩 2 条')

    strict_keys = {_rule_key(r) for r in strict_support}
    _assert_in(
        (('SHORTSHOT',), (('inj_pres_1', 'increase'),), 'qualified'),
        strict_keys, 'B 高支持度下规则1 仍在',
    )
    _assert_not_in(
        (('FLASH',), (), 'qualified'),
        strict_keys, 'B 高支持度下 {FLASH}（support=3/12）被过滤',
    )


# ========== 场景 C：不可用样本过滤 ==========

def test_scenario_c_unusable_samples():
    print("\n[场景 C] 不可用样本过滤")
    samples = _base_samples() + [
        _sample('x001', ['SHORTSHOT'], [_change('inj_pres_1', 'increase', 50, 60)], 'pending'),
        _sample('x002', [], [_change('inj_pres_1', 'increase', 50, 60)], 'qualified'),
        _sample('x003', ['SHORTSHOT'], [], 'qualified'),
    ]
    rules = mine_association_rules(samples)
    _assert_eq(len(rules), 4, 'C 不可用样本不改变规则条数')
    for rule in rules:
        for sid in rule.evidence:
            _assert_not_in(sid, ('x001', 'x002', 'x003'), f'C 证据不含不可用样本 {sid}')

    _assert_eq(len(mine_association_rules([])), 0, 'C 空样本返回 0 条')
    _assert_eq(
        len(mine_association_rules([
            _sample('y001', ['SHORTSHOT'], [_change('inj_pres_1', 'increase', 50, 60)], 'pending'),
        ])),
        0, 'C 全 pending 返回 0 条',
    )


# ========== 场景 D：双标签方向 ==========

def test_scenario_d_both_labels():
    print("\n[场景 D] target_label=None ⇒ 同时挖两个标签方向")
    rules = mine_association_rules(
        _base_samples(), min_support=0.05, min_confidence=0.7, min_lift=1.0,
        target_label=None,
    )
    keys = {_rule_key(r) for r in rules}
    _assert_in(
        (('SHORTSHOT',), (('hold_pres_1', 'decrease'),), 'unqualified'),
        keys, 'D unqualified 方向规则产出',
    )
    r = next(r for r in rules if r.consequent == 'unqualified')
    _assert_close(r.support, 0.25, 'D unqualified 规则 support = 3/12')
    _assert_close(r.confidence, 1.0, 'D unqualified 规则 confidence = 3/3')
    _assert_close(r.lift, 4.0, 'D unqualified 规则 lift = 1.0/0.25')


# ========== 场景 E：文件样本仓库 ==========

def test_scenario_e_file_repository():
    print("\n[场景 E] 文件样本仓库（JSONL 往返 / 增量游标 / id 可比）")
    with tempfile.TemporaryDirectory() as tmp:
        repo = FileSampleRepository(tmp)
        _assert_eq(repo.get_samples(), [], 'E 语料不存在时返回空')

        written = repo.append_samples(_base_samples())
        _assert_eq(written, 12, 'E 追加 12 条')
        loaded = repo.get_samples()
        _assert_eq(len(loaded), 12, 'E 读回 12 条')
        _assert_eq(loaded[0].sample_id, 's000', 'E 按 sample_id 升序')
        _assert_eq(loaded[0].label, 'qualified', 'E 字段往返（label）')
        _assert_eq(loaded[0].defects, ['SHORTSHOT'], 'E 字段往返（defects）')
        _assert_eq(
            loaded[0].changes[0]['param'], 'inj_pres_1', 'E 字段往返（changes）',
        )
        _assert_eq(loaded[0].source_ref, 'tuning_record:s000', 'E 字段往返（source_ref）')

        tail = repo.get_samples(since='s005')
        _assert_eq(len(tail), 6, 'E 增量游标 after s005 ⇒ 6 条')
        _assert_eq(tail[0].sample_id, 's006', 'E 增量游标首条 = s006')

        # append-only：再次追加只增不改
        repo.append_samples([_sample('s012', ['FLASH'], [_change('inj_pres_1', 'increase', 50, 60)], 'qualified')])
        _assert_eq(len(repo.get_samples()), 13, 'E 二次追加后 13 条')
        _assert_eq(repo.get_samples()[0].sample_id, 's000', 'E 历史样本未被改写')

    _assert_eq(format_sample_id('tr', 70), 'tr:000000000070', 'E sample_id 零填充')
    _assert_eq(
        format_sample_id('tr', 99) < format_sample_id('tr', 100),
        True, 'E sample_id 字典序可比（99 < 100）',
    )


# ========== 场景 F：引擎外壳 ==========

def test_scenario_f_engine():
    print("\n[场景 F] 引擎外壳（is_available / evaluate_rule）")
    engine = RuleMinerEngine(min_samples=10)
    samples = _base_samples()
    _assert_eq(engine.is_available({'samples': samples}), True, 'F 12 条 ⇒ 可用')
    _assert_eq(engine.is_available({'samples': samples[:9]}), False, 'F 9 条 ⇒ 不可用')
    _assert_eq(engine.is_available({}), False, 'F 空上下文 ⇒ 不可用')
    _assert_eq(len(engine.run({'samples': samples})), 4, 'F run() 产出 4 条')
    _assert_eq(len(engine.run({'samples': samples[:9]})), 0, 'F 样本不足 run() 返回 0 条')

    rules = engine.run({'samples': samples})
    r1 = rules[0]
    evaluated = engine.evaluate_rule(r1, samples)
    _assert_close(evaluated['support'], r1.support, 'F evaluate_rule support 一致')
    _assert_close(evaluated['confidence'], r1.confidence, 'F evaluate_rule confidence 一致')
    _assert_close(evaluated['lift'], r1.lift, 'F evaluate_rule lift 一致')
    _assert_eq(len(evaluated['evidence']), len(r1.evidence), 'F evaluate_rule 证据条数一致')


# ========== 场景 G：零 ORM ==========

def test_scenario_g_zero_orm():
    print("\n[场景 G] 零 ORM 约束")
    _passes.append(
        f"  {PASS}[PASS]{NC} G 全程 0 次 SQL 执行（CursorWrapper.execute 已被拦截）"
    )


def main():
    test_scenario_a_rules_and_metrics()
    test_scenario_b_thresholds()
    test_scenario_c_unusable_samples()
    test_scenario_d_both_labels()
    test_scenario_e_file_repository()
    test_scenario_f_engine()
    test_scenario_g_zero_orm()

    print('\n' + '=' * 70)
    for line in _passes:
        print(line)
    for line in _failures:
        print(line)
    print('=' * 70)
    print(f"通过: {len(_passes)}    失败: {len(_failures)}")
    if _failures:
        print('❌ 规则挖掘 smoke test 存在失败项')
        return 1
    print('✅ 全部规则挖掘 smoke test 通过！')
    return 0


if __name__ == '__main__':
    sys.exit(main())
