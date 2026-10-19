"""
工艺参数数据校验器（算法层接口契约）

职责：
- 按字段定义（specs.MOLD_INFO_FIELDS / MACHINE_INFO_FIELDS / POLYMER_INFO_FIELDS）校验必填字段
- 按材料族（MaterialDatabase）智能填充物理参数
- 算法层不抛业务异常（保持纯净）：校验失败 raise ValueError
- 业务层（service）在调用时捕获 ValueError 转 BizException 400

调用方：
- ProcessInitializer.__init__() 在构造时调用 validate()
- 任何调用 ProcessInitializer 的入口（service / 第三方 / CLI）都自动获得校验
"""

import logging

from .material_db import MaterialDatabase
from .specs import (
    MACHINE_INFO_FIELDS,
    MOLD_INFO_SPEC,
    POLYMER_INFO_FIELDS,
    audit_field_completeness,
)

logger = logging.getLogger(__name__)


class DataValidator:
    """算法层数据校验器（接口契约 + 智能默认值）

    在 ProcessInitializer 构造时调用 validate()，确保输入数据符合算法要求。

    Usage:
        validator = DataValidator()
        validator.validate(mold_info, machine_info, polymer_info, is_hydraulic=True)

    Raises:
        ValueError: 校验失败时抛出（不依赖业务异常）
    """

    def validate(
        self,
        mold_info: dict,
        machine_info: dict,
        polymer_info: dict,
        *,
        is_hydraulic: bool = False,
    ) -> None:
        """校验输入数据 + 智能填充材料默认值

        顺序：智能填充 → 校验 → 最终检查
        原因：先按 abbreviation 查材料族填充，校验后只需要检查
              是否还有"无法补"的能力（材料不在数据库中）。

        Args:
            mold_info: 模具/产品信息 dict
            machine_info: 设备信息 dict
            polymer_info: 材料信息 dict（会被直接修改，填充默认值）
            is_hydraulic: 是否液压机驱动（仅影响 condition='液压机必填' 的处理）

        Raises:
            ValueError: 校验失败时抛出
        """
        # 1. 智能默认值（按 abbreviation 查材料族）— 先做
        #    物理参数缺失时按材料族填充，避免使用统一默认值
        #    （如 melt_density=0.95 给 POM 用会算错）
        #
        #    兑底范围【仅限材料参数】polymer_info：
        #    - 模具参数（mold_info）— 设备实测数据，必须由前端提供
        #    - 注塑机参数（machine_info）— 设备规格数据，必须由前端提供
        #    - 模具/机器参数如果缺失，让上游 audit 拦
        #
        #    为什么材料可以兑底而模具/机器不能：
        #    - 材料族推荐值是「行业经验值」（PP density=0.91, melt_temp=220）
        #    - 有行业共识，业务采集困难时能给个合理起点
        #    - 模具/机器参数是「设备/模具实测值」，没有合理默认值
        #    - 猜错了会出安全/质量事故（如 screw_diameter 猜错导致过射）
        MaterialDatabase.fill_defaults(polymer_info)

        # 2. 业务规则 + 算法必需校验（按字段定义 spec）
        for dim, info, spec in [
            ('mold_info', mold_info, MOLD_INFO_SPEC),
            ('machine_info', machine_info, MACHINE_INFO_FIELDS),
            ('polymer_info', polymer_info, POLYMER_INFO_FIELDS),
        ]:
            missing = audit_field_completeness(
                info, spec, dim, is_hydraulic=is_hydraulic,
            )
            if missing:
                raise ValueError(
                    f"{dim} 校验失败: {', '.join(missing)}"
                )

        # 3. 算法必需字段的最终检查
        #    字段名用 POLYMER_INFO_FIELDS 的"外层字段名"（algorithm 入参 dict 的 key）
        #    如果 MaterialDatabase 中没有这个材料（或数据库缺失参数），必须报错
        for field in ['melt_density', 'recommend_melt_temperature']:
            if not polymer_info.get(field):
                abbreviation = polymer_info.get('abbreviation', '?')
                if MaterialDatabase.has_defaults(abbreviation):
                    raise ValueError(
                        f"polymer_info.{field} 缺失（材料族 {abbreviation} 应该有此参数，请检查 MaterialDatabase）"
                    )
                raise ValueError(
                    f"polymer_info.{field} 缺失（abbreviation={abbreviation} 在材料数据库中无默认值，"
                    f"请补充材料参数）"
                )


__all__ = ["DataValidator"]
