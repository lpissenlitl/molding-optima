# L2 策略层：形态设计讨论纪要（2026-11-12）

> ⚠️ **本文是讨论纪要，不是执行计划。**
> 文中所有「方向 / 建议 / 待办」均**未经用户拍板** ⇒ 不得据此直接实施。
> （规范：用户的话 = 授权；文档里的清单 = 需用户点头。）
>
> 配套主计划：`docs/strategy-consistency-layer-plan.md`（§8.4.3 是本轮的接线记录）。
>
> ✅ **已拍板并落地的部分**（2026-11-12 批次 7.2）见 §6 的标注；
> 未标注的仍待拍板 ⇒ 不得据此实施。

---

## 0. 状态速览

| 项 | 状态 |
|---|---|
| 批次 7.1（L2 **机制**接线） | ✅ 已完成 |
| 批次 7.2（L2 **形态**落地：策略表 + 场景） | ⏪ **已撤回**（批次 11）—— 机制保留，**载体**由策略表改为策略清单文件（§6.2） |
| 批次 9（**代码结构**按 4 层重排） | ✅ 已完成 —— pytest **80 passed**（76 → 80）；文件对照见 §3.7 |
| L2 的**形态** | 🟡 **部分拍板**：§6 ①②④ 已落地（**载体于批次 11 改为策略清单文件**）；③⑤⑥⑦⑧ 待定（⑧ = 阶段化，新提出） |
| 下一轮接续点 | **阶段化调机模型**（§6 表 ⑧）—— 每阶段关注点不同，先讨论清楚再落清单 |

---

## 1. 分层定位（此前已确立，本轮沿用；**批次 9 按「流程 4 层」重写表述**）

> 用户拍板（2026-11-12）：「**逻辑只有 4 层** ——
> 1. 算法给出调整方向 2. 结合实际情况，确定明确的调整方向
> 3. 整合参数 4. 校验参数合理性」⇒ **代码结构按这 4 层切**，
> 一层一个模块，依赖单向（``anchors ← direction ← integration ← validation``）。

| 层 | 职责 | 不管 | 代码落点 |
|---|---|---|---|
| **第1层** 算法给出调整方向 | 产出**平级**候选建议（调什么、调到多少） | 不做取舍 | 各算法包（`fuzzy/` `llm/` `empirical/`） |
| **第2层** 结合实际情况，确定**明确的**调整方向 | 这一轮属于哪类情形、允许调哪些、按什么次序、谁让位、谁暂缓 | 不重算数值 | `algorithms/decide_direction.py` |
| **第3层** 整合参数 | `MEL` 目标 ⇒ 计量位置 ⇒ 再定 `MEL`（只对**关系**负责） | 不做新旧值取舍、不判断场景 | `algorithms/integrate_params.py` |
| **第4层** 校验参数合理性 | 通用能力（差值越限 / 工艺窗口 / 锚点自检，**只读**） | 不改值、不阻断 | `algorithms/check_params.py` |
| 底座 | 字段口径 + 锚点关系（只定义一次） | — | `algorithms/anchors.py` |

**两条硬约束**：
- **歧义消解归第2层**（同批能否同时调 `MEL` 与 `DDAM` 是第2层的裁决）；
- **第3层手里只有「旧值 + 调整量」**，没有「新值」这个概念 ⇒ 第3层不做二选一。

---

## 2. 用户给出的原始例子（逐字保留 + 机制解释）

### 2.1 「短射有好多条调整方向和规则，我只需要在 L2 写一条」

> 「如果是短射，那么只调整注射量，那么最终结果就完全根据我们意图相关了；
> 如果我们 L2，短射允许调整注射量和注射速度，那么最终结果也会更改。」

⇒ 这是**准入（白名单）**语义：同一条 L2 规则换个取值 ⇒ 最终落地结果跟着变。
⇒ **L1 产出不变，变的是 L2 的筛** ⇒ 「最终结果完全由 L2 决定」。

### 2.2 「L2 其实更多的是经验」

> 「比如说我们先考虑产品是否打满，再考虑别的缺陷，或者说先考虑注射，再考虑保压。」

⇒ 两种不同**粒度**的次序：

| 例子 | 粒度 | 语义 |
|---|---|---|
| 先考虑产品是否打满，再考虑别的缺陷 | **方向级** | 先解决「充填不到位」这一方向，其余方向后置 |
| 先考虑注射，再考虑保压 | **参数组级** | 注射组优先于保压组 |

### 2.3 用户在本轮的两处纠正（**术语与边界**）

| 纠正 | 含义 |
|---|---|
| 「这里不应该叫缺陷归属」 | L2 要的不是「来自哪个缺陷」，而是**触发源**（`source` / `matched_rules`）。缺陷在规则库那边是**关键词**（`RuleKeyword`），不是建议的属性 |
| 「但是我们确实也需要 feedback 信息」 | 反馈用于**证伪 L2 的经验**（详见 §5.5） |

---

## 3. 现状事实（代码可核对）

### 3.1 L1 建议**已经带了**触发源 ⇒ L1 契约不用改

`fuzzy/recommendations.py::FuzzyRecommendation`：

| 字段 | 内容 |
|---|---|
| `param_name` / `current_value` / `recommended_value` | 基本量 |
| `confidence` | 组内平均原始激活度（聚合强度，非统计置信度） |
| `direction` | increase / decrease / hold / check |
| `reason` | 如「模糊推理 (sources=…)」 |
| `source` | `fuzzy.numeric` / `fuzzy.advisory` / `fuzzy.check` / `empirical…` |
| `conflict` | 冲突视图（只标记、不改数值） |
| **`matched_rules`** | **命中规则明细**：`[{rule, weight, raw_activation}]` —— **只透出、不参与计算** |

⇒ 「这条建议由哪条/哪组规则触发」信息**已在**（`matched_rules`；展示侧另有 `rule_refs` 提取逻辑）。

### 3.2 缺陷选取**已有可替换点**（不是缺口）

`algorithms/defect_selection.py`（213 行，「本轮处理哪个缺陷」的**唯一真相源**）：

- `DefectSelectionStrategy`（`Protocol`）—— docstring 明写「**业务优先级规则将来作为新策略接入，不改调用点**」；
- `FirstValidDefectStrategy`（fuzzy 用，默认）/ `FirstOnlyDefectStrategy`（empirical 用，**刻意不同**，保持历史行为）；
- `DefectSelection` 自带留痕（`selected` / `candidates` / `skipped`）+ `to_trace()`；
- 模块口径：「一次只解决一个缺陷，优先级机制**功能预留**」。

⇒ **缺陷级次序有现成接入点**，不必新造。

### 3.3 第2层现有机制（现落在 `algorithms/decide_direction.py`）

- `PriorityEntry(param_name, priority, group, reason)`
  ⇒ ⚠️ **`group` 目前只做标注，不参与裁决**；
- `PriorityTable(entries, default_priority=1000)`；
- `StrategyDecision(kept, yielded, order, deferred)` + `to_trace()`
  ⇒ ⚠️ **`to_trace` 只有 kept / yielded / deferred / order —— 没有「依据」**；
- `resolve_priority(candidates, table, satisfied, max_items)`
  ⇒ 排序（priority 升序、同级稳定）+ 让位（`satisfied`）+ 暂缓（`max_items`）；
- `priority_table_from_mapping` —— **次序的唯一来源是数据**（红线：模块不内置任何业务次序）。

### 3.4 已落地的接线（批次 7.1，✅）

> ⚠️ **文件位置已被批次 9 重排**（见 §3.7）：下表的机制**全部保留**，
> 只是从「按技术角色切分」改成「按 4 层流程切分」。

- `algorithms/decide_direction.py::build_plan`（原 `recommendation_apply.py::apply_recommendations`）
  ⇒ ① 候选集 → ② **第2层裁决** → ③ 明确方向（`MEL` 目标已翻成计量位置）；
- `services/parameter_optimize.py::_decide_plan_by_strategy`（原 `_apply_recommendations_to_baseline`，批次 14.3 / 14.4 改名）
  ⇒ **当前传空表/空场景 ⇒ 不裁决 ⇒ 运行行为与「不接第2层」完全一致**；
- 留痕落**后端日志**（`_logger.info('infer plan: …')`），**不动响应契约**；
- 护栏 `tests/test_direction_layer.py`（让位不落地 / 让位的 MEL 不进翻译 / 空表不变 / 暂缓也留痕 / 次序只来自数据）；
- 第3层侧口径（同时期）：`MEL` 两步式推算 `① ML_N 基准 = 原MEL − 原DDAM` `② MEL_新 = ML_N + DDAM + ΔDDAM + ΔMEL`
  ⇒ 落库的计量位置 = `原ML_N + ΔMEL`（**`ΔDDAM` 不叠加到计量位置**）。

### 3.5 当前**不可用**的两条路径（批次 7.2 后）

| 路径 | 依赖 | 现状 |
|---|---|---|
| `satisfied`（目标已达成 ⇒ 让位） | 派生输入量表（§7.0） | ⚠️ **机制已就位、但恒不触发**（批次 12.5 核实）—— ① 场景条件 = `selected_defect ∈ 某阶段码` ⇒ **场景命中即该阶段未达成**；② 白名单（准入）排在 `satisfied` **之前** ⇒ 白名单外的候选先被「本场景不允许」挡掉，**走不到** `satisfied` ⇒ 只剩「白名单内 + 其对应缺陷已消失」这一条窄路，而它对应的缺陷正是 `selected_defect`（在反馈里 ⇒ 未消失） |
| `max_items`（名额已满 ⇒ 暂缓） | 轮次名额 | ✅ **机制已就位**（批次 7.2）：由策略清单的 `max_items` 提供；✅ **12.3 起已生效**（清单有兜底场景 ⇒ 缺省一轮一个量，兼容旧版） |

