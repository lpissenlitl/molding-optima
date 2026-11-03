# -*- coding: utf-8 -*-
"""导出工具（**开发期**）—— 数据库 → 本地文件（第二数据源）。

把 `RuleLibrary` / `RuleMethod` / `RuleKeyword` 三张表导出成本地 JSON，
让 `library/files/` 的文件来源能完全脱离数据库运行。

用法（从 `backend` 目录）：

```
..\\.venv\\Scripts\\python.exe process\\algorithms\\fuzzy\\library\\files\\export.py
..\\.venv\\Scripts\\python.exe -m process.algorithms.fuzzy.library.files.export --out-dir D:\\tmp\\rules
```

产出（默认 `library/files/data/`）：

```
data/
├── libraries.json     规则库清单
├── keywords.json      关键字元数据
└── rules/<库码>.json  按库分文件的规则条目
```

⚠️ **这是开发期工具，不是运行时组件**：它 import 了 ORM 模型，只能作为
  脚本单独跑；运行时代码（`library/files/loader.py`、`repository.py`）
  **绝不 import 本模块**。

⚠️ **导出口径必须与数据库来源逐条一致**，否则两条路径的结果会分叉：

| 环节 | 导出时的处理 | 与数据库侧的对应 |
|---|---|---|
| 库 | 导出 `is_deleted=False` 的全部库（含停用库，带 `is_active` 标记） | `get_libraries_by_codes` 过滤 `is_active=True, is_deleted=False` |
| 同码多库 | **只导出第一条**（按主键升序），其余记警告 | `qs.first()` 取第一条 |
| 规则 | 导出 `is_deleted=False` 的全部规则（含停用规则，带 `is_active` 标记） | `get_methods` 过滤 `is_active=True, is_deleted=False` |
| 关键字 | **全部导出**（不带任何过滤，带 `is_deleted` 标记仅供查阅） | `RuleKeyword.objects.filter(keyword_name__in=...)` 不带过滤 |
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List


# —— 路径引导（脚本与 -m 两种跑法都支持）———————————————————————

_HERE = os.path.dirname(os.path.abspath(__file__))
# files → library → fuzzy → algorithms → process → backend
_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(_HERE)))))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

DEFAULT_OUT_DIR = os.path.join(_HERE, 'data')
RULES_SUBDIR = 'rules'
SCHEMA_VERSION = 1


def _bootstrap_django():
    """初始化 Django 环境（只在真正跑导出时才做）。"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')
    import django
    django.setup()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _write_json(path: str, payload: Dict[str, Any], indent: int = 2) -> None:
    """写 JSON（UTF-8、保留中文、末尾换行）。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=indent, sort_keys=False)
        f.write('\n')


# —— 导出：库 ————————————————————————————————————————————————

def export_libraries() -> List[Dict[str, Any]]:
    """导出规则库清单。

    ⚠️ **同码多库只导第一条**（按主键升序）—— 与数据库来源
      `get_libraries_by_codes` 的 ``qs.first()`` 口径一致 ⇒ 两条路径
      选中的库**逐条相同**。
    """
    from process.models.rules import RuleLibrary

    rows: List[Dict[str, Any]] = []
    seen: Dict[str, int] = {}
    for lib in RuleLibrary.objects.filter(is_deleted=False).order_by('id'):
        if lib.library_code in seen:
            print('  [警告] 库编码 %r 有多条记录，只导出第一条（id=%s），'
                  '跳过 id=%s —— 与数据库来源的 qs.first() 口径一致'
                  % (lib.library_code, seen[lib.library_code], lib.id))
            continue
        seen[lib.library_code] = lib.id
        rows.append({
            'library_id': lib.id,
            'library_code': lib.library_code,
            'library_name': lib.library_name,
            'library_type': lib.library_type,
            'priority': lib.priority,
            'is_active': lib.is_active,
            'source_ref': 'RuleLibrary:%s' % lib.id,
        })
    return rows


# —— 导出：规则 ————————————————————————————————————————————————

def export_rules(library_id: int, library_code: str) -> List[Dict[str, Any]]:
    """导出某个库的规则条目。

    ⚠️ **按库主键导出**（不是按 `library_code`）⇒ 同码多库时不会把
      两个库的规则混进同一个文件。
    """
    from process.models.rules import RuleMethod

    rows: List[Dict[str, Any]] = []
    qs = RuleMethod.objects.filter(
        rule_library_id=library_id,
        is_deleted=False,
    ).order_by('id')
    for rm in qs:
        rows.append({
            'id': rm.id,
            'rule_no': rm.rule_no,
            'defect_code': rm.defect_code,
            'defect_label': rm.defect_label,
            'rule_description': rm.rule_description,
            'rule_explanation': rm.rule_explanation,
            'priority': rm.priority,
            'polymer_abbreviation': rm.polymer_abbreviation,
            'product_category': rm.product_category,
            'is_active': rm.is_active,
            'source': rm.source,
        })
    return rows


# —— 导出：关键字 ——————————————————————————————————————————————

def export_keywords() -> List[Dict[str, Any]]:
    """导出关键字元数据（**全量，不带过滤**）。

    ⚠️ 与数据库侧 `RuleKeyword.objects.filter(keyword_name__in=...)` 一致
      —— 那个查询不带 `is_active` / `is_deleted` 条件 ⇒ 导出侧也不加，
      否则「同一条关键字在两条路径下去留不同」。
    """
    from process.models.rules import RuleKeyword

    rows: List[Dict[str, Any]] = []
    for kw in RuleKeyword.objects.order_by('id'):
        rows.append({
            'id': kw.id,
            'keyword_name': kw.keyword_name,
            'keyword_alias': kw.keyword_alias,
            'category': kw.category,
            'parameter_kind': kw.parameter_kind,
            'range_min': kw.range_min,
            'range_max': kw.range_max,
            'action_range_min': kw.action_range_min,
            'action_range_max': kw.action_range_max,
            'action_max_val': kw.action_max_val,
            'fuzzy_level': kw.fuzzy_level,
            'step': kw.step,
            'keyword_type': kw.keyword_type,
            'unit': kw.unit,
            'description': kw.description,
            # 仅供查阅（文件侧不按它过滤，与数据库侧口径一致）
            'is_deleted': kw.is_deleted,
        })
    return rows


# —— 主流程 ————————————————————————————————————————————————

def export_all(out_dir: str = DEFAULT_OUT_DIR, indent: int = 2) -> Dict[str, Any]:
    """执行完整导出，返回统计摘要。"""
    _bootstrap_django()

    exported_at = _now_iso()
    os.makedirs(out_dir, exist_ok=True)

    print('导出目标目录: %s' % out_dir)

    # 1) 库清单
    libraries = export_libraries()
    _write_json(os.path.join(out_dir, 'libraries.json'), {
        'schema_version': SCHEMA_VERSION,
        'exported_at': exported_at,
        'source': 'database',
        'libraries': libraries,
    }, indent=indent)
    print('  库清单      %d 条 → libraries.json' % len(libraries))

    # 2) 规则（按库分文件）
    rules_dir = os.path.join(out_dir, RULES_SUBDIR)
    os.makedirs(rules_dir, exist_ok=True)
    # 清掉上一轮的旧文件（库被删了时不会留残影）
    for name in os.listdir(rules_dir):
        if name.endswith('.json'):
            os.remove(os.path.join(rules_dir, name))

    total_rules = 0
    for lib in libraries:
        rows = export_rules(lib['library_id'], lib['library_code'])
        total_rules += len(rows)
        _write_json(os.path.join(rules_dir, '%s.json' % lib['library_code']), {
            'schema_version': SCHEMA_VERSION,
            'exported_at': exported_at,
            'library_code': lib['library_code'],
            'library_name': lib['library_name'],
            'library_id': lib['library_id'],
            'rules': rows,
        }, indent=indent)
        print('  规则 %-18s %4d 条 → rules/%s.json'
              % (lib['library_code'], len(rows), lib['library_code']))

    # 3) 关键字
    keywords = export_keywords()
    _write_json(os.path.join(out_dir, 'keywords.json'), {
        'schema_version': SCHEMA_VERSION,
        'exported_at': exported_at,
        'source': 'database',
        'keywords': keywords,
    }, indent=indent)
    print('  关键字      %d 条 → keywords.json' % len(keywords))

    summary = {
        'out_dir': out_dir,
        'exported_at': exported_at,
        'libraries': len(libraries),
        'rules': total_rules,
        'keywords': len(keywords),
    }
    print('导出完成: %d 个库 / %d 条规则 / %d 条关键字'
          % (summary['libraries'], summary['rules'], summary['keywords']))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description='把规则库 / 规则 / 关键字从数据库导出到本地文件')
    parser.add_argument('--out-dir', default=DEFAULT_OUT_DIR,
                        help='输出目录（默认: library/files/data/）')
    parser.add_argument('--indent', type=int, default=2,
                        help='JSON 缩进（默认: 2）')
    args = parser.parse_args(argv)
    export_all(out_dir=args.out_dir, indent=args.indent)
    return 0


if __name__ == '__main__':
    sys.exit(main())