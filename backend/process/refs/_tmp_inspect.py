import json
from collections import Counter

with open(r'f:\items\moldingx\molding-optima\backend\process\refs\rule_keyword_extracted.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'总记录数: {len(data)}')
print(f'不同 keyword_name 数: {len(set(d["keyword_name"] for d in data))}')
print()
print('按 keyword_type 分组:')
type_counts = Counter(d['keyword_type'] for d in data)
for t, c in type_counts.most_common():
    print(f'  {t}: {c}')

print()
print('== 前 10 条样本 ==')
for d in data[:10]:
    print(f'  {d}')

print()
print('== 唯一 name 示例 (前 30 个) ==')
unique_names = sorted(set(d['keyword_name'] for d in data))
for n in unique_names[:30]:
    print(f'  {n}')

print()
print('== 各类型样本 (每种取 1 个) ==')
seen = set()
for d in data:
    t = d['keyword_type']
    if t not in seen:
        seen.add(t)
        print(f'  [{t}] {d}')
