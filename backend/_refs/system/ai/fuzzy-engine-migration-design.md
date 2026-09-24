# FuzzyEngine 迁移实施计划

> 本文档记录将 `old/mdprocess/utils/fuzzykit/` 中的模糊推理能力迁移到 `process/engines/fuzzy/` 的完整方案，包括数据模型、算法层、适配层与服务层的端到端改造路径。
>
> 文档生成时间：2026-07-02

## 1. 背景与目标

### 1.1 现状

- 老 fuzzykit 位于 `old/mdprocess/utils/fuzzykit/`，约 3663 行
- 当前 `process/engines/fuzzy/` 仅保留骨架（约 540 行，`recommend()` 返回空）
- 服务侧 `recommendation_service.py` 的 `get_recommendations()` 也直接返回空结果
- 规则库模型（`RuleKeyword` / `RuleMethod`）已就位，但 `RuleKeyword` 缺 `step` 字段
- `FuzzyEngine.is_available()` 已正确判断 trend 与缺陷

### 1.2 目标

1. 把 `NumTskRuleNet`（生产主路径）+ `FuzzyRuleNet`（兼容老字符串规则）从老 fuzzykit 迁入 `fuzzy_core/`
2. **不**迁 `TskRuleNet`（一阶代数式 TSK），它是死代码，命名误导，从未真实启用
3. 把规则来源从字符串文件改为 `RuleMethod` 为主，兼容老字符串文件作为初始规则源
4. 让 `recommendation_service.get_recommendations()` 端到端跑通，返回真实推荐
5. `iteration_trend` 调整因子从 `FuzzyEngine` 内部外移到 `recommendation_service`，保持引擎纯粹

### 1.3 迁移范围限定（本研究只关注模糊神经网络本身）

本次迁移工作**仅覆盖 FuzzyEngine 模糊神经网络本身**，不包括以下业务层调用细节：

**在范围内（本次实施）：**
- fuzzy_core 算法实现（FuzzyRuleNet、NumTskRuleNet、ParticularRules、MF 函数）
- RuleMethod JSON Schema 定义与序列化适配
- FuzzyEngine.recommend() 串联推理
- RuleKeyword.step 字段补全与迁移

**不在范围内（本次不实施）：**
- ProcessRecommendationService 业务编排（含 defect_degree→w 调整系数、iteration_trend 调整因子、opt_nums 迭代反馈、IDT1~6 行程计算、HOLDEXIST/VALVEEXIST 派生字段等）
- optimize_export 完整 schema 设计（candidate_rules + adjust_rules 双轨混合输出）
- API 层输入参数构造的所有细节

以上业务层内容由调用方（`ProcessRecommendationService`）实现，本文档只在 §2 的设计中列出"调用方约定"作为接口约定，不在算法层实施。

### 1.4 项目原始设计的命名混乱记录

> **本节是历史教训，迁移时必须了解的背景**

老 fuzzykit 在命名与实际用途上有三层混乱，下个开发者容易踩坑：

| 混乱维度 | 具体表现 |
|---------|---------|
| 函数名 vs 实际网络 | `tsk_algorithm()` 函数名误导，主体跑的是 `NumTskRuleNet`（零阶 TSK），但函数名里有 `tsk` 让人误解 |
| 类名 vs 实际启用 | `TskRuleNet` 类（一阶代数式 TSK）有实现但被显式注释，从未真实启用；它是死代码 |
| 开发者主观归类 | 早期项目把模糊推理整套叫"TSK"，实际跑的是 Mamdani 处理 Rule.dat 全模糊规则 |

真实演化路径：

1. **阶段 A**：规则存 Rule.dat 文本，全模糊（`_add_low`），跑 `FuzzyRuleNet`（Mamdani）
2. **阶段 B**：规则改存数据库（`RuleMethod`），结论数字化（`add_10` / `add_50%`），跑 `NumTskRuleNet`，函数沿用 `tsk_algorithm` 命名
3. **TskRuleNet（代数式）**：从未启用，**直接跳过，不实现**

### 1.5 本次设计哲学：双层规则架构（工厂级 + 兜底层）

基于代码事实以及规则质量反思，本次迁移采用**双层并行架构**，而非简单的"只迁一种网络"：

