r"""engine.recommend → RuleQueryContext 的上下文取值护栏。

契约说明：
- 缺陷名取 ``feedback.defects[].keyword_name``（英文缺陷码，如 SHORTSHOT），
  与 ``RuleMethod.defect_code`` / ``RuleKeyword.keyword_name`` 对齐
  （``defect_name``（中文或 snake_case）不被读取）
- ``process_parameter`` 是算法命名空间（IV0 / IP0 / ...，0-based）

策略：spy ``ResourceRepository.get_rules``（不 mock 返回值，只看传入的
``RuleQueryContext`` 字段）。

运行：
  cd backend
  ..\.venv\Scripts\python.exe -m pytest tests/test_fuzzy_nested_context.py -q
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch  # noqa: E402

from process.algorithms.fuzzy import FuzzyEngine  # noqa: E402
from process.algorithms.fuzzy.library.contracts import RuleQueryContext  # noqa: E402

#: `ResourceRepository` 在 `engine` 里是**函数内延迟导入**，模块级没有该属性
#: ⇒ patch 必须指向真实定义处（library.repository）。
_GET_RULES_TARGET = "process.algorithms.fuzzy.library.repository.ResourceRepository.get_rules"


def _context(**overrides):
    """构造一份完整的引擎上下文（缺陷选取在调用方收敛一次，引擎只读结果）。"""
    context = {
        "feedback": {"defects": [{"keyword_name": "SHORTSHOT", "level": "high", "position": "DL1"}]},
        "process_parameter": {"IP0": 60.0},
        "machine_info": {"drive_system": "hydraulic"},
        "polymer_info": {"abbreviation": "PE", "melt_flow_rate": 7.0},
        "mold_info": {"product_category": "酒瓶", "cavity_count": 4},
    }
    context.update(overrides)
    return context


def _run_and_capture(context):
    """跑一次引擎，把构造出来的 RuleQueryContext 收起来。"""
    from process.services.optimize_chain.defect_selection import select_defect

    captured: list[RuleQueryContext] = []

    def _spy_get_rules(ctx, *args, **kwargs):
        captured.append(ctx)
        return []  # 返回空，让 fuzzy 自然结束

    engine = FuzzyEngine()
    context["feedback"] = select_defect(context.get("feedback") or {})
    with patch(_GET_RULES_TARGET, side_effect=_spy_get_rules):
        engine.recommend(context)
    return captured


def test_query_context_takes_nested_context_values():
    """参照系（业务口径）：引擎从嵌套对象 context['polymer'] / context['mold']
    取 abbreviation / product_category 传给规则查询上下文。"""
    captured = _run_and_capture(_context())

    assert len(captured) == 1, f"RuleQueryContext 应被构造 1 次, got {len(captured)}"
    qctx = captured[0]
    assert qctx.polymer_abbreviation == "PE", (
        f"polymer_abbreviation 应取 context['polymer']['abbreviation']='PE', "
        f"got {qctx.polymer_abbreviation!r}"
    )
    assert qctx.product_category == "酒瓶", (
        f"product_category 应取 context['mold']['product_category']='酒瓶', "
        f"got {qctx.product_category!r}"
    )
    assert qctx.defect_name == "SHORTSHOT"


def test_query_context_degrades_when_dimensions_missing():
    """参照系（业务口径）：polymer_info / mold_info 缺失 ⇒ 退化到 None，不抛错。"""
    captured = _run_and_capture({
        "feedback": {"defects": [{"keyword_name": "SHORTSHOT", "level": "high"}]},
        "process_parameter": {},
        "machine_info": {},
    })

    assert len(captured) == 1
    assert captured[0].polymer_abbreviation is None
    assert captured[0].product_category is None


def test_query_context_degrades_when_dimensions_are_none():
    """参照系（业务口径）：polymer_info / mold_info 显式为 None ⇒ 退化到 None，不抛错。"""
    captured = _run_and_capture({
        "feedback": {"defects": [{"keyword_name": "SHORTSHOT", "level": "high"}]},
        "process_parameter": {},
        "machine_info": {},
        "polymer_info": None,
        "mold_info": None,
    })

    assert len(captured) == 1
    assert captured[0].polymer_abbreviation is None
    assert captured[0].product_category is None


def main():
    """独立跑法（不依赖 pytest）：``python -m tests.test_fuzzy_nested_context``。"""
    cases = [
        test_query_context_takes_nested_context_values,
        test_query_context_degrades_when_dimensions_missing,
        test_query_context_degrades_when_dimensions_are_none,
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