"""
verify_fuzzy_nested_context.py
验证 engine.recommend() 正确从嵌套对象 context['polymer'] / context['mold']
取出 abbreviation / product_category 传给 RuleQueryContext。

契约说明（2026-10-20 随 optimize 链路打通同步）：
- 缺陷名取 `feedback.defect[].keyword_name`（英文缺陷码，如 SHORTSHOT），
  与 RuleMethod.defect_code / RuleKeyword.keyword_name 对齐；
  旧的 `defect_name`（中文或 snake_case）已不再被读取
- process_parameter 是算法命名空间（IV0 / IP0 / ...，0-based）

策略：spy ResourceRepository.get_rules（不 mock 返回值，只看传入的 RuleQueryContext 字段）。
"""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")
django.setup()

from unittest.mock import patch
from process.algorithms.fuzzy import FuzzyEngine
from process.algorithms.fuzzy.library.contracts import RuleQueryContext


def main():
    print("=" * 70)
    print("engine.recommend: 验证嵌套 context['polymer/mold'] 取值")
    print("=" * 70)

    engine = FuzzyEngine()
    context = {
        "feedback": {
            "defect": [{"keyword_name": "SHORTSHOT", "level": "high", "position": "DL1"}],
        },
        "process_parameter": {"IP0": 60.0},
        "machine_info": {"drive_system": "hydraulic"},
        "polymer_info": {"abbreviation": "PE", "melt_flow_rate": 7.0},
        "mold_info": {"product_category": "酒瓶", "cavity_count": 4},
    }

    captured: list[RuleQueryContext] = []

    def _spy_get_rules(ctx, *args, **kwargs):
        captured.append(ctx)
        return []  # 返回空，让 fuzzy 自然结束

    with patch(
        # `ResourceRepository` 在 `engine` 里是**函数内延迟导入**，
        # 模块级没有该属性 ⇒ patch 必须指向真实定义处（library.repository）。
        "process.algorithms.fuzzy.library.repository.ResourceRepository.get_rules",
        side_effect=_spy_get_rules,
    ):
        recs = engine.recommend(context)

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
    print(f"[1/3] RuleQueryContext 正确接收: "
          f"polymer_abbreviation={qctx.polymer_abbreviation!r}, "
          f"product_category={qctx.product_category!r}, "
          f"defect_name={qctx.defect_name!r}")

    # 退化：polymer_info / mold_info 缺失时走空 dict，不应抛错
    captured.clear()
    context_empty = {
        "feedback": {"defect": [{"keyword_name": "SHORTSHOT", "level": "high"}]},
        "process_parameter": {},
        "machine_info": {},
    }
    with patch(
        # `ResourceRepository` 在 `engine` 里是**函数内延迟导入**，
        # 模块级没有该属性 ⇒ patch 必须指向真实定义处（library.repository）。
        "process.algorithms.fuzzy.library.repository.ResourceRepository.get_rules",
        side_effect=_spy_get_rules,
    ):
        recs2 = engine.recommend(context_empty)
    assert len(captured) == 1
    assert captured[0].polymer_abbreviation is None
    assert captured[0].product_category is None
    print("[2/3] polymer_info / mold_info 缺失时退化到 None OK")

    # 退化：polymer_info / mold_info 是 None（极端 case）
    captured.clear()
    context_none = {
        "feedback": {"defect": [{"keyword_name": "SHORTSHOT", "level": "high"}]},
        "process_parameter": {},
        "machine_info": {},
        "polymer_info": None,
        "mold_info": None,
    }
    with patch(
        # `ResourceRepository` 在 `engine` 里是**函数内延迟导入**，
        # 模块级没有该属性 ⇒ patch 必须指向真实定义处（library.repository）。
        "process.algorithms.fuzzy.library.repository.ResourceRepository.get_rules",
        side_effect=_spy_get_rules,
    ):
        recs3 = engine.recommend(context_none)
    assert len(captured) == 1
    assert captured[0].polymer_abbreviation is None
    assert captured[0].product_category is None
    print("[3/3] polymer_info / mold_info 显式 None 时不抛错 OK")

    print("\n=== verify_fuzzy_nested_context PASSED ===")
    return True


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
