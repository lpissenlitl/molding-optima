"""
远程搜索建议服务（selection-options）

为前端 autocomplete 提供候选值：

- 只覆盖主数据实体（模具 / 注塑机 / 塑料 / 填充物 / 项目 / 辅机）
- table → model 走**显式白名单**，不接受任意表名拼接
- column 必须是目标 model 的文本字段（CharField / TextField），
  既保证 icontains 语义可用，也避免列名被当作 lookup 表达式注入
- 结果按 company_id 隔离，软删除由 SoftDeleteManager 自动过滤
"""
from django.apps import apps
from django.db.models import CharField, TextField

from extensions.exceptions import BizException, ERROR_ILLEGAL_ARGUMENT


# table → (app_label, model_name)
# 与前端 FormItem.query.table 的取值一一对应
TABLE_MODEL_MAP = {
    "auxiliary_equipment": ("masterdata", "AuxiliaryEquipment"),
    "filler": ("masterdata", "Filler"),
    "injection_molding_machine": ("masterdata", "InjectionMoldingMachine"),
    "mold": ("masterdata", "Mold"),
    "polymer": ("masterdata", "Polymer"),
    "project": ("masterdata", "Project"),
}

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _resolve_model(table: str):
    """按白名单解析 table → model"""
    key = (table or "").strip()
    if key not in TABLE_MODEL_MAP:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"不支持的 table: {table!r}")
    app_label, model_name = TABLE_MODEL_MAP[key]
    return apps.get_model(app_label, model_name)


def _check_column(model, column: str) -> str:
    """校验 column 是该 model 的文本字段，返回规范化后的列名"""
    name = (column or "").strip()
    if not name:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "column 不能为空")
    try:
        field = model._meta.get_field(name)
    except Exception:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"字段不存在: {name}")
    if not isinstance(field, (CharField, TextField)):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"字段不支持模糊搜索: {name}")
    return name


def get_selection_options(
    company_id,
    table: str,
    column: str,
    input_text: str = "",
    limit=None,
) -> list:
    """返回候选值列表 [{"value": ...}, ...]

    Args:
        company_id: 租户隔离字段（取 request.user.company_id）
        table: 白名单表 key
        column: 目标表的文本字段名
        input_text: 搜索关键词
        limit: 返回条数上限（None → DEFAULT_LIMIT，超过 MAX_LIMIT 截断）
    """
    model = _resolve_model(table)
    col = _check_column(model, column)

    try:
        n = int(limit) if limit else DEFAULT_LIMIT
    except (TypeError, ValueError):
        n = DEFAULT_LIMIT
    n = max(1, min(n, MAX_LIMIT))

    return model.get_prompt_list_of_column(
        column=col,
        input=input_text or "",
        limit=n,
        extra_filters={"company_id": company_id},
    )
