"""
工艺参数初始化器

基于机器、材料、产品信息推理初始工艺参数

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

logger = logging.getLogger(__name__)


# ========== 多级参数系数映射表（硬编码专家经验）==========

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


class ProcessInitializer:
    """
    工艺参数初始化器

    基于机器、材料、产品信息，使用专家规则推理初始工艺参数

    设备分组：
    - 注塑机参数（ProcessParams）
    - 模温机参数（MoldTempParams）
    - 热流道参数（HotRunnerParams）
    """

    def __init__(self, machine_info: Dict[str, Any], polymer_info: Dict[str, Any]):
        if not machine_info:
            raise ValueError("机器信息不能为空")
        if not polymer_info:
            raise ValueError("材料信息不能为空")

        self.machine = machine_info
        self.material = polymer_info
        self.product: Optional[Dict[str, Any]] = None

    def derive(self, product_info: Dict[str, Any]) -> ProductionParams:
        """
        推导初始工艺参数

        包含注塑机、模温机、热流道的完整工艺参数。
        """
        self.product = product_info
        self._validate_inputs()

        params = ProductionParams(
            process=ProcessParams(),
            mold_temp=MoldTempParams(),
            hot_runner=HotRunnerParams(),
        )

        # 按设备分组推导
        # 主体：ProcessParams（行业默认的"工艺参数"）
        # 拓展：MoldTempParams、HotRunnerParams
        self._derive_process(params)
        self._derive_mold_temp(params)
        self._derive_hot_runner(params)

        self._apply_multi_stage(params)
        self._format_output(params)

        return params

    def _validate_inputs(self):
        """校验输入信息"""
        # 机器信息
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

        # 材料信息 - 填充默认值
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

        # 产品信息
        required_product_fields = ['product_weight', 'gate_type', 'ave_thickness', 'max_thickness']
        for field in required_product_fields:
            if not self.product.get(field):
                raise ValueError(f"产品信息缺少必要字段: {field}")
        # runner_weight 允许为 0（表示热流道）

    def _derive_process(self, params: ProductionParams):
        """
        推导注塑机工艺参数（主体）

        包含：注射、VP切换、保压、冷却、计量、松退、温度
        """
        prod = self.product
        mach = self.machine
        mat = self.material
        proc = params.process

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

        # 注射压力
        inj_pres = max_inj_pres * 0.65

        # 注射速度（按材料类型）
        poly_type = mat.get('abbreviation', 'ABS')
        if poly_type in ["PVC", "POM", "PMMA", "ABS", "AS", "PE", "HDPE", "LDPE", "LLDPE", "PP"]:
            inj_velo = max_inj_velo * (0.4 if inj_ratio >= 100 else max_inj_velo * (0.3 + inj_ratio / 500.0))
        elif poly_type == "PC+ABS":
            inj_velo = max_inj_velo * (0.34 if inj_ratio >= 100 else max_inj_velo * (0.215 + inj_ratio / 800.0))
        else:
            inj_velo = max_inj_velo * (0.42 if inj_ratio >= 100 else max_inj_velo * (0.35 + inj_ratio / 500.0))

        # 注射时间
        inj_time = max(3, 4 * inj_len / inj_velo)

        proc.inj_stg = 1
        proc.inj_spd_steps = [inj_velo]
        proc.inj_pres_steps = [inj_pres]
        proc.inj_pos_steps = [0]
        proc.inj_t = inj_time
        proc.inj_dly_t = HSO_INJ_START_DELAY_TIME

        # ========== VP切换参数 ==========
        vp_mode = prod.get('VP_switch_mode', '位置')
        proc.vps_mode = 0 if vp_mode == "位置" else (1 if vp_mode == "时间" else 2)

        base_posi = 10 if product_weight < 120 else 15
        vp_pos = base_posi + (1 - length_ratio) * injection_length
        proc.vps_pos = vp_pos
        proc.vps_t = 0
        proc.vps_pres = 0
        proc.vps_spd = 0

        # 更新注射位置为VP切换位置
        proc.inj_pos_steps = [vp_pos]

        # ========== 保压参数 ==========
        max_hold_pres = mach.get('max_set_holding_pressure', 100)
        max_hold_velo = mach.get('max_set_holding_velocity', 100)

        # 保压压力
        hold_pres = 0.25 * max_hold_pres + 10 * avg_thickness
        if hold_pres >= 120:
            hold_pres = 0.65 * inj_pres

        # 保压速度
        hold_velo = 0.15 * max_hold_velo

        # 保压时间（按浇口类型）
        hold_time = self._calc_hold_time(prod)

        proc.hold_stg = 1
        proc.hold_pres_steps = [hold_pres]
        proc.hold_spd_steps = [hold_velo]
        proc.hold_time_steps = [hold_time]
        proc.hold_limit_spd = HSO_PACK_VELOCITY

        # ========== 冷却参数 ==========
        k_weight = 1 if product_weight < 100 else (product_weight / 100) ** 0.5
        cool_time = 5 * prod.get('max_thickness', 2) * k_weight

        if prod.get('inject_cycle_require'):
            else_time = 1.5
            cool_time = int(prod['inject_cycle_require'] - inj_time - hold_time - else_time)

        proc.cool_t = max(5, cool_time)

        # ========== 计量参数 ==========
        meter_pres = 0
        if mach.get('power_method') == '液压机':
            nozzle_type = mach.get('nozzle_type', '直通型')
            max_metering_pres = mach.get('max_set_metering_pressure', 20)
            meter_pres = 0.55 * max_metering_pres if nozzle_type == "直通型" else 0.6 * max_metering_pres

        max_screw_speed = mach.get('max_set_screw_rotation_speed', 150)
        recommend_shear_speed = mat.get('recommend_shear_linear_speed', 160)
        temp_ratio = max(0.3, min(0.75, 60.0 * recommend_shear_speed / (screw_diameter * HSO_PI) / max_screw_speed))
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
        proc.pre_met_decomp_mode = 0  # 否
        proc.pre_met_decomp_spd = HSO_SUCKBACK_VELO_BEFORE_METER
        proc.pre_met_decomp_dist = HSO_SUCKBACK_DIS_BEFORE_METER

        proc.pst_met_decomp_mode = 0  # 距离
        proc.pst_met_decomp_spd = HSO_SUCKBACK_VELO_AFTER_METER
        decomp_dist = max(2, min(0.1 * injection_length, 10))
        proc.pst_met_decomp_dist = decomp_dist

        proc.met_end_pos = meter_posi + decomp_dist

        # ========== 温度参数 ==========
        nozzle_type = mach.get('nozzle_type', '直通型')
        recommend_melt_temp = mat.get('recommend_melt_temperature', 250)
        proc.noz_temp = recommend_melt_temp - 5.0 if nozzle_type == "直通型" else recommend_melt_temp

        proc.brl_temp_stg = prod.get('barrel_temperature_stage', 5)
        proc.brl_temp_steps = [recommend_melt_temp - 10 * i for i in range(proc.brl_temp_stg)]

    def _derive_mold_temp(self, params: ProductionParams):
        """推导模温机工艺参数"""
        mat = self.material
        prod = self.product

        recommend_mold_temp = mat.get('recommend_mold_temperature', 0)
        if recommend_mold_temp != 0:
            params.mold_temp.mold_temp = recommend_mold_temp
        else:
            mold_temp_defaults = {
                "PP": 40, "PC": 80, "ABS": 50, "PC+ABS": 70, "PC/ABS": 70,
                "PS": 40, "PE": 40, "LDPE": 40, "HDPE": 40, "LLDPE": 40,
                "PVC": 40, "PA6": 60, "PA66": 70, "PA": 60, "PET": 90,
            }
            params.mold_temp.mold_temp = mold_temp_defaults.get(mat.get('abbreviation', 'ABS'), 50)

    def _derive_hot_runner(self, params: ProductionParams):
        """推导热流道工艺参数"""
        prod = self.product

        valve_num = prod.get('valve_num', 0)
        params.hot_runner.valve_num = valve_num
        if valve_num:
            params.hot_runner.valve_time_steps = list(range(1, int(valve_num) + 1))

    def _calc_hold_time(self, prod: Dict[str, Any]) -> float:
        """计算保压时间（按浇口类型）"""
        gate_type = prod.get('gate_type', '直浇口')
        avg_thickness = prod.get('ave_thickness', 2)

        if gate_type in ("直浇口", "护耳式浇口", "点浇口"):
            hold_time = 0.5 + 0.1 * avg_thickness
        elif gate_type == "侧浇口":
            gate_radius = prod.get('gate_radius')
            gate_length = prod.get('gate_length')
            gate_width = prod.get('gate_width')
            if gate_radius:
                gate_area = HSO_PI * (gate_radius ** 2)
            elif gate_length and gate_width:
                gate_area = gate_length * gate_width
            else:
                return 2.0
            hold_time = 2 * gate_area
        else:
            hold_time = 0.3 + 0.6 * (avg_thickness ** 2)

        return max(2, min(hold_time, 10))

    def _apply_multi_stage(self, params: ProductionParams):
        """
        应用多级参数

        根据注射行程自动推荐段数，并应用多级系数：
        - 注射段数：根据注射行程（>=40mm→4段, 20-40mm→3段, 10-20mm→2段, <10mm→1段）
        - 保压段数：固定2段
        - 计量段数：固定1段
        """
        prod = self.product
        mat = self.material
        proc = params.process

        # 计算注射行程（已在 _derive_process 中计算）
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

        # 如果产品指定了段数，以产品为准
        if prod.get('inj_stg'):
            inj_stg = prod['inj_stg']

        proc.inj_stg = inj_stg

        # ========== 2. 确定保压段数 ==========
        # 默认2段
        prod_hold_stg = prod.get('hold_stg', 2)
        proc.hold_stg = prod_hold_stg

        # ========== 3. 确定计量段数 ==========
        # 默认1段
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
            self._apply_multi_metering(proc, prod_met_stg)

    def _apply_multi_injection(
        self,
        proc: ProcessParams,
        inj_stg: int,
        runner_weight: float,
        injection_length: float
    ):
        """
        应用多级注射参数

        根据流道类型（热流道/冷流道）和材料类型应用不同系数
        """
        mat = self.material

        # 获取基础参数
        inj_pres = proc.inj_pres_steps[0] if proc.inj_pres_steps else 0
        inj_velo = proc.inj_spd_steps[0] if proc.inj_spd_steps else 0
        vp_pos = proc.vps_pos
        meter_end_pos = proc.met_end_pos
        decomp_dist = proc.pst_met_decomp_dist

        # 根据材料和流道类型选择系数表
        is_hot_runner = runner_weight <= 0.01
        is_abs = mat.get('abbreviation') == 'ABS'

        if is_abs:
            # ABS材料特殊系数
            if is_hot_runner:
                # ABS热流道
                coef_map = _MULTI_INJ_ABS_HOT
            else:
                # ABS冷流道
                coef_map = _MULTI_INJ_ABS_COLD
        else:
            # 通用系数
            if is_hot_runner:
                # 通用热流道
                coef_map = _MULTI_INJ_GENERIC_HOT
            else:
                # 通用冷流道
                coef_map = _MULTI_INJ_GENERIC_COLD

        # 获取对应段数的系数
        if inj_stg not in coef_map:
            inj_stg = max(k for k in coef_map.keys() if k <= inj_stg)

        coefs = coef_map[inj_stg]
        pres_coefs = coefs[0]  # 压力系数
        velo_coefs = coefs[1]  # 速度系数
        pos_coefs = coefs[2]   # 位置系数

        # 计算多级注射压力
        proc.inj_pres_steps = [pres_coefs[i] * inj_pres for i in range(inj_stg)]

        # 计算多级注射速度
        proc.inj_spd_steps = [velo_coefs[i] * inj_velo for i in range(inj_stg)]

        # 计算多级注射位置
        if is_hot_runner:
            proc.inj_pos_steps = [
                vp_pos + pos_coefs[i] * (injection_length + decomp_dist)
                for i in range(inj_stg)
            ]
        else:
            # 冷流道：根据流道比和产品比计算
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
        # 获取基础参数
        hold_pres = proc.hold_pres_steps[0] if proc.hold_pres_steps else 0
        hold_velo = proc.hold_spd_steps[0] if proc.hold_spd_steps else 0
        hold_time = proc.hold_time_steps[0] if proc.hold_time_steps else 0

        # 多级保压系数 [压力系数, 速度系数, 时间系数]
        holding_coef_map = {
            2: [[1, 0.5], [1, 0.5], [0.5, 0.5]],
            3: [[1, 0.7, 0.4], [1, 0.7, 0.4], [0.3, 0.4, 0.3]],
            4: [[1, 0.75, 0.5, 0.25], [1, 0.75, 0.5, 0.25], [0.25, 0.25, 0.25, 0.25]],
            5: [[1, 0.8, 0.6, 0.4, 0.2], [1, 0.8, 0.6, 0.4, 0.2], [0.2, 0.2, 0.2, 0.2, 0.2]],
        }

        # 找到最接近的段数
        if hold_stg not in holding_coef_map:
            hold_stg = max(k for k in holding_coef_map.keys() if k <= hold_stg)

        coefs = holding_coef_map[hold_stg]

        proc.hold_pres_steps = [coefs[0][i] * hold_pres for i in range(hold_stg)]
        proc.hold_spd_steps = [coefs[1][i] * hold_velo for i in range(hold_stg)]
        proc.hold_time_steps = [coefs[2][i] * hold_time for i in range(hold_stg)]

    def _apply_multi_metering(self, proc: ProcessParams, met_stg: int):
        """应用多级计量参数"""
        # 获取基础参数
        meter_pres = proc.met_pres_steps[0] if proc.met_pres_steps else 0
        meter_speed = proc.met_rot_spd_steps[0] if proc.met_rot_spd_steps else 0
        meter_back_pres = proc.met_back_pres_steps[0] if proc.met_back_pres_steps else 0
        meter_posi = proc.met_pos_steps[0] if proc.met_pos_steps else 0

        # 计算注射行程（用于计量位置计算）
        total_weight = self.product['product_weight']
        melt_density = self.material.get('melt_density', 0.95)
        screw_diameter = self.machine.get('screw_diameter', 35)
        injection_volume = total_weight / melt_density
        injection_length = injection_volume * 1000.0 / (HSO_PI * (screw_diameter ** 2) / 4)

        # 多级计量系数 [压力系数, 转速系数, 背压系数, 位置系数]
        metering_coef_map = {
            2: [[1, 1], [1, 0.8], [0.8, 1], [0.5, 1]],
            3: [[1, 1, 1], [0.75, 1, 0.75], [0.5, 0.75, 1], [0.3, 0.7, 1]],
            4: [[1, 1, 1, 1], [0.75, 1, 1, 0.75], [0.25, 0.5, 0.75, 1], [0.2, 0.5, 0.8, 1]],
        }

        # 找到最接近的段数
        if met_stg not in metering_coef_map:
            met_stg = max(k for k in metering_coef_map.keys() if k <= met_stg)

        coefs = metering_coef_map[met_stg]
        base_posi = proc.vps_pos  # 使用VP切换位置作为基准

        proc.met_pres_steps = [coefs[0][i] * meter_pres for i in range(met_stg)]
        proc.met_rot_spd_steps = [coefs[1][i] * meter_speed for i in range(met_stg)]
        proc.met_back_pres_steps = [coefs[2][i] * meter_back_pres for i in range(met_stg)]
        proc.met_pos_steps = [base_posi + coefs[3][i] * injection_length for i in range(met_stg)]

    def _format_output(self, params: ProductionParams):
        """格式化输出"""
        proc = params.process

        # 注射参数
        proc.inj_pres_steps = [round(v, 0) for v in proc.inj_pres_steps]
        proc.inj_spd_steps = [round(v, 0) for v in proc.inj_spd_steps]
        proc.inj_pos_steps = [round(v, 2) for v in proc.inj_pos_steps]
        proc.inj_t = round(proc.inj_t, 2)
        proc.inj_dly_t = round(proc.inj_dly_t, 2)

        # VP切换参数
        proc.vps_pos = round(proc.vps_pos, 2)
        proc.vps_t = round(proc.vps_t, 2)

        # 保压参数
        proc.hold_pres_steps = [round(v, 0) for v in proc.hold_pres_steps]
        proc.hold_spd_steps = [round(v, 0) for v in proc.hold_spd_steps]
        proc.hold_time_steps = [round(v, 2) for v in proc.hold_time_steps]

        # 冷却参数
        proc.cool_t = round(proc.cool_t, 2)

        # 松退参数
        proc.pst_met_decomp_dist = round(proc.pst_met_decomp_dist, 2)
        proc.met_end_pos = round(proc.met_end_pos, 2)

        # 温度参数
        proc.noz_temp = round(proc.noz_temp, 0)
        proc.brl_temp_steps = [round(t, 0) for t in proc.brl_temp_steps]