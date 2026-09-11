"""验证 JSON 输出"""
import json

for filename in ["rule_keyword_extracted.json", "rule_method_extracted.json"]:
    path = f"F:\\items\\moldingx\\molding-optima\\backend\\process\\refs\\{filename}"
    data = json.load(open(path, encoding="utf-8"))
    ids = [d["id"] for d in data]
    print(f"\n=== {filename} ===")
    print(f"Total records: {len(data)}")
    print(f"First id: {data[0]['id']}")
    print(f"Last id: {data[-1]['id']}")
    print(f"Unique ids: {len(set(ids))}")
    duplicates = [x for x in set(ids) if ids.count(x) > 1]
    print(f"Duplicate ids: {len(duplicates)}")
    if duplicates[:5]:
        print(f"First duplicates: {sorted(duplicates)[:5]}")