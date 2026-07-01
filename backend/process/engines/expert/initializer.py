"""
工艺参数初始化器

基于机器、材料、产品信息推理初始工艺参数。

系数来源：
    1. InitRuleMatcher（数据库 ExpertRule）
    2. InitRuleLoader（JSON 文件，本地/无 DB）
    3. InitRuleMatcher 内置默认值（兜底）

Usage:
    initializer = ProcessInitializer(machine_info, polymer_info)
    params = initializer.derive(product_info)  # 返回 ProductionParams
"""

import logging
from typing import Dict, Any, Optional

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
        machine_info: Dict[str, Any],
        polymer_info: Dict[str, Any],
        rule_matcher: Optional[InitRuleMatcher] = None,
    ):
        if not machine_info:
            raise ValueError("机器信息不能为空")
        if not polymer_info:
            raise ValueError("材料信息不能为空")

        self.machine = machine_info
        self.material = polymer_info
        self.product: Optional[Dict[str, Any]] = None
        self.rule_matcher = rule_matcher or InitRuleMatcher()
        # 当前上下文匹配后的合并系数（derive 时填充）
        self._coeffs: Dict[str, Any] = {}

    def derive(self, product_info: Dict[str, Any]) -> ProductionParams:
        """
        推导初始工艺参数

        包含注塑机、模温机、热流道的完整工艺参数。
        """
        self.product = product_info
        self._validate_inputs()
        # 关键：先加载规则系数，再进入派生流程
        self._coeffs = self.rule_matcher.match({
            'polymer': self.material,
            'product': self.product,
            'machine': self.machine,
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
            'recommend_melt_temperature': 250,
            'recommend_shear_linear_speed': 160,
            'recommend_back_pressure': 15,
            'recommend_mold_temperature': 0,
            'melt_density': 0.95,
        }
        for key, default in material_defaults.items():
            if not self.material.get(key):
                self.material[key] = default

        required_product_fields = ['product_weight', 'gate_type', 'ave_thickness', 'max_thickness']
        for field in required_product_fields:
            if not self.product.get(field):
                raise ValueError(f"产品信息缺少必要字段: {field}")
        # runner_weight 允许为 0（表示热流道）

    # ========== 系数读取辅助 ==========

    def _get(self, group: str, key: str, default: Any = None) -> Any:
        """从合并系数中安全读取指定键值"""
        return self._coeffs.get(group, {}).get(key, default)

    # ========== 注塑机工艺参数（主体） ==========

    def _derive_process(self, params: ProductionParams):
        """
        推导注塑机工艺参数（主体）

        包含：注射、VP切换、保压、冷却、计量、松退、温度
        """
        prod = self.product
        mach = self.machine
        mat = self.material
        proc = params.process

        # 提取分组系数（避免每处重复 .get）
        c_inj = self._coeffs.get('injection', {})
        c_vps = self._coeffs.get('vp_switch', {})
        c_hold = self._coeffs.get('holding', {})
        c_cool = self._coeffs.get('cooling', {})
        c_met = self._coeffs.get('metering', {})
        c_decomp = self._coeffs.get('decompression', {})
        c_temp = self._coeffs.get('temperature', {})

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
        injection_volume = total_weight / melt_density
        injection_length = injection_volume * 1000.0 / (HSO_PI * (screw_diameter ** 2) / 4)
        length_ratio = 0.85 if total_weight <= 50 else (0.90 if total_weight <= 100 else 0.95)
        inj_len = injection_length * length_ratio

        # ========== 注射参数 ==========
        max_inj_pres = mach.get('max_set_injection_pressure', 150)
        max_inj_velo = mach.get('max_set_injection_velocity', 100)

        # 注射压力 - 来自 DEFAULT.injection.inj_pres_ratio
        inj_pres = max_inj_pres * c_inj.get('inj_pres_ratio', 0.65)

        # 注射速度 - 按 MATERIAL_* 规则覆盖，固定回退到 MATERIAL_OTHER
        poly_type = mat.get('abbreviation', 'ABS')
        inj_ratio_threshold = c_inj.get('inj_ratio_threshold', 100)
        if poly_type in self._GENERAL_MATERIALS:
            inj_velo = self._calc_inj_velo(
                max_inj_velo, inj_ratio, inj_ratio_threshold,
                thin=c_inj.get('inj_velo_ratio_thin', 0.30),
                thick=c_inj.get('inj_velo_ratio_thick', 0.40),
                coef=c_inj.get('inj_ratio_coef', 500.0),
            )
        elif poly_type == "PC+ABS":
            inj_velo = self._calc_inj_velo(
                max_inj_velo, inj_ratio, inj_ratio_threshold,
                thin=c_inj.get('inj_velo_ratio_thin', 0.215),
                thick=c_inj.get('inj_velo_ratio_thick', 0.34),
                coef=c_inj.get('inj_ratio_coef', 800.0),
            )
        else:
            inj_velo = self._calc_inj_velo(
                max_inj_velo, inj_ratio, inj_ratio_threshold,
                thin=c_inj.get('inj_velo_ratio_thin', 0.35),
                thick=c_inj.get('inj_velo_ratio_thick', 0.42),
                coef=c_inj.get('inj_ratio_coef', 500.0),
            )

        # 注射时间 - 来自 DEFAULT.injection.inj_time_coef / inj_time_min
        inj_time = max(
            c_inj.get('inj_time_min', 3.0),
            c_inj.get('inj_time_coef', 4.0) * inj_len / inj_velo,
        )

        proc.inj_stg = 1
        proc.inj_spd_steps = [inj_velo]
        proc.inj_pres_steps = [inj_pres]
        proc.inj_pos_steps = [0]
        proc.inj_t = inj_time
        proc.inj_dly_t = HSO_INJ_START_DELAY_TIME

        # ========== VP切换参数 ==========
        # vps_mode 优先使用 product_info['vps_mode'] (int)，否则从字符串派生
        vps_mode_int = prod.get('vps_mode')
        if isinstance(vps_mode_int, int) and 0 <= vps_mode_int <= 2:
            proc.vps_mode = vps_mode_int
        else:
            vp_mode = prod.get('VP_switch_mode', '位置')
            proc.vps_mode = 0 if vp_mode == "位置" else (1 if vp_mode == "时间" else 2)

        weight_threshold = c_vps.get('base_posi_threshold_weight', 120)
        base_posi = (
            c_vps.get('base_posi_small', 10)
            if product_weight < weight_threshold
            else c_vps.get('base_posi_large', 15)
        )

        proc.vps_pos = base_posi + (1 - length_ratio) * injection_length
        proc.vps_t = 0
        proc.vps_pres = 0
        proc.vps_spd = 0

        # 更新注射位置为VP切换位置
        proc.inj_pos_steps = [proc.vps_pos]

        # ========== 保压参数 ==========
        max_hold_pres = mach.get('max_set_holding_pressure', 100)
        max_hold_velo = mach.get('max_set_holding_velocity', 100)

        # 保压压力 - 来自 DEFAULT.holding.{base_ratio/thickness_factor/max_limit/inj_ratio}
        hold_pres = (
            c_hold.get('hold_pres_base_ratio', 0.25) * max_hold_pres
            + c_hold.get('hold_pres_thickness_factor', 10) * avg_thickness
        )
        if hold_pres >= c_hold.get('hold_pres_max_limit', 120):
            hold_pres = c_hold.get('hold_pres_inj_ratio', 0.65) * inj_pres

        # 保压速度 - 来自 DEFAULT.holding.hold_velo_ratio
        hold_velo = max_hold_velo * c_hold.get('hold_velo_ratio', 0.15)

        # 保压时间 - 按浇口类型（GATE_* 规则覆盖系数）
        hold_time = self._calc_hold_time(prod)

        proc.hold_stg = 1
        proc.hold_pres_steps = [hold_pres]
        proc.hold_spd_steps = [hold_velo]
        proc.hold_time_steps = [hold_time]
        proc.hold_limit_spd = HSO_PACK_VELOCITY

        # ========== 冷却参数 ==========
        weight_threshold_cool = c_cool.get('weight_factor_threshold', 100)
        k_weight = (
            1 if product_weight < weight_threshold_cool
            else (product_weight / 100) ** 0.5
        )
        cool_time = c_cool.get('cool_time_factor', 5.0) * prod.get('max_thickness', 2) * k_weight

        if prod.get('inject_cycle_require'):
            else_time = c_cool.get('else_time', 1.5)
            cool_time = int(prod['inject_cycle_require'] - inj_time - hold_time - else_time)

        proc.cool_t = max(c_cool.get('cool_time_min', 5.0), cool_time)

        # ========== 计量参数 ==========
        meter_pres = 0
        if mach.get('power_method') == '液压机':
            nozzle_type = mach.get('nozzle_type', '直通型')
            max_metering_pres = mach.get('max_set_metering_pressure', 20)
            # 来自 DEFAULT.metering.{meter_pres_ratio_straight/locking}
            if nozzle_type == "直通型":
                meter_pres = max_metering_pres * c_met.get('meter_pres_ratio_straight', 0.55)
            else:
                meter_pres = max_metering_pres * c_met.get('meter_pres_ratio_locking', 0.6)

        max_screw_speed = mach.get('max_set_screw_rotation_speed', 150)
        recommend_shear_speed = mat.get('recommend_shear_linear_speed', 160)
        # temp_ratio 上下限与系数来自 DEFAULT.metering
        screw_speed_factor = c_met.get('screw_speed_factor', 60.0)
        temp_ratio = max(
            c_met.get('meter_speed_temp_ratio_min', 0.3),
            min(
                c_met.get('meter_speed_temp_ratio_max', 0.75),
                screw_speed_factor * recommend_shear_speed / (screw_diameter * HSO_PI) / max_screw_speed,
            ),
        )
        meter_speed = temp_ratio * max_screw_speed

        meter_back_pres = mat.get('recommend_back_pressure', 15)
        meter_posi = base_posi + injection_length

        proc.met_stg = 1
        proc.met_lim_t = HSO_METER_START_DELAY_TIME
        proc.met_pres_steps = [meter_pres]
        proc.met_rot_spd_steps = [meter_speed]
        proc.met_back_pres_steps = [meter_back_pres]
        proc.met_pos_steps = [meter_posi]

        # ========== 松退参数 ==========
        # decomp_modes 优先使用 product_info 中的 int 覆盖
        # 来自 DEFAULT.decompression.{pre_decomp_mode, pst_decomp_mode} 或调用方覆盖
        proc.pre_met_decomp_mode = prod.get(
            'pre_met_decomp_mode',
            c_decomp.get('pre_decomp_mode', 0),
        )
        proc.pre_met_decomp_spd = HSO_SUCKBACK_VELO_BEFORE_METER
        proc.pre_met_decomp_dist = HSO_SUCKBACK_DIS_BEFORE_METER

        proc.pst_met_decomp_mode = prod.get(
            'pst_met_decomp_mode',
            c_decomp.get('pst_decomp_mode', 0),
        )
        proc.pst_met_decomp_spd = HSO_SUCKBACK_VELO_AFTER_METER
        decomp_dist = max(
            c_decomp.get('decomp_dist_min', 2.0),
            min(c_decomp.get('decomp_dist_ratio', 0.1) * injection_length,
                c_decomp.get('decomp_dist_max', 10.0)),
        )
        proc.pst_met_decomp_dist = decomp_dist

        proc.met_end_pos = meter_posi + decomp_dist

        # ========== 温度参数 ==========
        # 喷嘴温度偏移：来自 DEFAULT.temperature.noz_temp_offset_{straight/locking}
        nozzle_type = mach.get('nozzle_type', '直通型')
        recommend_melt_temp = mat.get('recommend_melt_temperature', 250)
        if nozzle_type == "直通型":
            proc.noz_temp = recommend_melt_temp + c_temp.get('noz_temp_offset_straight', -5.0)
        else:
            proc.noz_temp = recommend_melt_temp + c_temp.get('noz_temp_offset_locking', 0.0)

        # 料筒温度递减：来自 DEFAULT.temperature.brl_temp_decrement_{normal/high} + stage_threshold
        proc.brl_temp_stg = prod.get('barrel_temperature_stage', 5)
        stage_threshold = c_temp.get('brl_temp_stage_threshold', 7)
        if proc.brl_temp_stg > stage_threshold:
            decrement = c_temp.get('brl_temp_decrement_high', 8.0)
        else:
            decrement = c_temp.get('brl_temp_decrement_normal', 10.0)
        proc.brl_temp_steps = [recommend_melt_temp - decrement * i for i in range(proc.brl_temp_stg)]

    @staticmethod
    def _calc_inj_velo(
        max_inj_velo: float,
        inj_ratio: float,
        threshold: float,
        thin: float,
        thick: float,
        coef: float,
    ) -> float:
        """注射速度计算（按流长比切换厚薄系数）"""
        if inj_ratio >= threshold:
            return max_inj_velo * thick
        return max_inj_velo * (thin + inj_ratio / coef)

    # ========== 模温机工艺参数 ==========

    def _derive_mold_temp(self, params: ProductionParams):
        """推导模温机工艺参数 - 来自 MOLD_TEMP_DEFAULTS 规则"""
        mat = self.material

        recommend_mold_temp = mat.get('recommend_mold_temperature', 0)
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
        prod = self.product

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
        """
        prod = self.product
        mat = self.material
        proc = params.process

        # 计算注射行程
        total_weight = prod['product_weight']
        runner_weight = prod.get('runner_weight', 0)
        melt_density = mat.get('melt_density', 0.95)
        screw_diameter = self.machine.get('screw_diameter', 35)
        injection_volume = total_weight / melt_density
        injection_length = injection_volume * 1000.0 / (HSO_PI * (screw_diameter ** 2) / 4)

        # ========== 1. 确定注射段数 ==========
        if injection_length >= 40:
            inj_stg = 4
        elif injection_length > 20:
            inj_stg = 3
        elif injection_length > 10:
            inj_stg = 2
        else:
            inj_stg = 1

        if prod.get('inj_stg'):
            inj_stg = prod['inj_stg']

        proc.inj_stg = inj_stg

        # ========== 2. 确定保压段数 ==========
        prod_hold_stg = prod.get('hold_stg', 2)
        proc.hold_stg = prod_hold_stg

        # ========== 3. 确定计量段数 ==========
        prod_met_stg = prod.get('met_stg', 1)
        proc.met_stg = prod_met_stg

        # ========== 4. 多级注射 ==========
        if inj_stg > 1:
            self._apply_multi_injection(proc, inj_stg, runner_weight, injection_length)

        # ========== 5. 多级保压 ==========
        if prod_hold_stg > 1:
            self._apply_multi_holding(proc, prod_hold_stg)

        # ========== 6. 多级计量 ==========
        if prod_met_stg > 1:
            self._apply_multi_metering(proc, prod_met_stg, injection_length)

    def _apply_multi_injection(
        self,
        proc: ProcessParams,
        inj_stg: int,
        runner_weight: float,
        injection_length: float
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
                vp_pos + pos_coefs[i] * (injection_length + decomp_dist)
                for i in range(inj_stg)
            ]
        else:
            product_weight = self.product['product_weight'] - runner_weight
            total_weight = self.product['product_weight']
            part_percent = product_weight / total_weight
            runner_percent = runner_weight / total_weight

            proc.inj_pos_steps = self._calc_multi_inj_pos_cold(
                inj_stg, meter_end_pos, vp_pos, injection_length,
                runner_percent, part_percent
            )

    def _calc_multi_inj_pos_cold(
        self,
        inj_stg: int,
        meter_end_pos: float,
        vp_pos: float,
        injection_length: float,
        runner_percent: float,
        part_percent: float
    ) -> list:
        """计算冷流道多级注射位置"""
        positions = []

        if inj_stg == 2:
            inj_posi_1 = meter_end_pos - 1.05 * runner_percent * injection_length
            inj_posi_2 = vp_pos
            positions = [inj_posi_1, inj_posi_2]
        elif inj_stg == 3:
            inj_posi_1 = meter_end_pos - 1.05 * runner_percent * injection_length
            inj_posi_2 = vp_pos + 0.09 * injection_length
            inj_posi_3 = vp_pos
            positions = [inj_posi_1, inj_posi_2, inj_posi_3]
        elif inj_stg == 4:
            inj_posi_1 = meter_end_pos - 0.98 * runner_percent * injection_length
            inj_posi_2 = meter_end_pos - (runner_percent + 0.05 * part_percent) * injection_length
            inj_posi_3 = vp_pos + 0.09 * injection_length
            inj_posi_4 = vp_pos
            positions = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4]
        elif inj_stg == 5:
            inj_posi_1 = meter_end_pos - 0.98 * runner_percent * injection_length
            inj_posi_2 = meter_end_pos - (runner_percent + 0.05 * part_percent) * injection_length
            inj_posi_3 = meter_end_pos - (runner_percent + 0.5 * part_percent) * injection_length
            inj_posi_4 = vp_pos + 0.09 * injection_length
            inj_posi_5 = vp_pos
            positions = [inj_posi_1, inj_posi_2, inj_posi_3, inj_posi_4, inj_posi_5]
        elif inj_stg >= 6:
            inj_posi_1 = meter_end_pos - 0.98 * runner_percent * injection_length
            inj_posi_2 = meter_end_pos - (runner_percent + 0.05 * part_percent) * injection_length
            inj_posi_3 = meter_end_pos - (runner_percent + 0.4 * part_percent) * injection_length
            inj_posi_4 = meter_end_pos - (runner_percent + 0.7 * part_percent) * injection_length
            inj_posi_5 = vp_pos + 0.09 * injection_length
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

    def _apply_multi_metering(self, proc: ProcessParams, met_stg: int, injection_length: float):
        """应用多级计量参数"""
        meter_pres = proc.met_pres_steps[0] if proc.met_pres_steps else 0
        meter_speed = proc.met_rot_spd_steps[0] if proc.met_rot_spd_steps else 0
        meter_back_pres = proc.met_back_pres_steps[0] if proc.met_back_pres_steps else 0

        if met_stg not in _MULTI_METER_COEF_MAP:
            met_stg = max(k for k in _MULTI_METER_COEF_MAP.keys() if k <= met_stg)

        coefs = _MULTI_METER_COEF_MAP[met_stg]
        base_posi = proc.vps_pos

        proc.met_pres_steps = [coefs[0][i] * meter_pres for i in range(met_stg)]
        proc.met_rot_spd_steps = [coefs[1][i] * meter_speed for i in range(met_stg)]
        proc.met_back_pres_steps = [coefs[2][i] * meter_back_pres for i in range(met_stg)]
        proc.met_pos_steps = [base_posi + coefs[3][i] * injection_length for i in range(met_stg)]

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