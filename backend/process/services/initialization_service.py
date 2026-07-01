"""
工艺参数初始化服务

基于 InitRuleMatcher（数据库规则）+ ProcessInitializer 推理初始工艺参数。
对应接口：POST /api/processes/initialization/

支持两种输入模式：
- Mode A: condition_id（推荐）— 从数据库 ProcessCondition + Mold/InjectionMachine/Polymer 组装上下文
- Mode B: 字典快照 — 直接传 machine_info/polymer_info/product_info（向后兼容/纯试算）
"""

import logging
from typing import Dict, Any, Optional, Tuple

from process.engines.expert.initializer import ProcessInitializer
from process.engines.expert.rule_matcher import InitRuleMatcher

logger = logging.getLogger(__name__)


# ========== 字段映射 ==========
# masterdata 是复合模型：Mold 本身只有元数据，产品/浇口/壁厚信息分散在
# GatingSystem / Cavity / Gate 关联表中。这里集中维护映射逻辑。

# Mold ORM → product_info dict （仅模具级字段）
_MOLD_TO_PRODUCT = {
    'shot_count': 'shot_count',
    # inject_cycle_require 通常来自 Mold.target_cycle_time，需额外处理
}

# InjectionMoldingMachine ORM → machine_info dict
# 注：模型中 max_set_injection_speed / max_set_holding_speed 与
# ProcessInitializer 期望的 *_velocity 名字不同
_MACHINE_TO_MACHINE = {
    'screw_diameter': 'screw_diameter',
    'max_set_injection_pressure': 'max_set_injection_pressure',
    'max_set_injection_velocity': 'max_set_injection_speed',
    'max_set_holding_pressure': 'max_set_holding_pressure',
    'max_set_holding_velocity': 'max_set_holding_speed',
    'max_set_screw_rotation_speed': 'max_set_screw_rotation_speed',
    'max_set_metering_pressure': 'max_set_metering_pressure',
    'nozzle_type': 'nozzle_type',
}

# Polymer ORM → polymer_info dict
_POLYMER_TO_POLYMER = {
    'abbreviation': 'abbreviation',
    'recommend_melt_temperature': 'recommended_melt_temp',
    'recommend_shear_linear_speed': 'recommended_shear_line_speed',
    'recommend_back_pressure': 'recommend_back_pressure',
    'recommend_mold_temperature': 'recommended_mold_temp',
    'melt_density': 'melt_density',
}