### 3.6 批次 7.2 新增（形态落地）

| 模块 | 职责 | 关键点 |
|---|---|---|
| ~~`process/models/strategy.py`~~ | ⏪ **已撤回**（批次 11）—— 独立策略表（`StrategyPolicy` + `StrategyPriorityEntry`）连同 migration `0019` 与种子命令一并删除 | 撤回理由见 §6.2 |
| `process/algorithms/strategies.py` | **策略清单**（文件版）：场景 + 触发条件 + 准入 + 优先集 + 名额 + 目标口径 + 字段级优先级表 | **代码即规则**（不是 JSON 第二门语言）；**12.4a 起清单有 6 条**（S1 `filling_first` / S2 `shrinking_first` / S3 三条 `flash_first`·`burn_first`·`gasveins_first` + 兜底 `default_one_adjust`） |
| `process/algorithms/decide_direction.py` | 场景判定**机制**（条件求值 + 选策略）+ 裁决机制（同一模块） | **零 ORM**；条件沿用 `ExpertRule.conditions` 的 `field/operator/value` 范式；**缺数据 ⇒ 不命中**、**未知操作符 ⇒ 不命中** |
| `process/services/strategy_inputs.py` | 读策略清单 → 组装 `StrategyInputs`（场景 + 优先级表 + 留痕） | 读清单失败 ⇒ warning + **全空**（不裁决）；命中多条 ⇒ 取**第一条**（最具体） |
| `process/algorithms/anchors.py::resolve_fill_target` | 充填量目标求解器（第3层） | `目标行程 = 当前行程 × (目标重量/实测重量)`；`ML_N 目标 = VPTL + 目标行程`；数据不全 ⇒ `None`（回落增量口径，不臆造） |

**策略清单**（`process/algorithms/strategies.py`，批次 11 起）：

✅ **12.4a 起清单有 6 条**（不再为空）：
- **`filling_first`**（`priority=10`，S1 打足）：短射 + 重量不足 ⇒ 只动 `met_end_pos`、一次一个、
  `target_mode='fill_ratio'`（按重量比例重算行程）—— 对齐旧版「充填置顶 + 按重量比行程」；
- **`shrinking_first`**（`priority=20`，S2 补缩）：缩水/尺寸类 ⇒ 只动 `hold_pres_1` + `hold_t_1`；
- **`flash_first`**（`priority=30`）/ **`burn_first`**（`priority=40`）/ **`gasveins_first`**（`priority=50`）
  —— S3 外观三条（对齐拍板 G 的三种形态）：飞边 ⇒ 减胶量/降二段压力；
  烧焦 ⇒ 熔体侧（背压/松退/螺杆转速）；气纹 ⇒ 查背压；
- **`default_one_adjust`**（`priority=100`，`conditions=()` **恒命中** = 兜底）：
  缺省一轮只调一个量 —— 对齐旧版「给前端多条、只落地第一条」。

⚠️ **两类“不可调”是不同东西，别混**（12.4a 落地）：
- **白名单** `allowed_params`（空 = 不限制）= **场景范围** —— “这个场景该动哪些旋钮”；
  不在名单 ⇒ 让位「本场景不允许」；
- **禁入清单** `blocked_params`（空 = 不禁）= **基线项** —— “任何场景都不该动的旋钮”；
  在名单 ⇒ 让位「基线项 ⇒ 不参与阶段调机」。
⇒ 基线项（注射速度 `inj_spd_1`~`inj_spd_6`）**只写 6 个字面量**
（`tuning_strategy.BASELINE_BLOCKED_PARAMS`）⇒ **不需要列“所有可调旋钮”全集** ⇒ 新增旋钮不用改清单。
⚠️ **禁入排在准入之前**（裁决序 §2 早于 §3）⇒ 同时命中两者时留痕写**基线项**
（全局理由更强，不被“本场景不允许”掩盖）。
⚠️ **条件运算子 `in_any`**（12.4a 新增）：**字段值是集合** ⇒ 任一元素 ∈ 目标集合；
与 `in_set`（单值 ∈ 集合）**方向相反** ⇒ 两者并存不混。

⚠️ **名额是场景级参数，不是全局开关**：`max_items=None` = 不限 ⇒
**多参数输出是现成的出口** —— 某场景要一次调多个，只需让它不写 `max_items`
（或写更大的数）并排到兜底之前 ⇒ 兜底自动让位。**兼容旧版与多参数不是二选一。**

⚠️ **安全阀仍保留**：清单为空 / 一条都不命中 / 读清单失败 ⇒ 全部为空 ⇒ **不裁决**
⇒ 行为与「不接第2层」完全一致。（注：兜底恒命中 ⇒ 场景**永不为 None** ⇒
留痕里永远有「这一轮按什么场景裁决」。）

### 3.7 批次 9：代码结构按 **4 层流程**重排（✅ 已完成）

> 起因：用户连续两轮指出「**代码可读性太差**」——
> 之前是按「技术角色」（传导 / 检查 / 裁决 / 判定）切文件，
> 读懂一条链路要跳 7 个文件 ⇒ **按用户给的 4 层流程重新切**。

**新结构**（一层一个模块，依赖单向）：

```
anchors.py  ←  decide_direction.py  ←  integrate_params.py  ←  check_params.py
（底座）        （第2层）        （第3层）           （第4层）
```

**文件对照表**（旧 → 新）：

| 旧文件 | 职责 | 新落点 |
|---|---|---|
| `algorithms/strategy.py` | 优先级表 + 裁决 | ➡️ `algorithms/decide_direction.py`（裁决）+ `algorithms/strategies.py`（清单） |
| `algorithms/scenario.py` | 条件求值 + 选策略 | ➡️ `algorithms/decide_direction.py`（合并） |
| `algorithms/recommendation_apply.py` | 候选集 + 裁决 + 写入 | ➡️ 候选集 → `decide_direction.py::collect_candidates`；写入 → `integrate_params.py::apply_plan` |
| `algorithms/consistency.py` | 锚点传导 | ➡️ `algorithms/integrate_params.py` |
| `algorithms/param_consistency.py` | 差分 + 传导 + 自检编排 | ➡️ 差分 + 传导 → `integrate_params.py::integrate`；自检 → `check_params.py::validate` |
| `algorithms/param_checks.py` | 三类合理性检查 | ➡️ `algorithms/check_params.py` |
| `services/strategy.py` | 读策略表 + 组装 | ➡️ `services/strategy_inputs.py`（批次 11 起读**清单文件**） |

**命名统一**：`PolicySpec` / `ScenarioPolicy` / `StrategyResolution` 三名并存
⇒ 合并为**唯一** `ScenarioStrategy`（吸收 `conditions` / `priority` / `priority_table`），
服务层一律叫 `StrategyInputs`。
（批次 11：`policy_id` / `owner_rank` 随策略表一并撤回 —— 前者是表主键，后者是租户归属排序，
文件版载体两者都不存在。）

> 🔄 **2026-11-20 翻案：词根 `policy` → `strategy`**（用户拍板）
>
> - **理由①（工业语境）**：制造业现场的 "policy" 读作**管理制度/作业方针**
>   （安全方针、质量方针），不是「这台机这轮该调哪几个旋钮」的**加工决策**。
> - **理由②（词根一致）**：中文层本来就是「L1 = 规则 / L2 = 策略」，而英文里被劈成
>   `Policy` 与 `Strategy` 两套词根 ⇒ 纯词根不一致，与语义无关。
> - **词根排除**：`rule`（已被第1层规则库占满）/ `plan`（已被 `LandingPlan` 占用）
>   / `recipe`（中文「配方」偏材料配方）⇒ 只能统一到 `strategy`。
>
> **现行名**：`StrategyInputs` / `ScenarioStrategy` / `resolve_strategy_inputs` /
> `select_strategy` / `SCENARIO_STRATEGIES` / `services/strategy_inputs.py`。
> 本文档**历史批次记录**里的旧名（`PolicyResolution` / `ScenarioPolicy` /
> `resolve_policies` / `select_policy` / `SCENARIO_POLICIES` / `services/policies.py`）
> **一律保留原样** —— 那是当时的代码事实。

**service 层变成 4 层直线**（`parameter_optimize.py::_infer_core`）：

```python
# 第2层：结合实际情况，确定明确的调整方向
plan = _decide_plan_by_strategy(...)

# 第3层：整合参数（写入方向 + 锚点传导自洽）
integrated = apply_plan(baseline, plan, previous=baseline)

# 第4层：校验参数合理性（只报不阻断）
validation = validate(integrated.values)
```

⚠️ **行为等价**：除「出口统一量化」的时机由「写完方向就量化」改为
「整份参数整合完再量化」外，**算法产出的值不变**；
pytest **80 passed**（76 → 80，新增 4 条护栏）。

---

## 4. 差距清单

| # | 缺口 | 现状（批次 7.2 后） | 依赖新数据？ |
|---|---|---|---|
| 1 | **准入（白名单）**语义 | ✅ **已补**：场景 `allowed_params`（**空 = 不限制**，默认全允许）；不在白名单 ⇒ 让位，理由「本场景不允许」 | 否（机制） |
| 2 | **方向级次序**（「先充填打满」） | 🟡 **简化版已落地**：场景 `preferred_params`（优先集）能表达「充填优先」；但**缺「建议 → 方向」的通用映射** | 是 |
| 3 | **参数组级次序**（「先注射再保压」） | ❌ **未做**（本轮按旧版机制，旧版只有 `MEL` 置顶这一特例） | **否** |
| 4 | **group 未参与裁决** | ❌ **未做**（同 #3） | 否（机制） |
| 5 | **条件式让位** | ❌ **仍未做**（批次 12.5 核实：**当前架构下 `satisfied` 路径恒不触发**，见 §3.5）—— 12.5 只落地**阶段达成信号**（可观测、可留痕）；让位机制待「前提怎么算」拍板 | 依赖 #1 的前提量 |
| 6 | **留痕缺依据** | ✅ **已补**：`StrategyDecision.kept_reasons`（保留项依据）+ `to_trace()` 带出 ⇒ feedback **能证伪「次序」**了 | 否（小口子） |
| 7 | **建议列表与落地不一致** | ✅ **已修**（批次 12.8 + 12.9）—— 12.8 修「零落地」（L2 选了本轮落不了地的量 ⇒ L3 静默回退 ⇒ 整轮零变化）；12.9 修「展示含未采用项」：第2层的裁决结果逐条回填到建议（`decision_status` = adopted / yielded / deferred + 原因）并**随建议落库** ⇒ 前端**默认只显示已落地**（未采用项可折叠），开发模式 `?dev=1` 全量并逐条标记 | 否（已落地） |

