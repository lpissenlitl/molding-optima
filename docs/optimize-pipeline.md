# 工艺参数优化 · 端到端链路

> **目的**：把「一次调机请求从前端进来到最终工艺落库」的**完整链条**捋清楚 ——
> 每一步做什么、在哪份代码、数据怎么流、边界在哪、哪里是已知缺口。
>
> **状态**：**链路现状说明书**（2026-11-24，按代码实测写成）；本轮**只出文档，不改代码**。
>
> **关联**：
> `docs/tuning-thinking-chain.md`（调机思维链 · 环节模型与待办）、
> `docs/l2-stage-strategy-design.md`（L2 策略层口径；§12 目标值求解口径）、
> `docs/algorithm-layering-plan.md`（四层目录与分层铁律）、
> `docs/qualified-tuning-boundary.md`（合格态调机的功能边界）、
> `docs/open-questions.md`（未决项单一真相源）。

---

## 0. 全链一览

```
前端                     service（编排）                    算法层 / 策略层 / 落地层
────                     ──────────────                    ─────────────────────
① 传参
  condition_id
  parent_seq_idx
  parameter? (flat)
  feedback{defects, observations, tuning_result}
   │
   ├─ Step0 反馈转换与契约校验 ──→ _to_algorithm_feedback
   │        （缺陷码中文→英文码；仅 qualified 允许空缺陷）
   ├─ Step1 装配上下文（只读 DB）──→ _resolve_infer_context
   │        （三维上下文 + baseline ← ORM 反查 parent_param）
   │
   │                    ┌──────── _infer_kernel（纯推理，与 DB 无关）────────┐
   │                    │ 预处理层                                          │
   │                    │   ② select_defect  ← 收敛成「本轮处理哪条缺陷」   │
   │                    │   ② guard_parameter_limits ← 基线越限直接拒       │
   │                    │                                                    │
   │                    │ ③ 第1层：调算法出一堆平级建议                     │
   │                    │   _compose_algorithm_context → AlgorithmContext   │
   │                    │   _call_algorithms → 各引擎 recommend              │
   │                    │   _select_algorithm_result → 只取优先级最高的产出  │
   │                    │   _annotate_recommendations → 补中文标签           │
   │                    │                                                    │
   │                    │ ④ 第2层：结合调机策略确定调整方向               │
   │                    │   build_adjustment_scheme（决策层入口）→ 挑料 → 派生│
   │                    │     collect_facts → 事实表                       │
   │                    │     select_strategy → 命中场景                   │
   │                    │     resolve_scheme → resolve_priority（裁决）    │
   │                    │     _apply_decision_status → 裁决状态回填建议    │
   │                    │                                                    │
   │                    │ ⑤ 第3层：整理最终工艺                             │
   │                    │   apply_scheme → integrate（锚点传导）            │
   │                    │   _detect_zero_landing → 零落地即中止             │
   │                    │   _quantize_numeric_fields → 落库/响应同源        │
   │                    │ ⑥ 第4层：校验（只识别不改值）                    │
   │                    │   validate → 越限则拒绝本轮                      │
   │                    │   _build_suggestion_payload → 建议分组载荷         │
   │                    └────────────────────────────────────────────────────┘
   │
   ├─ Step2 纯推理（上面的 _infer_kernel）
   │
   ├─ Step3 原子事务落库
   │        _settle_recommendation_adoption → 结算父轮建议采纳
   │        _record_tuning_round            → TuningRecord（评价/缺陷/实测）
   │        _create_new_round               → 新轮次 ProcessParameter
   │
   └─ Step4 响应 {parameter, suggestion}
```

---

## 1. ① 前端传参

| 项 | 内容 |
|---|---|
| 前端入口 | `frontend/src/api/index.ts::processOptimizationInfer` → `POST /api/processes/algorithms/optimize/` |
| 视图 | `backend/process/views/processes.py` L507-515 → `parameter_optimize.optimize_from_condition(...)` |
| 入参 schema | `ProcessOptimizeFromConditionSchema`（`backend/process/schemas/optimization.py`） |

