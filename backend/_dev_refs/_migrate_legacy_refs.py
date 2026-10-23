"""一次性迁移工具：历史诊断脚本的 `HS_MAPPING_DICT` → 只读快照引用

背景（2026-10-23）：
    模糊引擎第一刀完成接线（`nets.py` 改用 `resolve_bucket(lvl, word)`）后，
    `fuzzy_core/macros.py` 已按其自陈的收尾动作**整表删除** `HS_MAPPING_DICT`。
    而 `_dev_refs/` 下的历史诊断脚本仍引用这个已不存在的名字 ⇒ 运行即 ImportError。

这些脚本需要**旧口径**做 A/B 对照（复现历史结论），不能删，故统一改用
`backend/_dev_refs/_legacy_bucket_map.py` 里的只读快照
`LEGACY_HS_MAPPING_DICT`。

本工具做的事（对每个目标脚本）：
    1. 裸引用 `HS_MAPPING_DICT` → `LEGACY_HS_MAPPING_DICT`
       （正则负向断言，跳过已带 `LEGACY_` 前缀的，不会变成 `LEGACY_LEGACY_`）
    2. 从 `macros` 的 import 块里摘掉这个键（它已不在 macros 里了）
    3. 单行 import 改为 `from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT`
    4. 缺 import 时在首个业务 import 前补一行

⚠️ 文件读写一律显式 UTF-8 + 保留原换行符（``newline=''``），
   避免 Windows 下把脚本里的中文写坏。

运行：cd backend; python _dev_refs/_migrate_legacy_refs.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 需要机械迁移的脚本（其余特例单独手改，避免批量改动误伤语义）
TARGETS = [
    'diag_fuzzy_algo_audit.py',
    'diag_fuzzy_design.py',
    'diag_fuzzy_fix_simulation.py',
    'diag_fuzzy_impact.py',
    'diag_fuzzy_level_audit.py',
    'diag_fuzzy_level_design.py',
    'diag_fuzzy_level_number_usage.py',
    'diag_fuzzy_level_word_crash.py',
    'diag_fuzzy_pipeline.py',
    'diag_fuzzy_rule_journey.py',
]

# 裸标识符（负向断言保证不误伤 LEGACY_ 前缀）
PAT_BARE = re.compile(r'(?<![A-Za-z_])HS_MAPPING_DICT(?![A-Za-z_])')
# 多行 import 块里那一行
PAT_BLOCK_ROW = re.compile(r'^[ \t]*LEGACY_HS_MAPPING_DICT,[ \t]*\r?\n', re.M)
# 单行 import
PAT_SINGLE_IMPORT = re.compile(
    r'^from [\w.]+ import LEGACY_HS_MAPPING_DICT[ \t]*\r?\n', re.M)
# import 插入点：首个业务 import（process / fuzzy_core）
PAT_INSERT = re.compile(r'^from (?:process|fuzzy_core)', re.M)

SNAPSHOT_IMPORT = 'from _legacy_bucket_map import LEGACY_HS_MAPPING_DICT'


def migrate(name):
    path = os.path.join(HERE, name)
    with open(path, 'r', encoding='utf-8', newline='') as f:
        src = f.read()
    origin = src

    # 1) 裸引用改名
    src = PAT_BARE.sub('LEGACY_HS_MAPPING_DICT', src)
    # 2) 摘掉 macros import 块里的那一行
    src = PAT_BLOCK_ROW.sub('', src)
    # 3) 单行 import 改指快照模块
    src = PAT_SINGLE_IMPORT.sub(SNAPSHOT_IMPORT + '\n', src)
    # 4) 缺 import 则补
    if SNAPSHOT_IMPORT not in src:
        m = PAT_INSERT.search(src)
        if not m:
            return name, 'SKIP（找不到 import 插入点）', False
        src = src[:m.start()] + SNAPSHOT_IMPORT + '\n' + src[m.start():]

    if src == origin:
        return name, '无需改动', False
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(src)
    return name, '已迁移', True


def main():
    changed = 0
    for name in TARGETS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            print(f'  [MISS] {name} 不存在')
            continue
        name, status, dirty = migrate(name)
        mark = '*' if dirty else ' '
        print(f'  {mark} {name:<40} {status}')
        changed += 1 if dirty else 0
    print()
    print(f'共处理 {len(TARGETS)} 个脚本，实际改动 {changed} 个')
    print('提示：跑完请用 py_compile 校验语法，并 grep 确认无裸引用残留')
    return 0


if __name__ == '__main__':
    sys.exit(main())