---

## 5. 设计方向（🟡 **①②④ 已落地；③⑤⑥⑦ 待定**）

### 5.1 落地链路（五步）—— 批次 7.2 落地状态

```text
算法建议（全部，平级）
  ↓ ① 技术过滤：能落地才进候选（现状即如此）
  ↓ ② 准入过滤：场景白名单 —— 不在白名单 ⇒ 让位，理由「本场景不允许」   ← ✅ 已落地
  ↓ ③ 次序裁决：优先级 + 名额 + 目标已达成                                    ← ✅ 已落地（名额来自策略清单；✅ 12.3 起已生效）
  ↓ ④ 执行保留项：MEL 先收集（它是「标」）                                  ← ✅ 已落地（含 fill_ratio 目标）
  ↓ ⑤ L3 传导：MEL ⇒ ML_N ⇒ MEL
```

### 5.2 三层次序

| 层 | 键 | 例子 | 来源 | 批次 7.2 状态 |
|---|---|---|---|---|
| 方向级 | 触发方向 | 充填 / 其它缺陷方向 | 规则 → 方向的映射（待定） | 🟡 简化版（场景优先集） |
| 参数组级 | 参数组 | 注射 / 保压 / 模温 / 计量 / 回抽 | **业务字段名机械推导** ✓ | ❌ 未做 |
| 字段级 | 单字段 | `inj_spd_1` … | 优先级表（数据） | ✅ 已落地 |

⇒ **建议做两级排序（组 → 字段），不要把组压成一个数字** ⇒ 现有 `group` 字段正好可以升级为「参与排序的第一级」。
⚠️ **本轮按旧版机制**：旧版只有「充填优先把 `MEL` 置顶」这一个特例 ⇒ 只落**方向级的简化版**
（场景 `preferred_params`），组级排序留到反馈证明需要时再做。

### 5.3 让位语义：排序式 → 条件式

| | 排序式让位 | **条件式让位**（更贴近「先充填打满」的意图） |
|---|---|---|
| 判据 | 排在第 2 ⇒ 本轮先不做 | 先做高优先项 ⇒ **推进后校验低优先项的前提是否还成立** |
| 静态 / 动态 | 静态 | 动态 |
| 留痕能答 | 「它排在后面」 | 「**它要解决的问题已经被解决了**」 |

⇒ 三类让位理由要分开：**目标已达成** / **本场景不允许** / **名额已满**。
（批次 7.2：三类理由**已可分辨** —— 但「目标已达成」这一路因派生量表未就位，
仍恒不触发；实际生效的是「本场景不允许」与「名额已满」。）

### 5.4 留痕要带依据 ✅（批次 7.2 已落地）

`PriorityEntry.reason` 只在**让位**时被消费（`table.reason_of(...) or '目标已达成'`）⇒
**保留项为什么排前面没有记录** ⇒ 而没有依据，feedback 无法证伪「次序」。

⇒ 留痕载荷应至少含：`kept`（含各自依据）/ `yielded`（含理由）/ `deferred`（含理由）/ `order`。

**落点**：`StrategyDecision.kept_reasons`（字段名 → 依据）+ `to_trace()` 增列
`kept_reasons` / `scenario_code`；依据来源优先级 = 场景优先集 ⇒ 优先级表字段依据
⇒ 「场景允许」。

### 5.5 feedback 的定位：**事后证伪**，不是事中门控

⚠️ L2 裁决时**不能**直接依赖 feedback —— 它稀疏、滞后、首轮没有 ⇒ 用它当门控会让绝大多数轮次无法裁决。

```text
L2 留痕（用了哪条经验 / 谁让位 / 为什么）
    + 落库参数集（这一轮实际调了什么）
    + 调机反馈（调完的效果）
    ────────────────────────────────────
    ⇒ 同一轮次对齐（轮次 id）⇒ 这条经验这次成立吗？
```

⇒ 前两环现成：**调机轮次的「参数-反馈配对」已在落**；L2 留痕也有 `kept/yielded/deferred/order`（**依据已补**，见 §5.4）。

---

## 6. 拍板清单（**①②④ 已按「先照旧版机制实现」拍板并落地**）

> 用户原话（2026-11-12）：「我觉得可以先按照旧版的机制实现，然后我们再看怎么调整，
> 目前我们不是已经分层了吗？旧版代码都是冗杂在一起的，起码我们已经前进了一步。」
>
> ⇒ **拍板口径**：**机制照旧版**，但**落点必须在已建的分层里**（L1/L2/L3），
> 不退回旧版「if-else 混在 service」的冗杂写法；**业务知识落数据**（§7.0 红线）——
> **逻辑（解释规则的方式）固定，规则（知识本体）可增长** ⇒ 物理算式可落代码（L3 侧），
> 触发条件必须落数据。

| # | 待拍 | 状态 |
|---|---|---|
| **①** | **准入的默认语义**：默认全允许 + 显式收紧／默认全禁止 + 显式允许 | ✅ **已拍板：默认全允许 + 显式收紧**（`allowed_params` 空 = 不限制；漏配退化为「没筛选」，不挡掉必要调整）⇒ `ScenarioStrategy.allowed_params` |
| **②** | **「本场景不允许」的存储形态**：复用规则表加一列／独立策略表／**文件清单** | ✅ **已定：文件清单**（批次 11，原「独立策略表」已撤回 ⇒ §6.2）⇒ `algorithms/strategies.py`（场景 + 条件 + 准入 + 优先集 + 名额 + 目标口径 + 字段级优先级表） |
| ③ | 次序要几层：方向级 + 参数组级 + 字段级三层／先落组级 + 字段级两层 | 🟡 **部分落地**：本轮按旧版机制 ⇒ 只落**场景优先集（方向级简化版）+ 字段级**；**组级未做**（旧版无此需求）；⚠️ **批次 13.0**：场景优先集已能表达**组级次序**（`filling_stage_first` 把「胶量端 → 保压 → 熔体侧 → 料筒温度」写在优先集里）⇒ **组级实际可用**，但仍**没有独立的组级配置层** |
| ④ | 方向 / 场景的数据来源：规则库关键词／独立策略表／**文件清单**／手工配置 | ✅ **已定：文件清单**（同 ②，批次 11）；⚠️ **清单当前为空** ⇒ 待阶段口径（§6 表 ⑧）定后填充 |
| **⑤** | 条件式让位的「前提」怎么算 | ⏳ **待定**（依赖派生输入量表 §7.0）；⚠️ **2026-11-16 核实**：拿「阶段达成信号」当前提，在现有架构下**恒不触发**（§3.5）⇒ 需另定判据（阶段准入 / 参数×缺陷派生量表） |
| ⑥ | 被让位 / 暂缓的建议要不要在响应里标出 | ✅ **已定**（2026-11-16 批次 12.9，用户拍板）：**标出、不删条目** —— 每条建议带 `decision_status` + `decision_reason`；前端**默认只显示已落地**（未采用项折叠展开），开发模式 `?dev=1` 全量并逐条标记 |
| ⑦ | feedback 的对齐口径与评估节奏（离线？周期性？多久回看一次） | ⏳ **待定**（依据字段已补，见 §5.4 ⇒ 具备回看条件了） |
| ⑧ | **调机按什么组织**：一次性裁决／按**阶段**推进（打足 → 补缩 → 外观） | ✅ **口径已定**（2026-11-12 拍板 A–G）⇒ `docs/l2-stage-strategy-design.md`：阶段 = **缺陷族**（打足 / 补缩 / 外观，覆盖 17 类缺陷码）；**状态不落库、每轮从反馈推导**；阶段表是 `defect_selection` 与 `strategies` **共同数据源**（前者**排**、后者**查**）；「基线项」= `allowed_params` 补集；条件改引用**任意键**（新增 `in_set` 运算子）；⚠️ **2026-11-13 口径修正：L2 不重选缺陷**（L2 输入 = 规则 + 已确定的缺陷信息） |

### 6.1 旧版机制 → 新版落点（本轮实现的对照表）

| 旧版机制 | 旧版位置 | 新版落点 | 形态 |
|---|---|---|---|
| 一轮只调一个量 | `process_optimize_service.py:832-836` | L2 场景名额 `max_items`（`default_one_adjust`） | 机制已有，接上 |
| 谁排第一 | 旧版激活度降序 | L1 候选顺序≈激活度降序（`nets.py:1060`） | 无需新造 |
| 充填优先（`MEL` 置顶） | `process_optimize_service.py:666-673` | L2 场景优先集 `preferred_params` | **数据**（策略清单文件） |
| 按重量比例重算行程 | `process_optimize_service.py:915-926` | L3 充填量目标求解器 `resolve_fill_target` | **算式落代码、触发条件落数据** |

