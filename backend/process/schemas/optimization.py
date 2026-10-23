"""molding-optima 工艺参数调优（optimize）Schema 定义

对应接口：
- POST /api/processes/algorithms/optimize/                  业务主流程（FromCondition）
- POST /api/processes/algorithms/optimize-from-provided/     纯推理（FromProvided、待路由注册）

两个入口（命名范式与 initialization.py 对齐：Process<动作>From<入口>）：
- ProcessOptimizeFromConditionSchema：业务主流程。initialize 是其前置，落库时
  mold/machine/polymer 已挂在 condition 上，后端全部可反查，前端只给 ID。
- ProcessOptimizeFromProvidedSchema：纯推理。调用方自带完整上下文，后端不查库不落库。
  面向第三方系统集成（其库内没有我们的 masterdata，却同样有「缺陷 → 调优」诉求）。

设计原则（2026-10-15 确认）：
- 上下文三维按实体归属分组（mold_info / machine_info / polymer_info），不扁平化：
  ① 与 DB 模式反查的三张表 1:1 对应，字段来源可追溯；
  ② 调用方可按自己「知道什么」分段填，不必在混合字段堆里判断；
  ③ 与 initialize 的 FromProvided 保持同一心智模型。
- 必填性分两层，与 initialization 完全同构：
  ① 维度对象本身必填（mold_info / machine_info / polymer_info 必须出现）——
     它们对应 AlgorithmContext 的必需 key，缺一个维度等于缺整类判级依据；
  ② 对象内字段的必填等级不写在 pydantic，而是定义在 algorithms/fuzzy/specs.py，
     由 OptimizeDataValidator 在算法入口校验。理由：pydantic 表达不了
     「液压机必填」这类条件必填；且算法层校验能让 service / 第三方 / CLI
     所有调用方自动受约束，而不是只守住一个 HTTP 入口。
     所以 pydantic 里字段全是 Optional —— 那是传输形状，不是契约强度。
- 调优的消费面与初始化不同：模具/材料只需极少数（多为规则筛选键与边界值），
  设备是重点（HMI 设定上限决定推荐值的物理可行性），故【不复用】initialization 的
  MoldInfoSchema / MachineInfoSchema / PolymerInfoSchema。
- optimize 无 process_set 维度：段数与模式（inj_stg / hold_stg / vps_mode ...）属于
  当前工艺本身，已包含在 parameter 基线内，不是外部配置。所以是三维而非四维。

调用链路（详见 docs/optimization-infer-design-status-2026-09-22.md）：
  Step 1: 入口适配  —— condition_id + parent_seq_idx（业务编号）反查 parent_param
  Step 2: 数据准备  —— parent_param.parameters 作为基线，可选 parameter 覆盖
  Step 3: 推理算法  —— recommendation_service.get_recommendations()（接口契约）
  Step 4: 落库       —— ProcessParameter + TuningRecord + Recommendation 原子事务

术语规范：
- parameter：调优基线 / 手动修改覆盖（两个入口语义不同，见各自 docstring）
- feedback：嵌套结构（defect / observations / tuning_result）
- new_parameter：算法推理后的新工艺参数（含 parameter_id）
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
    """缺陷反馈数据（与前端 DefectFeedbackData 对齐）

    数据约束：
    - keyword_id / keyword_name：可空（用户未选时为 null；后端匹配走 keyword_name）
    - level：当 keyword_name='DEFECTFREE' 时为 null；其他情况按 fuzzy_level 选词
    - position：缺陷位置（产品区域描述，如 "DL飞边3"）
    - position_3d：可选的 3D 模型点选坐标
    """

    keyword_id: Optional[int] = Field(None, description="缺陷关键词 ID（关联 RuleKeyword.id，可空）")
    keyword_name: Optional[str] = Field(None, description="缺陷关键词名称（冗余存，可空）")
    level: Optional[str] = Field(None, description="缺陷档位（low/medium/high/...）")
    position: Optional[str] = Field("", description="缺陷位置")
    position_3d: Optional[Dict[str, float]] = Field(
        None, description="3D 模型点选坐标（可选）",
    )


class CycleObservationSchema(BaseSchema):
    """实测观察项

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
    """反馈信息（嵌套在 InferRequest 内）

    3 类反馈合一：
    - defect[]：缺陷反馈列表（多个，算法识别优先级）
    - observations[]：实测观察（按需传）
    - tuning_result：增量反馈（effective / ineffective / null）
    """

    defect: List[DefectFeedbackDataSchema] = Field(
        default_factory=list, description="缺陷反馈列表（可空，可多个）",
    )
    observations: List[CycleObservationSchema] = Field(
        default_factory=list, description="实测观察列表（按需传）",
    )
    tuning_result: Optional[str] = Field(
        None, description="调机效果评价：effective / ineffective / null",
    )


