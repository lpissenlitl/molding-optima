"""
工艺参数移植 Schema

对应接口：
- POST /api/processes/algorithms/transplant/

业务语义（与前端 algorithmsTransplant 对齐）：
- 把某个 ProcessParameter 移植到目标注塑机
- 算法根据源参数 + 目标机台规格做适配
- 与"算法初始化"不同：transplant 必须有源 parameter；initialize 从 masterdata 启动

入参字段来源：
- source_parameter_id：源工艺参数 ID（必填）
- target_machine_spec：目标注塑机规格 dict（必填）
  必含字段: screw_diameter（service 层会强校验）
"""
from typing import Dict, Any

from pydantic import Field

from extensions.schemas import BaseSchema


class TransplantRequestSchema(BaseSchema):
    """工艺参数移植请求 Schema

    与前端 api/index.ts 里的 algorithmsTransplant 参数对齐。
    """

    source_parameter_id: int = Field(
        ...,
        description="源工艺参数 ID（必填，须为 is_deleted=False 的 ProcessParameter）",
    )

    target_machine_spec: Dict[str, Any] = Field(
        ...,
        description=(
            "目标注塑机规格 dict（必填）。必含 screw_diameter，"
            "其它字段按需透传给算法层。"
        ),
    )


__all__ = ["TransplantRequestSchema"]