| 层级 | 网络 | 适用场景 | 规则特征 | 推理结果 |
|------|------|---------|---------|---------|
| **工厂级** | NumTskRuleNet | 材料机台工艺稳定后，通过数据训练或专家经验固化的标准操作规则 | 百分比（`add_10%`）或关键数值阈值（`add_5`），需仔细调整 | 精确调整量 |
| **兜底层** | FuzzyRuleNet (Mamdani) | 新材料、新机器、新缺陷类型；工程师现场经验 | 模糊级别（`add_low`/`add_mid`/`add_high`），实写自然 | 隶属度计算自适应 |

**双层并行运行**：
- FuzzyEngine 同时加载两层规则
- 同名参数上：工厂级优先（已知材机型的标准答案）
- 未覆盖参数上：兜底级补充（新场景的应急经验）
- 两层互不覆盖，结果合并返回（含 `sources` 列表说明谁在场）

**设计动机**：
- **避免规则膨胀**：工程师写兜底规则用 "low→add_mid"，不需枚举 `add_1, add_3, add_1.5`
- **渐进式智能化**：初期只兜底规则 = 能跑；成熟后增加工厂规则 = 提高精度
- **降级容错**：工厂规则解析失败自动退化到兜底

所以本次迁的"双网络"是：**Mamdani（兜底层）+ NumTskRuleNet（工厂级）双层并行，TskRuleNet 不迁**。

## 2. 设计决策

| 决策点 | 选项 | 理由 |
|--------|------|------|
| 推理网络 | Mamdani（兼容历史 Rule.dat）+ NumTskRuleNet（生产路径） | **不迁 TskRuleNet（一阶代数式）**，它是死代码从未真实启用；Mamdani 只为历史全模糊规则导入留个口子 |
| 规则形式 | 只迁移两种规则：条件模糊+结论模糊（Mamdani 时代 Rule.dat）、条件模糊+结论数值（数据库时代） | **不迁代数式 TSK 规则**——项目从未有过这种规则 |
| 规则来源 | RuleMethod 为主 + `engines/fuzzy/rules/` 目录兼容老字符串 | RuleMethod 是 DB 持久化方案；老字符串作为初始规则、调试样本与导出格式 |
| 数值表示 | action 字段：`add/reduce`（绝对）vs `add_pct/reduce_pct`（百分比） | 保留老 NumTSK 的"数值/百分比规则分类"语义，对应 `rule_classify` |
| 调整机制 | （调用方约定）缺陷程度与 trend 调整是业务层职责，不在 FuzzyEngine 内部实现 | FuzzyEngine 只产出包含 absolute value 的 Recommendation，外层（`ProcessRecommendationService`）负责调整系数与迭代逻辑 |
| 规则组织方式 | 多规则库（RuleLibrary隔离大类）+ 库内条件匹配（polymer/product） | 现有模型已预留字段（RuleLibrary.library_code / polymer_category / product_category），以多库粗粒度 + 库内细粒度混合模式与现实工业场景匹配 |
| 分类维度位置 | polymer_category / product_category 保留在 RuleMethod 模型字段，不写进 rule_content.conditions | 路由层 vs 推理层职责隔离：分类维度是离散值（exact match 在路由层），工艺参数是连续值（fuzzy_level 在推理层）；两者本质不同不应混入同一表达式 |
| 跨聚合复用 | 用 RuleLibrary.parent_library 库层级继承，不在 rule_content 里写 OR | 优势：天然支持跨 polymer 复用 + 特定场景覆盖，无需扩展推理算法 |
| 冲突消解策略 | **同层聚合 + 跨层覆盖（方案B）**：同层规则按 priority 与激活度加权求和；跨层（工厂 vs 兜底）工厂级胜出 | 集成 fuzzykit 已有 priority_array 机制（nets.py:1209），加权和自然消解；跨层覆盖提息可解释性 |
| priority 协议 | 精度分级：L1精确=10 / L2部分（polymer）=5 / L3部分（product）=4 / L4默认=1 | 手动表，避免引入自动计算逻辑 |
| step 字段填充 | 扫描 `old/mdprocess/utils/fuzzykit/range_test.csv` 迁移填充 | 老数据是事实标准来源；其他留空待业务补 |
| x dict 范围 | 只取 process_parameter 与 RuleMethod 涉及的 keywords 交集 | 避免空值/无关参数污染模糊化计算 |
| 字符串目录用途 | 新建 `engines/fuzzy/rules/` 作为初始规则源，提供"导入 DB"和"从 DB 导出"脚本 | 既保留文档可读性，又能让 DB 与文件双向同步 |

