"""模糊推理常量定义 —— 常量、枚举、映射表。"""

import numpy as np

from .memberships import MEMBERSHIP_SPECS

# === 缺陷名称常量集合 ===
# 用途：在规则词法解析时区分"工艺参数名称"与"缺陷名称"——
# 工艺参数名若命中本集合则看作缺陷条件。
#
# ⚠️ 必须与 RuleKeyword 的 defect 类完全对齐：缺失的缺陷名会被
# classify_name 误判成"工艺参数"，进而被参数名收集逻辑当作参数收走 →
# 该缺陷也变成一个"参数论域" → 规则的缺陷前件被当成可判级条件，
# 而缺陷变量根本没有数值，激活度被 EPSILON 压到 ~0，整类规则全部失活。
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
    # ---- 历史规则兼容词（保留）----
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
#      就一定落在合法桶上。它表达的是“编号”，不是“档位语义”。
# 与 LEVEL_WORDS_BY_LVL 的关系：levelN 的 N 就是该字段词表里的第 N 个词。
#      两者互补——编号形式负责精确定位，语义词形式负责可读性。
LEVEL_NUMBER_TO_BUCKET = {f'level{i}': i - 1 for i in range(1, 10)}

# ⚠️ 档位→桶**没有全局静态口径**：档位词的权威定义是 LEVEL_WORDS_BY_LVL，
# 编号轨（levelN）的权威定义是 LEVEL_NUMBER_TO_BUCKET。
# 静态的 low/mid/medium/high 表在 5/7/9 档字段上会错位一档（现网 310/311
# 个字段是 5 档 ⇒ 全部前件门控偏一档），必须按字段自己的词表定位
# （见 LEVEL_WORDS_BY_LVL + resolve_bucket）。

# === 档位词表（按字段的模糊等级数）===
# 这是档位词的**唯一权威定义**。
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

# 别名词：兼容写法 'mid' 与规则库 / 前端的 'medium' 同义（第 2 档）
LEVEL_WORD_ALIASES = {'mid': 'medium'}

# === 合法等级词全集（词法解析用）===
# 用途：判定规则前件的等级词是否可判级。
# 不在表里的词（如 'worse'——"该参数不合理"的人工判断词）无法映射到隶属度
# 等级索引，遇到时必须跳过而不是查表（否则 KeyError）。
#
# 由 LEVEL_WORDS_BY_LVL 派生（唯一词表源）。
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

# === 动作名 -> 字串映射（补全 Action 用）===
ADJUST_ACTIONS = {
    'add': '增加',
    'reduce': '减少',
    'adjust': '提示',
    'add_pct': '增加百分比',
    'reduce_pct': '减少百分比',
}

# === 隶属度函数类型（内核**真正实现**的类型）===
# 由 `memberships.MEMBERSHIP_SPECS` **派生**，不再手写：
# 「白名单 = 分派表的键」⇒ 新增一个形状只需加一行分派，类型白名单自动跟上，
# 不会出现"声明了但没实现"或"实现了但没声明"。
MEMBERSHIP_TYPES = tuple(MEMBERSHIP_SPECS.keys())

# 内核构造 FuzzyFeature 时的默认隶属度类型（生产路径当前全部用它）
DEFAULT_MEMBERSHIP_TYPE = 'gauss'

# === 反模糊化方法 ===
DEFUZZ_METHODS = [
    'centroid',        # 重心法（推荐）
    'bisector',        # 均分面积法
    'mom',             # 最大隶属度均值
    'som',             # 最大隶属度取小
    'lom',             # 最大隶属度取大
]

# === 模糊等级 ===
# LEVEL_WORDS_BY_LVL 的别名（list 形式，保持既有引用不破）。
# 词表用规范形式 'medium'（'mid' 是别名，见 LEVEL_WORD_ALIASES）。
FUZZY_LEVELS = {lvl: list(words) for lvl, words in LEVEL_WORDS_BY_LVL.items()}

# === 推理超参 ===
MIN_ACTIVATION_THRESHOLD = 0.01001     # 无效激活判定阈值
MAMDANI_SAMPLE_POINTS = 200            # Mamdani 输出值采样点
EPSILON = 1e-7                         # 防除零


# === 桶中心（论域分位点）===
# 桶有两套必须对齐的定义 ——
#   ① 桶**位置**（论域上的中心）= 本函数
#   ② 桶**语义**（档位词）= LEVEL_WORDS_BY_LVL 的词序
# 两者必须一一对应：词表第 i 个词 ↔ 第 i 个桶中心（由单测断言兜底）。

def bucket_centers(f_interval, lvl):
    """返回论域上各桶的中心（0-based 下标 = 桶索引）。

    桶 0 = 论域下界，桶 ``lvl - 1`` = 论域上界，中间桶 = 等分位点。

    与 `LEVEL_WORDS_BY_LVL` 的对应关系：**词表第 i 个词对应第 i 个桶**，
    即该词的桶中心就是 ``bucket_centers(f_interval, lvl)[i]``。

    Parameters
    ----------
    f_interval : sequence[float]
        论域区间 ``[min_val, max_val]``
    lvl : int
        桶数（== 字段的模糊等级数）

    Returns
    -------
    numpy.ndarray
        长度为 ``lvl`` 的桶中心数组
    """
    return np.r_[
        f_interval[0],
        np.quantile(f_interval, np.arange(1, lvl - 1) / (lvl - 1)),
        f_interval[1],
    ]


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

