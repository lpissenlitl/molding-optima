"""
生成规则关键词 curated JSON

从原 JSON（rule_keyword_extracted.original.json）出发：
  1. 按 keyword_name 去重（保留首条）
  2. 排除不导入的数据（17 条）
  3. 统一 fuzzy_level = 5（与 Model 默认一致）
  4. 输出到 rule_keyword_curated.json

后续人工审校再覆盖导入。
"""
import json
import re
from collections import OrderedDict
from pathlib import Path

SRC = Path('process/refs/rule_keyword_extracted.original.json')
DST = Path('process/refs/rule_keyword_curated.json')

# 不导入的关键词（与 init_fuzzy_keyword.py 保持一致）
EXCLUDED_KEYWORDS = {'HOLDEXIST', 'VALVEEXIST'}
EXCLUDED_PREFIXES = ('injectstage', 'holdingstage', 'meteringstage')

# 统一模糊级别（Model 默认值）
DEFAULT_FUZZY_LEVEL = 5


def should_exclude(name: str) -> bool:
    if name in EXCLUDED_KEYWORDS:
        return True
    name_lower = name.lower()
    return any(name_lower.startswith(p) for p in EXCLUDED_PREFIXES)


def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f'原始: {len(data)} 条')

    # 1. 按 keyword_name 去重（保留首条）
    seen = set()
    deduped = []
    for record in data:
        name = record.get('keyword_name', '').strip()
        if not name or name in seen:
            continue
        seen.add(name)
        deduped.append(record)
    print(f'去重后: {len(deduped)} 条')

    # 2. 排除不导入
    filtered = [r for r in deduped if not should_exclude(r['keyword_name'])]
    excluded = len(deduped) - len(filtered)
    print(f'排除: {excluded} 条')
    print(f'最终: {len(filtered)} 条')

    # 3. 统一 fuzzy_level = 5
    for record in filtered:
        record['fuzzy_level'] = DEFAULT_FUZZY_LEVEL
        # 保留原 id 作为参考
        # 也可以删掉 id 让 curated 更干净（保留便于对照原数据）
    fuzzy_dist = {r['fuzzy_level'] for r in filtered}
    print(f'统一 fuzzy_level={DEFAULT_FUZZY_LEVEL}（当前集合: {fuzzy_dist}）')

    # 4. 写出（按 keyword_name 排序便于审校）
    filtered.sort(key=lambda r: r['keyword_name'])
    with open(DST, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    print(f'\n输出: {DST}')
    print(f'文件大小: {DST.stat().st_size} 字节')

    # 按类型统计
    from collections import Counter
    type_dist = Counter(r['keyword_type'] for r in filtered)
    print('\n按 keyword_type 分布:')
    for t, c in type_dist.most_common():
        print(f'  {t}: {c} 条')


if __name__ == '__main__':
    main()