def _build_product_info(mold) -> Dict[str, Any]:
    """从 Mold（复合模型）组装 product_info dict

    数据源：
    - Mold 自身：模具级元数据
    - GatingSystem（取第一个）：浇注系统与产品重量
    - Cavity（取第一个）：型腔与壁厚
    - Gate（取第一个）：浇口类型/尺寸
    """
    from masterdata.models.mold import GatingSystem, Cavity, Gate

    product_info: Dict[str, Any] = {}

    # 1. 模具级字段
    for target_key, attr in _MOLD_TO_PRODUCT.items():
        value = getattr(mold, attr, None)
        if value is not None:
            product_info[target_key] = value

    # 2. 浇注系统（GatingSystem）→ 产品重量 / 流道重量
    gating = getattr(mold, 'gating_systems', None)
    gating_first = gating.first() if gating is not None else None
    if gating_first is not None:
        if gating_first.total_product_weight is not None:
            product_info['product_weight'] = gating_first.total_product_weight
        # runner_weight 兜底链：runner_weight → estimated_runner_weight
        runner_w = gating_first.runner_weight or gating_first.estimated_runner_weight
        if runner_w is not None:
            product_info['runner_weight'] = runner_w
        if getattr(gating_first, 'runner_type', None):
            product_info['runner_type'] = gating_first.runner_type
        if getattr(mold, 'target_cycle_time', None) is not None:
            product_info['inject_cycle_require'] = mold.target_cycle_time

    # 3. 型腔（Cavity）→ 壁厚 / 流长 / 流长比
    # 注意：Cavity 是 GatingSystem 的子表，不是 Mold 直接子表
    cavities = getattr(gating_first, 'cavities', None) if gating_first is not None else None
    cavity_first = cavities.first() if cavities is not None else None
    if cavity_first is not None:
        if cavity_first.ave_wall_thickness is not None:
            product_info['ave_thickness'] = cavity_first.ave_wall_thickness
        if cavity_first.max_wall_thickness is not None:
            product_info['max_thickness'] = cavity_first.max_wall_thickness
        if cavity_first.max_flow_length is not None:
            product_info['max_length'] = cavity_first.max_flow_length
        elif cavity_first.flow_ratio and cavity_first.ave_wall_thickness:
            # 兜底：max_flow_length 缺失时从 flow_ratio × ave_wall_thickness 反推
            product_info['max_length'] = (
                cavity_first.flow_ratio * cavity_first.ave_wall_thickness
            )

    # 4. 浇口（Gate）→ 浇口类型与尺寸
    if cavity_first is not None:
        gates = getattr(cavity_first, 'gates', None)
        gate_first = gates.first() if gates is not None else None
        if gate_first is not None:
            if gate_first.gate_type is not None:
                product_info['gate_type'] = gate_first.gate_type
            # 侧浇口几何参数
            if gate_first.length is not None:
                product_info['gate_length'] = gate_first.length
            if gate_first.width is not None:
                product_info['gate_width'] = gate_first.width
            # 圆形浇口半径（取 outer_diameter / 2 兜底）
            radius = None
            if gate_first.outer_diameter is not None:
                radius = gate_first.outer_diameter / 2
            if radius is not None:
                product_info['gate_radius'] = radius

    # 5. 段数与默认值（避免 _apply_multi_stage 按行程自动推导段数）
    # 与 Mode B 字典模式保持一致：hold_stg=1, met_stg=1
    product_info.setdefault('inj_stg', 1)
    product_info.setdefault('hold_stg', 1)
    product_info.setdefault('met_stg', 1)
    product_info.setdefault('barrel_temperature_stage', 5)

    return product_info


