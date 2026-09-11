"""检查 deleted 字段"""
import json

path = "F:\\items\\moldingx\\molding-optima\\backend\\process\\refs\\rule_keyword_extracted.json"
data = json.load(open(path, encoding="utf-8"))

# 看看是否有 deleted 字段
if data and "deleted" in data[0]:
    print("Has 'deleted' field")
    deleted_count = sum(1 for d in data if d.get("deleted") == 1)
    print(f"Deleted records: {deleted_count}")
else:
    print("No 'deleted' field in extracted data")

# 看看完整字段
print(f"\nFields in first record: {list(data[0].keys())}")

# 检查 id 范围
ids = sorted([d["id"] for d in data])
print(f"\nID gaps:")
prev_id = 0
gaps = []
for current_id in ids:
    if current_id - prev_id > 1:
        gaps.append((prev_id, current_id))
    prev_id = current_id
print(f"Total gaps: {len(gaps)}")
print(f"First 10 gaps: {gaps[:10]}")

# 看一组中间 id 的数据
print("\nMiddle data (around id 1700):")
middle = [d for d in data if 1690 < d["id"] < 1710]
for d in middle:
    print(f"  id={d['id']}, name={d.get('keyword_name')}, type={d.get('keyword_type')}")