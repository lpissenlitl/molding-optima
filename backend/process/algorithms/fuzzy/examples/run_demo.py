# -*- coding: utf-8 -*-
"""案例离线 runner —— 读 JSON 案例，跑模糊推理，逐位比对期望输出。

⚠️ **全程不访问数据库**：案例数据是自持的（规则 + 论域元数据 + 输入上下文都在
   JSON 里），通过替换 `FuzzyEngine` 的数据源（`AlgorithmResourceRepository`
   协议）实现离线。脚本会**拦截所有 SQL 执行** —— 一旦有人不小心在链路上碰到
   数据库，立刻报错而不是悄悄连上去（离线这个卖点必须可证，不能只是说说）。

用法：
    cd backend
    ..\\.venv\\Scripts\\python.exe process\\algorithms\\fuzzy\\examples\\run_demo.py

    # 跑全部案例并比对期望输出（等价于 --check，退出码非 0 表示有偏差）
    ..\\.venv\\Scripts\\python.exe process\\algorithms\\fuzzy\\examples\\run_demo.py --check

    # 只跑指定案例（不比对）
    ..\\.venv\\Scripts\\python.exe process\\algorithms\\fuzzy\\examples\\run_demo.py fuzzy_shortshot_low

    # 列出全部案例
    ..\\.venv\\Scripts\\python.exe process\\algorithms\\fuzzy\\examples\\run_demo.py --list

    # 按当前输出重刷案例的 expected（改了规则 / 论域元数据后用；会就地改写 JSON）
    ..\\.venv\\Scripts\\python.exe process\\algorithms\\fuzzy\\examples\\run_demo.py --refresh-expected
"""
import json
import os
import sys

BACKEND = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))))
sys.path.insert(0, BACKEND)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')

import django  # noqa: E402

django.setup()

from django.db.backends import utils as db_utils  # noqa: E402

# ---------------------------------------------------------------- SQL 拦截
# 离线这个性质必须**可证**：把 CursorWrapper.execute 换成会抛异常的版本，
# 任何 SQL 执行都会立刻暴露（而不是靠「我记得没查库」）。
_SQL_GUARD = {'count': 0}


def _forbid_sql(self, sql, *args, **kwargs):
    _SQL_GUARD['count'] += 1
    raise AssertionError(
        '离线 runner 不应访问数据库，但捕获到 SQL: %s' % str(sql)[:120])


db_utils.CursorWrapper.execute = _forbid_sql

from process.algorithms.fuzzy import field_names  # noqa: E402
from process.algorithms.fuzzy.engine import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.fuzzy_core.profiles import (  # noqa: E402
    RuleProfile,
)
from process.algorithms.fuzzy.library.keywords import (  # noqa: E402
    RuleKeywordAdapter,
)

HERE = os.path.dirname(os.path.abspath(__file__))
CASES_DIR = os.path.join(HERE, 'cases')


class CaseRepository:
    """从案例 JSON 取规则与论域元数据（实现 `AlgorithmResourceRepository` 协议）。

    ⚠️ **零 ORM**：本类不 import 任何 `process.models.*` ——
       数据全部来自案例文件，与数据库无关。
    """

    def __init__(self, rules, keywords):
        self._rules = list(rules)
        self._keywords = {kw.keyword: kw for kw in keywords}
        self.calls = []

    def get_rules(self, context):
        self.calls.append(('get_rules', context.defect_name))
        return list(self._rules)

    def get_keywords_by_names(self, names):
        self.calls.append(('get_keywords_by_names', tuple(sorted(names))))
        wanted = set(names)
        return [kw for name, kw in self._keywords.items() if name in wanted]


def load_case(case_id):
    path = os.path.join(CASES_DIR, '%s.json' % case_id)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_cases():
    if not os.path.isdir(CASES_DIR):
        return []
    return sorted(
        f[:-5] for f in os.listdir(CASES_DIR) if f.endswith('.json')
    )


def build_repository(case):
    """案例 → 离线仓库（规则与关键词都走**生产适配器**，口径零重复）。"""
    rules = [RuleProfile(**row) for row in case['rules']]
    # ⚠️ 直接复用生产的 dict 适配器：step 为空时的 `span/3` 推导逻辑
    #    在适配器里，不在这里重写一遍（避免两处口径漂移）。
    keywords = RuleKeywordAdapter.to_keyword_profiles(case['keywords'])
    return CaseRepository(rules, keywords)


def build_context(case):
    """案例 → 引擎上下文（工艺参数做业务名 → 算法名翻译，与生产同一条路）。"""
    ctx = dict(case['context'])
    ctx['process_parameter'] = field_names.to_algo_params(
        case['context']['process_parameter'])
    return ctx


def run_case(case):
    repo = build_repository(case)
    engine = FuzzyEngine(repository=repo)
    recs = engine.recommend(build_context(case))
    return recs, repo


