"""
molding-optima 工艺参数导出服务

仅服务于 process app，不集成试模/模流相关的报告。

导出结构（每行 = 一条工艺档案的档案参数）：
    工艺条件编号 | 工艺参数编号 | 序列序号 | 参数来源 | <模板决定的具体参数列>
    每个工艺条件只导一行（取最新一条 parameter = 档案参数），
    调机过程的中间轮次不属于工艺档案，不导出。

三档模板：
    compact  精简总览：各段第 1 段 + 关键单值（约 20 列）
    default  标准工艺卡：全量工艺参数（约 86 列）
    detail   追溯用：default + 工艺上下文（前端输入）
"""
import json
from datetime import date, datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from extensions.exceptions import BizException, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT
from reporting.utils import build_export_list_path


# ==================== 导出模板 ====================

TEMPLATE_COMPACT = "compact"
TEMPLATE_DEFAULT = "default"
TEMPLATE_DETAIL = "detail"

VALID_TEMPLATES = (TEMPLATE_COMPACT, TEMPLATE_DEFAULT, TEMPLATE_DETAIL)


# --- 固定头列（所有模板都含）---
HEADER_FIELDS = [
    ("condition_no", "工艺条件编号"),
    ("parameter_no", "工艺参数编号"),
    ("seq_idx", "序列序号"),
    ("param_source", "参数来源"),
]


# --- compact：各段第 1 段 + 关键单值 ---
COMPACT_FIELDS = [
    ("inj_stg", "注射段数"),
    ("inj_spd_1", "一段注射速度"),
    ("inj_pres_1", "一段注射压力"),
    ("inj_pos_1", "一段注射位置"),
    ("inj_t", "注射时间"),
    ("inj_dly_t", "注射延时"),
    ("hold_stg", "保压段数"),
    ("hold_pres_1", "一段保压压力"),
    ("cool_t", "冷却时间"),
    ("met_stg", "熔胶段数"),
    ("met_pres_1", "一段熔胶压力"),
    ("met_lim_t", "熔胶延时"),
    ("met_end_pos", "熔胶终止位置"),
    ("brl_temp_stg", "料筒温度档数"),
    ("brl_temp_1", "一段料筒温度"),
    ("noz_temp", "喷嘴温度"),
]


# --- default：compact 之外的全量工艺参数 ---
DEFAULT_EXTRA_FIELDS = [
    # --- VP 切换 ---
    ("vps_mode", "VP切换模式"),
    ("vps_pos", "VP切换位置"),
    ("vps_t", "VP切换时间"),
    ("vps_pres", "VP切换压力"),
    ("vps_spd", "VP切换速度"),
    # --- 注射 2~6 段 ---
    ("inj_spd_2", "二段注射速度"),
    ("inj_spd_3", "三段注射速度"),
    ("inj_spd_4", "四段注射速度"),
    ("inj_spd_5", "五段注射速度"),
    ("inj_spd_6", "六段注射速度"),
    ("inj_pres_2", "二段注射压力"),
    ("inj_pres_3", "三段注射压力"),
    ("inj_pres_4", "四段注射压力"),
    ("inj_pres_5", "五段注射压力"),
    ("inj_pres_6", "六段注射压力"),
    ("inj_pos_2", "二段注射位置"),
    ("inj_pos_3", "三段注射位置"),
    ("inj_pos_4", "四段注射位置"),
    ("inj_pos_5", "五段注射位置"),
    ("inj_pos_6", "六段注射位置"),
    # --- 保压 2~5 段 + 各段时间 ---
    ("hold_pres_2", "二段保压压力"),
    ("hold_pres_3", "三段保压压力"),
    ("hold_pres_4", "四段保压压力"),
    ("hold_pres_5", "五段保压压力"),
    ("hold_spd_1", "一段保压速度"),
    ("hold_spd_2", "二段保压速度"),
    ("hold_spd_3", "三段保压速度"),
    ("hold_spd_4", "四段保压速度"),
    ("hold_spd_5", "五段保压速度"),
    ("hold_t_1", "一段保压时间"),
    ("hold_t_2", "二段保压时间"),
    ("hold_t_3", "三段保压时间"),
    ("hold_t_4", "四段保压时间"),
    ("hold_t_5", "五段保压时间"),
    # --- 熔胶 1~4 段 ---
    ("met_pres_2", "二段熔胶压力"),
    ("met_pres_3", "三段熔胶压力"),
    ("met_pres_4", "四段熔胶压力"),
    ("met_rot_spd_1", "一段螺杆转速"),
    ("met_rot_spd_2", "二段螺杆转速"),
    ("met_rot_spd_3", "三段螺杆转速"),
    ("met_rot_spd_4", "四段螺杆转速"),
    ("met_back_pres_1", "一段背压"),
    ("met_back_pres_2", "二段背压"),
    ("met_back_pres_3", "三段背压"),
    ("met_back_pres_4", "四段背压"),
    ("met_pos_1", "一段熔胶位置"),
    ("met_pos_2", "二段熔胶位置"),
    ("met_pos_3", "三段熔胶位置"),
    ("met_pos_4", "四段熔胶位置"),
    # --- 熔胶前松退 ---
    ("pre_met_decomp_mode", "熔胶前松退模式"),
    ("pre_met_decomp_pres", "熔胶前松退压力"),
    ("pre_met_decomp_spd", "熔胶前松退速度"),
    ("pre_met_decomp_t", "熔胶前松退时间"),
    ("pre_met_decomp_dist", "熔胶前松退距离"),
    # --- 熔胶后松退 ---
    ("pst_met_decomp_mode", "熔胶后松退模式"),
    ("pst_met_decomp_pres", "熔胶后松退压力"),
    ("pst_met_decomp_spd", "熔胶后松退速度"),
    ("pst_met_decomp_t", "熔胶后松退时间"),
    ("pst_met_decomp_dist", "熔胶后松退距离"),
    # --- 料筒温度 2~9 段 ---
    ("brl_temp_2", "二段料筒温度"),
    ("brl_temp_3", "三段料筒温度"),
    ("brl_temp_4", "四段料筒温度"),
    ("brl_temp_5", "五段料筒温度"),
    ("brl_temp_6", "六段料筒温度"),
    ("brl_temp_7", "七段料筒温度"),
    ("brl_temp_8", "八段料筒温度"),
    ("brl_temp_9", "九段料筒温度"),
]


