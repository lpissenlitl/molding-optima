"""
工艺参数初始化器

基于模具、设备、材料、工艺设定 4 维上下文，使用专家规则推理初始工艺参数。
术语统一：使用 "mold" 不用 "product"（mold_info 覆盖模具+产品派生信息）。

系数来源：
    1. InitRuleMatcher（数据库 ExpertRule）
    2. InitRuleLoader（JSON 文件，本地/无 DB）
    3. InitRuleMatcher 内置默认值（兜底）

Usage:
    initializer = ProcessInitializer(
        mold_info=mold_info,        # 模具信息
        machine_info=machine_info,  # 设备信息
        polymer_info=polymer_info,  # 材料信息
        process_set=process_set,    # 工艺设定
    )
    params = initializer.derive()  # 返回 ProductionParams
"""

import logging
import math
from typing import Dict, Any, List, Optional, Tuple

from .macros import (
    HSO_PI,
    HSO_INJ_START_DELAY_TIME,
    HSO_METER_START_DELAY_TIME,
    HSO_PACK_VELOCITY,
    HSO_SUCKBACK_VELO_BEFORE_METER,
    HSO_SUCKBACK_VELO_AFTER_METER,
    HSO_SUCKBACK_DIS_BEFORE_METER,
    HSO_SUCKBACK_DIS_AFTER_METER,
)
from .param_types import ProcessParams, MoldTempParams, HotRunnerParams, ProductionParams
from .rule_matcher import InitRuleMatcher

logger = logging.getLogger(__name__)


# ========== 多级参数系数映射表 ==========
# 这些"段间比例"暂不在 JSON 规则覆盖范围内，
# 保留为模块常量；下一轮迭代可迁入 DEFAULT 规则。
#
# 多级注射系数 - 热流道通用
# 格式: [压力系数], [速度系数], [位置系数]
_MULTI_INJ_GENERIC_HOT = {
    2: [[1, 1.05], [0.78, 1], [0.9, 0]],
    3: [[1, 1.05, 1], [0.78, 1, 0.45], [0.9, 0.3, 0]],
    4: [[1, 1, 1.05, 1], [0.78, 0.9, 1, 0.45], [0.9, 0.4, 0.15, 0]],
    5: [[1, 1, 1.05, 1.03, 1], [0.78, 1, 1.2, 1.5, 0.45], [0.9, 0.65, 0.4, 0.15, 0]],
    6: [[1, 1, 1.05, 1.05, 1.03, 1], [0.78, 1, 1.2, 1.5, 1.3, 0.45], [0.9, 0.7, 0.4, 0.25, 0.1, 0]],
}

# 多级注射系数 - 冷流道通用
_MULTI_INJ_GENERIC_COLD = {
    2: [[1, 1.05], [1, 0.8], [1, 0.8]],
    3: [[1, 1.05, 1], [0.78, 1, 0.45], [0.78, 1, 0.45]],
    4: [[1, 1, 1.05, 1], [0.7, 0.36, 1, 0.45], [0.7, 0.36, 1, 0.45]],
    5: [[1, 1, 1.05, 1.03, 1], [0.7, 0.36, 1, 1.2, 0.45], [0.7, 0.36, 1, 1.2, 0.45]],
    6: [[1, 1, 1.05, 1.05, 1.03, 1], [0.7, 0.3, 1, 1.2, 1.1, 0.45], [0.7, 0.3, 1, 1.2, 1.1, 0.45]],
}

# 多级注射系数 - ABS热流道
_MULTI_INJ_ABS_HOT = {
    2: [[1, 1.05], [0.78, 1], [0.9, 0]],
    3: [[1, 1.05, 0.75], [0.78, 1, 0.5], [0.9, 0.3, 0]],
    4: [[1, 1, 1.05, 0.75], [0.78, 1, 1.3, 0.5], [0.9, 0.4, 0.15, 0]],
    5: [[1, 1, 1.05, 1.03, 0.75], [0.78, 1, 1.2, 1.5, 0.5], [0.9, 0.65, 0.4, 0.15, 0]],
    6: [[1, 1, 1.05, 1.05, 1.03, 0.75], [0.78, 1, 1.2, 1.5, 1.3, 0.5], [0.9, 0.7, 0.4, 0.25, 0.1, 0]],
}

# 多级注射系数 - ABS冷流道
_MULTI_INJ_ABS_COLD = {
    2: [[1, 1.05], [0.36, 1], [0.36, 1]],
    3: [[1, 1.05, 0.75], [0.45, 1, 0.4], [0.45, 1, 0.4]],
    4: [[1, 1, 1.05, 0.75], [0.7, 0.4, 1, 0.5], [0.7, 0.4, 1, 0.5]],
    5: [[1, 1, 1.05, 1.03, 0.75], [0.7, 0.4, 1, 1.2, 0.5], [0.7, 0.4, 1, 1.2, 0.5]],
    6: [[1, 1, 1.05, 1.05, 1.03, 0.75], [0.7, 0.3, 1, 1.2, 1.1, 0.4], [0.7, 0.3, 1, 1.2, 1.1, 0.4]],
}


# 多级保压系数 - [压力系数, 速度系数, 时间系数]
_MULTI_HOLD_COEF_MAP = {
    2: [[1, 0.5], [1, 0.5], [0.5, 0.5]],
    3: [[1, 0.7, 0.4], [1, 0.7, 0.4], [0.3, 0.4, 0.3]],
    4: [[1, 0.75, 0.5, 0.25], [1, 0.75, 0.5, 0.25], [0.25, 0.25, 0.25, 0.25]],
    5: [[1, 0.8, 0.6, 0.4, 0.2], [1, 0.8, 0.6, 0.4, 0.2], [0.2, 0.2, 0.2, 0.2, 0.2]],
}

# 多级计量系数 - [压力系数, 转速系数, 背压系数, 位置系数]
_MULTI_METER_COEF_MAP = {
    2: [[1, 1], [1, 0.8], [0.8, 1], [0.5, 1]],
    3: [[1, 1, 1], [0.75, 1, 0.75], [0.5, 0.75, 1], [0.3, 0.7, 1]],
    4: [[1, 1, 1, 1], [0.75, 1, 1, 0.75], [0.25, 0.5, 0.75, 1], [0.2, 0.5, 0.8, 1]],
}