## 3. 实施阶段

### 阶段 1：数据模型补全

#### 1.1 RuleKeyword 加 `step` 字段

**修改文件**：`process/models/rules.py`

```python
# 在 action_max_val 之后新增
step = models.FloatField(null=True, blank=True, verbose_name="单次调整步长")
```

#### 1.2 迁移命令 `init_fuzzy_ranges`

**新增文件**：`bootstrap/management/commands/init_fuzzy_ranges.py`

**功能**：
- 读 `old/mdprocess/utils/fuzzykit/range_test.csv`（7 列：Name, level, range_min, range_max, action_range_min, action_range_max, action_maxVal）
- 通过字段名映射（草案见下）匹配 RuleKeyword
- 用 CSV 中的 `action_maxVal` 列填充 `RuleKeyword.step`
- 支持 `--dry-run` 与 `--force` 参数

**字段名映射草案**（待业务侧确认）：
```python
KEYWORD_NAME_MAPPING = {
    'IDT1': 'inj_dly_t',
    'IDT2': 'inj_t',
    'IP1':  'inj_pres_1',
    # ... 待补充完整映射
}
```

> **风险提示**：若业务已有正式映射表，请告知；否则按草案写入命令。

### 阶段 2：fuzzy_core 算法层

#### 2.1 扩充 `macros.py`

**修改文件**：`process/engines/fuzzy/fuzzy_core/macros.py`

追加：
```python
HS_MAPPING_DICT = {
    'low': 0, 'mid': 1, 'high': 2,
    'level1': 0, 'level2': 1, 'level3': 2,
    'level4': 3, 'level5': 4, 'level6': 5,
    'level7': 6, 'level8': 7, 'level9': 8,
    'add': 1, 'reduce': -1, 'adjust': -2,
}

HS_DEFECT_DICT = {
    1: 'SHORTSHOT', 2: 'FLASH', 3: 'SHRINKAGE',
    4: 'WELDLINE', 5: 'ABERRATION', 6: 'AIRTRAP', 7: 'TOPWHITE',
}

ADJUST_ACTIONS = {
    'add': 1, 'reduce': -1,            # 绝对
    'add_pct': 'mul_pct_pos',
    'reduce_pct': 'mul_pct_neg',
}
```

#### 2.2 扩充 `functional.py`

**修改文件**：`process/engines/fuzzy/fuzzy_core/functional.py`

保留现有 5 个 MF，追加老 fuzzykit 三个核心 MF：
```python
def gauss_mf(x, mean, sigma): ...
def tri_mf(x, a, b, c): ...
def trap_mf(x, a, b, c, d): ...
```

#### 2.3 重写 `models/nets.py`

**修改文件**：`process/engines/fuzzy/fuzzy_core/models/nets.py`

迁移 4 个核心类（约 800 行）：

| 类 | 来源行号 | 关键方法 |
|----|----------|----------|
| `FuzzyFeature` | 老 nets.py L12 | `__init__` / `get_value_by_level(x, level)` / `get_all_value(x)` |
| `FuzzyRule` | 老 nets.py L74 | `__init__(rule_string)` / `_rule_process` 解析 |
| `NumTskRule` | 老 nets.py L869 | 同上，识别 `%` 后缀区分数值/百分比 |
| `FuzzyRuleNet` (Mamdani) | 老 nets.py L132 | `inference(x)` → centroid 去模糊；`predict(x, top_k)` |
| `NumTskRuleNet` | 老 nets.py L959 | `tsk_inference(x, priority_array)` → 数值 TSK + 优先级加权 |

**保留** `TskRuleNet` 作为兼容占位（暂不实现完整逻辑）。

#### 2.4 新建 `utils/translate.py`

**新增文件**：`process/engines/fuzzy/fuzzy_core/utils/translate.py`

迁移自 `old/mdprocess/utils/fuzzykit/fuzzy_core/utils/translate.py`：
```python
def defect_translate(defect: dict) -> List[str]:
    """数值 → '短射_low' / '短射_mid' / '短射_high'"""

def rule_standard(label: str, rules: list, defects: list) -> List[str]:
    """CSV 字符串规则 → 标准 'IF X_mid AND Y_low THEN Z_add_5' 格式"""
```

### 阶段 3：适配层

#### 3.1 新建 `adapters.py`

**新增文件**：`process/engines/fuzzy/adapters.py`

