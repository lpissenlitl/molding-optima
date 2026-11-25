"""工艺参数调优（optimize）Schema 定义。

两个入口（命名范式与 initialization.py 对齐：Process<动作>From<入口>）：
- ProcessOptimizeFromConditionSchema：业务主流程，POST /api/processes/algorithms/optimize/
  initialize 是其前置；mold/machine/polymer 已挂在 condition 上，后端全部可反查，前端只给 ID。
- ProcessOptimizeFromProvidedSchema：纯推理，调用方自带完整上下文，后端不查库不落库
  （路由尚未注册）。面向第三方系统集成（其库内没有我们的 masterdata，
  却同样有「缺陷 → 调优」诉求）。

契约要点：
- 三维上下文按实体归属分组（mold_info / machine_info / polymer_info），不扁平化
- 必填性分两层：维度对象本身必填；对象内字段的必填等级不在 pydantic，定义在
  algorithms/fuzzy/specs.py，由 OptimizeDataValidator 在算法入口校验
  ⇒ pydantic 里字段全是 Optional（传输形状 ≠ 契约强度）
- 三维 schema 与 initialization 的同名 schema 不同源（调优只消费规则筛选键与物理边界值）
- 无 process_set 维度：段数与模式属于当前工艺本身，已含在 parameter 基线内

设计取舍见 docs/process-schema-design-notes.md §1.1–1.4。

术语规范：
- parameter：入参 = 调优基线 / 手动修改覆盖（两个入口语义不同，见各自 docstring）；
  响应 = 新工艺参数（落库端点为完整对象，未落库端点为纯工艺字段）
- feedback：嵌套结构（defect / observations / tuning_result）
- suggestion：算法建议展示对象（含 source_type / recommendation_id / groups）
"""
from typing import Optional, List, Dict, Any  # noqa: F401 保留 Dict/Any 供后续子 schema 用

from pydantic import Field, model_validator

from extensions.schemas import BaseSchema
from .parameter import ProcessParameterSchema


# ============================================================================
# 入参 Schema（Feedback 子结构）
# ============================================================================

class DefectFeedbackDataSchema(BaseSchema):
    """缺陷反馈数据（与前端 DefectFeedbackData 对齐）。

    数据约束：
    - keyword_name：可空（用户未选时为 null；后端匹配走 keyword_name）
    - level：当 keyword_name='DEFECTFREE' 时为 null；其他情况按 fuzzy_level 选词
    - position：缺陷位置（产品区域描述，如 "DL飞边3"）
    - position_3d：可选的 3D 模型点选坐标
    """

    keyword_name: Optional[str] = Field(None, description="缺陷关键词名称（冗余存，可空）")
    level: Optional[str] = Field(None, description="缺陷档位（low/medium/high/...）")
    position: Optional[str] = Field("", description="缺陷位置")
    position_3d: Optional[Dict[str, float]] = Field(
        None, description="3D 模型点选坐标（可选）",
    )


class CycleObservationSchema(BaseSchema):
    """实测观察项。

    对齐前端 CycleObservation：
    - param_key：4 种参数类型之一（actual_product_weight / peak_pressure / ...）
    - value：单值字段，可为 null（未观测）
    """

    param_key: str = Field(
        ...,
        description="实测参数键：actual_product_weight / peak_pressure / injection_time / cycle_time",
    )
    value: Optional[float] = Field(None, description="实测值（未观测时为 null）")


class FeedbackSchema(BaseSchema):
    """反馈信息（嵌套在 InferRequest 内）。

    3 类反馈合一：
    - defects[]：缺陷反馈列表（多个，算法识别优先级）
    - observations[]：实测观察（按需传）
    - tuning_result：试模效果评价（对【该轮工艺参数】的整体评价）

    tuning_result：首轮 qualified/unqualified，第 2 轮起 qualified + effective/unchanged/ineffective
    """

    defects: List[DefectFeedbackDataSchema] = Field(
        default_factory=list, description="缺陷反馈列表（可空，可多个）",
    )
    observations: List[CycleObservationSchema] = Field(
        default_factory=list, description="实测观察列表（按需传）",
    )
    tuning_result: Optional[str] = Field(
        None,
        description=(
            "试模效果评价（对该轮工艺参数的整体评价，写入该轮 TuningRecord.result，"
            "并作为该轮 Recommendation.is_adopted 的训练标签）。"
            "前端枚举：qualified（合格）/ unqualified（不合格）/ effective（改善）/ "
            "unchanged（无变化）/ ineffective（变差）/ null（未评价）；"
            "首轮只提供 qualified/unqualified；第 2 轮起提供 qualified + 后三档"
        ),
    )


