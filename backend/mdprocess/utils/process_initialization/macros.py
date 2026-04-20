"""
初始工艺参数宏定义
"""
# 注射量与注塑机最大注射量的最小比值
HSO_Min_Inj_Vol_Rate = 0.25
# 注射量与注塑机最大注射量的最小比值
HSO_Max_Inj_Vol_Rate = 0.85
# 料筒加热各段之间梯度值(后段)
HSO_Compute_TMP_BACK_GRADS = 15.0
# 料筒加热各段之间梯度值(前段)
HSO_Compute_TMP_FRONT_GRADS = 10.0
# 注射压力与流长比关系
HSO_RATIO_PRESSURE_MAP = {
    50: 1.05,
    100: 1.03,
    150: 1.01,
    200: 1.00,
    250: 0.99,
    300: 0.97,
    350: 0.95
}
# 制品总重量与注射时间关系
# HSO_WEIGHT_TIME_MAP = {
#     50: 0.8,
#     100: 1.0,
#     250: 1.25,
#     500: 1.5,
#     1000: 1.75,
#     2000: 2.25,
#     4000: 3.0,
#     6000: 3.75,
# }

HSO_WEIGHT_TIME_MAP = {
    50: 1.6,
    100: 2,
    250: 2.5,
    500: 3,
    1000: 3.5,
    2000: 4.5,
    4000: 6,
    6000: 7.5,
}
# 射胶延迟时间（单位：s）
HSO_INJ_START_DELAY_TIME = 0.2
# 计量延迟时间（单位：s）
HSO_METER_START_DELAY_TIME = 0.5
# 中间时间（单位：s）
HSO_INTERVAL_TIME = 0.1
# 保压速度（单位：mm/s）
HSO_PACK_VELOCITY = 30.0
# 计量前减压速度（mm/s）
HSO_SUCKBACK_VELO_BEFORE_METER = 15.0
# 计量前减压距离（mm）
HSO_SUCKBACK_DIS_BEFORE_METER = 0.0
# 计量后减压速度（mm/s）
HSO_SUCKBACK_VELO_AFTER_METER = 15.0
# 计量后减压距离（mm）
HSO_SUCKBACK_DIS_AFTER_METER = 2.0
# 注射压力（速度）是注塑机最大注射压力（速度）的比例
HSO_Inject_Max_Ratio = 0.8
# 保压时间和注射时间的比值经验值
HSO_PackTime_InjTime_Ratio = 10.0
# 额外的冷却时间和注射时间的比值经验值
HSO_CoolTime_InjTime_Ratio = 10.0
# 保压压力（速度）和注射压力（速度）的比值经验值
HSO_PACK_INJ_PRES_RATIO = 0.85
# 保压压力的安全因子
HSO_PACK_SAFE_FACTOR = 0.8
# 实例工程误差20%
HSO_PROJECT_ERROR = 0.2
# PS的密度
HSO_PS_Density = 1.05
# π
HSO_PI = 3.141592
# 制品类型
# HSO_PRODUCT_TYPE = {
#     '1': 21,  # 普通型
#     '2': 35,  # 外观型
#     '3': 25,  # 精密型
#     '4': 30,  # 透明型
# }
HSO_PRODUCT_TYPE = {
    '普通型': 21,  # 普通型
    '外观型': 35,  # 外观型
    '精密型': 25,  # 精密型
    '透明型': 30,  # 透明型
}

# HSO_GATE_TYPE = {
#     '直浇口': lambda x: 0.5 + 0.1 * x,  # 直浇口
#     '点浇口': lambda x: 0.1,  # 点浇口
#     '侧浇口': lambda x: 0.1,  # 侧浇口
#     '护耳式浇口': lambda x: 0.5 + 0.1 * x,  # 护耳式浇口
#     '其他浇口': lambda x: 0.3 + 0.6 * (x ** 2),  # 其他浇口
# }

HS_MAPPING_DICT = {
    'low': 0,
    'mid': 1,
    'high': 2,
    'add': 1,
    'reduce': -1
}

HS_DEFECT_DICT = {
    1: 'SHORTSHOT',
    2: 'FLASH',
    3: 'BURN',
    4: 'DELAMINATION',
    5: 'RIPPLE',
    6: 'AIRBUBBLE',
    7: 'SHRINK',
    8: 'WELDLINE',
    9: 'WARPAGE',
    # 10: 'BUMPWHITE',
    11: 'DARK',
    12: 'HARDDEMOLDING',
    13: 'BADGLASS',
    14: 'OPACITY',
    15: 'TOPWHITE'
}