# ---------------------------------------------------------------- 比对
def compare(case, recs):
    """实际输出 vs 期望输出 —— 返回不一致描述列表（空 = 一致）。

    比对口径：按 `param_name` 配对（**不依赖输出顺序** ——
    顺序是呈现细节，值与置信度才是行为契约）。
    浮点用 `repr` 逐位比（避免 `==` 的容差掩盖真实漂移）。
    """
    problems = []
    expected = {
        r['param_name']: r
        for r in case['expected']['recommendations']
    }
    actual = {r.param_name: r for r in recs}

    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    for name in missing:
        problems.append('缺少建议：%s（期望 %s → %s）'
                        % (name, expected[name]['current_value'],
                           expected[name]['recommended_value']))
    for name in extra:
        problems.append('多出建议：%s（实际 %s → %s）'
                        % (name, actual[name].current_value,
                           actual[name].recommended_value))

    for name in sorted(set(expected) & set(actual)):
        exp, act = expected[name], actual[name]
        for field, exp_v, act_v in (
            ('current_value', exp['current_value'], act.current_value),
            ('recommended_value', exp['recommended_value'],
             act.recommended_value),
            ('confidence', exp['confidence'], act.confidence),
            ('direction', exp['direction'], act.direction),
            ('source', exp['source'], act.source),
        ):
            if isinstance(exp_v, float) or isinstance(act_v, float):
                same = repr(float(exp_v)) == repr(float(act_v))
            else:
                same = exp_v == act_v
            if not same:
                problems.append('%s.%s 不一致：期望 %r，实际 %r'
                                % (name, field, exp_v, act_v))
    return problems


def refresh_expected(case_id, case, recs):
    """按**当前输出**重刷案例 JSON 的 `expected` 块（就地写回）。

    用途：改了规则库 / 论域元数据后，案例的期望值会过时 ⇒ 用它把基线刷成
    当前行为。写出的格式与 `export_case.py` 导出时**完全一致**（便于 diff）。

    ⚠️ **会改写案例文件** —— 刷之前先确认这次改动是有意的。
    """
    case['expected']['recommendations'] = [
        {
            'param_name': r.param_name,
            'business_param_name': field_names.to_business_name(r.param_name),
            'current_value': r.current_value,
            'recommended_value': r.recommended_value,
            'confidence': r.confidence,
            'direction': r.direction,
            'source': r.source,
        }
        for r in recs
    ]
    path = os.path.join(CASES_DIR, '%s.json' % case_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(case, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write('\n')
    return path


def print_case(case, recs):
    print('=' * 74)
    print('案例 %s —— %s' % (case['case_id'], case.get('title', '')))
    print('=' * 74)
    defect = (case['context'].get('feedback') or {}).get('defect') or []
    for d in defect:
        print('缺陷: %s / 程度=%s / 位置=%s'
              % (d.get('keyword_name'), d.get('level'), d.get('position')))
    print('规则池: %d 条    论域元数据: %d 条'
          % (len(case['rules']), len(case['keywords'])))
    print()
    print('%-6s %-18s %14s %14s %10s  %s'
          % ('参数', '业务名', '当前值', '推荐值', '置信度', '方向'))
    print('-' * 74)
    for r in recs:
        print('%-6s %-18s %14s %14s %10.6f  %s'
              % (r.param_name,
                 field_names.to_business_name(r.param_name) or '-',
                 r.current_value, r.recommended_value,
                 r.confidence, r.direction))
    print()


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    flags = {a for a in argv[1:] if a.startswith('--')}

    if '--list' in flags:
        for cid in list_cases():
            print(cid)
        return 0

    if not args:
        targets = list_cases()
    else:
        targets = args

    if not targets:
        print('cases/ 下没有案例')
        return 1

    refresh = '--refresh-expected' in flags

    all_problems = []
    for cid in targets:
        case = load_case(cid)
        recs, repo = run_case(case)
        print_case(case, recs)
        if refresh:
            path = refresh_expected(cid, case, recs)
            print('[REFRESH] %s —— expected 已按当前输出重刷（%d 条）：%s'
                  % (cid, len(recs), path))
            print('  数据源调用: %s' % repo.calls)
            print()
            continue
        problems = compare(case, recs)
        if problems:
            all_problems.extend('%s: %s' % (cid, p) for p in problems)
            print('[FAIL] %s —— %d 项与期望输出不一致：' % (cid, len(problems)))
            for p in problems:
                print('    - %s' % p)
        else:
            print('[PASS] %s —— 与期望输出完全一致' % cid)
        print('  数据源调用: %s' % repo.calls)
        print()

    if _SQL_GUARD['count']:
        print('[FAIL] 期间发生了 %d 次 SQL 执行 —— 离线性被破坏'
              % _SQL_GUARD['count'])
        return 1
    print('（自证）全程 0 次 SQL 执行 —— 确认未访问数据库')

    if all_problems:
        print('[FAIL] 共 %d 项偏差' % len(all_problems))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