# ============================================================================
# 入参 Schema（三维上下文·调优精度旋钮，全部可选）
# ============================================================================
# 与 initialization.py 的同名维度【不复用】：调优不消费几何/密度等推导输入，
# 只取「规则筛选键 + 物理边界值」。字段名严格贴 masterdata ORM 字段名，
# 使 FromCondition（DB 反查）与 FromProvided（调用方直传）喂给算法的结构同构。


class OptimizeMoldInfoSchema(BaseSchema):
    """模具信息（调优精度上下文 · 按需最小集）。

    两类内容：
    1. **规则筛选键 + 周期余量**（product_category / target_cycle_time）；
    2. **制品级物理基准**（壁厚 / 制品重 / 流道 / 浇口）—— 冷却时间（CT）
       判级论域的权威源（冷却时间 ∝ 最大壁厚²，见 specs.py 的
       ``resolve_product_limits``）。

    字段名贴 masterdata ORM 字段名（Cavity / GatingSystem / Gate）。

    必填等级见 specs.py::OPTIMIZE_MOLD_INFO_FIELDS：都是可选。
    product_category 是精度旋钮（填了命中高特异度规则，不填退到默认规则，
    算法不报缺该值而不能运行），target_cycle_time 是同类；
    制品级字段缺失 ⇒ 冷却时间回落经验域，**不报错、不阻塞**。
    """

    product_category: Optional[str] = Field(
        None,
        description="产品大类（如 '空调' / '酒瓶'）；规则库精确筛选键之一（specificity 1/3）",
    )
    target_cycle_time: Optional[float] = Field(
        None, description="目标成型周期 [s]；判断能否用周期换质量",
    )

    # --- 制品级物理基准（Cavity：型腔壁厚）---
    max_wall_thickness: Optional[float] = Field(
        None,
        description=(
            "制品最大壁厚 [mm]；**冷却时间（CT）判级论域的物理基准输入**"
            "（冷却时间 ∝ 壁厚²）；缺失 ⇒ 冷却时间回落经验域"
        ),
    )
    ave_wall_thickness: Optional[float] = Field(
        None, description="制品平均壁厚 [mm]；平均壁厚（本轮算法未消费，先入契约备查）",
    )

    # --- 制品级物理基准（GatingSystem：流道 / 制品总重）---
    total_product_weight: Optional[float] = Field(
        None, description="制品总重 [g]；充填量基准候选输入（本轮算法未消费）",
    )
    runner_type: Optional[str] = Field(
        None, description="流道类型（冷流道 / 热流道 / ...）；本轮算法未消费，先入契约备查",
    )

    # --- 制品级物理基准（Gate：浇口类型）---
    gate_type: Optional[str] = Field(
        None, description="浇口类型（直浇口 / 侧浇口 / 点浇口 / ...）；本轮算法未消费，先入契约备查",
    )


