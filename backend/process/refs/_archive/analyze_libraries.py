"""分析各库之间的关系：重复还是互不相关？"""
import json
from collections import Counter, defaultdict

path = "F:\\items\\moldingx\\molding-optima\\backend\\process\\refs\\rule_method_by_library.json"
data = json.load(open(path, encoding="utf-8"))

libraries = data["libraries"]

# 1. 每个库的 defect_code 分布
print("=== 1. 每个库覆盖的缺陷类型 ===")
lib_defects = {}
for lib_code, rules in libraries.items():
    defects = Counter(r.get("defect_code") for r in rules if r.get("defect_code"))
    lib_defects[lib_code] = set(defects.keys())

# 显示每个库的特征缺陷
for lib_code in sorted(libraries.keys()):
    defects = lib_defects[lib_code]
    print(f"\n{lib_code} ({len(libraries[lib_code])} 条):")
    for d, c in sorted(Counter(r.get("defect_code") for r in libraries[lib_code]).items(), key=lambda x: -x[1]):
        print(f"  {d}: {c}")

# 2. 库之间的覆盖关系（共享缺陷）
print("\n\n=== 2. 缺陷覆盖矩阵 ===")
all_defects = sorted(set().union(*lib_defects.values()))
matrix = {}
for lib in libraries:
    matrix[lib] = {d: d in lib_defects[lib] for d in all_defects}

# 输出每个缺陷被哪些库覆盖
for defect in all_defects:
    libs_with_defect = [lib for lib in libraries if matrix[lib][defect]]
    if len(libs_with_defect) > 1:
        print(f"  {defect} ({len(libs_with_defect)} 个库): {libs_with_defect}")

# 3. 库之间的关系：重合度
print("\n\n=== 3. 库之间的重合度 ===")
lib_codes = sorted(libraries.keys())
for i, lib1 in enumerate(lib_codes):
    for lib2 in lib_codes[i+1:]:
        set1 = lib_defects[lib1]
        set2 = lib_defects[lib2]
        if set1 or set2:
            intersection = set1 & set2
            union = set1 | set2
            jaccard = len(intersection) / len(union) if union else 0
            if jaccard > 0:
                print(f"  {lib1} ∩ {lib2}: {len(intersection)} 共享缺陷, Jaccard={jaccard:.2%}")

# 4. 基础库与其他库的关系
print("\n\n=== 4. 基础库是否被其他库完整继承？ ===")
base_lib = "基础库"
if base_lib in lib_defects:
    base_defects = lib_defects[base_lib]
    for lib in libraries:
        if lib == base_lib:
            continue
        lib_d = lib_defects[lib]
        new_defects = lib_d - base_defects
        shared = lib_d & base_defects
        print(f"  {lib}:")
        print(f"    共享基础库缺陷: {len(shared)}/{len(lib_d)}")
        print(f"    新增缺陷: {sorted(new_defects) if new_defects else '(无)'}")
        print(f"    基础库没有的: {sorted(lib_d - base_defects)[:5]}{'...' if len(lib_d - base_defects) > 5 else ''}")

# 5. 看几个具体例子：相同 defect_code 的规则在不同库中是否一样
print("\n\n=== 5. 同缺陷跨库对比示例 ===")
sample_defects = ["SHORTSHOT", "BURN", "WARPING"]
for defect in sample_defects:
    if defect not in all_defects:
        continue
    print(f"\n[{defect}]")
    for lib in libraries:
        rules_with_defect = [r for r in libraries[lib] if r.get("defect_code") == defect]
        if rules_with_defect:
            unique_rules = set(r.get("rule_description", "").strip() for r in rules_with_defect)
            print(f"  {lib}: {len(rules_with_defect)} 条, {len(unique_rules)} 唯一规则")
            # 显示前 2 个
            for r in rules_with_defect[:2]:
                print(f"    - {r.get('rule_description', '').strip()}")