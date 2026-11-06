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
LEVEL_NUMBER_TO_BUCKET = {f'level{i}': i - 1 for i in range(1, 8)}

# ⚠️ 档位→桶**没有全局静态口径**：档位词的权威定义是 LEVEL_WORDS_BY_LVL，
# 编号轨（levelN）的权威定义是 LEVEL_NUMBER_TO_BUCKET。
# 静态的 low/mid/medium/high 表在 5/7 档字段上会错位一档（现网 310/311
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
#
# 注意 3 档的 low/high 落在两端（更极端），5/7 档落在中间（更温和）。
# 这是“级数越多、档位越细”的必然结果：同一个 `X_high` 在 3 档字段上
# 要求接近论域上界，在 5 档字段上只要求高于中位。不是错误，但会影响
# 跨级数字段的规则激活严格程度。
#
# ★ 口径（与业务对齐）：**档位词是绝对词义** —— 规则写 `low`
#   就是「偏低」这一档，它落在向量的哪一格由**该字段切了几格**决定。
#   5 档体系比 3 档体系多一个 `very_low` 在 `low` 之下 ⇒ `low` 自然上移一格
#   （落桶 1 = 25% 分位）。**这是正确实现，不是缺陷、不是“语义漂移”。**
#   ⇒ 规则**不需要**声明自己属于哪套档位体系，算法无需知道这件事。
#   ⇒ 落格随字段档数变化**不列为风险**；规则**填不进**词表时的处理见
#     `nets.py::_construct_numtskruleNet`（整条规则激活度 0，**不静默删条件**）。
# 词表只覆盖 3|5|7 档（与 RuleKeyword.FUZZY_LEVELS、前端 FuzzyLevel 对齐）：
#    9 档独有词 ultra_low / ultra_high 前端没有对应命名，字段一旦设成 9 档，
#    前端 levelOptionsFor() 会静默兜底成 3 档 ⇒ 选出来的档位与论域对不上。
LEVEL_WORDS_BY_LVL = {
    3: ('low', 'medium', 'high'),
    5: ('very_low', 'low', 'medium', 'high', 'very_high'),
    7: ('extremely_low', 'very_low', 'low', 'medium', 'high', 'very_high', 'extremely_high'),
}

# 别名词：兼容写法 'mid' 与规则库 / 前端的 'medium' 同义（第 2 档）
LEVEL_WORD_ALIASES = {'mid': 'medium'}

# === 合法等级词全集（词法解析用）===
# 用途：判定规则前件的等级词是否可判级。
# 不在表里的词（如 'worse'——"该参数不合理"的人工判断词）无法映射到隶属度
# 等级索引，遇到时必须跳过而不是查表（否则 KeyError）。
#
# 由 LEVEL_WORDS_BY_LVL 派生（唯一词表源）。
# level1..7 是编号档位词，与词表并行（双轨）——上界跟最大档位数一致。
ALL_LEVEL_WORDS = {
    *{w for words in LEVEL_WORDS_BY_LVL.values() for w in words},
    *LEVEL_WORD_ALIASES,                       # 别名也要能被词法层认出
    *{f'level{i}' for i in range(1, 8)},
}

# 档位词后缀匹配表 —— 按「段数降序、同段数按长度降序」排好，
# split_phase 顺序试后缀即可拿到**最长**匹配：
# 'IV0_very_low' → name='IV0', level='very_low'（而不是 name='IV0_very' + level='low'
# —— 那样档位会错一档）。本表由 ALL_LEVEL_WORDS 派生，不另立词表。
LEVEL_WORD_SUFFIXES = tuple(sorted(
    ALL_LEVEL_WORDS,
    key=lambda w: (-len(w.split('_')), -len(w)),
))

# === 隶属度函数类型（内核**真正实现**的类型）===
# 由 `memberships.MEMBERSHIP_SPECS` **派生**：
# 「白名单 = 分派表的键」⇒ 新增一个形状只需加一行分派，类型白名单自动跟上，
# 不会出现"声明了但没实现"或"实现了但没声明"。
MEMBERSHIP_TYPES = tuple(MEMBERSHIP_SPECS.keys())