**四个入参**：

| 字段 | 必填 | 含义 |
|---|---|---|
| `condition_id` | ✅ | 工艺条件 ID |
| `parent_seq_idx` | ✅ | 基准业务编号（父轮） |
| `parameter` | ❌ | 手动修改覆盖；**flat 字段**（前端 `parameterToFlat` 翻译）；不给则从 ORM 反查 `parent_param` 作 baseline |
| `feedback` | ❌ | `defects[]` / `observations[]` / `tuning_result` |

**实测观察项 4 键**（`frontend/src/constants/observation-order.ts` L19-23）：

| `param_key` | 中文 | 单位 | 后端消费方 |
|---|---|---|---|
| `actual_product_weight` | 制品实际重量 | g | ✅ `read_weights`（充填量口径输入，anchors 底座） |
| `peak_pressure` | 峰值压力 | MPa | ❌ 零消费 |
| `injection_time` | 实际注射时间 | s | ❌ 零消费 |
| `cycle_time` | 周期时间 | s | ❌ 零消费 |

**Step 0 · 反馈转换与契约校验**（`parameter_optimize.py::_to_algorithm_feedback` L975-1012）：

- 缺陷码**中文名 → 英文码**（`to_defect_code`）⇒ 引擎查规则与 L2 阶段/场景裁决拿到**同一份英文码**；
- `observations` **原样透传**（不做投影）；
- `audit_feedback_defects`（`allow_empty=is_qualified_result(...)`）⇒ **仅合格态允许空缺陷**。

**Step 1 · 装配上下文**（`_resolve_infer_context` L1288-1298）：

- 反查 `condition` / `parent_param` / `baseline`（**只读 DB，不落库**）；
- 抽三维上下文 `machine_info` / `polymer_info` / `mold_info`；
- `last_advised_params = _load_adopted_params(parent_param_orm)`（L1311）⇒ **上一轮实际落地的参数**
  ⇒ 退阶的事实来源（纯推理入口 `optimize_from_provided` 没有上一轮 ⇒ 传空）。

---

## 2. ② 识别缺陷（预处理层）

`_infer_kernel` 的预处理层（L1432-1448）三件事，**顺序固定**：

| 序 | 动作 | 代码 | 作用 |
|---|---|---|---|
| 1 | 三维上下文必填校验 | `_validate_optimize_inputs` | 缺则不推理 |
| 2 | **缺陷选取** | `select_defect(feedback)`（`optimize_chain/defect_selection.py` L143-165） | 收敛成「本轮处理哪一条」+ 留痕 `defect_selection` |
| 3 | 基线越限守卫 | `guard_parameter_limits`（scope=`optimize`） | 当前设定值超机台上限 ⇒ 直接拒 |

**选取口径固定 = 阶段序**（`StagePriorityDefectStrategy`）⇒ 按 `STAGE_ORDER`
（`filling` → `shrinking` → `appearance`）选最靠前阶段的那条缺陷。

> 【注意】**收敛只做一次，L1 / L2 共用同一份** —— 这是已定的口径
> （`feedback` 预处理层：缺陷整理只做一次）。L2 侧只读 `defect_codes`，**不重选缺陷**。

---

## 3. ③ 调用算法给建议（L1 · 载体）

### 3.1 入参组装

`_compose_algorithm_context`（L515-560）⇒ `AlgorithmContext`：

| 键 | 内容 | 取值来源 |
|---|---|---|
| `machine_info` / `polymer_info` / `mold_info` | 三维上下文 | service 层 `shared/spec_extract.py` 抽取 |
| `parameter` | 当前参数（baseline） | ORM / 前端 flat |
| `feedback` | **已收敛**的缺陷反馈 | ② 的产物 |
| `libraries` | 本轮可见规则库 | `_resolve_visible_libraries(condition_orm.company_id)` ⇒ **租户隔离在 service 层完成**，算法侧不持有租户概念 |

### 3.2 调度（**载体择优，不是载体合并**）

`_call_algorithms`（L464-509）：

