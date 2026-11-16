"""策略清单（文件版）—— 第2层（``decide_direction``）的**规则来源**。

⚠️ **本文件是业务规则的唯一存放处**（取代已撤回的策略表）：
改一条经验 = 改这个文件 ⇒ 随版本走、可评审、可测试、可 diff。

为什么是「文件 + 代码」而不是「表 + JSON」：

- 表里的 JSON 是**第二门语言** —— 没人看得懂、IDE 不认、无法评审；
- 代码里的清单**只有一门语言**（Python）—— 可读、可测、可跳转。

⚠️ **清单为空 ⇒ 第2层不裁决**（行为与「不接第2层」完全一致）：
没有命中场景 ⇒ 不做准入 / 优先 / 名额裁决，只按字段级优先级排。

⚠️ **命中顺序 = 优先级升序，取第一条命中**（:func:`load_strategies` 排序 +
:func:`select_policy` 取首条）⇒ **具体场景排前面、兜底场景排最后** ——
命中具体场景时兜底自动让位。

⚠️ **名额（``max_items``）是场景级参数，不是全局开关**：
``None`` = 不限 ⇒ **多参数输出是现成的出口** —— 某场景若要一次调多个，
只需让它**不写** ``max_items``（不限）或写一个更大的数。
这正是第2层的意义：**同一套机制，按场景决定「这一轮调几个」** ——
既能与旧版对齐（缺省一轮一个），也能按需放开（多参数），**不是二选一**。

⚠️ **两类“不可调”是不同东西，别混**：

- :attr:`ScenarioPolicy.allowed_params`（**白名单**）= **场景范围** ——
  “这个场景该动哪些旋钮”。不写 = 不限制。
  ⚠️ 白名单写窄了 ⇒ 白名单外的候选全部让位 ⇒ **这一轮可能无输出**，
  所以只写**该缺陷公认的主旋钮**，不写全量。
- :attr:`ScenarioPolicy.blocked_params`（**禁入清单**）= **基线项** ——
  “任何场景都不该动的旋钮”。见 :data:`BASELINE_EXCLUDED_PARAMS`。

⚠️ **两者都作用在候选的**业务字段名**上**（算法命名空间已在候选收集阶段译回）。

条件可引用的**标准字段**见 :data:`process.algorithms.decide_direction.CONTEXT_FIELDS`；
还可引用 ``ScenarioContext.extra`` 里注入的任意键（附加字段）。
"""

from typing import Tuple

from .decide_direction import ScenarioPolicy

#: **基线项**（禁入清单）—— 任何场景都不把它当调机对象。
#:
#: ⚠️ **用户口径**：注射速度一般用户为成型周期与保证质量采用较大速度，
#:    **属基线取值，不参与阶段调机** ⇒ 阶段调机不以它为对象。
#: ⚠️ **与白名单的分工**：白名单是“这个场景该动哪些”（可为空 = 不限制）；
#:    禁入清单是“任何场景都不该动”（独立生效）——
#:    靠禁入清单实现基线项，**不需要**把“所有可调旋钮”列成全集
#:    （全集会随新增旋钮漂移）。
#: ⚠️ **这是本轮相对旧版的偏离**：旧版兜底只取规则命中第一条，
#:    可能落地注射速度；现在注射速度在任何场景下都让位。
BASELINE_EXCLUDED_PARAMS: Tuple[str, ...] = (
    'inj_spd_1',
    'inj_spd_2',
    'inj_spd_3',
    'inj_spd_4',
    'inj_spd_5',
    'inj_spd_6',
)