class ProcessInitializationService:
    """工艺参数初始化服务

    封装 ProcessInitializer 调用，对外暴露：
    - 完整 ProductionParams（扁平 dict）
    - 命中的规则代码列表（便于前端展示"由哪些规则推导"）
    - 参数来源标识
    """

    PARAM_SOURCE = "algorithm_init"

    def __init__(self, rule_matcher: Optional[InitRuleMatcher] = None):
        self.rule_matcher = rule_matcher or InitRuleMatcher()

    # ========== 公开入口（兼容两种模式）==========

    def infer_initial_params(
        self,
        machine_info: Optional[Dict[str, Any]] = None,
        polymer_info: Optional[Dict[str, Any]] = None,
        product_info: Optional[Dict[str, Any]] = None,
        condition_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """推理初始工艺参数

        Args:
            machine_info: 注塑机信息字典（Mode B）
            polymer_info: 材料信息字典（Mode B）
            product_info: 产品信息字典（Mode B）
            condition_id: 工艺条件 ID（Mode A，与字典参数互斥）

        Returns:
            {
                "param_source": "algorithm_init",
                "condition_id": int | None,
                "matched_rules": [...],
                "process": {...},
                "mold_temp": {...},
                "hot_runner": {...},
                "summary": {...}
            }
        """
        if condition_id is not None:
            machine_info, polymer_info, product_info = self._build_context_from_condition(
                condition_id,
            )
        else:
            # Mode B：字典模式，三个字典都必填
            if not (machine_info and polymer_info and product_info):
                raise ValueError(
                    "字典模式下 machine_info/polymer_info/product_info 均必填；"
                    "或传入 condition_id 走数据库组装模式。"
                )

        logger.info(
            "工艺参数初始化: condition_id=%s, polymer=%s, gate_type=%s, weight=%s",
            condition_id,
            polymer_info.get("abbreviation"),
            product_info.get("gate_type"),
            product_info.get("product_weight"),
        )

        initializer = ProcessInitializer(
            machine_info=machine_info,
            polymer_info=polymer_info,
            rule_matcher=self.rule_matcher,
        )
        params = initializer.derive(product_info)

        matched_rules = list(self.rule_matcher.last_matched_codes)

        result = {
            "param_source": self.PARAM_SOURCE,
            "condition_id": condition_id,
            "matched_rules": matched_rules,
            "process": params.process.to_dict(),
            "mold_temp": params.mold_temp.to_dict(),
            "hot_runner": params.hot_runner.to_dict(),
            "summary": self._build_summary(params),
        }
        logger.info(
            "工艺参数初始化完成: 命中规则=%s, inj_pres=%.2f, hold_t=%.2f, cool_t=%.2f",
            matched_rules,
            result["summary"]["injection_pressure"],
            result["summary"]["holding_time"],
            result["summary"]["cooling_time"],
        )
        return result

    # ========== Mode A: 从 condition_id 组装上下文 ==========

    @staticmethod
    def _build_context_from_condition(
        condition_id: int,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """从 ProcessCondition 关联的 Mold/InjectionMachine/Polymer 组装完整上下文

        Returns:
            (machine_info, polymer_info, product_info)

        Raises:
            ProcessCondition.DoesNotExist: condition_id 不存在
            ValueError: condition 缺少必要外键（mold / machine / polymer）
        """
        from process.models.process_condition import ProcessCondition

        try:
            condition = (
                ProcessCondition.objects
                .select_related('mold', 'injection_machine', 'polymer')
                .get(pk=condition_id)
            )
        except ProcessCondition.DoesNotExist:
            raise ValueError(f"ProcessCondition(id={condition_id}) 不存在")

        if not condition.mold:
            raise ValueError(f"Condition(id={condition_id}) 缺少 mold 关联")
        if not condition.injection_machine:
            raise ValueError(f"Condition(id={condition_id}) 缺少 injection_machine 关联")
        if not condition.polymer:
            raise ValueError(f"Condition(id={condition_id}) 缺少 polymer 关联")

        # 注塑机的注射参数（screw_diameter / max_set_* / nozzle_type）
        # 不在 InjectionMoldingMachine 本体上，而在 InjectionUnit 子表中。
        # 按 condition.injection_index 选择特定 unit（默认 1）。
        machine_info = _build_machine_info(condition.injection_machine, condition.injection_index)
        polymer_info = _map_model_to_dict(condition.polymer, _POLYMER_TO_POLYMER)
        product_info = _build_product_info(condition.mold)

        # shot_index / injection_index 透传给 product_info
        if condition.shot_index is not None:
            product_info.setdefault('shot_index', condition.shot_index)
        if condition.injection_index is not None:
            product_info.setdefault('injection_index', condition.injection_index)

        return machine_info, polymer_info, product_info

    @staticmethod
    def _build_summary(params) -> Dict[str, float]:
        """从 ProductionParams 抽取关键参数摘要，便于前端展示"""
        proc = params.process
        return {
            "injection_pressure": (proc.inj_pres_steps[0] if proc.inj_pres_steps else 0.0),
            "injection_velocity": (proc.inj_spd_steps[0] if proc.inj_spd_steps else 0.0),
            "vp_switch_position": proc.vps_pos,
            "holding_pressure": (proc.hold_pres_steps[0] if proc.hold_pres_steps else 0.0),
            "holding_time": (proc.hold_time_steps[0] if proc.hold_time_steps else 0.0),
            "cooling_time": proc.cool_t,
            "injection_time": proc.inj_t,
            "barrel_nozzle_temp": proc.noz_temp,
            "barrel_temps": list(proc.brl_temp_steps),
            "metering_back_pressure": (
                proc.met_back_pres_steps[0] if proc.met_back_pres_steps else 0.0
            ),
            "mold_temp": params.mold_temp.mold_temp,
            "hot_runner_valve_num": params.hot_runner.valve_num,
        }

    # ========== Mode C: 从 ID 创建 Condition + Parameter 并推理 ==========

    def create_and_infer_initial_params(
        self,
        mold_id: int,
        polymer_id: int,
        injection_machine_id: int,
        shot_index: int = 1,
        injection_index: int = 1,
        status: str = "draft",
        origin_type: str = "ai_recommendation",
        condition_code: Optional[str] = None,
        overrides: Optional[Dict[str, Any]] = None,
        inj_stg: int = 1,
        hold_stg: int = 1,
        met_stg: int = 1,
        barrel_temperature_stage: int = 5,
        vps_mode: Optional[int] = None,
        pre_met_decomp_mode: Optional[int] = None,
        pst_met_decomp_mode: Optional[int] = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """第三方场景：一站式创建 ProcessCondition + ProcessParameter 并返回推理参数

        Args:
            mold_id: 模具 ID
            polymer_id: 材料 ID
            injection_machine_id: 注塑机 ID
            shot_index: 注射次数
            injection_index: 注射单元索引
            status: Condition 状态
            origin_type: Condition 起源类型
            condition_code: Condition 编号（None 时自动生成）
            overrides: 用户覆盖字段（覆盖 masterdata 默认值）
            inj_stg/hold_stg/met_stg: 段数覆盖
            barrel_temperature_stage: 料筒温度段数覆盖
            vps_mode/pre_met_decomp_mode/pst_met_decomp_mode: 模式覆盖
            save: 是否落库（True=创建 Condition+Parameter；False=纯推理不落库，condition_id 返回 None）

        Returns:
            save=True:
            {
                "condition_id": int,
                "parameter_id": int,
                "matched_rules": [...],
                "process": {...}, "mold_temp": {...}, "hot_runner": {...},
                "summary": {...}
            }
            save=False:
            {
                "condition_id": None,
                "parameter_id": None,
                "matched_rules": [...],
                "process": {...}, "mold_temp": {...}, "hot_runner": {...},
                "summary": {...}
            }

        Raises:
            Mold/Polymer/InjectionMoldingMachine.DoesNotExist: 关联主数据不存在
        """
        from django.db import transaction
        from process.models.process_condition import ProcessCondition
        from process.models.process_parameter import ProcessParameter
        from masterdata.models.mold import Mold
        from masterdata.models.injection import InjectionMoldingMachine
        from masterdata.models.material import Polymer

        # 1. 校验主数据存在
        try:
            mold = Mold.objects.get(pk=mold_id)
        except Mold.DoesNotExist:
            raise ValueError(f"Mold(id={mold_id}) 不存在")
        try:
            machine = InjectionMoldingMachine.objects.get(pk=injection_machine_id)
        except InjectionMoldingMachine.DoesNotExist:
            raise ValueError(f"InjectionMoldingMachine(id={injection_machine_id}) 不存在")
        try:
            polymer = Polymer.objects.get(pk=polymer_id)
        except Polymer.DoesNotExist:
            raise ValueError(f"Polymer(id={polymer_id}) 不存在")

        # 2. 用 Mode A 组装上下文（数据库组装）
        # 临时创建 Condition 给 _build_context_from_condition 用，然后建真正的 Condition
        # ——为简化逻辑，直接复用 _build_context_from_condition 但它需要 condition_id
        # 这里改为复用 _build_machine_info / _build_product_info + 手动构造 polymer_info
        machine_info = _build_machine_info(machine, injection_index)
        polymer_info = _map_model_to_dict(polymer, _POLYMER_TO_POLYMER)
        product_info = _build_product_info(mold)

        # 应用 overrides（用户覆盖 masterdata 默认值）
        if overrides:
            for k, v in overrides.items():
                if v is not None:
                    product_info[k] = v
        product_info['shot_index'] = shot_index
        product_info['injection_index'] = injection_index
        # 段数覆盖（与 ProcessInitializer/ProcessParameter 模型字段对应）
        product_info['inj_stg'] = inj_stg
        product_info['hold_stg'] = hold_stg
        product_info['met_stg'] = met_stg
        product_info['barrel_temperature_stage'] = barrel_temperature_stage
        # 模式覆盖（可选手填，否则走默认派生逻辑）
        if vps_mode is not None:
            product_info['vps_mode'] = vps_mode
        if pre_met_decomp_mode is not None:
            product_info['pre_met_decomp_mode'] = pre_met_decomp_mode
        if pst_met_decomp_mode is not None:
            product_info['pst_met_decomp_mode'] = pst_met_decomp_mode

        # 3. 推理参数
        logger.info(
            "工艺参数初始化(Mode C, save=%s): mold_id=%s, machine_id=%s, polymer_id=%s, "
            "shot=%s, inj_idx=%s",
            save, mold_id, injection_machine_id, polymer_id, shot_index, injection_index,
        )
        initializer = ProcessInitializer(
            machine_info=machine_info,
            polymer_info=polymer_info,
            rule_matcher=self.rule_matcher,
        )
        params = initializer.derive(product_info)
        matched_rules = list(self.rule_matcher.last_matched_codes)

        # 4. 根据 save 决定是否落库
        condition_id: Optional[int] = None
        parameter_id: Optional[int] = None
        if save:
            with transaction.atomic():
                condition = ProcessCondition.objects.create(
                    condition_code=condition_code or self._auto_condition_code(mold_id, shot_index),
                    status=status,
                    origin_type=origin_type,
                    mold=mold,
                    shot_index=shot_index,
                    injection_machine=machine,
                    injection_index=injection_index,
                    polymer=polymer,
                    process_context_snapshot={
                        'source': 'initialization_from_ids',
                        'matched_rules': matched_rules,
                        'overrides': overrides or {},
                    },
                )
                parameter = self._create_process_parameter(condition, params)
                condition_id = condition.id
                parameter_id = parameter.id
            logger.info(
                "Mode C 落库完成: condition_id=%s, parameter_id=%s, rules=%s",
                condition_id, parameter_id, matched_rules,
            )
        else:
            logger.info(
                "Mode C 纯推理完成（save=False）: rules=%s",
                matched_rules,
            )

        return {
            "condition_id": condition_id,
            "parameter_id": parameter_id,
            "matched_rules": matched_rules,
            "process": params.process.to_dict(),
            "mold_temp": params.mold_temp.to_dict(),
            "hot_runner": params.hot_runner.to_dict(),
            "summary": self._build_summary(params),
        }

    @staticmethod
    def _auto_condition_code(mold_id: int, shot_index: int) -> str:
        """自动生成 condition_code

        格式：C-{mold_id}-S{shot_index}-{ts}
        ts 用 microseconds 保证同一毫秒内的多次调用也不冲突
        """
        import time
        ts = int(time.time() * 1000000) % 1000000
        return f"C-{mold_id}-S{shot_index}-{ts:06d}"

    @staticmethod
    def _create_process_parameter(condition, params):
        """把 ProductionParams 拍扁为 ProcessParameter 字段并落库

        ProcessParameter 的字段是 inj_spd_1/2/3/... 形式，
        而 ProductionParams 用 inj_spd_steps 数组形式。需要在中间转换。
        """
        from process.models.process_parameter import ProcessParameter

        proc = params.process
        flat = {
            'process_condition': condition,
            'param_source': ProcessInitializationService.PARAM_SOURCE,
        }
        # 单值字段（必须与 ProcessParameter 模型字段对应）
        single_value_fields = [
            'inj_stg', 'inj_t', 'inj_dly_t',
            'vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd',
            'hold_stg',
            'cool_t',
            'met_stg', 'met_lim_t', 'met_end_pos',
            'pre_met_decomp_mode', 'pre_met_decomp_pres', 'pre_met_decomp_spd',
            'pre_met_decomp_t', 'pre_met_decomp_dist',
            'pst_met_decomp_mode', 'pst_met_decomp_pres', 'pst_met_decomp_spd',
            'pst_met_decomp_t', 'pst_met_decomp_dist',
            'brl_temp_stg', 'noz_temp',
        ]
        for f in single_value_fields:
            if hasattr(proc, f):
                flat[f] = getattr(proc, f, None)

        # 多级数组 → 扁平字段（inj_spd_1, inj_spd_2, ...）
        steps_mappings = [
            ('inj_spd_steps',   'inj_spd_{}', 6),
            ('inj_pres_steps',  'inj_pres_{}', 6),
            ('inj_pos_steps',   'inj_pos_{}', 6),
            ('hold_pres_steps', 'hold_pres_{}', 5),
            ('hold_spd_steps',  'hold_spd_{}', 5),
            ('hold_time_steps', 'hold_t_{}', 5),
            ('met_pres_steps',  'met_pres_{}', 4),
            ('met_rot_spd_steps', 'met_rot_spd_{}', 4),
            ('met_back_pres_steps', 'met_back_pres_{}', 4),
            ('met_pos_steps',   'met_pos_{}', 4),
            ('brl_temp_steps',  'brl_temp_{}', 9),
        ]
        for src_attr, fmt, n_stages in steps_mappings:
            steps = getattr(proc, src_attr, []) or []
            for i in range(n_stages):
                field = fmt.format(i + 1)
                flat[field] = steps[i] if i < len(steps) else None

        return ProcessParameter.objects.create(**flat)


# ========== 映射辅助函数 ==========

def _map_model_to_dict(model_obj, mapping: Dict[str, str]) -> Dict[str, Any]:
    """按 mapping 把 ORM 对象的指定字段提取到目标键的字典

    mapping 格式: {target_key: model_attr_name}
    """
    result: Dict[str, Any] = {}
    for target_key, attr_name in mapping.items():
        if hasattr(model_obj, attr_name):
            value = getattr(model_obj, attr_name, None)
            if value is not None:
                result[target_key] = value
    return result


def _build_machine_info(machine, injection_index: Optional[int] = None) -> Dict[str, Any]:
    """从 InjectionMoldingMachine + 选定的 InjectionUnit 组装 machine_info dict

    关系链：InjectionMoldingMachine → InjectionUnit（多个）
    selection 逻辑：
        - 指定 injection_index 时，按 1-based 选第 N 个
        - 未指定时，取第一个
    """
    units_qs = getattr(machine, 'injection_units', None)
    units_list = list(units_qs.all() if units_qs is not None else [])
    if not units_list:
        # 没有注射单元时，返回机器级字段（drive_system 等）
        return {
            'power_method': _drive_system_to_power_method(
                getattr(machine, 'drive_system', None)
            ),
        }

    if injection_index and 1 <= injection_index <= len(units_list):
        unit = units_list[injection_index - 1]
    else:
        unit = units_list[0]

    machine_info = _map_model_to_dict(unit, _MACHINE_TO_MACHINE)
    machine_info['power_method'] = _drive_system_to_power_method(
        getattr(machine, 'drive_system', None)
    )
    return machine_info


def _drive_system_to_power_method(drive_system: Optional[str]) -> Optional[str]:
    """InjectionMoldingMachine.drive_system → ProcessInitializer 期望的 power_method

    drive_system 字段取值（参考 molding-expert 模型 choices）：
        'hydraulic' / 'hydraulic_rear' / 'hydraulic_front' → '液压机'
        'electric' / 'hybrid' → '电动机'
    """
    if not drive_system:
        return None
    ds = str(drive_system).lower()
    if 'hydraulic' in ds or '液压' in ds:
        return '液压机'
    return '电动机'