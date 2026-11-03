"""
molding-optima 列表导出服务

为前端主数据列表页的"导出列表"按钮提供后端能力：
    POST /api/reports/export-list/  {"resource": "polymer_list", "ids": [1, 2]}
        -> {"url": "archives/export_lists/polymer_list_20260101_120000.xlsx", "count": 2}
    GET  /api/reports/download/<url>/
        -> Excel 文件流

设计要点：
- resource 白名单：只允许导出前端已接入的列表资源，避免任意表/任意列导出。
- 租户隔离：查询强制带 company_id，跨租户数据不会被导出。
- 导出列与前端列表列保持一致（表头文案沿用前端列定义），保证"所见即所得"。
"""
from datetime import date, datetime

from django.apps import apps
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT
from reporting.utils import build_export_list_path


# ==================== 资源白名单 ====================

# resource -> (app_label, model_name)
RESOURCE_MODEL_MAP = {
    "auxiliary_list": ("masterdata", "AuxiliaryEquipment"),
    "filler_list": ("masterdata", "Filler"),
    "injection_list": ("masterdata", "InjectionMoldingMachine"),
    "polymer_list": ("masterdata", "Polymer"),
}

# resource -> Excel 工作表名称
RESOURCE_SHEET_TITLE = {
    "auxiliary_list": "辅助设备",
    "filler_list": "填充物",
    "injection_list": "注塑机",
    "polymer_list": "塑料",
}

# 单次导出上限（防止超大导出拖垮服务）
MAX_EXPORT_ROWS = 5000


# ==================== 取值辅助 ====================

def _format_value(value):
    """单元格取值格式化：空值转空串，日期/时间转标准文本"""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return value


def _field(obj, field_name):
    """读取模型字段并格式化"""
    return _format_value(getattr(obj, field_name, None))


def _unit_values(obj, field_name):
    """注射单元多值列：按射台顺序用 " / " 拼接（与前端列表页一致）"""
    units = obj.injection_units.all()
    values = []
    for unit in units:
        value = getattr(unit, field_name, None)
        if value is not None:
            values.append(str(value))
    return " / ".join(values)


def _range_text(min_value, max_value, unit):
    """区间文本：min - max（与前端列表页一致）"""
    if min_value is not None and max_value is not None:
        return f"{min_value} - {max_value} {unit}"
    if min_value is not None:
        return f"{min_value} {unit}"
    if max_value is not None:
        return f"{max_value} {unit}"
    return ""


# ==================== 导出列定义 ====================
# 每列 = (表头, 取值函数)；表头与前端列表页列标签保持一致

def _auxiliary_columns():
    return [
        ("名称", lambda o: _field(o, "equipment_name")),
        ("类型", lambda o: _field(o, "equipment_type")),
        ("规格", lambda o: _field(o, "specification")),
        ("数量", lambda o: _field(o, "total_count")),
        ("可用数量", lambda o: _field(o, "available_count")),
        ("备注", lambda o: _field(o, "remarks")),
        ("更新日期", lambda o: _field(o, "updated_at")),
    ]


def _filler_columns():
    return [
        ("名称", lambda o: _field(o, "name")),
        ("缩写", lambda o: _field(o, "abbreviation")),
        ("类别", lambda o: _field(o, "category")),
        ("形状", lambda o: _field(o, "shape")),
        ("中位粒径 D50 [μm]", lambda o: _field(o, "particle_size_d50")),
        ("长径比", lambda o: _field(o, "aspect_ratio")),
        ("含水率 [%]", lambda o: _field(o, "moisture_content")),
        ("表面处理", lambda o: _field(o, "surface_treatment")),
        ("密度 [g/cm³]", lambda o: _field(o, "density")),
        ("热稳定温度 [℃]", lambda o: _field(o, "thermal_stability_temp")),
        ("颜色", lambda o: _field(o, "color")),
        ("更新日期", lambda o: _field(o, "updated_at")),
    ]


def _injection_columns():
    return [
        ("品牌", lambda o: _field(o, "brand")),
        ("设备型号", lambda o: _field(o, "model")),
        ("设备编号", lambda o: _field(o, "device_no")),
        ("设备位置", lambda o: _field(o, "location")),
        ("设备类型", lambda o: _field(o, "machine_type")),
        ("驱动系统", lambda o: _field(o, "drive_system")),
        ("最大注射重量(g)", lambda o: _unit_values(o, "max_injection_weight")),
        ("最大注射速度(mm/s)", lambda o: _unit_values(o, "max_injection_speed")),
        ("最大注射行程(mm)", lambda o: _unit_values(o, "max_injection_stroke")),
        ("最大注射压力(MPa)", lambda o: _unit_values(o, "max_injection_pressure")),
        ("最大保压压力(MPa)", lambda o: _unit_values(o, "max_holding_pressure")),
        ("最大螺杆转速(rpm)", lambda o: _unit_values(o, "max_screw_rotation_speed")),
        ("塑化能力(g/h)", lambda o: _unit_values(o, "plasticizing_capacity")),
        ("螺杆直径(mm)", lambda o: _unit_values(o, "screw_diameter")),
        ("投产日期", lambda o: _field(o, "commissioning_date")),
        ("更新日期", lambda o: _field(o, "updated_at")),
    ]


