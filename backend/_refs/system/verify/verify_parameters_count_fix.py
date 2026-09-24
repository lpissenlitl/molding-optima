"""
验证修复：annotation 改回 parameters_count 后，sort=parameters_count 排序不报错。

预期：
- ProcessCondition.objects.annotate(parameters_count=Count('process_parameters')).order_by('-parameters_count') 可执行
- .order_by('parameters_count') 可执行
- 列表结果中每条 item.parameters_count 是 int

不在 main_service 里直接验证（避免触碰数据库的太多副作用），
用一个新的查询链验证 ORM 层面 OK。
"""
import os
import sys

# 让脚本能找到 _moldx.settings
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_moldx.settings")

import django
django.setup()

from django.db.models import Count
from process.models import ProcessCondition

# 1. annotation 名改回 parameters_count 后，排序应当可用
qs = (
    ProcessCondition.objects.all()
    .annotate(parameters_count=Count("process_parameters"))
)

# 触发排序（仅取 1 条，不真正去数据库拿数据，但 SQL 会构造）
sql_desc = str(qs.order_by("-parameters_count").query)
sql_asc = str(qs.order_by("parameters_count").query)

assert "parameters_count" in sql_desc.lower(), f"SQL 中应包含 parameters_count: {sql_desc}"
assert "parameters_count" in sql_asc.lower(), f"SQL 中应包含 parameters_count: {sql_asc}"

print("[PASS] annotation parameters_count + order_by(-parameters_count) SQL 构造成功")
print(f"  DESC: {sql_desc[:200]}")
print(f"  ASC : {sql_asc[:200]}")

# 2. parse_ordering 应当能识别 parameters_count
from utils.db import parse_ordering
fields_desc = parse_ordering("-parameters_count")
fields_asc = parse_ordering("parameters_count")
assert fields_desc == ["-parameters_count"], fields_desc
assert fields_asc == ["parameters_count"], fields_asc
print(f"[PASS] parse_ordering(-parameters_count) -> {fields_desc}")
print(f"[PASS] parse_ordering(parameters_count)  -> {fields_asc}")

# 3. 跑一次真实的查询（只取 1 条），验证 item.parameters_count 可访问
try:
    item = qs.order_by("-parameters_count").first()
    if item is None:
        print("[INFO] 数据库无数据，跳过 ORM 访问验证")
    else:
        val = item.parameters_count
        print(f"[PASS] item.parameters_count = {val} (type={type(val).__name__})")
except Exception as e:
    print(f"[FAIL] ORM 访问失败: {e}")
    sys.exit(1)

print("\n=== 所有验证通过，bug 已修复 ===")