⚠️ **旧版两处共享同一触发条件**（`target_defect == "SHORTSHOT" and actual_product_weight < product_weight`）
⇒ 新版合并为**一个场景** `filling_first`（既置顶又用重量比解算）。
⚠️ **旧版「把 `MEL` 提首位」≠「只允许 `MEL`」** ⇒ 新版用 `preferred_params` + `max_items=1`，
**不收紧准入**（`allowed_params` 留空）。
⚠️ **物理口径**：充填量 ∝ 制品重量 ∝ 注射行程 ⇒ `目标行程 = 当前行程 × (目标重量/实测重量)`；
`ML_N 目标 = VPTL + 目标行程`；`DDAM` 是螺杆回抽量，**不参与**注射量计算。

### 6.2 批次 11：撤回策略表 → 策略清单文件（用户反馈驱动的形态修正）

**触发**：用户指出「你这个策略模型，好像根本没法维护」—— 规则若写成人看不懂的形式，**没人能维护**。

**撤回理由**：

| # | 理由 | 事实依据 |
|---|---|---|
| ① | **动作被固化成模型字段的枚举** ⇒ 每加一条经验都要改 DDL | `target_mode = CharField(choices=[delta, fill_ratio])`；要新增「幅度按缺陷程度缩放」就得改 model + migration |
| ② | **条件字段集写死在代码里** ⇒ 表达不了「缺陷程度」「上一模反馈」 | `CONTEXT_FIELDS = (defect_codes, actual_weight, target_weight, fill_gap)` |
| ③ | **没有管理界面** ⇒ 「落表免发版」的收益为零 | 改一条策略仍要改代码 + 跑命令；表里的 JSON 是**第二门语言**（IDE 不认、无法评审） |
| ④ | **项目里已有两套规则体系** ⇒ 新建第三套是最弱的重复 | ①`expert/macros.py`（经验用带中文注释的常量写）②`models/rules.py` 的 `RuleLibrary`/`ExpertRule`（DB + conditions JSON + priority + 归属隔离） |

**撤回内容**（含从未执行的 migration ⇒ 零迁移成本）：

- `process/models/strategy.py`（`StrategyPolicy` + `StrategyPriorityEntry`）
- `process/migrations/0019_strategy_policy.py`（**从未执行** ⇒ 无回滚负担）
- `process/management/commands/init_strategy_policies.py`（种子命令）
- `services/policies.py` 的读表逻辑 ⇒ 改为读**文件**

**新载体**：`process/algorithms/strategies.py`（**代码即规则**）

| | 表版（撤回） | 清单版（现行） |
|---|---|---|
| 规则语言 | JSON（第二门语言） | Python（唯一一门语言） |
| 改一条经验 | 改数据 + 发版 | 改文件 + 发版（**可评审、可 diff、可测**） |
| 表结构 | 加一种动作 ⇒ 改 DDL | **永不变**（新增经验 = 清单加一条） |
| 租户私有策略 | 有归属隔离 | **暂无**（待真实需求出现再建表） |

**同时改的算法层形态**：`ScenarioPolicy` 去掉 `policy_id`（表主键）与 `owner_rank`（租户归属排序），
改为自带 `priority_table`（字段级优先级随场景一起来，取代原子表）。

⚠️ **清单当前为空** ⇒ 第2层不裁决 ⇒ **行为零变化**（pytest 80 passed）。

⚠️ **下一轮主题（§6 表 ⑧）**：调机应按**阶段**组织 —— 用户口径：
「先把产品打到差不多（注射行程）→ 再补缩（保压）→ 最后针对性处理外观缺陷」，
每阶段关注点不同；**注射速度属基线取值，不进阶段调机**。
⇒ 待拍板：阶段定义（进入条件／动作／达成条件）、阶段状态存哪、「基线项」怎么表达。

---

## 7. 术语纠正记录（避免下一轮再犯）

| 我曾用的说法 | 正确说法 | 来源 |
|---|---|---|
| 「缺陷归属」 | **触发源**（`source` / `matched_rules`）；缺陷在规则库侧是关键词 | 用户纠正 |
| 「用旧 DDAM 还是新 DDAM」的二选一 | **伪问题** —— L3 只有旧值 + 调整量，没有「新值」 | 用户纠正 |
| 提「二选一」方案 | 先核对**该选项在该层是否成立**；不成立就别拿去拍板 | 教训（已入记忆） |

---

## 8. 下一轮接续点

1. 先读本文 + `docs/strategy-consistency-layer-plan.md`（§8.4.1 锚点口径、§8.4.3 第2层接线位置、§10 批次表）；
2. **形态按反馈迭代**：批次 7.2 已把「旧版机制」完整落成分层实现 ⇒ 下一轮看**实际反馈**
   再决定要不要加组级次序 / 通用方向映射 / 条件式让位（§6 ③⑤）；
3. **不要重做批次 7.1 / 7.2 / 9**（pytest **80 passed**）；
4. §6 ⑤⑥ 未拍板前**不要动代码**（⑥ 动响应契约 ⇒ 需用户点头）；
5. ⚠️ **待办（随批次 11 作废）**：策略表迁移 + 种子数据 —— 策略表已撤回，
   载体改为 `backend/process/algorithms/strategies.py`；**清单当前为空 ⇒ 不裁决 ⇒ 行为零变化**
   （⚠️ 此为**批次 11 当时**的状态；清单自批次 12.3 起已有内容，见本文 §8 第 8 条）；
6. **专业知识参考已就位**：`backend/process/references/`
   （`README.md` + `01-troubleshooting-methodology.md` + `02-defect-playbook.md`
   + `03-glossary-and-field-mapping.md`，源自《Injection Molding Advanced Troubleshooting Guide》）。
   讨论 §6 表 ⑧（阶段化调机）前先读：
   - `01`：**STOP 循环**（调机是循环不是直线）、**硬修 vs 绕过问题**（processing around）、
     **调整纪律**（一次只改一个量）、**验收四问**；
   - `02`：**短射**（充填优先）/ **缩水**（保压优先，锚点是浇口封冻）/ **成型周期**（速度取大值但不得掩盖烧焦）；
   - `03`：**术语 ↔ 项目字段**映射（含差距 G1–G9，G1 = 模温在优化链路不可调）。
7. **缺陷调整规则文档已出**：`backend/process/references/04-defect-adjustment-rules.md`（Draft）——
   把书本的缺陷优化策略整理成结构化规则（通用纪律 `U-01`~`U-08` + 短射/缩水/飞边/烧焦/周期），
   含**旋钮优先级**（充填量：先 `met_end_pos`，MEL 偏大后 `vps_pos`）与**落地清单**
   （🟢 可直接落 / 🟡 待校准 / 🔵 需先补字段）。
   策略清单落 `filling_first` 时，参数口径与理由可直接引该文档的 SS-01。
