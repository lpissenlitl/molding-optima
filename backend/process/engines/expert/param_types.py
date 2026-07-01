"""
工艺参数类型定义

按设备分组，组成完整生产工艺参数：
1. ProcessParams - 注塑机工艺参数（行业默认的"工艺参数"）
2. MoldTempParams - 模温机工艺参数
3. HotRunnerParams - 热流道工艺参数

ProductionParams 组合以上三类设备参数，形成完整生产工艺。

命名规范：
- 与 process_parameter.py 保持一致
- 多级参数使用 _steps 后缀表示有序数组
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ProcessParams:
    """
    注塑机工艺参数

    行业默认的"工艺参数"，直接参考 process_parameter.py 的命名规范。
    多级参数使用 _steps 后缀。

    包含注射、保压、冷却、计量、松退、温度等参数。
    """
    # ========== 注射参数 ==========
    inj_stg: int = 1  # 注射段数

    # 多级注射速度 (mm/s)
    inj_spd_steps: List[float] = field(default_factory=list)
    # 多级注射压力 (MPa)
    inj_pres_steps: List[float] = field(default_factory=list)
    # 多级注射位置 (mm)
    inj_pos_steps: List[float] = field(default_factory=list)

    inj_t: float = 0.0  # 注射时间 (s)
    inj_dly_t: float = 0.0  # 注射延迟 (s)

    # ========== VP切换参数 ==========
    vps_mode: int = 0  # VP切换模式
    vps_pos: float = 0.0  # VP切换位置 (mm)
    vps_t: float = 0.0  # VP切换时间 (s)
    vps_pres: float = 0.0  # VP切换压力 (MPa)
    vps_spd: float = 0.0  # VP切换速度 (mm/s)

    # ========== 保压参数 ==========
    hold_stg: int = 1  # 保压段数

    # 多级保压压力 (MPa)
    hold_pres_steps: List[float] = field(default_factory=list)
    # 多级保压速度 (mm/s)
    hold_spd_steps: List[float] = field(default_factory=list)
    # 多级保压时间 (s)
    hold_time_steps: List[float] = field(default_factory=list)

    hold_limit_spd: float = 30.0  # 保压限速 (mm/s)

    # ========== 冷却参数 ==========
    cool_t: float = 0.0  # 冷却时间 (s)

    # ========== 计量/熔胶参数 ==========
    met_stg: int = 1  # 计量段数

    # 多级计量压力 (MPa)
    met_pres_steps: List[float] = field(default_factory=list)
    # 多级螺杆转速 (rpm)
    met_rot_spd_steps: List[float] = field(default_factory=list)
    # 多级背压 (MPa)
    met_back_pres_steps: List[float] = field(default_factory=list)
    # 多级计量位置 (mm)
    met_pos_steps: List[float] = field(default_factory=list)

    met_lim_t: float = 0.5  # 计量延时 (s)

    # ========== 松退参数 ==========
    # 参考 process_parameter.py 的命名
    pre_met_decomp_mode: int = 0  # 熔胶前松退模式
    pre_met_decomp_pres: float = 0.0  # 熔胶前松退压力
    pre_met_decomp_spd: float = 0.0  # 熔胶前松退速度
    pre_met_decomp_t: float = 0.0  # 熔胶前松退时间
    pre_met_decomp_dist: float = 0.0  # 熔胶前松退距离

    pst_met_decomp_mode: int = 0  # 熔胶后松退模式
    pst_met_decomp_pres: float = 0.0  # 熔胶后松退压力
    pst_met_decomp_spd: float = 0.0  # 熔胶后松退速度
    pst_met_decomp_t: float = 0.0  # 熔胶后松退时间
    pst_met_decomp_dist: float = 0.0  # 熔胶后松退距离

    met_end_pos: float = 0.0  # 熔胶终止位置

    # ========== 温度参数 ==========
    brl_temp_stg: int = 5  # 料筒温度段数
    noz_temp: float = 0.0  # 喷嘴温度 (℃)
    # 多级料筒温度 (℃)
    brl_temp_steps: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'inj_stg': self.inj_stg,
            'inj_spd_steps': self.inj_spd_steps,
            'inj_pres_steps': self.inj_pres_steps,
            'inj_pos_steps': self.inj_pos_steps,
            'inj_t': self.inj_t,
            'inj_dly_t': self.inj_dly_t,
            'vps_mode': self.vps_mode,
            'vps_pos': self.vps_pos,
            'vps_t': self.vps_t,
            'vps_pres': self.vps_pres,
            'vps_spd': self.vps_spd,
            'hold_stg': self.hold_stg,
            'hold_pres_steps': self.hold_pres_steps,
            'hold_spd_steps': self.hold_spd_steps,
            'hold_time_steps': self.hold_time_steps,
            'hold_limit_spd': self.hold_limit_spd,
            'cool_t': self.cool_t,
            'met_stg': self.met_stg,
            'met_pres_steps': self.met_pres_steps,
            'met_rot_spd_steps': self.met_rot_spd_steps,
            'met_back_pres_steps': self.met_back_pres_steps,
            'met_pos_steps': self.met_pos_steps,
            'met_lim_t': self.met_lim_t,
            'pre_met_decomp_mode': self.pre_met_decomp_mode,
            'pre_met_decomp_pres': self.pre_met_decomp_pres,
            'pre_met_decomp_spd': self.pre_met_decomp_spd,
            'pre_met_decomp_t': self.pre_met_decomp_t,
            'pre_met_decomp_dist': self.pre_met_decomp_dist,
            'pst_met_decomp_mode': self.pst_met_decomp_mode,
            'pst_met_decomp_pres': self.pst_met_decomp_pres,
            'pst_met_decomp_spd': self.pst_met_decomp_spd,
            'pst_met_decomp_t': self.pst_met_decomp_t,
            'pst_met_decomp_dist': self.pst_met_decomp_dist,
            'met_end_pos': self.met_end_pos,
            'brl_temp_stg': self.brl_temp_stg,
            'noz_temp': self.noz_temp,
            'brl_temp_steps': self.brl_temp_steps,
        }


@dataclass
class MoldTempParams:
    """模温机工艺参数"""
    mold_temp: float = 50.0  # 模具温度 (℃)

    def to_dict(self) -> dict:
        return {'mold_temp': self.mold_temp}


@dataclass
class HotRunnerParams:
    """热流道工艺参数"""
    valve_num: int = 0  # 阀口数量
    valve_time_steps: List[float] = field(default_factory=list)  # 阀口时间

    def to_dict(self) -> dict:
        return {'valve_num': self.valve_num, 'valve_time_steps': self.valve_time_steps}


@dataclass
class ProductionParams:
    """
    完整生产工艺参数

    组合多个设备的工艺参数：
    - process: 注塑机工艺参数
    - mold_temp: 模温机工艺参数
    - hot_runner: 热流道工艺参数

    后续可扩展其他设备参数。
    """
    process: ProcessParams = field(default_factory=ProcessParams)
    mold_temp: MoldTempParams = field(default_factory=MoldTempParams)
    hot_runner: HotRunnerParams = field(default_factory=HotRunnerParams)

    def to_dict(self) -> dict:
        return {
            **self.process.to_dict(),
            **self.mold_temp.to_dict(),
            **self.hot_runner.to_dict(),
        }


# 别名
InitialParams = ProductionParams