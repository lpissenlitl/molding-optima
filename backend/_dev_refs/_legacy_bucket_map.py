"""旧版全局静态档位表快照（2026-10-23 从 `fuzzy_core/macros.py` 整表删除后归档）

`HS_MAPPING_DICT` 曾把三种互不相干的语义混在一张表里：

  · 动作键 add/reduce/adjust   → 动作符号（与档位、级数无关）
  · 编号键 level1..level9      → 桶编号（与级数解耦，永远正确）
  · 语义键 low/mid/medium/high → **全局静态 3 档口径**（在 5/7/9 档字段上错位一档）

2026-10-23 `nets.py` 完成接线（改用 `resolve_bucket(lvl, word)` 按字段自己的
档位词表取桶）后，该表已按其自陈的收尾动作**整表删除**。

本模块保留一份**只读快照**，专供历史诊断脚本做 A/B 对照（复现历史结论），
**不得被产品代码 import**。

用法（诊断脚本内）::

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT
"""

import os
import sys

# 本模块需要能 import 到 `process` 包（backend 根目录）
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from process.algorithms.fuzzy.fuzzy_core.macros import (  # noqa: E402
    ACTION_MAP,
    LEVEL_NUMBER_TO_BUCKET,
)

# 旧表快照：与 macros.py 中被删除的定义逐字一致
LEGACY_HS_MAPPING_DICT = {
    'low': 0, 'mid': 1, 'medium': 1, 'high': 2,
    **LEVEL_NUMBER_TO_BUCKET,
    **ACTION_MAP,
}