8. **阶段化调机方案已成稿**：`docs/l2-stage-strategy-design.md` —— §6 表 ⑧ 的专题设计。
   核心结论：阶段 = **缺陷族**（打足 / 补缩 / 外观，覆盖 17 类缺陷码）；
   **阶段状态不落库**（每轮从反馈推导 ⇒ 幂等、自愈）；
   阶段优先级表是 `defect_selection` 与 `strategies` **共同的数据源**（前者**排**、后者**查**）；
   ⚠️ **2026-11-13 口径修正 2**：「基线项」**不靠白名单排挤**，而用独立的**禁入清单**
   （`blocked_params`）—— 白名单 = 场景范围，禁入清单 = 全局基线项（两者分开，见 §8 第 8 条）。
   ⚠️ **2026-11-13 口径修正**：**L2 不重选缺陷** —— L2 的输入是「规则」+「**已确定的**缺陷信息」，
   第2层不选取、不重排；「选哪个缺陷」属 **L1 侧**（`defect_selection`，各引擎调用点不变）。
   ⇒ L2 只做：**查阶段 → 命中策略 → 调什么 / 次序 / 调几个**。
   **拍板 A–G 见该文档 §10**；落地批次见 §11。
   ⚠️ **批次 12.1 已落地**（2026-11-12）：新增 `algorithms/stage_order.py` +
   `defect_selection.py` 的 `StagePriorityDefectStrategy`（**只加能力、未接线**，
   `DEFAULT_STRATEGY` 未动）⇒ pytest **135 passed**，行为零变化。
   （⚠️ **批次 12.7 起该策略已接线**为 `DEFAULT_STRATEGY`。）
   ⚠️ **批次 12.2 已落地**（2026-11-13）：`ScenarioContext` 加 `extra` 通道
   （条件可引用**任意键**，未知键 ⇒ 不命中）+ `_compare` 新增 `in_set` / `not_in_set`
   （单值 ∈ 集合；原 `in` = 目标 ⊆ 字段值，方向不变）⇒ pytest **135 passed**，行为零变化。
   ⚠️ **当前 pytest 基线是 135 passed**（本文上文出现的 80 / 62 是历史批次的当时值，勿改）。
   ⚠️ **批次 12.3 已落地**（2026-11-13）：策略清单 `algorithms/strategies.py` 落 2 条 ——
   S1 `filling_first`（短射 + 重量缺口 ⇒ 只动 `met_end_pos`、一次一个、`fill_ratio` 解算行程）
   + 兜底 `default_one_adjust`（`conditions=()` 恒命中、`max_items=1` ⇒ 兼容旧版「一轮只调一个量」）。
   ⇒ **L2 开始真正裁决输出**（第一批改变最终落地结果的经验）。
   ⚠️ **名额是场景级参数**：`max_items=None` = 不限 ⇒ **多参数出口现成**，
   将来某场景不写 `max_items` 即多参数 ⇒ **兼容旧版与多参数不是二选一**。
   ⚠️ **口径修正（2026-11-13 → 2026-11-16 再修）**：**L2 不重选缺陷** —— L2 输入 = 规则 + 已确定的缺陷信息；
   场景条件引用**本轮实际处理的缺陷码**（`selected_defect` + `in_set`），
   **不按全部缺陷码**（`defect_codes`）。
   ⚠️ **批次 12.4a 已落地**（2026-11-13）：清单扩到 **6 条**（S2 `shrinking_first`
   + S3 三条 `flash_first` / `burn_first` / `gasveins_first`，对齐拍板 G）+ **两类“不可调”机制**：
   ① `decide_direction.py` 加 `blocked_params`（禁入清单）与新运算子 `in_any`
   （**字段值是集合** ⇒ 任一元素 ∈ 目标集合；与 `in_set`（单值 ∈ 集合）**方向相反**，并存不混）；
   ② `strategies.py` 加 `BASELINE_EXCLUDED_PARAMS`（注射速度 6 项 = 基线项）。
   ⚠️ **裁决序改为「禁入先于准入」** ⇒ 同时命中两者时留痕写“基线项”（全局理由更强）。
   ⇒ pytest **135 passed**；一次性核对 **41 项全过**（脚本已删）。
   ✅ **批次 12.6a / 12.6b / 12.6c 已落地**（2026-11-16）—— **缺陷选取单一入口**：
   ① **12.6a**：service 预处理层新增「缺陷整理」，调一次 `select_defect`，
   结果经 `DefectSelection.to_context()` 随 context 的 `selected_defect` 下传；
   ② **12.6b**：`fuzzy` / `empirical` 改为**只读载荷**，不再各自 `select_defect`
   （原 12.4b ① 的阶段序接线**已撤回** —— 选取只做一次、在预处理层；
   当时规则 = **「只选第一条」**，`stage_priority` 降级为未接线的候选规则；
   ⚠️ **该状态已由 12.7 终结** —— 撤回理由里的「选取散落」被 12.6 消除）；
   ③ **12.6c**：5 条场景条件改引用 `selected_defect`，`resolve_policies` 调用点挪进
   `_infer_kernel` ⇒ **L1 与 L2 同一份口径** ⇒ §8 前提 ⑦ **闭环**。
   ⇒ pytest **135 passed**；场景判定核对 4 项全过（含「旧口径实证会错配」的对照）。

   ⚠️ **现状更新（2026-11-19）** —— 缺陷选取的**载体**已改（**判定口径不变**）：
   ① `select_defect` 成为**唯一入口**，入参 = feedback，返回**收敛后的 feedback**
      （`defects` 只剩本轮处理的那条 + `defect_selection` 留痕）；
   ② `DefectSelection.to_context()` 与 `ensure_selected_defect(context)` **已删除**；
      context 顶层键 `selected_defect` **已移除**；
   ③ `resolve_policies` 的 `selected_defect` 参数**已删**（改为从收敛后的
      `defects[0]` 自行取）。
   ⇒ 上文「随 context 的 `selected_defect` 下传」是**当时形态**；
      「**不按全部缺陷码**（`defect_codes`）」的论证也已随收敛失效
      （`defect_codes` 现在只含本轮处理的那条 ⇒ 与 `selected_defect` 同源）。

   ✅ **批次 12.5 已落地**（2026-11-16）—— **阶段达成信号 + 留痕**（**只观测，不裁决**）：
   ① `algorithms/stage_order.py` 新增 `derive_stage_progress()` + `StageProgress`
   （达成 = 该阶段的缺陷码在本轮反馈中**全部消失**；**纯推导、不落库**，每轮重算）；
   ② `services/policies.py` 把 `current_stage` 注入 `ScenarioContext.extra`
   （场景条件**可以**引用，但**当前无场景引用** ⇒ 行为零变化）+
   `PolicyResolution.stage_progress` 进留痕；
   ③ `services/parameter_optimize.py` 落一条阶段进度日志。
   ⇒ pytest **135 passed**；核对 20 项全过；黄金快照差异数不变（仍为 6，历史遗留）。
   ⚠️ **条件式让位（§4 ⑤）仍未落地** —— 12.5 核实「拿阶段达成信号当前提」在现有架构下
   **恒不触发**（§3.5）⇒ 该批只落地可观测的阶段信号，**不接让位**。

   ✅ **condition chain 断链已修**（2026-11-16）—— 两处根因：
   ① `condition.py::_build_optimization_context` 的缺陷项**只有** `defect_name`，
   **没有 `keyword_name`** ⇒ 缺陷选取（有效性判据 = 有非空 `keyword_name`）**一直落空**
   ⇒ 引擎拿不到缺陷类型 ⇒ chain 必然抛 `BizException(OPERATION_FAILED)`；
   ② `condition.py::DEFECT_NAME_MAP` 的 **11 条译名与规则库脱节**
   （缩水→`SINK_MARK`、气纹→`FLOW_MARK`、困气→`TRAP`…；规则库 17 类里**不存在**这些码）
   ⇒ 即使选中缺陷也查不到规则。
   ⇒ 修复：补 `keyword_name` + 译名表对齐 `RuleKeyword.keyword_name`
   （中文名逐条取自规则库条目的 `description`；「色差」规则库无此类 ⇒ 保留原名）。
   ⇒ **行为变化（修复，非回归）**：condition chain 由「必然抛异常」变为「能出推荐」——
   端到端离线实测：chain 式 context（无 level/position）⇒ 选中 `SHRINKAGE` ⇒
   命中真实规则库 93 条规则 ⇒ 产出推荐 `IV0 decrease → 87.3`。

   ✅ **批次 12.7 已落地**（2026-11-16）—— **多缺陷选取接阶段序**：
   ① `algorithms/defect_selection.py` 的 `DEFAULT_STRATEGY` 由 `FirstValidDefectStrategy`
   改为 `StagePriorityDefectStrategy`（`FIRST_VALID_STRATEGY` 保留为历史口径/回退开关）；
   ② `services/parameter_optimize.py` 预处理层落一条 `[optimize] … 缺陷选取` 日志。
   ⇒ **为何现在能接**：12.6b 撤回阶段序的理由是「选取散落在两个引擎里」——
   该理由在 12.6 把选取上移到 service 预处理层（**唯一入口**）后**已消除**；
   剩下的「换一套规则」正是用户口径要的（「结合入参进行分析」，
   例：短射+缩水⇒先短射；缩水+飞边⇒先缩水）。
   ⇒ pytest **135 passed**；核对 **18 项全过**；黄金快照差异数不变（仍为 6，历史遗留）。
   ⚠️ **行为变化**：多缺陷反馈下选中项**可能不是列表第一条** ⇒
   L1 推理对象 + L2 命中场景随之变（已留痕：`selection.to_trace()`）。
   ⚠️ **现状更新（2026-11-19）**：`FirstValidDefectStrategy` /
   `FIRST_VALID_STRATEGY` / 策略 Protocol / `select_defect` 的 `strategy` 形参 ——
   **全部删除**（占位口径 + 用不到的切换机制，按「用不到就不写代码」原则不留空壳）。
   ⚠️ **现状更新（2026-11-19，纯改名 + 合并）**：调机策略全套（**阶段表 + 场景清单**）
   合并为 **`algorithms/tuning_strategy.py`** —— 阶段表与场景规则是同一张表的两端
   （场景清单按 S1/S2/S3 分区，恰好对应三个阶段）。曾用名：
   `algorithms/stage_order.py`（阶段表）、`algorithms/strategies.py`（场景清单）。
   符号改名：`stage_of` → `stage_of_defect`、`stage_rank` → `rank_of_stage`、
   `order_defects` → `sort_defects_by_stage`、`DEFECT_STAGE` → `DEFECT_STAGE_MAP`、
   `STRATEGIES` → `SCENARIO_POLICIES`、`load_strategies()` →
   `sorted_scenario_policies()`、`BASELINE_EXCLUDED_PARAMS` → `BASELINE_BLOCKED_PARAMS`
   ⇒ 行为零变化；上文纪实里的旧名是**当时形态**。

   ✅ **批次 12.8 已落地**（2026-11-16）—— **修「一屏建议、参数没动」**（用户报 bug）：
   ① **根因：L2 与 L3 的规则打架** —— L2 的**禁入清单**排除 `inj_spd_1`（基线项），
   而 L3 的 **G3 让位规则**要求「改 `inj_t` ⇒ 让位给 `inj_spd_1`」；
   L3 的让位是**值回退**（改了也不生效）⇒ 只要 L2 选中 `inj_t`，
   必被静默回退 ⇒ **整轮零变化**（新建一个与父轮一模一样的轮次）。
   兜底场景 `default_one_adjust` 的候选序 = 算法输出原序 ⇒ `inj_t` 正好占掉
   `max_items=1` 的唯一名额 ⇒ 后面的候选（`hold_spd_1` 等）根本没机会。
   ② **修法（A：L2 排除不可落地候选项）** —— 让位关系**下沉到底座**：
   `algorithms/anchors.py` 新增 `FREEDOM_YIELDS`（`inj_t → inj_spd_1`）+ `unlandable_params()`
   （判据 = 让位对象**既在禁入清单**里**又**在 baseline 里可调）；
   L3 的 `FREEDOM_OVERRIDES` 改为引用底座（**只定义一次**，两层不各持一份真相）；
   L2 的 `resolve_priority` 新增第 4 类让位理由「**本轮落不了地**」
   （排在 allowed 之后、satisfied 之前）⇒ 名额**顺延**到下一个候选；
   `parameter_optimize.py` 加**零落地守卫**：L2 有保留项但落地后无任何数值变化 ⇒
   明确抛 `BizException(ERROR_OPERATION_FAILED)`，不再静默产出「与上一轮一样」的新轮次。
   ③ **效果**：兜底场景由「`inj_t` 被静默回退（零变化）」变为
   「`inj_t` 让位（留痕理由：本轮落不了地（让位对象 `inj_spd_1` 不可调）⇒ 让位）
   ⇒ **`hold_spd_1` 6 → 9.69 真正落地**」；
   `filling_first` 路径行为**不变**（`met_pos_1` 118.35→123.85 + 派生 `met_end_pos`→127.49）。
   ④ **回归**：pytest **135 passed**；三离线脚本 e2=0 / algo=0 / nested=0；
   黄金快照差异数**仍为 6**（未新增，历史遗留）。
   ⚠️ **本批次明确不修**：展示层与落地不一致（§4 ⑦ / §6 ⑥）—— 前端仍会显示
   被让位 / 暂缓的建议（6 条建议 vs 1 条落地），**属另一形态**，需用户另行点头。
   ⚠️ **遗留（既有失效脚本，非本批引入）**：`backend/tests/verify_provided_smoke.py`
   仍断言 `inj_pres_2 == 70.0`，但 12.3 起 `max_items=1` 生效 ⇒ 该项已被暂缓
   （实际 55.0）⇒ 脚本自 12.3 起即失败。

   ✅ **批次 12.9 已落地**（2026-11-16）—— **建议带裁决状态**（§6 ⑥ 拍板落地）：
   ① **后端**：第2层的裁决结果**逐条回填到建议**——
   `StrategyDecision.status_of()`（新增）给出 `(状态, 原因)`，
   状态三取值 `adopted`（本轮保留并执行）/ `yielded`（让位）/ `deferred`（暂缓）；
   `parameter_optimize._apply_decision_status()` **就地**回填到每条建议
   ⇒ 同一批 dict 既是响应载荷又是**落库载荷**（`Recommendation.recommendations`）
   ⇒ **当轮响应 / 落库 / 历史轮次回显**三处自动一致（**不改落库结构**）。
   已采用项另带 `applied_value`（**实际落地值**：当轮 = 整合后参数集，
   历史回显 = 该轮落库参数 ⇒ 两者同源）。
   ② **前端**：默认视图**只显示已落地**（未采用项折叠在「另有 N 条建议本轮未采用」里），
   已采用项标「已应用」；开发模式（**`?dev=1`**）全量展示并逐条标状态
   （未采用置灰 + 原因进 `title`）。
   ⚠️ **无状态即旧数据**：状态字段是 12.9 才加的 ⇒ 历史轮次没有状态
   ⇒ 前端按「有状态才过滤」处理，旧轮次照常显示。
   ③ **实测**（用户那组 6 条建议，兜底场景）：`inj_spd_2` / `inj_spd_1` = **yielded**
   （基线项）、`inj_t` = **yielded**（本轮落不了地）、`hold_spd_1` = **adopted**
   （`applied_value=9.69`）、`met_back_pres_1` / `met_end_pos` = **deferred**（名额已满）
   ⇒ adopted=1 / not_adopted=5。
   ④ **回归**：pytest **135 passed**；三离线脚本 e2=0 / algo=0 / nested=0；
   黄金快照差异**仍为 6**（未新增，历史遗留）；前端 `vue-tsc` 类型检查通过。
   ⚠️ **采用判据（用户拍板）** = **L2 保留即已采用**（不要求「数值一定变了」）；
   MEL 翻译等特殊情形由 `applied_value` 体现实际落地值。

   ✅ **批次 13.0 已落地**（2026-11-16）—— **「打足阶段优先」场景**（次序能力首次生效）：
   **用户现场报的现象**：短射轮次落地的是「一段料筒温度 270 → 271」
   （依据 `IF SHORTSHOT_low THEN BT1_add_1`）⇒ **打足阶段却调了熔体黏度的间接旋钮**。

   ⚠️ **先澄清一点**：L2 **裁决生效了**（留痕：`kept=['brl_temp_1']`、
   `yielded` 3 条、`deferred` 3 条、`max_items=1`）——
   **缺的不是「裁决」，是「定次序」**：兜底场景**没有优先集**
   ⇒ `resolve_priority` 的排序键退化为**原序**
   ⇒ 次序**完全继承 L1 的输出序**（= 规则库遍历序，`aggregate()` 用 dict 保序）
   ⇒ 恰好 BT1 的规则排在最前 ⇒ 料筒温度上位。

   ⚠️ **四层根因**（逐层有据）：
   ① 兜底场景 `default_one_adjust` 的 `preferred_params=()`、`priority_table={}`
   ⇒ 排序键退化（原序）；
   ② L1 输出序 = **规则库遍历序**（`fuzzy/recommendations.py::aggregate` 用 dict 保序）；
   ③ 短射**没走**「充填优先」：`filling_first` 的条件含 `fill_gap > 0`，
   而本次反馈**没填「实测制品重量」** ⇒ `actual_weight=None` ⇒ `fill_gap=None`
   ⇒ 不命中 ⇒ 掉进兜底（`filling_first` 里**本来就有**胶量端优先的优先集，
   **正因为没命中而整份浪费**）；
   ④ **根子**：阶段进度**已经算出**「还在打足」（`current='filling'`），
   且 `current_stage` **已注入 `ScenarioContext.extra`、场景条件可引用**——
   但**没有任何场景引用它**（源码注释自认「阶段准入尚未落地」）
   ⇒ **最强的信号被丢弃**。

   ① **修法**（用户拍板：**新增「打足阶段优先」场景**，只改策略清单数据、不改架构）：
   `algorithms/strategies.py` 新增 `filling_stage_first`（`priority=15`）：
   - **条件**：`selected_defect in {SHORTSHOT}` + **`current_stage == 'filling'`**
   （**不依赖重量数据** —— 阶段由缺陷码推导）；
   - **白名单**：胶量端（`met_end_pos` / `vps_pos`）+ 注射时间 `inj_t`
   + 注射压力 `inj_pres_1/2` + 保压组 + 熔体侧 + 料筒温度组
   （⚠️ 含 `inj_pres_1/2`：规则库实测短射类会产出（4 条 / 1 条）
   ⇒ 不放进白名单会有「本场景无输出」风险；
   ⚠️ 含 `inj_t`：**不在白名单会让位理由被「本场景不允许」掩盖** ⇒ 反而看不出 G3 规则在工作）；
   - **优先集**（用户拍板）：**胶量端 → 保压 → 背压 → 料筒温度**
   ⇒ 白名单成员**在优先集里的先后 = 调整次序**；
   - **`priority=15`** ⇒ 排在 `filling_first`(10) **之后**
   ⇒ **有重量数据时仍走 `filling_first`**（按重量比例解算行程），
   本条**只在「拿不到重量口径」时接管** ⇒ 两个场景互不覆盖；
   - **`target_mode='delta'`**（默认）：无重量口径 ⇒ 不能按比例解算行程。
   ② **效果**（用户那组候选，实测）：
   `kept` 由 `brl_temp_1` 改为 **`met_end_pos`（胶量端）**
   ⇒ **MEL 增量口径**落地 `met_pos_1` 300.0 → **303.0**；
   `brl_temp_1` 降为「**本轮名额已满 ⇒ 暂缓**」；
   `inj_t` 仍为「本轮落不了地（让位对象 `inj_spd_1` 不可调）⇒ 让位」（**G3 仍可见**）；
   `inj_spd_1/2` 仍为「基线项 ⇒ 不参与阶段调机」。
   ③ **回归**：pytest **135 passed**；三离线脚本 e2=0 / algo=0 / nested=0；
   黄金快照差异**仍为 6**（未新增，历史遗留）。
   ④ **顺带清理**：三处「阶段准入尚未落地」的过时注释
   （`stage_order.py` / `services/policies.py` / `services/parameter_optimize.py`）
   ⇒ 改为「阶段进度已被 `filling_stage_first` 引用」。
   ⚠️ **本批次明确不修**：**G3 让位规则把 `inj_t` 彻底废了** ——
   `inj_t` 让位给 `inj_spd_1`，而 `inj_spd_1` 属基线项禁入 ⇒ **`inj_t` 永远调不了**。
   这符合 G3 原意（注射阶段是速度控制，设定时间只是设定值），
   但意味着短射少了一个强力旋钮 ⇒ **需用户另行拍板**。

