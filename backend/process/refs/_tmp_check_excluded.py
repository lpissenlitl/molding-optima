"""
检查不导入的数据到底有多少条
"""
import json

with open(r'f:\items\moldingx\molding-optima\backend\process\refs\rule_keyword_extracted.json',
          'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. injectstage / holdingstage / meteringstage
from collections import Counter
import re

patterns = {
    'injectstage': re.compile(r'^injectstage\d+$', re.I),
    'holdingstage': re.compile(r'^holdingstage\d+$', re.I),
    'meteringstage': re.compile(r'^meteringstage\d+$', re.I),
}

for name, pat in patterns.items():
    matched = [d for d in data if pat.match(d['keyword_name'])]
    print(f'{name}: {len(matched)} 条')
    print(f"  唯一 keyword_name: {sorted(set(d['keyword_name'] for d in matched))}")

# 2. HOLDEXIST / VALVEEXIST
for kw in ['HOLDEXIST', 'VALVEEXIST']:
    matched = [d for d in data if d['keyword_name'] == kw]
    print(f'{kw}: {len(matched)} 条')
    for d in matched:
        print(f"  [{d['keyword_type']}] {d['description']}")

# 3. 总计应排除
all_excluded = []
for d in data:
    name = d['keyword_name']
    name_lower = name.lower()
    if name in ('HOLDEXIST', 'VALVEEXIST'):
        all_excluded.append(d)
    elif any(name_lower.startswith(p) for p in ('injectstage', 'holdingstage', 'meteringstage')):
        all_excluded.append(d)
print(f'\n应排除总计: {len(all_excluded)} 条')

# 4. 去重后剩多少
seen = set()
deduped = []
for d in data:
    if d['keyword_name'] in seen:
        continue
    seen.add(d['keyword_name'])
    deduped.append(d)
print(f'去重后: {len(deduped)} 条')

# 5. 去重后再排除
filtered = [d for d in deduped if d['keyword_name'] not in ('HOLDEXIST', 'VALVEEXIST')
            and not any(d['keyword_name'].lower().startswith(p) for p in ('injectstage', 'holdingstage', 'meteringstage'))]
print(f'去重+排除后: {len(filtered)} 条')
print(f'应排除: {len(deduped) - len(filtered)} 条')