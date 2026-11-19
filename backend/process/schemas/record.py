"""molding-optima 工艺记录 Schema 定义。

对应 URL 段: /api/processes/records/  业务对象 ID: condition_id
(具体路由见 process/urls.py 的 records 段)

records 段业务: 工艺条件 CRUD + 工艺参数只读子视图 (parameter-list / parameter-tree)
              + 调机历史 + 前端嵌套写入

schema 契约:
- ProcessRecordListSchema            列表 (继承 ProcessConditionListSchema, 视图维度 view_type="parameter")
- ProcessConditionAndParameterSchema 创建 (POST /api/processes/records/, condition + 可选 parameter)
- ProcessConditionWriteSchema        更新 condition (PUT /api/processes/records/<int:condition_id>/, 仅 condition)
- ProcessRecordBatchDeleteSchema     批量删除 (DELETE /api/processes/records/actions/batch-delete/)

注: parameter 的读写走 parameters 段 (单段 URL /api/processes/parameters/<int:parameter_id>/),
    其写入契约见 parameter.py::ProcessParameterUpdateSchema。
"""
from typing import Optional

from pydantic import Field

from extensions.schemas import BaseSchema

from .condition import ProcessConditionListSchema, ProcessConditionSchema
from .parameter import ProcessParameterNestSchema


class ProcessConditionAndParameterSchema(BaseSchema):
    """工艺条件 + 第一条 parameter (POST /api/processes/records/ 写入契约)。

    condition:  必填 (强验证, 与 ProcessCondition model 对齐)
    parameter:  可选 (parameter 业务容器, 当前含 setting_process, 未来可扩展)
    """

    condition: ProcessConditionSchema = Field(..., description="工艺条件 (强验证)")
    parameter: ProcessParameterNestSchema = Field(
        None,
        description=(
            "parameter 业务容器 (当前含 setting_process, 未来可扩展)。"
            "不传或为 null 时不创建空 parameter。"
            "算法 / 移植请用 ProcessParameterSchema (FLAT)。"
        ),
    )


class ProcessConditionWriteSchema(BaseSchema):
    """工艺条件写入 (PUT /api/processes/records/<int:condition_id>/ 写入契约, 仅 condition)

    注: parameter 更新走独立端点 PUT /api/processes/parameters/<int:parameter_id>/

    允许修改: status (状态流转) / process_context (前端可控覆盖输入)。

    禁止修改 (业务身份锁): 传入时被**静默忽略**, 原值保持不变;
    字段清单见 services/condition.py::CONDITION_LOCKED_FIELDS。
    """

    condition: ProcessConditionSchema = Field(..., description="工艺条件 (强验证)")


class ProcessRecordListSchema(ProcessConditionListSchema):
    """工艺记录列表查询条件。

    继承 ProcessConditionListSchema (按 condition 字段过滤)。
    增加 view_type 字段区分业务视图:

    - 'parameter'    工艺参数视图：condition + 最新 parameter (默认)
    - 'optimization' 工艺优化视图：condition + parameters_count (无 parameter 详情)

    参考 condition.get_condition_list (view_type 业务区分)
    """

    view_type: Optional[str] = Field(
        "parameter",
        description="视图类型: parameter (工艺参数, 默认) | optimization (工艺优化)",
    )


class ProcessRecordBatchDeleteSchema(BaseSchema):
    """批量删除工艺记录（按 condition_id, 级联软删其下 parameter）。"""

    ids: list[int] = Field(..., min_length=1, description="工艺条件 ID 列表")