class OptimizeMachineInfoSchema(BaseSchema):
    """设备信息（调优精度上下文 · 重点维度）。

    作用：给推荐值划定「这台机设得出来」的物理边界，并参与参数模糊等级判定。

    下限统一为 0，故不设 min_set_*：压力/速度/位置类参数不做功即为 0，
    只需保证推荐值不超上限。（温度不同，见 OptimizePolymerInfoSchema 的 min_*。）

    必填等级见 algorithms/fuzzy/specs.py::OPTIMIZE_MACHINE_INFO_FIELDS：
    max_set_decompression_pressure / max_set_decompression_speed 是「可选」
    （无对应规则参数族，不参与判级论域）；
    max_set_metering_pressure / max_set_metering_back_pressure 是「液压机必填」
    （全电机 HMI 物理上无此栏，缺失属正常）；
    其余 6 个（注射压力/速度、保压压力/速度、螺杆转速、**最大注射行程**）是「必填」
    ——缺上界不是精度下降，而是判级错误。
    【注意】**单位不在算法层考虑**：这里取的就是**界面值**（HMI 面板显示上限），
    算法侧直接用，**不做单位换算、不做单位一致性校验**。ORM 字段声明的单位仅作
    字段描述用。

    """

    # --- 驱动形式（InjectionMoldingMachine 主表）：「液压机必填」等级的评估前提 ---
    # 全电机无油缸，HMI 上根本没有「计量压力」输入栏，该字段缺失属物理正常；
    # 只有知道 drive_system 才能区分「该填没填」与「本来就不存在」
    drive_system: Optional[str] = Field(
        None, description="动力系统原始值（液压/电动/...），算法层标准化为 power_method",
    )

    # --- HMI 可设定上限（InjectionUnit「成型能力」段）---
    max_set_injection_pressure: Optional[float] = Field(None, description="最大可设定注射压力（HMI 界面值）")
    max_set_injection_speed: Optional[float] = Field(None, description="最大可设定注射速度（HMI 界面值）")
    max_set_holding_pressure: Optional[float] = Field(None, description="最大可设定保压压力（HMI 界面值）")
    max_set_holding_speed: Optional[float] = Field(None, description="最大可设定保压速度（HMI 界面值）")
    max_set_metering_pressure: Optional[float] = Field(None, description="最大可设定计量压力（HMI 界面值）")
    max_set_metering_back_pressure: Optional[float] = Field(None, description="最大可设定计量背压（HMI 界面值）")
    max_set_screw_rotation_speed: Optional[float] = Field(None, description="最大可设定螺杆转速（HMI 界面值）")
    max_set_decompression_pressure: Optional[float] = Field(None, description="最大可设定松退压力（HMI 界面值）")
    max_set_decompression_speed: Optional[float] = Field(None, description="最大可设定松退速度（HMI 界面值）")

    # --- 设备实测能力（InjectionUnit「行程」段）：位置类判级论域上界的唯一权威源 ---
    # 【注意】**必填**：行程缺失 ⇒ 位置类判级区间没有上界 ⇒
    # 「充填量第一优先」的规则失活 ⇒ 契约层直接报错（400），不回落经验论域。
    # 【注意】**必须在这里声明**：BaseSchema 是 ``extra="ignore"``
    # ⇒ 未声明的字段会被**静默丢弃** ⇒ 契约层会误判「缺行程」。
    max_injection_stroke: Optional[float] = Field(
        None, description="最大注射行程 [mm]（螺杆向前推进的最大距离）",
    )


class OptimizePolymerInfoSchema(BaseSchema):
    """材料信息（调优精度上下文 · 按需最小集）。

    两类价值：
    1. abbreviation 是规则库精确筛选键（specificity 1/2），缺了只能落到通用默认规则。
    2. 温度边界——调优会推荐料筒/喷嘴温度（建议分类含 brl_temp_ / noz_temp），
       而温度的物理上界来自材料（超 max_melt_temp 降解/变色），不来自机器。
       若无这些值，温度类推荐将重演「当前值×2」的猜测问题。

    与设备不同：温度的 0 无物理意义，故 min_* 与 max_* 都需要真实数据。

    字段名贴 Polymer（masterdata/models/material.py）。
    initialize 需要的 melt_density / 推荐剪切线速度等推导输入，调优不消费，不在此列。

    必填等级见 algorithms/fuzzy/specs.py::OPTIMIZE_POLYMER_INFO_FIELDS：都是可选。
    abbreviation 是精度旋钮（填了命中高特异度规则，不填退到默认规则），温度边界
    现阶段是「推荐」——不是因为不重要，而是 field_contract 的 condition_when 只能
    对本维度内的键求值，而温度的触发条件在维度外（本次调优是否涉及温度参数）。
    强行标必填会拦住纯压力类的调优，属过度约束。
    """

    abbreviation: Optional[str] = Field(
        None, description="材料简称（ABS/PC/PE...）；规则库精确筛选键",
    )
    min_melt_temp: Optional[float] = Field(None, description="最小熔体温度 [℃]")
    max_melt_temp: Optional[float] = Field(None, description="最大熔体温度 [℃]")
    recommended_melt_temp: Optional[float] = Field(None, description="推荐熔体温度 [℃]")
    min_mold_temp: Optional[float] = Field(None, description="最小模具温度 [℃]")
    max_mold_temp: Optional[float] = Field(None, description="最大模具温度 [℃]")
    recommended_mold_temp: Optional[float] = Field(None, description="推荐模具温度 [℃]")