#: 策略清单（按 ``priority`` 升序命中，**取第一条命中**）。
STRATEGIES: Tuple[ScenarioPolicy, ...] = (
    # --- S1 打足：短射 + 重量不足 ⇒ 充填优先 ---
    # ⚠️ ``fill_gap`` = 目标重量 − 实测重量（**正数 = 缺料**）⇒ ``gt 0`` 等价于
    #    旧版的「实际重量 < 目标重量」；缺重量数据 ⇒ ``fill_gap`` 为 None ⇒ 不命中。
    # ⚠️ ``target_mode='fill_ratio'`` ⇒ ``MEL`` 走**充填量比例**口径解算行程
    #    （不是 MEL 增量），与旧版「按重量比例重算行程」逐项一致。
    # ⚠️ 白名单 = **充填量两个旋钮**（素材 U-07：先胶量端，MEL 偏大后才轮到 VPTL）
    #    ⇒ 其余旋钮让位，而不是“暂缓”（含义：这个场景不管它们）。
    ScenarioPolicy(
        scenario_code='filling_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'contains', 'value': 'SHORTSHOT'},
            {'field': 'fill_gap', 'operator': 'gt', 'value': 0},
        ),
        allowed_params=('met_end_pos', 'vps_pos'),
        blocked_params=BASELINE_EXCLUDED_PARAMS,
        preferred_params=('met_end_pos',),   # 旧版：MEL 旋转到首位
        max_items=1,                          # 旧版：一轮只调一个量
        target_mode='fill_ratio',
        reason='充填量不足 ⇒ 充填优先，并按重量比例重算行程',
        priority=10,
    ),
    # --- S2 补缩：缩水类 ⇒ 只动保压组 ---
    # ⚠️ 白名单 = 二段压力 + 二段时间（素材 SK-01 / SK-02）
    #    ⇒ 二段时间的定量锚点是**浇口封冻时间**（🔵 尚缺判据 ⇒ 目标值待校准）。
    # ⚠️ 条件用 ``in_any``（字段值 ``defect_codes`` 是**集合**）
    #    ⇒ 任一缺陷码落在目标集合内即命中。
    ScenarioPolicy(
        scenario_code='shrinking_first',
        conditions=(
            {
                'field': 'defect_codes',
                'operator': 'in_any',
                'value': ('SHRINKAGE', 'UNDERSIZE', 'OVERSIZE', 'WARPING'),
            },
        ),
        allowed_params=('hold_pres_1', 'hold_t_1'),
        blocked_params=BASELINE_EXCLUDED_PARAMS,
        preferred_params=('hold_pres_1',),
        max_items=1,
        reason='充填已足 ⇒ 只动保压：二段压力与二段时间（二段时间锚点是浇口封冻）',
        priority=20,
    ),
    # --- S3 外观：飞边 ⇒ 降压或减胶量 ---
    # ⚠️ 素材 FL-01（降二段压力）/ FL-02（减胶量，充填比例 ≤ 98%）
    #    ⇒ 白名单只留这两个主旋钮；目标值待校准（FL-02 的 98% 上限）。
    # ⚠️ 优先项取 ``met_end_pos``（减胶量）—— 飞边是型腔压力过高，
    #    胶量端是充填量第一旋钮。
    # ⚠️ **2026-11-13 用户口径**：飞边**可能是模具问题而不是工艺问题**（素材 FL-06：
    #    不带二段的充填件本身就飞边 ⇒ 判为模具问题，⛔ 不属工艺）。
    #    ⇒ 本场景的前提应是「已排除模具问题」，但**该判据目前系统里没有信号**
    #    （🔵 需「不带二段的充填件」测试结果）⇒ 只能写进 ``reason``（进留痕），
    #    **不写成条件**（写了就等于该场景永不命中）。
    ScenarioPolicy(
        scenario_code='flash_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'contains', 'value': 'FLASH'},
        ),
        allowed_params=('hold_pres_1', 'met_end_pos'),
        blocked_params=BASELINE_EXCLUDED_PARAMS,
        preferred_params=('met_end_pos',),
        max_items=1,
        reason=(
            '飞边 ⇒ 型腔压力过高 ⇒ 减胶量或降二段压力'
            '（⚠️ 若不带二段的充填件本身就飞边 ⇒ 属模具问题，应先修模）'
        ),
        priority=30,
    ),
    # --- S3 外观：烧焦 ⇒ 熔体侧（背压 / 松退 / 螺杆转速）---
    # ⚠️ 素材 BN-01 要求「先提示修模/清模，不要先给参数建议」——
    #    **提示通道尚未具备**（🔵 需 4M 归因字段）⇒ 本条只给参数侧。
    # ⚠️ 素材 BN-02（降一段充填速度）落在**基线项**（注射速度）⇒ 不可用，
    #    故白名单只留熔体侧三项 + 保压压力。
    # ⚠️ **2026-11-13 用户口径**：烧焦**首要根因是模具排气不良**（素材 BN-01），
    #    调参 = 绕过根因 ⇒ 「已排气处理」本应是前提，但**没有信号**
    #    （🔵）⇒ 只能写进 ``reason``（进留痕）。
    ScenarioPolicy(
        scenario_code='burn_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'contains', 'value': 'BURN'},
        ),
        allowed_params=(
            'met_back_pres_1',
            'pst_met_decomp_dist',
            'met_rot_spd_1',
            'hold_pres_1',
        ),
        blocked_params=BASELINE_EXCLUDED_PARAMS,
        preferred_params=('met_back_pres_1',),
        max_items=1,
        reason=(
            '烧焦 ⇒ 熔体侧排查：背压 / 熔胶后松退 / 螺杆转速'
            '（⚠️ 首要根因是排气不良 ⇒ 应先修模/清模，不要先给参数建议）'
        ),
        priority=40,
    ),
    # --- S3 外观：气纹 ⇒ 查背压 ---
    # ⚠️ 拍板 G：气纹形态 = 「查背压」⇒ 优先项取 ``met_back_pres_1``。
    #    规则库实测：气纹 152 条里 ``MBP0``（背压）有 15 条，是第 5 大输出参数。
    # ⚠️ 白名单比拍板 G 宽（背压 + 保压压力 + 保压时间）—— 只留背压一个时，
    #    若本轮规则只推了其它旋钮，会出现“本场景无输出”。
    ScenarioPolicy(
        scenario_code='gasveins_first',
        conditions=(
            {'field': 'defect_codes', 'operator': 'contains', 'value': 'GASVEINS'},
        ),
        allowed_params=('met_back_pres_1', 'hold_pres_1', 'hold_t_1'),
        blocked_params=BASELINE_EXCLUDED_PARAMS,
        preferred_params=('met_back_pres_1',),
        max_items=1,
        reason='气纹 ⇒ 查背压（塑料含气 / 背压不足）',
        priority=50,
    ),
    # --- 兜底：缺省一轮只调一个量（兼容旧版）---
    # ⚠️ ``conditions=()`` ⇒ **恒命中**（空条件 = 无条件成立）⇒ 没命中任何
    #    具体场景时的缺省行为；``priority`` 排最后 ⇒ 具体场景永远优先。
    # ⚠️ 兜底恒命中 ⇒ **场景永不为 None** ⇒ 留痕里永远有「这一轮按什么场景裁决」。
    # ⚠️ **白名单留空**（不限制）⇒ 兜底不窄化；基线项由禁入清单挡住。
    ScenarioPolicy(
        scenario_code='default_one_adjust',
        conditions=(),
        blocked_params=BASELINE_EXCLUDED_PARAMS,
        max_items=1,
        reason='缺省一轮只调一个量',
        priority=100,
    ),
)


def load_strategies() -> Tuple[ScenarioPolicy, ...]:
    """取策略清单（按 ``priority`` 升序 ⇒ 命中判定从靠前的开始）。"""
    return tuple(
        sorted(STRATEGIES, key=lambda item: (item.priority, item.scenario_code))
    )


__all__ = ['BASELINE_EXCLUDED_PARAMS', 'STRATEGIES', 'load_strategies']