# ============================================================================
# 入参 Schema（三维上下文·调优精度旋钮，全部可选）
# ============================================================================
# 与 initialization.py 的同名维度【不复用】：调优不消费几何/密度等推导输入，
# 只取「规则筛选键 + 物理边界值」。字段名严格贴 masterdata ORM 字段名，
# 使 FromCondition（DB 反查）与 FromProvided（调用方直传）喂给算法的结构同构。


class OptimizeMoldInfoSchema(BaseSchema):
    """模具信息（调优精度上下文 · 按需最小集）

    调优不消费模具几何（浇口/壁厚/流长是初始化的推导输入）。
    这里只留两类：规则精确筛选键 + 周期余量判断。

    字段名贴 Mold（masterdata/models/mold.py）。

    必填等级见 specs.py::OPTIMIZE_MOLD_INFO_FIELDS：都是可选。
    product_category 是精度旋钮（填了命中高特异度规则，不填退到默认规则，
    算法不报缺该值而不能运行），target_cycle_time 是同类。

    未来候选（本期未纳入，需成对使用才有意义）：
    - projected_area（在 GatingSystem 表，按 shot_index 选）
      + 机台 max_clamping_force（在 InjectionMoldingMachine 主表）
      → 飞边类推荐的压力上界。两者跨两张表，单独取其一无法算出所需锁模力。
    """

    product_category: Optional[str] = Field(
        None,
        description="产品大类（如 '空调' / '酒瓶'）；规则库精确筛选键之一（specificity 1/3）",
    )
    target_cycle_time: Optional[float] = Field(
        None, description="目标成型周期 [s]；判断能否用周期换质量",
    )


class OptimizeMachineInfoSchema(BaseSchema):
    """设备信息（调优精度上下文 · 重点维度）

    作用：给推荐值划定「这台机设得出来」的物理边界，并参与参数模糊等级判定。

    为何必需（2026-10-15 结论）：
    fuzzy 算法构造隶属度函数时需要参数论域 [min_val, max_val]。现状两处都不看设备：
    - RuleKeyword 覆盖到的参数：论域取 keyword.range_min/range_max（全厂通用值）
    - 未覆盖的参数：论域取 当前值×2（自我参照，等于猜）
    后果：同一套参数在 180MPa 与 350MPa 的机上被判成同一模糊等级，规则条件命中失真。
    算法侧接设备实际值的改造另行讨论，本 schema 先把契约钉死。

    下限统一为 0，故不设 min_set_*：压力/速度/位置类参数不做功即为 0，
    只需保证推荐值不超上限。（温度不同，见 OptimizePolymerInfoSchema 的 min_*。）

    未纳入的能力字段（对调优无意义，initialize 才需要）：
    screw_diameter / max_injection_volume / plasticizing_capacity 等。

    必填等级见 algorithms/fuzzy/specs.py::OPTIMIZE_MACHINE_INFO_FIELDS：除
    max_set_decompression_speed（可选）与 3 个「液压机必填」项外，这里的
    max_set_* 全部是必填——缺上界不是精度下降，而是判级错误。

    命名空间：本 schema 的字段名 == ORM 字段名（InjectionUnit / InjectionMoldingMachine）。
    fuzzy 的端口命名空间就是业务/ORM 名（FuzzyEngine.FIELD_NAME_ALIAS 为空 dict）。
    """

    # --- 驱动形式（InjectionMoldingMachine 主表）：「液压机必填」等级的评估前提 ---
    # 全电机无油缸，HMI 上根本没有「计量压力」输入栏，该字段缺失属物理正常；
    # 只有知道 drive_system 才能区分「该填没填」与「本来就不存在」
    drive_system: Optional[str] = Field(
        None, description="动力系统原始值（液压/电动/...），算法层标准化为 power_method",
    )

    # --- HMI 可设定上限（InjectionUnit「成型能力」段）---
    max_set_injection_pressure: Optional[float] = Field(None, description="最大可设定注射压力 [MPa]")
    max_set_injection_speed: Optional[float] = Field(None, description="最大可设定注射速度 [mm/s]")
    max_set_holding_pressure: Optional[float] = Field(None, description="最大可设定保压压力 [MPa]")
    max_set_holding_speed: Optional[float] = Field(None, description="最大可设定保压速度 [mm/s]")
    max_set_metering_pressure: Optional[float] = Field(None, description="最大可设定计量压力 [MPa]")
    max_set_metering_back_pressure: Optional[float] = Field(None, description="最大可设定计量背压 [MPa]")
    max_set_screw_rotation_speed: Optional[float] = Field(None, description="最大可设定螺杆转速 [rpm]")
    max_set_decompression_pressure: Optional[float] = Field(None, description="最大可设定松退压力 [MPa]")
    max_set_decompression_speed: Optional[float] = Field(None, description="最大可设定松退速度 [mm/s]")