def _polymer_columns():
    return [
        ("塑料厂商", lambda o: _field(o, "manufacturer")),
        ("塑料简称", lambda o: _field(o, "abbreviation")),
        ("塑料牌号", lambda o: _field(o, "grade")),
        ("塑料类别", lambda o: _field(o, "category")),
        ("数据来源", lambda o: _field(o, "data_source")),
        ("等级代码", lambda o: _field(o, "level_code")),
        ("供应商代码", lambda o: _field(o, "vendor_code")),
        ("推荐成型温度(℃)", lambda o: _field(o, "recommended_melt_temp")),
        ("塑料降解温度(℃)", lambda o: _field(o, "degradation_temp")),
        ("推荐模具温度(℃)", lambda o: _field(o, "recommended_mold_temp")),
        ("推荐顶出温度(℃)", lambda o: _field(o, "ejection_temp")),
        ("推荐剪切线速度(mm/s)", lambda o: _field(o, "recommended_shear_line_speed")),
        ("推荐注射速率(cm³/s)", lambda o: _field(o, "recommend_injection_rate")),
        ("推荐背压(MPa)", lambda o: _field(o, "recommend_back_pressure")),
        ("干燥方式", lambda o: _field(o, "drying_method")),
        ("干燥温度(℃)", lambda o: _range_text(o.drying_temp_min, o.drying_temp_max, "℃")),
        ("干燥时间(h)", lambda o: _range_text(o.drying_time_min, o.drying_time_max, "h")),
        ("更新日期", lambda o: _field(o, "updated_at")),
    ]


RESOURCE_COLUMNS = {
    "auxiliary_list": _auxiliary_columns,
    "filler_list": _filler_columns,
    "injection_list": _injection_columns,
    "polymer_list": _polymer_columns,
}


# ==================== 服务函数 ====================

def _resolve_model(resource: str):
    """按白名单解析模型"""
    key = (resource or "").strip()
    if key not in RESOURCE_MODEL_MAP:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"不支持的 resource: {resource!r}")
    app_label, model_name = RESOURCE_MODEL_MAP[key]
    return apps.get_model(app_label, model_name)


def _validate_ids(ids) -> list:
    """校验导出 ID 列表"""
    if not ids:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "ids 不能为空")
    try:
        id_list = [int(i) for i in ids]
    except (TypeError, ValueError):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "ids 必须为整数列表")
    if not id_list:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "ids 不能为空")
    if len(id_list) > MAX_EXPORT_ROWS:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"单次最多导出 {MAX_EXPORT_ROWS} 条数据")
    # 去重并保持顺序
    return list(dict.fromkeys(id_list))


def export_list(company_id: int, tenant_slug: str, resource: str, ids: list) -> dict:
    """导出列表数据到 Excel

    Args:
        company_id: 租户公司 ID（强制隔离）
        tenant_slug: 租户标识（存储目录）
        resource: 导出资源（白名单 key）
        ids: 待导出的数据 ID 列表

    Returns:
        dict: {"url": 相对路径, "count": 导出条数, "resource": 资源名}
    """
    model = _resolve_model(resource)
    columns = RESOURCE_COLUMNS[resource]()
    id_list = _validate_ids(ids)

    queryset = model.objects.filter(id__in=id_list, company_id=company_id)
    if resource == "injection_list":
        queryset = queryset.prefetch_related("injection_units")

    rows = list(queryset.order_by("id"))
    if not rows:
        raise BizException(ERROR_DATA_NOT_FOUND, "未找到可导出的数据")

    template_name = f"{resource}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    full_path, relative_path = build_export_list_path(tenant_slug, template_name, "xlsx")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = RESOURCE_SHEET_TITLE.get(resource, "导出数据")

    # 表头
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    for col_idx, (header, _getter) in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # 数据行
    for row_idx, obj in enumerate(rows, start=2):
        for col_idx, (_header, getter) in enumerate(columns, start=1):
            sheet.cell(row=row_idx, column=col_idx, value=getter(obj))

    # 列宽
    for col_idx, (header, _getter) in enumerate(columns, start=1):
        width = max(12, min(len(header) * 2 + 4, 32))
        sheet.column_dimensions[get_column_letter(col_idx)].width = width

    workbook.save(full_path)

    return {
        "url": relative_path,
        "count": len(rows),
        "resource": resource,
    }
