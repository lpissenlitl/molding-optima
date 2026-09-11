"""按 library_code 分组统计"""
import json
from collections import Counter

path = "F:\\items\\moldingx\\molding-optima\\backend\\process\\refs\\rule_method_extracted.json"
data = json.load(open(path, encoding="utf-8"))

# 按 library_code 分组
library_counter = Counter(d.get("library_code") for d in data)
print("=== 按 library_code 分组统计 ===")
for lib, count in sorted(library_counter.items(), key=lambda x: -x[1]):
    print(f"  {lib}: {count} 条")

# 按 product_type 分组
print("\n=== 按 product_type 分组统计 ===")
type_counter = Counter(d.get("product_type") for d in data)
for pt, count in sorted(type_counter.items(), key=lambda x: -x[1]):
    print(f"  {pt}: {count} 条")

# 按 rule_type 分组
print("\n=== 按 rule_type 分组统计 ===")
rule_type_counter = Counter(d.get("rule_type") for d in data)
for rt, count in sorted(rule_type_counter.items(), key=lambda x: -x[1]):
    print(f"  {rt}: {count} 条")

# 检查重复规则（同一 library_code + rule_description）
print("\n=== 重复规则检查（同 library_code + rule_description）===")
seen = {}
duplicates = []
for d in data:
    key = (d.get("library_code"), d.get("rule_description"))
    if key in seen:
        duplicates.append((seen[key], d))
    else:
        seen[key] = d

print(f"重复组数: {len(duplicates)}")
if duplicates:
    print("前 5 个重复:")
    for orig, dup in duplicates[:5]:
        print(f"  id={orig['id']} 与 id={dup['id']}: {orig.get('rule_description')}")

# 展示一个完整记录
print("\n=== 一条完整记录示例 ===")
for d in data:
    if d.get("library_code") and d.get("library_code") != "基础类":
        print(json.dumps(d, ensure_ascii=False, indent=2))
        break