# 内核构造 FuzzyFeature 时的默认隶属度类型（生产路径当前全部用它）
DEFAULT_MEMBERSHIP_TYPE = 'gauss'

# === 模糊等级 ===
# LEVEL_WORDS_BY_LVL 的别名（list 形式，保持既有引用不破）。
# 词表用规范形式 'medium'（'mid' 是别名，见 LEVEL_WORD_ALIASES）。
FUZZY_LEVELS = {lvl: list(words) for lvl, words in LEVEL_WORDS_BY_LVL.items()}

# === 推理超参 ===
# 三个阈值分列，因为对应的**量纲互不相同**（值相同）：
#      ① Mamdani 输出侧 —— 结论隶属度之和（`np.sum(degree_values)`）
#      ② TSK 输入侧   —— 规则绝对激活度（`min(各前件 μ)`）
#      ③ TSK 相对量   —— 规则在所属输出参数组内的占比
#    ⇒ 一个旋钮控三件正交的事，既没法单独调、也没法各自解释。
MIN_CONCLUSION_DEGREE = 0.01001        # ① Mamdani 输出侧：结论隶属度之和下限
MIN_RULE_ACTIVATION = 0.01001         # ② TSK 输入侧：规则绝对激活度下限
MIN_GROUP_SHARE = 0.01001             # ③ TSK 相对量：组内占比下限
MAMDANI_SAMPLE_POINTS = 200            # Mamdani 输出值采样点
EPSILON = 1e-7                         # 防除零

# === M-1 门控三参数 ===
#
# ⚠️ 三者**性质不同**，各有各的指定规则 ——
#    **不可当成「三个可以一起调的旋钮」**，也不可把它们的区间合并后重取中点。
#
# ① GATE_TAU（τ）—— **结构量**（R1 推导优先，绝不标定）
#    推导链：σ = span / (2 × (lvl − 1)) ⇒ 相邻桶中心距 ≡ 2σ
#           ⇒ 桶中心处对**相邻桶**的隶属度 ≡ exp(−(2σ)² / (2σ²)) = **exp(−2)**
#           ⇒ 与档位数（3/5/7/9）、与 span 都无关 ⇒ 跨档位统一。
#    语义：规则**引用的那个桶**像不像（`μ_used`）—— 低于「相邻桶的隶属度」
#          ⇒ 前提比相邻档还弱 ⇒ 未命中，规则不参与结论。
#    ⚠️ 这是 τ 的**唯一**正确取法：取 exp(−2) 才使「相邻档 = 压到 β_min 而不出局」
#       精确成立（τ ≤ 0.10 ⇒ 疗效仅 80%；τ ≥ 0.20 ⇒ 相邻档整体出局、语义阶跃不可调）。
GATE_TAU = 0.1353352832366127          # exp(-2) —— 相邻桶隶属度
#
# ② GATE_EPSILON（ε）—— **纯代价旋钮**（R2 代价可测 + 取零）
#    语义：领先相邻档多少才算「明确态」（`competition = μ_used − μ_alt`）。
#    ⚠️ 它**对疗效零贡献**：错配侧 competition 全为负 ⇒ β_p ≡ β_min，与 ε 无关；
#       ε 唯一的作用是误伤「归属一致但领先不足」的相符规则。
#    实测零误伤上界 ε* = 0.180599（桶几何的离散刻度，25 个参数取值完全相同）
#    ⇒ 取 0.10（允许工况偏离桶中心 0.917σ 仍不误伤）。
GATE_EPSILON = 0.10
#
# ③ GATE_BETA_MIN（β_min）—— **效果旋钮**（R3 区间夹逼 + 取中点）
#    语义：归属不一致（档位不符）的规则保留多少权重。
#    效果判据：错配残留 = 17.729·b / (98.25 + 17.729·b)
#           「压到 2%~5%」⇒ b ∈ [0.113, 0.292] ⇒ 取中点 **0.20**（残留 3.48%，压 5.2×）。
#    ⚠️ 另有**可行性约束**（组内占比闸零触发 ⇒ b ≥ 0.154）—— 那是**检验**、
#       **不是效果区间的端点** ⇒ 不参与中点计算（review §28.6）。
GATE_BETA_MIN = 0.20

