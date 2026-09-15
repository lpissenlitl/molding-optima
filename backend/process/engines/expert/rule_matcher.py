"""
工艺参数初始化规则匹配器（数据库版）

数据源优先级：
    1. 数据库 ExpertRule（生产环境主路径）
    2. InitRuleLoader(JSON 文件)（本地/无 DB 场景）
    3. 内置 _BUILTIN_DEFAULTS（兜底）

匹配逻辑：
    - 按 priority 升序遍历（数字越小越优先）
    - 条件数组 AND 关系，空条件表示默认规则
    - 多条匹配规则深度合并 coefficients
"""

import logging
from typing import Dict, Any, Optional, List

from .rule_loader import InitRuleLoader

logger = logging.getLogger(__name__)


# ========== 内置兜底默认值 ==========
# 数据库与 JSON 都没数据时使用的硬编码兜底，
# 与 expert_rules.json 的 DEFAULT 规则保持完全一致。
_BUILTIN_DEFAULTS: Dict[str, Any] = {
    'injection': {
        'inj_pres_ratio': 0.65,
        # 材料分支默认（其他材料）
        'inj_velo_ratio_thin': 0.35,
        'inj_velo_ratio_thick': 0.42,
        'inj_ratio_threshold': 100,
        'inj_ratio_coef': 500.0,
        # 注射时间物理化默认值（与 expert_rules.json DEFAULT 保持一致）
        'thickness_bucket_thresholds': [1.5, 3.0],
        'default_thickness_bucket': 'medium',
        'default_time_window': [0.6, 2.5],
        'family_time_window': {
            'PP':   {'thin': [0.6, 1.6], 'medium': [0.8, 2.5], 'thick': [1.2, 4.0]},
            'PE':   {'thin': [0.6, 1.6], 'medium': [0.8, 2.5], 'thick': [1.2, 4.0]},
            'PS':   {'thin': [0.6, 1.8], 'medium': [0.8, 2.8], 'thick': [1.5, 4.5]},
            'ABS':  {'thin': [0.5, 1.5], 'medium': [0.6, 2.5], 'thick': [1.0, 4.0]},
            'PC':   {'thin': [0.5, 1.5], 'medium': [0.6, 2.5], 'thick': [1.0, 4.0]},
            'PA':   {'thin': [0.5, 1.4], 'medium': [0.6, 2.0], 'thick': [1.0, 3.5]},
            'POM':  {'thin': [0.6, 1.8], 'medium': [0.8, 2.8], 'thick': [1.2, 4.0]},
            'PMMA': {'thin': [0.6, 1.8], 'medium': [0.8, 2.5], 'thick': [1.2, 4.0]},
            'PET':  {'thin': [0.6, 1.8], 'medium': [0.8, 2.5], 'thick': [1.2, 4.0]},
            'PBT':  {'thin': [0.6, 1.8], 'medium': [0.8, 2.5], 'thick': [1.2, 4.0]},
        },
    },
    'vp_switch': {
        'base_posi_small': 10,
        'base_posi_large': 15,
        'base_posi_threshold_weight': 120,
        # === 算法 #9：VP 切换模式推荐（v3.1：3 级兜底 + 4 种模式）===
        # 行业标准系数（可被企业配置覆盖）
        'time_switch_ratio': 0.95,   # mode=1 时 vps_t = inj_time × time_switch_ratio
        'pres_switch_ratio': 0.85,   # mode=2 时 vps_pres = inj_pres × pres_switch_ratio
    },
    'holding': {
        # 保压压力物理化默认值（与 expert_rules.json DEFAULT 保持一致）
        # 四维半经验物理方法：材料 × 壁厚 × 浇口 × 流道
        'family_hold_ratio': {
            'PP': 0.50, 'PE': 0.50, 'PS': 0.55, 'ABS': 0.60, 'AS': 0.55,
            'PMMA': 0.60, 'PET': 0.65, 'PBT': 0.65, 'PA': 0.70, 'POM': 0.75, 'PC': 0.75,
        },
        'default_hold_ratio': 0.60,
        'thickness_factor': {'thin': 0.95, 'medium': 1.00, 'thick': 1.10},
        'gate_factor': {
            '直浇口': 0.95, '护耳式浇口': 1.00, '点浇口': 1.10, '侧浇口': 1.00,
        },
        'runner_factor': {
            '热流道': 0.95, '热转冷': 1.00, '冷流道': 1.05,
        },
        'max_safe_hold_ratio': 0.95,
        'hold_pres_inj_ratio_min': 0.40,
        'hold_pres_inj_ratio_max': 0.85,
        # === 保压速度（#7 三维物理化）===
        # 维度 1: family_velo_ratio（材料临界剪切速率等级）
        'family_velo_ratio': {
            'PP': 0.30, 'PE': 0.30,
            'PS': 0.25,
            'ABS': 0.20, 'AS': 0.20,
            'PMMA': 0.18,
            'PA': 0.15, 'POM': 0.15,
            'PC': 0.12, 'PBT': 0.12,
            'PET': 0.10,
        },
        'default_velo_ratio': 0.15,
        # 维度 2: gate_factor_hold_velo（浇口尺寸修正，3 桶）
        'gate_factor_hold_velo': {
            'thin': 0.90,
            'medium': 1.00,
            'thick': 1.10,
        },
        # 维度 3: max_safe_hold_velo_ratio（机器上限钳制，行业共识 30%）
        'max_safe_hold_velo_ratio': 0.30,
        # === 保压时间（#8 五维物理化）===
        # hold_time_min / hold_time_max 仅供 GATE_* 兜底公式使用
        # 新算法使用 family_hold_time_max[family] 作为上限
        'hold_time_min': 2.0,
        'hold_time_max': 10.0,
        # 维度 1：family × 壁厚浇口冻结时间（基于 Fourier 热扩散 t ≈ h²/α_eff）
        'family_gate_freeze_time': {
            'PP':   {'thin': 3.6, 'medium': 12.5, 'thick': 50.0},
            'PE':   {'thin': 3.6, 'medium': 12.5, 'thick': 50.0},
            'PS':   {'thin': 5.3, 'medium': 18.8, 'thick': 75.0},
            'ABS':  {'thin': 5.3, 'medium': 18.8, 'thick': 75.0},
            'AS':   {'thin': 5.3, 'medium': 18.8, 'thick': 75.0},
            'PMMA': {'thin': 5.3, 'medium': 18.8, 'thick': 75.0},
            'PC':   {'thin': 6.4, 'medium': 22.5, 'thick': 90.0},
            'PET':  {'thin': 8.5, 'medium': 30.0, 'thick': 120.0},
            'PBT':  {'thin': 6.4, 'medium': 22.5, 'thick': 90.0},
            'PA':   {'thin': 7.5, 'medium': 26.5, 'thick': 105.9},
            'POM':  {'thin': 4.6, 'medium': 16.1, 'thick': 64.3},
        },
        'default_freeze_time': {'thin': 5.3, 'medium': 18.8, 'thick': 75.0},
        # 维度 2：保压时间场景浇口修正因子（与 #6 保压压力方向相反）
        'gate_factor_hold_time': {
            '直浇口': 1.20, '护耳式浇口': 1.05, '侧浇口': 0.85, '点浇口': 0.70,
        },
        # 维度 4：模温修正因子（4 桶）
        'mold_temp_factor_hold_time': {
            'low': 0.95, 'medium': 1.00, 'high': 1.10, 'ultra_high': 1.20,
        },
        # 维度 5：结晶动力学拉长因子（半结晶 family 显著）
        'crystallinity_kick': {
            'PET': 1.80, 'PBT': 1.50, 'PA': 1.40, 'POM': 1.30,
            'PP': 1.10, 'PE': 1.05,
            'PC': 1.00, 'PS': 1.00, 'ABS': 1.00, 'AS': 1.00, 'PMMA': 1.00,
        },
        # family 自适应保压时间上限（**关键**：移除 10s 硬上限）
        'family_hold_time_max': {
            'PP': 30.0, 'PE': 30.0, 'PS': 60.0, 'ABS': 60.0, 'AS': 60.0, 'PMMA': 60.0,
            'PC': 60.0, 'POM': 60.0, 'PBT': 120.0, 'PA': 120.0,
            'PET': 600.0,
        },
        'default_hold_time_max': 300.0,
        # GATE_* 兜底公式系数（保留兼容旧数据）
        'hold_time_strategy': 'quadratic',
        'hold_time_linear_a': 0.5,
        'hold_time_linear_b': 0.1,
        'hold_time_area_coef': 2.0,
        'hold_time_quadratic_a': 0.3,
        'hold_time_quadratic_b': 0.6,
    },
    'cooling': {
        # === 算法 #10：冷却参数物理化（v1.0：4 维物理化）===
        # 推导公式：t_cool = max_thickness² × family_cool_factor × ΔT_factor × crystallinity_kick
        # 物理依据：Fourier 热扩散 t ∝ h²/α × ln((T_melt-T_mold)/(T_eject-T_mold))
        # 物理正交：与 #8 保压时间正交（局部 vs 整体）
        # 详见 _dev_refs/2026-07-05-cool-time-physics-design.md
        'cool_time_min': 5.0,
        'else_time': 1.5,
        # 材料系数（11 family × 1 系数，行业共识 Tederic 2026 / Moldflow / 海天工艺手册）
        'family_cool_factor': {
            'PP': 0.9, 'PE': 0.9,         # 易冷（无定形倾向 + 低 Tg）
            'PS': 1.0,                    # 无定形中位
            'ABS': 1.1, 'AS': 1.1,        # 无定形稍慢（玻璃化转变影响）
            'PMMA': 1.3,                  # 玻璃化转变较慢
            'PA': 1.6, 'POM': 1.6,        # 半结晶 + 中等结晶潜热
            'PBT': 1.7,                   # 半结晶 + 稍高黏度
            'PC': 1.8,                    # 高黏度无定形慢冷
            'PET': 2.0,                   # 半结晶 + 高结晶潜热（瓶盖长冷却）
        },
        'default_cool_factor': 1.2,       # 未知材料保守中位
        # 结晶拉长因子（半结晶 vs 无定形 二分）
        'crystallinity_kick': {
            'crystalline': 1.15,          # 半结晶（释放结晶潜热）
            'amorphous': 1.00,            # 无定形（无潜热）
        },
        'default_crystallinity_kick': 1.10,  # 未知 category 保守拉长
    },
    'metering': {
        # v1.0 base_ratio（保留原有字段用于向后兼容）
        'meter_pres_ratio_straight': 0.55,
        'meter_pres_ratio_locking': 0.6,
        # v1.0 钳制范围（同源数值，不假设 MPa）
        'meter_pres_min': 3.0,
        'meter_pres_max': 18.0,
        # v1.0 family 黏度修正系数（相对比例，default=1.0）
        # 物理依据：PP/PS/PVC 低黏度 < ABS/POM/PC 中黏度 < PA66/PA6 高黏度+吸湿
        'family_meter_viscosity': {
            # 低黏度结晶（推荐 5–8）
            'PP': 0.6, 'PE': 0.6, 'LDPE': 0.6, 'HDPE': 0.6, 'LLDPE': 0.6,
            # 非晶态低黏度
            'PS': 0.7,
            # 剪切敏感（推荐 4–8）
            'PVC': 0.5,
            # 中等黏度（推荐 8–12）
            'ABS': 1.0, 'POM': 1.0,
            # 高黏度（推荐 5–10）
            'PC': 1.0, 'PMMA': 1.0,
            # 吸湿高黏度（推荐 12–18）
            'PA6': 1.2, 'PA66': 1.3, 'PA': 1.2,
            # 结晶+黏度适中（推荐 8–12）
            'PET': 1.0, 'PBT': 1.0,
            # 复合配方
            'PC+ABS': 1.0, 'PC/ABS': 1.0,
        },
        'default_family_meter_viscosity': 1.0,
        # v1.0 喷嘴类型修正系数
        # 物理依据：锁闭喷嘴有止逆阀增加阻力，需更高油压
        'nozzle_factor': {
            '直通型': 1.00,
            '锁定型': 1.10,
        },
        'default_nozzle_factor': 1.00,
        # 其他计量参数（保留原有逻辑）
        'meter_speed_temp_ratio_min': 0.3,
        'meter_speed_temp_ratio_max': 0.75,
        'screw_speed_factor': 60.0,
        # v1.0 family 剪切敏感度修正系数（计量螺杆转速 #12）
        # 物理依据：不同材料剪切降解敏感度差异大
        # - PVC/POM：严重降解（HCl / 甲醛释放）→ 偏保守（0.50~0.65）
        # - PC/PA66：高黏度 → 偏保守（0.50~0.55）
        # - ABS/PS：中等黏度 → 基准 1.00
        # - PP/PE：流动性好 → 可偏高（1.10）
        'family_meter_shear_ratio': {
            # 低黏度结晶（流动性好 → 可偏高）
            'PP': 1.10, 'PE': 1.10, 'LDPE': 1.10, 'HDPE': 1.10, 'LLDPE': 1.10,
            # 非晶态低黏度
            'PS': 1.00,
            # 剪切敏感（严重降解 → 偏保守）
            'PVC': 0.50, 'POM': 0.65,
            # 中等黏度（基准 1.00）
            'ABS': 1.00, 'PMMA': 1.00, 'PBT': 1.00, 'PET': 1.00,
            # 高黏度（防剪切降解 → 偏保守）
            'PC': 0.55, 'PA6': 0.55, 'PA66': 0.50, 'PA': 0.55,
            # 复合配方
            'PC+ABS': 0.65, 'PC/ABS': 0.65,
        },
        'default_family_meter_shear_ratio': 1.0,
        # v1.0 L/D 修正系数（计量螺杆转速 #12）
        # 物理依据：螺杆长径比影响塑化路径长度与停留时间
        # - L/D < 18（short）：塑化路径短、停留时间不足 → 微升（1.05）
        # - 18 ≤ L/D ≤ 22（standard）：海天/震雄主流机型 → 基准 1.00
        # - L/D > 22（long）：塑化路径长、防过剪切降解 → 微降（0.95）
        'ld_correction': {
            'short': 1.05,       # < 18
            'standard': 1.00,    # 18 ≤ L/D ≤ 22
            'long': 0.95,        # > 22
        },
        'ld_thresholds': [18, 22],
        'default_ld_correction': 1.00,  # 字段缺失兜底（不修正）
    },
    'back_pressure': {
        # v1.0 钳制范围（基于材料物理耐受度，非设备能力）
        # - 下限 0.5 MPa：PA66 下限 2.0 的 25% 安全余量（避免材料水解）
        # - 上限 30.0 MPa：PMMA 上限 28 的 7% 安全余量（避免剪切降解）
        'meter_back_pres_min': 0.5,
        'meter_back_pres_max': 30.0,
        # v1.0 recommend_back_pressure 缺失兑底（行业中位 10.0 MPa）
        'default_recommend_back_pressure': 10.0,
        # v1.0 family 排气需求修正系数（计量背压 #13）
        # 物理依据：不同材料排气需求与物理耐受度差异巨大
        # - PMMA=1.50（高黏度需强排气）
        # - PA66=0.40（极易水解，不能高背压）
        # - PA6=0.60（吸湿）
        # - PVC=0.50（剪切敏感，防 HCl 释放）
        'family_back_pres_factor': {
            # 低黏度结晶（流动性好，结晶型需密度均匀）
            'PP': 1.00, 'PE': 1.00, 'LDPE': 1.00, 'HDPE': 1.00, 'LLDPE': 1.00,
            # 低黏度非晶
            'PS': 0.90, 'HIPS': 0.90,
            # 剪切敏感（严重降解 → 不能高背压）
            'PVC': 0.50,
            # 中等黏度（基准 1.00）
            'ABS': 1.00, 'PBT': 0.95, 'PET': 0.95,
            # 高黏度（PMMA=1.50 需强排气；POM=0.85 甲醛释放；PC=1.30 热敏高黏度）
            'PMMA': 1.50, 'POM': 0.85, 'PC': 1.30,
            # 吸湿高黏度（PA6=0.60、PA66=0.40 不能高背压）
            'PA6': 0.60, 'PA66': 0.40, 'PA': 0.60,
            # 复合配方
            'PC+ABS': 1.10, 'PC/ABS': 1.10,
        },
        'default_family_back_pres_factor': 1.0,
        # v1.0 螺杆转速联动修正系数（计量背压 #13）
        # 物理依据：转速越高 → 熔体停留时间越短 → 密度均匀性越差 → 需更高背压补偿
        # 公式：speed_factor = 1.0 + slope × (rpm_ratio - base)
        'speed_factor_base': 0.5,        # speed_factor=1.0 对应的 rpm_ratio 中位
        'speed_factor_slope': 0.3,       # rpm_ratio 偏离 base 时的斜率
        'speed_factor_min': 0.85,        # 钉制下限
        'speed_factor_max': 1.15,        # 钉制上限
        'default_speed_factor': 1.0,     # rpm_ratio 缺失兑底（不修正）
    },
    # 🆕 v1.1 松退参数族（#15-#18）：5 维物理化
    # 设计依据：2026-07-05-suckback-decompression-physics-design.md
    # - 压力 P：base_ratio × family × mode_factor × nozzle_factor（仅液压机）
    # - 距离 D：base_dist × family × nozzle × runner × gate（5 维）
    # - 速度 V：max_decomp_velo × family × nozzle（3 维）
    # - 时间 T：距离 / 速度（派生）
    # - runner_factor 与 #6 保压压力方向相反（松退↑ 热流道 / 保压↓ 热流道）
    'suckback': {
        # 钳制范围
        'min_pressure': 1.0,            # MPa（液压机最小油压）
        'max_pressure': 5.0,            # MPa（业内实测上限）
        'min_dist': 1.0,                # mm
        'max_dist': 12.0,               # mm（🆕 v1.1：6.0→12.0 覆盖热流道+针阀式）
        'min_velo': 3.0,                # mm/s（防拉丝下限）
        'max_velo': 50.0,               # mm/s（防爆上限）
        'min_time': 0.1,                # s
        'max_time': 5.0,                # s

        # 基础值
        'base_ratio': 0.25,             # 松退压力 / max_set_metering_pressure（业内中位）
        'base_dist': 3.5,               # mm（业内中位）
        'pre_mode_factor': 0.80,        # 前松退压力修正（冷料局部点抗力小）
        'post_mode_factor': 1.00,       # 后松退压力修正（高温熔体连续流阻基准）

        # family 距离修正（4 档）
        'family_dist_factor': {
            # 高黏度（摩控生热偏高，距离偏小）
            'PC': 0.80, 'PMMA': 0.80, 'POM': 0.80,
            # 吸湿（排气料筒场景规格，防吸入空气）
            'PA66': 0.65, 'PA6': 0.65, 'PA': 0.65,
            # 基准（流动性好）
            'PP': 1.00, 'PE': 1.00, 'LDPE': 1.00, 'HDPE': 1.00, 'LLDPE': 1.00,
            'PS': 1.00, 'HIPS': 1.00, 'ABS': 1.00, 'PET': 1.00, 'PBT': 1.00,
            # 低黏度（高流动性易流涎）
            'PVC': 1.20,
            # 共混
            'PC+ABS': 1.00, 'PC/ABS': 1.00,
        },
        'default_family_dist_factor': 1.0,

        # family 速度修正（4 档）
        'family_velo_factor': {
            'PC': 0.75, 'PMMA': 0.75, 'POM': 0.75,
            'PA66': 0.85, 'PA6': 0.85, 'PA': 0.85,
            'PP': 1.00, 'PE': 1.00, 'LDPE': 1.00, 'HDPE': 1.00, 'LLDPE': 1.00,
            'PS': 1.00, 'HIPS': 1.00, 'ABS': 1.00, 'PET': 1.00, 'PBT': 1.00,
            'PVC': 1.10,
            'PC+ABS': 1.00, 'PC/ABS': 1.00,
        },
        'default_family_velo_factor': 1.0,

        # 🆕 v1.1：流道类别修正（与 #6 保压 runner_factor 方向相反）
        # 松退关心"流道残余压力释放" → 热流道需更大吸回距离
        'runner_factor': {
            '冷流道':   1.00,    # 流道已凝固，松退只需处理喷嘴
            '热转冷':   1.15,    # 主流道热、分流道冷，残余压力部分释放
            '热流道':   1.60,    # 流道全程熔融 → 残余压力需传递更远
        },
        'default_runner_factor': 1.0,

        # 🆕 v1.1：浇口结构修正（仅热流道生效）
        'gate_factor': {
            '针阀式点浇口': 1.70,    # 针阀关闭不彻底，残余压力最大
            '针阀式侧浇口': 1.70,    # 同上
            '点浇口':       1.30,    # 浇口小，残余压力较大
            '侧浇口':       1.00,    # 开放浇口，残余压力易释放
            '直浇口':       1.00,    # 同上
            '护耳式浇口':   1.00,    # 同上
        },
        'default_gate_factor': 1.0,
        'gate_factor_applies_to_runner': ['热流道'],   # 仅热流道叠加 gate_factor

        # 喷嘴修正
        'nozzle_dist_factor': {
            '直通型': 0.95,
            '锁闭型': 1.10,
        },
        'default_nozzle_dist_factor': 1.0,
        'nozzle_velo_factor': {
            '直通型': 1.00,
            '锁闭型': 0.80,
        },
        'default_nozzle_velo_factor': 1.0,

        # #15+#16 模式逻辑
        'pre_decomp_default_mode': 0,    # 默认关（仅在启用时推导前松退参数）
        'pst_decomp_default_mode': 1,    # 默认距离模式

        # 全电机分支默认
        'electric_default_dist': 3.5,
        'electric_default_velo': 20.0,
        'electric_default_pressure': 0.0,
    },

    # 向后兼容：保留旧 decompression 键（仅作为 alias 跳转到 suckback）
    'decompression': {
        'pre_decomp_mode': 0,
        'pst_decomp_mode': 1,
        'decomp_dist_ratio': 0.1,
        'decomp_dist_min': 2.0,
        'decomp_dist_max': 12.0,        # 🆕 v1.1 同步更新
    },
    'nozzle': {                              # 🆕 v1.0 #19 喷嘴温度（2 维物理化：nozzle_offset + family_offset）
        'noz_offset_straight': -5.0,         # 直通喷嘴基准（防流诞）
        'noz_offset_locking':   0.0,         # 锁闭喷嘴基准（防阀芯冷凝）
        'family_offset': {                    # 17 family 差异化（PA +5℃、PET/PBT +3℃、PVC -5℃）
            # 注：_parse_family 把 PA66/PA6 归为 PA，所以这里只以 PA 为 key
            'PA':  +5.0,                                       # PA66/PA6/PA 大类 +5℃（防含水率/结晶冷凝）
            'PET': +3.0, 'PBT': +3.0,                         # 结晶型冷凝阻塞 +3℃
            'PC':   0.0,  'PMMA': 0.0, 'POM': 0.0,            # 高黏度持平
            'PP':   0.0,  'PE':   0.0,  'PS':  0.0, 'ABS': 0.0,
            'AS':   0.0,  'HDPE': 0.0,  'LDPE': 0.0, 'LLDPE': 0.0,
            'PVC':  -5.0,                                      # 热敏防 HCl 析出
        },
        'family_offset_default': 0.0,
        'noz_temp_clamp_tolerance': 10.0,    # 钳制容差（±10℃）
    },
    'barrel': {                              # 🆕 v1.0 #20 料筒温度分布（4 维物理化：family_decrement × stages × 幂函数k × 双层边界钳制）
        'family_decrement': {                 # 17 family 递减梯度（PVC 5℃、PC/PMMA/POM/PA/PET/PBT 8℃、PP/PE/ABS/PS 10℃）
            'PVC':   5.0,                     # 极平缓防分解
            'PC':    8.0,  'PMMA': 8.0, 'POM': 8.0,  # 高黏度平缓防降解
            'PA':    8.0,                     # PA 大类 8℃（PA66/PA6/PA）
            'PET':   8.0,  'PBT':   8.0,
            'PP':   10.0,  'PE':   10.0, 'PS': 10.0, 'ABS': 10.0,
            'AS':   10.0,  'HDPE': 10.0, 'LDPE': 10.0, 'LLDPE': 10.0,
            # 其他 family 默认 10.0
        },
        'family_decrement_default': 10.0,
        'stages_threshold': 7,                # 段数阈值（>threshold 走细颗粒）
        'high_stages_factor': 0.8,            # >7 段时 × 0.8（细颗粒）
        'high_stages_clamp': 8.0,             # 细颗粒上限（不超 8℃ 与 PC 平缓对齐）
        'power_k': 1.2,                       # 幂函数指数（非线性）
        # 边界钳制（双层）
        'segment_1_upper_offset':  5.0,       # 段 1 上限（melt+5℃）
        'segment_1_lower_offset': -5.0,       # 段 1 下限（melt-5℃）
        'segment_N_lower_min':    -60.0,      # 段 N 下限（melt-60℃）
        'segment_N_lower_min_tg_plus': 30.0,  # 段 N 下限（Tg+30℃）
        'segment_N_upper_offset': -5.0,       # 段 N 上限（melt-5℃）
    },
    'mold_temp': {
        'PP': 40, 'PC': 80, 'ABS': 50, 'PC+ABS': 70, 'PC/ABS': 70,
        'PS': 40, 'PE': 40, 'LDPE': 40, 'HDPE': 40, 'LLDPE': 40,
        'PVC': 40, 'PA6': 60, 'PA66': 70, 'PA': 60, 'PET': 90,
        'default': 50,
    },
}