class ProcessOptimizeFromConditionSchema(BaseSchema):
    """【工艺参数调优 - 业务主流程】基于 condition + 缺陷反馈调优推理。

    POST /api/processes/algorithms/optimize/

    业务语义：
      产品出现缺陷时，以已有工艺条件为锚点（当前工艺参数 + 缺陷反馈），
      算法自动给出推荐工艺并落新轮次。

    - condition_id：工艺条件 ID（必填，后端反查 mold/machine/polymer 上下文）
    - parent_seq_idx：基准业务编号（必填，与 condition_id 联合定位父节点）
    - parameter：手动修改覆盖（可选，flat 字段对齐 ProcessParameterSchema；前端
      嵌套 UI（settingProcessForm）→ flat 的翻译由前端 API 层负责）
    - feedback：反馈信息（嵌套结构）

    主动不传的字段（从 condition_id 反查）：
    - machine_id / polymer_id / mold_id / process_set
    - subrule_no（后端算法自动识别）
    - 上一轮 suggestion（后端实时推理）

    parameter 字段一律 flat（与 FromProvided 同形，key 均为 ORM 字段名）；
    稀疏覆盖与全量基线的差别只在数量，不在 length。
    """

    condition_id: int = Field(..., description="工艺条件 ID（必填）")
    parent_seq_idx: int = Field(
        ..., description="基准业务编号 seq_idx（必填，与 condition_id 联合定位父节点）",
    )
    parameter: Optional[ProcessParameterSchema] = Field(
        None,
        description=(
            "手动修改覆盖（flat 字段，与 FromProvided 同形；前端嵌套 form → flat "
            "的翻译由前端 API 层负责，详见 frontend/src/views/process/optimization/"
            "components/parameterTransform.ts 的 parameterToFlat）"
        ),
    )
    feedback: FeedbackSchema = Field(
        default_factory=FeedbackSchema, description="反馈信息",
    )

    @model_validator(mode="after")
    def _parameter_must_have_override(self):
        """parameter 不为 None 时必须至少有一个标量工艺字段（拦截「忘翻译」「误传空 dict」）。

        业务元数据字段由 service 层自动处理，不计入此校验——
        调优上下文里调用方只需关心「改了哪些工艺参数」，不需要重写业务元数据。

        通过条件：
        - parameter is None：合法。用户没改参数，service 从 DB 反查 baseline。
        - parameter 至少有一个非 None 标量工艺字段：合法。用户明确改了参数。
        - parameter 全 None（包括「空对象 {}」/「全是业务元数据」）：非法。
          这两种都属于前端忘翻译/误传空 dict 的 bug，应在 HTTP 边界直接报错。
        """
        if self.parameter is None:
            return self
        # 业务元数据字段：service 层处理，不算「工艺覆盖」
        _BUSINESS_META = frozenset({
            "parameter_no", "param_source", "seq_idx",
        })
        non_none = [
            (k, v) for k, v in self.parameter.model_dump(exclude_none=True).items()
            if k not in _BUSINESS_META and v is not None
        ]
        if not non_none:
            raise ValueError(
                "parameter 不为 None 时必须至少提供一个工艺字段"
                "（前端嵌套 form 忘翻译 / 误传空 dict / 全填业务元数据 "
                "三种异常都会落入此分支）"
            )
        return self


class ProcessOptimizeFromProvidedSchema(BaseSchema):
    """【工艺参数调优 - 纯推理，不查库不落库】调用方自带完整上下文。

    POST /api/processes/algorithms/optimize-from-provided/（待路由注册）

    适用场景：
    - 第三方系统集成：对方库内没有我们的 masterdata / ProcessCondition，
      但同样有「缺陷 → 推荐工艺」诉求，且往往已跑了多年工艺
    - 算法试算：只看建议，不落轮次记录

    与 FromCondition 的区别：不传 condition_id / parent_seq_idx，后端不反查、
    不落库；三维上下文由调用方直接提供。

    请求体：
    {
        "parameter": {...},         // 必填：调优基线（算法的作用对象）
        "feedback": {...},          // 必填：缺陷反馈（调优的触发原因）
        "mold_info": {...},         // 必填对象（product_category 为精度旋钮）
        "machine_info": {...},      // 必填对象（HMI 设定上限是硬约束）
        "polymer_info": {...}       // 必填对象（abbreviation 为精度旋钮）
    }

    陷阱：三维上下文传 {} 能过 pydantic，但进算法会被 OptimizeDataValidator 拒
    （字段级等级由 algorithms/fuzzy/specs.py 校验）。

    响应：suggestion 与 FromCondition 同构（groups / items），但无落库产物
    ——parameter 里没有 id / seq_idx（未落库），也没有 recommendation_id。
    """

    # --- 必填：调优的作用对象与触发原因 ---
    parameter: ProcessParameterSchema = Field(
        ..., description="调优基线：当前工艺参数（flat 字段，与 ProcessParameter 模型对齐）",
    )
    feedback: FeedbackSchema = Field(
        ..., description="缺陷反馈（无上一轮可调，defect 为空则调优不成立）",
    )

    # --- 必填：三维上下文（维度对象必须存在；字段级等级见 algorithms/fuzzy/specs.py）---
    # 字段名顺序与 initialize 保持一致：模具 → 设备 → 材料
    mold_info: OptimizeMoldInfoSchema = Field(
        ..., description="模具上下文（产品大类是规则库精确筛选键，可选精度旋钮）",
    )
    machine_info: OptimizeMachineInfoSchema = Field(
        ...,
        description="设备上下文（HMI 设定上限：算法硬约束，缺失则模糊等级判错、推荐值可能设不出来）",
    )
    polymer_info: OptimizePolymerInfoSchema = Field(
        ...,
        description="材料上下文（abbreviation 是规则库精确筛选键，可选精度旋钮；含温度边界）",
    )


