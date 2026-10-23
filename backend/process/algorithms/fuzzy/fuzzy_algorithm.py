"""
模糊推理引擎 - 主入口

基于模糊规则进行缺陷修正推荐。

采用"双层并行架构"（见 fuzzy-engine-reference.md §2）：

⚠️ 这里的"层"按**结论形态**划分（这条规则的结论能不能算出数值），
   与规则库层级（base / 产品库 / specificity）**完全无关**：

- 数值层 (NumTskRuleNet)   → 数值/百分比结论（``X_add_3.8`` / ``X_reduce_30%``）
- 提示层 (FuzzyRuleNet)    → 检查/弹窗结论（``X_adjust_请检查锁模力是否不合理。``）
                            + 模糊等级结论（``X_add_low``，兼容 Rule.dat 风格）
- 合并策略                → 同层聚合 + 跨层覆盖（方案 B）
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

from process.algorithms.base import AlgorithmBase, Recommendation, AlgorithmRegistry
from process.algorithms.fuzzy.fuzzy_core.models.nets import (
    FuzzyRuleNet,
    NumTskRuleNet,
)
from process.algorithms.fuzzy.fuzzy_core.parsing import (
    collect_param_names,
    parse_rule,
)
from process.algorithms.fuzzy.ports import (
    ResolvedRule,
    RuleQueryContext,
    RuleRepository,
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

    # ============================================================
    # 字段命名约束声明（Port-Adapter 模式的“端口”部分）
    #
    # 设计（见 algorithm-context-design.md §6.10）：
    # - fuzzy rule 用的字段名（来自 RuleKeyword.keyword_name）是稳定的“业务专家约定”
    # - 本声明让算法侧声明“我需要什么字段名”这种接口契约
    # - 上层（数据准备层 _normalize_field_name_by_spec）按此映射翻译业务命名
    # - 算法内部不需要懂业务命名（保持纯函数）
    #
    # 约定：每个 key 是业务 prefix 或完整字段名，value 是算法侧使用的字段名。
    # - 前缀映射：value 是算法 prefix，拼上原序号（如 IL1、BT3）
    # - 完整字段名映射：value 是算法完整名（如 NT、CT、MEL、DDBM）
    #
    # 设计原则（2026-09-30 确认）：
    # - 以算法侧 RuleKeyword 为准则：表中每个 mapping 都对应实际存在的算法 keyword
    # - 理论上 ProcessParameter 中每个工艺字段都能在此找到映射（70/71 已覆盖）
    # - 未映射场景只发生在业务控制字段（如 _stg / _mode）或算法未启用的边界 case（如 met_lim_t）
    # ============================================================
    FIELD_NAME_ALIAS: Dict[str, str] = {
        # ---- 注射阶段（inj_*_N → IL/IV/IP_N，前缀映射）----
        "inj_pos":  "IL",   # 注射位置 1-6 → IL1-IL6
        "inj_spd":  "IV",   # 注射速度 1-6 → IV1-IV6
        "inj_pres": "IP",   # 注射压力 1-6 → IP1-IP6
        # ---- 保压阶段（hold_*_N → PP/PV/PT_N，前缀映射）----
        # 注意：保压只有压力/速度/时间三组（无位置字段：算法 ML 实际是熔胶位置）
        "hold_pres": "PP",   # 保压压力 1-5 → PP1-PP5
        "hold_spd":  "PV",   # 保压速度 1-5 → PV1-PV5
        "hold_t":    "PT",   # 保压时间 1-5 → PT1-PT5
        # ---- 熔胶阶段（met_*_N → ML/MP/MBP/MSR_N，前缀映射）----
        "met_pos":      "ML",   # 熔胶位置 1-4 → ML1-ML4（算法侧 ML 实际是熔胶位置）
        "met_pres":     "MP",   # 熔胶压力 1-4 → MP1-MP4
        "met_back_pres":"MBP",  # 背压 1-4 → MBP1-MBP4
        "met_rot_spd":  "MSR",  # 螺杆转速 1-4 → MSR1-MSR4
        # ---- 温度（完整字段名映射 或 前缀映射）----
        "noz_temp":  "NT",   # 喷嘴温度 → NT
        "cool_t":    "CT",   # 冷却时间 → CT
        "brl_temp":  "BT",   # 料筒温度 1-9 → BT1-BT9
        # ---- 熔胶动作（完整字段名映射）----
        "pre_met_decomp_dist":    "DDBM", # 熔胶前松退距离 → DDBM
        "pst_met_decomp_dist":    "DDAM", # 熔胶后松退距离 → DDAM
        "met_end_pos":            "MEL",  # 计量终点位置 → MEL
        # ---- 注射耗时（完整字段名映射）----
        "inj_t":     "IT",       # 注射时间 → IT
        "inj_dly_t": "ID",       # 注射延迟 → ID
        # ---- VP 切换（完整字段名映射）----
        "vps_mode": "VPTM",      # VP 切换模式 → VPTM
        "vps_pos":  "VPTL",      # VP 切换位置 → VPTL
        "vps_pres": "VPTP",      # VP 切换压力 → VPTP
        "vps_spd":  "VPTV",      # VP 切换速度 → VPTV
        "vps_t":    "VPTT",      # VP 切换时间 → VPTT
    }

    # 分段参数的序号偏移（业务 1-based → 规则库 0-based）
    #
    # 事实依据：规则库段号以 0-based 为主（IV0 719 次 / IV1 38 次 / IV2 15 次），
    # 与 RuleKeyword 的 IV0~IV5 / PP0~PP4 完全吻合；而业务字段是 1-based
    # （inj_spd_1..6）。翻译层统一对齐规则库，故分段参数偏移 -1。
    #
    # 不在表里的前缀偏移为 0（整段参数，不带序号）。
    FIELD_INDEX_OFFSET: Dict[str, int] = {
        "inj_pos": -1,      # 注射位置 1-6 → IL0-IL5
        "inj_spd": -1,      # 注射速度 1-6 → IV0-IV5
        "inj_pres": -1,     # 注射压力 1-6 → IP0-IP5
        "hold_pres": -1,    # 保压压力 1-5 → PP0-PP4
        "hold_spd": -1,     # 保压速度 1-5 → PV0-PV4
        "hold_t": -1,       # 保压时间 1-5 → PT0-PT4
        "met_pos": -1,      # 熔胶位置 1-4 → ML0-ML3
        "met_pres": -1,     # 熔胶压力 1-4 → MP0-MP3
        "met_back_pres": -1,  # 背压 1-4 → MBP0-MBP3
        "met_rot_spd": -1,  # 螺杆转速 1-4 → MSR0-MSR3
    }

    # 整段族参数：业务侧 N 个独立段，规则库侧只认一个名字
    #
    # 规则库用单一 `BT` 表示整体料筒温度（334 次），业务侧是 brl_temp_1..9。
    # 翻译规则：段 1 → 家族名（BT），段 N → 家族名 + N（BT2..BT9）。
    # 规则库实际只引用 BT（BT1 是历史 1-based 写法，少量），其余段无害。
    FAMILY_FIELD_ALIAS: Dict[str, str] = {
        "brl_temp": "BT",
    }

    # ------------------------------------------------------------------
    # 反向映射：算法字段名 → 业务字段名
    # ------------------------------------------------------------------
    @classmethod
    def to_business_name(cls, algo_name: str) -> Optional[str]:
        """算法字段名 → 业务字段名（FIELD_NAME_ALIAS 的反向映射）。

        与「业务 → 算法」的翻译共用同一份声明（FIELD_NAME_ALIAS /
        FIELD_INDEX_OFFSET / FAMILY_FIELD_ALIAS），保证两向一致：

        - 整段族（brl_temp_1..9 → BT / BT2..BT9）：``BT`` → ``brl_temp_1``，
          ``BT3`` → ``brl_temp_3``
        - 分段参数（业务 1-based → 规则库 0-based）：``IV0`` → ``inj_spd_1``
        - 完整字段名：``NT`` → ``noz_temp``、``MEL`` → ``met_end_pos``

        编排层（parameter_optimize）用它把算法推荐写回业务字段：
        算法名与业务字段名不在同一个命名空间，直接覆盖 baseline 必然落空。

        Returns:
            业务字段名；无对应业务字段时返回 None
            （如 ``IPOS`` / ``CUSION`` 这类规则库专用参数，ProcessParameter
            里没有对应列），调用方应原样保留。
        """
        name = (algo_name or '').strip()
        if not name:
            return None

        # 1) 整段族参数（BT → brl_temp_1；BT3 → brl_temp_3）
        for business_prefix, family_name in cls.FAMILY_FIELD_ALIAS.items():
            if name == family_name:
                return f'{business_prefix}_1'
            if not name.startswith(family_name):
                continue
            suffix = name[len(family_name):]
            if suffix.isdigit():
                return f'{business_prefix}_{suffix}'

        # 2) 分段参数（IV0 → inj_spd_1）
        for business_prefix, offset in cls.FIELD_INDEX_OFFSET.items():
            algo_prefix = cls.FIELD_NAME_ALIAS.get(business_prefix)
            if not algo_prefix or not name.startswith(algo_prefix):
                continue
            suffix = name[len(algo_prefix):]
            if not suffix.isdigit():
                continue
            return f'{business_prefix}_{int(suffix) - offset}'

        # 3) 完整字段名（NT → noz_temp）
        for business_key, algo_full in cls.FIELD_NAME_ALIAS.items():
            if business_key in cls.FIELD_INDEX_OFFSET or business_key in cls.FAMILY_FIELD_ALIAS:
                continue
            if algo_full == name:
                return business_key

        return None

    def __init__(self, repository: Optional[RuleRepository] = None):
        """构造引擎。

        Args:
            repository: 规则仓库端口（`RuleRepository` 协议）。
                传 None 时使用默认实现 `RuleQueryService`，
                且**延迟到首次访问数据时才导入**——
                这样 `import fuzzy_algorithm` 不会把 Django ORM 拖进来，
                编排层可以在没有数据库环境时被 import 和调用。
        """
        self._repo = repository
        # 字段定性降级清单（每次 recommend 开头重置，见 recommend()）
        self._field_reports = []
        # 规则级诊断清单（条目级跳过时记录；每次 recommend 开头重置）
        self._diagnostics = []

    def _get_repository(self) -> RuleRepository:
        """取规则仓库端口（默认实现延迟导入）。"""
        if self._repo is None:
            from process.algorithms.fuzzy.services.rule_query_service import RuleQueryService
            self._repo = RuleQueryService()
        return self._repo

    def recommend(self, context: dict) -> List[Recommendation]:
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
                'rule_library_code': 'packaging',    # 可选
            }

        Returns:
            List[Recommendation]
        """
        # 本引擎是模块级单例（见文件末尾 AlgorithmRegistry.register），
        # 而 _field_reports 会在推理过程中被追加 ⇒ 不重置就会随请求数无界增长
        # （内存泄漏），且上一轮的降级清单会被误读成本轮的结果。
        self._field_reports = []
        self._diagnostics = []

        try:
            return self._recommend(context)
        except Exception:
            # 第 0 层故障边界（编排层兜底）：异常止步于此。
            # 模糊算法失败不应该让整条 optimize 链 500。
            logger.exception('[FuzzyEngine] 模糊推理异常，已降级为空推荐')
            return []

    def _recommend(self, context: dict) -> List[Recommendation]:
        """主流程：5 步一条直线。

        1) 认缺陷   —— 从 feedback 取缺陷名 / 严重程度 / 位置
        2) 拉规则   —— 按缺陷 + 材料 + 产品选规则（DB 故障在此隔离）
        3) 分两堆   —— 按结论形态分流：numeric（数值结论）/ advisory（提示类结论）
        4) 并行推理 —— 数值层走 TSK，提示层走文本建议 / Mamdani（层间互不影响）
        5) 合并     —— 同参数聚合 + 跨层覆盖（方案 B）
        """
        # 1) 认缺陷
        defects = (context.get('feedback') or {}).get('defect', []) or []
        if not defects:
            return []

        # 缺陷上下文（缺陷名 / 严重程度 / 位置）——算法自己从 input 推导
        defect_ctx = self._extract_defect_context(context)
        defect_name = defect_ctx.get('defect_name')
        if not defect_name:
            logger.warning('[FuzzyEngine] 反馈中未指定缺陷类型（keyword_name），跳过推荐')
            return []

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

        # 3) 分两堆（按结论形态：数值结论 / 提示类结论）
        split = repo.split_by_conclusion_kind(all_rules)
        numeric_rules = split['numeric']
        advisory_rules = split['advisory']

        # 收集涉及的 RuleKeyword 名称（避免全表扫描）
        # 去掉空值字段：论域计算需要数值，None 会让隶属度函数直接抛错
        process_parameter = {
            k: v for k, v in (context.get('process_parameter') or {}).items()
            if v is not None
        }
        trend = context.get('iteration_trend', {}) or {}
        adjustment_factor = self._trend_to_factor(trend.get('trend', 'unknown'))

        # 4) 并行推理（层间隔离：一层失败不影响另一层）
        numeric_results = self._infer_numeric_layer(numeric_rules, process_parameter)
        advisory_results = self._infer_advisory_layer(advisory_rules, process_parameter)

        # 5) 合并（方案 B）：同层聚合 + 跨层覆盖
        return self._merge_layer_results(
            numeric_results=numeric_results,
            advisory_results=advisory_results,
            adjustment_factor=adjustment_factor,
            current_params=process_parameter,
        )

    def is_available(self, context: dict) -> bool:
        """判断是否可用。"""
        if not self._extract_defect_context(context):
            return False

        trend = context.get('iteration_trend', {}) or {}
        if trend.get('trend') == 'final':
            return False

        return True

    def run(self, context: dict) -> List[Recommendation]:
        """统一入口：包装 recommend()。

        algorithm_type='optimization'，返回 List[Recommendation]。
        """
        return self.recommend(context)

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

        历史实现读的是 `defect_name`（中文名），与规则库的英文缺陷码完全对不上，
        必然查不到规则——这是整条 optimize 链路 400 的最外层症状。
        """
        defects = (context.get('feedback') or {}).get('defect') or []
        for defect in defects:
            if not isinstance(defect, dict):
                continue
            keyword_name = defect.get('keyword_name')
            if not keyword_name:
                continue
            return {
                'defect_name': keyword_name,
                'level': defect.get('level'),
                'position': defect.get('position'),
            }
        return {}

    @staticmethod
    def _trend_to_factor(trend: str) -> float:
        """迭代趋势 → 调整系数。"""
        return {
            'worsening': 0.5,
            'improving': 1.2,
            'stable': 1.0,
            'unknown': 1.0,
            'final': 1.0,
        }.get(trend, 1.0)

    @staticmethod
    def _collect_keyword_names(rules: List[ResolvedRule]) -> set:
        """从规则字符串中提取所有涉及的工艺参数名。

        复用 fuzzykit 的词法解析（`fuzzy_core/parsing.py`）：
        - 剔除缺陷名（缺陷前件在规则匹配阶段已经保证，不参与论域；
          若把缺陷名当成参数收进来，缺陷会多出一个"参数论域"，
          规则的缺陷前件被当成可判级条件，而缺陷没有数值，
          激活度被 EPSILON 压到 ~0，整类规则全部失活）
        - 剔除缺陷位置名（DL*）

        前件与结论的参数都要收：结论参数缺 RuleKeyword 元数据时，
        该条规则的调整量会整体丢失。
        """
        return collect_param_names(r.rule_str for r in rules)

    def _load_keyword_dicts(
        self,
        param_names,
        process_parameter: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """按参数名批量拉 RuleKeyword 论域元数据（缺失的走兜底分支）。"""
        keyword_dicts: List[Dict[str, Any]] = []
        if param_names:
            try:
                keyword_dicts = self._get_repository().get_keywords_by_names(sorted(param_names))
            except Exception as e:
                logger.warning('[FuzzyEngine] 加载 RuleKeyword 失败: %s', e)

        # 兜底：用当前工艺参数值补全 keyword 元数据
        known_keywords = {kw['keyword'] for kw in keyword_dicts}
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
            keyword_dicts.append({
                'keyword': name,
                'lvl': 3,
                'min_val': 0.0,
                'max_val': current * 2,
                'step': max(current * 0.1, 0.01),
                # 标记这是【推测】出来的论域，不是 RuleKeyword 权威元数据
                'source': FIELD_SOURCE_GUESSED,
            })
        return keyword_dicts

    def _build_field_context(
        self,
        rules: List[ResolvedRule],
        process_parameter: Dict[str, Any],
        layer: str = 'numeric',
    ):
        """加载规则字段的论域元数据，并做一次字段体检。

        字段分三类：

        - ``authority``：有 RuleKeyword 权威元数据
        - ``guessed``  ：无权威元数据，按当前工艺参数值推测了一个论域
                        （lvl=3、论域[0, 当前值*2]）
        - ``unknown``  ：既无权威元数据也无当前值 ⇒ 规则少了一个门控条件，激活度偏高

        为什么要体检：字段缺元数据时，``nets.py`` 会【静默跳过】它（只有 debug 级
        日志），于是规则少了一个门控条件却无人知晓。现在把它提升到 warning 级。

        Args:
            rules: 本层要推理的规则。
            process_parameter: 当前工艺参数（字段名已归一化；不含设备/材料/模具信息）。
            layer: 层名（numeric / advisory），仅用于日志与清单归类。

        Returns:
            ``(keyword_dicts, classification)`` —— 前者送引擎，后者是分类结果。
        """
        param_names = self._collect_keyword_names(rules)
        keyword_dicts = self._load_keyword_dicts(param_names, process_parameter)

        guessed = {kw['keyword'] for kw in keyword_dicts
                   if kw.get('source') == FIELD_SOURCE_GUESSED}
        known = {kw['keyword'] for kw in keyword_dicts}
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
                '[FuzzyEngine][%s] %d 个字段使用推测论域（lvl=3、论域[0, 当前工艺参数值*2]）: %s',
                layer, len(classification['guessed']), classification['guessed'])

        self._field_reports.append({'layer': layer, 'classification': classification})
        return keyword_dicts, classification

    @staticmethod
    def _precheck_numeric_rules(
        rules: List[ResolvedRule],
    ) -> Tuple[List[ResolvedRule], List[Dict[str, Any]]]:
        """预检：把「送进数值层推理会崩」的规则挡在推理之前。

        崩溃点（`nets.py` 结论层）：``float(value['level'])``。
        而 `classify_conclusion_kind` 只要求「**至少一个**结论是数字」，
        所以形如 ``THEN IV0_add_2 AND IV0_add_low`` 的混合规则会被判为 numeric，
        但 ``float('low')`` 会抛 ValueError ⇒ **整层归零**（一条脏规则拖垮全部）。

        预检口径与 `classify_conclusion_kind` **完全一致**（同一套 isdigit 判定），
        保证「被判为 numeric」⇒「一定可安全推理」。

        Returns:
            ``(safe_rules, skipped)`` —— 可安全推理的规则（保持原顺序）、
            以及被跳过的规则明细（``{'rule', 'reason'}``）。
        """
        safe: List[ResolvedRule] = []
        skipped: List[Dict[str, Any]] = []
        for r in rules:
            bad_value = None
            for sol in parse_rule(r.rule_str)['solutions']:
                action = sol.get('action')
                if action not in ('add', 'reduce'):
                    # adjust / popup 在 nets 走特殊分支（存 9999.9 或进 r_extra），
                    # 不会做 float 转换 ⇒ 不需要预检。
                    continue
                value = str(sol.get('value', ''))
                if not value.rstrip('%').lstrip('-').replace('.', '', 1).isdigit():
                    bad_value = value
                    break
            if bad_value is None:
                safe.append(r)
            else:
                skipped.append({
                    'rule': r.rule_str,
                    'reason': f'结论值 {bad_value!r} 不是数值，送进数值层会抛 ValueError',
                })
        return safe, skipped

    def _infer_numeric_layer(
        self,
        numeric_rules: List[ResolvedRule],
        process_parameter: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """数值层推理（NumTskRuleNet，数值/百分比结论）。"""
        if not numeric_rules:
            return []

        # 第 2 层故障边界（条目级）：先把注定会崩的规则挑出去，
        # 其余规则照常推理（现状是：一条脏规则 ⇒ 整个数值层归零）。
        safe_rules, skipped = self._precheck_numeric_rules(numeric_rules)
        if skipped:
            self._diagnostics.append({'layer': 'numeric', 'skipped': skipped})
            logger.warning(
                '[FuzzyEngine] 数值层跳过 %d 条不可推理规则（其余规则照常推理）: %s',
                len(skipped), [s['reason'] for s in skipped][:5])
        if not safe_rules:
            logger.info('[FuzzyEngine] 数值层无安全规则，跳过')
            return []

        keyword_dicts, _classification = self._build_field_context(
            safe_rules, process_parameter, 'numeric')

        if not keyword_dicts:
            logger.info('[FuzzyEngine] 数值层无可用 RuleKeyword，跳过')
            return []

        repo = self._get_repository()
        rule_array = repo.to_rule_array(safe_rules)
        priority_array = repo.get_priority_array(safe_rules)

        try:
            net = NumTskRuleNet(rule_array, keyword_dicts, priority_array)
            results, extra = net.predict(process_parameter, top_k=len(safe_rules))
        except Exception as e:
            logger.exception('[FuzzyEngine] NumTskRuleNet 推理失败: %s', e)
            return []

        # 提取 [{param: value}] 字典 → List[Dict]
        out = []
        for rule_str, activation, adjustments in results:
            for param, value in adjustments.items():
                out.append({
                    'source': 'numeric',
                    'param': param,
                    'delta': float(value) * float(activation),
                    'activation': float(activation),
                    'rule': rule_str,
                })
        return out

    def _infer_advisory_layer(
        self,
        advisory_rules: List[ResolvedRule],
        process_parameter: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """提示层推理。

        提示层有两类规则，必须分开处理：

        1) 检查/弹窗类结论（`X_adjust_请检查锁模力是否不合理。`）
           → 提取提示文本，作为**文本建议**输出（不给数值）。
           这类规则绝不能进 Mamdani 数值层：它的结论值是提示语而不是模糊等级，
           查 HS_MAPPING_DICT 会 KeyError；就算不崩也算不出有意义的数值。

        2) 模糊等级结论（`X_add_low`）
           → Mamdani 全模糊推理（历史路径，规则库当前没有这种结论）。
        """
        if not advisory_rules:
            return []

        check_rules: List[ResolvedRule] = []
        mamdani_rules: List[ResolvedRule] = []
        for r in advisory_rules:
            if self._is_check_rule(r.rule_str):
                check_rules.append(r)
            else:
                mamdani_rules.append(r)

        out: List[Dict[str, Any]] = []

        # 1) 检查/弹窗类 → 文本建议
        for r in check_rules:
            for sol in parse_rule(r.rule_str)['solutions']:
                if sol.get('action') not in ('adjust', 'popup'):
                    continue
                advice = sol.get('value')
                if not advice:
                    continue
                out.append({
                    'source': 'advisory',
                    'param': sol.get('name', ''),
                    'delta': 0.0,
                    'activation': 0.0,
                    'rule': r.rule_str,
                    'advice': advice,
                })

        # 2) 模糊等级结论 → Mamdani
        if not mamdani_rules:
            return out

        keyword_dicts, _classification = self._build_field_context(
            mamdani_rules, process_parameter, 'advisory')
        if not keyword_dicts:
            return out

        rule_array = self._get_repository().to_rule_array(mamdani_rules)
        try:
            net = FuzzyRuleNet(rule_array, keyword_dicts)
            results = net.predict(process_parameter, top_k=len(mamdani_rules))
        except Exception as e:
            logger.exception('[FuzzyEngine] FuzzyRuleNet 推理失败: %s', e)
            return out

        for param_name, value, _ in results:
            out.append({
                'source': 'advisory',
                'param': param_name,
                'delta': float(value),
                'activation': float(_[0]) if isinstance(_, tuple) else 1.0,
                'rule': 'advisory',
            })
        return out

    @staticmethod
    def _is_check_rule(rule_str: str) -> bool:
        """规则结论是否是检查/弹窗类（`X_adjust_提示语` / `X_popup_xxx`）。"""
        for sol in parse_rule(rule_str)['solutions']:
            if sol.get('action') in ('adjust', 'popup'):
                return True
        return False

    @staticmethod
    def _merge_layer_results(
        numeric_results: List[Dict[str, Any]],
        advisory_results: List[Dict[str, Any]],
        adjustment_factor: float,
        current_params: Dict[str, float],
    ) -> List[Recommendation]:
        """合并双层结果（方案 B：同层聚合 + 跨层覆盖）。

        两层按**结论形态**划分，与规则库层级无关：

        - 数值层（numeric）：能算出数值的结论，delta 参与聚合
        - 提示层（advisory）：检查/弹窗类文本结论，不参与数值聚合

        跨层规则：数值层胜出，提示层只作 `advisory_reference` 注释。

        返回 Recommendation 列表。
        """
        merged: Dict[str, Dict[str, Any]] = {}
        advice_items: List[Dict[str, Any]] = []

        for rec in numeric_results:
            p = rec['param']
            if p not in merged:
                merged[p] = {
                    'param': p,
                    'delta': rec['delta'],
                    'activation_sum': rec['activation'],
                    'rule_count': 1,
                    'sources': ['numeric'],
                    'advisory_reference': None,
                }
            else:
                merged[p]['delta'] += rec['delta']
                merged[p]['activation_sum'] += rec['activation']
                merged[p]['rule_count'] += 1

        for rec in advisory_results:
            # 检查/弹窗类结论（`X_adjust_提示语`）是**文本建议**：
            # delta 恒为 0，混进数值聚合会产生"保持不变"的假推荐，
            # 必须单独输出（recommended_value=None）。
            if rec.get('advice'):
                advice_items.append(rec)
                continue
            p = rec['param']
            if p not in merged:
                merged[p] = {
                    'param': p,
                    'delta': rec['delta'],
                    'activation_sum': rec['activation'],
                    'rule_count': 1,
                    'sources': ['advisory'],
                    'advisory_reference': None,
                }
            else:
                # 数值层已覆盖，仅作 advisory_reference 注释
                merged[p]['advisory_reference'] = rec['delta']
                merged[p]['sources'].append('advisory')

        # 转换为 Recommendation
        recommendations: List[Recommendation] = []
        for p, info in merged.items():
            raw_current = current_params.get(p)
            current_value = float(raw_current) if raw_current is not None else 0.0
            adjusted_delta = info['delta'] * adjustment_factor
            recommended_value = current_value + adjusted_delta

            recommendations.append(Recommendation(
                param_name=p,
                current_value=current_value,
                recommended_value=recommended_value,
                confidence=min(info['activation_sum'] / max(info['rule_count'], 1), 1.0),
                reason=f"模糊推理 (sources={info['sources']})",
                source='fuzzy.numeric' if 'numeric' in info['sources'] else 'fuzzy.advisory',
                direction=(
                    'increase' if adjusted_delta > 0
                    else 'decrease' if adjusted_delta < 0
                    else 'hold'
                ),
            ))

        # 检查/弹窗类建议：文本建议，不给数值，方向为「检查」
        for rec in advice_items:
            param_name = rec.get('param') or ''
            raw_current = current_params.get(param_name)
            recommendations.append(Recommendation(
                param_name=param_name,
                current_value=float(raw_current) if raw_current is not None else 0.0,
                recommended_value=None,
                confidence=None,
                reason=f"模糊推理建议：{rec.get('advice')}",
                source='fuzzy.check',
                direction='check',
            ))

        return recommendations

    # -----------------------------------------------------------------------
    # 兼容老接口（暂时不实现）
    # -----------------------------------------------------------------------

    def load_rules(self):
        """加载模糊规则（兼容接口，占位）。"""
        # 当前实现：规则在每次 recommend 时通过 RuleQueryService 动态拉取
        pass


# 注册引擎
AlgorithmRegistry.register('fuzzy', FuzzyEngine())