1. `AlgorithmRegistry.get_available_algorithms(context)` ⇒ **各引擎自己判** `is_available(context)`；
2. 按 `AlgorithmRegistry.get_priority(subtype)` 排序 —— **fuzzy 1 / llm 2 / empirical 3**
   （`algorithms/base.py` L178-184）；
3. 逐个 `algorithm.recommend(context)`，**单个引擎异常不牵连其它**（try/except 降级为空）；
4. **`_select_algorithm_result(algorithm_sources)`** ⇒ 最终建议集**只采用优先级最高的那个有产出的引擎**
   （其余引擎的产出保留在 `algorithm_sources` 里，仅供来源标注）。

> 【注意】这是**「一个载体说话」**语义，不是「多载体合并」——
> ⇒ 载体优先级被当成了**逻辑顺序**（见 §7 缺口 G4）。

> 【注意】**「调」无条件** —— service 层**不预判**该不该调，「本轮适不适合发言」由
> 各引擎自己的 `is_available` 判；「这一轮用不用 L1 的建议」由**第2层裁决**决定
> （候选合并 + 准入/次序/名额/让位）⇒ **「调」与「用」是两件事**。

### 3.3 出口

- `_annotate_recommendations(raw_recommendations)`（L1476）⇒ 补中文标签与业务文案；
- **fail-fast**（已**移位**，2026-11-25 批次 15.1）：**L1 零产出不拒** ⇒ 交 L2 裁决；
  **引擎零产出 且 L2 零保留项** ⇒ 才 `BizException(ERROR_OPERATION_FAILED, "推荐算法暂不可用，请稍后重试或联系管理员")`。
  ⇒ **对非合格态行为完全等价**（引擎有产出时消息不变；引擎零产出但全被让位时仍落到第3层的「零落地」守卫）。
  ⚠️ **引擎零产出 ≠ 合格态** —— 零产出是**现象**（成因很多：无缺陷 / 规则库无匹配 / 引擎不适用），
  **不能拿它反推合格**；合格态的判据只有 **`feedback.tuning_result`**（§4.1 的 `last_tuning_result`）。
  ⇒ 拒绝判据落在**裁决结果**（L2 零保留项）上，而不是**原因层信号**（L1 零产出）。

> ⚠️ **这条 fail-fast 就是合格态当前的死路**（见 §7 缺口 G1）—— **已于 15.1 解决**。

**建议的数据形态**（`algorithms/base.py::AlgorithmRecommendation.to_dict`）：

```python
{'param': 字段名, 'current_value': 现值, 'recommended_value': 目标值,
 'confidence': 置信度, 'reason': 依据, 'source': 来源引擎, 'direction': 方向}
```

---

## 4. ④ 结合调机策略确定调整方向（L2）

> 【注意】**第2层只有一个入口**（`build_adjustment_scheme`）—— 挑料、派生、匹配、裁决全在它内部；
> service 层只**交原料**（`feedback` / `mold_info` / 上一轮落地参数）拿**结论**。

### 4.1 挑料：从原料取出事实

`collect_facts(feedback, mold_info, last_advised_params)`（`decide_adjustment.py`）⇒ **一次成型**的事实表（键名 = 场景条件可引用的字段名）：

| 键 | 来源 | 用途 |
|---|---|---|
| `defect_codes` | ② 收敛结果（**只认一手出口** `defect_selection`） | 场景条件 |
| `actual_weight` / `target_weight` | observations / `mold_info.total_product_weight` | 充填量口径 |
| `last_tuning_result` | `feedback.tuning_result` | **合格态判据位** |
| `last_advised_params` | 上一轮实际落地的参数 | 退阶的事实来源 |

> 【注意】**只放取到的值** —— 取不到的键**根本不存在** ⇒ 条件引用不到 ⇒ **不命中**（不臆造）。
> ⇒ 条件可引用的字段名**不写死在代码里**（`docs/l2-stage-strategy-design.md` §10 拍板 E）。

### 4.2 派生：为条件补中间量

同一函数内完成（不回头改事实表）：