class OptimizePolymerInfoSchema(BaseSchema):
    """材料信息（调优精度上下文 · 按需最小集）

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
    """【工艺参数调优 - 业务主流程】基于 condition + 缺陷反馈调优推理

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
    - ❌ machine_id / polymer_id / mold_id / process_set
    - ❌ subrule_no（后端算法自动识别）
    - ❌ 上一轮 suggestion（后端实时推理）

    parameter 字段一律 flat（与 FromProvided 同形）：
    - 算法契约源头就是 flat（AlgorithmContext.process_parameter，FIELD_NAME_ALIAS
      按 flat 业务名翻译为算法名），上游嵌套 = 多一层翻译、多一处故障点
    - 服务契约是镜像（ProcessParameterSchema 镜像 ORM，与 _to_full_dict 同源），
      用 flat 后调用方无歧义
    - 即使是「稀疏覆盖」（只带要改的几个键），也用 flat 形状——每个 key 都是
      ORM 字段名；与「全量基线」的差别只在数量，不在 length
    """

    condition_id: int = Field(..., description="工艺条件 ID（必填）")
    parent_seq_idx: int = Field(
        ..., description="基准业务编号 seq_idx（必填，与 condition_id 联合定位父节点）",
    )
    parameter: Optional[ProcessParameterSchema] = Field(
        None,
        description=(
            "手动修改覆盖（flat 字段，与 FromProvided 同形；前端嵌套 form → flat "
            "的翻译由前端 API 层负责，详见 views/process/optimization/components/"
            "parameterTransform.ts 的 parameterToFlat）"
        ),
    )
    feedback: FeedbackSchema = Field(
        default_factory=FeedbackSchema, description="反馈信息",
    )

    @model_validator(mode="after")
    def _parameter_must_have_override(self):
        """parameter 不为 None 时必须至少有一个标量工艺字段（拦截「忘翻译」「误传空 dict」）

        业务元数据字段（process_condition_id / param_code / param_source /
        parent_seq_idx / seq_idx）由 service 层自动处理，不计入此校验——
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
            "process_condition_id", "param_code", "param_source",
            "parent_seq_idx", "seq_idx",
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
    """【工艺参数调优 - 纯推理，不查库不落库】调用方自带完整上下文

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
    
    为何不放 rule_library_code：这是算法内部的资源选择（哪一套规则库），
    调优侧不需知道该概念。RuleQueryContext 已自带 fallback 链
    （user 指定 → 按 polymer_abbreviation + product_category 自动解析），
    上游完全可以自解，传出来只是多一个泄漏点。

    对象必填 + 字段等级由 specs.py 校验：传 {} 能过 pydantic，但进算法会被
    OptimizeDataValidator 拒（与 initialize 的 FromProvided 同一套两层设计）

    响应：与 FromCondition 同构的 suggestion（groups / items），但无落库产物
    ——没有 new_parameter.parameter_id / seq_idx，也没有 recommendation_id。

    两个入口 parameter 形状一致的说明（2026-10-15 统一为 ProcessParameterSchema）：
    - FromProvided 用全量基线：第三方需要明确契约，传不齐就是漏数据
    - FromCondition 用稀疏覆盖：调用方只带要改的几个键，service 按
      `_resolve_baseline`（入参优先，否则 ORM 反查）补齐未传的字段
    - 两者形状一致（key 都是 ORM 字段名），差异在「数量」而非「length」

    为何三维上下文在 FromProvided 必填、FromCondition 却不传：
    FromCondition 的上下文由后端从 condition 反查（DB 里已有），FromProvided 无人可查，
    只能调用方给。两者最终汇流到同一个 algorithm context，同一套契约校验。
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


# 注：rule_library_code 不在此处暴露。该字段是算法内部资源选择——上游自解或由
# service 从 condition.process_context_snapshot 注入，不该作为公共 HTTP 入参。

# ============================================================================
# 出参 Schema（Suggestion 子结构）
# ============================================================================

class SuggestionItemSchema(BaseSchema):
    """单条建议项

    对齐前端 Suggestion：
    - description：建议文本
    - direction：调整方向（increase / decrease / hold / check）
    - rule_refs：关联规则 ID 列表
    """

    description: str = Field(..., description="建议文本")
    direction: Optional[str] = Field(
        None, description="调整方向：increase / decrease / hold / check",
    )
    rule_refs: Optional[List[str]] = Field(
        default_factory=list, description="关联规则 ID 列表",
    )


class SuggestionGroupSchema(BaseSchema):
    """同一类别的多个建议

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
    """算法建议（infer 返回的核心对象）

    设计要点：
    - source_type：算法来源（fuzzy_rule / rule_miner / llm ...）
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