# --- detail：default 之外追加的追溯列 ---
DETAIL_EXTRA_FIELDS = [
    ("__process_context__", "工艺上下文"),
]


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


def _json_text(value):
    """JSON 字段转可读文本"""
    if value in (None, "", {}, []):
        return ""
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(value)


def _resolve_columns(template: str):
    """按模板组装列定义"""
    if template == TEMPLATE_COMPACT:
        return HEADER_FIELDS + COMPACT_FIELDS
    if template == TEMPLATE_DETAIL:
        return HEADER_FIELDS + COMPACT_FIELDS + DEFAULT_EXTRA_FIELDS + DETAIL_EXTRA_FIELDS
    return HEADER_FIELDS + COMPACT_FIELDS + DEFAULT_EXTRA_FIELDS


def _resolve_template(template) -> str:
    """校验导出模板"""
    name = (template or TEMPLATE_DEFAULT).strip()
    if name not in VALID_TEMPLATES:
        raise BizException(
            ERROR_ILLEGAL_ARGUMENT,
            f"不支持的模板: {template!r}（可选 {', '.join(VALID_TEMPLATES)}）",
        )
    return name


def _validate_ids(ids) -> list:
    """校验工艺条件 ID 列表"""
    if not ids:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "process_condition_ids 不能为空")
    try:
        id_list = [int(i) for i in ids]
    except (TypeError, ValueError):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "process_condition_ids 必须为整数列表")
    if not id_list:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "process_condition_ids 不能为空")
    return list(dict.fromkeys(id_list))


# ==================== 导出主流程 ====================

def export_process_parameters(
    company_id: int,
    tenant_slug: str,
    process_condition_ids: list,
    template: str = TEMPLATE_DEFAULT,
    include_snapshots: bool = False,
):
    """
    导出工艺参数到 Excel 文件。

    Args:
        company_id: 租户公司 ID（强制隔离）
        tenant_slug: 租户标识（存储目录）
        process_condition_ids: 工艺条件 ID 列表
        template: 导出模板（compact / default / detail）
        include_snapshots: 是否追加"工艺条件快照"列

    Returns:
        dict: {"url", "relative_path", "count", "template", "include_snapshots"}
    """
    # 延迟导入 process 模型，避免循环依赖
    from process.models import ProcessCondition, ProcessParameter

    template = _resolve_template(template)
    id_list = _validate_ids(process_condition_ids)

    conditions = ProcessCondition.objects.filter(
        id__in=id_list,
        company_id=company_id,
        is_deleted=False,
    ).prefetch_related("process_parameters")

    if not conditions.exists():
        raise BizException(ERROR_DATA_NOT_FOUND, "未找到任何匹配的工艺条件")

    columns = _resolve_columns(template)
    param_source_labels = dict(ProcessParameter.PARAMETER_SOURCE_CHOICES)

    template_name = f"process_parameters_{template}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    full_path, relative_path = build_export_list_path(tenant_slug, template_name, "xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "工艺参数"

    # --- 表头 ---
    headers = [zh for _, zh in columns]
    if include_snapshots:
        headers.append("工艺条件快照")

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # --- 数据行 ---
    row = 2
    for condition in conditions:
        # 工艺档案一条记录只表示一个工艺参数：只取最新一条（档案参数），
        # 调机过程的中间轮次不进入档案导出
        param = (
            condition.process_parameters
            .filter(is_deleted=False)
            .order_by("-created_at", "-id")
            .first()
        )
        if param is None:
            continue
        for col_idx, (field, _) in enumerate(columns, start=1):
            if field == "condition_no":
                value = condition.condition_no
            elif field == "param_source":
                value = param_source_labels.get(param.param_source, param.param_source)
            elif field == "__process_context__":
                value = _json_text(condition.process_context)
            else:
                value = _format_value(getattr(param, field, None))
            ws.cell(row=row, column=col_idx, value=value)

        if include_snapshots:
            ws.cell(row=row, column=len(headers), value=_json_text(condition.process_context_snapshot))

        row += 1

    # --- 列宽（>26 列时用 get_column_letter，不能用 chr 拼接）---
    for col_idx, header in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = max(12, min(len(header) * 2 + 4, 32))

    wb.save(full_path)

    return {
        "url": relative_path,
        "relative_path": relative_path,
        "count": row - 2,
        "template": template,
        "include_snapshots": include_snapshots,
    }
