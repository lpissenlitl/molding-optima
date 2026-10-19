"""molding-optima 工艺记录 Schema 定义

对应 URL 段: processes/records/  业务对象 ID: condition_id

records 段业务: 工艺条件 CRUD + 工艺参数子资源 + 前端嵌套视图

URL 列表 (按 B 方案拆分, condition_id 与 parameter_id 同时显式表达):
- POST   /api/processes/records/                        创建 condition + 第一条 parameter (NEST)
- GET    /api/processes/records/                        列表 (condition 视角)
- GET    /api/processes/records/<condition_id>/         详情
- PUT    /api/processes/records/<condition_id>/         更新 condition (仅 condition, 不含 parameter)
- DELETE /api/processes/records/<condition_id>/         软删 condition (级联 parameter)
- GET    /api/processes/records/<condition_id>/frontend/ 前端嵌套视图
- GET    /api/processes/records/<condition_id>/history/  工艺参数修改历史
- GET    /api/processes/records/<condition_id>/tree/     工艺参数版本树

工艺参数子资源 (新增, B 方案核心):
- GET    /api/processes/records/<condition_id>/parameter/             列出 condition 内所有 parameter
- GET    /api/processes/records/<condition_id>/parameter/<parameter_id>/  parameter 详情
- PUT    /api/processes/records/<condition_id>/parameter/<parameter_id>/  更新指定 parameter
- DELETE /api/processes/records/<condition_id>/parameter/<parameter_id>/  软删指定 parameter

批量:
- DELETE /api/processes/records/batch-delete/           批量删除 condition

独立 records service 契约:
- ProcessRecordListSchema            列表 (继承 ProcessConditionListSchema, 视图维度 view_type="parameter")
- ProcessConditionAndParameterSchema 创建 (POST /records/, condition + 可选 parameter)
- ProcessConditionWriteSchema        更新 condition (PUT /records/<id>/, 仅 condition)
- ProcessParameterUpdateSchema       更新 parameter (PUT /records/<id>/parameter/<id>/)
- ProcessRecordBatchDeleteSchema     批量删除 (按 condition_id)
"""
from typing import Optional

from pydantic import Field

from extensions.schemas import BaseSchema

from .condition import ProcessConditionListSchema, ProcessConditionSchema
from .parameter import ProcessParameterNestSchema


class ProcessConditionAndParameterSchema(BaseSchema):
    """工艺条件 + 第一条 parameter (POST /records/ 写入契约)

    命名按"结构"而非"段归属"——业务上 records 段创建契约 (POST /records/),
    schema 描述"condition + parameter 组合", 便于跨段复用。

    condition:  必填 (强验证, 10 字段, 与 ProcessCondition model 对齐)
    parameter:  可选 (parameter 业务容器, 当前含 setting_process, 未来可扩展)

    设计选择:
    - 保留 parameter 包装层 (不顶层平铺 setting_process)
    - parameter Optional: 不传则不创建空 parameter, 避免数据库污染
      (业务上用户可能先建 condition 骨架, 后续填数据再调 PUT /records/<id>/parameter/<id>/)
    - 100% 真实流量来自前端 UI (NEST)
    - 算法 / 移植 / 优化请直接用 ProcessParameterSchema (92 字段 FLAT)
    """

    condition: ProcessConditionSchema = Field(..., description="工艺条件 (强验证, 10 字段)")
    parameter: ProcessParameterNestSchema = Field(
        None,
        description=(
            "parameter 业务容器 (当前含 setting_process, 未来可扩展)。"
            "不传或为 null 时不创建空 parameter。"
            "算法 / 移植请用 ProcessParameterSchema (FLAT)。"
        ),
    )


class ProcessConditionWriteSchema(BaseSchema):
    """工艺条件写入 (PUT /records/<condition_id/ 写入契约, 仅 condition)

    注: parameter 更新走独立端点 PUT /records/<condition_id>/parameter/<parameter_id>/

    ┌────────────────────────────────────────────────────────────────────┐
    │ 允许修改 (B 方案基础业务逻辑):                                         │
    │   - status           状态流转 (draft / active / archived)            │
    │   - process_context  前端可控覆盖输入                                  │
    ├────────────────────────────────────────────────────────────────────┤
    │ 禁止修改 (业务身份锁, service 拦截) :                                  │
    │   - condition_no         service 自动生成, 不允许覆盖                 │
    │   - origin_type          业务身份 (manual_creation / ai_recommend…),   │
    │                          改 == 改变业务身份                            │
    │   - process_context_snapshot 后端快照, 创建时锁定, 不允许覆盖          │
    │   - mold_id / shot_index                                              │
    │   - injection_machine_id / injection_index                            │
    │   - polymer_id                                                         │
    │     改则违反"同一三联 (mold+machine+polymer) 应对应不同 condition"       │
    │     业务约束 → 应新建 condition 而非修改                               │
    └────────────────────────────────────────────────────────────────────┘
    """

    condition: ProcessConditionSchema = Field(..., description="工艺条件 (强验证, 10 字段)")


class ProcessRecordListSchema(ProcessConditionListSchema):
    """工艺记录列表查询条件 (2026-10-12)

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
    """批量删除工艺记录（按 condition_id, 级联软删其下 parameter）"""

    ids: list[int] = Field(..., min_length=1, description="工艺条件 ID 列表")