# ============================================================================
# 出参 Schema（Suggestion 子结构）
# ============================================================================

class SuggestionItemSchema(BaseSchema):
    """单条建议项。

    对齐前端 Suggestion：
    - description：建议文本
    - direction：调整方向（increase / decrease / hold / check）
    - rule_refs：关联规则 ID 列表
    - param / current_value / recommended_value：业务字段名与调整前后值
    - decision_status / decision_reason：第2层的**本轮裁决状态**与原因
    - applied_value：**已采用项的实际落地值**（当轮响应 = 整合后参数集；
      历史回显 = 该轮落库参数 ⇒ 两者同源）

    【注意】本 schema **不是响应契约的守门人**（优化接口未用它做 response_model，
    响应体直接返回 dict）⇒ 实际载荷字段比这里多也不会被裁掉。
    此处声明是为了让契约与实际载荷**保持一致**（可读 + 可 model_validate）。
    """

    description: str = Field(..., description="建议文本")
    direction: Optional[str] = Field(
        None, description="调整方向：increase / decrease / hold / check",
    )
    rule_refs: Optional[List[str]] = Field(
        default_factory=list, description="关联规则 ID 列表",
    )
    param: Optional[str] = Field(
        None, description="业务字段名（如 'inj_pres_1'）",
    )
    current_value: Optional[float] = Field(
        None, description="调整前的当前值",
    )
    recommended_value: Optional[float] = Field(
        None, description="建议的目标值（未采用时只是建议）",
    )
    decision_status: Optional[str] = Field(
        None,
        description=(
            "本轮裁决状态：adopted 已采用 / yielded 让位 / deferred 暂缓；"
            "无值 = 历史轮次没有状态字段，或该建议未进候选集"
        ),
    )
    decision_reason: Optional[str] = Field(
        None, description="未采用的原因（中文）；已采用时为保留依据",
    )
    applied_value: Optional[float] = Field(
        None, description="实际落地值（仅已采用项有）",
    )


class SuggestionGroupSchema(BaseSchema):
    """同一类别的多个建议。

    与后端 Recommendation.recommendations 对齐（按 category 分组）：
    - category：类别名（如 '注射参数' / '保压参数'）
    - icon：类别图标（mdi iconify 名）
    - items：该类下的多条建议
    """

    category: str = Field(..., description="类别名")
    icon: Optional[str] = Field(None, description="类别图标（mdi iconify 名）")
    items: List[SuggestionItemSchema] = Field(
        default_factory=list, description="该类下的多条建议",
    )


class SuggestionSchema(BaseSchema):
    """算法建议（_infer_kernel 返回的核心对象）。

    设计要点：
    - source_type：算法来源（fuzzy / empirical / rule_miner / llm ...）
    - recommendation_id：落库后产生（关联后端 Recommendation 表）
    - groups：按类别分组的建议项
    """

    source_type: str = Field(..., description="算法来源类型")
    recommendation_id: Optional[int] = Field(
        None, description="推荐记录 ID（落库后产生）",
    )
    groups: List[SuggestionGroupSchema] = Field(
        default_factory=list, description="按类别分组的建议项",
    )


__all__ = [
    "DefectFeedbackDataSchema",
    "CycleObservationSchema",
    "FeedbackSchema",
    # 三维上下文（调优精度旋钮）
    "OptimizeMoldInfoSchema",
    "OptimizeMachineInfoSchema",
    "OptimizePolymerInfoSchema",
    # 两个入口
    "ProcessOptimizeFromConditionSchema",
    "ProcessOptimizeFromProvidedSchema",
    "SuggestionItemSchema",
    "SuggestionGroupSchema",
    "SuggestionSchema",
]