class ProcessInitializer:
    """
    工艺参数初始化器

    基于机器、材料、产品信息，使用专家规则推理初始工艺参数。

    设备分组：
    - 注塑机参数（ProcessParams）
    - 模温机参数（MoldTempParams）
    - 热流道参数（HotRunnerParams）
    """

    # 通用材料分组（按 MATERIAL_GENERAL 规则匹配）
    _GENERAL_MATERIALS = ("PVC", "POM", "PMMA", "ABS", "AS", "PE", "HDPE", "LDPE", "LLDPE", "PP")

    def __init__(
        self,
        mold_info: Dict[str, Any],
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        process_set: Optional[Dict[str, Any]] = None,
        rule_matcher: Optional[InitRuleMatcher] = None,
    ):
        """
        工艺参数初始化器（4 维独立 dict 输入）

        接受 4 个独立维度的输入，顺序统一为：模具 → 设备 → 材料 → 工艺设定
        - mold_info：模具信息（模具级 + 产品/浇口/壁厚派生合一）
        - machine_info：设备信息（机台本身 + 注射单元合一）
        - polymer_info：材料信息
        - process_set：工艺设置（段数 + 模式），None 时用空 dict
        """
        if not mold_info:
            raise ValueError("模具信息不能为空")
        if not machine_info:
            raise ValueError("设备信息不能为空")
        if not polymer_info:
            raise ValueError("材料信息不能为空")

        self.mold = mold_info
        self.machine = machine_info
        self.material = polymer_info
        self.process_set = process_set or {}
        self.rule_matcher = rule_matcher or InitRuleMatcher()
        # 当前上下文匹配后的合并系数（derive 时填充）
        self._coeffs: Dict[str, Any] = {}

    def derive(self) -> ProductionParams:
        """
        推导初始工艺参数

        直接使用 __init__ 传入的 4 维 dict，不再接受额外参数。
        包含注塑机、模温机、热流道的完整工艺参数。
        """
        self._validate_inputs()
        # 关键：先加载规则系数，再进入派生流程
        # 规则匹配传入 4 维 context（与类属性命名一致）
        self._coeffs = self.rule_matcher.match({
            'machine': self.machine,
            'material': self.material,
            'mold': self.mold,
            'process_set': self.process_set,
        })

        params = ProductionParams(
            process=ProcessParams(),
            mold_temp=MoldTempParams(),
            hot_runner=HotRunnerParams(),
        )

        # 按设备分组推导
        self._derive_process(params)
        self._derive_mold_temp(params)
        self._derive_hot_runner(params)

        self._apply_multi_stage(params)
        self._format_output(params)

        return params

    # ========== 输入校验 ==========

    def _validate_inputs(self):
        """校验输入信息"""
        required_machine_fields = [
            'screw_diameter',
            'max_set_injection_pressure',
            'max_set_injection_velocity',
            'max_set_holding_pressure',
            'max_set_holding_velocity',
            'max_set_screw_rotation_speed',
            'nozzle_type',
        ]
        for field in required_machine_fields:
            if not self.machine.get(field):
                logger.warning(f"机器信息缺少字段: {field}")

        # 材料默认值（若缺）
        material_defaults = {
            'abbreviation': 'ABS',
            'recommended_melt_temp': 250,
            'recommend_shear_linear_speed': 160,
            # v1.0：与 #13 算法设计同步，从 15 调整为 10.0（行业中位）
            'recommend_back_pressure': 10.0,
            'recommended_mold_temp': 0,
            'melt_density': 0.95,
        }
        for key, default in material_defaults.items():
            if not self.material.get(key):
                self.material[key] = default

        # 模具/产品必填字段（来自 mold_info）
        required_mold_fields = ['product_weight', 'gate_type', 'ave_thickness', 'max_thickness']
        for field in required_mold_fields:
            if not self.mold.get(field):
                raise ValueError(f"模具/产品信息缺少必要字段: {field}")
        # runner_weight 允许为 0（表示热流道）

    # ========== 系数读取辅助 ==========

    def _get(self, group: str, key: str, default: Any = None) -> Any:
        """从合并系数中安全读取指定键值"""
        return self._coeffs.get(group, {}).get(key, default)

    # ========== 材料参数辅助（3 级兜底）==========

    def _parse_family(self, abbrev: str) -> str:
        """
        从材料完整名称解析出材料大类

        例："PA66+GF30" → "PA"，"PC+ABS" → "PC"，"PET" → "PET"，
           "HDPE" → "PE"，"PVC" → "PVC"

        注意顺序：长前缀优先（PET 必须在 PE 之前，否则误匹配）
        """
        if not abbrev:
            return ''
        abbrev = str(abbrev).upper().strip()
        # 注意顺序：长前缀优先匹配
        # - PET 必须在 PE 之前（否则 'PET'.startswith('PE') 误匹配）
        # - PBT 可放任意位置（不存在 PB 前缀冲突）
        # - PMMA 必须在 PM 子串前（暂无冲突）
        # - 2026-07-05 #19+#20 温度族：补充 PVC / AS / HDPE / LDPE / LLDPE 5 个 family
        for family in (
            'PP', 'PBT', 'PET', 'PE',          # PE 匹配 PE/HDPE/LDPE/LLDPE
            'PS', 'ABS', 'AS',
            'PC', 'PA', 'POM', 'PMMA',
            'PVC',                              # 补 PVC
        ):
            if abbrev.startswith(family):
                return family
        return ''

    def _get_shrink_rate(self, c_inj: Dict[str, Any]) -> tuple:
        """
        获取材料体积收缩率（3 级兜底）

        优先级：
        1. 第 1 级 - Polymer.shrink_rate 字段（精确值）
        2. 第 2 级 - family_shrink_map[family]（大类典型值）
        3. 第 3 级 - default_shrink_rate（兜底）

        Args:
            c_inj: injection 分组合并系数（包含 family_shrink_map / default_shrink_rate）

        Returns:
            (shrink_rate, level) 元组，level ∈ {'precise', 'family', 'default'}
            level 用于日志审计，便于后续补充精确数据
        """
        # ====== 第 1 级：精确值 ======
        if self.material.get('shrink_rate') is not None:
            return self.material['shrink_rate'], 'precise'

        # ====== 第 2 级：按大类查表 ======
        family = self._parse_family(self.material.get('abbreviation', ''))
        family_map = c_inj.get('family_shrink_map', {})
        if family and family in family_map:
            return family_map[family], 'family'

        # ====== 第 3 级：默认值（兜底）======
        return c_inj.get('default_shrink_rate', 0.030), 'default'

    # ========== 计量压力算法（#11，v1.0）==========

    def _compute_meter_pres(self, mach: Dict[str, Any], abbreviation: str, c_met: Dict[str, Any]) -> float:
        """
        v1.0 计量压力计算（3 维物理化 + 动力源分支）

        物理背景：
            - 计量压力 = 液压机液压油缸推动螺杆后退的油压（液压机油路）
            - 全电机无油缸，HMI 不显示“计量压力”输入栏 → meter_pres = 0（物理正确）
            - 液压机调用公式：max × base_ratio × family_factor × nozzle_factor → 钳制 [min, max]

        Args:
            mach: 设备信息 dict（需含 power_method / nozzle_type / max_set_metering_pressure）
            abbreviation: 材料完整缩写（原始值，如 'PA66' / 'PVC' / 'PC+ABS'）。
                          用于优先精确匹配，再 fallback 到 family 解析（如 PA66 → PA）
            c_met: metering 分组合并系数

        Returns:
            float: 计量压力（同源数值，不假设 MPa；具体单位由设备 HMI 决定）
        """
        # ======== 分支 1：全电机 → meter_pres = 0 ========
        if mach.get('power_method') == '全电机':
            # 物理依据：全电机没有液压油缸，HMI 无“计量压力”输入栏
            # 这不是 bug，而是物理正确。
            return 0.0

        # ======== 分支 2：液压机（或默认）→ 3 维公式 ========
        # 读取输入值
        nozzle_type = mach.get('nozzle_type', '直通型')
        max_metering_pres = mach.get('max_set_metering_pressure', 20)

        # 维度 1：base_ratio（按喷嘴类型区分）
        if nozzle_type == '锁定型':
            base_ratio = c_met.get('meter_pres_ratio_locking', 0.60)
        else:
            # 默认与“直通型”走同一路径
            base_ratio = c_met.get('meter_pres_ratio_straight', 0.55)

        # 维度 2：family 黏度修正系数（相对比例，默认 1.0）
        family_factor, family_level, family_key = self._get_family_meter_viscosity(abbreviation, c_met)

        # 维度 3：nozzle_factor（直通/锁闭）
        nozzle_factor, nozzle_level = self._get_nozzle_factor(nozzle_type, c_met)

        # 公式推导
        meter_pres_raw = max_metering_pres * base_ratio * family_factor * nozzle_factor

        # 钳制约束
        meter_pres_min = c_met.get('meter_pres_min', 0.0)
        meter_pres_max = c_met.get('meter_pres_max', max_metering_pres)
        meter_pres = max(meter_pres_min, min(meter_pres_raw, meter_pres_max))

        logger.debug(
            f"[meter_pres:液压机] base_ratio={base_ratio:.3f}, "
            f"family={family_key} (family_factor={family_factor:.2f}, level={family_level}), "
            f"nozzle={nozzle_type} (nozzle_factor={nozzle_factor:.2f}, level={nozzle_level}), "
            f"raw={meter_pres_raw:.2f}, clamped=[{meter_pres_min:.2f}, {meter_pres_max:.2f}], "
            f"final={meter_pres:.2f}"
        )
        return meter_pres

    def _get_family_meter_viscosity(self, abbreviation: str, c_met: Dict[str, Any]) -> Tuple[float, str, str]:
        """
        获取材料种类的“计量压力黏度修正系数”（3 级兜底）

        物理意义：
            材料熔体黏度（Pa·s）越高，需要的油压越大（克服熔体回流阻力）。
            以 family 为 key 取相对比例，默认 1.0。

        优先级：
            1. 第 1 级 - family_meter_viscosity[abbreviation]（精确全名匹配，如 'PA66' / 'PVC' / 'PC+ABS'）
            2. 第 2 级 - family_meter_viscosity[family]（大类匹配，如 PA66 → PA）
            3. 第 3 级 - default_family_meter_viscosity（默认 1.0，保留原行为）

        顺序设计理由：
            PA66/PA6/PBT/PET 细分材料有不同的 relative viscosity，直接用 family
            会丢信息。优先匹配原始 abbreviation 保留细分能力。

        Args:
            abbreviation: 材料完整缩写（原始值）
            c_met: metering 分组合并系数

        Returns:
            (family_factor, level, key_used) 元组，
            level ∈ {'precise_abbrev', 'precise_family', 'default'}
        """
        family_map = c_met.get('family_meter_viscosity', {})
        abbrev = str(abbreviation or '').upper().strip()

        # 第 1 级：精确全名匹配（如 PA66, PVC, PC+ABS）
        if abbrev in family_map:
            return family_map[abbrev], 'precise_abbrev', abbrev

        # 第 2 级：family 大类匹配（PA66 → PA）
        family = self._parse_family(abbrev)
        if family and family in family_map:
            return family_map[family], 'precise_family', family

        # 第 3 级：兜底默认
        return c_met.get('default_family_meter_viscosity', 1.0), 'default', abbrev or 'unknown'

    def _get_nozzle_factor(self, nozzle_type: str, c_met: Dict[str, Any]) -> Tuple[float, str]:
        """
        获取喷嘴类型修正系数（直通/锁闭）

        物理依据：
            锁闭喷嘴有止逆阀（shut-off valve），增加回流阻力，需要更高油压克服。
            - 直通型：1.00（无额外阻力，标准）
            - 锁闭型：1.10（止逆阀增加阻力）

        Args:
            nozzle_type: 喷嘴类型（'直通型' / '锁定型'，中文字段名）
            c_met: metering 分组合并系数

        Returns:
            (nozzle_factor, level) 元组，level ∈ {'straight', 'locking', 'default'}
        """
        nozzle_map = c_met.get('nozzle_factor', {})
        if nozzle_type in nozzle_map:
            level = 'locking' if nozzle_type == '锁定型' else 'straight'
            return nozzle_map[nozzle_type], level
        return nozzle_map.get('直通型', c_met.get('default_nozzle_factor', 1.00)), 'default'

    # ========== 计量螺杆转速算法（#12，v1.0）==========

    def _compute_meter_speed(self, mach: Dict[str, Any], mat: Dict[str, Any], abbreviation: str, c_met: Dict[str, Any]) -> float:
        """
        v1.0 计量螺杆转速计算（family 修正 + L/D 修正）

        物理背景：
            螺杆旋转表面线速度 = π × D × N / 60
            反推 N = 60 × v_surface / (π × D)
            转速比 = N / max_screw_speed = 60 × v_surface / (π × D × max_screw_speed)

            v1.0 修正：
            - 维度 1：family 修正（必选，17 family × 0.50~1.10）
            - 维度 2：L/D 修正（条件性启用，字段缺失 → 1.00 兜底）
            - 不分支动力源（全电机/液压机走同一公式）
            - 钳制 [0.30, 0.75]（行业共识）

        Args:
            mach: 设备信息 dict
                  需含 max_set_screw_rotation_speed / screw_diameter
                  可选 screw_length_to_diameter_ratio（L/D 修正）
            mat: 材料信息 dict（用于取 recommend_shear_linear_speed）
            abbreviation: 材料完整缩写（原始值，如 'PA66' / 'PVC'）
            c_met: metering 分组合并系数

        Returns:
            float: 计量螺杆转速 [rpm]
        """
        # 读取输入值
        max_screw_speed = mach.get('max_set_screw_rotation_speed', 150)        # [rpm]
        screw_diameter = mach.get('screw_diameter', 40)                          # [mm]
        recommend_shear_speed = mat.get('recommend_shear_linear_speed', 160) or 160  # [mm/s]

        # 维度 1：family 剪切敏感度修正（3 级兜底：abbreviation → family → default）
        family_factor, family_level, family_key = self._get_family_meter_shear_ratio(abbreviation, c_met)

        # 维度 2：L/D 修正（条件性启用，字段缺失 → 1.00 兜底）
        ld_factor, ld_level = self._get_ld_correction(mach.get('screw_length_to_diameter_ratio'), c_met)

        # 基础推导：v_surface → N → ratio
        # 60 = s → min 单位换算因子（v_surface × 60 / (π × D) = rpm）
        v_target = recommend_shear_speed * family_factor * ld_factor
        ratio_raw = (60.0 * v_target) / (screw_diameter * HSO_PI * max_screw_speed)

        # 钳制约束
        ratio_min = c_met.get('meter_speed_temp_ratio_min', 0.30)
        ratio_max = c_met.get('meter_speed_temp_ratio_max', 0.75)
        ratio = max(ratio_min, min(ratio_raw, ratio_max))

        # 输出转速
        meter_speed = ratio * max_screw_speed

        logger.debug(
            f"[meter_speed:液压机/全电机通用] recommend_shear={recommend_shear_speed}, "
            f"family={family_key} (family_factor={family_factor:.2f}, level={family_level}), "
            f"ld_factor={ld_factor:.2f} (level={ld_level}), "
            f"v_target={v_target:.2f}, ratio_raw={ratio_raw:.3f}, "
            f"clamped=[{ratio_min:.2f}, {ratio_max:.2f}], "
            f"final_ratio={ratio:.3f}, meter_speed={meter_speed:.2f}rpm"
        )
        return meter_speed

    def _get_family_meter_shear_ratio(self, abbreviation: str, c_met: Dict[str, Any]) -> Tuple[float, str, str]:
        """
        获取材料种类的“计量螺杆转速剪切敏感度修正系数”（3 级兑底）

        物理意义：
            不同材料剪切降解敏感度差异大：
            - PVC/POM：严重降解（HCl / 甲醛释放）→ 偏保守（0.50~0.65）
            - PC/PA66：高黏度 → 偏保守（0.50~0.55）
            - ABS/PS：中等黏度 → 基准 1.00
            - PP/PE：流动性好 → 可偏高（1.10）

        优先级：
            1. 第 1 级 - family_meter_shear_ratio[abbreviation]（精确全名匹配，如 'PA66' / 'PVC' / 'PC+ABS'）
            2. 第 2 级 - family_meter_shear_ratio[family]（大类匹配，如 PA66 → PA）
            3. 第 3 级 - default_family_meter_shear_ratio = 1.0（兑底）

        Args:
            abbreviation: 材料完整缩写（原始值）
            c_met: metering 分组合并系数

        Returns:
            (family_factor, level, key_used) 元组，
            level ∈ {'precise_abbrev', 'precise_family', 'default'}
        """
        family_map = c_met.get('family_meter_shear_ratio', {})
        abbrev = str(abbreviation or '').upper().strip()

        # 第 1 级：精确全名匹配（如 PA66, PVC, PC+ABS）
        if abbrev in family_map:
            return family_map[abbrev], 'precise_abbrev', abbrev

        # 第 2 级：family 大类匹配（PA66 → PA）
        family = self._parse_family(abbrev)
        if family and family in family_map:
            return family_map[family], 'precise_family', family

        # 第 3 级：兑底默认
        return c_met.get('default_family_meter_shear_ratio', 1.0), 'default', abbrev or 'unknown'

    def _get_ld_correction(self, screw_ld_ratio: Optional[float], c_met: Dict[str, Any]) -> Tuple[float, str]:
        """
        获取长径比修正系数（条件性启用，字段缺失 → 1.00 兑底）

        物理意义：
            螺杆长径比 L/D 影响塑化路径长度与停留时间：
            - L/D < 18（short）：塑化路径短、停留时间不足 → 微升（1.05）
            - 18 ≤ L/D ≤ 22（standard）：海天/震雄主流机型 → 基准 1.00
            - L/D > 22（long）：塑化路径长、防过剪切降解 → 微降（0.95）

        条件性启用：
            设备字段 `screw_length_to_diameter_ratio` 为 None（缺失）时 → 1.00 兑底，不修正
            避免强制要求设备字段，保持算法兑底友好

        Args:
            screw_ld_ratio: 长径比（无量纲，可为 None）
            c_met: metering 分组合并系数

        Returns:
            (ld_factor, level) 元组，
            level ∈ {'short', 'standard', 'long', 'default'}
        """
        # 字段缺失 → 兑底 1.00（不修正）
        if screw_ld_ratio is None:
            return c_met.get('default_ld_correction', 1.00), 'default'

        thresholds = c_met.get('ld_thresholds', [18, 22])
        ld_map = c_met.get('ld_correction', {})

        if screw_ld_ratio < thresholds[0]:                                  # < 18
            return ld_map.get('short', 1.05), 'short'
        elif screw_ld_ratio > thresholds[1]:                                # > 22
            return ld_map.get('long', 0.95), 'long'
        else:                                                                # 18 ≤ L/D ≤ 22
            return ld_map.get('standard', 1.00), 'standard'

    # ========== 计量背压算法（#13，v1.0）==========

    def _compute_meter_back_pres(self, mach: Dict[str, Any], mat: Dict[str, Any],
                                  abbreviation: str, meter_speed: float,
                                  c_back: Dict[str, Any]) -> float:
        """
        v1.0 计量背压计算（family 排气需求修正 + 螺杆转速联动修正）

        物理背景：
            背压在塑化阶段压缩熔体、排除空气、提升密度均匀性。
            不同材料排气需求差异巨大：
            - PMMA 高黏度 → 需强排气（family_factor=1.50）
            - PA66 极易水解 → 不能高背压（family_factor=0.40，防摩擦生热水解）
            - PVC 剪切敏感 → 不能高背压（family_factor=0.50，防 HCl 释放）

            v1.0 修正：
            - 维度 1：family 排气需求修正（必选，17 family × 0.40~1.50）
            - 维度 2：螺杆转速联动修正（条件性启用，rpm_ratio 缺失 → 1.0 兑底）
            - 不分支动力源（全电机/液压机走同一公式，与 #12 对称）
            - 钉制 [0.5, 30.0] MPa（行业共识：PA66 下限 2.0 安全余量 + PMMA 上限 28 安全余量）

        Args:
            mach: 设备信息 dict（需含 max_set_screw_rotation_speed）
            mat: 材料信息 dict（需含 recommend_back_pressure 字段或缺失兑底 10.0）
            abbreviation: 材料完整缩写（原始值，如 'PA66' / 'PVC'）
            meter_speed: #12 算法推导出的计量螺杆转速 [rpm]
            c_back: back_pressure 分组合并系数

        Returns:
            float: 计量背压 [MPa]
        """
        # 读取输入值
        max_screw_speed = mach.get('max_set_screw_rotation_speed', 150)
        recommend_back_pressure = mat.get('recommend_back_pressure') or c_back.get('default_recommend_back_pressure', 10.0)

        # 维度 1：family 排气需求修正（3 级兑底：abbreviation → family → default）
        family_factor, family_level, family_key = self._get_family_back_pres_factor(abbreviation, c_back)

        # 维度 2：螺杆转速联动修正（条件性启用）
        # 物理：转速越高 → 熔体停留时间越短 → 密度均匀性越差 → 需更高背压补偿
        speed_factor, speed_level = self._get_speed_factor(meter_speed, max_screw_speed, c_back)

        # 基础推导
        meter_back_pres_raw = recommend_back_pressure * family_factor * speed_factor

        # 钉制约束（基于材料物理耐受度，非设备能力）
        meter_back_pres_min = c_back.get('meter_back_pres_min', 0.5)
        meter_back_pres_max = c_back.get('meter_back_pres_max', 30.0)
        meter_back_pres = max(meter_back_pres_min, min(meter_back_pres_raw, meter_back_pres_max))

        logger.debug(
            f"[meter_back_pres:液压机/全电机通用] recommend_back={recommend_back_pressure}, "
            f"family={family_key} (family_factor={family_factor:.2f}, level={family_level}), "
            f"speed_factor={speed_factor:.3f} (level={speed_level}), "
            f"raw={meter_back_pres_raw:.2f}MPa, "
            f"clamped=[{meter_back_pres_min:.2f}, {meter_back_pres_max:.2f}], "
            f"final={meter_back_pres:.2f}MPa"
        )
        return meter_back_pres

    def _get_family_back_pres_factor(self, abbreviation: str, c_back: Dict[str, Any]) -> Tuple[float, str, str]:
        """
        获取材料种类的“计量背压排气需求修正系数”（3 级兑底）

        物理意义：
            不同材料排气需求与耐受度差异巨大：
            - PMMA 高黏度 → 需强排气（1.50）
            - PA66 极易水解 → 不能高背压（0.40，防摩擦生热水解）
            - PVC 剪切敏感 → 不能高背压（0.50，防 HCl 释放）

        优先级：
            1. 第 1 级 - family_back_pres_factor[abbreviation]（精确全名匹配，如 'PA66' / 'PVC' / 'PC+ABS'）
            2. 第 2 级 - family_back_pres_factor[family]（大类匹配，如 PA66 → PA）
            3. 第 3 级 - default_family_back_pres_factor = 1.0（兑底）

        Args:
            abbreviation: 材料完整缩写（原始值）
            c_back: back_pressure 分组合并系数

        Returns:
            (family_factor, level, key_used) 元组，
            level ∈ {'precise_abbrev', 'precise_family', 'default'}
        """
        family_map = c_back.get('family_back_pres_factor', {})
        abbrev = str(abbreviation or '').upper().strip()

        # 第 1 级：精确全名匹配（如 PA66, PVC, PC+ABS）
        if abbrev in family_map:
            return family_map[abbrev], 'precise_abbrev', abbrev

        # 第 2 级：family 大类匹配（PA66 → PA）
        family = self._parse_family(abbrev)
        if family and family in family_map:
            return family_map[family], 'precise_family', family

        # 第 3 级：兑底默认
        return c_back.get('default_family_back_pres_factor', 1.0), 'default', abbrev or 'unknown'

    def _get_speed_factor(self, meter_speed: Optional[float], max_screw_speed: float,
                           c_back: Dict[str, Any]) -> Tuple[float, str]:
        """
        获取螺杆转速联动修正系数（条件性启用，rpm_ratio 缺失 → 1.0 兑底）

        物理意义：
            螺杆转速 N 越高 → 熔体在料筒中停留时间 t ∝ 1/N 越短
            停留时间短 → 熔体密度均匀性越差 → 需更高背压补偿
            反之，转速过低 → 停留时间长 → 熔体已充分均匀 → 背压可略降低

        公式：
            speed_factor = 1.0 + slope × (rpm_ratio - base)
            钉制到 [speed_factor_min, speed_factor_max]

        条件性启用：
            meter_speed 为 None（缺失）时 → 1.00 兑底，不修正
            max_screw_speed 为 0 / None 时 → 1.00 兑底，避免除零

        Args:
            meter_speed: 计量螺杆转速 [rpm]，可为 None
            max_screw_speed: 最大可设定螺杆转速 [rpm]
            c_back: back_pressure 分组合并系数

        Returns:
            (speed_factor, level) 元组，
            level ∈ {'high', 'base', 'low', 'default'}
        """
        # 字段缺失 → 兑底 1.00（不修正）
        if meter_speed is None or not max_screw_speed:
            return c_back.get('default_speed_factor', 1.0), 'default'

        rpm_ratio = meter_speed / max_screw_speed

        # 读取参数
        base = c_back.get('speed_factor_base', 0.5)
        slope = c_back.get('speed_factor_slope', 0.3)
        sf_min = c_back.get('speed_factor_min', 0.85)
        sf_max = c_back.get('speed_factor_max', 1.15)

        # 基础推导
        raw_factor = 1.0 + slope * (rpm_ratio - base)

        # 钉制 + level 判定
        if rpm_ratio > base:
            level = 'high'
        elif rpm_ratio < base:
            level = 'low'
        else:
            level = 'base'

        return max(sf_min, min(raw_factor, sf_max)), level

    # ========== 注射压力查表（材料大类 + 流长比，二维差异化）==========

    def _get_base_pressure_ratio(self, family: str, c_inj: Dict[str, Any]) -> tuple:
        """
        获取材料基准压力比例（3 级兜底）

        优先级：
        1. 第 1 级 - Polymer.recommend_inj_pressure_ratio 字段（精确值）
        2. 第 2 级 - base_pressure_ratio_map[family]（大类典型值）
        3. 第 3 级 - default_base_pressure_ratio（兜底）

        物理依据：
        - 基准比例反映材料黏度等级（PP/PE 流动性好 → 基准压力低；PC 高黏度 → 基准压力高）
        - 定量数字来自材料手册 + Moldflow 共识中位近似

        Args:
            family: 材料大类（来自 _parse_family）
            c_inj: injection 分组合并系数

        Returns:
            (base_ratio, level) 元组，level ∈ {'precise', 'family', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        precise_ratio = self.material.get('recommend_inj_pressure_ratio')
        if precise_ratio is not None:
            return precise_ratio, 'precise'

        # ====== 第 2 级：按大类查表 ======
        ratio_map = c_inj.get('base_pressure_ratio_map', {})
        if family and family in ratio_map:
            return ratio_map[family], 'family'

        # ====== 第 3 级：默认值（兜底）======
        return c_inj.get('default_base_pressure_ratio', 0.70), 'default'

    def _get_length_factor(self, inj_ratio: float, c_inj: Dict[str, Any]) -> tuple:
        """
        获取流长比修正系数（3 级兜底）

        优先级：
        1. 第 1 级 - Polymer.length_factor_override 字段（精确值）
        2. 第 2 级 - length_factor_buckets（按 inj_ratio 分档查表）
        3. 第 3 级 - default_length_factor（兜底）

        物理依据：
        - 流长比 L/t 越大 → 填充路径压力梯度越陡 → 压力修正越大
        - 分档近似 Poiseuille 流动公式的定性关系，定量来自工艺手册

        Args:
            inj_ratio: 流长比 L/t
            c_inj: injection 分组合并系数

        Returns:
            (length_factor, level) 元组，level ∈ {'precise', 'bucket', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        override = self.material.get('length_factor_override')
        if override is not None:
            return override, 'precise'

        # ====== 第 2 级：按分档查表 ======
        buckets = c_inj.get('length_factor_buckets', [])
        if inj_ratio > 0 and buckets:
            sorted_buckets = sorted(
                buckets,
                key=lambda b: b.get('max_ratio') if b.get('max_ratio') is not None else float('inf'),
            )
            for bucket in sorted_buckets:
                max_ratio = bucket.get('max_ratio')
                if max_ratio is None or inj_ratio <= max_ratio:
                    return bucket['factor'], 'bucket'

        # ====== 第 3 级：默认值（兜底）======
        return c_inj.get('default_length_factor', 1.20), 'default'
    
    # ========== 注射速度查表（材料流动性 + 流长比 + 模温，三维差异化）==========
    
    def _get_base_velocity_ratio(self, family: str, c_inj: Dict[str, Any]) -> tuple:
        """
        获取材料基准速度比例（3 级兜底）
    
        优先级：
        1. 第 1 级 - Polymer.recommend_inj_velocity_ratio 字段（精确值）
        2. 第 2 级 - base_velocity_ratio_map[family]（大类典型值）
        3. 第 3 级 - default_base_velocity_ratio（兜底）
    
        物理依据：
        - 基准比例反映材料流动性等级（MFI 高 → 基准速度可偏低；高黏度 → 基准速度偏高）
        - 定量数字来自材料手册 MFI 区间 + Moldflow 推荐填充速度 + 注塑机厂家推荐值中位
    
        Args:
            family: 材料大类（来自 _parse_family）
            c_inj: injection 分组合并系数
    
        Returns:
            (base_velo_ratio, level) 元组，level ∈ {'precise', 'family', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        precise_ratio = self.material.get('recommend_inj_velocity_ratio')
        if precise_ratio is not None:
            return precise_ratio, 'precise'
    
        # ====== 第 2 级：按大类查表 ======
        ratio_map = c_inj.get('base_velocity_ratio_map', {})
        if family and family in ratio_map:
            return ratio_map[family], 'family'
    
        # ====== 第 3 级：默认值（兜底）======
        return c_inj.get('default_base_velocity_ratio', 0.40), 'default'
    
    def _get_length_velocity_factor(self, inj_ratio: float, c_inj: Dict[str, Any]) -> tuple:
        """
        获取流长比修正系数（3 级兜底）
    
        优先级：
        1. 第 1 级 - Polymer.length_velocity_override 字段（精确值）
        2. 第 2 级 - length_velocity_factors（按 inj_ratio 分档查表）
        3. 第 3 级 - default_length_velocity_factor（兜底）
    
        物理依据：
        - 流长比 L/t 越大 → 前缘冷却风险越高 → 需加速补偿
        - 分档近似体积流量恒等式 + 剪切速率约束的定性关系，定量来自工艺手册
    
        Args:
            inj_ratio: 流长比 L/t
            c_inj: injection 分组合并系数
    
        Returns:
            (length_velo_factor, level) 元组，level ∈ {'precise', 'bucket', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        override = self.material.get('length_velocity_override')
        if override is not None:
            return override, 'precise'
    
        # ====== 第 2 级：按分档查表 ======
        factors = c_inj.get('length_velocity_factors', [])
        if inj_ratio > 0 and factors:
            sorted_factors = sorted(
                factors,
                key=lambda f: f.get('max_ratio') if f.get('max_ratio') is not None else float('inf'),
            )
            for factor in sorted_factors:
                max_ratio = factor.get('max_ratio')
                if max_ratio is None or inj_ratio <= max_ratio:
                    return factor['factor'], 'bucket'
    
        # ====== 第 3 级：默认值（兜底）======
        return c_inj.get('default_length_velocity_factor', 1.20), 'default'
    
    def _get_temp_velocity_modifier(self, mold_temp: float, c_inj: Dict[str, Any]) -> tuple:
        """
        获取模温修正系数（3 级兜底）
    
        优先级：
        1. 第 1 级 - Polymer.temp_velocity_override 字段（精确值）
        2. 第 2 级 - temp_velocity_buckets（按 mold_temp 分档查表）
        3. 第 3 级 - default_temp_velocity_modifier（兜底，不修正）
    
        物理依据：
        - 模温高 → 黏度低 → 流动性好 → 速度可微降
        - 模温低 → 黏度高 → 流动性差 → 速度需微升
        - 修正幅度控制在 ±5% （微修正）
    
        Args:
            mold_temp: 模具温度（℃）
            c_inj: injection 分组合并系数
    
        Returns:
            (temp_velo_modifier, level) 元组，level ∈ {'precise', 'bucket', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        override = self.material.get('temp_velocity_override')
        if override is not None:
            return override, 'precise'
    
        # ====== 第 2 级：按分档查表 ======
        buckets = c_inj.get('temp_velocity_buckets', [])
        if mold_temp > 0 and buckets:
            sorted_buckets = sorted(
                buckets,
                key=lambda b: b.get('max_temp') if b.get('max_temp') is not None else float('inf'),
            )
            for bucket in sorted_buckets:
                max_temp = bucket.get('max_temp')
                if max_temp is None or mold_temp <= max_temp:
                    return bucket['factor'], 'bucket'
    
        # ====== 第 3 级：默认值（兜底）======
        return c_inj.get('default_temp_velocity_modifier', 1.00), 'default'

    # ========== 注射时间查表（材料大类 × 壁厚档，二维差异化）==========

    def _get_thickness_bucket(self, max_thickness: float, c_inj: Dict[str, Any]) -> Tuple[str, str]:
        """
        按壁厚分档（3 级兜底）

        优先级：
        1. 第 1 级 - Polymer.thickness_bucket_override 字段（精确值）
        2. 第 2 级 - 按 thickness_bucket_thresholds 计算（thin / medium / thick）
        3. 第 3 级 - default_thickness_bucket（兜底）

        物理依据：
        - thin 桶（t ≤ 1.5mm）：薄壁冻结风险高，前缘冷却时间约束
        - medium 桶（1.5 < t ≤ 3.0mm）：标准结构件，几何下限主导
        - thick 桶（t > 3.0mm）：厚壁飞边下限约束，高剪切速率风险

        Args:
            max_thickness: 最大壁厚（mold.max_thickness）
            c_inj: injection 分组合并系数

        Returns:
            (bucket, level) 元组，bucket ∈ {'thin', 'medium', 'thick'}
            level ∈ {'precise', 'bucket', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        override = self.material.get('thickness_bucket_override')
        if override is not None:
            return override, 'precise'

        # ====== 第 2 级：按 max_thickness 计算 ======
        if max_thickness > 0:
            thresholds = c_inj.get('thickness_bucket_thresholds', [1.5, 3.0])
            thin_max = thresholds[0]
            medium_max = thresholds[1] if len(thresholds) > 1 else float('inf')

            if max_thickness <= thin_max:
                return 'thin', 'bucket'
            elif max_thickness <= medium_max:
                return 'medium', 'bucket'
            else:
                return 'thick', 'bucket'

        # ====== 第 3 级：默认值（兜底）======
        return c_inj.get('default_thickness_bucket', 'medium'), 'default'

    def _get_inj_time_window(self, family: str, bucket: str, c_inj: Dict[str, Any]) -> Tuple[Tuple[float, float], str]:
        """
        获取工艺时间窗口（3 级兜底）

        优先级：
        1. 第 1 级 - Polymer.recommend_inj_time_window[bucket] 字段（精确值）
        2. 第 2 级 - family_time_window[family][bucket]（按材料 × 桶查表）
        3. 第 3 级 - default_time_window（兜底）

        物理依据：
        - 薄壁冻结上限（thin max_t 1.0~2.5s）：防前缘冷却成欠注
        - 厚壁飞边下限（thick min_t 1.5~3.0s）：防高剪切烧焦 / 飞边
        - 材料窗口差异：PC/PA66/PET 等高黏度窗口整体放宽；PP/PE 收紧

        Args:
            family: 材料大类（来自 _parse_family）
            bucket: 壁厚档（'thin' / 'medium' / 'thick'）
            c_inj: injection 分组合并系数

        Returns:
            ((min_t, max_t), level) 元组
            level ∈ {'precise', 'family', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        polymer_window = self.material.get('recommend_inj_time_window')
        if polymer_window is not None:
            precise = polymer_window.get(bucket)
            if precise is not None:
                return tuple(precise), 'precise'

        # ====== 第 2 级：按 family × bucket 查表 ======
        family_windows = c_inj.get('family_time_window', {})
        if family and family in family_windows:
            family_bucket_window = family_windows[family]
            if bucket in family_bucket_window:
                return tuple(family_bucket_window[bucket]), 'family'

        # ====== 第 3 级：默认值（兑底）======
        return tuple(c_inj.get('default_time_window', (0.6, 2.5))), 'default'
    
    # ========== 保压压力查表（材料大类 × 壁厚 × 浇口 × 流道，四维差异化）==========
    
    def _get_family_hold_ratio(self, family: str, c_hold: Dict[str, Any]) -> Tuple[float, str]:
        """
        获取材料相对保压比例（3 级兜底）
    
        优先级：
        1. 第 1 级 - Polymer.recommend_hold_pres_ratio 字段（精确值）
        2. 第 2 级 - family_hold_ratio[family]（大类典型值）
        3. 第 3 级 - default_hold_ratio（兜底）
    
        物理依据：
        - 比例反映材料黏度等级（PP/PE 流动性好 → 保压偏低防飞边）
        - 半结晶（PET/PA）结晶补缩需要保压偏高
        - 高黏度（PC/POM）防凹陷需要保压偏高
        - 定量数值 0.50~0.75 来自海天/震雄/Fanuc 工艺手册 + Moldflow 共识中位
    
        Args:
            family: 材料大类（来自 _parse_family）
            c_hold: holding 分组合并系数
    
        Returns:
            (family_hold_ratio, level) 元组
            level ∈ {'precise', 'family', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        precise_ratio = self.material.get('recommend_hold_pres_ratio')
        if precise_ratio is not None:
            return precise_ratio, 'precise'
    
        # ====== 第 2 级：按大类查表 ======
        ratio_map = c_hold.get('family_hold_ratio', {})
        if family and family in ratio_map:
            return ratio_map[family], 'family'
    
        # ====== 第 3 级：默认值（兜底）======
        return c_hold.get('default_hold_ratio', 0.60), 'default'
    
    def _get_family_hold_velo_ratio(self, family: str, c_hold: Dict[str, Any]) -> Tuple[float, str]:
        """
        获取材料保压速度相对比例（3 级兜底）

        优先级：
        1. 第 1 级 - Polymer.recommend_hold_velo_ratio 字段（精确值）
        2. 第 2 级 - family_velo_ratio[family]（大类黏度等级查表）
        3. 第 3 级 - default_velo_ratio（兜底保守值）

        物理依据：
        - 比例反映材料临界剪切速率（高黏度 → 偏低防剪切降解；低黏度 → 偏高流动性好）
        - PET 0.10（高黏度 + 半结晶，剪切降解 + 结晶窗口敏感）
        - PC/PBT 0.12（高黏度，剪切降解敏感）
        - PA/POM 0.15（高黏度）
        - PP/PE 0.30（MFI 高，流动性好，可偏高）
        - 定量数值来自材料手册 γ̇_critical 推导 + 海天/震雄/Fanuc 工艺手册

        与保压压力 #6 正交拆分：#6 是流变学驱动（ΔP = Q × R），
        本函数是运动学上限约束（v × A = Q ≤ Q_max）。两者通过材料黏度隐式耦合。

        Args:
            family: 材料大类（来自 _parse_family）
            c_hold: holding 分组合并系数

        Returns:
            (family_velo_ratio, level) 元组
            level ∈ {'precise', 'family', 'default'}
        """
        # ====== 第 1 级：精确值 ======
        precise_ratio = self.material.get('recommend_hold_velo_ratio')
        if precise_ratio is not None:
            return precise_ratio, 'precise'

        # ====== 第 2 级：按大类查表 ======
        ratio_map = c_hold.get('family_velo_ratio', {})
        if family and family in ratio_map:
            return ratio_map[family], 'family'

        # ====== 第 3 级：默认值（兜底）======
        return c_hold.get('default_velo_ratio', 0.15), 'default'

    def _get_gate_factor(self, gate_type: str, c_hold: Dict[str, Any]) -> float:
        """
        获取浇口修正因子（4 档 + 默认）
    
        物理依据：
        - 浇口尺寸决定流阻 → 需更高保压克服阻力
        - 大浇口（直浇口）流阻小 → 偏低于中位
        - 小浇口（点浇口）流阻大 → 偏高于中位
    
        Args:
            gate_type: 浇口类型字符串
    
        Returns:
            gate_factor ∈ {0.95, 1.00, 1.10, 1.00}
        """
        gate_factor_map = c_hold.get('gate_factor', {
            '直浇口': 0.95,
            '护耳式浇口': 1.00,
            '点浇口': 1.10,
            '侧浇口': 1.00,
        })
        return gate_factor_map.get(gate_type, 1.00)
    
    def _get_runner_factor(
        self,
        runner_type: str,
        runner_weight: float,
        c_hold: Dict[str, Any],
    ) -> Tuple[float, str]:
        """
        获取流道修正因子（4 级兜底）
    
        优先级：
        1. 第 1 级 - mold.runner_pressure_factor（制品级精确值）
        2. 第 2 级 - runner_factor[runner_type]（枚举查表）
        3. 第 3 级 - runner_weight 推断（向后兼容老数据）
        4. 第 4 级 - 1.00（默认不修正）
    
        物理依据：
        - 热流道：流道始终熔融 → 无流道冷却收缩 → 保压可偏低
        - 冷流道：流道随制品冷却 → 流道收缩需保压补缩 → 保压需偏高
        - 热转冷：部分流道凝固（混合系统）→ 中位
    
        Args:
            runner_type: 流道类型（热流道/冷流道/热转冷）
            runner_weight: 流道重量 [g]（兜底推断）
            c_hold: holding 分组合并系数
    
        Returns:
            (runner_factor, level) 元组
            level ∈ {'precise', 'runner_type', 'inferred_hot', 'inferred_cold', 'default'}
        """
        from utils.constants import RUNNER_TYPE_HOT, RUNNER_TYPE_COLD, RUNNER_TYPE_HOT_TO_COLD  # noqa
    
        # ====== 第 1 级：制品级精确值 ======
        precise = self.mold.get('runner_pressure_factor')
        if precise is not None:
            return precise, 'precise'
    
        # ====== 第 2 级：枚举查表 ======
        runner_factor_map = c_hold.get('runner_factor', {
            RUNNER_TYPE_HOT: 0.95,
            RUNNER_TYPE_HOT_TO_COLD: 1.00,
            RUNNER_TYPE_COLD: 1.05,
        })
        if runner_type in runner_factor_map:
            return runner_factor_map[runner_type], 'runner_type'
    
        # ====== 第 3 级：runner_weight 推断（向后兼容老数据）======
        if runner_weight == 0:
            return 0.95, 'inferred_hot'      # runner_weight=0 → 热流道
        if runner_weight is not None and runner_weight > 0:
            return 1.05, 'inferred_cold'     # runner_weight>0 → 冷流道
    
        # ====== 第 4 级：默认不修正 ======
        return 1.00, 'default'

    # ========== 松退参数族辅助函数（#15-#18，v1.1）==========

    def _get_suckback_runner_factor(
        self,
        runner_type: str,
        runner_weight: float,
        c_suck: Dict[str, Any],
    ) -> Tuple[float, str]:
        """
        获取松退流道修正因子（3 级兑底）

        物理依据（与 #6 保压压力 runner_factor 方向相反）：
        - 热流道：流道全程熔融 → 浇口关闭后残余压力需传递更远 → 距离×1.60
        - 冷流道：流道随制品冷却已凝固 → 松退只需处理喷嘴 → 距离×1.00
        - 热转冷：主流道热、分流道冷 → 残余压力部分释放 → 距离×1.15

        优先级：
        1. 第 1 级 - runner_factor[runner_type]（枚举查表，suckback 专用表）
        2. 第 2 级 - runner_weight 推断（向后兼容：=0→热流道 1.60 / >0→冷流道 1.00）
        3. 第 3 级 - default_runner_factor（默认 1.00）

        Args:
            runner_type: 流道类型（热流道/冷流道/热转冷）
            runner_weight: 流道重量 [g]（兑底推断）
            c_suck: suckback 分组合并系数

        Returns:
            (runner_factor, level) 元组
            level ∈ {'runner_type', 'inferred_hot', 'inferred_cold', 'default'}
        """
        from utils.constants import RUNNER_TYPE_HOT, RUNNER_TYPE_COLD, RUNNER_TYPE_HOT_TO_COLD  # noqa

        # ====== 第 1 级：suckback 专用查表（与 #6 保压压力方向相反）======
        runner_factor_map = c_suck.get('runner_factor', {
            RUNNER_TYPE_HOT: 1.60,
            RUNNER_TYPE_HOT_TO_COLD: 1.15,
            RUNNER_TYPE_COLD: 1.00,
        })
        if runner_type in runner_factor_map:
            return runner_factor_map[runner_type], 'runner_type'

        # ====== 第 2 级：runner_weight 推断（向后兼容）======
        if runner_weight == 0:
            return 1.60, 'inferred_hot'      # runner_weight=0 → 热流道
        if runner_weight is not None and runner_weight > 0:
            return 1.00, 'inferred_cold'     # runner_weight>0 → 冷流道

        # ====== 第 3 级：默认不修正 ======
        return c_suck.get('default_runner_factor', 1.0), 'default'

    def _get_suckback_gate_factor(
        self,
        runner_type: str,
        gate_type: str,
        c_suck: Dict[str, Any],
    ) -> Tuple[float, str]:
        """
        获取松退浇口修正因子（仅热流道生效）

        物理依据：
        - 冷流道/热转冷：浇口已凝固或部分凝固 → 浇口结构与残余压力释放关系不大 → 1.00
        - 热流道：浇口关闭后仍有残余压力，不同浇口结构释放难度不同
          - 针阀式点浇口/侧浇口：阀门关闭不彻底，残余压力最大 → 1.70
          - 点浇口：浇口小，残余压力较大 → 1.30
          - 侧浇口/直浇口/护耳式浇口：开放浇口，残余压力易释放 → 1.00

        Args:
            runner_type: 流道类型（仅热流道生效）
            gate_type: 浇口类型
            c_suck: suckback 分组合并系数

        Returns:
            (gate_factor, applied) 元组
            applied ∈ {'yes', 'no_cold_runner', 'no_gate_match'}
        """
        applies_to = c_suck.get('gate_factor_applies_to_runner', ['热流道'])

        # ====== 第 1 级：冷流道/热转冷 → 不叠加 gate_factor ======
        if runner_type not in applies_to:
            return 1.0, 'no_cold_runner'

        # ====== 第 2 级：热流道 → 查表 ======
        gate_factor_map = c_suck.get('gate_factor', {
            '针阀式点浇口': 1.70, '针阀式侧浇口': 1.70,
            '点浇口': 1.30,
            '侧浇口': 1.00, '直浇口': 1.00, '护耳式浇口': 1.00,
        })
        if gate_type in gate_factor_map:
            return gate_factor_map[gate_type], 'yes'

        # ====== 第 3 级：未识别浇口 → 默认 ======
        return c_suck.get('default_gate_factor', 1.0), 'no_gate_match'

    def _compute_suckback_distance(
        self,
        abbreviation: str,
        nozzle_type: str,
        runner_type: str,
        runner_weight: float,
        gate_type: str,
        c_suck: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算松退距离（v1.1 5 维物理化推导）

        推导公式：
            D = base_dist × family_dist_factor × nozzle_dist_factor
                × runner_factor × gate_factor
            D = clamp(D, min_dist, max_dist)

        物理依据：详见设计文档 §3.3
            - base_dist: 3.5mm（业内中位）
            - family_dist_factor: 4 档分档（PA 0.65 / 高黏度 0.80 / 基准 1.00 / PVC 1.20）
            - nozzle_dist_factor: 直通 0.95 / 锁闭 1.10
            - runner_factor: 冷 1.00 / 热转冷 1.15 / 热流道 1.60（与 #6 方向相反）
            - gate_factor: 仅热流道生效，针阀式 1.70 / 点浇口 1.30 / 开放 1.00

        Args:
            abbreviation: 材料完整缩写
            nozzle_type: 喷嘴类型
            runner_type: 流道类型
            runner_weight: 流道重量
            gate_type: 浇口类型
            c_suck: suckback 分组合并系数

        Returns:
            (distance, debug_info) 元组
            debug_info 包含各因子与中间值
        """
        # 1. family 距离因子（3 级兑底：精确全名 → 大类 → 默认）
        family_dist_map = c_suck.get('family_dist_factor', {})
        family = self._parse_family(abbreviation)
        if abbreviation in family_dist_map:
            family_dist_factor = family_dist_map[abbreviation]
            family_dist_level = 'precise_abbrev'
        elif family in family_dist_map:
            family_dist_factor = family_dist_map[family]
            family_dist_level = 'precise_family'
        else:
            family_dist_factor = c_suck.get('default_family_dist_factor', 1.0)
            family_dist_level = 'default'

        # 2. 喷嘴距离因子（直通 / 锁闭）
        nozzle_dist_map = c_suck.get('nozzle_dist_factor', {
            '直通型': 0.95, '锁闭型': 1.10,
        })
        nozzle_dist_factor = nozzle_dist_map.get(
            nozzle_type,
            c_suck.get('default_nozzle_dist_factor', 1.0),
        )

        # 3. 流道距离因子（v1.1 新增，与 #6 保压压力方向相反）
        runner_factor, runner_level = self._get_suckback_runner_factor(
            runner_type, runner_weight, c_suck,
        )

        # 4. 浇口距离因子（v1.1 新增，仅热流道生效）
        gate_factor, gate_applied = self._get_suckback_gate_factor(
            runner_type, gate_type, c_suck,
        )

        # 5. 主公式推导
        base_dist = c_suck.get('base_dist', 3.5)
        D_raw = base_dist * family_dist_factor * nozzle_dist_factor * runner_factor * gate_factor

        # 6. 钳制
        min_dist = c_suck.get('min_dist', 1.0)
        max_dist = c_suck.get('max_dist', 12.0)
        D_final = max(min_dist, min(D_raw, max_dist))

        debug_info = {
            'base_dist': base_dist,
            'family_dist_factor': family_dist_factor,
            'family_dist_level': family_dist_level,
            'nozzle_dist_factor': nozzle_dist_factor,
            'runner_factor': runner_factor,
            'runner_level': runner_level,
            'gate_factor': gate_factor,
            'gate_applied': gate_applied,
            'D_raw': D_raw,
            'min_dist': min_dist,
            'max_dist': max_dist,
            'D_final': D_final,
        }
        return D_final, debug_info

    def _compute_suckback_pressure(
        self,
        mach: Dict[str, Any],
        abbreviation: str,
        nozzle_type: str,
        mode: str,
        c_suck: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算松退压力（v1.1，液压机专属 / 全电机为 0）

        推导公式：
            P = max_set_metering_pressure × base_ratio × family_factor
                × mode_factor × nozzle_factor
            P = clamp(P, min_pressure, max_pressure)

        物理依据：详见设计文档 §3.2
            - base_ratio: 0.25（业内中位 2.5/14）
            - family_factor: 4 档分档（PVC 0.50 / PA 1.30 / 高黏度 1.10 / 基准 1.00）
            - mode_factor: 前 0.80 / 后 1.00（仅压力差异化）
            - nozzle_factor: 直通 0.95 / 锁闭 1.10（与距离/速度同源）

        Args:
            mach: 机器信息字典
            abbreviation: 材料完整缩写
            nozzle_type: 喷嘴类型
            mode: 'pre' 前松退 / 'post' 后松退
            c_suck: suckback 分组合并系数

        Returns:
            (pressure, debug_info) 元组
        """
        power_method = mach.get('power_method', '液压机')

        # 全电机分支：P = 0
        if power_method != '液压机':
            return 0.0, {
                'power_method': power_method,
                'P_final': 0.0,
                'note': '全电机无松退压力概念',
            }

        # 液压机分支
        max_set_meter_pres = mach.get('max_set_metering_pressure', 14.0)

        # 1. family 黏度修正（4 档，与 #11 计量压力同语义）
        # 这里不依赖 c_suck，而是复用 #11 的 family_pres_map（设计上一致）
        family_pres_map = {
            'PVC': 0.50,
            'PA66': 1.30, 'PA6': 1.30, 'PA': 1.30,
            'PC': 1.10, 'PMMA': 1.10, 'POM': 1.10,
            'PP': 1.00, 'PE': 1.00, 'LDPE': 1.00, 'HDPE': 1.00, 'LLDPE': 1.00,
            'PS': 1.00, 'HIPS': 1.00, 'ABS': 1.00, 'PET': 1.00, 'PBT': 1.00,
            'PC+ABS': 1.00, 'PC/ABS': 1.00,
        }
        family = self._parse_family(abbreviation)
        if abbreviation in family_pres_map:
            family_pres_factor = family_pres_map[abbreviation]
            family_pres_level = 'precise_abbrev'
        elif family in family_pres_map:
            family_pres_factor = family_pres_map[family]
            family_pres_level = 'precise_family'
        else:
            family_pres_factor = 1.0
            family_pres_level = 'default'

        # 2. mode_factor（前 0.80 / 后 1.00）
        if mode == 'pre':
            mode_factor = c_suck.get('pre_mode_factor', 0.80)
        else:
            mode_factor = c_suck.get('post_mode_factor', 1.00)

        # 3. 喷嘴修正（与 #11 nozzle_factor 对齐）
        nozzle_pres_map = {'直通型': 0.95, '锁闭型': 1.10}
        nozzle_pres_factor = nozzle_pres_map.get(nozzle_type, 1.0)

        # 4. 主公式
        base_ratio = c_suck.get('base_ratio', 0.25)
        P_raw = max_set_meter_pres * base_ratio * family_pres_factor * mode_factor * nozzle_pres_factor

        # 5. 钳制
        min_p = c_suck.get('min_pressure', 1.0)
        max_p = c_suck.get('max_pressure', 5.0)
        P_final = max(min_p, min(P_raw, max_p))

        debug_info = {
            'power_method': power_method,
            'max_set_meter_pres': max_set_meter_pres,
            'base_ratio': base_ratio,
            'family_pres_factor': family_pres_factor,
            'family_pres_level': family_pres_level,
            'mode_factor': mode_factor,
            'nozzle_pres_factor': nozzle_pres_factor,
            'P_raw': P_raw,
            'min_pressure': min_p,
            'max_pressure': max_p,
            'P_final': P_final,
        }
        return P_final, debug_info

    def _compute_suckback_velocity(
        self,
        abbreviation: str,
        nozzle_type: str,
        power_method: str,
        c_suck: Dict[str, Any],
        mach: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算松退速度（v1.1，3 维物理化推导）

        推导公式：
            V = max_set_decompression_velocity × family_velo_factor × nozzle_velo_factor
            V = clamp(V, min_velo, max_velo)

        物理依据：详见设计文档 §3.4
            - family_velo_factor: 4 档分档（PA 0.85 / 高黏度 0.75 / 基准 1.00 / PVC 1.10）
            - nozzle_velo_factor: 直通 1.00 / 锁闭 0.80

        全电机分支：使用 electric_default_velo（机器控制器自动）

        Args:
            abbreviation: 材料完整缩写
            nozzle_type: 喷嘴类型
            power_method: 动力源类型
            c_suck: suckback 分组合并系数
            mach: 机器信息字典（液压机必选）

        Returns:
            (velocity, debug_info) 元组
        """
        # 全电机分支：使用默认速度
        if power_method != '液压机':
            V_final = c_suck.get('electric_default_velo', 20.0)
            return V_final, {
                'power_method': power_method,
                'V_final': V_final,
                'note': '全电机走 electric_default_velo',
            }

        # 液压机分支
        if mach is None:
            mach = {}
        max_decomp_velo = mach.get('max_set_decompression_velocity', 50.0)

        # 1. family 速度因子（3 级兑底）
        family_velo_map = c_suck.get('family_velo_factor', {})
        family = self._parse_family(abbreviation)
        if abbreviation in family_velo_map:
            family_velo_factor = family_velo_map[abbreviation]
            family_velo_level = 'precise_abbrev'
        elif family in family_velo_map:
            family_velo_factor = family_velo_map[family]
            family_velo_level = 'precise_family'
        else:
            family_velo_factor = c_suck.get('default_family_velo_factor', 1.0)
            family_velo_level = 'default'

        # 2. 喷嘴速度因子
        nozzle_velo_map = c_suck.get('nozzle_velo_factor', {
            '直通型': 1.00, '锁闭型': 0.80,
        })
        nozzle_velo_factor = nozzle_velo_map.get(
            nozzle_type,
            c_suck.get('default_nozzle_velo_factor', 1.0),
        )

        # 3. 主公式
        V_raw = max_decomp_velo * family_velo_factor * nozzle_velo_factor

        # 4. 钳制
        min_v = c_suck.get('min_velo', 3.0)
        max_v = c_suck.get('max_velo', 50.0)
        V_final = max(min_v, min(V_raw, max_v))

        debug_info = {
            'power_method': power_method,
            'max_decomp_velo': max_decomp_velo,
            'family_velo_factor': family_velo_factor,
            'family_velo_level': family_velo_level,
            'nozzle_velo_factor': nozzle_velo_factor,
            'V_raw': V_raw,
            'min_velo': min_v,
            'max_velo': max_v,
            'V_final': V_final,
        }
        return V_final, debug_info

    @staticmethod
    def _compute_suckback_time(
        distance: float,
        velocity: float,
        c_suck: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算松退时间（派生）

        派生公式：
            T = D / V
            T = clamp(T, min_time, max_time)

        Args:
            distance: 松退距离 [mm]
            velocity: 松退速度 [mm/s]
            c_suck: suckback 分组合并系数

        Returns:
            (time, debug_info) 元组
        """
        if velocity <= 0:
            T_final = c_suck.get('min_time', 0.1)
        else:
            T_raw = distance / velocity
            min_t = c_suck.get('min_time', 0.1)
            max_t = c_suck.get('max_time', 5.0)
            T_final = max(min_t, min(T_raw, max_t))

        return T_final, {
            'distance': distance,
            'velocity': velocity,
            'T_final': T_final,
            'note': '派生：T = D / V',
        }

    # ========== 温度族辅助函数（#19+#20，v1.0）==========

    def _get_noz_family_offset(
        self,
        family: str,
        c_noz: Dict[str, Any],
    ) -> Tuple[float, str]:
        """
        获取喷嘴温度 family 修正偏移（3 级兑底）

        优先级：
        1. 第 1 级 - family_offset[family]（精确值）
        2. 第 2 级 - family_offset_default（兑底）

        物理依据（详见设计文档 §3.1）：
        - PA66 +5℃：防含水率突变致黏度突降
        - PA6/PA/PET/PBT +3℃：结晶型冷凝阻塞
        - PC/PMMA/POM 0℃：高黏度持平
        - PVC -5℃：热敏降防 HCl 析出
        - PP/PE/PS/ABS 0℃：通用基准

        Args:
            family: 材料大类（来自 _parse_family）
            c_noz: nozzle 分组合并系数

        Returns:
            (offset, level) 元组，level ∈ {'precise', 'default'}
        """
        family_offset_map = c_noz.get('family_offset', {})
        if family in family_offset_map:
            return family_offset_map[family], 'precise'
        return c_noz.get('family_offset_default', 0.0), 'default'

    def _compute_noz_temp(
        self,
        recommend_melt_temp: float,
        nozzle_type: str,
        family: str,
        c_noz: Dict[str, Any],
        min_melt_temp: Optional[float] = None,
        max_melt_temp: Optional[float] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        计算喷嘴温度（#19，2 维物理化推导）

        推导公式：
            noz_temp_raw = melt_temp + noz_offset[nozzle_type] + family_offset[family]
            noz_temp = clamp(noz_temp_raw, [min_melt - tol, max_melt + tol])

        钳制容差 ±10℃（noz_temp_clamp_tolerance）
        - 字段缺失时用 melt_temp ± 40℃ 兑底边界

        Args:
            recommend_melt_temp: 推荐熔体温度
            nozzle_type: 喷嘴类型（直通型/锁闭型）
            family: 材料大类
            c_noz: nozzle 分组合并系数
            min_melt_temp: 材料手册下限（可选）
            max_melt_temp: 材料手册上限（可选）

        Returns:
            (noz_temp, debug_info) 元组
        """
        # 维度 1：noz_offset 基准
        noz_key = 'noz_offset_locking' if nozzle_type != '直通型' else 'noz_offset_straight'
        noz_offset = c_noz.get(noz_key, 0.0)

        # 维度 2：family_offset 修正
        family_offset, family_level = self._get_noz_family_offset(family, c_noz)

        noz_temp_raw = recommend_melt_temp + noz_offset + family_offset

        # 边界钳制（材料手册容差 ±10℃）
        tol = c_noz.get('noz_temp_clamp_tolerance', 10.0)
        if min_melt_temp is None:
            min_melt_temp = recommend_melt_temp - 40.0
        if max_melt_temp is None:
            max_melt_temp = recommend_melt_temp + 40.0
        lower = min_melt_temp - tol
        upper = max_melt_temp + tol
        noz_temp_final = max(lower, min(noz_temp_raw, upper))

        clamped = (noz_temp_final != noz_temp_raw)
        return noz_temp_final, {
            'noz_offset': noz_offset,
            'family_offset': family_offset,
            'family_offset_level': family_level,
            'noz_temp_raw': noz_temp_raw,
            'clamped': clamped,
            'clamp_bounds': (lower, upper),
        }

    def _get_barrel_family_decrement(
        self,
        family: str,
        c_brl: Dict[str, Any],
    ) -> Tuple[float, str]:
        """
        获取料筒 family 递减梯度（3 级兑底）

        优先级：
        1. 第 1 级 - family_decrement[family]（精确值）
        2. 第 2 级 - family_decrement_default（兑底 10.0）

        物理依据（详见设计文档 §3.2）：
        - PVC 5℃：极平缓防分解
        - PC/PMMA/POM/PA/PET/PBT 8℃：高黏度平缓防降解
        - PP/PE/ABS/PS 10℃：通用中位

        Args:
            family: 材料大类
            c_brl: barrel 分组合并系数

        Returns:
            (decrement, level) 元组
        """
        family_decrement_map = c_brl.get('family_decrement', {})
        if family in family_decrement_map:
            return family_decrement_map[family], 'precise'
        return c_brl.get('family_decrement_default', 10.0), 'default'

    def _compute_brl_temp_steps(
        self,
        recommend_melt_temp: float,
        stages: int,
        family: str,
        c_brl: Dict[str, Any],
        glass_transition_temp: Optional[float] = None,
    ) -> Tuple[List[float], Dict[str, Any]]:
        """
        计算料筒温度分布（#20，4 维物理化推导）

        推导公式：
            T[i] = melt_temp - i^k × family_decrement × stages_factor(i)
            T[0] = clamp(T[0], [melt-5, melt+5])
            T[N-1] = clamp(T[N-1], [max(Tg+30, melt-60), melt-5])

        物理依据：
        - 幂函数 k=1.2 非线性：靠喷嘴平缓、防降解；靠料口陡、防冷料阻塞
        - family_decrement 5/8/10℃ 三档（热敏 / 平缓 / 中位）
        - stages 自适应：>7 段 × 0.8 但上限 8℃（与 PC 平缓对齐）
        - 双层边界钳制：防冷料入喷嘴 + 防塑化不充分

        Args:
            recommend_melt_temp: 推荐熔体温度
            stages: 段数
            family: 材料大类
            c_brl: barrel 分组合并系数
            glass_transition_temp: 玻璃化转变温度（可选）

        Returns:
            (brl_temp_steps, debug_info) 元组
        """
        if stages <= 0:
            return [], {'note': 'stages=0，返回空列表'}

        # 维度 1：family_decrement 修正
        family_decrement, family_level = self._get_barrel_family_decrement(family, c_brl)

        # 维度 2：stages 自适应（> 阈值走细颗粒）
        threshold = c_brl.get('stages_threshold', 7)
        high_stages_factor = c_brl.get('high_stages_factor', 0.8)
        high_stages_clamp = c_brl.get('high_stages_clamp', 8.0)
        if stages > threshold:
            decrement = min(family_decrement * high_stages_factor, high_stages_clamp)
        else:
            decrement = family_decrement

        # 维度 3：幂函数 k 非线性递减
        k = c_brl.get('power_k', 1.2)
        raw_steps = [recommend_melt_temp - (i ** k) * decrement for i in range(stages)]

        # 维度 4：双层边界钳制
        s1_upper = recommend_melt_temp + c_brl.get('segment_1_upper_offset', 5.0)
        s1_lower = recommend_melt_temp + c_brl.get('segment_1_lower_offset', -5.0)
        sN_lower_offset = c_brl.get('segment_N_lower_min', -60.0)
        sN_lower_tg_plus = c_brl.get('segment_N_lower_min_tg_plus', 30.0)
        sN_lower = max(
            recommend_melt_temp + sN_lower_offset,
            (glass_transition_temp or -999) + sN_lower_tg_plus,
        )
        sN_upper = recommend_melt_temp + c_brl.get('segment_N_upper_offset', -5.0)

        # 段 N 钳制（下限与上限独立判定，避免 sN_lower > sN_upper 边界矛盾时丢失保护）
        # 例外：Tg+30 > melt-5 时（如极端 Tg=200, melt=230），sN_lower=230 > sN_upper=225
        # 此时 raw < sN_lower → 钳到 230，但需进一步钳上限避免料口过热 → 225
        clamped_steps = list(raw_steps)
        clamped_segments = []
        # 段 1 钳制
        if clamped_steps[0] > s1_upper:
            clamped_steps[0] = s1_upper
            clamped_segments.append(('segment_1', 0, 'upper'))
        elif clamped_steps[0] < s1_lower:
            clamped_steps[0] = s1_lower
            clamped_segments.append(('segment_1', 0, 'lower'))
        # 段 N 钳制下限
        if clamped_steps[-1] < sN_lower:
            clamped_steps[-1] = sN_lower
            clamped_segments.append(('segment_N', stages - 1, 'lower'))
        # 段 N 钳制上限（独立 if，不与下限互斥）
        if clamped_steps[-1] > sN_upper:
            clamped_steps[-1] = sN_upper
            clamped_segments.append(('segment_N', stages - 1, 'upper'))

        return clamped_steps, {
            'family_decrement': family_decrement,
            'family_decrement_level': family_level,
            'stages': stages,
            'stages_factor': (high_stages_factor if stages > threshold else 1.0),
            'effective_decrement': decrement,
            'power_k': k,
            'raw_steps': raw_steps,
            'clamped_steps': clamped_segments,
            's1_bounds': (s1_lower, s1_upper),
            'sN_bounds': (sN_lower, sN_upper),
        }

    # ========== 保压时间查表（材料 × 壁厚 + 浇口 + 流道 + 模温 + 结晶拉长，五维差异化）==========

    def _get_family_gate_freeze_time(
        self,
        family: str,
        bucket: str,
        c_hold: Dict[str, Any],
    ) -> Tuple[float, str]:
        """
        获取材料 × 壁厚浇口凝固时间（4 级兜底）

        优先级：
        1. 第 1 级 - mold.hold_time_override[bucket]（制品级精确值）
        2. 第 2 级 - family_gate_freeze_time[family][bucket]（大类 × 桶查表）
        3. 第 3 级 - family_gate_freeze_time[family][medium]（同 family 中桶兜底）
        4. 第 4 级 - default_freeze_time[bucket]（材料未知兜底）

        物理依据：
        - 基于 Fourier 热扩散 t ≈ h²/α_eff
        - α_eff 来自材料手册 + 模具接触热阻综合
        - h 取典型浇口厚度：thin 0.8mm / medium 1.5mm / thick 3.0mm

        Args:
            family: 材料大类（来自 _parse_family）
            bucket: 壁厚档（'thin' / 'medium' / 'thick'）
            c_hold: holding 分组合并系数

        Returns:
            (freeze_time, level) 元组
            level ∈ {'precise', 'family_bucket', 'family_default_bucket', 'default'}
        """
        # ====== 第 1 级：制品级精确值 ======
        override_map = self.mold.get('hold_time_override') or {}
        if isinstance(override_map, dict):
            precise = override_map.get(bucket)
            if precise is not None:
                return precise, 'precise'

        # ====== 第 2 级：按 family × bucket 查表 ======
        family_map = c_hold.get('family_gate_freeze_time', {})
        if family and family in family_map:
            fam_bucket = family_map[family].get(bucket)
            if fam_bucket is not None:
                return fam_bucket, 'family_bucket'
            # ====== 第 3 级：同 family 中桶兜底 ======
            fam_medium = family_map[family].get('medium')
            if fam_medium is not None:
                return fam_medium, 'family_default_bucket'

        # ====== 第 4 级：未知材料兜底 ======
        default_map = c_hold.get(
            'default_freeze_time', {'thin': 5.3, 'medium': 18.8, 'thick': 75.0}
        )
        return default_map.get(bucket, 18.8), 'default'

    def _get_gate_factor_for_hold(self, gate_type: str, c_hold: Dict[str, Any]) -> float:
        """
        获取保压时间场景的浇口修正因子（4 档 + 默认）

        与 #6 保压压力的 gate_factor **取值方向相反**：
        - 保压压力：直浇口 ×0.95（流阻小、压力可偏低）
        - 保压时间：直浇口 ×1.20（大浇口凝固慢、时间需偏长）

        物理依据：
        - 大浇口冷却时间长 → 凝固时窗大 → 保压时间长
        - 小浇口冷却时间短 → 凝固时窗小 → 保压时间短

        Args:
            gate_type: 浇口类型字符串

        Returns:
            gate_factor_hold ∈ {1.20, 1.05, 0.85, 0.70, 1.00}
        """
        gate_factor_map = c_hold.get('gate_factor_hold_time', {
            '直浇口': 1.20,
            '护耳式浇口': 1.05,
            '侧浇口': 0.85,
            '点浇口': 0.70,
        })
        return gate_factor_map.get(gate_type, 1.00)

    def _get_gate_factor_for_hold_velo(self, bucket: str, c_hold: Dict[str, Any]) -> float:
        """
        获取保压速度场景的浇口尺寸修正因子（3 桶 + 默认）

        物理依据：浇口间隙 h_gate 越小 → 相同螺杆速度下浇口处流速越高 → 剪切速率约束越紧
        - thin 桶（h=0.8mm）→ 浇口薄 → 偏低（防剪切降解）
        - medium 桶（h=1.5mm）→ 中位
        - thick 桶（h=3.0mm）→ 浇口厚 → 偏高（防凹陷）

        与 #8 保压时间 gate_factor 维度同源但语义不同：
        - #8 看浇口凝固时间（薄浇口凝固快 → 时间短）
        - 本函数看浇口剪切速率（薄浇口剪切敏感 → 速度低）
        - **方向相同**：thin 偏小，thick 偏大

        Args:
            bucket: 壁厚档（'thin' / 'medium' / 'thick'）
            c_hold: holding 分组合并系数

        Returns:
            gate_factor_velo ∈ {0.90, 1.00, 1.10, 1.00}
        """
        gate_factor_map = c_hold.get('gate_factor_hold_velo', {
            'thin': 0.90,
            'medium': 1.00,
            'thick': 1.10,
        })
        return gate_factor_map.get(bucket, 1.00)

    def _get_mold_temp_factor(self, mold_temp: float, c_hold: Dict[str, Any]) -> Tuple[float, str]:
        """
        获取模温修正因子（4 桶 + 默认）

        物理依据：高模温拉长浇口凝固时窗（每 +20℃ 拉长 10~15%）

        Args:
            mold_temp: 模具温度（℃）

        Returns:
            (mold_temp_factor, level) 元组
            level ∈ {'low', 'medium', 'high', 'ultra_high', 'default'}
        """
        temp_factor_map = c_hold.get('mold_temp_factor_hold_time', {
            'low': 0.95, 'medium': 1.00, 'high': 1.10, 'ultra_high': 1.20,
        })
        if mold_temp <= 0:
            return temp_factor_map.get('medium', 1.00), 'default'
        if mold_temp <= 40:
            return temp_factor_map.get('low', 0.95), 'low'
        if mold_temp <= 80:
            return temp_factor_map.get('medium', 1.00), 'medium'
        if mold_temp <= 120:
            return temp_factor_map.get('high', 1.10), 'high'
        return temp_factor_map.get('ultra_high', 1.20), 'ultra_high'

    def _get_crystallinity_kick(self, family: str, c_hold: Dict[str, Any]) -> float:
        """
        获取结晶动力学拉长因子（仅半结晶 family 显著）

        物理依据：半结晶在 Tg~Tm 中段结晶速率最高，拉长保压可促结晶
        - PET 1.80 长结晶窗口（酒瓶瓶盖长保压典型）
        - PA 1.40 含水扩散
        - POM 1.30 高结晶速率
        - PP/PE 1.10/1.05 结晶快
        - PC/PS/ABS/AS/PMMA 1.00 非结晶

        Args:
            family: 材料大类（来自 _parse_family）

        Returns:
            crystallinity_kick ∈ [1.00, 1.80]
        """
        kick_map = c_hold.get('crystallinity_kick', {
            'PET': 1.80, 'PBT': 1.50, 'PA': 1.40, 'POM': 1.30,
            'PP': 1.10, 'PE': 1.05,
            'PC': 1.00, 'PS': 1.00, 'ABS': 1.00, 'AS': 1.00, 'PMMA': 1.00,
        })
        return kick_map.get(family, 1.00)

    def _get_family_hold_time_max(self, family: str, c_hold: Dict[str, Any]) -> float:
        """
        获取 family 自适应保压时间上限（**关键**：移除 10s 硬上限）

        物理依据：
        - 标准材料（PP/PE/PS/ABS/...）：30~60s（工艺上限）
        - 半结晶材料（PBT/PA）：120s（中长保压）
        - **PET：600s**（酒瓶瓶盖长保压典型 100~300s，支持上限合理设置 600s）
        - 未识别 family：300s（默认兑底，保守上限）

        Args:
            family: 材料大类（来自 _parse_family）

        Returns:
            family_hold_time_max [s]
        """
        max_map = c_hold.get('family_hold_time_max', {
            'PP': 30.0, 'PE': 30.0, 'PS': 60.0, 'ABS': 60.0, 'AS': 60.0, 'PMMA': 60.0,
            'PC': 60.0, 'POM': 60.0, 'PBT': 120.0, 'PA': 120.0,
            'PET': 600.0,
        })
        return max_map.get(family, c_hold.get('default_hold_time_max', 300.0))

    # ========== 冷却参数辅助（v1.0：算法 #10）==========

    @staticmethod
    def _get_delta_temp_factor(
        t_mold: float, t_melt: float, t_eject: float
    ) -> Tuple[float, str]:
        """
        获取温差修正因子 ΔT_factor（模温修正，5 档分档）

        物理依据：Fourier 热扩散 t ∝ ln((T_melt-T_mold)/(T_eject-T_mold))
        温差比越大 → 冷源越冷 → 冷却越快

        5 档分级：
        - < 0.5   → 1.20  模温过高（接近熔温）→ 冷却极慢
        - 0.5~0.7 → 1.10  模温偏高 → 偏慢
        - 0.7~1.0 → 1.00  正常模温（行业典型）
        - 1.0~1.5 → 0.95  模温偏低 → 偏快
        - > 1.5   → 0.90  模温过低（冷流道）→ 冷却快但质量差

        缺失数据兑底：t_mold=0 或 t_eject=0 → 1.0（行业通用中位值）

        Args:
            t_mold: 模具温度（℃）
            t_melt: 熔体温度（℃）
            t_eject: 顶出温度（℃）

        Returns:
            (delta_factor ∈ [0.90, 1.20], level: str)
        """
        # 缺失数据兑底：1.0（行业通用中位值）
        if t_mold <= 0 or t_eject <= 0 or t_melt <= 0:
            return 1.0, 'missing_data_default'

        # 温差比 = (T_melt - T_mold) / (T_melt - T_eject)
        if t_melt <= t_eject:
            # 异常场景：熔温 <= 顶出温度（不应该发生）→ 兑底到 1.0
            return 1.0, 'invalid_temp_default'

        delta_ratio = (t_melt - t_mold) / (t_melt - t_eject)

        if delta_ratio < 0.5:
            return 1.20, 'extreme_hot_mold'
        elif delta_ratio < 0.7:
            return 1.10, 'hot_mold'
        elif delta_ratio < 1.0:
            return 1.00, 'normal'
        elif delta_ratio < 1.5:
            return 0.95, 'cold_mold'
        else:
            return 0.90, 'extreme_cold_mold'

    @staticmethod
    def _get_cool_crystallinity_kick(
        mat: Dict[str, Any], c_cool: Dict[str, Any]
    ) -> Tuple[float, str]:
        """
        获取冷却结晶拉长因子（半结晶释放潜热）

        物理依据：半结晶材料冷却过程释放结晶潜热，额外冷却时间 +10~18%
        （结晶潜热 PP 207J/g, PA66 230J/g, PET 140J/g, POM 250J/g）

        与 #8 保压时间的区别：
        - #8 保压 kick：按 family 细化（PET 1.80 / PA 1.40 / POM 1.30 / PP 1.10）
        - 冷却 kick：统一 1.15（半结晶 / 无定形 二分）
          原因：冷却场景使用统一的结晶潜热修正即可，不需要 family 级细化

        缺失数据兑底：默认 1.10（保守拉长，避免低估冷却需求）

        Args:
            mat: 材料字典（含 category 字段：结晶型 / 无定形）
            c_cool: 冷却规则配置

        Returns:
            (crystallinity_kick ∈ [1.00, 1.15], level: str)
        """
        category = (mat.get('category') or '').strip() if mat.get('category') else ''
        kick_map = c_cool.get('crystallinity_kick', {
            'crystalline': 1.15,   # 半结晶（释放潜热）
            'amorphous': 1.00,     # 无定形（无潜热）
        })

        if category == '结晶型':
            return kick_map.get('crystalline', 1.15), 'crystalline'
        elif category == '无定形':
            return kick_map.get('amorphous', 1.00), 'amorphous'
        else:
            return c_cool.get('default_crystallinity_kick', 1.10), 'unknown_default'

    # ========== 料垫计算辅助（机器物理）==========

    @staticmethod
    def _compute_cushion_len(screw_diameter: float, c_vps: Dict[str, Any]) -> int:
        """
        计算料垫长度（螺杆最终停止位置）

        公式：cushion_len = max(ceil(D / 4), cushion_min_abs)

        物理依据：
        - D / 4 为各厂商经验值的物理基础
          · 海天 8–12mm（推算 D=32–48mm）
          · Fanuc 10–15mm（推算 D=40–60mm）
        - 向上取整符合工业实践（安全优先，料垫宁多勿少）
        - cushion_min_abs 为绝对最小值（防止螺杆撞模）

        Args:
            screw_diameter: 螺杆直径 [mm]
            c_vps: vp_switch 分组合并系数

        Returns:
            料垫长度 [mm]（整数，与各厂商经验值一致）
        """
        cushion_min_abs = c_vps.get('cushion_min_abs', 5)
        return max(math.ceil(screw_diameter / 4), cushion_min_abs)

    # ========== 几何量计算辅助 ==========

    @staticmethod
    def _compute_a_screw(screw_diameter: float) -> float:
        """计算螺杆截面积 [mm²]

        A_screw = π × D² / 4
        """
        return HSO_PI * (screw_diameter ** 2) / 4

    @staticmethod
    def _compute_total_len(total_weight: float, melt_density: float, screw_diameter: float) -> float:
        """计算完整理论行程 [mm]

        推导：质量守恒 + 圆柱几何
            injection_volume = total_weight / melt_density    # [cm³]
            L_theory = injection_volume / A_screw × 1000     # [mm]

        Args:
            total_weight: 总重量（制品 + 流道）[g]
            melt_density: 熔体密度 [g/cm³]
            screw_diameter: 螺杆直径 [mm]

        Returns:
            完整理论行程 [mm]
        """
        a_screw = ProcessInitializer._compute_a_screw(screw_diameter)
        injection_volume = total_weight / melt_density
        return injection_volume * 1000.0 / a_screw

    # ========== 注塑机工艺参数（主体） ==========

    def _derive_process(self, params: ProductionParams):
        """
        推导注塑机工艺参数（主体）

        包含：注射、VP切换、保压、冷却、计量、松退、温度

        字段来源：
        - 模具/产品参数：self.mold（product_weight / runner_weight / ave_thickness / max_thickness / max_length / gate_type / gate_radius / gate_length / gate_width / inject_cycle_require）
        - 工艺设定：self.process_set（vps_mode / VP_switch_mode / pre_met_decomp_mode / pst_met_decomp_mode）
        """
        prod = self.mold
        mach = self.machine
        mat = self.material
        proc = params.process
        ps = self.process_set

        # 提取分组系数（避免每处重复 .get）
        c_inj = self._coeffs.get('injection', {})
        c_vps = self._coeffs.get('vp_switch', {})
        c_hold = self._coeffs.get('holding', {})
        c_cool = self._coeffs.get('cooling', {})
        c_met = self._coeffs.get('metering', {})
        c_back = self._coeffs.get('back_pressure', {})
        c_decomp = self._coeffs.get('decompression', {})
        c_noz = self._coeffs.get('nozzle', {})              # 🆕 v1.0 #19 喷嘴温度
        c_brl = self._coeffs.get('barrel', {})               # 🆕 v1.0 #20 料筒温度分布
        c_temp = {'nozzle': c_noz, 'barrel': c_brl}          # 向后兼容（可兑底）

        # ========== 基础计算 ==========
        total_weight = prod['product_weight']
        runner_weight = prod.get('runner_weight', 0)
        product_weight = total_weight - runner_weight
        melt_density = mat.get('melt_density', 0.95)

        # 流长比
        max_length = prod.get('max_length', 100)
        avg_thickness = prod.get('ave_thickness', 2)
        inj_ratio = max_length / avg_thickness

        # 注射行程
        screw_diameter = mach.get('screw_diameter', 35)
        a_screw = self._compute_a_screw(screw_diameter)
        total_len = self._compute_total_len(total_weight, melt_density, screw_diameter)

        # 【重构】length_ratio 基于实际保压推进需求反推，不再按总重量三档硬分
        # 推导链：质量守恒 → PVT压缩 → 圆柱几何 → 螺杆推进距离 → 反推 ratio
        # 数据源：3 级兜底（精确值 / 大类典型值 / 默认值）
        shrink_rate, shrink_level = self._get_shrink_rate(c_inj)
        pvt_compress = c_inj.get('default_pvt_compress', 0.015)

        # 实际需要的保压推进距离 = (收缩 + PVT压缩) × 制品体积 / 螺杆截面积
        # 不设下限：ratio 自然被 max(0, min(1, ...)) 钳制，小制品下 ratio 自然趋近 1.0
        replenish_len = (shrink_rate + pvt_compress) * total_weight / (melt_density * a_screw) * 1000.0

        # 反推 length_ratio（钳制到 [0, 1] 避免物理上无意义）
        length_ratio = max(0.0, min(1.0, 1.0 - replenish_len / total_len))
        inj_len = total_len * length_ratio

        # 【重构】cushion_len（料垫）由机器物理参数推导，不再取拍脑袋中间值 12mm
        # 公式：cushion_len = max(ceil(D / 4), cushion_min_abs)
        # 依据：D / 4 与海天（8–12mm）、Fanuc（10–15mm）经验值高度吻合
        cushion_len = self._compute_cushion_len(screw_diameter, c_vps)

        # inj_pos 位置语义：默认单段注射位置 = 料垫 + 补缩长度（与 VP 切换位置同源）
        # 复用 inj_pos 使 inj_pos_steps / vps_pos 共享同一推导量，避免表达式散落
        inj_pos = cushion_len + replenish_len

        logger.debug(
            f"注射行程: shrink_rate={shrink_rate:.3f} (level={shrink_level}), "
            f"replenish_len={replenish_len:.2f}mm, length_ratio={length_ratio:.3f}"
        )

        # ========== 注射参数 ==========
        max_inj_pres = mach.get('max_set_injection_pressure', 150)
        max_inj_velo = mach.get('max_set_injection_velocity', 100)

        # 【重构】注射压力 = 材料黏度等级 × 流长比修正（二维物理推导）
        # 推导链：流变学定律 → 材料黏度等级（base_ratio） × 流长比修正（length_factor）
        # 数据源：3 级兜底（精确值 / 大类查表 / 默认值）
        # 物理详见 _dev_refs/2026-07-05-injection-pressure-physics-design.md
        family = self._parse_family(mat.get('abbreviation', ''))
        base_ratio, base_level = self._get_base_pressure_ratio(family, c_inj)
        length_factor, factor_level = self._get_length_factor(inj_ratio, c_inj)

        inj_pres_calculated = max_inj_pres * base_ratio * length_factor
        # 安全钳制：不超 HMI 设定上限的 max_safe_pressure_ratio，避免极端推导出爆模
        max_safe_ratio = c_inj.get('max_safe_pressure_ratio', 0.90)
        inj_pres = min(inj_pres_calculated, max_inj_pres * max_safe_ratio)

        logger.debug(
            f"注射压力: family={family or 'unknown'} (level={base_level}), "
            f"base_ratio={base_ratio:.3f}, inj_ratio={inj_ratio:.1f}, "
            f"length_factor={length_factor:.3f} (level={factor_level}), "
            f"inj_pres={inj_pres:.2f}MPa ({(inj_pres / max_inj_pres * 100):.1f}% max)"
        )

        # 【重构】注射速度 = 材料流动性等级 × 流长比修正 × 模温修正（三维物理推导）
        # 推导链：体积流量恒等式 + 剪切速率约束 → 流动性等级 × 几何修正 × 温度修正
        # 数据源：3 级兜底（精确值 / 大类查表 / 默认值）
        # 复用上层已计算的 family（同函数中 inj_pres 也用），inj_ratio
        # 物理详见 _dev_refs/2026-07-05-injection-velocity-physics-design.md
        mold_temp = mat.get('recommended_mold_temp', 50)
        base_velo_ratio, base_velo_level = self._get_base_velocity_ratio(family, c_inj)
        length_velo_factor, length_velo_level = self._get_length_velocity_factor(inj_ratio, c_inj)
        temp_velo_modifier, temp_velo_level = self._get_temp_velocity_modifier(mold_temp, c_inj)

        inj_velo_calculated = max_inj_velo * base_velo_ratio * length_velo_factor * temp_velo_modifier
        # 安全钳制：不超 HMI 设定上限的 max_safe_velocity_ratio，避免剪切烧焦、飞边
        max_safe_velo_ratio = c_inj.get('max_safe_velocity_ratio', 0.95)
        inj_velo = min(inj_velo_calculated, max_inj_velo * max_safe_velo_ratio)

        logger.debug(
            f"注射速度: family={family or 'unknown'} (level={base_velo_level}), "
            f"base_velo_ratio={base_velo_ratio:.3f}, inj_ratio={inj_ratio:.1f}, "
            f"length_velo_factor={length_velo_factor:.3f} (level={length_velo_level}), "
            f"mold_temp={mold_temp:.1f}℃, temp_modifier={temp_velo_modifier:.3f} (level={temp_velo_level}), "
            f"inj_velo={inj_velo:.2f}mm/s ({(inj_velo / max_inj_velo * 100):.1f}% max)"
        )

        # 【重构】注射时间 = 几何下限 + 工艺窗口钳制（家族 × 壁厚档，二维差异化）
        # 推导链：体积守恒 → 几何下限 (inj_len / inj_velo) → 材料×壁厚钳制窗口 (min_t, max_t)
        # 数据源：3 级兜底（精确值 / 大类×壁厚查表 / 默认值）
        # 物理详见 _dev_refs/2026-07-05-injection-time-physics-design.md
        max_thickness = prod.get('max_thickness', 0)
        bucket, bucket_level = self._get_thickness_bucket(max_thickness, c_inj)
        (min_t, max_t), window_level = self._get_inj_time_window(family, bucket, c_inj)

        # 几何下限：与已物理化的 inj_velo 同源（inj_len / inj_velo）
        # inj_velo=0 时退化到 min_t（避免除零）
        inj_time_geo = inj_len / inj_velo if inj_velo > 0 else min_t

        # 钳制：保留物理可达性（≥ min_t 防冻结、≤ max_t 防飞边/欠注）
        inj_time = max(min_t, min(inj_time_geo, max_t))

        logger.debug(
            f"注射时间: family={family or 'unknown'}, max_thickness={max_thickness:.2f}mm, "
            f"bucket={bucket} (level={bucket_level}), window=({min_t:.2f}s, {max_t:.2f}s) (level={window_level}), "
            f"inj_time_geo={inj_time_geo:.3f}s → inj_time={inj_time:.3f}s"
        )

        proc.inj_stg = 1
        proc.inj_spd_steps = [inj_velo]
        proc.inj_pres_steps = [inj_pres]
        proc.inj_pos_steps = [inj_pos]
        proc.inj_t = inj_time
        proc.inj_dly_t = HSO_INJ_START_DELAY_TIME

        # ========== VP 切换参数（v3.1：3 级兜底 + 4 种模式行业标准推荐）==========
        # 优先级：
        #   Level 1 - 用户明确指定 vps_mode（int 0~3）         → 'explicit'
        #   Level 2 - 字符串兼容（process_set['VP_switch_mode']）   → 'legacy_string'
        #   Level 3 - 默认位置切换（mode=0）                     → 'default'
        # 推荐原则：基于行业标准推导公式填充推荐值
        #   mode=0 位置：vps_pos = inj_pos（算法 #1+#2 推导）
        #   mode=1 时间：vps_t = inj_time × 0.95（行业共识：95% 注射时间）
        #   mode=2 压力：vps_pres = inj_pres × 0.85（避开压力峰值）
        #   mode=3 位置&时间：两者同时填充（冗余保护）
        # 物理详见 _dev_refs/2026-07-05-vp-switch-mode-physics-design.md
        vps_mode_int = ps.get('vps_mode')
        if isinstance(vps_mode_int, int) and 0 <= vps_mode_int <= 3:
            proc.vps_mode = vps_mode_int
            vps_mode_source = 'explicit'
        elif ps.get('VP_switch_mode') is not None:
            vp_mode_str = ps.get('VP_switch_mode')
            if vp_mode_str == '位置':
                proc.vps_mode = 0
            elif vp_mode_str == '时间':
                proc.vps_mode = 1
            elif vp_mode_str == '压力':
                proc.vps_mode = 2   # 显式映射
            elif vp_mode_str == '位置&时间':
                proc.vps_mode = 3   # 仅此一种写法
            else:
                # "其他" 等未知字符串 → 兜底到压力切换
                proc.vps_mode = 2
            vps_mode_source = 'legacy_string'
        else:
            proc.vps_mode = 0   # 默认位置切换
            vps_mode_source = 'default'

        # 按 mode 填充推荐值（行业标准推导公式）
        proc.vps_pos = 0
        proc.vps_t = 0
        proc.vps_pres = 0
        proc.vps_spd = 0

        # 获取 inj_pres（用于 mode=2 的推荐值）
        inj_pres_1st_for_vps = proc.inj_pres_steps[0] if proc.inj_pres_steps else 0.0

        if proc.vps_mode == 0:
            # 位置切换：来自算法 #1+#2 推导的 inj_pos
            proc.vps_pos = inj_pos
        elif proc.vps_mode == 1:
            # 时间切换：time_switch_ratio × inj_time（行业共识 0.95，可被配置覆盖）
            proc.vps_t = inj_time * c_vps.get('time_switch_ratio', 0.95)
        elif proc.vps_mode == 2:
            # 压力切换：pres_switch_ratio × inj_pres（避开压力峰值 0.85，可被配置覆盖）
            proc.vps_pres = inj_pres_1st_for_vps * c_vps.get('pres_switch_ratio', 0.85)
        elif proc.vps_mode == 3:
            # 位置&时间（冗余保护）：两个值都填
            proc.vps_pos = inj_pos
            proc.vps_t = inj_time * c_vps.get('time_switch_ratio', 0.95)

        logger.debug(
            f"VP 切换参数: mode={proc.vps_mode} (source={vps_mode_source}) "
            f"vps_pos={proc.vps_pos:.2f}mm vps_t={proc.vps_t:.3f}s "
            f"vps_pres={proc.vps_pres:.2f}MPa (inj_pos={inj_pos:.2f}mm, "
            f"inj_time={inj_time:.3f}s, inj_pres={inj_pres_1st_for_vps:.2f}MPa)"
        )

        # ========== 保压参数 ==========
        max_hold_pres = mach.get('max_set_holding_pressure', 100)
        max_hold_velo = mach.get('max_set_holding_velocity', 100)

        # 【重构】保压压力 = 注射压力 × 材料相对保压比例 × 壁厚修正 × 浇口修正 × 流道修正
        # 推导链：保压是注射的延续 → 材料黏度等级 × 几何修正（壁厚/浇口） × 流道状态 → 安全钳制
        # 数据源：3 级兜底（精确值 / 大类查表 / 默认值）
        # 物理详见 _dev_refs/2026-07-05-holding-pressure-physics-design.md
        inj_pres_1st = proc.inj_pres_steps[0] if proc.inj_pres_steps else inj_pres
        gate_type = prod.get('gate_type', '其他')
        max_thickness = prod.get('max_thickness', 0)
        runner_type = prod.get('runner_type', '')
        runner_weight = prod.get('runner_weight', 0)

        family_hold_ratio, hold_level = self._get_family_hold_ratio(family, c_hold)
        bucket, bucket_level = self._get_thickness_bucket(max_thickness, c_inj)
        thickness_factor = c_hold.get(
            'thickness_factor', {'thin': 0.95, 'medium': 1.00, 'thick': 1.10}
        ).get(bucket, 1.00)
        gate_factor = self._get_gate_factor(gate_type, c_hold)
        runner_factor, runner_level = self._get_runner_factor(runner_type, runner_weight, c_hold)

        hold_pres_raw = inj_pres_1st * family_hold_ratio * thickness_factor * gate_factor * runner_factor
        hold_pres = min(
            max(
                inj_pres_1st * c_hold.get('hold_pres_inj_ratio_min', 0.40),
                min(hold_pres_raw, inj_pres_1st * c_hold.get('hold_pres_inj_ratio_max', 0.85)),
            ),  # 物理比例钳制（防凹陷下限 + 防飞边上限）
            max_hold_pres * c_hold.get('max_safe_hold_ratio', 0.95),  # 机器硬上限
        )

        logger.debug(
            f"保压压力: family={family or 'unknown'} (level={hold_level}), "
            f"family_hold_ratio={family_hold_ratio:.3f}, "
            f"bucket={bucket} (level={bucket_level}), thickness_factor={thickness_factor:.3f}, "
            f"gate_type={gate_type}, gate_factor={gate_factor:.3f}, "
            f"runner_type={runner_type or 'inferred'} (level={runner_level}), runner_factor={runner_factor:.3f}, "
            f"hold_pres_raw={hold_pres_raw:.2f}MPa → hold_pres={hold_pres:.2f}MPa"
        )

        # 【重构】保压速度 = 材料黏度等级 × 浇口尺寸修正 × 机器上限钳制
        # 推导链：剪切速率约束 γ̇ = v × (A_screw / A_gate) / h_gate → 防剪切降解上限
        # 数据源：3 级兜底（精确值 / family×bucket 查表 / 默认）+ 机器上限钳制（≤ 30% HMI 上限）
        # 与 #6 保压压力正交拆分：#6 是流变学驱动（ΔP = Q × R），本算法是运动学上限约束（v × A = Q ≤ Q_max）
        # 物理详见 _dev_refs/2026-07-05-holding-velocity-physics-design.md
        family_velo_ratio, velo_level = self._get_family_hold_velo_ratio(family, c_hold)
        gate_factor_velo = self._get_gate_factor_for_hold_velo(bucket, c_hold)

        hold_velo_raw = max_hold_velo * family_velo_ratio * gate_factor_velo
        hold_velo_cap = max_hold_velo * c_hold.get('max_safe_hold_velo_ratio', 0.30)
        hold_velo = min(hold_velo_raw, hold_velo_cap)

        logger.debug(
            f"保压速度: family={family or 'unknown'} (level={velo_level}), "
            f"family_velo_ratio={family_velo_ratio:.3f}, "
            f"bucket={bucket}, gate_factor_velo={gate_factor_velo:.3f}, "
            f"hold_velo_raw={hold_velo_raw:.2f}mm/s → cap {hold_velo_cap:.2f}mm/s → hold_velo={hold_velo:.2f}mm/s"
        )

        # 【重构】保压时间 = 浇口凝固时间 × 5 维修正因子（Fourier 热扩散 + 五维差异化）
        # 推导链：Fourier 热扩散 t ≈ h² / α_eff → family × thickness 基准 × 浇口修正 × 流道修正 × 模温修正 × 结晶拉长 → family 自适应上限钳制
        # 数据源：4 级兜底（精确值 / family×bucket / family 中桶兜底 / 默认）+ family 自适应上限（**移除 10s 硬上限**）
        # 物理详见 _dev_refs/2026-07-05-holding-time-physics-design.md
        freeze_t, freeze_level = self._get_family_gate_freeze_time(family, bucket, c_hold)
        gate_factor_hold = self._get_gate_factor_for_hold(gate_type, c_hold)
        runner_factor_hold, runner_level = self._get_runner_factor(runner_type, runner_weight, c_hold)
        mold_temp_factor, mold_temp_level = self._get_mold_temp_factor(mold_temp, c_hold)
        cryst_kick = self._get_crystallinity_kick(family, c_hold)

        hold_time_raw = (
            freeze_t * gate_factor_hold * runner_factor_hold * mold_temp_factor * cryst_kick
        )
        hold_time_min_t = c_hold.get('hold_time_min', 2.0)
        hold_time_max_t = self._get_family_hold_time_max(family, c_hold)
        hold_time = max(hold_time_min_t, min(hold_time_raw, hold_time_max_t))

        logger.debug(
            f"保压时间: family={family or 'unknown'}, bucket={bucket}, "
            f"t_gf={freeze_t:.2f}s (level={freeze_level}), "
            f"gate_factor={gate_factor_hold:.3f}, "
            f"runner_factor={runner_factor_hold:.3f} (level={runner_level}), "
            f"mold_temp_factor={mold_temp_factor:.3f} (level={mold_temp_level}), "
            f"cryst_kick={cryst_kick:.3f}, "
            f"hold_time_raw={hold_time_raw:.2f}s → clamp to [{hold_time_min_t}, {hold_time_max_t}]s = {hold_time:.2f}s"
        )

        proc.hold_stg = 1
        proc.hold_pres_steps = [hold_pres]
        proc.hold_spd_steps = [hold_velo]
        proc.hold_time_steps = [hold_time]
        proc.hold_limit_spd = HSO_PACK_VELOCITY

        # ========== 冷却参数（v1.0：4 维物理化）==========
        # 推导公式：t_cool = max_thickness² × family_cool_factor × ΔT_factor × crystallinity_kick
        # 物理依据：Fourier 热扩散 t ∝ h²/α × ln((T_melt-T_mold)/(T_eject-T_mold))
        # 物理正交：与 #8 保压时间正交（保压时间=浇口凝固局部，冷却时间=制品整体冷到 ejection_temp）
        # 详见 _dev_refs/2026-07-05-cool-time-physics-design.md

        # Step 1: 基础冷却时间（材料系数 × 壁厚²）
        family_cool_factor_map = c_cool.get('family_cool_factor', {})
        default_cool_factor = c_cool.get('default_cool_factor', 1.2)
        family_factor = family_cool_factor_map.get(family, default_cool_factor)
        max_thickness_cool = prod.get('max_thickness', 2.0)
        t_cool_raw = (max_thickness_cool ** 2) * family_factor

        # Step 2: 模温修正（温差比 → ΔT_factor 5 档，缺失数据兜底 1.0）
        t_mold_cool = mat.get('recommended_mold_temp', 0) or 0
        t_melt_cool = mat.get('recommended_melt_temp', 0) or 0
        t_eject_cool = mat.get('ejection_temp', 0) or 0
        delta_factor, delta_level = self._get_delta_temp_factor(
            t_mold_cool, t_melt_cool, t_eject_cool
        )
        t_cool_mold = t_cool_raw * delta_factor

        # Step 3: 结晶拉长（半结晶释放潜热，无定形不拉长）
        crystallinity_kick, crystallinity_level = self._get_cool_crystallinity_kick(
            mat, c_cool
        )
        t_cool_phys = t_cool_mold * crystallinity_kick

        # Step 4: 用户强制覆盖（总周期倒推冷却时间）
        t_cool_user = None
        if prod.get('inject_cycle_require'):
            else_time = c_cool.get('else_time', 1.5)
            t_cool_user = prod['inject_cycle_require'] - inj_time - hold_time - else_time

        # Step 5: 钳制下限（开模+顶出机械动作最小耗时）
        t_cool_final = t_cool_user if t_cool_user is not None else t_cool_phys
        proc.cool_t = max(c_cool.get('cool_time_min', 5.0), t_cool_final)

        logger.debug(
            f"冷却时间: family={family or 'unknown'} (factor={family_factor:.2f}), "
            f"h_max={max_thickness_cool:.2f}mm, "
            f"ΔT_factor={delta_factor:.2f} (level={delta_level}), "
            f"cryst_kick={crystallinity_kick:.2f} (level={crystallinity_level}), "
            f"t_cool_raw={t_cool_raw:.2f}s → t_cool_phys={t_cool_phys:.2f}s, "
            f"user_override={t_cool_user if t_cool_user is None else f'{t_cool_user:.2f}s'}, "
            f"final={proc.cool_t:.2f}s"
        )

        # ========== 计量参数 ==========
        # v1.0 物理化：3 维公式 + 全电机分支
        # - 液压机：max × base_ratio × family_factor × nozzle_factor，再钳制 [min, max]
        # - 全电机：无油缸 → meter_pres = 0（HMI 不显示“计量压力”输入栏）
        # 注意：传原始 abbreviation（如 PA66/PVC），内部会先精确匹配再 fallback 到 family
        abbreviation = mat.get('abbreviation', '')
        meter_pres = self._compute_meter_pres(mach, abbreviation, c_met)
        logger.debug(
            f"[meter_pres] power={mach.get('power_method', '液压机')}, "
            f"nozzle={mach.get('nozzle_type', '直通型')}, "
            f"abbreviation={abbreviation}, "
            f"max={mach.get('max_set_metering_pressure', 20)}, "
            f"final={meter_pres}"
        )

        max_screw_speed = mach.get('max_set_screw_rotation_speed', 150)
        # v1.0 物理化：family 修正（必须） + L/D 修正（条件性启用）
        # 不分支动力源（全电机/液压机走同一公式）
        # 60 = s→min 单位换算因子（v_surface × 60 / (π × D) = rpm）
        meter_speed = self._compute_meter_speed(mach, mat, abbreviation, c_met)
        logger.debug(
            f"[meter_speed] abbreviation={abbreviation}, "
            f"max_screw_speed={max_screw_speed}, "
            f"screw_diameter={mach.get('screw_diameter', 40)}, "
            f"recommend_shear={mat.get('recommend_shear_linear_speed', 160)}, "
            f"final={meter_speed}"
        )

        meter_back_pres = self._compute_meter_back_pres(
            mach, mat, abbreviation, meter_speed, c_back,
        )
        logger.debug(
            f"[meter_back_pres] abbreviation={abbreviation}, "
            f"recommend_back={mat.get('recommend_back_pressure') or 10.0}, "
            f"meter_speed={meter_speed}, "
            f"final={meter_back_pres}"
        )
        # ========== 算法 #14：计量位置 (meter_posi) ==========
        # v1.0 推导公式（物理意义清晰，无需算法化）
        #
        # 物理含义：螺杆储料回退到位时的目标位置（距离机械零点＝马达侧零点的距离）
        #   meter_posi = cushion_len + total_len
        #       - cushion_len：保压完成后螺杆前端与熔体末端的距离（#2 料垫长度算法，防欠注/补缩）
        #       - total_len：从机械最大前进位置到最大后退位置的总行程（#1 收缩长度算法）
        #
        # 物理正确性：偏移量叠加，机器坐标系下螺杆终点 = 起点偏移 + 总行程，任何动力源（液压/全电机）均成立
        # 与 4.10 节“已基于物理含义推导，只需在料垫算法实施时同步更新”一致——#2 算法实施后本行无需变动
        meter_posi = cushion_len + total_len
        logger.debug(
            f"[meter_posi] cushion_len={cushion_len}, "
            f"total_len={total_len}, "
            f"final={meter_posi}"
        )

        proc.met_stg = 1
        proc.met_lim_t = HSO_METER_START_DELAY_TIME
        proc.met_pres_steps = [meter_pres]
        proc.met_rot_spd_steps = [meter_speed]
        proc.met_back_pres_steps = [meter_back_pres]
        proc.met_pos_steps = [meter_posi]

        # ========== 松退参数（#15-#18，v1.1：5 维物理化推导）==========
        # 设计依据：2026-07-05-suckback-decompression-physics-design.md
        # 推导链：
        #   #15 模式决策（3 级兑底：用户输入 → DEFAULT 规则 → 默认）
        #   #16+#17 参数推导（液压机/全电机分支）
        #   #18 met_end_pos = meter_posi + pst_dist
        c_suck = self._coeffs.get('suckback', {})
        if not c_suck:
            # fallback 到旧 decompression 块（向后兼容）
            c_suck = self._coeffs.get('decompression', {})

        power_method = mach.get('power_method', '液压机')
        nozzle_type = mach.get('nozzle_type', '直通型')
        abbreviation = mat.get('abbreviation', '')

        # 读取制品上下文
        runner_type = prod.get('runner_type', '')
        runner_weight = prod.get('runner_weight', 0)
        gate_type = prod.get('gate_type', '侧浇口')

        # ========== #15：松退模式决策（3 级兑底）==========
        # 前松退默认关（0 = 否 / 1 = 距离 / 2 = 时间）
        pre_mode = prod.get(
            'pre_met_decomp_mode',
            c_suck.get('pre_decomp_default_mode', 0),
        )
        # 后松退默认距离模式（活跃使用）
        pst_mode = prod.get(
            'pst_met_decomp_mode',
            c_suck.get('pst_decomp_default_mode', 1),
        )

        # ========== #17：后松退参数推导（活跃使用，5 维物理化）==========
        # 1. 距离：5 维物理化（base × family × nozzle × runner × gate）
        pst_dist, dist_info = self._compute_suckback_distance(
            abbreviation, nozzle_type, runner_type, runner_weight, gate_type, c_suck,
        )
        # 2. 压力：液压机分支（仅后松退需推导，前松退默认关时不强求）
        pst_pres, pres_info = self._compute_suckback_pressure(
            mach, abbreviation, nozzle_type, 'post', c_suck,
        )
        # 3. 速度：3 维物理化（机器能力 × family × nozzle）
        pst_velo, velo_info = self._compute_suckback_velocity(
            abbreviation, nozzle_type, power_method, c_suck, mach,
        )
        # 4. 时间：派生（distance / velo）
        pst_time, time_info = self._compute_suckback_time(pst_dist, pst_velo, c_suck)

        proc.pre_met_decomp_mode = pre_mode
        proc.pre_met_decomp_pres = 0.0      # 前松退默认关，不推导压力
        proc.pre_met_decomp_spd = 0.0
        proc.pre_met_decomp_t = 0.0
        proc.pre_met_decomp_dist = 0.0

        proc.pst_met_decomp_mode = pst_mode
        proc.pst_met_decomp_pres = round(pst_pres, 2)
        proc.pst_met_decomp_spd = round(pst_velo, 2)
        proc.pst_met_decomp_t = round(pst_time, 2)
        proc.pst_met_decomp_dist = round(pst_dist, 2)

        # ========== #18：计量终止位置 ==========
        # met_end_pos = meter_posi + pst_dist（公式透明，与 #14 同类）
        # 仅后松退距离进入位置计算，前松退净位移=0（方案C）不影响 met_end_pos
        proc.met_end_pos = round(meter_posi + pst_dist, 2)

        logger.debug(
            f"[suckback:post] power_method={power_method}, "
            f"abbreviation={abbreviation}, nozzle={nozzle_type}, "
            f"runner={runner_type}/{runner_weight}g, gate={gate_type}, "
            f"family_dist={dist_info['family_dist_factor']:.2f}({dist_info['family_dist_level']}), "
            f"nozzle_factor={dist_info['nozzle_dist_factor']:.2f}, "
            f"runner={dist_info['runner_factor']:.2f}({dist_info['runner_level']}), "
            f"gate={dist_info['gate_factor']:.2f}({dist_info['gate_applied']}), "
            f"D_raw={dist_info['D_raw']:.2f}mm, D={pst_dist:.2f}mm, "
            f"P={pst_pres:.2f}MPa, V={pst_velo:.2f}mm/s, T={pst_time:.2f}s"
        )
        logger.debug(
            f"[met_end_pos] meter_posi={meter_posi:.2f}, pst_dist={pst_dist:.2f}, "
            f"final={proc.met_end_pos:.2f}mm"
        )

        # ========== #19+#20 温度族参数 ==========
        # #19 喷嘴温度（2 维物理化：nozzle_offset + family_offset）
        nozzle_type = mach.get('nozzle_type', '直通型')
        recommend_melt_temp = mat.get('recommended_melt_temp', 250)
        min_melt_temp = mat.get('min_melt_temp')
        max_melt_temp = mat.get('max_melt_temp')
        glass_transition_temp = mat.get('glass_transition_temp')

        # 取 _parse_family（与 #11 #13 #15-#18 一致）
        abbreviation = mat.get('abbreviation', '')
        family = self._parse_family(abbreviation) if abbreviation else ''

        noz_temp, noz_info = self._compute_noz_temp(
            recommend_melt_temp=recommend_melt_temp,
            nozzle_type=nozzle_type,
            family=family,
            c_noz=c_noz,
            min_melt_temp=min_melt_temp,
            max_melt_temp=max_melt_temp,
        )
        proc.noz_temp = round(noz_temp, 1)

        # #20 料筒温度分布（4 维物理化：family_decrement × stages × 幂函数k × 双层边界钳制）
        proc.brl_temp_stg = prod.get('barrel_temperature_stage', 5)
        brl_temp_steps, brl_info = self._compute_brl_temp_steps(
            recommend_melt_temp=recommend_melt_temp,
            stages=proc.brl_temp_stg,
            family=family,
            c_brl=c_brl,
            glass_transition_temp=glass_transition_temp,
        )
        proc.brl_temp_steps = [round(t, 1) for t in brl_temp_steps]

        logger.debug(
            f"[nozzle:19] family={family}, nozzle={nozzle_type}, "
            f"noz_offset={noz_info['noz_offset']:.2f}, "
            f"family_offset={noz_info['family_offset']:.2f}({noz_info['family_offset_level']}), "
            f"raw={noz_info['noz_temp_raw']:.2f}, "
            f"final={proc.noz_temp:.2f}°C"
            f"{' (clamped)' if noz_info['clamped'] else ''}"
        )
        logger.debug(
            f"[barrel:20] family={family}, stages={brl_info['stages']}, "
            f"decrement={brl_info['family_decrement']:.2f}({brl_info['family_decrement_level']}), "
            f"effective={brl_info['effective_decrement']:.2f}, "
            f"k={brl_info['power_k']:.2f}, "
            f"steps={proc.brl_temp_steps}"
        )

    # ========== 模温机工艺参数 ==========

    def _derive_mold_temp(self, params: ProductionParams):
        """推导模温机工艺参数 - 来自 MOLD_TEMP_DEFAULTS 规则"""
        mat = self.material

        recommend_mold_temp = mat.get('recommended_mold_temp', 0)
        if recommend_mold_temp != 0:
            params.mold_temp.mold_temp = recommend_mold_temp
            return

        mold_temp_map = self._coeffs.get('mold_temp', {})
        poly_abbr = mat.get('abbreviation', 'ABS')
        params.mold_temp.mold_temp = mold_temp_map.get(
            poly_abbr,
            mold_temp_map.get('default', 50),
        )

    # ========== 热流道工艺参数 ==========

    def _derive_hot_runner(self, params: ProductionParams):
        """推导热流道工艺参数"""
        prod = self.mold

        valve_num = prod.get('valve_num', 0)
        params.hot_runner.valve_num = valve_num
        if valve_num:
            params.hot_runner.valve_time_steps = list(range(1, int(valve_num) + 1))

    # ========== 保压时间（按浇口类型分支） ==========

    def _calc_hold_time(self, prod: Dict[str, Any]) -> float:
        """计算保压时间（按浇口类型）

        公式策略与系数来自 GATE_* 规则：
        - GATE_DIRECT: linear  -> 0.5 + 0.1 * avg_thickness
        - GATE_SIDE:   gate_area -> 2 * gate_area
        - GATE_OTHER:  quadratic -> 0.3 + 0.6 * avg_thickness^2

        由于侧浇口需要计算 gate_area 几何（圆/矩形），
        分支策略仍在 Python 中实现，公式系数从规则读取。
        """
        gate_type = prod.get('gate_type', '直浇口')
        avg_thickness = prod.get('ave_thickness', 2)

        c_hold = self._coeffs.get('holding', {})
        time_min = c_hold.get('hold_time_min', 2.0)
        time_max = c_hold.get('hold_time_max', 10.0)

        if gate_type in ("直浇口", "护耳式浇口", "点浇口"):
            a = c_hold.get('hold_time_linear_a', 0.5)
            b = c_hold.get('hold_time_linear_b', 0.1)
            hold_time = a + b * avg_thickness
        elif gate_type == "侧浇口":
            gate_radius = prod.get('gate_radius')
            gate_length = prod.get('gate_length')
            gate_width = prod.get('gate_width')
            if gate_radius:
                gate_area = HSO_PI * (gate_radius ** 2)
            elif gate_length and gate_width:
                gate_area = gate_length * gate_width
            else:
                return time_min
            area_coef = c_hold.get('hold_time_area_coef', 2.0)
            hold_time = area_coef * gate_area
        else:
            a = c_hold.get('hold_time_quadratic_a', 0.3)
            b = c_hold.get('hold_time_quadratic_b', 0.6)
            hold_time = a + b * (avg_thickness ** 2)

        return max(time_min, min(hold_time, time_max))

    # ========== 多级参数 ==========

    def _apply_multi_stage(self, params: ProductionParams):
        """
        应用多级参数

        根据注射行程自动推荐段数，并应用多级系数：
        - 注射段数：根据注射行程（>=40mm→4段, 20-40mm→3段, 10-20mm→2段, <10mm→1段）
        - 保压段数：默认2段
        - 计量段数：默认1段

        段数/模式优先使用 process_set 中的值（如 inj_stg / hold_stg / met_stg），
        未指定时按行程自动推荐。
        """
        prod = self.mold
        ps = self.process_set
        mat = self.material
        proc = params.process

        # 计算注射行程
        total_weight = prod['product_weight']
        runner_weight = prod.get('runner_weight', 0)
        melt_density = mat.get('melt_density', 0.95)
        screw_diameter = self.machine.get('screw_diameter', 35)
        total_len = self._compute_total_len(total_weight, melt_density, screw_diameter)

        # ========== 1. 确定注射段数 ==========
        if total_len >= 40:
            inj_stg = 4
        elif total_len > 20:
            inj_stg = 3
        elif total_len > 10:
            inj_stg = 2
        else:
            inj_stg = 1

        if ps.get('inj_stg'):
            inj_stg = ps['inj_stg']

        proc.inj_stg = inj_stg

        # ========== 2. 确定保压段数 ==========
        prod_hold_stg = ps.get('hold_stg', 2)
        proc.hold_stg = prod_hold_stg

        # ========== 3. 确定计量段数 ==========
        prod_met_stg = ps.get('met_stg', 1)
        proc.met_stg = prod_met_stg

        # ========== 4. 多级注射 ==========
        if inj_stg > 1:
            self._apply_multi_injection(proc, inj_stg, runner_weight, total_len)

        # ========== 5. 多级保压 ==========
        if prod_hold_stg > 1:
            self._apply_multi_holding(proc, prod_hold_stg)

        # ========== 6. 多级计量 ==========
        if prod_met_stg > 1:
            self._apply_multi_metering(proc, prod_met_stg, total_len)

    def _apply_multi_injection(
        self,
        proc: ProcessParams,
        inj_stg: int,
        runner_weight: float,
        total_len: float
    ):
        """应用多级注射参数"""
        mat = self.material

        inj_pres = proc.inj_pres_steps[0] if proc.inj_pres_steps else 0
        inj_velo = proc.inj_spd_steps[0] if proc.inj_spd_steps else 0
        vp_pos = proc.vps_pos
        meter_end_pos = proc.met_end_pos
        decomp_dist = proc.pst_met_decomp_dist

        is_hot_runner = runner_weight <= 0.01
        is_abs = mat.get('abbreviation') == 'ABS'

        if is_abs:
            coef_map = _MULTI_INJ_ABS_HOT if is_hot_runner else _MULTI_INJ_ABS_COLD
        else:
            coef_map = _MULTI_INJ_GENERIC_HOT if is_hot_runner else _MULTI_INJ_GENERIC_COLD

        if inj_stg not in coef_map:
            inj_stg = max(k for k in coef_map.keys() if k <= inj_stg)

        coefs = coef_map[inj_stg]
        pres_coefs = coefs[0]
        velo_coefs = coefs[1]
        pos_coefs = coefs[2]

        proc.inj_pres_steps = [pres_coefs[i] * inj_pres for i in range(inj_stg)]
        proc.inj_spd_steps = [velo_coefs[i] * inj_velo for i in range(inj_stg)]

        if is_hot_runner:
            proc.inj_pos_steps = [
                vp_pos + pos_coefs[i] * (total_len + decomp_dist)
                for i in range(inj_stg)
            ]
        else:
            product_weight = self.mold['product_weight'] - runner_weight
            total_weight = self.mold['product_weight']
            part_percent = product_weight / total_weight
            runner_percent = runner_weight / total_weight

            proc.inj_pos_steps = self._calc_multi_inj_pos_cold(
                inj_stg, meter_end_pos, vp_pos, total_len,
                runner_percent, part_percent
            )

    def _calc_multi_inj_pos_cold(
        self,
        inj_stg: int,
        meter_end_pos: float,
        vp_pos: float,
        total_len: float,
        runner_percent: float,
        part_percent: float
    ) -> list:
        """计算冷流道多级注射位置"""
        positions = []

        if inj_stg == 2:
            inj_posi_1 = meter_end_pos - 1.05 * runner_percent * total_len
            inj_posi_2 = vp_pos
            positions = [inj_posi_1, inj_posi_2]
        elif inj_stg == 3:
            inj_posi_1 = meter_end_pos - 1.05 * runner_percent * total_len
            inj_posi_2 = vp_pos + 0.09 * total_len
            inj_posi_3 = vp_pos
            positions = [inj_posi_1, inj_posi_2, inj_posi_3]
        elif inj_stg == 4:
            inj_posi_1 = meter_end_pos - 0.98 * runner_percent * total_len
            inj_posi_2 = meter_end_pos - (runner_percent + 0.05 * part_percent) * total_len
            inj_posi_3 = vp_pos + 0.09 * total_len
            inj_posi_4 = vp_pos
            positions = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4]
        elif inj_stg == 5:
            inj_posi_1 = meter_end_pos - 0.98 * runner_percent * total_len
            inj_posi_2 = meter_end_pos - (runner_percent + 0.05 * part_percent) * total_len
            inj_posi_3 = meter_end_pos - (runner_percent + 0.5 * part_percent) * total_len
            inj_posi_4 = vp_pos + 0.09 * total_len
            inj_posi_5 = vp_pos
            positions = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4, inj_posi_5]
        elif inj_stg >= 6:
            inj_posi_1 = meter_end_pos - 0.98 * runner_percent * total_len
            inj_posi_2 = meter_end_pos - (runner_percent + 0.05 * part_percent) * total_len
            inj_posi_3 = meter_end_pos - (runner_percent + 0.4 * part_percent) * total_len
            inj_posi_4 = meter_end_pos - (runner_percent + 0.7 * part_percent) * total_len
            inj_posi_5 = vp_pos + 0.09 * total_len
            inj_posi_6 = vp_pos
            positions = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4, inj_posi_5, inj_posi_6]
        else:
            positions = [vp_pos]

        return positions

    def _apply_multi_holding(self, proc: ProcessParams, hold_stg: int):
        """应用多级保压参数"""
        hold_pres = proc.hold_pres_steps[0] if proc.hold_pres_steps else 0
        hold_velo = proc.hold_spd_steps[0] if proc.hold_spd_steps else 0
        hold_time = proc.hold_time_steps[0] if proc.hold_time_steps else 0

        if hold_stg not in _MULTI_HOLD_COEF_MAP:
            hold_stg = max(k for k in _MULTI_HOLD_COEF_MAP.keys() if k <= hold_stg)

        coefs = _MULTI_HOLD_COEF_MAP[hold_stg]

        proc.hold_pres_steps = [coefs[0][i] * hold_pres for i in range(hold_stg)]
        proc.hold_spd_steps = [coefs[1][i] * hold_velo for i in range(hold_stg)]
        proc.hold_time_steps = [coefs[2][i] * hold_time for i in range(hold_stg)]

    def _apply_multi_metering(self, proc: ProcessParams, met_stg: int, total_len: float):
        """应用多级计量参数"""
        meter_pres = proc.met_pres_steps[0] if proc.met_pres_steps else 0
        meter_speed = proc.met_rot_spd_steps[0] if proc.met_rot_spd_steps else 0
        meter_back_pres = proc.met_back_pres_steps[0] if proc.met_back_pres_steps else 0

        if met_stg not in _MULTI_METER_COEF_MAP:
            met_stg = max(k for k in _MULTI_METER_COEF_MAP.keys() if k <= met_stg)

        coefs = _MULTI_METER_COEF_MAP[met_stg]
        vp_pos = proc.vps_pos  # 计量起点 = VP 切换位置（与 cushion_len 区分）

        proc.met_pres_steps = [coefs[0][i] * meter_pres for i in range(met_stg)]
        proc.met_rot_spd_steps = [coefs[1][i] * meter_speed for i in range(met_stg)]
        proc.met_back_pres_steps = [coefs[2][i] * meter_back_pres for i in range(met_stg)]
        proc.met_pos_steps = [vp_pos + coefs[3][i] * total_len for i in range(met_stg)]

    # ========== 格式化输出 ==========

    def _format_output(self, params: ProductionParams):
        """格式化输出"""
        proc = params.process

        proc.inj_pres_steps = [round(v, 0) for v in proc.inj_pres_steps]
        proc.inj_spd_steps = [round(v, 0) for v in proc.inj_spd_steps]
        proc.inj_pos_steps = [round(v, 2) for v in proc.inj_pos_steps]
        proc.inj_t = round(proc.inj_t, 2)
        proc.inj_dly_t = round(proc.inj_dly_t, 2)

        proc.vps_pos = round(proc.vps_pos, 2)
        proc.vps_t = round(proc.vps_t, 2)

        proc.hold_pres_steps = [round(v, 0) for v in proc.hold_pres_steps]
        proc.hold_spd_steps = [round(v, 0) for v in proc.hold_spd_steps]
        proc.hold_time_steps = [round(v, 2) for v in proc.hold_time_steps]

        proc.cool_t = round(proc.cool_t, 2)

        proc.pst_met_decomp_dist = round(proc.pst_met_decomp_dist, 2)
        proc.met_end_pos = round(proc.met_end_pos, 2)

        proc.noz_temp = round(proc.noz_temp, 0)
        proc.brl_temp_steps = [round(t, 0) for t in proc.brl_temp_steps]