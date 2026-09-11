"""
从 SQL dump 文件中提取 rule_keyword 和 rule_method 数据，
映射到新字段格式，输出为 JSON 文件。
"""
import json
import re
from pathlib import Path

# ---- 配置 ----
SQL_FILE = Path(__file__).parent / "Dump20260910.sql"
OUTPUT_DIR = Path(__file__).parent

# ---- 字段映射 ----
# rule_keyword: 旧字段 → 新字段
KEYWORD_FIELD_MAP = {
    "id": "id",
    "name": "keyword_name",
    "level": "fuzzy_level",
    "all_range_min": "range_min",
    "all_range_max": "range_max",
    "action_range_min": "action_range_min",
    "action_range_max": "action_range_max",
    "action_max_val": "action_max_val",
    "keyword_type": "keyword_type",
    "comment": "description",  # 字段名差异: comment → description
    "subrule_no": "_ignore_subrule_no",
    "product_small_type": "_ignore_product_small_type",
    "polymer_abbreviation": "_ignore_polymer_abbreviation",
    "rule_type": "_ignore_rule_type",
    "show_on_page": "_ignore_show_on_page",
}

# rule_keyword 字段顺序（CREATE TABLE 中）
KEYWORD_FIELD_ORDER = [
    "id", "name", "level",
    "all_range_min", "all_range_max",
    "action_range_min", "action_range_max", "action_max_val",
    "keyword_type", "comment",
    "created_at", "updated_at", "deleted",
    "subrule_no", "product_small_type",
    "polymer_abbreviation", "rule_type", "show_on_page",
]

# rule_method 字段顺序
METHOD_FIELD_ORDER = [
    "id",
    "polymer_abbreviation", "product_type",
    "rule_description", "rule_explanation",
    "is_auto", "enable",
    "created_at", "updated_at", "deleted",
    "product_small_type",
    "defect_name", "defect_desc",
    "subrule_no", "rule_type", "priority",
]

# rule_method: 旧字段 → 新字段
METHOD_FIELD_MAP = {
    "id": "id",
    "polymer_abbreviation": "polymer_abbreviation",
    "product_type": "product_category",  # 重命名
    "rule_description": "rule_description",
    "rule_explanation": "rule_explanation",
    "enable": "is_active",  # 重命名
    "product_small_type": "product_type",  # 产品小类型
    "defect_name": "defect_label",  # 重命名
    "defect_desc": "defect_code",  # 重命名
    "subrule_no": "library_code",  # 子规则库编号 → 作为 library_code
    "rule_type": "rule_type",  # 规则类型
    "priority": "priority",
}


def parse_sql_value(val: str):
    """解析 SQL 单个值"""
    val = val.strip()
    if val == "NULL":
        return None
    if val.startswith("'") and val.endswith("'"):
        # 字符串：去掉引号，处理转义
        inner = val[1:-1].replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")
        return inner
    # 数字
    if "." in val:
        try:
            return float(val)
        except ValueError:
            return val
    try:
        return int(val)
    except ValueError:
        return val


def split_sql_values(line: str) -> list[str]:
    """拆分 SQL VALUES 行，正确处理引号内的逗号"""
    values = []
    current = ""
    in_quote = False
    escape = False

    for char in line:
        if escape:
            current += char
            escape = False
            continue
        if char == "\\":
            current += char
            escape = True
            continue
        if char == "'":
            in_quote = not in_quote
            current += char
            continue
        if char == "," and not in_quote:
            values.append(current)
            current = ""
            continue
        current += char

    if current:
        values.append(current)
    return values


def extract_insert_data(sql_text: str, table_name: str) -> list[tuple]:
    """提取指定表的 INSERT 数据，返回原始字段元组列表"""
    pattern = rf"INSERT INTO `{table_name}` VALUES\s*(.+?);"
    match = re.search(pattern, sql_text, re.DOTALL)
    if not match:
        return []

    values_block = match.group(1)
    # 拆分行（每行一个 VALUES tuple）
    raw_tuples = re.findall(r"\(([^)]+(?:\([^)]*\)[^)]*)*)\)", values_block, re.DOTALL)
    # 简化：按 ); 拆分 + 最后一个
    raw_tuples = re.findall(r"\((.+?)\)(?:,|;|$)", values_block)

    result = []
    for raw in raw_tuples:
        values = split_sql_values(raw)
        parsed = [parse_sql_value(v) for v in values]
        result.append(parsed)

    return result


def map_record(values: list, field_order: list, field_map: dict) -> dict | None:
    """将原始值映射到新字段格式"""
    if len(values) != len(field_order):
        return None  # 字段数不匹配

    record = {}
    for i, old_field in enumerate(field_order):
        new_field = field_map.get(old_field)
        if new_field is None:
            continue  # 字段不在映射表中
        if new_field.startswith("_ignore_"):
            continue  # 显式忽略
        record[new_field] = values[i]

    return record


def main():
    print(f"读取 SQL 文件: {SQL_FILE}")
    sql_text = SQL_FILE.read_text(encoding="utf-8")

    # ---- rule_keyword ----
    print("\n提取 rule_keyword 数据...")
    keyword_raw = extract_insert_data(sql_text, "rule_keyword")
    print(f"  原始记录数: {len(keyword_raw)}")

    keywords = []
    for values in keyword_raw:
        record = map_record(values, KEYWORD_FIELD_ORDER, KEYWORD_FIELD_MAP)
        if record and record.get("keyword_name"):
            keywords.append(record)

    print(f"  有效记录数: {len(keywords)}")

    keyword_output = OUTPUT_DIR / "rule_keyword_extracted.json"
    keyword_output.write_text(
        json.dumps(keywords, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  输出: {keyword_output}")

    # ---- rule_method ----
    print("\n提取 rule_method 数据...")
    method_raw = extract_insert_data(sql_text, "rule_method")
    print(f"  原始记录数: {len(method_raw)}")

    methods = []
    for values in method_raw:
        record = map_record(values, METHOD_FIELD_ORDER, METHOD_FIELD_MAP)
        if record and record.get("rule_description"):
            methods.append(record)

    print(f"  有效记录数: {len(methods)}")

    method_output = OUTPUT_DIR / "rule_method_extracted.json"
    method_output.write_text(
        json.dumps(methods, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  输出: {method_output}")

    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()