| 键 | 算法 | 供哪个条件用 |
|---|---|---|
| `fill_gap` | 制品总重 − 实测重量（**正数 = 缺料**） | `filling_first` 的 `fill_gap > 0` |
| `current_stage` | `derive_stage_progress(defect_codes)`（`decide_adjustment.py`）⇒ 纯函数、不落库 | `filling_stage_first` 的 `current_stage == 'filling'` |

> 【注意】**阶段达成** = 该阶段的所有缺陷码本轮都不出现；**当前阶段** = 第一个未达成的阶段。

### 4.3 命中场景

`select_strategy(strategies, facts)`（`decide_adjustment.py`）⇒ **取第一条命中**，不合并多条。

场景清单（`decide_adjustment.py::SCENARIO_STRATEGIES`，共 **8** 条，按 `priority` 升序）：

| 场景 | 触发条件 | 白名单 | 优先项 |
|---|---|---|---|
| `filling_first` | `SHORTSHOT` + `fill_gap > 0` | `met_end_pos` / `vps_pos` | `met_end_pos`（+ `fill_ratio` 口径） |
| `filling_stage_first` | `SHORTSHOT` + `current_stage == filling` | 胶量端 + `inj_t` + 压力等 | 胶量端 |
| `shrinking_first` | 缩水类（`SHRINKAGE`/`UNDERSIZE`/`OVERSIZE`/`WARPING`） | `hold_pres_1` / `hold_t_1` | `hold_pres_1` |
| `flash_first` | `FLASH` | `hold_pres_1` / `met_end_pos` | `met_end_pos` |
| `burn_first` | `BURN` | 熔体侧 4 项 | `met_back_pres_1` |
| `gasveins_first` | `GASVEINS` | `met_back_pres_1` / `hold_pres_1` / `hold_t_1` | `met_back_pres_1` |
| **`qualified_efficiency`**（**新增，15.1**） | `last_tuning_result == 'qualified'`（**合格态**） | `inj_pres_1` | `inj_pres_1`（+ `step_down` 口径） |
| `default_one_adjust` | **空条件 ⇒ 恒命中**（兜底） | 不限制 | — |

⇒ 全部 `max_items=1`（U-01「一轮只改一个量」）；全部 `blocked_params = BASELINE_BLOCKED_PARAMS`
（`inj_spd_1..6` 属基线取值，不参与阶段调机）。

⚠️ **`qualified_efficiency` 的特殊性** —— 它是**唯一一条自带候选的场景**
（`candidate_params=('inj_pres_1',)`）：缺陷场景的候选**全部来自 L1 建议**，
而合格态**没有缺陷 ⇒ 缺陷驱动引擎零产出 ⇒ 没有候选** ⇒ 光加场景仍然落不了地。
⇒ 场景自带候选 = **不新建引擎、不新判据源**前提下，合格态唯一的候选来源。

### 4.4 裁决

`build_adjustment_scheme`（`decide_adjustment.py`）内部：`collect_candidates`（收 L1 建议）→ **`_merge_candidates`（追加场景自带候选，15.1）** → `resolve_scheme` → `resolve_priority`。

**裁决序**（`decide_adjustment.py` L418-437）：

```
1 场景优先集 → 2 禁入（基线项） → 3 上轮证伪（failed_params） → 4 准入（白名单）
→ 5 落不了地（vetoed） → 6 目标已达成（satisfied） → 7 名额（max_items）
```

- 让位与暂缓**都是显式决策并留痕**（`yielded` / `deferred` + 理由）；
- 保留项也留依据（`kept_reasons`）—— 反馈回来才能证伪「为什么按这个次序调」。

**目标值口径**（§12 已定型）：

- `met_end_pos` ⇒ 走 `fill_ratio` 口径（目标行程 = 当前行程 × 目标重量/实测重量），
  **L2 只带口径名，算式在 L3**；
