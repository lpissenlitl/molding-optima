"""检查 subrule_no / rule_type 字段（rule_library 标识）"""
import json
import re
from pathlib import Path

# 从原始 SQL 读取
sql_text = Path("F:\\items\\moldingx\\molding-optima\\backend\\process\\refs\\Dump20260910.sql").read_text(encoding="utf-8")

# 提取 rule_method 的 INSERT 语句
pattern = r"INSERT INTO `rule_method` VALUES\s*(.+?);"
match = re.search(pattern, sql_text, re.DOTALL)
if match:
    values_block = match.group(1)

# 简单解析：看几个示例数据
samples = values_block[:1500]
print("=== 前 1500 字符 ===")
print(samples)
print("\n=== 末尾 1500 字符 ===")
print(values_block[-1500:])