class InitRuleMatcher:
    """初始化规则匹配器（数据库版）

    Usage:
        matcher = InitRuleMatcher()
        coeffs = matcher.match({'polymer': {...}, 'product': {...}})
        inj_pres = max_inj_pres * coeffs['injection']['inj_pres_ratio']
    """

    def __init__(self, library_code: str = 'expert_rules'):
        self.library_code = library_code
        self._cached_rules: Optional[List[Dict[str, Any]]] = None
        # 最近一次 match 命中的规则代码列表（按 priority 顺序）
        self.last_matched_codes: List[str] = []

    def match(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """匹配规则并返回合并后的嵌套系数字典

        Args:
            context: 匹配上下文
                {
                    'polymer': {'abbreviation': 'ABS', ...},
                    'product': {'gate_type': '点浇口', 'ave_thickness': 2.0, ...},
                    'machine': {...},
                }

        Returns:
            合并后的嵌套系数字典，结构如：
            {
                'injection': {'inj_pres_ratio': 0.65, ...},
                'holding':   {'hold_pres_base_ratio': 0.25, ...},
                ...
            }

        副作用：
            self.last_matched_codes 被填充为本次命中规则代码列表（按 priority 升序）。
        """
        self.last_matched_codes = []
        rules = self._load_rules()

        if not rules:
            return self._build_fallback(context)

        # 按 priority 升序排序
        sorted_rules = sorted(rules, key=lambda r: r.get('priority', 9999))

        matched_coefficients: Dict[str, Any] = {}

        for rule in sorted_rules:
            if not rule.get('is_active', True):
                continue
            if self._match_conditions(rule.get('conditions', []), context):
                matched_coefficients = self._merge_coefficients(
                    matched_coefficients,
                    rule.get('coefficients', {}),
                )
                code = rule.get('rule_code')
                if code:
                    self.last_matched_codes.append(code)

        logger.debug(f"InitRuleMatcher 命中规则: {self.last_matched_codes}")

        # 用内置默认兜底，确保所有必要键都存在
        return self._merge_coefficients(_BUILTIN_DEFAULTS, matched_coefficients)

    def reload(self) -> None:
        """清除缓存，强制下次 match 时重新加载"""
        self._cached_rules = None

    # ========== 数据加载 ==========

    def _load_rules(self) -> List[Dict[str, Any]]:
        """加载规则：先 DB，后 JSON；都不行返回空"""
        if self._cached_rules is not None:
            return self._cached_rules

        # 1. 数据库
        rules = self._load_from_db()
        if rules:
            logger.info(f"InitRuleMatcher: 从数据库加载 {len(rules)} 条规则")
            self._cached_rules = rules
            return rules

        # 2. JSON 文件
        rules = self._load_from_json()
        if rules:
            logger.info(f"InitRuleMatcher: 从 JSON 加载 {len(rules)} 条规则")
            self._cached_rules = rules
            return rules

        logger.warning("InitRuleMatcher: 数据库和 JSON 均无可用规则，将使用内置默认值")
        return []

    def _load_from_db(self) -> List[Dict[str, Any]]:
        try:
            from process.models.rules import RuleLibrary  # noqa
        except Exception as e:
            logger.debug(f"InitRuleMatcher: 导入 RuleLibrary 失败: {e}")
            return []

        try:
            library = RuleLibrary.objects.filter(
                library_code=self.library_code,
                is_active=True,
            ).first()
            if not library:
                return []

            qs = library.expert_rules.filter(is_active=True).values(
                'rule_code', 'rule_name', 'priority', 'is_active',
                'conditions', 'coefficients',
            )
            rules = list(qs)
            return rules
        except Exception as e:
            logger.warning(f"InitRuleMatcher: 数据库加载失败: {e}")
            return []

    def _load_from_json(self) -> List[Dict[str, Any]]:
        try:
            loader = InitRuleLoader()
            return loader.get_all_rules()
        except Exception as e:
            logger.warning(f"InitRuleMatcher: JSON 加载失败: {e}")
            return []

    # ========== 匹配逻辑（复用 InitRuleLoader 的实现） ==========

    @staticmethod
    def _match_conditions(conditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        """所有条件 AND 满足返回 True；无条件规则始终匹配"""
        if not conditions:
            return True

        for cond in conditions:
            field = cond.get('field', '')
            operator = cond.get('operator', 'exact')
            value = cond.get('value')
            field_value = InitRuleMatcher._get_field_value(field, context)
            if field_value is None:
                return False
            if not InitRuleMatcher._compare(field_value, operator, value):
                return False
        return True

    @staticmethod
    def _get_field_value(field: str, context: Dict[str, Any]) -> Any:
        """从上下文中提取字段值，支持嵌套字段（polymer.abbreviation 形式）"""
        parts = field.split('.')
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
            if value is None:
                return None
        return value

    @staticmethod
    def _compare(field_value: Any, operator: str, target: Any) -> bool:
        """单条件比较"""
        try:
            if operator == 'exact':
                return field_value == target
            if operator == 'in':
                return field_value in target
            if operator == 'not_in':
                return field_value not in target
            if operator == 'gte':
                return field_value >= target
            if operator == 'lte':
                return field_value <= target
            if operator == 'gt':
                return field_value > target
            if operator == 'lt':
                return field_value < target
        except TypeError:
            return False
        return False

    @staticmethod
    def _merge_coefficients(base: Dict[str, Any], addition: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并：嵌套 dict 递归合并，标量值由 addition 覆盖 base"""
        result = {k: v for k, v in (base or {}).items()}
        for key, value in (addition or {}).items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = InitRuleMatcher._merge_coefficients(result[key], value)
            else:
                result[key] = value
        return result

    # ========== 兜底 ==========

    def _build_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """DB 与 JSON 都拿不到数据时的纯内置默认值"""
        return {k: {kk: vv for kk, vv in v.items()} for k, v in _BUILTIN_DEFAULTS.items()}