- 其余字段 ⇒ **目标值原样取自 L1 建议**（`resolve_scheme` L797-801）⇒ L2 不参与「改成多少」；
- ⚠️ **例外（15.1）**：`step_down` 口径的字段（首批 `inj_pres_1`）⇒
  **目标值由 L3 按口径解算**（当前设定 × (1 − 步长)）⇒ **覆盖** L1 的绝对值
  （口径比算法建议更具体 ⇒ 口径优先）。

**回填**：`build_adjustment_scheme` 内的 `_apply_decision_status` ⇒ 裁决状态回填到建议 ⇒ **前端展示与落库同源**。

---

## 5. ⑤ 整理最终工艺（L3 落地 + L4 校验）

### 5.1 L3 · 锚点传导

`apply_scheme(baseline, scheme, previous=baseline, feedback=..., mold_info=...)`（`integrate_params.py` L512-615）：

```
scheme.assignments  ──→ 直接写入
MEL 目标 + 口径     ──→ resolve_fill_target（按比例解算注射行程）→ met_pos_N
step_down 口径      ──→ resolve_step_down（当前设定 × (1 − 步长)）—— 15.1 新增
                    ──→ integrate()（物理联动传导：位置类双向同步等）
                    ──→ _detect_zero_landing（零落地检测）
```

- **重量由第3层自己取** —— `read_weights(feedback, mold_info)`（`anchors.py`）⇒ 制品总重 + 实测制品重量；
  「要哪两个重量」是**口径**的事 ⇒ 上层只递原料，不替它挑（15.3）；
- **零落地** ⇒ `BizException(ERROR_OPERATION_FAILED, '本轮调整无法落地（...）')`（L1520-1529）。

### 5.2 出口定稿

`_quantize_numeric_fields(integrated.values)`（L1533）⇒ 统一两位小数
⇒ **落库值与响应值同一份**（L4 也据此判定）。

### 5.3 L4 · 校验（只识别不改值）

`validate(new_parameter_dict, limits=..., machine_limits=...)`：

- **不越限** ⇒ 只记日志，**不改值**；
- **越限**（`over_limit_violations`）⇒ `BizException(ERROR_PROCESS_UNFIT_PARAM, ...)` ⇒ **拒绝本轮**。

### 5.4 建议载荷

`_build_suggestion_payload(recommendations, algorithm_sources, baseline, applied_values)`（L1557）
⇒ 按分类归拢成前端要的 `groups`。

---

## 6. ⑥ 落库与回执（Step 3 · 原子事务）

`optimize_from_condition` L1314-1343，**只开一个事务**（`db_transaction.atomic`）：

| 步 | 动作 | 作用 |
|---|---|---|
| 3.1 | `_settle_recommendation_adoption(parent_param, tuning_result)` | 结算父轮建议的采纳状态（`is_adopted`） |
| 3.2 | `_record_tuning_round(...)` | 写 `TuningRecord`：`result`（`TUNING_RESULT_MAP` 映射）/ `defect_feedbacks` / `observations` / `adjustments`（快照差异） |
| 3.3 | `_create_new_round(condition, parent_param, parameters_dict)` | 新轮次 `ProcessParameter` + 它自己的 `TuningRecord`（1:1 同批建） |

**Step 4 响应**（L1346-1352）：

```python
{'parameter': new_param.to_dict(),
 'suggestion': {**suggestion_payload, 'recommendation_id': recommendation.id}}
```

**下一轮推进**（跨轮）：`last_advised_params`（上一轮实际落地的参数）⇒ `_failed_params`
（上轮 `unchanged` / `ineffective` ⇒ 该参数本轮让位换旋钮）+ `derive_stage_progress`（阶段推进信号）。

---

## 7. 已知缺口与断点（**本链上**）

