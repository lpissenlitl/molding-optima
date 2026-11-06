"""
模糊推理引擎 - 主入口

基于模糊规则进行缺陷修正推荐。

⚠️ 这里的"层"按**结论形态**划分（这条规则的结论能不能算出数值），
   与规则库层级（base / 产品库 / specificity）**完全无关**：

- 数值层 (NumTskRuleNet)   → 数值/百分比结论（``X_add_3.8`` / ``X_reduce_30%``）
- 提示层 (FuzzyRuleNet)    → 检查/弹窗结论（``X_adjust_请检查锁模力是否不合理。``）
                            + 模糊等级结论（``X_add_low``，兼容 Rule.dat 风格）
- 合并策略                → 同层聚合 + 跨层覆盖
"""

import logging
from typing import List, Dict, Any, Optional

from process.algorithms.base import AlgorithmBase, AlgorithmRecommendation, AlgorithmRegistry
from process.algorithms.defect_selection import select_defect
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
from process.algorithms.fuzzy.fuzzy_core.macros import level_to_domain_value
from process.algorithms.fuzzy.fuzzy_core.models.nets import (
    FuzzyRuleNet,
    NumTskRuleNet,
)
from process.algorithms.fuzzy.fuzzy_core.profiles import KeywordProfile
from process.algorithms.fuzzy.fuzzy_core.rules_filter import (
    FilteredRules,
    build_rule_objects,
)
from process.algorithms.fuzzy.over_limit import detect_over_limits
from process.algorithms.fuzzy.specs import (
    lookup_param_limit,
    resolve_domain_limits,
    resolve_param_limits,
)
from process.algorithms.fuzzy.library.contracts import (
    AlgorithmResourceRepository,
    RuleQueryContext,
)


logger = logging.getLogger(__name__)

