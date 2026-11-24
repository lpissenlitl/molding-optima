"""模糊推理算法模块。

algorithm_type='optimization'，由 condition service 通过 AlgorithmRegistry 编排 chain。

模块分层（每层职责单一，文件名各自自解释）：
- 【0 对外接口】specs: 调优入参契约（字段选择 + 必填等级）+ OptimizeDataValidator
  契约定在算法层，所有调用方（service / 第三方 / CLI）自动受约束
- 【1 编排】engine: FuzzyEngine 主流程；recommendations: 推荐结果产出；
  diagnostics: 诊断出口（每请求一个的诊断容器 + 结构化日志）
- 【2 规则库适配】library: 对外契约 library.contracts（AlgorithmResourceRepository 协议 +
  RuleQueryContext，零依赖）/ library.rules（规则资源：取数 + 规则串语义）/ library.keywords（关键字资源）
  / library.repository（资源集合：编排选库→收集→组装，算法实际要用的资源）
- 【3 内核】fuzzy_core: 归属它自己的**输入契约**（profiles: KeywordProfile / RuleProfile）
  + 论域实例（features: FuzzyFeature）+ 规则串解析（rules: FuzzyRule / NumTskRule）
  + 推理网络（nets: FuzzyRuleNet / NumTskRuleNet）

命名约定：`specs` = 对外接口格式（与 expert 包同名同层）；`profiles` = 内核输入契约；`engine` = 模糊推理引擎（与类名 `FuzzyEngine` 对应）；`recommendations` = 推理结果 → 对外推荐契约（与 `base.AlgorithmRecommendation` 同词根）。

【注意】**算法命名空间在本包内**（``field_names`` 字段名映射 + ``device_limits``
算法族表）：算法字段名（``IV0`` / ``IP0`` / ``MEL``）是**模糊规则库的内部命名**，
只在 fuzzy 推理网络里成立 ⇒ 命名契约与被命名的算法住同一个包；
**跨出算法边界的字段名一律是 ORM 业务字段名**（``inj_spd_1`` / ``met_end_pos``），
service 层与其它算法线不认算法名。

【注意】`recommendations` 产出的具体类型是 **`FuzzyRecommendation`**（`base.AlgorithmRecommendation` 的**子类**）——
比基类多挂一个 `conflict` 视图：
**同参数命中规则方向相反时**非空，用来显式暴露「多条规则互相抵消」这种静默失败。
**只加标记、不改数值**（建议值 / 方向 / 置信度一字未变）；
基类 `to_dict()` 的键集合**一字未改** ⇒ llm / empirical 两个算法的输出**逐位不变**。
"""

from . import device_limits, field_names  # noqa: F401
from .engine import FuzzyEngine
from .specs import (
    OPTIMIZE_MACHINE_INFO_FIELDS,
    OPTIMIZE_POLYMER_INFO_FIELDS,
    OPTIMIZE_MOLD_INFO_FIELDS,
    REQUIRED_OPTIMIZE_MACHINE_FIELDS,
    REQUIRED_OPTIMIZE_POLYMER_FIELDS,
    REQUIRED_OPTIMIZE_MOLD_FIELDS,
    OptimizeDataValidator,
    VALID_DEFECT_LEVEL_WORDS,
    VALID_DEFECT_LEVEL_WORDS_TEXT,
    is_valid_defect_level_word,
)

__all__ = [
    "FuzzyEngine",
    "OPTIMIZE_MACHINE_INFO_FIELDS",
    "OPTIMIZE_POLYMER_INFO_FIELDS",
    "OPTIMIZE_MOLD_INFO_FIELDS",
    "REQUIRED_OPTIMIZE_MACHINE_FIELDS",
    "REQUIRED_OPTIMIZE_POLYMER_FIELDS",
    "REQUIRED_OPTIMIZE_MOLD_FIELDS",
    "OptimizeDataValidator",
    "VALID_DEFECT_LEVEL_WORDS",
    "VALID_DEFECT_LEVEL_WORDS_TEXT",
    "is_valid_defect_level_word",
]
