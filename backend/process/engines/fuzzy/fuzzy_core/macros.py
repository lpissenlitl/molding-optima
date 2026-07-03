"""
模糊推理常量定义

定义常见的常量、枚举、映射表等。
本文件从 `old/mdprocess/utils/fuzzykit/macros.py` 迁入必要的常量
"""

# === 缺陷名称常量集合（老 fuzzykit 遗留）===
# 描述：用于在 FuzzyRule 词法解析时区分"工艺参数名称"与"缺陷名称"
# 构造时将工艺参数名与这些缺陷名比对，若在 set 里则看作缺陷条件
DEFECT_CONST = {
    'SHORTSHOT',    # 短射
    'FLASH',        # 飞边
    'SHRINKAGE',    # 缩痕
    'WELDLINE',     # 熔接线
    'ABERRATION',   # 异色
    'AIRTRAP',      # 气穴
    'TOPWHITE',     # 顶白
    'WARPAGE',      # 翘曲
    'BUBBLE',       # 气泡
    'BURN_MARK',    # 烧焦
    'FLOW_MARK',    # 流痕
    'JET_MARK',     # 喷射纹
    'DELAMINATION', # 分层
    'GLOSS_VARIATION', # 光泽不良
}

# === 映射字典（严重级别/动作 -> 整数映射）===
# 低/中/高 -> 0/1/2（表示隶属度等级索引）
# 动作映射：add -> +1 / reduce -> -1 / adjust -> -2（弹出标记）
HS_MAPPING_DICT = {
    'low': 0, 'mid': 1, 'high': 2,
    'level1': 0, 'level2': 1, 'level3': 2, 'level4': 3, 'level5': 4,
    'level6': 5, 'level7': 6, 'level8': 7, 'level9': 8,
    'add': 1, 'reduce': -1, 'adjust': -2,
}

# === 缺陷字典（数字 id -> 缺陷名称）===
HS_DEFECT_DICT = {
    1: 'SHORTSHOT',    # 短射
    2: 'FLASH',        # 飞边
    3: 'SHRINKAGE',    # 缩痕
    4: 'WELDLINE',     # 熔接线
    5: 'ABERRATION',   # 异色
    6: 'AIRTRAP',      # 气穴
    7: 'TOPWHITE',     # 顶白
}

# === 动动作名 -> 字串映射（补全 Action 用）===
ADJUST_ACTIONS = {
    'add': '增加',
    'reduce': '减少',
    'adjust': '提示',
    'add_pct': '增加百分比',
    'reduce_pct': '减少百分比',
}

# === 隶属度函数类型 ===
MEMBERSHIP_TYPES = [
    'gauss',           # 高斯（默认）
    'tri',             # 三角
    'trap',            # 梯形（预留）
]

# === 反模糊化方法 ===
DEFUZZ_METHODS = [
    'centroid',        # 重心法（推荐）
    'bisector',        # 均分面积法
    'mom',             # 最大隶属度均值
    'som',             # 最大隶属度取小
    'lom',             # 最大隶属度取大
]

# === 模糊等级 ===
FUZZY_LEVELS = {
    3: ['low', 'mid', 'high'],
    5: ['very_low', 'low', 'mid', 'high', 'very_high'],
}

# === 推理超参 ===
MIN_ACTIVATION_THRESHOLD = 0.01001     # 无效激活判定阈值
MAMDANI_SAMPLE_POINTS = 200            # Mamdani 输出值采样点
EPSILON = 1e-7                         # 防除零