```python
class RuleMethodAdapter:
    """RuleMethod.rule_content JSON ↔ RuleNet 字符串"""

    @staticmethod
    def to_rule_string(rule_method: dict) -> str:
        """JSON → 'IF X_low THEN Z_add_10' 格式"""

    @staticmethod
    def from_rule_string(rule_str: str) -> dict:
        """反向：字符串 → JSON（用于 DB 导出场景）"""

    @staticmethod
    def extract_keyword_names(rules: List[dict]) -> List[str]:
        """从 conditions/adjustments 中抽出所有 param 名"""


class RuleKeywordAdapter:
    """RuleKeyword ↔ RuleNet keyword dict"""

    @staticmethod
    def to_range_dict(keyword: dict) -> dict:
        """输出：{'keyword': 'inj_pres_1', 'lvl': 3,
               'min_val': 0, 'max_val': 200, 'step': 10}"""

    @staticmethod
    def get_keywords_by_names(names: List[str]) -> List[dict]:
        """按变量名列表查询 RuleKeyword，返回 RuleNet 格式 dict 列表"""
```

#### 3.2 字符串规则目录

**新增目录**：`process/engines/fuzzy/rules/`

**初始文件**：`fuzzy_rules.txt`，从老 fuzzykit 复制 5-10 条典型规则（短射、飞边各 2-3 条）作为文档与调试样本。

### 阶段 4：FuzzyEngine.recommend 串联

**修改文件**：`process/engines/fuzzy/fuzzy_engine.py`

**核心流程**（替代原 70 行 stub）：
```python
def recommend(self, context: dict) -> List[Recommendation]:
    defects = context.get('defect_feedbacks', [])
    if not defects:
        return []

    # 1. 按主缺陷拉规则
    main_defect = defects[0].get('defect_type')
    rules = rule_service.get_rules_by_defect(main_defect)
    if not rules:
        return []

    # 2. 字符串化
    rule_strs = [RuleMethodAdapter.to_rule_string(r) for r in rules]
    priority_array = [r.get('priority', 1.0) for r in rules]

    # 3. 取相关 keywords
    keyword_names = RuleMethodAdapter.extract_keyword_names(rules)
    keywords = RuleKeywordAdapter.get_keywords_by_names(keyword_names)

    # 4. 当前参数 → x dict（只取交集）
    param = context.get('process_parameter', {})
    x = {k: param[k] for k in keyword_names if k in param}

    # 5. 构造 RuleNet + 推理
    try:
        net = NumTskRuleNet(rule_strs, keywords, priority_array)
        results, _ = net.predict(x, top_k=5)
    except Exception as e:
        logger.warning(f"FuzzyEngine 推理失败: {e}")
        return []

    # 6. 转 Recommendation（trend 在外部处理，此处不乘因子）
    return [
        Recommendation(
            param_name=adj_param,
            current_value=x.get(adj_param, 0),
            recommended_value=adj_value,
            confidence=activation,
            reason=rule_desc,
            source='fuzzy_rule',
        )
        for rule_desc, activation, adjustments in results
        for adj_param, adj_value in adjustments.items()
    ]
```

**删除**：原 `adjustment_factor = 0.5/1.0/1.2` 的 trend 因子逻辑（按决策外移）。

### 阶段 5：recommendation_service 串通 + trend 后处理

**修改文件**：`process/services/recommendation_service.py`

```python
def get_recommendations(self, process_condition_id, defect_feedbacks, engine_types=None):
    context = self._build_context(...)

    # 1. 拿可用引擎
    engines = EngineRegistry.get_engines_by_priority(context, engine_types)

    # 2. 收集各引擎结果
    all_recs = []
    engine_sources = {}
    for engine in engines:
        recs = engine.recommend(context)
        engine_sources[engine.engine_name] = recs
        all_recs.extend(recs)

    # 3. trend 后处理（外移到此处）
    trend = context.get('iteration_trend', {})
    factor = self._trend_adjustment_factor(trend)
    for rec in all_recs:
        if rec.source == 'fuzzy_rule' and rec.action_type == 'absolute':
            rec.recommended_value = rec.current_value + \
                (rec.recommended_value - rec.current_value) * factor

    # 4. 合并去重
    merged = self._merge_recommendations(all_recs)

    return {
        'recommendations': merged,
        'engine_sources': engine_sources,
        'best_recommendation': merged[0] if merged else None,
    }

def _trend_adjustment_factor(self, trend: dict) -> float:
    return {
        'worsening': 0.5,
        'improving': 1.2,
        'stable':    1.0,
    }.get(trend.get('trend', 'unknown'), 1.0)
```

