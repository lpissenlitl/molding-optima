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

# === 动作映射（动作名 -> 整数符号）===
# 含义：add=+1（增加）、reduce=-1（减少）、adjust=-2（提示，不改数值）。
# 这是【动作】语义，与档位（level）无关，与字段的模糊等级数也无关，
# 因此单独成表，不与档位词表混在一起。
ACTION_MAP = {
    'add': 1, 'reduce': -1, 'adjust': -2,
}

# === 桶编号表（levelN -> 桶索引）===
# 语义：levelN = “该字段论域内的第 N 个分位”，桶索引恒为 N-1
#      （1-based 编号 → 0-based 下标）。
# 关键性质：与字段的模糊等级数**解耦**——只要 N ≤ 该字段的等级数，
#      就一定落在合法桶上。这是旧版 fuzzykit 的原设计（当年混在
#      HS_MAPPING_DICT 里），拆出来独立成表：它表达的是“编号”，
#      不是“档位语义”。
# 与 LEVEL_WORDS_BY_LVL 的关系：levelN 的 N 就是该字段词表里的第 N 个词。
#      两者互补——编号形式负责精确定位，语义词形式负责可读性。
LEVEL_NUMBER_TO_BUCKET = {f'level{i}': i - 1 for i in range(1, 10)}

# === 档位映射（已弃用：HS_ 前缀 + 全局静态表）===
# 2026-10-22：
# - `HS_` 前缀是老 HsMoldingService 的缩写，随 fuzzykit 迁入时保留下来，现已弃用。
# - 本表已按语义拆分为三块：
#     ACTION_MAP           动作（add/reduce/adjust）——与档位、级数无关
#     LEVEL_NUMBER_TO_BUCKET 桶编号（level1..level9）——与级数解耦，永远正确
#     下方字典字面量       档位词（low/mid/medium/high）——全局静态 3 档口径，
#                          在 5/7/9 档字段上会错位一档
# - 档位词那部分的正确做法是 `resolve_bucket(lvl, level_word)`
#   （按字段自己的词表定位）。本表暂留仅为过渡期兼容
#   （诊断脚本会 monkeypatch 本表做 A/B 对照），接线完成后整表删除。
# @deprecated
HS_MAPPING_DICT = {
    'low': 0, 'mid': 1, 'medium': 1, 'high': 2,
    **LEVEL_NUMBER_TO_BUCKET,
    **ACTION_MAP,
}

# === 档位词表（按字段的模糊等级数）===
# 2026-10-22 E2：这是档位词的**唯一权威定义**。
#
# 词表下标 = 该字段的桶索引（0-based）。
# 硬约束 1：len(词表) == lvl  —— 桶数必须等于等级数。
# 硬约束 2：每张词表都必须含 low / medium / high 三个核心词
#            —— 现有规则库 1646 条用的就是这三个词，缺一个就整类规则无法解析。
#
# 各核心词的物理位置（占论域的百分比）：
#   3 档：low=0%    medium=50%  high=100%   ← 粗粒度，low/high 压在论域两端
#   5 档：low=25%   medium=50%  high=75%
#   7 档：low=33%   medium=50%  high=67%
#   9 档：low=25%   medium=50%  high=75%
#
# 注意 3 档的 low/high 落在两端（更极端），5/7/9 档落在中间（更温和）。
# 这是“级数越多、档位越细”的必然结果：同一个 `X_high` 在 3 档字段上
# 要求接近论域上界，在 5 档字段上只要求高于中位。不是错误，但会影响
# 跨级数字段的规则激活严格程度。
LEVEL_WORDS_BY_LVL = {
    3: ('low', 'medium', 'high'),
    5: ('very_low', 'low', 'medium', 'high', 'very_high'),
    7: ('extremely_low', 'very_low', 'low', 'medium', 'high', 'very_high', 'extremely_high'),
    9: ('extremely_low', 'very_low', 'low', 'ultra_low', 'medium',
        'ultra_high', 'high', 'very_high', 'extremely_high'),
}

# 别名词：老 fuzzykit 写 'mid'，规则库与前端写 'medium'，同义（第 2 档）
LEVEL_WORD_ALIASES = {'mid': 'medium'}