✅ **批次 14.0 已落地**（2026-11-20）—— **「改成多少」归第3层**（第2层不再求落地值）：
   **用户指出的问题**：第2层耦合参数 —— 「我现在的场景就是天黑的情况，所以第2层应该只考虑
   规则信息，我不认为需要和参数有关联；参数怎么落地是第三层的工作」。
   ⇒ **与本文 §1 的分层定位对齐**：第2层「**不重算数值**」、第3层「MEL 目标 ⇒ 计量位置」——
   **代码此前偏离了文档**（MEL 翻译落在第2层），本批次把实现拉回文档口径。

   ① **第2层（`decide_direction.py`）回归纯筛选**：
      - `resolve_direction()` **去掉 `baseline` 入参**（不再读现状参数集）；
      - 删掉 MEL 翻译块（`apply_mel_targets` / `resolve_fill_target` 的调用）；
      - `Direction` 契约改为：`decisions`（**非派生量**的绝对值）+ `mel_targets`
        （MEL 目标值，**未翻算**）+ `target_mode`（口径：`'fill_ratio'` / `'delta'`）；
      - 删掉 `Direction.fill_target`（第2层不再解算充填量目标）。
   ② **第3层（`integrate_params.py`）接管落地值**：
      - `apply_direction()` 新增 `fill_weights`（目标重量, 实测重量）入参；
      - 按 `direction.target_mode` 换算：`'fill_ratio'` ⇒ 按重量比例解算行程
        （解不出来 ⇒ **回落增量口径**）；其它 ⇒ 旧 MEL + ΔMEL；
      - `IntegratedParams` 新增 `fill_target` 字段（充填量目标随留痕）。
   ③ **底座（`anchors.py`）**：`apply_mel_targets()` 从第2层**下沉到底座**
      （与 `resolve_mel_target` 同居 ⇒ 物理换算只有一处）。
   ④ **编排层（`services/parameter_optimize.py`）**：第2层分节标题**上移**
      （此前「策略数据」那段落在第1层分节里 ⇒ 读代码会误判归属）；新增 `_fill_weights(context)`。
   ⇒ **行为零变化**：同一套公式、同一个旧值基线 ⇒ 落地值与顺序完全一致
     （**A/B 对拍 8 个用例逐条差异 = 0**：增量口径 / 比例口径 / 缺重量回落 / MEL 让位 /
     多候选 / 纯非派生量）；pytest **117 passed**；`verify_provided_smoke.py` PASSED。
   ⚠️ **第2层仍读参数的两处**（**筛选依据**，不是落地计算）：
      - **候选准入**：基线里没有这个字段 ⇒ 无处可落 ⇒ 不进候选；
      - **让位预筛**：只有当前有值的旋钮才算「可调」（批次 12.8 的明确要求）。
      ⇒ ⚠️ **这两处已在批次 14.1 拿掉**（第2层不再碰参数）。
   ⚠️ **口径表述**（本文 §1 表第2层「不重算数值」）：`MEL` 这类**派生量**仍由第2层**裁决**
     （用不用它、什么口径），只是**换算**挪到第3层 ⇒ 「不重算」指不产出落地值。

