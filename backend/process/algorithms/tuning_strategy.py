"""调机策略 —— **阶段模型** + **场景裁决规则**（业务知识，非逻辑）。

【注意】**本模块是落地场景规则的唯一存放处** —— 改一条经验 = 改这个文件 ⇒ 随版本走、
可评审、可测试、可 diff。

**一、阶段模型** —— 阶段 = **缺陷族**（要解决的问题），不是「工艺组」。

划分依据（用户拍板）：阶段的进入/达成信号必须是**可观测量**（缺陷码 + 重量缺口）
——「保压参数」不可观测 ⇒ 阶段按缺陷族划分。三个阶段按用户口径排序
（「先把产品打到差不多 → 再补缩 → 最后针对性处理外观缺陷」）⇒ 阶段码见
:data:`STAGE_ORDER`。

- **阶段状态不落库** —— 阶段由**本轮反馈的缺陷构成**推导（纯函数）⇒ 换模 /
  轮次失败 / 反馈缺失都自动自愈，不会「状态卡在某一步」。
- **未知缺陷码不臆造归属** —— 归 ``UNKNOWN_STAGE``（排末位），既不塞进已知阶段，
  也不丢。

**二、场景裁决规则**（第 2 层的规则来源）

一条 :class:`~process.algorithms.decide_direction.ScenarioStrategy` = **一套完整的
经验组合** ⇒ 命中即整条采用，**不合并**多条（合并语义会随条数增加而含糊）。

- **命中顺序 = 优先级升序，取第一条命中** ⇒ 具体场景排前面、兜底场景排最后。
- **条件按「本轮实际处理的缺陷」判定** —— service 预处理层已把 feedback **收敛**
  成只剩本轮处理的那条，经 ``ScenarioContext.extra`` 注入 ⇒ 字段值是**单值** ⇒
  条件用 ``in_set``（落在目标集合内即命中）。
- **名额（``max_items``）是场景级参数**，不是全局开关：不写 = 不限 ⇒ 多参数输出
  是现成出口（缺省一轮一个，也能按需放开）。
- **两类「不可调」不是一回事**：``allowed_params``（白名单）= **场景范围**
  「这个场景该动哪些旋钮」，不写 = 不限制；``blocked_params``（禁入清单）= **基线项**
  「任何场景都不该动的旋钮」，独立生效。
- 条件可引用的**标准字段**见
  :data:`process.algorithms.decide_direction.CONTEXT_FIELDS`；还可引用
  ``ScenarioContext.extra`` 里注入的任意键。

【注意】**阶段表与场景规则必须同源** —— 缺陷选取
（:mod:`process.algorithms.defect_selection`）与第 2 层
（:mod:`process.algorithms.decide_direction`）读的是同一份，否则会「选出 A 阶段的
缺陷却命中 B 阶段的策略」。

**规则原料**（``U-07`` / ``SK-01`` / ``FL-06`` / ``BN-01`` …）见
``backend/process/references/04-defect-adjustment-rules.md``。

零 ORM、零 Django（本模块只认裸 dict / 纯数据）。
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .decide_direction import ScenarioStrategy


# ── 第 1 节：阶段模型（数据 + 推导）──────────────────────────

#: 阶段优先级（**升序 = 推进顺序**）：``filling`` 打足 → ``shrinking`` 补缩
#: → ``appearance`` 外观。
STAGE_ORDER: Tuple[str, ...] = ('filling', 'shrinking', 'appearance')

#: 未知缺陷码的兜底阶段（排在所有已知阶段之后）。
UNKNOWN_STAGE: str = 'unknown'

#: 缺陷码 → 阶段。
DEFECT_STAGE_MAP: Mapping[str, str] = {
    # —— S1 打足（充填）——
    'SHORTSHOT': 'filling',
    # —— S2 补缩（尺寸与形状；根因在收缩与冷却，不是表面）——
    'SHRINKAGE': 'shrinking',
    'UNDERSIZE': 'shrinking',
    'OVERSIZE': 'shrinking',
    'WARPING': 'shrinking',
    # —— S3 外观（表面质量）——
    'WATERRIPPLE': 'appearance',
    'GASVEINS': 'appearance',
    'TOPWHITE': 'appearance',
    'HARDDEMOLDING': 'appearance',
    'ABERRATION': 'appearance',
    'WELDLINE': 'appearance',
    'FLASH': 'appearance',
    'AIRTRAP': 'appearance',
    'MATERIALFLOWER': 'appearance',
    'BURN': 'appearance',
    'GATEMARK': 'appearance',
    'SHADING': 'appearance',
}


def stage_of_defect(defect_code: Optional[str]) -> str:
    """返回缺陷码对应的阶段码；未知或空 ⇒ :data:`UNKNOWN_STAGE`。"""
    if not defect_code:
        return UNKNOWN_STAGE
    return DEFECT_STAGE_MAP.get(str(defect_code), UNKNOWN_STAGE)


def rank_of_stage(stage: str) -> int:
    """返回阶段码的推进次序；未知阶段排**末位**。"""
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return len(STAGE_ORDER)


def sort_defects_by_stage(
    defects: Sequence[Any],
) -> List[Tuple[int, Any]]:
    """返回按阶段优先级排序的 ``[(原始下标, 缺陷项), ...]``。

    - 阶段顺序见 :data:`STAGE_ORDER`；
    - **同阶段内保持原始顺序**（稳定排序 —— 同阶段缺陷的先后是用户的判断，不改）；
    - 无 ``keyword_name`` 的项与未知缺陷码归末位（**不丢**，交给选取环节跳过）。

    【注意】返回**原始下标**是刻意的：留痕里的 ``index`` 要能指回用户提交的那一项，
    重排后的下标会指错位置。
    """
    decorated: List[Tuple[int, int, Any]] = []
    for index, item in enumerate(defects or ()):
        code = item.get('keyword_name') if isinstance(item, Mapping) else None
        decorated.append((rank_of_stage(stage_of_defect(code)), index, item))
    decorated.sort(key=lambda row: (row[0], row[1]))
    return [(index, item) for _, index, item in decorated]


@dataclass(frozen=True)
class StageProgress:
    """阶段进度（**每轮从反馈纯推导**）。

    Attributes:
        defect_codes: 推导所用的缺陷码（去重，保持出现顺序）。
        achieved: **未复现**的阶段（推导所用的缺陷码里没有该阶段的）。
        pending: 仍有缺陷的阶段（**明确未达成**）。
        current: 当前应推进的阶段 = 第一个 ``pending``
            （``None`` = 本轮无已知阶段的缺陷）。
    """

    defect_codes: Tuple[str, ...] = ()
    achieved: Tuple[str, ...] = ()
    pending: Tuple[str, ...] = ()
    current: Optional[str] = None

    def to_trace(self) -> Dict[str, Any]:
        """返回阶段进度的留痕载荷（进第 2 层留痕）。"""
        return {
            'defect_codes': list(self.defect_codes),
            'achieved': list(self.achieved),
            'pending': list(self.pending),
            'current': self.current,
        }


def derive_stage_progress(defect_codes: Sequence[str]) -> StageProgress:
    """由本轮缺陷码推导**阶段进度**（纯函数，不落库、不查库）。

    口径（**阶段达成信号**，见 ``docs/l2-stage-strategy-design.md``）：

    - **达成**：该阶段的**所有**缺陷码在本轮反馈里**都不出现**
      （「这一类缺陷不见了」= 可观测的达成信号）；
    - **未达成（pending）**：本轮反馈里还有该阶段的缺陷码；
    - **当前阶段（current）**：第一个未达成的阶段（按 :data:`STAGE_ORDER` 推进顺序）。

    【注意】**不区分「已解决」与「从未报过」** —— 阶段状态不落库 ⇒ 没有历史可比
    ⇒ 「本轮没报该阶段缺陷」一律记为达成。反馈稀疏时**可能高估达成度**。

    【注意】**推导所用的缺陷码来自收敛后的反馈**（service 预处理层只留本轮
    处理的那条）⇒ ``achieved`` / ``pending`` 只反映**该条**所在阶段，
    不再是「本轮全阶段」视图；``current`` 不受影响（阶段序选中的必然是
    最靠前的未达成阶段）。

    【注意】**本函数只做推导，不做裁决** —— 裁决由**场景清单**做
    （:data:`SCENARIO_STRATEGIES`）：``current`` 经 ``services/strategy_inputs.py`` 注入
    ``ScenarioContext.extra`` ⇒ 场景条件**可引用**它（如 ``filling_stage_first``
    用 ``current_stage == 'filling'`` 判定「还在打足阶段」）。
    """
    codes: List[str] = []
    for code in defect_codes or ():
        if not code:
            continue
        text = str(code)
        if text not in codes:
            codes.append(text)

    # 阶段 → 本轮该阶段的缺陷码（未知码归 UNKNOWN_STAGE，不影响任何已知阶段）
    by_stage: Dict[str, List[str]] = {}
    for code in codes:
        by_stage.setdefault(stage_of_defect(code), []).append(code)

    pending = tuple(stage for stage in STAGE_ORDER if by_stage.get(stage))
    achieved = tuple(stage for stage in STAGE_ORDER if not by_stage.get(stage))
    return StageProgress(
        defect_codes=tuple(codes),
        achieved=achieved,
        pending=pending,
        current=pending[0] if pending else None,
    )


# ── 第 2 节：场景裁决规则（清单）────────────────────────────

#: **基线项**（禁入清单）—— 任何场景都不把它当调机对象。
#:
#: 【注意】**用户口径**：注射速度一般用户为成型周期与保证质量采用较大速度，
#:    **属基线取值，不参与阶段调机** ⇒ 阶段调机不以它为对象。
BASELINE_BLOCKED_PARAMS: Tuple[str, ...] = (
    'inj_spd_1',
    'inj_spd_2',
    'inj_spd_3',
    'inj_spd_4',
    'inj_spd_5',
    'inj_spd_6',
)

#: 场景清单（按 ``priority`` 升序排列）。
SCENARIO_STRATEGIES: Tuple[ScenarioStrategy, ...] = (
    # --- S1 打足：短射 + 重量不足 ⇒ 充填优先 ---
    # 【注意】``fill_gap`` = 目标重量 − 实测重量（**正数 = 缺料**）⇒ ``gt 0``
    #    即「实际重量 < 目标重量」；缺重量数据 ⇒ ``fill_gap`` 为 None ⇒ 不命中。
    # 【注意】``target_mode='fill_ratio'`` ⇒ ``MEL`` 走**充填量比例**口径解算行程
    #    （不是 MEL 增量）。
    # 【注意】**规则原料 U-07**：充填量有两个旋钮、有先后（先胶量端，MEL 偏大后才轮到
    #    VPTL）⇒ 白名单只留胶量端两个旋钮；其余旋钮**让位**（而不是「暂缓」——
    #    含义：这个场景不管它们）。
    ScenarioStrategy(
        scenario_code='filling_first',
        conditions=(
            {'field': 'selected_defect', 'operator': 'in_set', 'value': ('SHORTSHOT',)},
            {'field': 'fill_gap', 'operator': 'gt', 'value': 0},
        ),
        allowed_params=('met_end_pos', 'vps_pos'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_end_pos',),   # 首选 MEL（充填量第一旋钮）
        max_items=1,                          # 一轮只调一个量
        target_mode='fill_ratio',
        reason='充填量不足 ⇒ 充填优先，并按重量比例重算行程',
        priority=10,
    ),
    # --- S1b 打足（缺重量口径）：短射 + 仍在打足阶段 ⇒ 充填量优先 ---
    # 【注意】**缺实测重量 ⇒ 本条接管**：``filling_first`` 命中依赖 ``fill_gap > 0``
    #    （缺实测重量 ⇒ ``fill_gap`` 为 None ⇒ 不命中）⇒ 短射轮次会落进
    #    **兜底场景**，而兜底**没有优先集** ⇒ 次序完全继承 L1 的输出序
    #    （= 规则库遍历序）⇒ 料筒温度等**间接旋钮**可能排到首位而上位。
    # 【注意】本条**不依赖重量数据**：改用**阶段进度**（``current_stage``）判定
    #    「还在打足阶段」—— 阶段由**缺陷码**推导，与重量数据无关。
    # 【注意】**priority=15 ⇒ 排在 ``filling_first``(10) 之后** ⇒
    #    **有重量数据时仍走 ``filling_first``**（按重量比例解算行程），
    #    本条只在「拿不到重量口径」时接管 ⇒ 两个场景互不覆盖。
    # 【注意】**规则原料 U-07「先胶量端」** ⇒ 白名单顺序 = 调整次序：
    #    胶量端（熔胶终止位置 / VP 切换位置）→ 保压组 → 熔体侧 → 料筒温度组。
    #    **料筒温度组排末位**（熔体黏度的间接影响，打足阶段不是主旋钮）。
    # 【注意】白名单**含 ``inj_t``**：它虽受 G3 让位规则约束（改注射时间要让位给
    #    注射速度，而注射速度是基线项不可调），但**不在白名单会让位理由被
    #    「本场景不允许」掩盖** ⇒ 反而看不出 G3 规则在工作。
    ScenarioStrategy(
        scenario_code='filling_stage_first',
        conditions=(
            {'field': 'selected_defect', 'operator': 'in_set', 'value': ('SHORTSHOT',)},
            {'field': 'current_stage', 'operator': 'exact', 'value': 'filling'},
        ),
        allowed_params=(
            # --- 胶量端（充填量端，主旋钮）---
            'met_end_pos',        # 熔胶终止位置（MEL）
            'vps_pos',            # VP 切换位置（VPTL）
            # --- 注射时间（受 G3 让位规则约束，保留在白名单内）---
            'inj_t',
            # 【注意】**注射压力**：规则库实测短射类会产出 ``inj_pres_1`` / ``inj_pres_2``
            #    ⇒ 不放进白名单会有「本场景无输出」风险
            #    （白名单写窄 ⇒ 候选全部让位 ⇒ 这一轮什么都不落地）。
            #    【注意】但**不进优先集** ⇒ 排在优先集之后 ⇒ 胶量端/保压/熔体侧
            #    都不可调时才轮得到它（注射速度才是基线项，注射压力不是）。
            'inj_pres_1', 'inj_pres_2',
            # --- 保压组 ---
            'hold_pres_1',        # 一段保压压力
            'hold_spd_1',         # 一段保压速度
            'hold_t_1',           # 一段保压时间
            # --- 熔体侧 ---
            'met_back_pres_1',    # 一段背压
            'met_rot_spd_1',      # 一段螺杆转速
            'pst_met_decomp_dist',  # 熔胶后松退距离
            # --- 料筒温度组（末位：熔体黏度的间接影响）---
            'brl_temp_1', 'brl_temp_2', 'brl_temp_3', 'brl_temp_4', 'brl_temp_5',
            'brl_temp_6', 'brl_temp_7', 'brl_temp_8', 'brl_temp_9',
            'noz_temp',
        ),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        # 【注意】优先集与白名单同序 ⇒ **白名单成员的先后即调整次序**
        #    （`resolve_priority` 的排序键：场景优先集 → 字段级优先级 → 原序）。
        preferred_params=(
            'met_end_pos', 'vps_pos',
            'inj_t',
            'hold_pres_1', 'hold_spd_1', 'hold_t_1',
            'met_back_pres_1', 'met_rot_spd_1', 'pst_met_decomp_dist',
            'brl_temp_1', 'brl_temp_2', 'brl_temp_3', 'brl_temp_4', 'brl_temp_5',
            'brl_temp_6', 'brl_temp_7', 'brl_temp_8', 'brl_temp_9',
            'noz_temp',
        ),
        max_items=1,             # 一轮只调一个量（与其它场景一致）
        # 【注意】``target_mode='delta'``（默认）：拿不到重量口径 ⇒ 不能按比例解算行程。
        reason='打足阶段（短射）⇒ 充填量优先：胶量端 → 保压 → 熔体侧 → 料筒温度',
        priority=15,
    ),
    # --- S2 补缩：缩水类 ⇒ 只动保压组 ---
    # 【注意】**规则原料 SK-01 / SK-02** ⇒ 白名单 = 二段压力 + 二段时间；
    #    二段时间的定量锚点是**浇口封冻时间**（【待补】尚缺判据 ⇒ 目标值待校准）。
    ScenarioStrategy(
        scenario_code='shrinking_first',
        conditions=(
            {
                'field': 'selected_defect',
                'operator': 'in_set',
                'value': ('SHRINKAGE', 'UNDERSIZE', 'OVERSIZE', 'WARPING'),
            },
        ),
        allowed_params=('hold_pres_1', 'hold_t_1'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('hold_pres_1',),
        max_items=1,
        reason='充填已足 ⇒ 只动保压：二段压力与二段时间（二段时间锚点是浇口封冻）',
        priority=20,
    ),
    # --- S3 外观：飞边 ⇒ 降压或减胶量 ---
    # 【注意】**规则原料 FL-01**（降二段压力）/ **FL-02**（减胶量，充填比例 ≤ 98%）
    #    ⇒ 白名单只留这两个主旋钮；目标值待校准（FL-02 的 98% 上限）。
    # 【注意】优先项取 ``met_end_pos``（减胶量）—— 飞边是型腔压力过高，
    #    胶量端是充填量第一旋钮。
    # 【注意】**用户口径**：飞边**可能是模具问题而不是工艺问题**（规则原料 FL-06：
    #    不带二段的充填件本身就飞边 ⇒ 判为模具问题，**不属工艺**）。
    #    ⇒ 本场景的前提应是「已排除模具问题」，但**该判据目前系统里没有信号**
    #    （【待补】需「不带二段的充填件」测试结果）⇒ 只能写进 ``reason``（进留痕），
    #    **不写成条件**（写了就等于该场景永不命中）。
    ScenarioStrategy(
        scenario_code='flash_first',
        conditions=(
            {'field': 'selected_defect', 'operator': 'in_set', 'value': ('FLASH',)},
        ),
        allowed_params=('hold_pres_1', 'met_end_pos'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_end_pos',),
        max_items=1,
        reason=(
            '飞边 ⇒ 型腔压力过高 ⇒ 减胶量或降二段压力'
            '（【注意】若不带二段的充填件本身就飞边 ⇒ 属模具问题，应先修模）'
        ),
        priority=30,
    ),
    # --- S3 外观：烧焦 ⇒ 熔体侧（背压 / 松退 / 螺杆转速）---
    # 【注意】**规则原料 BN-01** 要求「先提示修模/清模，不要先给参数建议」——
    #    **提示通道尚未具备**（【待补】需 4M 归因字段）⇒ 本条只给参数侧。
    # 【注意】**规则原料 BN-02**（降一段充填速度）落在**基线项**（注射速度）⇒ 不可用，
    #    故白名单只留熔体侧三项 + 保压压力。
    # 【注意】**用户口径**：烧焦**首要根因是模具排气不良**（规则原料 BN-01），
    #    调参 = 绕过根因 ⇒ 「已排气处理」本应是前提，但**没有信号**
    #    （【待补】）⇒ 只能写进 ``reason``（进留痕）。
    ScenarioStrategy(
        scenario_code='burn_first',
        conditions=(
            {'field': 'selected_defect', 'operator': 'in_set', 'value': ('BURN',)},
        ),
        allowed_params=(
            'met_back_pres_1',
            'pst_met_decomp_dist',
            'met_rot_spd_1',
            'hold_pres_1',
        ),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_back_pres_1',),
        max_items=1,
        reason=(
            '烧焦 ⇒ 熔体侧排查：背压 / 熔胶后松退 / 螺杆转速'
            '（【注意】首要根因是排气不良 ⇒ 应先修模/清模，不要先给参数建议）'
        ),
        priority=40,
    ),
    # --- S3 外观：气纹 ⇒ 查背压 ---
    # 【注意】拍板 G：气纹形态 = 「查背压」⇒ 优先项取 ``met_back_pres_1``。
    #    规则库实测：气纹类规则里背压（``MBP0``）是主要输出参数之一。
    # 【注意】白名单比拍板 G 宽（背压 + 保压压力 + 保压时间）—— 只留背压一个时，
    #    若本轮规则只推了其它旋钮，会出现“本场景无输出”。
    ScenarioStrategy(
        scenario_code='gasveins_first',
        conditions=(
            {'field': 'selected_defect', 'operator': 'in_set', 'value': ('GASVEINS',)},
        ),
        allowed_params=('met_back_pres_1', 'hold_pres_1', 'hold_t_1'),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        preferred_params=('met_back_pres_1',),
        max_items=1,
        reason='气纹 ⇒ 查背压（塑料含气 / 背压不足）',
        priority=50,
    ),
    # --- 兜底：缺省一轮只调一个量 ---
    # 【注意】``conditions=()`` ⇒ **恒命中**（空条件 = 无条件成立）⇒ 没命中任何
    #    具体场景时的缺省行为；``priority`` 排最后 ⇒ 具体场景永远优先。
    # 【注意】兜底恒命中 ⇒ **场景永不为 None** ⇒ 留痕里永远有「这一轮按什么场景裁决」。
    # 【注意】**白名单留空**（不限制）⇒ 兜底不窄化；基线项由禁入清单挡住。
    ScenarioStrategy(
        scenario_code='default_one_adjust',
        conditions=(),
        blocked_params=BASELINE_BLOCKED_PARAMS,
        max_items=1,
        reason='缺省一轮只调一个量',
        priority=100,
    ),
)


def sorted_scenario_strategies() -> Tuple[ScenarioStrategy, ...]:
    """返回场景清单（按 ``priority`` 升序 ⇒ 命中判定从靠前的开始）。"""
    return tuple(
        sorted(SCENARIO_STRATEGIES, key=lambda item: (item.priority, item.scenario_code))
    )


__all__ = [
    'BASELINE_BLOCKED_PARAMS',
    'DEFECT_STAGE_MAP',
    'SCENARIO_STRATEGIES',
    'STAGE_ORDER',
    'StageProgress',
    'UNKNOWN_STAGE',
    'derive_stage_progress',
    'rank_of_stage',
    'sort_defects_by_stage',
    'sorted_scenario_strategies',
    'stage_of_defect',
]
