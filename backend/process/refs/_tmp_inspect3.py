"""
检查 JSON 里是否有"分段参数"（如 injection_time_stage_1）
"""
import json
import re

with open(r'f:\items\moldingx\molding-optima\backend\process\refs\rule_keyword_extracted.json',
          'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. 查找以 stage 结尾的关键词
stage_pattern = re.compile(r'_stage\d+$|_stage$|_section\d+$|_seg\d+$', re.I)
print("=" * 70)
print("== 含 '_stage' / '_section' / '_seg' 的关键词 ==")
print("=" * 70)
matched = [d for d in data if stage_pattern.search(d['keyword_name'])]
for d in matched[:30]:
    print(f"  [{d['keyword_type']:<10}] {d['keyword_name']:<25} {d['description']}")
print(f"  ... 共 {len(matched)} 条\n")

# 2. 查找 injectstage/holdingstage/meteringstage 这些"激活位"
print("=" * 70)
print("== injectstage/holdingstage/meteringstage 类的激活位 ==")
print("=" * 70)
active_pattern = re.compile(r'^(inject|holding|metering)stage\d+$', re.I)
active_matched = [d for d in data if active_pattern.match(d['keyword_name'])]
print(f"  共 {len(active_matched)} 条")
for d in active_matched[:6]:
    print(f"  [{d['keyword_type']:<10}] {d['keyword_name']:<25} {d['description']}")
print()

# 3. 查找类似 BT1/BT2 的"段位物理参数"
print("=" * 70)
print("== 编号型参数（如 BT1/BT2、IP1/IP2）样本 ==")
print("=" * 70)
number_pattern = re.compile(r'^[A-Z]+\d+$')
num_matched = [d for d in data if number_pattern.match(d['keyword_name'])]
print(f"  共 {len(num_matched)} 条")
# 按类型分组
from collections import Counter
type_counter = Counter(d['keyword_type'] for d in num_matched)
for t, c in type_counter.most_common():
    print(f"  [{t}]: {c} 条")
print()
# 取样本
seen_names = set()
samples = []
for d in num_matched:
    # 取名字前缀作为代表（如 BT 代表料筒温度）
    prefix = re.match(r'^([A-Z]+)\d+$', d['keyword_name']).group(1)
    if prefix not in seen_names:
        seen_names.add(prefix)
        samples.append(d)
for d in samples[:20]:
    print(f"  [{d['keyword_type']:<6}] {d['keyword_name']:<10} {d['description']}")