✅ **批次 14.1 已落地**（2026-11-20）—— **第2层不掺合参数**（第2层只筛规则）：

   **用户指出的问题**：我拿「规则是否可用」在第2层讨论了两轮（候选准入 / 让位预筛），
   用户纠正：「**参数是否合理，甚至规则是否能用，放在第三层校验即可**……
   第二层就是对规则的筛选，不应该糅合参数」⇒ 共识：
   **每一层的工作都要清晰，不互相糅合**；**不为单个字段在某一层加特例兜底**。

   ① **第2层（`decide_direction.py`）不再碰参数**：
      - `collect_candidates()` **去掉 `baseline` 入参**与「基线里没有 ⇒ 不进候选」的准入
        ⇒ 它只筛「**根本不算建议**」的条目（没推荐值 / 译不出业务字段名）；
      - `resolve_direction()` 已于批次 14.0 去掉 `baseline` ⇒ **本层入参只剩
        候选建议 + 实际情况 + 策略数据**；
      - 删掉 `services/parameter_optimize.py::_unlandable_veto()`（让位预筛：
        按「让位对象当前有没有值」预判白改）⇒ **第2层不再为单个字段做兜底**。
   ② **第3层（`integrate_params.py`）接管「规则是否可用」**：
      - `apply_direction()` 写入前校验字段是否在参数集里 ⇒ 不在 ⇒ **剔除 + 记入
        `IntegratedParams.unresolved` 留痕**（不写进参数集 ⇒ 落库不脏）；
      - 真正「一个量都没落地」时 ⇒ 由编排层既有的**零落地守卫**明确报错。
   ③ **底座**：`anchors.unlandable_params()` 保留（**物理判据**），口径改为
      「第2层已不再用它预判；供第3层 / 规则层在需要时引用」。
   ④ **编排层**：`parameter_optimize._decide_direction_by_strategy()` 去掉 `baseline` 入参；
      展示层过滤（`_build_suggestion_payload`）与第3层校验**同口径**。

   ⇒ **验证**：pytest **118 passed**（新增 1 条护栏：`test_layer2_does_not_check_parameter_existence`）；
     `verify_provided_smoke.py` PASSED —— `not_in_baseline` 那条建议**仍不进参数集**
     （现在是**第3层剔除 + 留痕**，可见而非静默）。

   ⚠️ **行为变化（1 处，需知悉）**：**兜底场景**（`default_one_adjust`）当候选首位是
   `inj_t` 时，由「第2层预筛 ⇒ 名额顺延给 `hold_spd_1` ⇒ 落地」变成
   「`inj_t` 占名额 ⇒ 第3层 G3 让位回退 ⇒ **零落地** ⇒ 零落地守卫报错
   （「本轮调整无法落地（让位回退：inj_t→inj_spd_1）」）」。
   ⇒ 这是「第2层不为单个字段做兜底」的**必然代价**（用户口径：
   「不管调不调 `inj_t`，我的系统都能运行……如果因为你这一个字段，
   我的第2层需要做这么多兜底的工作，这是不合理的」）。
   ⇒ **根治路径在规则/策略层**（`inj_t` 的替代规则，或 `inj_spd_1` 的禁入口径），
   **不在第2层** ⇒ 留作后续批次。

---

### 批次 14.2：回退第3层兜底 + 候选准入改为「是不是工艺量」（2026-11-20，已落地）

**用户追问**：「注塑机上肯定是有 `inj_t` 的，所以这部分我认为不可能存在第2步，
也不应该考虑兜底问题……采用兜底的操作，导致的结果就是掩饰错误，如果规则有误，
那理应修改规则，如果规则无误，比如说规则特意写一个 `add_xxxx`，那么我们应该
解析 `xxxx`，可能是同时调整 `inj_velo` + `inj_pres`」

⇒ 与批次 14.1 的结论**冲突**（14.1 把「规则是否可用」下放到第3层兜底）
⇒ 本批次**回退 14.1 的第3层兜底**，并把准入判据**从本机现状换成静态字段字典**。

**① 候选准入改为「是不是工艺量」（判据换源）**
   - 判据从 `baseline`（**本机现状**：这台机有没有这个字段/值）
     换成 **静态字段字典** `ProcessParameterSchema.model_fields`（**字段定义**）
     ⇒ **不依赖本机现状** ⇒ 第2层仍然不读参数集；
   - 后果：`IPOS` / `CUSION` / `not_in_baseline` 这类**不是工艺量**的名字
     ⇒ **不进候选**（源头挡住，不靠下游兜底）；
     而 **`inj_t` 这类「是工艺量、但本机没值」的照常进候选、照常落地**。

**② 第3层回退兜底**（`integrate_params.py::apply_direction`）
   - 删掉「字段不在 `values` ⇒ 剔除 + 记入 `unresolved` 留痕」；
   - 改为**照写进 `values`** ⇒ 兜底 = 掩饰错误，被排除在链路之外。

**③ 注释口径对齐**（本批次的主要产出之一）
   - `_normalize_recommendations`：**第 2 步是「去噪」（丢弃零变化项），不是「取舍」**
     ⇒ 取舍是第2层的事；
   - 同处补一条：**这份不是定版点** —— 第2层裁决后还会就地回填裁决状态
     （`decision_status` / `decision_reason`）⇒ 落库/展示看到的是回填后的版本；
   - `decide_direction` / `integrate_params` / `anchors` / `algorithms/__init__`
     的职责表述同步更新（**第3层不再「校验规则是否可用」**）。

**④ 时序结论**（用户在讨论中追问并拍板）
   - 「计算放在筛选之后是否更合适？」⇒ **位置不用挪**：
     计算都在第2层之前，但**算出来的结论必须活过筛选**；
   - 前提是**筛子要精确**：**噪声**（零变化项）与**冲突**（两条规则互相抵消）
     要分开 —— 现在的「丢零变化项」会把 conflict 项一起丢掉
     ⇒ **conflict 让位那两处本批次没有动**（待用户拍板）。

**验证**：pytest **119 passed**（`test_layer2_does_not_check_parameter_existence`
改为 `test_layer2_does_not_check_local_value_presence`；新增
`test_non_process_params_never_enter_candidates`）；`verify_provided_smoke.py` PASSED
—— `not_in_baseline` 那条建议**仍不进参数集**（机制换成**候选准入挡住**）。

⇒ **与批次 14.1 的差异**：14.1 = 「规则是否可用」交给第3层兜底；
14.2 = **兜底撤掉**，改由**候选准入**（静态字段字典）保证下游只见到工艺量。

---

### 批次 14.3：编排层方法改名 `_resolve_direction` → `_decide_direction_by_strategy`（2026-11-20，已落地）

**用户提问**：「接下来是这个方法，我觉得函数命名存在歧义」⇒ 核实后**歧义成立**，三处：

   ① **动词语义冲突**：仓库里 `resolve_*` 全部是「**算出来 / 查出来**」
      （`resolve_mel_target` 解算 MEL 目标、`resolve_fill_target` 解算充填目标、
      `resolve_stage_count` 解析段数、`resolve_baseline` 查出基线）⇒
      `resolve_direction` 读起来就是「**算出**调整方向」⇒ 与本轮口径
      （第2层**不产出落地值**，只给「调哪个 + 谁让位 + 什么口径」）**正好反着**；
   ② **同名差一个下划线**：编排层 `_resolve_direction`（封装：候选准入 + 策略裁决）
      与算法层 `resolve_direction`（第2层本体）几乎同名 ⇒ 读代码分不清在调哪个；
   ③ **一个概念两个动词**：模块叫 `decide_direction.py`（裁决），
      函数叫 `resolve_direction`（解算）⇒「裁决」语义已被模块名占用；
   ④ **名字只说了后半截**：该方法实际做两件事（候选准入 + 策略裁决），
      名字把 14.2 刚立的「是不是工艺量」准入判据藏了起来。

**改名**（动宾齐、动词分工清晰）：

   - 编排层 `_resolve_direction` → **`_decide_direction_by_strategy`**
     （`decide` = 取舍裁决，与模块名一致；宾语 = `direction` = 返回值 `Direction`；
     `by_strategy` 标明「按策略清单裁决」，与 `sort_defects_by_stage` 同型）；
   - 算法层 `resolve_direction` **不动** —— 用户口径「算法部分等流程调完再说」
     ⇒ 本次只改编排层（service 私有函数，改名零风险）。

**验证**：pytest **119 passed**；`_resolve_direction` 全仓库残留 0
（1 个定义 + 1 个调用 + 1 处 docstring 引用 + 本文档 3 处引用）。

