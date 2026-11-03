"""文件读取层 —— 本地 JSON → 来源无关记录（**零 ORM**）。

职责：**只把文件读出来并规约成记录**，不做适用性判定、不做契约构造。
那些都在 `library/assembly.py`（来源无关的共用编排层）。

⚠️ **零 ORM**：本模块不 import 任何 Django 模块 —— 文件来源必须能在
  没有数据库的环境里跑（这正是「打通第二条路径」的意义）。

文件布局（默认目录 `library/files/data/`）：

```
data/
├── libraries.json          规则库清单（每个库一条）
├── keywords.json           关键字元数据（论域 / 档位 / 步长）
└── rules/
    ├── base.json           按库分文件的规则条目
    └── <库码>.json
```

⚠️ **取数口径与数据库来源逐条一致**（这是两条路径能对拍的前提）：

| 环节 | 数据库来源 | 文件来源 |
|---|---|---|
| 库的过滤 | `is_active=True, is_deleted=False` | 导出时过滤（`is_deleted`），读取时查 `is_active` |
| 规则的过滤 | `is_active=True, is_deleted=False` | 导出时过滤（`is_deleted`），读取时查 `is_active` |
| 规则的排序 | `ORDER BY priority DESC, id ASC` | `(-priority, id)` 升序（**用原始值排**） |
| 适用性判定 | `RuleService.matches_context` | 同左（**共用，不在本层**） |
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from process.algorithms.fuzzy.library.adapters import (
    LibraryRecordAdapter,
    RuleRecordAdapter,
)
from process.algorithms.fuzzy.library.contracts import LibraryRecord, RuleRecord


logger = logging.getLogger(__name__)


# —— 文件名约定 ——————————————————————————————————————————————

DEFAULT_DATA_DIR = Path(__file__).resolve().parent / 'data'
LIBRARIES_FILE = 'libraries.json'
KEYWORDS_FILE = 'keywords.json'
RULES_DIR = 'rules'
SCHEMA_VERSION = 1


class FileLibraryLoader:
    """本地文件读取器 —— 把 JSON 规约成**来源无关记录**。

    ⚠️ **零 ORM**：不 import 任何 Django 模块。

    ⚠️ **按 mtime 自动重载**（`auto_reload=True`）：改完 JSON 立即生效，
      不用重启进程 —— 这是「用本地文件探讨规则与关键词」这条路径的
      核心便利性；关掉它（`auto_reload=False`）则整个会话只读一次。
    """

    def __init__(
        self,
        root_dir: Optional[str] = None,
        auto_reload: bool = True,
    ):
        """构造读取器。

        Args:
            root_dir: 数据根目录（默认 `library/files/data/`）。
            auto_reload: 文件 mtime 变化时自动重读。
        """
        self._root = Path(root_dir) if root_dir else DEFAULT_DATA_DIR
        self._auto_reload = auto_reload
        self._cache: Dict[str, Any] = {}

    # —— 根目录 ————————————————————————————————————————————————

    @property
    def root_dir(self) -> Path:
        """数据根目录。"""
        return self._root

    @property
    def rules_dir(self) -> Path:
        """按库分文件的规则目录。"""
        return self._root / RULES_DIR

    # —— 底层读取（带 mtime 缓存）——————————————————————————————

    def _read_json(self, path: Path) -> Any:
        """读 JSON（带 mtime 缓存）。文件不存在 ⇒ `FileNotFoundError`。"""
        if not path.exists():
            raise FileNotFoundError('资源文件不存在: %s' % path)
        key = str(path)
        cached = self._cache.get(key)
        if cached is not None:
            mtime, data = cached
            if not self._auto_reload or mtime == path.stat().st_mtime:
                return data
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        self._cache[key] = (path.stat().st_mtime, data)
        return data

    # —— 库清单 ————————————————————————————————————————————————

    def load_libraries(self) -> Dict[str, LibraryRecord]:
        """读库清单，返回 `library_code` → `LibraryRecord` 的索引。

        ⚠️ **同编码多记录时只留第一条**（`setdefault`）—— 与数据库来源
          `RuleQueryService.get_library_index` 的口径一致 ⇒ 两条路径
          选中的库**逐条相同**。
        """
        data = self._read_json(self._root / LIBRARIES_FILE)
        index: Dict[str, LibraryRecord] = {}
        for item in data.get('libraries', []):
            record = LibraryRecordAdapter.from_dict(item)
            index.setdefault(record.library_code, record)
        return index

    # —— 关键字 ————————————————————————————————————————————————

    def load_keywords(self) -> List[Dict[str, Any]]:
        """读关键字元数据（**原始 dict 形态**，未转契约）。

        ⚠️ **不过滤**：与数据库来源一致 —— `RuleKeyword.objects.filter(...)`
          不带 `is_active` / `is_deleted` 条件 ⇒ 文件侧也不加，
          否则「同一条关键字在两条路径下去留不同」。
        """
        data = self._read_json(self._root / KEYWORDS_FILE)
        return list(data.get('keywords', []))

    def get_keyword_rows(self, names: List[str]) -> List[Dict[str, Any]]:
        """按参数名取关键字原始行（保持文件中的先后顺序）。"""
        if not names:
            return []
        wanted = set(names)
        return [row for row in self.load_keywords()
                if row.get('keyword_name') in wanted]

    # —— 规则 ————————————————————————————————————————————————

    def load_library_rules(self, library_code: str) -> List[Dict[str, Any]]:
        """读某个库的规则条目（**原始 dict 形态**，未转契约）。

        库文件不存在 ⇒ 返回空列表（该库没有规则，例如专家规则库）。
        """
        path = self.rules_dir / ('%s.json' % library_code)
        if not path.exists():
            return []
        data = self._read_json(path)
        return list(data.get('rules', []))

    def get_candidate_methods(
        self,
        library_code: str,
        defect_code: str,
    ) -> List[RuleRecord]:
        """取某库中「该缺陷的**候选**规则」，转成来源无关记录。

        ⚠️ **与数据库来源 `RuleQueryService.get_methods` 口径逐条一致**：

        1. 过滤：``defect_code`` 相等 + ``is_active`` 为真；
        2. 排序：``priority`` 降序、``id`` 升序
           —— **用原始值排**（不是转换后的 1.0 归一值），
           否则 ``priority=0`` 的规则排序位置会与数据库侧不同；
        3. **不做适用性判定**（聚合物 / 产品两维）—— 那是
           `RuleService.matches_context` 的事，在共用编排层统一做。

        Args:
            library_code: 规则库编码。
            defect_code: 缺陷标识。

        Returns:
            候选规则记录列表（已按数据库侧同口径排序）。
        """
        rows = [r for r in self.load_library_rules(library_code)
                if (r.get('defect_code') or '') == defect_code
                and bool(r.get('is_active', True))]
        rows.sort(key=self._sort_key)
        return [RuleRecordAdapter.from_dict(r, library_code) for r in rows]

    @staticmethod
    def _sort_key(row: Dict[str, Any]):
        """排序键：``(-原始 priority, id)`` —— 对齐 SQL 的 `ORDER BY priority DESC, id ASC`。"""
        priority = row.get('priority')
        priority = 0 if priority is None else float(priority)
        rid = row.get('id')
        rid = 0 if rid is None else int(rid)
        return (-priority, rid)

    # —— 自检 ————————————————————————————————————————————————

    def describe(self) -> Dict[str, Any]:
        """描述当前数据目录的内容（排查用，不参与算法）。"""
        libraries = self.load_libraries()
        return {
            'root_dir': str(self._root),
            'libraries': len(libraries),
            'keywords': len(self.load_keywords()),
            'rule_files': sorted(
                p.name for p in self.rules_dir.glob('*.json')
            ) if self.rules_dir.exists() else [],
        }


__all__ = [
    'FileLibraryLoader',
    'DEFAULT_DATA_DIR',
    'LIBRARIES_FILE',
    'KEYWORDS_FILE',
    'RULES_DIR',
    'SCHEMA_VERSION',
]