# === 合法等级词全集（词法解析用）===
# 用途：判定规则前件的等级词是否可判级。
# 不在表里的词（如 'worse'——"该参数不合理"的人工判断词）无法映射到隶属度
# 等级索引，遇到时必须跳过而不是查表（否则 KeyError）。
#
# 2026-10-22 E2：由 LEVEL_WORDS_BY_LVL 派生，消除“前端 LEVEL_WORDS /
# 后端 FUZZY_LEVELS / 引擎 HS_MAPPING_DICT”三处词表分叉。
# level1..9 是编号档位词，与词表并行（双轨）。
ALL_LEVEL_WORDS = {
    *{w for words in LEVEL_WORDS_BY_LVL.values() for w in words},
    *LEVEL_WORD_ALIASES,                       # 别名也要能被词法层认出
    *{f'level{i}' for i in range(1, 10)},
}

# 多段档位词（'very_low' / 'extremely_low' / 'slightly_low' ...）
# split_phase 用它做“最长后缀”匹配：'IV0_very_low' → name='IV0', level='very_low'
MULTI_SEGMENT_LEVEL_WORDS = tuple(sorted(
    (w for w in ALL_LEVEL_WORDS if '_' in w),
    key=lambda w: (-len(w.split('_')), -len(w)),
))

# === 缺陷字典（数字 id -> 缺陷名称）===
# 2026-10-22：全仓零消费方，已删除。
# 缺陷与数字 id 的对应关系以 RuleKeyword.category='defect' 与
# RuleMethod.defect_code 为准（旧版 7 项的 HS_DEFECT_DICT 已与现库 18 个
# 缺陷严重不一致，不宜保留）。

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
# 2026-10-22 E2：改为 LEVEL_WORDS_BY_LVL 的别名，保持既有引用不破。
# 词表用规范形式 'medium'（'mid' 是别名，见 LEVEL_WORD_ALIASES）。
FUZZY_LEVELS = {lvl: list(words) for lvl, words in LEVEL_WORDS_BY_LVL.items()}

# === 推理超参 ===
MIN_ACTIVATION_THRESHOLD = 0.01001     # 无效激活判定阈值
MAMDANI_SAMPLE_POINTS = 200            # Mamdani 输出值采样点
EPSILON = 1e-7                         # 防除零


# === 档位词 → 桶索引（E2 核心）===

def resolve_bucket(lvl, level_word, field_words=None):
    """把规则的档位词解析成该字段的桶索引（0-based）。

    双轨解析：

    1. **编号形式** ``levelN``（如 ``level4``）
       语义是“该字段论域内的第 N 个分位”（相对位置），
       因此**与字段级数解耦**，只要 ``N <= lvl`` 就一定落在合法桶上。
       解析结果恒为 ``N - 1``。

    2. **自然语言词**（如 ``low`` / ``medium`` / ``high``）
       语义词要靠该字段**自己的词表**定位，因为同一个 'low'
       在 3 档字段里是桶 0（论域下界），在 5 档字段里是桶 1（25% 分位）。
       默认词表由 ``lvl`` 从 ``LEVEL_WORDS_BY_LVL`` 取；
       ``field_words`` 可传入字段级自定义词表以覆盖默认。

    Args:
        lvl: 字段的模糊等级数（RuleKeyword.fuzzy_level）
        level_word: 规则里的档位词
        field_words: 该字段的自定义词表（可选），长度必须等于 lvl

    Returns:
        int: 桶索引（0-based）

    Raises:
        ValueError: 档位词无法解析 / 越界 / 该等级数没有对应词表
    """
    word = str(level_word or '').strip().lower()
    word = LEVEL_WORD_ALIASES.get(word, word)
    if not word:
        raise ValueError('档位词为空，无法解析桶索引')

    # ---- 轨道 1：编号形式 levelN ----
    if word in LEVEL_NUMBER_TO_BUCKET:
        n = int(word[5:])
        if n > lvl:
            raise ValueError(
                f'档位词 {word!r} 超出字段等级数 {lvl}'
                f'（合法范围 level1..level{lvl}）'
            )
        return LEVEL_NUMBER_TO_BUCKET[word]

    # ---- 轨道 2：自然语言词 ----
    words = field_words if field_words is not None else LEVEL_WORDS_BY_LVL.get(lvl)
    if not words:
        raise ValueError(f'模糊等级数 {lvl} 没有对应的档位词表')
    words = [LEVEL_WORD_ALIASES.get(w, w) for w in words]
    if len(words) != lvl:
        raise ValueError(
            f'档位词表长度 {len(words)} 与模糊等级数 {lvl} 不一致'
            f'（桶数必须等于等级数）'
        )
    if word not in words:
        raise ValueError(
            f'档位词 {word!r} 不在等级 {lvl} 的词表 {tuple(words)} 中'
        )
    return words.index(word)