**引擎自注册**：在 `ProcessRecommendationService.__init__` 中 import 引擎模块以触发 `EngineRegistry.register()`：

```python
def __init__(self):
    from process.engines.fuzzy import fuzzy_engine     # noqa
    from process.engines.expert import expert_engine   # noqa
    # TODO: rule_miner / llm
```

## 4. 端到端验证路径

1. **算法层**（阶段 2 末尾）：写 demo 数据跑通 `NumTskRuleNet.predict()` 返回 `(results, extras)` 形式
2. **适配层**（阶段 3 末尾）：构造 1 条 RuleMethod JSON 调 `RuleMethodAdapter.to_rule_string()` 验证字符串输出
3. **引擎层**（阶段 4 末尾）：手动构造 context（含 defect + current params）调 `FuzzyEngine().recommend(ctx)` 返回非空
4. **服务层**（阶段 5 末尾）：跑完整链路验 `recommendation_service` 输出 dict 中 `engine_sources['模糊推理']` 非空

## 5. 种子数据

阶段 5 完成后，准备 2-3 条 RuleMethod 种子数据入库（如短射 → `inj_pres_1` +10），通过 `init_rules` 风格脚本导入，覆盖以下场景：

| defect_name | condition 示例 | adjustment 示例 |
|-------------|---------------|-----------------|
| 短射 | `inj_pres_1` < 60 | `inj_pres_1` add 10 |
| 飞边 | `inj_pres_1` > 150 | `inj_pres_1` reduce 15 |
| 缩痕 | `hold_pres_1` < 50 | `hold_pres_1` add 5 |

## 6. 风险与待确认点

1. **CSV 字段名映射**：老 CSV 的 `IDT1` 等短码到新 `inj_pres_1` 长码，内嵌映射 dict 写入迁移命令
2. **rule_method.rule_content JSON 结构**：当前 `{conditions: [...], adjustments: [...]}`，按此解析
3. **fuzzy_rules.txt 内容**：从老 fuzzykit 复制 5-10 条典型规则作为初始样本
4. **trend factor 仅作用绝对增量**：百分比类的调整（`add_pct`）不适合乘 factor 缩放，跳过
5. **百分号解析兼容性**：保留老 fuzzykit 的 `%` 后缀识别（如 `IP_add_50%`），同时支持 JSON 的 `add_pct` 显式标记

## 7. 实施顺序

```
阶段 1: 数据模型
   ↓ RuleKeyword.step 字段就绪
阶段 2: fuzzy_core 算法层
   ↓ Net 类跑通 demo
阶段 3: 适配层
   ↓ Adapter + 字符串目录就绪
阶段 4: FuzzyEngine.recommend 串联
   ↓ 引擎返回真实 Recommendation
阶段 5: recommendation_service 串通
   ↓ 端到端验证通过
种子数据入库 → 服务可用
```

## 8. 文件变更清单

| 操作 | 路径 | 说明 |
|------|------|------|
| 修改 | `process/models/rules.py` | RuleKeyword 新增 step 字段 |
| 新增 | `bootstrap/management/commands/init_fuzzy_ranges.py` | 从老 CSV 迁移 step |
| 修改 | `process/engines/fuzzy/fuzzy_core/macros.py` | 追加 HS_MAPPING_DICT 等常量 |
| 修改 | `process/engines/fuzzy/fuzzy_core/functional.py` | 追加 gauss_mf / tri_mf / trap_mf |
| 修改 | `process/engines/fuzzy/fuzzy_core/models/nets.py` | 重写 4 个核心类 |
| 新增 | `process/engines/fuzzy/fuzzy_core/utils/translate.py` | defect_translate / rule_standard |
| 新增 | `process/engines/fuzzy/adapters.py` | RuleMethodAdapter / RuleKeywordAdapter |
| 新增 | `process/engines/fuzzy/rules/fuzzy_rules.txt` | 初始字符串规则样本 |
| 修改 | `process/engines/fuzzy/fuzzy_engine.py` | recommend() 重写 |
| 修改 | `process/services/recommendation_service.py` | 串通引擎 + trend 后处理 |

---

*文档生成时间：2026-07-02*
*最后更新：2026-07-02*