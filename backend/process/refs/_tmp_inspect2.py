"""
按 5 类分别采样 8-15 条 + 看 model 字段，看哪些细分可能是后期冗余的
"""
import json
from collections import Counter, defaultdict

with open(r'f:\items\moldingx\molding-optima\backend\process\refs\rule_keyword_extracted.json',
          'r', encoding='utf-8') as f:
    data = json.load(f)

by_type = defaultdict(list)
for d in data:
    by_type[d['keyword_type']].append(d)

print("=" * 70)
print("== 缺陷 (17 条) - 看是否真有质量描述 ==")
print("=" * 70)
for d in by_type['缺陷']:
    print(f"  [{d['keyword_name']:<20}] {d['description']}")

print()
print("=" * 70)
print("== 缺陷位置 (110 条) - 看是否描述位置信息 ==")
print("=" * 70)
for d in by_type['缺陷位置'][:15]:
    print(f"  [{d['keyword_name']:<25}] {d['description']}")
print(f"  ... 还有 {len(by_type['缺陷位置']) - 15} 条")

print()
print("=" * 70)
print("== 非工艺参数 (36 条) - 看是否真的不属于工艺 ==")
print("=" * 70)
for d in by_type['非工艺参数']:
    print(f"  [{d['keyword_name']:<25}] {d['description']}")

print()
print("=" * 70)
print("== 其他 (1 条) ==")
print("=" * 70)
for d in by_type['其他']:
    print(f"  [{d['keyword_name']:<25}] {d['description']}")