**未做**：把方法拆成 `_collect_candidates` + `_decide_by_strategy` ——
`collect_candidates` 本身已是独立函数，再包一层不增加信息。

**未做（待流程调完再处理）**：算法层公开类型 `Direction` 同样名不副实 ——
14.0 之前它求落地值（MEL 已翻成计量位置）⇒ 叫「调整方向」勉强说得通；
14.0 改成「只给调哪个 + 谁让位 + 什么口径」后，它装的是**一份调整决定**
⇒ 不是「往哪调」的那个**单一取向**。
⚠️ 它是算法层**公开类型** ⇒ 改名要动：类定义 + `__all__` + service 的 import 与类型标注 +
第3层形参与类型标注 + 测试 import/用法 + `docs/*.md`。
⇒ **已在批次 14.4 处理**（连带 `.decision` / `.decisions` 一并改名，见该段）。

⚠️ **附带问题**：同一个对象里同时存在 `decision`（裁决结果：谁保留/让位/暂缓）与
`decisions`（保留项清单：字段名 + 目标值）⇒ 两个近似名、语义却完全不同 ⇒
改名 `Direction` 时应一并处理（否则「方向 → 计划」之后，`decision` / `decisions`
的错位仍在）。
⇒ **已在批次 14.4 处理**（`.decision` → `.selection` / `.decisions` → `.assignments`）。

---

### 批次 14.4：`direction` 一词让开 —— 第2层产出物整链改名（2026-11-20，已落地）

**用户追问**：「direction 这里的 direction 究竟表示什么呢」
⇒ 核实后确认：**同一个词在仓库里有两层同名不同义的用法**。

| 层 | 含义 | 位置 | 能否动 |
| --- | --- | --- | --- |
| ① 经验推理的**取向** | `increase` / `decrease` / `hold` / `check` —— 「往哪调」 | `rec['direction']`、`'direction': 'check'`、`_direction_from_delta`、`_DIRECTION_CN` | **不可动** —— 对外契约字段（响应/落库结构） |
| ② 第2层的**产出物** | 一份**调整决定清单**（谁保留 / 谁让位 / 暂缓 + 字段名 + 目标值） | `algorithms/decide_direction.py::Direction` 及其上下游 | 可动 —— 内部类型 |

⇒ 14.0 之前 ② 装的是「算出来的落地值」，叫「调整方向」勉强说得通；
14.0 改成「只给调哪个 + 谁让位 + 什么口径」后，它**不是单一取向**，而是一份清单
⇒ **名不副实**（用户口径：「不然我看 direction 都不懂是什么」）。

**改名表**（用户拍板「调整吧」后整链执行）：

| 原名 | 新名 | 位置 |
| --- | --- | --- |
| `Direction` | **`AdjustmentPlan`** | `algorithms/decide_direction.py`（算法层公开类型） |
| `.decision` | **`.selection`** | 同上（裁决结果：谁保留/让位/暂缓 + 依据） |
| `.decisions` | **`.assignments`** | 同上（保留项清单：字段名 + 目标值） |
| `resolve_direction()` | **`build_plan()`** | 第2层本体 |
| `apply_direction()` | **`apply_plan()`** | 第3层（`integrate_params.py`） |
| `_decide_direction_by_strategy()` | **`_decide_plan_by_strategy()`** | 编排层（`services/parameter_optimize.py`） |
| 局部变量 `direction` | **`plan`** | 编排层 + 第3层 + 测试 |

**「不动」清单**（① 取向语义，属对外契约）：`rec['direction']`、`'direction': 'check'`、
`_direction_from_delta`、`_DIRECTION_CN` —— 一律保留。

**顺带解决的两处同名错位**：`decision`（裁决结果）与 `decisions`（字段清单）
近似名、语义完全不同 ⇒ 改为 `selection` / `assignments` 后不再互相干扰；
`to_trace()` 的留痕键同步改为 `'assignments'`。

**未做（用户口径：等流程调完再拆）**：不拆 `decide_direction.py` 文件 ——
本批次**只改名、不动结构**。

**验证**：pytest **119 passed**；`verify_provided_smoke.py` **PASSED（EXIT 0）**；
旧名 `Direction` / `resolve_direction` / `apply_direction` /
`_decide_direction_by_strategy` 在 backend 残留 **0**。

**教训（两条）**：

1. **smoke 抓到 pytest 没覆盖的漏改** —— `_guard_zero_landing(baseline, direction, …)`
   这一处参数名不在任何测试调用路径上 ⇒ pytest 119 项全绿，但 smoke 直接
   `NameError` ⇒ **改名后必须跑一次端到端 smoke**，不能只看单测；
2. **`replace_all` 前缀吞并** —— `direction.decision` 是 `direction.decisions` 的
   **前缀** ⇒ 一次性替换 `decision` → `selection` 会把 `decisions` 一并改掉
   （3 处）⇒ 文本替换前先确认**新串不是旧串的前缀**，否则要带上分隔符一起匹配。

---

### 批次 14.5：位置类超行程从「半处理」改为**阻断**（2026-11-21，已落地）

**用户拍板**（原话）：

> 「我不建议做回退这种事情，容易引起误解」
> 「我建议可以先按照超限值处理，或者超限先报错，回退容易污染流程」

⇒ 两条候选：**① 按超限值处理** / **② 超限先报错**；**回退一律不做**。

**① 病灶定位：优化链路发明了越限体系外的第三种处理**

`algorithms/fuzzy/over_limit.py` 已有完整的安全分层（三种上限来源 ⇒ 三档处理）：

| limit_source | 参数类型 | 风险性质 | 处理 |
| --- | --- | --- | --- |
| `device` | 设定值类 | 操作设备涉及安全 | **拒绝** 400 |
| `stroke` | 位置类 | 产品在本机做不出来 | 原：**留痕（不阻断）** |
| `material` | 温度类 | 材料降解 / 变色 | 告警 / 兜底 |

而优化链路在 `stroke` 档之外又做了一件事：**剔除超行程参数的数值推荐**（但值照写）
⇒ 成了**体系外的第三种处理**——既不是阻断（值照样落库），也不是纯告知（数值推荐被藏了）
⇒ **半处理**。后果：用户被告知「本机做不出这个产品」，系统却把**更超行程**的值落库；
而 `_drop_over_stroke_value_recommendations` 的 docstring 写的「不再写回 baseline」
**与实现不符**（值已由 `apply_plan` 无条件写入）。

**② 技术事实：`BLOCKING_LIMIT_SOURCES` 加 `stroke` 是无效改动**

`detect_blocking_over_limits()` 内部**只调 `detect_over_limits()`**（`limit_source` 恒为
`'device'`）⇒ `stroke` 档**永远进不了**它的结果 ⇒ 把 `'stroke'` 加进
`BLOCKING_LIMIT_SOURCES` **改了也不生效**。两套上限来源本就不同：
设定值类按**族前缀**查（`resolve_param_limits`），位置类按**设备实测行程**查
（`resolve_position_limits` + `lookup_position_limit` 两级匹配）。

⇒ 落点：**service 层的机台能力守卫**（与 `parameter_initialize` 已有守卫同一套）。

**③ 改动清单**

- **删** `parameter_optimize._drop_over_stroke_value_recommendations`（剔除数值推荐）
  与 `_append_position_over_stroke_notices`（追加 check 告知）⇒ 「半处理」整段消失；
- **增** `parameter_optimize._guard_position_over_stroke` —— 检出即
  `BizException(ERROR_PROCESS_OVER_STROKE, …)`；
- **改** 调用点：判据从「建议列表」改为**第3层整合后的落地值**（`integrated.values`）
  ⇒ 整合值 ⊇ 基线值 ⇒ 一道同时覆盖「当前值本来就超」与「本轮把它推超了」；
- **改** `over_limit.py` 的分层表与 `detect_over_stroke_limits` 的 docstring
  （`stroke` 档由「留痕（不阻断）」改为「**拒绝** 400（机台能力校验）」）；
- **改** `parameter_initialize.py` 守卫 docstring（「那边只告知不阻断」已不成立
  ⇒ 两边改为**同一判据、同一错误码、同一文案**，差别只在判据取值）；
- **增** `tests/test_over_stroke_guard.py`（5 条：超行程报错 / 不超放行 / 边界等于行程
  不算超 / 缺机台行程不判 / 多项合并成一条）。

**④ 「拦了没出路」这个前提被推翻**

旧口径说「用户改不了 ⇒ 拦了也没有出路 ⇒ 只告知」——但**出路是明确的**：
换行程更大的机（错误码标题已是「当前设备无法生产该制品」+ 文案「请更换行程更大的设备」）
⇒ 拦下去有出路 ⇒ **值得拦**。与 `device` 档的差别不再是「该不该拦」，
而是**拦了之后说什么**（出路：改值 vs 换机）。

**⑤ 代价（已知并接受）**

超行程产品**整个优化请求失败**（拿不到其它参数的建议）。
实测数据里确有超行程产品（`engine.py` 注释：「实测 MEL 56/70 行超行程」，
行程 200mm 而产品充填需 291mm）⇒ 这些行从「能出建议」变成「直接失败」。
⇒ 但初始化链路**本就拒绝**超行程（`parameter_initialize` 同名守卫）⇒
能走到优化链路的超行程只剩两类：**本轮推过头**（策略/规则有问题 ⇒ 报错合理）
与 **用户手工调超了**（本来就是错值 ⇒ 报错合理）。

**⑥ 验证**：pytest **124 passed**（119 + 新增 5）；`verify_provided_smoke.py`
**PASSED（EXIT 0）**；被删的两个函数在 backend 残留 **0**。

**教训**：处理链路上出现「**部分生效**」的分支（只改展示、不改落库）时，
要么**完整拦**、要么**完整放**，不要留中间态——中间态既让展示与落库对不上，
又让文档（说什么）与实现（做什么）对不上。


