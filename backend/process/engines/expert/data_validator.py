"""
工艺参数数据校验器

职责：
    - 校验机器、模具/产品必填字段
    - 填充材料默认值
    - 抛出明确的错误信息
"""

import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """
    工艺参数数据校验器

    在 ProcessInitializer 构造后调用 validate()，确保输入数据符合算法要求。

    Usage:
        validator = DataValidator()
        validator.validate(machine_info, material_info, mold_info)
    """

    # 机器必填字段（非致命，仅警告）
    REQUIRED_MACHINE_FIELDS = [
        'screw_diameter',
        'max_set_injection_pressure',
        'max_set_injection_velocity',
        'max_set_holding_pressure',
        'max_set_holding_velocity',
        'max_set_screw_rotation_speed',
        'nozzle_type',
    ]

    # 材料默认值（缺失时自动填充）
    MATERIAL_DEFAULTS = {
        'abbreviation': 'ABS',
        'recommended_melt_temp': 250,
        'recommend_shear_linear_speed': 160,
        # v1.0：与 #13 算法设计同步，从 15 调整为 10.0（行业中位）
        'recommend_back_pressure': 10.0,
        'recommended_mold_temp': 0,
        'melt_density': 0.95,
    }

    # 模具/产品必填字段（致命，抛异常）
    REQUIRED_MOLD_FIELDS = [
        'product_weight',
        'gate_type',
        'ave_thickness',
        'max_thickness',
    ]

    def validate(
        self,
        machine_info: dict,
        material_info: dict,
        mold_info: dict,
    ) -> None:
        """
        校验并填充输入数据

        Args:
            machine_info: 设备信息 dict（会被直接修改，填充默认值）
            material_info: 材料信息 dict（会被直接修改，填充默认值）
            mold_info: 模具/产品信息 dict

        Raises:
            ValueError: 模具/产品缺少必填字段时抛出
        """
        # 1. 校验机器字段（非致命警告）
        self._validate_machine(machine_info)

        # 2. 填充材料默认值
        self._fill_material_defaults(material_info)

        # 3. 校验模具/产品必填字段（致命异常）
        self._validate_mold(mold_info)

    def _validate_machine(self, machine_info: dict) -> None:
        """校验机器字段，非致命"""
        for field in self.REQUIRED_MACHINE_FIELDS:
            if not machine_info.get(field):
                logger.warning(f"机器信息缺少字段: {field}")

    def _fill_material_defaults(self, material_info: dict) -> None:
        """填充材料默认值"""
        for key, default in self.MATERIAL_DEFAULTS.items():
            if not material_info.get(key):
                material_info[key] = default
                logger.debug(f"材料信息填充默认值: {key}={default}")

    def _validate_mold(self, mold_info: dict) -> None:
        """
        校验模具/产品必填字段

        Raises:
            ValueError: 缺少必填字段时抛出

        Note:
            runner_weight 允许为 0（表示热流道系统）
        """
        for field in self.REQUIRED_MOLD_FIELDS:
            if not mold_info.get(field):
                raise ValueError(f"模具/产品信息缺少必要字段: {field}")
