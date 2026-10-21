"""
模糊推理常量定义

定义常见的常量、枚举、映射表等。
本文件从 `old/mdprocess/utils/fuzzykit/macros.py` 迁入必要的常量
"""

# === 缺陷名称常量集合（2026-10-20 补全）===
# 描述：用于在 FuzzyRule 词法解析时区分"工艺参数名称"与"缺陷名称"
# 构造时将工艺参数名与这些缺陷名比对，若在 set 里则看作缺陷条件
#
# 补全原因：原集合只含老 fuzzykit 遗留词（14 个），与 RuleKeyword 的
# defect 类（18 个）严重不一致。缺失的缺陷名会被 _classify_name 误判成
# "工艺参数"，进而被参数名收集逻辑当作参数收走 → RuleKeyword 里该缺陷
# 也变成一个"参数论域" → 规则的缺陷前件被当成可判级条件，而缺陷变量
# 根本没有数值，激活度被 EPSILON 压到 ~0，整类规则全部失活。
DEFECT_CONST = {
    # ---- 实际在用的 17 个缺陷（与 RuleKeyword.category='defect'、
    #      RuleMethod.defect_code 完全对齐，一个都不能少）----
    'ABERRATION',     # 异色 / 色差
    'AIRTRAP',        # 气穴 / 困气
    'BURN',           # 烧焦
    'FLASH',          # 飞边
    'GASVEINS',       # 气纹
    'GATEMARK',       # 浇口印
    'HARDDEMOLDING',  # 脱模不良
    'MATERIALFLOWER', # 料花
    'OVERSIZE',       # 尺寸偏大
    'SHADING',        # 阴阳面
    'SHORTSHOT',      # 短射
    'SHRINKAGE',      # 缩痕 / 缩水
    'TOPWHITE',       # 顶白
    'UNDERSIZE',      # 尺寸偏小
    'WARPING',        # 变形 / 翘曲
    'WATERRIPPLE',    # 水波纹
    'WELDLINE',       # 熔接线 / 熔接痕
    # ---- 无缺陷 sentinel（前端合法选项，本身不参与规则匹配）----
    'DEFECTFREE',     # 无缺陷
    # ---- 老 fuzzykit 遗留词（历史规则兼容，保留）----
    'WARPAGE',        # 翘曲（老写法，实际库用 WARPING）
    'BUBBLE',
    'BURN_MARK',
    'FLOW_MARK',
    'JET_MARK',
    'DELAMINATION',
    'GLOSS_VARIATION',
}

# === 映射字典（严重级别/动作 -> 整数映射）===
# 低/中/高 -> 0/1/2（表示隶属度等级索引）
# 动作映射：add -> +1 / reduce -> -1 / adjust -> -2（弹出标记）
#
# 'medium' 是前端 LEVEL_WORDS 与规则库 rule_description 实际使用的档位词，
# 老 fuzzykit 写的是 'mid'，两者同义（都指第 2 档），必须同时在表里，
# 否则规则前件 `X_medium` 查表会 KeyError。
HS_MAPPING_DICT = {
    'low': 0, 'mid': 1, 'medium': 1, 'high': 2,
    'level1': 0, 'level2': 1, 'level3': 2, 'level4': 3, 'level5': 4,
    'level6': 5, 'level7': 6, 'level8': 7, 'level9': 8,
    'add': 1, 'reduce': -1, 'adjust': -2,
}

# === 合法等级词全集（词法解析用）===
# 用途：判定规则前件的等级词是否可判级。
# 不在表里的词（如 'worse'——"该参数不合理"的人工判断词）无法映射到隶属度
# 等级索引，遇到时必须跳过而不是查表（否则 KeyError）。
ALL_LEVEL_WORDS = {
    'low', 'mid', 'medium', 'high', 'very_low', 'very_high',
    'extremely_low', 'extremely_high',
    *{f'level{i}' for i in range(1, 10)},
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