# 特异级衰减系数 ρ：**每退一级，匹配度权重打 ρ 折**。
# 语义：越精确的规则越该被采信；通用的兜底规则不该盖过精确规则。
# 详见 `specificity_weight`。
SPECIFICITY_DECAY = 0.5


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
        长度为 ``lvl`` 的桶中心数组。
    
    Raises
    ------
    ValueError
        论域倒序（``min >= max``）。
    
    ⚠️ **倒序为什么要报错而不是“将就着算”**：倒序会让「档位 0」对应论域**高端**
    ⇒ 档位语义整体翻转 ⇒ 是个**静默错误**（不报错、但结果全反）。
    生产路径上倒序**进不了内核** —— 契约层 `library/adapters.py` 对
    ``min_val >= max_val`` 直接跳过 + warning；推测论域也不会倒挂。
    ⇒ 内核真收到倒序 ⇒ 契约被绕过 ⇒ 显式失败。
    """
    if float(f_interval[0]) >= float(f_interval[1]):
        raise ValueError(
            f'论域区间非法（min={f_interval[0]!r}, max={f_interval[1]!r}）：'
            '必须 min < max，否则桶序会整体翻转（档位语义颠倒）。'
        )
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


# === 档位词 → 论域数值（离散档位进推理的前提）===

def level_to_domain_value(lvl, level_word, min_val, max_val):
    """把档位词翻译成该字段论域上的代表数值（**桶中心**）。

    用途：让**离散档位**也能作为推理输入参与隶属度计算。
    典型场景 = 缺陷程度（``level`` = low/medium/high）：它本身不是连续量，
    但推理网络的输入是数值 ⇒ 必须落到论域上才有意义。

    语义：取**该档位的桶中心** ⇒ 该档隶属度恰为 1.0，相邻档按论域跨度
    自然衰减 ⇒ 档位差异连续表达，而不是非此即彼的硬开关。

    与 `resolve_bucket` 的关系：先定桶，再取该桶在论域上的坐标。

    Args:
        lvl: 字段的模糊等级数（RuleKeyword.fuzzy_level）
        level_word: 档位词（如 ``low`` / ``medium`` / ``high``）
        min_val: 字段论域下界
        max_val: 字段论域上界

    Returns:
        float: 桶中心数值；档位词无法解析时返回 ``None``
        （调用方按"该维度不参与推理"处理，不抛错）
    """
    try:
        bucket = resolve_bucket(lvl, level_word)
    except ValueError:
        return None
    centers = bucket_centers([min_val, max_val], lvl)
    return float(centers[bucket])


# === 特异级 → 匹配度权重 ===

# 特异级到「距精确级隔了几级」的映射。
# 语义：1=精确匹配（差 0 级）、2/3=半匹配（差 1 级）、4=通用兜底（差 2 级）。
_SPECIFICITY_DISTANCE = {1: 0, 2: 1, 3: 1, 4: 2}


def specificity_weight(specificity) -> float:
    """特异级 → 匹配度权重（组内归一化前的乘数）。

    语义：**越精确的规则越该被采信**。用指数衰减表达「每退一级，权重打
    ρ 折」：``s = ρ^d``，d 为该规则距「精确匹配」隔了几级。

    ==========  ==============  ======  ==============
    特异级       含义             d      权重（ρ=0.5）
    ==========  ==============  ======  ==============
    1           精确匹配          0      1.0
    2           部分材料匹配      1      0.5
    3           部分产品匹配      1      0.5
    4           通用（默认）      2      0.25
    ==========  ==============  ======  ==============

    ⚠️ spec2 与 spec3 **同权**：两者都是「一个维度匹配、另一个不匹配」的
    半匹配，信息量相同。若给不同权重，等于人为断言「材料比产品更重要」，
    而规则库里没有任何依据支持这个排序。

    Args:
        specificity: 特异级（1~4；越界或非法值按「通用」处理）

    Returns:
        float: 权重（∈ (0, 1]）
    """
    try:
        d = _SPECIFICITY_DISTANCE.get(int(specificity),
                                      _SPECIFICITY_DISTANCE[4])
    except (TypeError, ValueError):
        d = _SPECIFICITY_DISTANCE[4]
    return SPECIFICITY_DECAY ** d