| # | 缺口 | 位置 | 性质 | 登记处 |
|---|---|---|---|---|
| **G1** | ~~**合格态走本链会 fail-fast**~~ → ✅ **已解决**（2026-11-25，批次 15.1）：fail-fast 从「L1 零产出」**移到「L2 零候选」** + 场景自带候选（`qualified_efficiency`）⇒ 合格态不再无产出 | `parameter_optimize.py::_infer_kernel` / `decide_adjustment.py::SCENARIO_STRATEGIES` | ✅ **已闭环**（**未新建引擎、未新判据源**） | `open-questions` Q12 / C1（**均已关闭**） |
| **G2** | **次序缺位**：场景优先级表全空 ⇒ 字段级排序键失效 ⇒ 实际次序 = L1（规则库）产出顺序 | `decide_adjustment.py`（8 条场景均未填表）/ 同文件 L486-493（排序键） | 能力缺口 | `open-questions` Q1 / Q4 |
| **G3** | **「改成多少」半缺**：非派生量目标值 = L1 原样透传，L2 不参与 | `decide_adjustment.py` L797-801 | 能力缺口（**部分缓解**：15.1 起带 `step_down` 口径的字段由 L3 解算） | `l2-stage-strategy-design.md` §12 |
| **G4** | **载体语义错位**：`_select_algorithm_result` 只取优先级最高的单一引擎 ⇒ 载体优先级被当成逻辑顺序 | `parameter_optimize.py` L505-507 | 语义问题 | `tuning-thinking-chain.md` T7 |
| **G5** | **匹配度被丢弃**：`confidence` 在 L1→L2 边界不进候选 | `decide_adjustment.py::collect_candidates` L609-654 | 能力缺口 | `tuning-thinking-chain.md` T4 同族 |
| **G6** | **观测 3 键零消费**：`peak_pressure` / `injection_time` / `cycle_time` 契约有、实现无 | `schemas/optimization.py` L56-68 | 待接线 | `qualified-tuning-boundary.md` §3.4 |
| **G7** | **阶段达成度可能高估**：「不区分已解决 / 从未报过」 | `decide_adjustment.py` L944-945（`derive_stage_progress` 的口径说明） | 口径待定 | `tuning-thinking-chain.md` T8 |
| **G8** | **缺陷选取口径** = 阶段序；规则原料 U-08 要求 Pareto（报废占比） | `defect_selection.py` | 待议 | `tuning-thinking-chain.md` T9 |

---

## 8. 思维链视角下的这条链

按 `docs/tuning-thinking-chain.md` 的环节模型，本链的**同一套四段式**在每个环节复用：

```
准入判据 → 判据源 → [L1 载体给建议] → L2 裁决 → L3 落地 → L4 校验
```

| 环节 | 准入判据 | 判据源 | 载体 | 现状 |
|---|---|---|---|---|
| ① 修缺陷 | 有缺陷码 | 缺陷码 + 规则库 | fuzzy（llm 占位 / empirical 兜底） | ✅ 本链 §2–§6 即此环 |
| ② 优化能耗 / 周期 | 无缺陷 + 合格 | 实测观测 + 目标参照 | **场景自带候选**（无载体） | ✅ **首批已落地**（15.1）：`qualified_efficiency` + `step_down` 口径（递减步进，步长 5% 初值）；⚠️ **只降压力**，省周期待补 |
| ③ 结束 | 无缺陷 + 无可省项 | — | — | ⚠️ 位置待正名（`default_one_adjust` 顶着） |

⇒ **G1 已闭环（15.1）** —— 合格态的**出口已建**（场景自带候选 + 口径解算），
**未新建引擎、未新判据源**，仍走同一条 L1–L4 分层。
⇒ **待补**：省周期（`cool_t` + 周期口径）、「降过头」回退机制、「合格但无可省项」的前端表现。

---

## 9. 一句话收口

> **一次调机请求 = 前端传参 → 识别缺陷（收敛成一条）→ L1 载体出一堆平级建议
> → L2 结合生产上下文裁决（调哪几个、次序、口径）→ L3 锚点传导整理成自洽参数
> → L4 只识别不改值地校验 → 原子落库建下一轮 → 响应。**
>
> 链条本身是通的；**七处缺口**集中在「次序（G2）」「改成多少（G3）」「观测接线（G6）」三处。
> **合格态（G1）已于 2026-11-25（批次 15.1）闭环** —— 补的是**调机策略**，不是新引擎。
