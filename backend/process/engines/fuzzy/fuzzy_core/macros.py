"""
模糊推理常量定义

定义常见的常量、枚举等
"""

# 缺陷类型
DEFECT_TYPES = [
    'short_shot',      # 短射
    'flash',           # 飞边
    'warpage',         # 翘曲
    'sink_mark',       # 缩痕
    'bubble',          # 气泡
    'burn_mark',       # 烧焦
    'flow_mark',       # 流痕
    'jet_mark',        # 喷射纹
    'delamination',    # 分层
    'gloss_variation', # 光泽不良
]

# 缺陷等级
DEFECT_LEVELS = [
    'light',    # 轻微
    'medium',   # 中等
    'severe',   # 严重
]

# 隶属度类型
MEMBERSHIP_TYPES = [
    'triangular',     # 三角形
    'trapezoidal',    # 梯形
    'gaussian',       # 高斯
    'bell',           # 钟形
    'singleton',      # 单点
]

# 模糊等级（3级或5级）
FUZZY_LEVELS = {
    3: {
        'low': (0, 0, 50),
        'medium': (30, 50, 70),
        'high': (50, 100, 100),
    },
    5: {
        'very_low': (0, 0, 25),
        'low': (0, 25, 50),
        'medium': (25, 50, 75),
        'high': (50, 75, 100),
        'very_high': (75, 100, 100),
    },
}

# 模糊运算方法
FUZZY_OPERATORS = [
    'min_max',      # min-max 运算
    'prod_sum',     # 乘积-求和运算
    'bounded',      # 有界运算
]

# 去模糊化方法
DEFUZZIFICATION_METHODS = [
    'centroid',     # 重心法
    'bisector',     #  bisector 法
    'mom',          # 最大隶属度均值法
    'lom',          # 最大隶属度取大法
    'som',          # 最大隶属度取小法
]