# 元数据来源标记：'guessed' 表示这个论域是按实时值猜的，不是 RuleKeyword 权威元数据
FIELD_SOURCE_GUESSED = 'guessed'


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

                ⚠️ **显式注入优先于配置**：传了实例就只用它，
                  忽略 `FUZZY_LIBRARY_SOURCE`。
        """
        self._repo = repository
        # ⚠️ 诊断数据**不放实例属性** —— 本引擎是模块级单例（见文件末尾
        #    `AlgorithmRegistry.register`），放实例属性会让并发请求互相清空/串写
        #    （已实测复现：A 的条目被 B 覆盖）。生产路径走**每请求一个**的容器
        #    （`diagnostics.request_diagnostics()`），见 `diagnostics.py`。
        # 这个 `_last_diag` 是「最近一次请求的诊断」的槽位：请求结束后仍能读到
        # （诊断脚本 / 快照脚本依赖这个约定）。
        # ⚠️ 并发下它会被别的请求覆盖 ⇒ 生产**不依赖**它（诊断已由
        #    `request_diagnostics` 打成结构化日志）。
        self._last_diag = Diagnostic()

    def _get_repository(self) -> AlgorithmResourceRepository:
        """取资源仓库契约（默认实现延迟导入）。

        ⚠️ 默认实现由 `library/provider.py::resolve_repository` 按配置选：
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
                'feedback': {                        # 反馈 dict（含 defect / observations / tuning_result）
                    'defect': [...],
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

        ⓪ 越限识别（**输入体检**，插在最前面）：详见下方注释。
        """
        # ⓪ 输入体检 —— **识别**当前值超出机台可设定上限的参数。
        #
        # 为什么放在**最前面**（而不是跟着推理走）：
        #   它回答的是「**进来的参数本身**合不合规」，与「本次有没有规则可推」无关 ——
        #   即使因为无缺陷 / 无规则而提前返回，越限这条事实也该被记录下来。
        #
        # ⚠️ **只识别，不处理**（用户口径：「首先要做到的点是能识别超限，
        #    再考虑别的问题」）：不告警、不拒绝、不改建议 ⇒ 对外输出零变化。
        #    不同参数类型的处理不一样（设定值类 = 设备安全红线；温度类 = 材料降解；
        #    时间类 = 无设备约束）⇒ **处理方式留待后续分层决策**，
        #    识别结果自带 `limit_source` 正是给分层用的依据。
        #
        # 机台物理上限（机台上限是**必填**等级字段）：一次解析，供「识别」与
        # 「第 6 步裁剪」共用 ⇒ 两处看到的是**同一份**上限，不会各自算一遍而漂移。
        param_limits = resolve_param_limits(context.get('machine_info') or {})
        over_limits = detect_over_limits(
            context.get('process_parameter') or {}, param_limits)
        if over_limits:
            self._diag.over_limits.extend(item.to_trace() for item in over_limits)
            logger.warning(
                '[FuzzyEngine] 检测到 %d 个参数超出机台可设定上限（仅识别，未处理）: %s',
                len(over_limits),
                ['%s=%.4f>%.4f' % (i.param_name, i.current_value, i.limit)
                 for i in over_limits[:5]])

        # 1) 认缺陷
        defects = (context.get('feedback') or {}).get('defect', []) or []
        if not defects:
            return []

        # 缺陷选取 —— **唯一真相源**（`process/algorithms/defect_selection.py`）。
        # selection 对象自带选取依据，这里顺手**留痕**（决策级，
        # 与 `field_reports` / `diagnostics` 那两个规则级清单分开）。
        selection = select_defect(context)
        self._diag.selections.append(selection.to_trace())
        defect_name = selection.keyword_name
        if not defect_name:
            logger.warning('[FuzzyEngine] 反馈中未指定缺陷类型（keyword_name），跳过推荐')
            return []

        # 缺陷上下文（缺陷名 / 严重程度 / 位置）——算法自己从 input 推导
        defect_ctx = {
            'defect_name': defect_name,
            'level': selection.level,
            'position': selection.position,
        }

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
            # 当前租户（可见性上下文）—— 缺上下文（None）⇒ 不过滤
            company_id=context.get('company_id'),
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
        process_parameter = {
            k: v for k, v in (context.get('process_parameter') or {}).items()
            if v is not None
        }
        # ⚠️ 编排层**不传** `iteration_trend` ⇒ 恒为 'unknown' ⇒ 系数恒 1.0。
        #    该乘数策略已判定**业务上不成立**（历史趋势 ≠ 本次建议幅度），
        #    故**刻意不接线**。
        trend = context.get('iteration_trend', {}) or {}
        adjustment_factor = self._trend_to_factor(trend.get('trend', 'unknown'))

        # 4) 并行推理（层间隔离：一层失败不影响另一层）
        #    判级论域上界 = 设备实测值（仅**必填等级**字段，用户口径：
        #    「我们定义必填的字段，必须校验并且替换，其余字段的论域可以用默认值」）。
        #    缺失的必填字段在 service 层已被校验器拦（400），到这里不会有缺失。
        domain_limits = resolve_domain_limits(context.get('machine_info') or {})
        numeric_results = self._infer_numeric_layer(
            filtered, process_parameter, defect_ctx, domain_limits)
        advisory_results = self._infer_advisory_layer(
            filtered, process_parameter, domain_limits)

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
        #    复用第 ⓪ 步已解析的 `param_limits`（同一份上限，不重算）
        return self._apply_machine_limits(recommendations, param_limits)

    def _apply_machine_limits(
        self,
        recommendations: List[AlgorithmRecommendation],
        limits: Dict[str, float],
    ) -> List[AlgorithmRecommendation]:
        """按机台物理上限裁剪推荐值（越限则封顶，方向重算）

        规则库论域上界普遍**宽于**机台 HMI 可设定范围（实测注射压力论域 0~200，
        同一台机上限 100），不裁剪就会给出操作工根本输不进去的推荐值。

        缺上限（机台没填）⇒ **不裁剪**，只记 warning：缺数据不等于不能给建议，
        也不拦请求。

        Args:
            recommendations: 聚合层产出的推荐列表
            limits: {算法参数前缀: 机台物理上限}（见 specs.resolve_param_limits）

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

            limit = lookup_param_limit(rec.param_name, limits)
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

        # ⚠️ 编排层不传 `iteration_trend` ⇒ 该分支在 optimize 链**不生效**；
        #    condition 链会传（见 condition.py）⇒ 那里终态时 fuzzy 不参与 chain。
        #    接线前必须先解决「终态无推荐 ⇒ fail-fast 报『算法暂不可用』」的问题。
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
    # ⚠️ 这两个属性是**读取入口**，不是数据存储位置 —— 真实存储在
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

        前端 DefectFeedback 传的是 `{keyword_id, keyword_name, level, position}`：
        - `keyword_name`：英文缺陷码（SHORTSHOT / FLASH / ...），
          与 `RuleMethod.defect_code`、`RuleKeyword.keyword_name` 对齐
        - `level`：严重程度（low / medium / high），与规则前件的档位词一致
        - `position`：缺陷位置（`DL` + 缺陷名 + 段号）

        ⚠️ 选取逻辑已收敛到**唯一真相源**
        （`process/algorithms/defect_selection.py`），本方法只是它的便捷包装，
        返回形状保持不变（`defect_name` / `level` / `position`）。
        """
        selection = select_defect(context)
        if selection.is_empty():
            return {}
        return {
            'defect_name': selection.keyword_name,
            'level': selection.level,
            'position': selection.position,
        }

    @staticmethod
    def _trend_to_factor(trend: str) -> float:
        """迭代趋势 → 调整系数。

        ⚠️ **刻意未接线**：编排层不传 `iteration_trend`
        ⇒ 本函数实际恒返回 1.0。理由 —— 历史趋势反映的是
        **过去几轮整体走向**，拿它当**本次建议幅度**的全局乘数在业务上不成立
        （时间错配 / 手段错配 / 全局 vs 局部），且系数 0.5 / 1.2 无业务出处。
        保留函数与调用点只为不破坏既有结构；**不要**在未定义业务口径前接线。
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

        ⚠️ **为什么保留兜底而不是删分支**：删掉会让那些脚本当场崩
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
        )

    def _load_keyword_profiles(
        self,
        param_names,
        process_parameter: Dict[str, Any],
        domain_limits: Optional[Dict[str, float]] = None,
    ) -> List[KeywordProfile]:
        """按参数名批量拉论域元数据（缺失的走兜底分支）。

        论域上界 = **设备实测值**，但**只对必填等级字段生效**（用户口径：
        「我们定义必填的字段，必须校验并且替换，其余字段的论域可以用默认值」）。
        其余字段保持 RuleKeyword 默认域（range_min / range_max）不动。
        下界统一取经验域下界（RuleKeyword.range_min）。
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

        # ---- 必填等级字段：论域上界替换成设备实测值 --------------------
        for kp in keyword_profiles:
            self._apply_device_bound(kp, domain_limits)

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
            # ⚠️ 必须给**正下限**：当前值为 0 时 `current * 2` = 0 ⇒ 论域退化成
            #    [0, 0]（σ=0 ⇒ 隶属度恒 0/nan）；当前值为负时区间倒挂 [0, 负数]。
            #    两种情况都会让该字段的门控失效（内核侧只告警，见 features.py）。
            #    只在「算出来的上界非正」时兜底 —— 正数路径逐位不变。
            max_val = current * 2
            if max_val <= 0.0:
                max_val = 0.01
            device_max = lookup_param_limit(name, domain_limits or {})
            if device_max is not None and device_max > 0.0:
                max_val = float(device_max)
            keyword_profiles.append(KeywordProfile(
                keyword=name,
                # 档位数按关键字的模糊等级 —— 规则库实测 310/311 条
                # RuleKeyword.fuzzy_level = 5 ⇒ 推测论域按主流档位 5 档
                lvl=5,
                min_val=0.0,
                max_val=max_val,
                step=max(max_val / 3.0, 0.01),
                # 标记这是【推测】出来的论域，不是 RuleKeyword 权威元数据
                meta_source=FIELD_SOURCE_GUESSED,
            ))
        return keyword_profiles

    @staticmethod
    def _apply_device_bound(
        profile: KeywordProfile,
        domain_limits: Optional[Dict[str, float]],
    ) -> bool:
        """把权威论域的**上界**替换成设备实测值（step 按跨度等比缩放）。

        只对**必填等级**字段生效（见 :func:`specs.resolve_domain_limits`）：
        下界仍是经验域下界（RuleKeyword.range_min），**只换上界**。

        Args:
            profile: 权威论域档案（就地修改）
            domain_limits: {算法参数前缀: 论域上界}

        Returns:
            是否发生了替换（未替换返回 False）
        """
        limits = domain_limits or {}
        if not limits:
            return False
        device_max = lookup_param_limit(profile.keyword, limits)
        if device_max is None or device_max <= 0.0:
            return False
        new_max = float(device_max)
        if new_max <= profile.min_val:
            logger.warning(
                '[FuzzyEngine] %s 设备上限 %s 不大于经验下界 %s，保留经验论域',
                profile.keyword, new_max, profile.min_val)
            return False

        old_max = profile.max_val
        old_span = old_max - profile.min_val
        new_span = new_max - profile.min_val
        if new_max > old_max:
            logger.warning(
                '[FuzzyEngine] %s 设备上限 %s 大于经验域上界 %s'
                '（设备能力 > 经验共识 ⇒ 论域被放宽；请核对该上限的录入值）',
                profile.keyword, new_max, old_max)
        # step 按跨度**等比缩放**：保持「档位粒度 / 论域跨度」的比例不变，
        # 换算后档位切分仍保持均匀（否则缩放会让步长与论域不匹配）。
        if old_span > 0 and profile.step > 0:
            profile.step = profile.step * new_span / old_span
        else:
            profile.step = max(new_span / 3.0, 0.01)
        if profile.step <= 0:
            profile.step = max(new_span / 3.0, 0.01)
        profile.max_val = new_max
        logger.info(
            '[FuzzyEngine] %s 论域上界 %s → %s（设备实测值，step 缩放为 %s）',
            profile.keyword, old_max, new_max, profile.step)
        return True

    def _build_field_context(
        self,
        param_names,
        process_parameter: Dict[str, Any],
        layer: str = 'numeric',
        domain_limits: Optional[Dict[str, float]] = None,
    ):
        """加载规则字段的论域元数据，并做一次字段体检。

        字段分三类：

        - ``authority``：有 RuleKeyword 权威元数据
        - ``guessed``  ：无权威元数据，按设备实测值（无则当前工艺参数值）推测了一个
                        论域（lvl=5；当前值非正时兜底为 [0, 0.01]）
        - ``unknown``  ：既无权威元数据也无当前值 ⇒ 规则少了一个门控条件，激活度偏高

        ⚠️ 必填等级字段的**论域上界会被替换成设备实测值**（见
        :func:`_load_keyword_profiles`）；其余字段保持 RuleKeyword 默认域。

        为什么要体检：字段缺元数据时，``nets.py`` 会【静默跳过】它（只有 debug 级
        日志），于是规则少了一个门控条件却无人知晓。现在把它提升到 warning 级。

        Args:
            param_names: 本层用到的工艺参数名（**第 4 层 filter 收好**，
                编排层不从规则串里抠参数名）。
            process_parameter: 当前工艺参数（字段名已归一化；不含设备/材料/模具信息）。
            layer: 层名（numeric / advisory），仅用于日志与清单归类。
            domain_limits: {算法参数前缀: 论域上界}（必填等级字段的设备实测值）。

        Returns:
            ``(keyword_profiles, classification)`` —— 前者送引擎，后者是分类结果。
        """
        keyword_profiles = self._load_keyword_profiles(
            param_names, process_parameter, domain_limits)

        guessed = {kp.keyword for kp in keyword_profiles
                   if kp.meta_source == FIELD_SOURCE_GUESSED}
        known = {kp.keyword for kp in keyword_profiles}
        classification = {
            'authority': sorted(known - guessed),
            'guessed': sorted(guessed),
            'unknown': sorted(n for n in param_names if n not in known),
        }

        if classification['unknown']:
            logger.warning(
                '[FuzzyEngine][%s] %d 个字段无元数据（规则缺一个门控条件，激活度偏高）: %s',
                layer, len(classification['unknown']), classification['unknown'])
        if classification['guessed']:
            logger.info(
                '[FuzzyEngine][%s] %d 个字段使用推测论域（lvl=5、论域[0, 设备值或当前工艺参数值*2]）: %s',
                layer, len(classification['guessed']), classification['guessed'])

        self._diag.field_reports.append(
            {'layer': layer, 'classification': classification})
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

        ⚠️ 返回值只喂给推理网络，**绝不能混进 `process_parameter`** ——
        后者会被 `to_recommendations` 当作「当前参数集合」，混进缺陷名会在
        推荐结果里冒出 SHORTSHOT 这种非参数条目。

        ⚠️ 反馈里没有值的维度**不产出数值**（例如用户没填缺陷位置）⇒
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
                value = level_to_domain_value(
                    kp.lvl, level, kp.min_val, kp.max_val)
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

    def _infer_numeric_layer(
        self,
        filtered: FilteredRules,
        process_parameter: Dict[str, float],
        defect_ctx: Dict[str, Any],
        domain_limits: Optional[Dict[str, float]] = None,
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
            domain_limits)

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
                    # ⚠️ activation 是**组内占比**（同参数组内各规则占比之和 = 1）
                    #    ⇒ 这里乘出来的是“该规则在它所属参数组里的贡献份额”，
                    #    聚合层裸累加 = 组内加权平均。
                    delta=float(value) * float(activation),
                    activation=float(activation),
                    # ⚠️ raw_activation 是**原始激活度**（前件隶属度之积），
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
        for item in filtered.advice_items:
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
            domain_limits)
        if not keyword_profiles:
            return out

        try:
            net = FuzzyRuleNet(mamdani_rules, keyword_profiles)
            # ⚠️ 传副本：内核不得改调用方的参数字典（口径同数值层）
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
    # 归并与格式化逻辑在 recommendations.py：
    #   - aggregate()          逐条调整量 → 参数级汇总
    #   - to_recommendations() 参数级汇总 → AlgorithmRecommendation
    # 本类只负责"调一下"，不掺和聚合细节。
    # -----------------------------------------------------------------------


# 注册引擎
AlgorithmRegistry.register('fuzzy', FuzzyEngine())
