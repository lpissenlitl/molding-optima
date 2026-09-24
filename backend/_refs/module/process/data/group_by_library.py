"""按 library_code 分组输出"""
import json
from collections import defaultdict

path = "F:\\items\\moldingx\\molding-optima\\backend\\process\\refs\\rule_method_extracted.json"
data = json.load(open(path, encoding="utf-8"))

# 按 library_code 分组
libraries = defaultdict(list)
for d in data:
    lib_code = d.get("library_code") or "_unknown"
    libraries[lib_code].append(d)

# 输出分组结果
output_path = "F:\\items\\moldingx\\molding-optima\\backend\\process\\refs\\rule_method_by_library.json"
result = {
    "_meta": {
        "total_records": len(data),
        "library_count": len(libraries),
        "libraries": {
            lib: len(records) for lib, records in sorted(libraries.items())
        },
    },
    "libraries": dict(libraries),
}

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"输出: {output_path}")
print(f"总计 {len(data)} 条规则，分布在 {len(libraries)} 个库")

# 列出每个库的中文名（如果有 product_type）
print("\n=== 每个库的产品类型 ===")
for lib_code in sorted(libraries.keys()):
    # 取该库第一条有 product_type 的记录
    product_types = set(d.get("product_type") for d in libraries[lib_code] if d.get("product_type"))
    rule_types = set(d.get("rule_type") for d in libraries[lib_code] if d.get("rule_type"))
    print(f"  {lib_code}:")
    print(f"    产品类型: {product_types or '(空)'}")
    print(f"    规则类型: {rule_types or '(空)'}")
    print(f"    规则数: {len(libraries[lib_code])}")