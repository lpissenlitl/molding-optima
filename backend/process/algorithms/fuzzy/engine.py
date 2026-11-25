"""模糊推理引擎 - 主入口。

基于模糊规则进行缺陷修正推荐。

【注意】这里的"层"按**结论形态**划分（这条规则的结论能不能算出数值），
   与规则库层级（base / 产品库 / specificity）**完全无关**：

- 数值层 (NumTskRuleNet)   → 数值/百分比结论（``X_add_3.8`` / ``X_reduce_30%``）
- 提示层 (FuzzyRuleNet)    → 检查/弹窗结论（``X_adjust_请检查锁模力是否不合理。``）
                            + 模糊等级结论（``X_add_low``，兼容 Rule.dat 风格）
- 合并策略                → 同层聚合 + 跨层覆盖
"""

import logging
from dataclasses import replace
from typing import List, Dict, Any, Optional, Tuple

from process.algorithms.base import (
    AlgorithmBase,
    AlgorithmRecommendation,
    AlgorithmRegistry,
    filter_unchanged,
)
# 【注意】**物理常量来自中立层**（`algorithms/common/material_physics.py`）：材料大类解析是
#    **物理事实**，不属于任何算法包的私有口径 ⇒ 与专家引擎共用同一份。
from process.algorithms.common.material_physics import (
    DEFAULT_COOL_FACTOR,
    parse_material_family,
)
from process.algorithms.fuzzy.diagnostics import (
    Diagnostic,
    current_diagnostic,
    request_diagnostics,
)
from process.algorithms.fuzzy.recommendations import (
    RuleAdjustment,
    aggregate,
    to_recommendations,
)
from process.algorithms.fuzzy.fuzzy_core.macros import (
    downgrade_level_word,
    level_to_domain_value,
    resolve_bucket,
)
from process.algorithms.fuzzy.fuzzy_core.models.features import FuzzyFeature
from process.algorithms.fuzzy.fuzzy_core.models.nets import (
    FuzzyRuleNet,
    NumTskRuleNet,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import parse_rule
from process.algorithms.fuzzy.fuzzy_core.profiles import (
    DIMENSION_PARAMETER,
    KeywordProfile,
)
from process.algorithms.fuzzy.fuzzy_core.rules_filter import (
    FilteredRules,
    build_rule_objects,
)
# 【注意】**设备上限的「查表 + 翻译」在本包**（`algorithms/fuzzy/device_limits.py`）：
#    算法层做**查表**（`lookup_limit` / `param_family`）与**翻译**
#    （`to_family_limits`：业务键区间表 → 算法族上界表）
#    —— **不知道**参数有没有上下限、也不持有「哪个族配哪个字段」。
#    **上限表的来源声明与取值都由 service 层负责、经 context 传入**
#    ⇒ 算法层不碰 ORM 字段名（context 里是**业务键**区间表）。
from .device_limits import (
    lookup_limit,
    param_family,
    to_family_limits,
)
from .field_names import (
    to_algo_params,
    to_business_name,
)
from process.algorithms.fuzzy.specs import (
    is_time_domain_field,
    resolve_domain_limits,
    resolve_product_limits,
    resolve_temperature_limits,
)
from process.algorithms.fuzzy.library.contracts import (
    AlgorithmResourceRepository,
    RuleQueryContext,
)


logger = logging.getLogger(__name__)

# 元数据来源标记：'guessed' 表示这个论域是按实时值猜的，不是 RuleKeyword 权威元数据
FIELD_SOURCE_GUESSED = 'guessed'

# ============================================================================
# 论域来源标记（B1-4 统一口径）
# ============================================================================
# 说的是「**这个论域的边界最终从哪来**」，与 `FIELD_SOURCE_GUESSED`
# （说的是「**关键字元数据**从哪来」）是两回事 ⇒ 两个字段**独立**填写。
#
# 【注意】**禁止静默兜底**：凡是没拿到权威源的参数，都必须落到下面这些
#    **明确的**标签上，并在诊断清单里可见 ⇒ 不允许「不知道论域从哪来，
#    却看起来像个正常值」。
DOMAIN_SOURCE_DEVICE = 'device'                  # 机台可设定上限（**所有参数一视同仁**）
DOMAIN_SOURCE_MATERIAL = 'material'              # 材料温度区间（温度类）
DOMAIN_SOURCE_PRODUCT = 'product'                # 制品级物理推导基准（产品类，如 CT）
DOMAIN_SOURCE_EXPERIENCE = 'experience_domain'   # RuleKeyword 经验域（**无权威源**）
# 'kept_experience_domain' 表示「权威源已拿到，但**守卫拒绝**用它」
#   ⇒ 保留了 RuleKeyword 经验域。触发条件：
#   H1（当前值 > 该参数自己的可设定上限，见 `_apply_declared_bound`）
#   / G7（当前值超出产品域物理上界，见 `_apply_product_bound`）。
DOMAIN_SOURCE_KEPT_EXPERIENCE = 'kept_experience_domain'
DOMAIN_SOURCE_GUESSED = 'guessed'                # 整段论域由引擎按当前值推测
DOMAIN_SOURCE_UNMARKED = 'unmarked'              # 未标注（外部构造的档案 / 测试替身）


def _as_float(value: Any) -> Optional[float]:
    """任意值 → float；``None`` / bool / 非数值 ⇒ ``None``（不抛异常）。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _product_limit_for(
    param_name: str,
    product_limits: Dict[str, Tuple[float, float]],
) -> Optional[Tuple[float, float]]:
    """算法参数名 → 该参数的产品域论域边界（无权威源返回 None）。

    【注意】**两级匹配**（时间类既有整段也有分段，与位置类同形）：
    - 整段参数（``CT`` / ``IT`` / ``ID``）→ **精确匹配**；
    - 分段参数（``PT0``~``PT4``）→ **族前缀匹配**
      （族前缀由 :func:`specs.param_family` 的正则取 ⇒ 命名规则仍是单一真相源）。

    Args:
        param_name: 算法侧参数名（如 'CT' / 'PT0'）。
        product_limits: {算法参数名: (下界, 上界)}（见
            :func:`specs.resolve_product_limits`）。

    Returns:
        (下界, 上界)；该参数不是产品类 / 没有权威源时返回 ``None``。
    """
    if not param_name or not product_limits:
        return None
    bounds = product_limits.get(param_name)
    if bounds is not None:
        return bounds
    family = param_family(param_name)
    if family is None:
        return None
    return product_limits.get(family)


class FuzzyEngine(AlgorithmBase):
    """模糊推理算法 - 基于模糊规则进行缺陷修正。

    algorithm_type='optimization'，由 condition service 通过 AlgorithmRegistry 编排 chain。
    适用于已知规则的场景，如工艺缺陷修正。
    """

    algorithm_name = "模糊推理"
    algorithm_type = "optimization"
    algorithm_subtype = "fuzzy"

    def __init__(self, repository: Optional[AlgorithmResourceRepository] = None):
        """构造引擎。

        Args:
            repository: 资源仓库契约（`AlgorithmResourceRepository` 协议）。
                传 None 时按**配置**选默认实现（`library/provider.py`）：
                `settings.FUZZY_LIBRARY_SOURCE` 为 `'db'`（默认）走数据库，
                为 `'file'` 走本地文件。
                且**延迟到首次访问数据时才导入**——
                这样 `import engine` 不会把 Django ORM 拖进来，
                编排层可以在没有数据库环境时被 import 和调用。

                【注意】**显式注入优先于配置**：传了实例就只用它，
                  忽略 `FUZZY_LIBRARY_SOURCE`。
        """
        self._repo = repository
        # 【注意】诊断数据**不放实例属性** —— 本引擎是模块级单例（见文件末尾
        #    `AlgorithmRegistry.register`），放实例属性会让并发请求互相清空/串写
        #    （已实测复现：A 的条目被 B 覆盖）。生产路径走**每请求一个**的容器
        #    （`diagnostics.request_diagnostics()`），见 `diagnostics.py`。
        # 这个 `_last_diag` 是「最近一次请求的诊断」的槽位：请求结束后仍能读到
        # （诊断脚本 / 快照脚本依赖这个约定）。
        # 【注意】并发下它会被别的请求覆盖 ⇒ 生产**不依赖**它（诊断已由
        #    `request_diagnostics` 打成结构化日志）。
        self._last_diag = Diagnostic()

    def _get_repository(self) -> AlgorithmResourceRepository:
        """取资源仓库契约（默认实现延迟导入）。

        【注意】默认实现由 `library/provider.py::resolve_repository` 按配置选：
          数据库来源（默认）或本地文件来源（`FUZZY_LIBRARY_SOURCE='file'`）。
        """
        if self._repo is None:
            from process.algorithms.fuzzy.library.provider import resolve_repository
            self._repo = resolve_repository()
        return self._repo

    def recommend(self, context: dict) -> List[AlgorithmRecommendation]:
        """根据缺陷反馈返回参数调整推荐。

        本方法只做**兜底**；真正的流程在 `_recommend()`。
        任何未预期异常都在这里被拦住，转换成"空推荐"，
        而不是让异常冒到 condition service 去炸掉整条 optimize 链。

        Args:
            context: {
                'feedback': {                        # 反馈 dict（含 defects / observations / tuning_result）
                    'defects': [...],
                    'observations': [...],
                    'tuning_result': str | None,
                },
                'process_parameter': {...},          # 当前参数
                'iteration_trend': {...},            # 迭代趋势
                'machine_info': {...},               # 设备 dict（与 HTTP schema / service 接口对齐）
                # --- FuzzyEngine 扩展上下文（以子对象形态传，避免后续动算法接口） ---
                'polymer_info': {                    # 完整材料 dict（与 schema 字段名对齐）
                    'abbreviation': 'PE',
                    # 预留：melt_flow_rate / density / ...
                },
                'mold_info': {                       # 完整模具 dict（与 schema 字段名对齐）
                    'product_category': '酒瓶',
                    # 预留：cavity_count / gate_type / ...
                },
                'rule_library_code': 'R20240516093115',  # 可选（只用它；None = 全部模糊库，适用性交由规则级判定）
            }

        Returns:
            List[AlgorithmRecommendation]

        【注意】**出口已译成业务字段名**（``param_name`` = ORM 业务字段名）⇒
            算法名只存在于引擎内部，不外传给 service 层。
        """
        # 诊断容器**每请求新建**：本引擎是模块级单例（见文件末尾
        # `AlgorithmRegistry.register`），放实例属性会让并发请求互相清空/串写
        # （已实测复现）。详见 `diagnostics.py`。
        with request_diagnostics() as diag:
            try:
                result = self._recommend(context)
            except Exception:
                # 第 0 层故障边界（编排层兜底）：异常止步于此。
                # 模糊算法失败不应该让整条 optimize 链 500。
                logger.exception('[FuzzyEngine] 模糊推理异常，已降级为空推荐')
                result = []

        # 出口翻译：**算法字段名 → 业务字段名**（算法名不外传）
        # 【注意】翻译放在**裁剪与诊断之后** ⇒ 引擎内部（裁剪查族表 / 诊断留痕）
        #   继续用算法名，两个命名空间不混。
        for rec in result:
            rec.param_name = to_business_name(rec.param_name) or rec.param_name

        # 丢掉「值没变」的建议 —— 放在**裁剪之后**：裁剪可能把推荐值压回当前值
        # （封顶值恰好等于当前值）⇒ 那条建议同样没有可执行内容。
        result = filter_unchanged(result)

        # 把诊断容器移交给实例槽位 ⇒ 请求返回后仍能读到本次诊断
        # （`tests/fuzzy_kernel/_snapshot_core.py` 与 `_verify_e2_offline.py` 依赖这个约定）。
        self._last_diag = diag
        return result

    def _recommend(self, context: dict) -> List[AlgorithmRecommendation]:
        """主流程：5 步一条直线。

        1) 认缺陷   —— 从 feedback 取缺陷名 / 严重程度 / 位置
        2) 拉规则   —— 按缺陷 + 材料 + 产品选规则（DB 故障在此隔离）
        3) 拆规则   —— 第 4 层 filter：规则串只拆一次 → 分类 → 建对象
        4) 并行推理 —— 数值层走 TSK，提示层走文本建议 / Mamdani（层间互不影响）
        5) 合并     —— 同参数聚合 + 跨层覆盖

        【注意】**入参体检不在这里**：越限识别与拒绝是**入参校验** ⇒ 归 service 层
        （``services/shared/param_limits.py``）⇒
        算法层只管「算出建议」，不判传进来的值合不合规。
        """
        # 设备上限表（**service 层解析好、经 context 传入**）—— 算法层不碰 ORM 字段名。
        # 【注意】**只有一张表**：机台**可设定**上限（族 / 整段名 → 上限）⇒
        #   所有参数一视同仁（位置参数与压力 / 速度参数同构，差别只在
        #   「上限取自哪个设备字段」：实测行程 vs 可设定最大值）。
        #   这张表既作**判级论域上界**，也作**推荐值物理天花板**（裁剪）。
        #   缺表（机台没录 / 调用方没给）⇒ 空表 ⇒ 相关逻辑按「缺权威源」处理
        #   （回落经验域、不裁剪、不报错）。
        # 【注意】**传入的是业务键区间表**（业务字段名 → 允许区间）⇒
        #   「业务键 → 算法族」的翻译**在算法内部做**（算法名不外传）。
        param_limits = to_family_limits(context.get('param_limits') or {})

        # 1) 认缺陷 —— **选取已在 service 预处理层做完**（只做一次）
        #    （见 `services/optimize_chain/defect_selection.py::select_defect`）
        #    ⇒ 本引擎**不再自己挑缺陷**，只读整理结果。
        # 选取依据留痕（决策级，与 `field_reports` / `diagnostics` 那两个
        # 规则级清单分开）—— 记的是预处理层写回 feedback 的完整 trace。
        trace = (context.get('feedback') or {}).get('defect_selection')
        if trace:
            self._diag.selections.append(trace)

        # 缺陷上下文（缺陷名 / 严重程度 / 位置）—— 取自预处理层的整理结果
        defect_ctx = self._extract_defect_context(context)
        if not defect_ctx:
            logger.warning('[FuzzyEngine] 反馈中未指定缺陷类型（keyword_name），跳过推荐')
            return []
        defect_name = defect_ctx['defect_name']

        # 2) 拉规则
        # context['polymer_info'] / context['mold_info'] 是子对象 dict
        # （字段名与 HTTP schema / service 接口对齐，避免命名割裂），这里只取算法关心的字段
        # （abbreviation / product_category），后续若算法需新字段直接从对应子对象取。
        repo = self._get_repository()
        query_ctx = RuleQueryContext(
            defect_name=defect_name,
            defect_level=defect_ctx.get('level'),
            defect_position=defect_ctx.get('position'),
            polymer_abbreviation=(context.get('polymer_info') or {}).get('abbreviation'),
            product_category=(context.get('mold_info') or {}).get('product_category'),
            rule_library_code=context.get('rule_library_code'),
            # 本轮可见的规则库（由 service 层按租户归属决定）
            libraries=context.get('libraries'),
        )
        try:
            all_rules = repo.get_rules(query_ctx)
        except Exception:
            # 第 0 层故障边界的具体落点：规则库挂了（DB 异常）也只降级为空推荐，
            # 且日志级别是 error（要人看），与「没有适用规则」的 info 明确区分。
            logger.exception('[FuzzyEngine] 规则库查询失败，已降级为空推荐: %s', query_ctx)
            return []
        if not all_rules:
            logger.info('[FuzzyEngine] 未找到适用规则: %s', query_ctx)
            return []

        # 3) 拆规则 —— 规则串只拆一次 → 分类 → 建对象
        #    拆解产物同时供「分类」「建对象」「收参数名」三处使用；
        #    编排层因此不做分流、不解析规则串。
        filtered = build_rule_objects(all_rules)
        if filtered.skipped:
            self._diag.diagnostics.append(
                {'layer': 'numeric', 'skipped': filtered.skipped})
            logger.warning(
                '[FuzzyEngine] 跳过 %d 条不可推理规则（其余规则照常推理）: %s',
                len(filtered.skipped), [s['reason'] for s in filtered.skipped][:5])

        # 去掉空值字段：论域计算需要数值，None 会让隶属度函数直接抛错
        # 【注意】**翻译在算法内部做**：context 传的是**业务字段名**，
        #   引擎内才译成算法字段名 ⇒ 算法名只存在于推理这一侧，不外传。
        process_parameter = to_algo_params({
            k: v for k, v in (context.get('process_parameter') or {}).items()
            if v is not None
        })
        # 【注意】编排层**不传** `iteration_trend` ⇒ 恒为 'unknown' ⇒ 系数恒 1.0。
        #    该乘数策略已判定**业务上不成立**（历史趋势 ≠ 本次建议幅度），
        #    故**刻意不启用**。
        trend = context.get('iteration_trend', {}) or {}
        adjustment_factor = self._trend_to_factor(trend.get('trend', 'unknown'))

        # 4) 并行推理（层间隔离：一层失败不影响另一层）
        #    判级论域上界 = 设备实测值（仅**必填等级**字段：必填字段必须校验
        #    并替换，其余字段的论域可以用默认值）。
        #    缺失的必填字段在 service 层已被校验器拦（400），到这里不会有缺失。
        #    设备类论域上界 = **机台对每个参数的可设定上限**（权威源 = 设备维度）
        #    —— **一张表覆盖所有参数**（位置参数与压力 / 速度参数同构）。
        #    【注意】位置类真实值域可达 27~716，远超规则库种子域（IL [0,150] / MEL [0,200]）
        #    ⇒ 回落经验域时这组「充填量第一优先」的规则会失活。
        #    缺权威源（机台没录上限）⇒ 回落经验域，不报错、不阻塞。
        domain_limits = resolve_domain_limits(param_limits)
        #    温度类论域 = **材料温度区间**（权威源 = 材料维度，不是设备）：
        #    温度类没有设备上限字段（`max_set_*` 不含温度），而材料的熔体/模温
        #    区间是物理红线。缺权威源 ⇒ 该参数回落经验域，不阻塞（见 specs）。
        temperature_limits = resolve_temperature_limits(
            context.get('polymer_info') or {})
        #    产品类论域 = **制品级物理推导基准**（权威源 = 产品维度）：
        #    冷却时间 CT 的判级上界 = f(制品最大壁厚, 材料大类)
        #    —— 冷却时间 ∝ 壁厚²（Fourier 热扩散）⇒ 厚壁件要冷却更久。
        #    【注意】这是**判级基准**、不是设备天花板：冷却时间没有机台可设上限
        #    （机台 HMI 不提供）⇒ 与设备域语义不同、不可混用。
        #    缺权威源（型腔壁厚没录）⇒ 回落经验域，不报错、不阻塞。
        product_limits = resolve_product_limits(
            context.get('mold_info') or {},
            context.get('polymer_info') or {},
        )
        self._trace_product_family(context, product_limits)
        numeric_results = self._infer_numeric_layer(
            filtered, process_parameter, defect_ctx, domain_limits,
            temperature_limits, product_limits)
        advisory_results = self._infer_advisory_layer(
            filtered, process_parameter, domain_limits, defect_ctx,
            temperature_limits, product_limits)

        # 5) 合并：同层聚合 + 跨层覆盖
        #    归并与格式化逻辑已抽到 recommendations.py（纯函数层），这里只负责“调一下”——
        #    引擎本身不掺和聚合细节。
        aggregated, advice_items = aggregate(numeric_results, advisory_results)
        recommendations = to_recommendations(
            aggregated=aggregated,
            advice_items=advice_items,
            adjustment_factor=adjustment_factor,
            current_params=process_parameter,
        )

        # 6) 机台物理上限裁剪：推荐值不得超出这台机 HMI 可设定的范围
        #    （规则库论域普遍宽于机台上限，不裁会给出操作工输不进去的值）
        #    复用第 0 步已解析的 `param_limits`（同一份上限，不重算）
        return self._apply_machine_limits(recommendations, param_limits)

    def _apply_machine_limits(
        self,
        recommendations: List[AlgorithmRecommendation],
        limits: Dict[str, float],
    ) -> List[AlgorithmRecommendation]:
        """按机台物理上限裁剪推荐值（越限则封顶，方向重算）。

        规则库论域上界普遍**宽于**机台 HMI 可设定范围（实测注射压力论域 0~200，
        同一台机上限 100），不裁剪就会给出操作工根本输不进去的推荐值。

        缺上限（机台没填）⇒ **不裁剪**，只记 warning：缺数据不等于不能给建议，
        也不拦请求。

        Args:
            recommendations: 聚合层产出的推荐列表
            limits: {算法参数前缀: 机台物理上限}（service 层解析好、经 context
                传入的 ``param_limits``）

        Returns:
            裁剪后的推荐列表（就地修改原对象）
        """
        if not limits:
            return recommendations

        clipped: List[AlgorithmRecommendation] = []
        for rec in recommendations:
            value = rec.recommended_value
            if value is None:
                clipped.append(rec)
                continue

            limit = lookup_limit(rec.param_name, limits)
            if limit is None or value <= limit:
                clipped.append(rec)
                continue

            # 越限 ⇒ 封顶，并按裁剪后的**相对方向**重算 direction：
            # 规则说「调高」但已被物理上限压回，实际效果是「调低」，
            # 方向若不重算，前端会显示成「↑ 180→100」这种自相矛盾的箭头。
            rec.recommended_value = limit
            rec.direction = (
                'increase' if limit > rec.current_value
                else 'decrease' if limit < rec.current_value
                else 'hold'
            )
            clipped.append(rec)

            self._diag.field_reports.append({
                'layer': 'machine_limits',
                'param': rec.param_name,
                'origin_value': value,
                'clipped_to': limit,
            })
            logger.info(
                '[FuzzyEngine] 推荐值超出机台物理上限，已封顶: %s %.4f → %.4f',
                rec.param_name, value, limit)

        return clipped

    def is_available(self, context: dict) -> bool:
        """判断是否可用。"""
        if not self._extract_defect_context(context):
            return False

        # 【注意】**编排层不传 `iteration_trend`** ⇒ 该分支恒不触发（context 里没这个键）。
        #    启用前必须先解决「终态无推荐 ⇒ fail-fast 报『算法暂不可用』」的问题。
        trend = context.get('iteration_trend', {}) or {}
        if trend.get('trend') == 'final':
            return False

        return True

    def run(self, context: dict) -> List[AlgorithmRecommendation]:
        """统一入口：包装 recommend()。

        algorithm_type='optimization'，返回 List[AlgorithmRecommendation]。
        """
        return self.recommend(context)

    # -----------------------------------------------------------------------
    # 诊断数据读取（兼容层）
    #
    # 【注意】这两个属性是**读取入口**，不是数据存储位置 —— 真实存储在
    #    **每请求一个**的诊断容器里（见 `diagnostics.py`）。
    #    生产代码要取诊断请用 `diagnostics.current_diagnostic()`。
    # -----------------------------------------------------------------------

    @property
    def _diag(self) -> Diagnostic:
        """本次执行正在用的诊断容器。

        生产路径（`recommend()` 内）⇒ `current_diagnostic()` 给的 per-request
        容器（并发隔离）；请求已结束或脱离 `recommend()` 直接调内部方法 ⇒
        实例槽位 `_last_diag`。
        """
        diag = current_diagnostic()
        return diag if diag is not None else self._last_diag

    @property
    def _field_reports(self) -> List[Dict[str, Any]]:
        """字段定性降级清单（当前执行上下文的）。"""
        return self._diag.field_reports

    @property
    def _diagnostics(self) -> List[Dict[str, Any]]:
        """规则级诊断清单（当前执行上下文的）。"""
        return self._diag.diagnostics

    # -----------------------------------------------------------------------
    # 内部方法
    # -----------------------------------------------------------------------

    @staticmethod
    def _extract_defect_context(context: dict) -> Dict[str, Any]:
        """从 feedback 里取缺陷上下文（缺陷名 / 严重程度 / 位置）。

        缺陷上下文只含算法消费的三个字段：
        - `keyword_name`：英文缺陷码（SHORTSHOT / FLASH / ...），
          与 `RuleMethod.defect_code`、`RuleKeyword.keyword_name` 对齐
        - `level`：严重程度（low / medium / high），与规则前件的档位词一致
        - `position`：缺陷位置（`DL` + 缺陷名 + 段号）

        【注意】**选取不在本引擎** —— 缺陷选取由 service 预处理层做**一次**
           （`services/optimize_chain/defect_selection.py::select_defect`），
           结果写回 ``feedback``（``defects`` 只剩本轮处理的那条）；
           本方法**只读、不挑**。
           返回形状保持不变（`defect_name` / `level` / `position`）。
        """
        defects = (context.get('feedback') or {}).get('defects') or []
        selected = defects[0] if defects else {}
        defect_name = selected.get('keyword_name') if isinstance(selected, dict) else None
        if not defect_name:
            return {}
        return {
            'defect_name': defect_name,
            'level': selected.get('level'),
            'position': selected.get('position'),
        }

    @staticmethod
    def _trend_to_factor(trend: str) -> float:
        """迭代趋势 → 调整系数。

        【注意】**刻意未启用**：编排层不传 `iteration_trend`
        ⇒ 本函数实际恒返回 1.0。理由 —— 历史趋势反映的是
        **过去几轮整体走向**，拿它当**本次建议幅度**的全局乘数在业务上不成立
        （时间错配 / 手段错配 / 全局 vs 局部），且系数 0.5 / 1.2 无业务出处。
        保留函数与调用点只为不破坏既有结构；**不要**在未定义业务口径前启用。
        """
        return {
            'worsening': 0.5,
            'improving': 1.2,
            'stable': 1.0,
            'unknown': 1.0,
            'final': 1.0,
        }.get(trend, 1.0)

    @staticmethod
    def _to_keyword_profile(item) -> KeywordProfile:
        """仓库返回项 → `KeywordProfile`（来源层契约的边界归一）。

        契约规定仓库返回 `KeywordProfile`（见 `library/contracts.py`），
        但测试替身与 `backend/tests/` 离线脚本仍可能给裸 dict / 简易对象
        —— 这里三种都收，**且非契约形态一律记 warning**（不静默降级）。

        【注意】**为什么保留兜底而不是删分支**：删掉会让那些脚本当场崩
        （`tests/fuzzy_kernel/_snapshot_core.py` 的仓库替身返回的就是裸 dict）。
        ⇒ 保留兼容，但**留痕**：契约被违反时看得见，而不是安静地按默认值造档案
        （默认值会把论域错成 0~1 ⇒ 规则永远匹配不上）。
        """
        if isinstance(item, KeywordProfile):
            return item
        if isinstance(item, dict):
            logger.warning(
                '[FuzzyEngine] 仓库返回了裸 dict（契约规定应为 KeywordProfile），'
                '已兜底转换')
            return KeywordProfile(
                keyword=item.get('keyword', ''),
                lvl=item.get('lvl', 3),
                min_val=item.get('min_val', 0.0),
                max_val=item.get('max_val', 1.0),
                step=item.get('step', 1.0),
                meta_source=item.get('meta_source', ''),
                dimension=item.get('dimension', DIMENSION_PARAMETER),
            )
        logger.warning(
            '[FuzzyEngine] 仓库返回了非 KeywordProfile 对象（%s），已兜底转换',
            type(item).__name__)
        return KeywordProfile(
            keyword=getattr(item, 'keyword', ''),
            lvl=getattr(item, 'lvl', 3),
            min_val=getattr(item, 'min_val', 0.0),
            max_val=getattr(item, 'max_val', 1.0),
            step=getattr(item, 'step', 1.0),
            meta_source=getattr(item, 'meta_source', ''),
            dimension=getattr(item, 'dimension', DIMENSION_PARAMETER),
        )

    def _load_keyword_profiles(
        self,
        param_names,
        process_parameter: Dict[str, Any],
        domain_limits: Optional[Dict[str, float]] = None,
        temperature_limits: Optional[Dict[str, Tuple[float, float]]] = None,
        product_limits: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> List[KeywordProfile]:
        """按参数名批量拉论域元数据（缺失的走兜底分支）。

        论域来源**按参数族分流**（四者语义不同，不可混用）：

        - **设备类**（**所有参数一视同仁**：压力 / 速度 / 转速 / 位置类
          ``IL`` / ``ML`` / ``MEL`` / ``VPTL``）：判级论域整段换成
          **[0, 机台对每个参数的可设定上限]**（权威源 = 设备维度，见
          :meth:`_apply_declared_bound`）—— **下界统一 0**：
          设备不会设负值，也设不出不存在的值；
          经验下界（如 VPTL 的 30）是**档位语义**、不是物理下限，
          真实值低于它就判不出档（规则恒失活）。
          **H1 守卫**：当前设定值 > 该参数自己的上限时**不替换**（保留经验域）。
        - **温度类**（`NT`/`BT`/`ET`/`MT`）：论域**整体**换成材料温度区间
          （权威源 = 材料维度，见 :func:`specs.resolve_temperature_limits`）。
        - **产品类**（``CT`` 冷却时间）：论域**整体**换成 **[0, 制品级物理推导
          冷却时间]**（权威源 = 产品维度，见 :func:`specs.resolve_product_limits`）
          —— 冷却时间 ∝ 最大壁厚²；**下界统一 0**（冷却时间 0 有物理意义）。
        - **其余字段**（含**时间类** ``PT``/``IT``/``ID``）：保持
          RuleKeyword 默认域（range_min / range_max），不动 —— 这三个时间类
          的产品级基准本轮实测判定不划算（见 ``specs.PRODUCT_DOMAIN_FIELDS``）。

        缺权威源（设备上限 / 材料区间 / 制品壁厚缺失）⇒ **回落经验域**，
        不报错、不阻塞。

        【注意】**B1-4：论域来源统一分支** —— 每个档案都会被打上
        ``domain_source`` 标记（这个论域的边界**最终从哪来**）：

        - ``device`` —— 设备类：判级论域 = [0, 机台可设定上限]
        - ``material`` —— 温度类：论域整体 = 材料温度区间
        - ``product`` —— 产品类：判级论域 = [0, 制品级物理推导基准]
        - ``kept_experience_domain`` —— 权威源已拿到但**守卫拒绝**
          （H1：当前值 > 该参数自己的可设定上限 /
          G7：当前值超产品域物理上界）⇒ 保留经验域
        - ``experience_domain`` —— 其余参数保留经验域
        - ``guessed`` —— 连 RuleKeyword 档案都没有 ⇒ 整段论域由引擎推测

        ⇒ 「哪些参数在靠经验域兜底」从此**可见**（诊断清单里可查），
        作为后续补权威源的输入清单。
        """
        keyword_profiles: List[KeywordProfile] = []
        if param_names:
            try:
                keyword_profiles = [
                    self._to_keyword_profile(item)
                    for item in self._get_repository().get_keywords_by_names(
                        sorted(param_names))
                ]
            except Exception as e:
                logger.warning('[FuzzyEngine] 加载 RuleKeyword 失败: %s', e)

        # ---- 论域来源统一分支（B1-4）------------------------------------
        #    逐参数判定「这个论域最终从哪来」：三类权威源互斥、只取其一；
        #    拿不到权威源的统一落回**经验域**并标记来源 ⇒ 不再有「静默兜底」。
        resolved: List[KeywordProfile] = []
        for kp in keyword_profiles:
            current = _as_float(process_parameter.get(kp.keyword))
            source = DOMAIN_SOURCE_EXPERIENCE

            # (1) 设备类字段（**所有参数一视同仁**）：论域整段换成 [0, 机台可设定上限]
            #     【注意】**H1 守卫**：当前设定值 > 该参数自己的上限 ⇒ **不替换**
            #        （保留经验域）—— 拿一个装不下当前状态的上界当判级上界，
            #        当前状态会落到论域之外 ⇒ 档位方向整体算反。
            #     【注意】**守卫判据对所有参数同源**：位置参数与压力 / 速度参数
            #        一律按「当前值 > 该参数自己的可设定上限」判 ⇒ 一条守卫、
            #        一个标签。
            #     【注意】返回**新档案**，不修改传入对象（上限逐请求不同，
            #        就地改会污染共享/缓存的档案 ⇒ H2 跨请求污染）。
            before_device = kp
            kp, declared_limit, guarded = self._apply_declared_bound(
                kp, domain_limits, current)
            if guarded:
                source = DOMAIN_SOURCE_KEPT_EXPERIENCE
                self._diag.field_reports.append({
                    'layer': 'domain_source',
                    'param': kp.keyword,
                    'domain_source': DOMAIN_SOURCE_KEPT_EXPERIENCE,
                    'guard': 'H1',
                    'device_limit': declared_limit,
                    'current_value': current,
                })
                logger.warning(
                    '[FuzzyEngine] %s 当前值 %.4f 超出机台可设定上限 %.4f'
                    '⇒ 保留经验论域（拿它当判级上界会把当前状态判成越界）',
                    kp.keyword, current, declared_limit)
            elif kp is not before_device:
                source = DOMAIN_SOURCE_DEVICE

            # (2) 温度类字段：论域替换成材料温度区间（权威源 = 材料）
            # 【注意】返回**新档案**，不修改传入对象（材料区间逐请求不同，
            #    就地改会污染共享/缓存的档案 ⇒ H2 跨请求污染）。
            before_temperature = kp
            kp = self._apply_temperature_bound(kp, temperature_limits)
            if kp is not before_temperature:
                source = DOMAIN_SOURCE_MATERIAL

            # (3) 产品类字段：论域替换成 [0, 制品级物理推导基准]（权威源 = 产品）
            # 【注意】返回**新档案**，不修改传入对象（壁厚 / 材料逐请求不同，
            #    就地改会污染共享/缓存的档案 ⇒ H2 跨请求污染）。
            # 【注意】**G7 守卫**：当前设定值 > 产品域上界 ⇒ **不替换**（保留经验域）：
            #    产品域上界是「刚好冷却到位」的物理时间；若当前设定已比它更长，
            #    说明该件的壁厚 / 材料基准与实际不符 ⇒ 用经验域更安全。
            #    判据用严格「>」（相等时落在上界、判成最高档是物理正确的）。
            product_bounds = _product_limit_for(kp.keyword, product_limits or {})
            product_max = self._product_upper_bound(product_bounds)
            before_product = kp
            kp = self._apply_product_bound(kp, product_limits, current)
            if kp is not before_product:
                source = DOMAIN_SOURCE_PRODUCT
            elif (product_max is not None and current is not None
                  and current > product_max):
                source = DOMAIN_SOURCE_KEPT_EXPERIENCE
                self._diag.field_reports.append({
                    'layer': 'domain_source',
                    'param': kp.keyword,
                    'domain_source': DOMAIN_SOURCE_KEPT_EXPERIENCE,
                    'guard': 'G7',
                    'product_limit': product_max,
                    'current_value': current,
                })
                logger.warning(
                    '[FuzzyEngine] %s 当前值 %.4f 超出产品域物理上界 %.4f'
                    '⇒ 保留经验论域（该件的壁厚/材料基准与实际不符）',
                    kp.keyword, current, product_max)

            # 【注意】用 `replace` 产出新档案，而不是就地写字段：档案可能来自
            #    仓库缓存 / 共享对象 ⇒ 就地写会跨请求串数据（H2）。
            resolved.append(replace(kp, domain_source=source))
        keyword_profiles = resolved

        # 兜底：用当前工艺参数值补全 keyword 元数据
        known_keywords = {kp.keyword for kp in keyword_profiles}
        for name in param_names:
            if name in known_keywords:
                continue
            value = process_parameter.get(name)
            if value is None:
                continue
            try:
                current = float(value)
            except (TypeError, ValueError):
                continue
            # 推测论域上界：优先用**设备实测值**（与权威论域同一口径）；
            # 没有对应的必填字段时退回「当前值 × 2」（当前值落在论域中档）。
            # 【注意】必须给**正下限**：当前值为 0 时 `current * 2` = 0 ⇒ 论域退化成
            #    [0, 0]（σ=0 ⇒ 隶属度恒 0/nan）；当前值为负时区间倒挂 [0, 负数]。
            #    两种情况都会让该字段的门控失效（内核侧只告警，见 features.py）。
            #    只在「算出来的上界非正」时兜底 —— 正数路径逐位不变。
            max_val = current * 2
            if max_val <= 0.0:
                max_val = 0.01
            # 【注意】**论域来源**（不是元数据来源）：推测档案的论域边界可能取自
            #    权威源（设备值 / 材料区间 / 制品基准）⇒ 照实标记。
            domain_source = DOMAIN_SOURCE_GUESSED
            # 设备类（**含位置类**）：机台可设定上限是权威源（比「当前值 × 2」
            # 可靠 —— 当前值只是**一个样本**，不能拿来定论域）。
            device_max = lookup_limit(name, domain_limits or {})
            if device_max is not None and device_max > 0.0:
                max_val = float(device_max)
                domain_source = DOMAIN_SOURCE_DEVICE
            min_val = 0.0
            # 温度类：材料温度区间是权威源，比「当前值 × 2」可靠
            # （当前值只是**一个样本**，不能拿来定论域）。
            temp_range = (temperature_limits or {}).get(name)
            if temp_range is not None:
                min_val, max_val = float(temp_range[0]), float(temp_range[1])
                domain_source = DOMAIN_SOURCE_MATERIAL
            # 产品类：制品级物理推导基准同样是权威源（比「当前值 × 2」可靠）。
            product_bounds = _product_limit_for(name, product_limits or {})
            if product_bounds is not None:
                min_val = float(product_bounds[0])
                max_val = float(product_bounds[1])
                domain_source = DOMAIN_SOURCE_PRODUCT
            keyword_profiles.append(KeywordProfile(
                keyword=name,
                # 档位数按关键字的模糊等级 —— 现网统一收敛到 **3 档**
                # ⇒ 推测论域按主流档位 3 档
                lvl=3,
                min_val=min_val,
                max_val=max_val,
                step=max((max_val - min_val) / 3.0, 0.01),
                # 标记这是【推测】出来的论域，不是 RuleKeyword 权威元数据
                # 【注意】温度类的**论域边界**已取材料区间（权威），但**关键字元数据**
                #    （档位数等）仍无权威来源 ⇒ 仍标 guessed，
                #    让「字段体检」能如实报出「这个字段缺元数据」。
                meta_source=FIELD_SOURCE_GUESSED,
                # 【注意】与 `meta_source` **独立**：那个说「关键字元数据」的来源，
                #    这个说「论域边界」的来源。
                domain_source=domain_source,
            ))
        return keyword_profiles

    @staticmethod
    def _apply_declared_bound(
        profile: KeywordProfile,
        limits: Optional[Dict[str, float]],
        current_value: Optional[float] = None,
    ) -> Tuple[KeywordProfile, Optional[float], bool]:
        """把论域整段换成 **[0, 该参数自己的可设定上限]**（一条路径，所有参数同构）。

        **所有参数一视同仁**：位置参数（注射位置 / 计量位置 / 储料终止
        位置 / VP 切换位置）与压力 / 速度 / 转速参数**同构** —— 它们都是「设定
        工艺参数」，上限都是「这台机器这个能力项最多能设到多少」⇒ 判定路径
        只有这一条，差别只在**上限取自哪个设备字段**（实测行程 vs 可设定最大值）。

        **整段换 [0, 上限]**（下界统一 0）：

        - 下界 0 是**物理下限**（设备不会设负值，也设不出不存在的值）；
        - 经验下界（如 VPTL 的 30mm）是**档位语义**、不是物理下限 ⇒ 真实值低于
          它时（如 VPTL 13.92）判不出档，规则恒失活 ⇒ 不能拿它当下界。

        【注意】**返回新档案，不修改传入对象**：上限**逐请求不同**（每台机不一样），
        而 ``KeywordProfile`` 可能来自仓库缓存 / 共享对象 ⇒ 就地改会跨请求串数据
        （H2 跨请求污染）。

        【注意】**守卫**：当前值 > 上限 ⇒ **回落经验论域**（视同缺权威源）——
        拿一个装不下当前状态的上界当判级上界，当前状态会落到论域之外 ⇒ 档位
        方向整体算反。判据用严格「>」（相等时当前值恰在上界、判成最高档是物理
        正确的）。**守卫判据对所有参数同源**：位置参数与压力 / 速度参数一律按
        「当前值 > 该参数自己的可设定上限」判。

        Args:
            profile: 权威论域档案（**不修改**）。
            limits: {算法参数族前缀 / 整段参数名: 可设定上限}。
            current_value: 该参数的当前设定值（``None`` = 没有值 ⇒ 不判守卫）。

        Returns:
            Tuple[档案, 上限, 守卫命中]:
              - 档案：换过论域的**新档案**；无可用上限 / 守卫命中时**原样返回**；
              - 上限：命中的上限值（守卫命中时也返回，供调用方留痕）；未命中为 None；
              - 守卫命中：当前值 > 上限（⇒ 调用方标记 ``kept_experience_domain``）。
        """
        limits = limits or {}
        if not limits:
            return profile, None, False
        declared_max = lookup_limit(profile.keyword, limits)
        if declared_max is None or declared_max <= 0.0:
            # 无权威源（机台没录上限 / 该参数没配来源）⇒ 回落经验论域
            return profile, None, False
        new_max = float(declared_max)

        # ---- 守卫：当前值 > 上限 ⇒ 回落经验论域 ----
        if current_value is not None and current_value > new_max:
            logger.warning(
                '[FuzzyEngine] %s 当前值 %.4f 超出机台可设定上限 %.4f'
                '⇒ 回落经验论域',
                profile.keyword, current_value, new_max)
            return profile, new_max, True

        new_min = 0.0
        old_min = profile.min_val
        old_max = profile.max_val
        old_span = old_max - old_min
        new_span = new_max - new_min
        if new_max > old_max:
            logger.warning(
                '[FuzzyEngine] %s 设备上限 %s 大于经验域上界 %s'
                '（设备能力 > 经验共识 ⇒ 论域被放宽；请核对该上限的录入值）',
                profile.keyword, new_max, old_max)
        # step 按跨度**等比缩放**：保持「档位粒度 / 论域跨度」的比例不变，
        # 换算后档位切分仍保持均匀（否则缩放会让步长与论域不匹配）。
        if old_span > 0 and profile.step > 0:
            step = profile.step * new_span / old_span
        else:
            step = max(new_span / 3.0, 0.01)
        if step <= 0:
            step = max(new_span / 3.0, 0.01)

        logger.info(
            '[FuzzyEngine] %s 论域 [%s, %s] → [%s, %s]（机台可设定上限，step 缩放为 %s）',
            profile.keyword, old_min, old_max, new_min, new_max, step)
        return replace(profile, min_val=new_min, max_val=new_max, step=step), new_max, False

    @staticmethod
    def _apply_temperature_bound(
        profile: KeywordProfile,
        temperature_limits: Optional[Dict[str, Tuple[float, float]]],
    ) -> KeywordProfile:
        """把温度类字段的论域换成**材料温度区间**（上下界一起换）。

        与 :meth:`_apply_declared_bound` 的区别（三处）：

        1. **上下界都换**（设备那套下界固定 0）；
        2. **整段替换**而不是裁剪（材料窗口就是该场景的合理工艺区间）；
        3. **返回新档案**，不改传入对象。

        【注意】**为什么必须返回新档案（而不是就地改）**：
           材料区间**逐请求不同**（每台机跑的材料不一样），而 `KeywordProfile`
           可能来自仓库缓存 / 共享对象 ⇒ 就地改会把 A 材料的区间泄漏到
           B 材料的请求里（这正是 H2「跨请求污染」那类隐患）。

        【注意】**为什么不需要「当前值越界守卫」**（设备那套 H1 有，这里没有）：
           温度是**双边窗口** —— 当前值低于材料下限，判「低」档的**方向是对的**
           （确实该升温）；只有设备上限那套才会出现「上限 ≤ 当前值 ⇒ 域整个
           落在当前值下方 ⇒ 方向算反」的问题。

        Args:
            profile: 权威论域档案（**不修改**）
            temperature_limits: {算法参数名: (下界, 上界)}
                （见 :func:`specs.resolve_temperature_limits`；键是**精确参数名**，
                不做族前缀匹配 —— 温度类只有整段参数，不存在分段同族歧义）

        Returns:
            换过论域的新档案；该参数不是温度类 / 没有权威源时**原样返回**
        """
        limits = temperature_limits or {}
        if not limits:
            return profile
        bounds = limits.get(profile.keyword)
        if bounds is None:
            return profile

        new_min, new_max = float(bounds[0]), float(bounds[1])
        if not (new_min < new_max):
            # 倒挂区间 ⇒ 论域会翻转（档位语义整体颠倒）⇒ 保留原档案
            logger.warning(
                '[FuzzyEngine] %s 材料温度区间非法（%s ~ %s），保留经验论域',
                profile.keyword, new_min, new_max)
            return profile

        old_min, old_max = profile.min_val, profile.max_val
        old_span = old_max - old_min
        new_span = new_max - new_min
        # step 按跨度**等比缩放**（与 _apply_declared_bound 同口径）：
        # 保持「档位粒度 / 论域跨度」的比例不变，换算后档位切分仍保持均匀。
        if old_span > 0 and profile.step > 0:
            step = profile.step * new_span / old_span
        else:
            step = max(new_span / 3.0, 0.01)
        if step <= 0:
            step = max(new_span / 3.0, 0.01)

        logger.info(
            '[FuzzyEngine] %s 论域 [%s, %s] → [%s, %s]（材料温度区间，step 缩放为 %s）',
            profile.keyword, old_min, old_max, new_min, new_max, step)
        return replace(profile, min_val=new_min, max_val=new_max, step=step)

    @staticmethod
    def _product_upper_bound(
        bounds: Optional[Tuple[float, float]],
    ) -> Optional[float]:
        """产品域边界的**有效上界**（区间缺失 / 非法 ⇒ None）。

        供 **G7 守卫**的留痕使用：只有「区间本身合法」时，
        「当前值 > 上界」才真的是 G7（而不是数据脏导致的上界不可信）。
        """
        if bounds is None:
            return None
        try:
            lo, hi = float(bounds[0]), float(bounds[1])
        except (TypeError, ValueError):
            return None
        if not (lo < hi):
            return None
        return hi

    @staticmethod
    def _apply_product_bound(
        profile: KeywordProfile,
        product_limits: Optional[Dict[str, Tuple[float, float]]],
        current_value: Optional[float] = None,
    ) -> KeywordProfile:
        """把产品类字段的判级论域换成 **[0, 制品级物理推导基准]**。

        与 :meth:`_apply_declared_bound` 同形（四处一致）：

        1. **匹配方式**：两级匹配（精确 + 族前缀），见 :func:`_product_limit_for`；
        2. **返回新档案**（不改传入对象）：壁厚 / 材料**逐请求不同**，
           就地改会污染共享/缓存的档案（同 `_apply_temperature_bound` 的理由）；
        3. **权威源可缺**：型腔壁厚没录入 ⇒ 回落经验论域，不报错、不阻塞；
        4. **下界统一取 0**：时间类的经验下界是**档位语义**（如 CT 经验域
           [0,120] 的 0 只是档位起点）、不是物理下限 ⇒ 冷却时间 0 有物理意义
           （等于不冷却）。

        【注意】**G7 守卫：当前值 > 产品域上界 ⇒ 回落经验论域**：
          产品域上界是「刚好冷却到位」的物理时间；若当前设定已比它更长，
          说明该件的壁厚 / 材料基准与实际不符 ⇒ 用经验域更安全。
          判据用严格「>」（相等时落在上界、判成最高档是**物理正确**的，
          回落经验域反而会把它判成最低档）。

        Args:
            profile: 权威论域档案（**不修改**）
            product_limits: {算法参数名: (下界, 上界)}
                （见 :func:`specs.resolve_product_limits`）
            current_value: 该参数的当前值；超出产品域上界时触发回落经验论域。

        Returns:
            换过论域的新档案；该参数不是产品类 / 没有权威源 / 当前值超上界时
            **原样返回**（= 经验论域）
        """
        limits = product_limits or {}
        if not limits:
            return profile
        bounds = _product_limit_for(profile.keyword, limits)
        if bounds is None:
            return profile
        try:
            new_min, new_max = float(bounds[0]), float(bounds[1])
        except (TypeError, ValueError):
            return profile
        if not (new_min < new_max):
            # 倒挂区间 ⇒ 论域会翻转（档位语义整体颠倒）⇒ 保留原档案
            logger.warning(
                '[FuzzyEngine] %s 产品域区间非法（%s ~ %s），保留经验论域',
                profile.keyword, new_min, new_max)
            return profile

        if current_value is not None and current_value > new_max:
            logger.warning(
                '[FuzzyEngine] %s 当前值 %.4f 超出产品域物理上界 %.4f ⇒ 回落经验论域'
                '（该件的壁厚/材料基准与实际不符）',
                profile.keyword, current_value, new_max)
            return profile

        old_min = profile.min_val
        old_max = profile.max_val
        old_span = old_max - old_min
        new_span = new_max - new_min
        if new_max > old_max:
            logger.warning(
                '[FuzzyEngine] %s 产品域上界 %s 大于经验域上界 %s'
                '（物理推导时间 > 经验共识 ⇒ 论域被放宽；请核对该件的壁厚/材料）',
                profile.keyword, new_max, old_max)
        # step 按跨度**等比缩放**（与 _apply_declared_bound 同口径）：
        # 保持「档位粒度 / 论域跨度」的比例不变，换算后档位切分仍保持均匀。
        if old_span > 0 and profile.step > 0:
            step = profile.step * new_span / old_span
        else:
            step = max(new_span / 3.0, 0.01)
        if step <= 0:
            step = max(new_span / 3.0, 0.01)

        logger.info(
            '[FuzzyEngine] %s 论域 [%s, %s] → [%s, %s]（制品级物理推导基准，step 缩放为 %s）',
            profile.keyword, old_min, old_max, new_min, new_max, step)
        return replace(profile, min_val=new_min, max_val=new_max, step=step)

    def _trace_product_family(
        self,
        context: dict,
        product_limits: Dict[str, Tuple[float, float]],
    ) -> None:
        """材料大类识别不出时的留痕（诊断标 ``product_family_unknown``）。

        产品域上界 = f(最大壁厚, 材料大类) ⇒ 材料大类识别不出时只能用
        **默认系数**（保守中位 1.2）。这不是错误，但**必须可见** ——
        否则「这个产品的冷却时间论域是用默认系数算的」这件事在诊断里查不到。
        """
        if not product_limits:
            return
        polymer_info = context.get('polymer_info') or {}
        abbreviation = polymer_info.get('abbreviation')
        if parse_material_family(abbreviation or ''):
            return
        self._diag.field_reports.append({
            'layer': 'domain_source',
            'domain_source': DOMAIN_SOURCE_PRODUCT,
            'note': 'product_family_unknown',
            'abbreviation': abbreviation,
            'default_cool_factor': DEFAULT_COOL_FACTOR,
        })
        logger.warning(
            '[FuzzyEngine] 材料大类识别不出（abbreviation=%s）'
            '⇒ 产品域冷却时间用默认系数 %.2f 估算（留痕 product_family_unknown）',
            abbreviation, DEFAULT_COOL_FACTOR)

    def _build_field_context(
        self,
        param_names,
        process_parameter: Dict[str, Any],
        layer: str = 'numeric',
        domain_limits: Optional[Dict[str, float]] = None,
        temperature_limits: Optional[Dict[str, Tuple[float, float]]] = None,
        product_limits: Optional[Dict[str, Tuple[float, float]]] = None,
    ):
        """加载规则字段的论域元数据，并做一次字段体检。

        字段分三类：

        - ``authority``：有 RuleKeyword 权威元数据
        - ``guessed``  ：无权威元数据，按设备实测值（无则当前工艺参数值）推测了一个
                        论域（lvl=3；当前值非正时兜底为 [0, 0.01]）
        - ``unknown``  ：既无权威元数据也无当前值 ⇒ 规则少了一个门控条件，激活度偏高

        【注意】**设备类字段的论域会整段换成 [0, 机台可设定上限]**（见
        :func:`_load_keyword_profiles`；当前设定值超出该上限时除外 ——
        H1 守卫保留经验域）；**温度类字段的论域会被整体替换成
        材料温度区间**；**产品类字段的论域会被整体替换成 [0, 制品级
        物理推导基准]**；其余字段保持 RuleKeyword 默认域。

        为什么要体检：字段缺元数据时，``nets.py`` 会【静默跳过】它（只有 debug 级
        日志），于是规则少了一个门控条件却无人知晓。现在把它提升到 warning 级。

        Args:
            param_names: 本层用到的工艺参数名（**第 4 层 filter 收好**，
                编排层不从规则串里抠参数名）。
            process_parameter: 当前工艺参数（字段名已归一化；不含设备/材料/模具信息）。
            layer: 层名（numeric / advisory），仅用于日志与清单归类。
            domain_limits: {算法参数前缀 / 整段参数名: 机台可设定上限}（所有参数一视同仁）。
            temperature_limits: {算法参数名: (下界, 上界)}（温度类的材料温度区间）。
            product_limits: {算法参数名: (下界, 上界)}（产品类的制品级物理基准）。

        Returns:
            ``(keyword_profiles, classification)`` —— 前者送引擎，后者是分类结果。
        """
        keyword_profiles = self._load_keyword_profiles(
            param_names, process_parameter, domain_limits, temperature_limits,
            product_limits)

        guessed = {kp.keyword for kp in keyword_profiles
                   if kp.meta_source == FIELD_SOURCE_GUESSED}
        known = {kp.keyword for kp in keyword_profiles}
        classification = {
            'authority': sorted(known - guessed),
            'guessed': sorted(guessed),
            'unknown': sorted(n for n in param_names if n not in known),
        }

        # ---- B1-4：论域来源矩阵（兜底参数清单 = 补权威源的施工单）-------
        #    「靠经验域兜底」= 论域边界来自 RuleKeyword 经验域（**无权威源**）
        #    或权威源被守卫拒绝（kept_experience_domain）⇒ 两种都算
        #    「没拿到可用的权威源」，都进清单。
        domain_sources: Dict[str, List[str]] = {}
        for kp in keyword_profiles:
            src = kp.domain_source or DOMAIN_SOURCE_UNMARKED
            domain_sources.setdefault(src, []).append(kp.keyword)
        domain_sources = {src: sorted(names)
                          for src, names in sorted(domain_sources.items())}
        fallback_params = sorted(
            kp.keyword for kp in keyword_profiles
            if kp.domain_source in (DOMAIN_SOURCE_EXPERIENCE,
                                    DOMAIN_SOURCE_KEPT_EXPERIENCE))
        # 时间类**显式**回落经验域 ⇒ 单列出来（产品维度接入的输入清单）
        # 【注意】CT 已接产品域 ⇒ 它的 domain_source 是 'product' ⇒ **天然不在此清单**；
        #    清单里剩下的就是「还没拿到权威源」的时间类（PT / IT / ID）。
        time_domain_params = sorted(
            kp.keyword for kp in keyword_profiles
            if kp.domain_source in (DOMAIN_SOURCE_EXPERIENCE,
                                    DOMAIN_SOURCE_KEPT_EXPERIENCE)
            and is_time_domain_field(kp.keyword))
        # 已接产品域的参数（CT 等）⇒ 诊断可见：谁拿到了制品级物理基准
        product_domain_params = sorted(
            kp.keyword for kp in keyword_profiles
            if kp.domain_source == DOMAIN_SOURCE_PRODUCT)

        if classification['unknown']:
            logger.warning(
                '[FuzzyEngine][%s] %d 个字段无元数据（规则缺一个门控条件，激活度偏高）: %s',
                layer, len(classification['unknown']), classification['unknown'])
        if classification['guessed']:
            logger.info(
                '[FuzzyEngine][%s] %d 个字段使用推测论域（lvl=3、论域[0, 设备值或当前工艺参数值*2]）: %s',
                layer, len(classification['guessed']), classification['guessed'])
        if fallback_params:
            logger.info(
                '[FuzzyEngine][%s] %d 个参数靠经验域兜底（无权威源，待补）: %s',
                layer, len(fallback_params), fallback_params)
        if time_domain_params:
            # 【注意】CT 已接产品域（见下一条日志），这里剩下的是**尚无权威源**的时间类
            #    （PT / IT / ID）。
            logger.info(
                '[FuzzyEngine][%s] %d 个时间类参数回落经验域'
                '（尚无制品级/权威源基准）: %s',
                layer, len(time_domain_params), time_domain_params)
        if product_domain_params:
            logger.info(
                '[FuzzyEngine][%s] %d 个参数已接产品域（制品级物理推导基准）: %s',
                layer, len(product_domain_params), product_domain_params)

        # 【注意】**合并进已有条目**（不新增 field_reports 条目）：既有断言
        #    「两次 `_build_field_context` ⇒ `_field_reports` 恰好 2 条」依赖
        #    条目数不变 ⇒ 来源矩阵作为**附加键**挂在同一条目上。
        #    黄金快照只记 `_diagnostics`（规则级），不含 field_reports ⇒ 零影响。
        self._diag.field_reports.append({
            'layer': layer,
            'classification': classification,
            'domain_sources': domain_sources,
            'fallback_params': fallback_params,
            'time_domain_params': time_domain_params,
            'product_domain_params': product_domain_params,
        })
        return keyword_profiles, classification

    def _load_defect_profiles(
        self,
        defect_names,
    ) -> Dict[str, KeywordProfile]:
        """按名字加载缺陷类关键词的论域元数据（**只认权威元数据**）。

        与 `_load_keyword_profiles` 的区别：工艺参数缺元数据时可以按当前值推测一个
        论域（反正有值可依），但缺陷维度**没有工艺值**可依 —— 推测出来的论域毫无
        意义 ⇒ 这里只取 RuleKeyword 里真实存在的记录，取不到就当作「该维度不参与
        推理」。

        Returns:
            ``{keyword: KeywordProfile}``
        """
        if not defect_names:
            return {}
        try:
            items = self._get_repository().get_keywords_by_names(
                sorted(defect_names))
        except Exception as e:
            logger.warning('[FuzzyEngine] 加载缺陷关键词元数据失败: %s', e)
            return {}

        profiles: Dict[str, KeywordProfile] = {}
        for item in items:
            kp = self._to_keyword_profile(item)
            if kp.meta_source == FIELD_SOURCE_GUESSED:
                continue
            profiles[kp.keyword] = kp
        return profiles

    def _build_defect_inputs(
        self,
        defect_ctx: Dict[str, Any],
        defect_profiles: Dict[str, KeywordProfile],
    ) -> Dict[str, float]:
        """缺陷反馈 → 推理输入里的**缺陷维度数值**。

        缺陷程度（``level``）是**离散档位**，而推理网络的输入是数值 ⇒ 用
        「档位词 → 论域桶中心」把它翻成数值（``macros.level_to_domain_value``）。
        取桶中心 ⇒ 该档隶属度恰为 1.0、相邻档自然衰减 ⇒ 档位差异**连续表达**，
        而不是非此即彼的硬开关。

        缺陷位置（``position``）同理：位置精确到段号本身就是强匹配信号，
        且规则库里 DL 前件的档位**恒为 high**（实测 20 条 100% 一致）
        ⇒ 取 high 档中心。

        【注意】返回值只喂给推理网络，**绝不能混进 `process_parameter`** ——
        后者会被 `to_recommendations` 当作「当前参数集合」，混进缺陷名会在
        推荐结果里冒出 SHORTSHOT 这种非参数条目。

        【注意】反馈里没有值的维度**不产出数值**（例如用户没填缺陷位置）⇒
        对应维度不会被建论域 ⇒ 其前件不作为门控。
        """
        inputs: Dict[str, float] = {}
        if not defect_profiles:
            return inputs

        defect_name = defect_ctx.get('defect_name')
        level = defect_ctx.get('level')
        if defect_name and level:
            kp = defect_profiles.get(defect_name)
            if kp is not None:
                # 【注意】档位词可能在**当前等级数下无法解析**（5/7 档独有词、
                #    编号轨越界词）⇒ 直接送进来会让**整个缺陷维度掉出
                #    推理网络**（静默失活：不报错、结果合理、就是少了
                #    缺陷相关建议）⇒ 先降级到语义最近的合法档位。
                #    详见 docs/defect-level-downgrade-plan.md
                word, downgraded = downgrade_level_word(kp.lvl, level)
                if downgraded:
                    self._report_level_downgrade(
                        defect_name, level, word, kp.lvl)
                value = level_to_domain_value(
                    kp.lvl, word, kp.min_val, kp.max_val)
                if value is not None:
                    inputs[defect_name] = value

        position = defect_ctx.get('position')
        if position:
            kp = defect_profiles.get(position)
            if kp is not None:
                value = level_to_domain_value(
                    kp.lvl, 'high', kp.min_val, kp.max_val)
                if value is not None:
                    inputs[position] = value
        return inputs

    def _report_level_downgrade(
        self,
        defect_name: str,
        origin_level: str,
        downgraded_to: str,
        lvl: int,
    ) -> None:
        """档位词降级留痕（**幂等**）。

        【注意】**幂等是必需的**：`_build_defect_inputs` 在一次 `recommend()` 内
        会被调用 **2 次**（`_infer_numeric_layer` 与 `_dedupe_advice_items`
        各一次）⇒ 直接 append 会产生重复记录。
        ⇒ 按 `(guard, param, origin_level)` 查重，同一次请求只留 1 条。

        留痕进**已有的** `field_reports` 容器（不新增第 5 个诊断容器 ⇒
        `Diagnostic.to_payload` 结构不变 ⇒ 黄金快照不受影响）。
        该容器本来的定位就是「字段定性降级清单（每层一条）」⇒
        正好落在这里。
        """
        reports = self._diag.field_reports
        for r in reports:
            if (r.get('guard') == 'LEVEL_DOWNGRADE'
                    and r.get('param') == defect_name
                    and r.get('origin_level') == origin_level):
                return
        reports.append({
            'layer': 'defect_input',
            'param': defect_name,
            'guard': 'LEVEL_DOWNGRADE',
            'origin_level': origin_level,
            'downgraded_to': downgraded_to,
            'fuzzy_level': lvl,
        })
        logger.warning(
            '[FuzzyEngine] 缺陷档位词在当前等级数下无法解析，已降级: '
            '%s %s → %s (lvl=%d)',
            defect_name, origin_level, downgraded_to, lvl)

    def _infer_numeric_layer(
        self,
        filtered: FilteredRules,
        process_parameter: Dict[str, float],
        defect_ctx: Dict[str, Any],
        domain_limits: Optional[Dict[str, float]] = None,
        temperature_limits: Optional[Dict[str, Tuple[float, float]]] = None,
        product_limits: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> List[RuleAdjustment]:
        """数值层推理（NumTskRuleNet，数值/百分比结论）。

        条目级故障边界已下沉到第 4 层 filter：
        「结论值不是数值」的规则在进 net **之前**就被挑出去了
        （`filtered.skipped`），其余规则照常推理。
        """
        numeric_rules = filtered.numeric_rules
        if not numeric_rules:
            if filtered.skipped:
                logger.info('[FuzzyEngine] 数值层无安全规则，跳过')
            return []

        keyword_profiles, _classification = self._build_field_context(
            filtered.numeric_param_names, process_parameter, 'numeric',
            domain_limits, temperature_limits, product_limits)

        if not keyword_profiles:
            logger.info('[FuzzyEngine] 数值层无可用 RuleKeyword，跳过')
            return []

        # ---- 缺陷维度：论域元数据 + 反馈数值 ----------------------------
        # 先拉权威元数据，再把反馈里的缺陷程度/位置翻成数值，最后**只给本次
        # 反馈真的给出了数值的维度**建论域 ——
        #   反馈没给数值的维度（如用户没填缺陷位置）不建论域 ⇒ 其前件不作门控
        #   （不会因空列把整类规则压成 EPSILON）。
        defect_profiles = self._load_defect_profiles(filtered.defect_param_names)
        defect_inputs = self._build_defect_inputs(defect_ctx, defect_profiles)
        defect_profiles = {
            k: v for k, v in defect_profiles.items() if k in defect_inputs
        }
        if defect_inputs:
            logger.info(
                '[FuzzyEngine] 缺陷维度进推理输入: %s',
                {k: round(v, 4) for k, v in defect_inputs.items()})

        try:
            # 缺陷 profile 追加在**末尾** ⇒ pre_dict 的列索引不受现有工艺字段影响
            net = NumTskRuleNet(
                numeric_rules, list(keyword_profiles) + list(defect_profiles.values()))
            # 推理输入 = 工艺参数 + 缺陷维度（两者分开，不污染 process_parameter）
            inference_input = {**process_parameter, **defect_inputs}
            results, extra = net.predict(
                inference_input, top_k=len(numeric_rules))
        except Exception as e:
            logger.exception('[FuzzyEngine] NumTskRuleNet 推理失败: %s', e)
            return []

        # 提取 [{param: value}] 字典 → RuleAdjustment
        out: List[RuleAdjustment] = []
        for rule_str, activation, adjustments, raw_activation in results:
            for param, value in adjustments.items():
                out.append(RuleAdjustment(
                    param_name=param,
                    # 【注意】activation 是**组内占比**（同参数组内各规则占比之和 = 1）
                    #    ⇒ 这里乘出来的是“该规则在它所属参数组里的贡献份额”，
                    #    聚合层裸累加 = 组内加权平均。
                    delta=float(value) * float(activation),
                    activation=float(activation),
                    # 【注意】raw_activation 是**原始激活度**（前件隶属度之积），
                    #    不含 priority / specificity 乘数 ⇒ 置信度用它。
                    raw_activation=float(raw_activation),
                    layer='numeric',
                    rule_str=rule_str,
                ))
        return out

    def _infer_advisory_layer(
        self,
        filtered: FilteredRules,
        process_parameter: Dict[str, float],
        domain_limits: Optional[Dict[str, float]] = None,
        defect_ctx: Optional[Dict[str, Any]] = None,
        temperature_limits: Optional[Dict[str, Tuple[float, float]]] = None,
        product_limits: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> List[RuleAdjustment]:
        """提示层推理。

        提示层有两类规则，必须分开处理：

        1) 检查/弹窗类结论（`X_adjust_请检查锁模力是否不合理。`）
           → 提取提示文本，作为**文本建议**输出（不给数值）。
           这类规则绝不能进 Mamdani 数值层：它的结论值是提示语而不是模糊等级，
           就算不崩也算不出有意义的数值。

        2) 模糊等级结论（`X_add_low`）
           → Mamdani 全模糊推理（保留路径，规则库当前没有这种结论）。

        两类都已是**第 4 层 filter 的产物**：文本建议在 `filtered.advice_items`，
        Mamdani 规则对象在 `filtered.mamdani_rules` —— 本层只消费产物。
        """
        mamdani_rules = filtered.mamdani_rules
        if not filtered.advice_items and not mamdani_rules:
            return []

        out: List[RuleAdjustment] = []

        # 1) 检查/弹窗类 → 文本建议
        #    【注意】先按缺陷程度去重（规则库里同一句检查提示按档位各写了一遍）
        advice_items = self._dedupe_advice_items(
            filtered.advice_items, defect_ctx, filtered.defect_param_names)
        for item in advice_items:
            out.append(RuleAdjustment(
                param_name=item.param_name,
                delta=0.0,
                activation=0.0,
                layer='advisory',
                rule_str=item.rule_description,
                advice=item.advice,
            ))

        # 2) 模糊等级结论 → Mamdani
        if not mamdani_rules:
            return out

        keyword_profiles, _classification = self._build_field_context(
            filtered.mamdani_param_names, process_parameter, 'advisory',
            domain_limits, temperature_limits, product_limits)
        if not keyword_profiles:
            return out

        try:
            net = FuzzyRuleNet(mamdani_rules, keyword_profiles)
            # 【注意】传副本：内核不得改调用方的参数字典（口径同数值层）
            results = net.predict(dict(process_parameter), top_k=len(mamdani_rules))
        except Exception as e:
            logger.exception('[FuzzyEngine] FuzzyRuleNet 推理失败: %s', e)
            return out

        for param_name, value, extra in results:
            # Mamdani 的 extra[0] 就是**原始激活度**（未经任何归一化）
            # ⇒ 数值层用组内占比、提示层用原始激活度，语义一致。
            mamdani_activation = float(extra[0]) if isinstance(extra, tuple) else 1.0
            out.append(RuleAdjustment(
                param_name=param_name,
                delta=float(value),
                activation=mamdani_activation,
                raw_activation=mamdani_activation,
                layer='advisory',
                # Mamdani 模糊等级结论没有单一来源规则串 ⇒ None
                rule_str=None,
            ))
        return out

    # -----------------------------------------------------------------------
    # 提示层去重（缺陷程度）
    # -----------------------------------------------------------------------

    def _dedupe_advice_items(
        self,
        advice_items: List[Any],
        defect_ctx: Optional[Dict[str, Any]],
        defect_names: Any,
    ) -> List[Any]:
        """检查类建议去重：同（参数 + 提示文本）只留**缺陷程度最匹配**的一条。

        为什么需要：检查类规则在规则库里按缺陷档位各写一遍
        （``FLASH_low`` / ``FLASH_medium`` / ``FLASH_high`` 各有一条
        「请检查锁模力是否不合理。」）而提示层**不走数值推理**
        （没有激活度可加权）⇒ 原实现逐条 append ⇒ 同一句话被输出 3 次。

        去重键是 ``(参数名, 提示文本)`` 而不是单个参数名 —— 同一参数下的
        **不同**检查项（「检查锁模力」+「检查模温」）是两条独立建议，都该保留。

        选谁：按缺陷维 μ（高斯隶属度）取最大者。
        【注意】**不是按档位字符串精确匹配**：规则库只写 low/medium/high 三档，
        而档位词表仍保留 5/7 档的独有词（macros.LEVEL_WORDS_BY_LVL）
        ⇒ 精确匹配会在传入「极轻微 / 极严重」这类 5 档词时把提示**全部切光**
        （同一理由见 ``library/semantics.py::match_defect_name``）。
        用 μ 则是「取最接近的那一档」⇒ 5/7 档输入安全。
        """
        if not advice_items:
            return []
        defect_ctx = defect_ctx or {}
        defect_name = defect_ctx.get('defect_name')
        level = defect_ctx.get('level')
        if not defect_name or not level:
            # 反馈没有缺陷程度 ⇒ 无从按程度挑 ⇒ 原样保留
            return list(advice_items)
        if not defect_names:
            return list(advice_items)

        defect_profiles = self._load_defect_profiles(set(defect_names))
        if not defect_profiles:
            return list(advice_items)
        defect_inputs = self._build_defect_inputs(defect_ctx, defect_profiles)
        if not defect_inputs:
            return list(advice_items)

        best: Dict[Any, Any] = {}
        order: List[Any] = []
        for item in advice_items:
            mu = self._advice_defect_mu(item, defect_profiles, defect_inputs)
            key = (item.param_name, item.advice)
            if key not in best:
                best[key] = (mu, item)
                order.append(key)
            elif mu > best[key][0]:
                best[key] = (mu, item)
        return [best[key][1] for key in order]

    def _advice_defect_mu(
        self,
        item: Any,
        defect_profiles: Dict[str, KeywordProfile],
        defect_inputs: Dict[str, float],
    ) -> float:
        """一条检查建议在缺陷维上的隶属度。

        【注意】**解析不出时返回 1.0**（视为「最匹配」）—— 宁可不去重，
        也不要把本该保留的检查项删掉（退化行为 = 改造前的样子）。

        规则串的第一个前件是缺陷名（规则库约定，1646 条实测 100% 一致）。
        """
        try:
            parsed = parse_rule(item.rule_description)
        except Exception:
            return 1.0
        preconditions = parsed.get('preconditions') or []
        if not preconditions:
            return 1.0
        first = preconditions[0]
        name = first.get('name')
        level_word = str(first.get('level') or '').lower()
        kp = defect_profiles.get(name)
        if kp is None or name not in defect_inputs:
            return 1.0
        try:
            bucket = resolve_bucket(kp.lvl, level_word)
        except ValueError:
            return 1.0
        feature = FuzzyFeature([kp.min_val, kp.max_val], f_level=kp.lvl)
        return float(feature.get_value_by_level(defect_inputs[name], bucket))

    # -----------------------------------------------------------------------
    # 归并与格式化逻辑在 recommendations.py：
    #   - aggregate()          逐条调整量 → 参数级汇总
    #   - to_recommendations() 参数级汇总 → AlgorithmRecommendation
    # 本类只负责"调一下"，不掺和聚合细节。
    # -----------------------------------------------------------------------


# 注册引擎
AlgorithmRegistry.register('fuzzy', FuzzyEngine())
