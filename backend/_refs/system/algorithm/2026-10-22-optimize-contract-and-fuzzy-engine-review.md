# 工艺优化链路契约与模糊推理引擎现状走查

- 日期：2026-10-22
- 前置文档：`2026-10-20-fuzzy-inference-review-and-roadmap.md`（模糊推理评估与改良路线）
- 性质：**讨论记录**。本文只记录已核实的代码事实与待决问题，不含实现改动。

---

## 0. 本轮已确认的决策

| # | 决策 | 状态 |
|---|------|------|
| D1 | 初始化参数（initialize）响应改为 **flat 格式**，与 optimize 的 `new_parameter` 对齐；参数形态转换统一由前端负责 | ✅ 用户已认可 |
| D2 | `observations` 与 `tuning_result` 需参与模糊推理 | ✅ 用户已认可（语义待定） |
| D3 | 模糊推理引擎现状需先讨论清楚再改造 | 🔶 进行中 |

---

## 1. 端到端链路的真实形态

### 1.1 三次 HTTP 交互

| # | 接口 | 路由 | 请求体 | 响应体 |
|---|------|------|--------|--------|
| A | initialize | `POST /api/processes/algorithms/initialize/` | masterdata ID 三件套 | `result.process` = **嵌套**（`inj_pres_steps` 等） |
| B | optimize | `POST /api/processes/algorithms/optimize/` | `condition_id` / `parent_seq_idx` / `parameter`(flat) / `feedback` | `new_parameter` = **flat**（ORM 88 字段镜像） |
| C | tuning-feedback | `POST /api/processes/tuning-feedback/` | `parameter_id` / `defect_feedbacks` / `observations` / `tuning_result` | 落库确认 |

### 1.2 请求侧字段的三种命运（实测）

| 字段 | 进推理 | 只落库 | 被忽略 |
|------|--------|--------|--------|
| `feedback.defect[].keyword_name` | ✅ 唯一进推理的请求字段 | ✅ | |
| `feedback.defect[].level` | ✅（规则前件档位） | ✅ | |
| `feedback.defect[].position` | ⚠️ 仅用于规则匹配，无独立作用 | ✅ | |
| `feedback.defect[].position_3d` | ❌ | ✅ | |
| `feedback.defect[]` 第 2 条起 | ❌（`_extract_defect_context` 只取第一个） | ✅ | |
| `feedback.observations[]` | ❌ | ✅ | |
| `feedback.tuning_result` | ❌ | ✅（写 `TuningRecord.result`） | |
| `parameter`（flat，可选） | ✅（写入 baseline） | ✅ | |

> **结论**：请求里 4 类反馈子块，后端实际只消费了「第一个缺陷」。

### 1.3 响应侧的结构性不对称

- **S1**：initialize 返回嵌套（`result.process`），optimize 返回 flat（`new_parameter`）。
- **S2**：前端 `OptimizationCreate.vue::getOptimizedProcess` 只从 `new_parameter` 取 `parameter_id` / `seq_idx`，
  **从未把 flat 字段翻译回嵌套结构填入 `newRound.parameter`**；而 `makeRound()` 的默认模板
  （`settingProcessForm`）全为 null → **优化后的工艺参数表是空模板**。
  `parameterTransform.ts` 注释里指向的 `mapInferResultToParameter` 读的是 `result.process.inj_pres_steps`
  （initialize 形态），与 flat 不兼容。
- **S3**：`source_type` 实际返回 `'fuzzy'` / `'empirical'`，但 schema 描述写的是 `'fuzzy_rule'` / `'rule_miner'` / `'llm'`。

---

## 2. D1（flat 统一）的落点

### 2.1 后端已有现成的拍扁逻辑

`backend/process/services/parameter_initialize.py::_create_process_parameter`（L719-797）内含：

- `single_value_fields`（L748-758）：`inj_t` / `cool_t` / `vps_*` / `noz_temp` / `brl_temp_stg` 等单值字段
- `steps_mappings`（L764-776）：`inj_pres_steps` → `inj_pres_1..6`、`hold_time_steps` → `hold_t_1..5` 等

该逻辑**目前只用于落库**，未暴露为响应。改造方式：抽成独立纯函数
`process_params_to_flat(proc_dict) -> Dict[str, Any]`，落库与响应共用，消除重复。

### 2.2 改造点清单

| 位置 | 改动 |
|------|------|
| `parameter_initialize.py` | 抽出 `process_params_to_flat()`；`infer` / `infer_from_provided` 响应增加 flat 形态（保留 `process` 嵌套以兼容，或直接替换——待定） |
| `parameter_optimize.py` | `new_parameter` 已是 flat，无需改 |
| `frontend/.../parameterTransform.ts` | 新增 `parameterFromFlat(flat) -> SettingProcessForm`（注释中提到但始终未实现） |
| `frontend/.../OptimizationCreate.vue` | `getOptimizedProcess` 用 `parameterFromFlat(inferData.new_parameter)` 填 `newRound.parameter`；`mapInferResultToParameter` 改为读 flat |

---

## 3. 模糊推理引擎全景（6 层）

```
HTTP View        processes.py :: AlgorithmsOptimizeView
   │
编排层          parameter_optimize.py (1102 行)
   Step 0  _validate_feedback        缺陷校验（非 DEFECTFREE 时 level 必填）
   Step 1  反查 parent param
   Step 2  _compose_algorithm_context  字段提取（specs 白名单）+ 命名翻译
   Step 3  _call_algorithms            按 priority 排序 → 依次 recommend → 直接 concat
   Step 4  _build_suggestion_payload   按 baseline 过滤 → 分组 → items
   Step 5  原子落库 (ProcessParameter + TuningRecord + Recommendation)
   │
契约             AlgorithmContext (TypedDict, 5 键)
   │
注册中心         algorithms/base.py :: AlgorithmRegistry
                  priority: fuzzy=1 / llm=2 / empirical=3
   │
算法             FuzzyEngine (fuzzy_algorithm.py, 623 行)
   1) _extract_defect_context        只取第一个缺陷
   2) RuleQueryService.get_rules     库层路由 → 规则层拉取 → 去重 → 排序
   3) split_by_conclusion_kind       双层分流（按结论形态，非库层级）
   4) _infer_numeric_layer           NumTskRuleNet（零阶 TSK）
      _infer_advisory_layer          FuzzyRuleNet（Mamdani）+ check 弹窗类
   5) _merge_layer_results           方案 B：同层聚合 + 跨层覆盖
   │
输出             List[Recommendation]
```

---

## 4. 散乱点清单（实证，附代码位置）

### S-1 两套 context 构造点，形态已分叉 🔴

| 构造点 | 形态 |
|--------|------|
| `condition.py::_build_optimization_context`（L1099-1114） | **平铺**：`defect_name` / `polymer_abbreviation` / `product_category`；`feedback.defect[0].defect_name`（旧字段名）；`process_parameter` **未翻译** |
| `parameter_optimize.py::_compose_algorithm_context`（L447-453） | **子对象**：`polymer_info` / `mold_info`；`process_parameter` **已翻译**；**无 iteration_trend** |

对当前 `FuzzyEngine` 而言，`condition.py` 那条路径**完全跑不通**：

1. `feedback.defect[0]` 没有 `keyword_name` → `_extract_defect_context` 返回 `{}` → `is_available()` 返回 False → 根本不推荐；
2. 无 `polymer_info` / `mold_info` → `RuleQueryContext` 的 polymer / product 恒为 None → 永远退到默认库；
3. `process_parameter` 用业务命名 → `RuleKeyword.keyword_name` 是算法命名 → 论域元数据查不到 → 走兜底 `min=0, max=当前值×2`。

### S-2 `iteration_trend` 未进入 AlgorithmContext 🔴

- `AlgorithmContext`（L95-99）只有 5 键，**没有 `iteration_trend`**；
- `FuzzyEngine.recommend` 读 `context.get('iteration_trend')` → 恒 `{}` → `_trend_to_factor('unknown')` → **恒 1.0**；
- `_trend_to_factor` 的 `improving=1.2 / worsening=0.5` 是**死代码**；
- 而 `condition.py` L1083 已经能通过 `TuningService.analyze_iteration_trend(first_param)` 算出 trend，只是没送到 optimize 这条路。

### S-3 `tuning_result` 不进算法

HTTP 收了 → service 只用于落库：

- `_update_previous_tuning_record`（L754-782）：写 `TuningRecord.result`（effective→improved / ineffective→worse）
- `_update_previous_recommendation_is_adopted`（L785+）：下一轮 ineffective → 上一轮 `Recommendation.is_adopted=False`（训练标签）

`AlgorithmContext.feedback` 是整体透传，理论上算法能读到，但 `FuzzyEngine` 从未读过。

**后果**：上一轮被判 `ineffective`，本轮会给出**与上一轮完全相同**的建议（规则查询条件一模一样），且调整幅度不打折。

### S-4 `observations` 不进算法

HTTP 收了（`CycleObservationSchema`：4 个 `param_key`），service 完全不碰，`FuzzyEngine` 从未读过。

4 个观察项与可用基准值：

| param_key | 含义 | 基准值来源 | 是否已在 context 中 |
|-----------|------|-----------|-------------------|
| `actual_product_weight` | 制品实际重量 | `GatingSystem.total_product_weight`（设计值，模具维度） | ❌ 未取 |
| `peak_pressure` | 峰值压力 | `InjectionUnit.max_set_injection_pressure` | ✅ `machine_info` |
| `injection_time` | 实际注射时间 | `ProcessParameter.inj_t` | ✅ `process_parameter`（算法名 `IT`） |
| `cycle_time` | 周期时间 | `Mold.target_cycle_time` | ✅ `mold_info` |

### S-5 论域有三套来源，没人定权威 🔴

| 来源 | 内容 | 现状 |
|------|------|------|
| `RuleKeyword.range_min/range_max` | DB 表 | `RuleKeywordAdapter` 实际采用 |
| `specs.py` 的 `max_set_*` / `max_*_temp` | 设备/材料物理边界 | `specs.py` L303-311 写了 TODO 要接，**未接** |
| `FuzzyEngine._load_keyword_dicts` 兜底 | `min=0, max=当前值×2` | L373-391，**仍在用** |

→ 同一个参数有三个可能论域。`specs.py` 说「不传设备上限 → 结论不可信」，但引擎实际根本不读 `machine_info` 的上界。

### S-6 参数分类前缀与算法命名不对齐

`_PARAM_CATEGORY_RULES`（L107-117）用**业务前缀**（`inj_` / `hold_` / `met_` / `brl_temp_`），
但 `FuzzyEngine` 输出的 `param` 是**算法命名**（`IV0` / `PP0` / `BT`）。
`_build_suggestion_payload` 先用 `FuzzyEngine.to_business_name` 翻译再分类，勉强对上；
但 `noz_temp`（算法名 `NT`）不匹配任何业务前缀 → 归入「其他参数」。

### S-7 fuzzy 与 empirical 结果直接 concat

`_call_algorithms` 把两个引擎的推荐**顺序拼接**：

- fuzzy 给数值（`recommended_value` 有值）
- empirical 只给方向（`recommended_value=None`，见 `base.py` Recommendation 注释）

同一参数两条建议 → 前端显示冲突项。

### S-8 confidence 公式量纲不对

`FuzzyEngine._merge_layer_results` L586：`confidence = min(activation_sum / rule_count, 1.0)`

- `activation_sum` 是**求和**，`rule_count` 是**计数**，量纲不同；
- `activation` 来自 nets 内部**已全局归一化**的激活度 → 求和后除以条数 ≈ 1/条数 → 恒为 0.33 / 0.5 这类常数；
- 且 confidence **算了但没进 `suggestion.items`**（`_build_suggestion_payload` 未取该字段）。

---

## 5. `observations` / `tuning_result` 接入方案（待讨论）

### 方案 A：作为「条件变量」参与论域判级

把实测值与基准值算成偏差/比值，归一化成 [0,1] 隶属度，参与规则的模糊等级判定。

- 真正的模糊推理用法，但需要 `FuzzyFeature` 支持派生量论域；
- **代价**：规则库要重建（DB 里没有这类前件），规则运营成本高。

### 方案 B：作为「门控 / 物理约束过滤」⭐ 当前最可行

observations 只用于**剔除物理上不可能的建议**，不参与判级：

- `peak_pressure` 接近 `max_set_injection_pressure` → 剔除「提高注射压力」类规则；
- `injection_time` 实测 ≫ 设定 `inj_t` → 流动阻力大 → 剔除「降低注射速度」类规则；
- `cycle_time` 实测 ≫ `target_cycle_time` → 周期超标 → 剔除「延长冷却时间」类规则。

- **优点**：不依赖规则库改造，改造面小，物理意义明确；
- **缺点**：只能做减法，不能主动从 observations 推出建议。

### 方案 C：作为「调整幅度调节因子」

类比 `iteration_trend` 的 trend → factor：

- trend（improving/worsening）+ tuning_result（effective/ineffective）+ observations 偏差 → 合成一个全局标量 factor。

- **优点**：改造面最小（扩 `_trend_to_factor` 为 `_adjustment_factor(context)`）；
- **缺点**：全局标量同时放大/缩小所有参数建议，精度低；无法表达「A 参数要加、B 参数要减」。

### 方案 D：`tuning_result` 的独立处理（无争议，应必做）

`tuning_result == 'ineffective'` 意味着上一轮方向错了。当前代码会重复给出同一建议。

可选实现：
1. 把上一轮推荐过的参数从本轮候选中排除；
2. 对这些参数的调整方向取反；
3. factor 打折（接近方案 C，但只作用于这些参数）。

**前提**：引擎需要知道「上一轮推荐了什么」——`TuningRecord` / `Recommendation` 表里有，**但 context 没传**。

---

## 6. 待决问题

| # | 问题 | 影响面 |
|---|------|--------|
| Q1 | observations 采用方案 A / B / C？（或 B + D 组合） | 决定 FuzzyFeature 是否改造、规则库是否重建 |
| Q2 | `tuning_result == 'ineffective'` 采取排除 / 反向 / 打折？ | 需扩充 context（传上一轮推荐） |
| Q3 | `condition.py::_build_optimization_context` 这条路径是否还在用？若在，是否直接删除、统一到 `parameter_optimize`？ | 决定 S-1 的修法 |
| Q4 | 论域权威源定哪个：RuleKeyword 表 / specs 的 `max_set_*` / 兜底？ | 决定 S-5 修法，影响所有判级准确性 |
| Q5 | initialize 响应：保留 `process` 嵌套并**新增** flat 字段，还是直接把 `process` 换成 flat？ | 决定 D1 的兼容策略 |
| Q6 | fuzzy 与 empirical 的合并语义：按参数去重 / 数值优先 / 并列展示？ | 决定 S-7 修法 |

---

## 7. 建议的推进顺序

1. **D1 flat 统一**（纯契约改造，风险低，先落地）
2. **S-1 + S-2 统一 context 构造点并补 `iteration_trend`**（让引擎有一条确定的输入路径）
3. **Q1/Q2 定 observations / tuning_result 语义** → S-3 / S-4 接入
4. **S-5 论域统一**（影响判级准确性，是后续一切的前置）
5. S-6 / S-7 / S-8 收尾

---

## 附：本文所有代码事实的验证位置

| 事实 | 位置 |
|------|------|
| AlgorithmContext 5 键、无 iteration_trend | `backend/process/services/parameter_optimize.py` L81-103 |
| context 组装（子对象 + 已翻译） | 同上 L427-453 |
| 两套 context 分叉 | `backend/process/services/condition.py` L1070-1114 |
| trend 计算逻辑 | `backend/process/services/tuning.py` L289-355 |
| fuzzy 只取第一个缺陷 | `backend/process/algorithms/fuzzy/fuzzy_algorithm.py` L306-331 |
| 论域兜底 min=0/max=×2 | 同上 L360-392 |
| 合并与 confidence 公式 | 同上 L515-610 |
| 字段命名契约 | 同上 L70-187 |
| specs 论域上界声明 + TODO | `backend/process/algorithms/fuzzy/specs.py` L57-145, L303-311 |
| RuleKeyword 适配 | `backend/process/algorithms/fuzzy/adapters.py` L223-272 |
| Recommendation 无 rule_refs | `backend/process/algorithms/base.py` L31-67 |
| empirical 只给方向 | `backend/process/algorithms/empirical/empirical_algorithm.py`, `base.py` L45-47 |
| 嵌套→flat 拍扁逻辑 | `backend/process/services/parameter_initialize.py` L719-797 |
| observations schema（4 键） | `backend/process/schemas/optimization.py` L75-88 |
| 前端未回填 new_parameter | `frontend/src/views/process/optimization/pages/OptimizationCreate.vue` `getOptimizedProcess` / `makeRound` |
| flat 转换现状 | `frontend/src/views/process/optimization/components/parameterTransform.ts` |

---

## 8. 编排层流程定义讨论（第二轮）

### 8.0 北极星语义

> 输入（当前工艺参数 + 当前缺陷信息 + …）→ 推理 → 输出修正后的工艺参数。

一句话可说明，但落地拆分后每段细节不同。目标是：**先定 `parameter_optimize.py` L863-987 这段的大流程，每个环节职责单一、互不干扰**，再逐环节细化。

### 8.1 当前实际流程（含越界点）

```
infer(condition_id, parent_seq_idx, parameter, feedback)
 │
 ├─ Step 0  _validate_feedback(feedback)              纯校验
 │
 ├─ Step 1  _resolve_parent(...)                       读 DB
 │
 ├─ Step 2  _resolve_baseline(user_parameter, parent)  ⚠ F1 读基线却写库
 │           └─ setattr + save()                        （在 Step 5 事务之外）
 │              → baseline = _to_full_dict(parent)
 │
 ├─ Step 3  _extract_machine_info / polymer / mold     读 DB
 │
 ├─ Step 4  self._infer_kernel(...)                    纯推理，无 DB
 │           ├─ _compose_algorithm_context
 │           ├─ _call_algorithms
 │           ├─ fail-fast（原始输出为空即抛）              ⚠ F5 错误分类单一
 │           ├─ _normalize_recommendations             译名 / 丢零变化 / 写文案
 │           ├─ _apply_recommendations_to_baseline     → new_parameter_dict
 │           └─ _build_suggestion_payload              → suggestion_payload
 │
 ├─ Step 5  with db_transaction.atomic():
 │           ├─ 5.1 _update_previous_tuning_record       写【历史】
 │           ├─ 5.2 _update_previous_recommendation_is_adopted  写【历史】
 │           ├─ 5.3 _create_new_parameter                写【当前】
 │           ├─ 5.4 _create_new_tuning_record           写【当前】
 │           └─ 5.5 _create_new_recommendation          写【当前】
 │
 └─ Step 6  { new_parameter: {**new_parameter_dict, parameter_id, seq_idx}, ... }
             ⚠ F2 new_parameter_dict 是 baseline 全量快照 → 含父记录 id / created_at / param_source
```

### 8.2 越界点（环节互相干扰的具体证据）

| # | 越界 | 位置 | 后果 |
|---|------|------|------|
| F1 | Step 2「解析基线」里做 `save()` | L330-341 | 写操作在 Step 5 事务之外；Step 4 推理失败时 **parent_param 已被改写并落库**（用户手改的值留下，推理却"没发生"）；且篡改上一轮记录 → 历史不可复现 |
| F2 | Step 6 响应直接展开 baseline 全量 | L977-982 | `new_parameter` 含父记录的 `id` / `created_at` / `parameter_no` / `param_source`；而落库侧 `_create_new_parameter` 用 `_NON_SNAPSHOT_FIELDS` 过滤过 → **落库干净、响应带脏数据** |
| F3 | 落库的 `Recommendation` ≠ 返回的 `suggestion` | L970 vs L1094 | 落库用未按 baseline 过滤的 `algorithm_recommendations`，返回用过滤后的 → **存了库但没告诉用户的推荐** |
| F4 | Step 0 校验把「HTTP 表单约束」和「算法输入需求」混在一起 | L256-277 | `position` 必填是前端表单镜像，算法侧实际不使用（`_match_defect_level` 未消费 `defect_position`） |
| F5 | fail-fast 只报一种错 | L1079-1084 | 「规则库没匹配到规则」「算法内部异常被 `except Exception` 吞掉」「缺陷名缺失」三种原因统一报"算法暂不可用，请联系管理员" → 业务问题被误报为系统故障 |
| F6 | `_infer_kernel` 违反本文件自身约定 | 文件头 L17-18 vs L1031 | 约定"helper 全部为模块顶层函数"，实际 `_infer_kernel` 是类内 `@staticmethod`，且调用处写 `self._infer_kernel(...)`（L928 / L1016） |
| F7 | Step 5 内「更新历史」与「创建新记录」同生共死 | L941-974 | 5.4 失败 → 事务回滚 → 用户填的缺陷反馈与试模结果（5.1/5.2）**一并丢失**；而这恰恰是最不该丢的数据 |
| F8 | 同一份缺陷反馈被**两条路径重复写** | 后端 L754-782 vs `tuning.py` 的 tuning-feedback | 前端 `onSubmit()` → `POST /parameters/<id>/tuning-feedback/` 写当前轮次的 `TuningRecord`（含 `observations`）；`getOptimizedProcess()` → optimize 的 Step 5.1 又写**同一轮**的 `TuningRecord`（`defect_feedbacks` + `result`）——两者指向同一个 `ProcessParameter`，且 `observations` 只在前一条路径里 |

### 8.3 重组草案：6 个环节，职责单一

| 环节 | 职责（一句话） | 输入 | 输出 | 明确**不做**什么 |
|------|---------------|------|------|----------------|
| **E1 校验** | 判断 feedback 是否满足**算法**的输入需求 | feedback | 合法 feedback | 不做前端表单级校验（`position` 必填等归 pydantic schema） |
| **E2 取上下文** | 读 ORM，拿到 condition / parent / 3 维 info | condition_id, parent_seq_idx | condition, parent_param, machine/polymer/mold info | 不写库、不改数据 |
| **E3 定基线** | 算出本轮推理起点 baseline | user_parameter, parent_param | baseline（flat dict） | **不写库**（当前会 `save()`） |
| **E4 推理** | 算法算出推荐集，并算出修正后的完整参数 | baseline + feedback + 3 维 | (推荐集, 修正后参数) | 不写库、不感知 ORM |
| **E5 提交** | 把结果写进新一轮，并结算上一轮历史 | 推荐集 + 修正后参数 | new_param / TuningRecord / Recommendation | 不做算法判断、不做展示层组装 |
| **E6 组装** | 拼出响应 | 落库产物 + 推理产物 | 响应 dict | 不含父记录元数据 |

### 8.4 本轮待拍板（3 个，均在流程定义层，不涉及算法内部）

| # | 问题 | 我的倾向 |
|---|------|---------|
| Q1 | E3 是否保留在 parent 上 `save()` user_parameter？ | **不保留**。`new_parameter = baseline + 推荐` 落库后，用户改的值自然进了新记录，parent 上的 `save()` 是纯多余的写副作用，还会污染上一轮历史 |
| Q2 | E5 中「更新上一轮历史」与「创建新一轮」是否拆开？ | **拆开**。历史结算（缺陷反馈 + 试模结果）先独立提交，不与新记录创建同生共死 |
| Q3 | E6 的 `new_parameter` 是否清掉父记录元数据（id / created_at / param_source）？ | **清掉**，与落库侧口径一致；`parameter_id` / `seq_idx` 单独由 E6 追加 |

### 8.5 下一步

按 6 环节顺序逐个细化。本轮只定大流程 → 下一轮建议先定 **E1 + E3**（最小、最独立、争议最少），再进 E4（推理内部，含 observations / tuning_result 语义）。

---

## 9. E1 校验环节定稿（第三轮）

### 9.1 `position` 的定性澄清（用户）

> `position` = 缺陷出现在**产品的第几段**；因为是**多段注射成型**，反馈第几段是为了定位到
> **调整注射的对应第几段**。目前算法部分还没跑通，所以这个参数尚未被用上。

结论：**`position` 是算法输入（IF 条件变量），不是单纯的落库记录。**

数据模型侧已预留：

- `RuleKeyword.category = 'defect_position'`，共 **110** 个关键字，命名 `DL{defect}{N}`（如 `DLSHORTSHOT1~6`，见 `rule-keyword-import-design.md` §1.1）；
- `RuleKeyword.category` 的 help_text 明写「缺陷位置（IF）」——**位置在规则模型里本就是 IF 变量**；
- `parsing.is_position_name()`（L134-136）+ `collect_param_names()` 剔除 `DL*`——解析器已预期规则串会出现位置前件。

**但现状**：现有规则串里**没有一条带 `DL*` 前件**，规则结论的参数段是写死的：

```
IF WELDLINE_low  AND PP0_low THEN PP0_add_2
IF WELDLINE_high AND IP0_low THEN IP0_add_3.8
```

即「位置 → 调哪一段」目前靠规则把参数段写死来隐含表达，而不是由 position 参与匹配。

### 9.2 E1 定稿

> **E1 = 确认缺陷反馈能驱动一次有意义的推理。**

| # | 检查 | 性质 | 定稿 |
|---|------|------|------|
| 1 | `defect` 非空 list，每项是 dict | 结构 | ✅ 保留 |
| 2 | `keyword_name` 非空 | 算法必需（查规则的唯一键） | ✅ 保留 |
| 3 | `level` 非空 **且是合法档位词** | 算法必需（选哪套调整方案） | 🆕 **新增合法性校验** |
| 4 | `position` 非空 | 算法输入（IF 条件变量） | ✅ 保留，**不校验格式** |
| 5 | `DEFECTFREE` 跳过 3、4 | 前端不显示这两个输入框 | ✅ 保留 |

**净改动只有一处**：第 3 条加「合法档位词」校验。

依据：`normalize_level_word()`（parsing.py L123-131）只做 `mid → medium`，**不认识的词原样返回**。传进非法档位（如 `'严重'`）时，E1 放行 → 与规则库档位比不上 → 该缺陷的规则被全过滤 → 表现为「无可用规则」的 400，而不是「档位填错了」。校验直接用现成的 `is_level_word()`（L114-120）。

第 4 条不校格式的依据：位置 keyword 是**数据驱动**的（110 条，且随业务增长），前端还允许 `allow-create` 自由输入；后端硬校验格式会误伤。格式治理应在前端（选预设）或算法侧容错（匹配不上 → 视为「位置未知」，降级为不过滤位置）。

### 9.3 已达成共识的三点

| 场景 | 结论 |
|------|------|
| 多缺陷 | 用户可反馈多个缺陷，**修正有优先级，默认一次只修一个**。优先级 = `defect` 数组顺序（前端 `DefectFeedback.addDefect` 仅 push，无排序）。**需写进契约**：后端不排序，取第一个有 `keyword_name` 的项 |
| `level` 缺失 | **接口层必须校验**（前端 + 后端双校验）；**算法层允许降级**（`_match_defect_level` L241-242 已有 `if not context.defect_level: return True`） |
| 无缺陷 `DEFECTFREE` | **放行是对的**，返回什么内容**由算法给出**（E4 的职责）。但 E4 的 fail-fast 文案「推荐算法暂不可用，请联系管理员」需区分「无规则」与「引擎故障」（见 F5） |

### 9.4 留给 E4 的两条（本轮不处理）

1. **多缺陷「本轮修了哪个」没有回传前端** —— 响应里没有「本轮处理的是哪个缺陷、哪些待处理」，前端无法决定下一轮怎么接（否则用户重复填同样 3 个 → 永远只修第 1 个 → 死循环）。
2. **position 要真正参与推理，需要先定「位置 → 参数段」的承载方式**：
   - (a) 规则库新增位置前件（`IF SHORTSHOT_high AND DLSHORTSHOT3 AND IP0_low THEN IP3_add_10`）——工艺知识归规则库，算法保持纯函数；
   - (b) 算法侧维护「位置 keyword → 参数段」映射表。

   倾同 (a)，但这是独立决策。

### 9.5 已落地的改动（2026-10-22）

E1 定稿的**唯一净改动**：第 3 条「`level` 取值合法性校验」。

| 文件 | 改动 |
|------|------|
| `backend/process/algorithms/fuzzy/specs.py` | 新增缺陷程度词表契约：`_LEVEL_WORD_DISPLAY_ORDER`（语义顺序）、`VALID_DEFECT_LEVEL_WORDS`（完整有序元组）、`VALID_DEFECT_LEVEL_WORDS_TEXT`（展示文本，`level1~level9` 折叠为区间）、`is_valid_defect_level_word()` |
| `backend/process/algorithms/fuzzy/__init__.py` | 导出上述契约，供 service 层只依赖算法包公开表面 |
| `backend/process/services/parameter_optimize.py` | `_validate_feedback` 新增一条检查（缺失 → 非法）；docstring 重写，逐条标注校验的**算法侧理由** |
| `backend/tests/verify_validate_feedback_backend.py` | 新增 7 个用例（3 个非法档位拦截 + 4 个合法档位放行） |

**判据选择的两个要点**：

1. **用 `ALL_LEVEL_WORDS`（= `is_level_word`）而非 `HS_MAPPING_DICT` 的键**。后者只登记到
   `low/mid/medium/high + level1..level9`，拿它当校验基准会把前端 `LEVEL_WORDS` 5 档里的
   `very_low` / `very_high` 误判为非法，直接把用户挡在门外。
   且缺陷档位过滤（`_match_defect_level`）走 `normalize_level_word` 字符串比较、不查
   `HS_MAPPING_DICT`，因此 `very_low` 在过滤语义上完全正确，接口层不该拦。
2. **`HS_MAPPING_DICT` 缺 5/7 档是规则库侧的问题**（规则前件写 `X_very_low` 会在判级时 KeyError），
   属 P0-1 算法内核改造范围，**不在接口校验里兜**。接口层只管「输入是不是合法档位词」，
   不管「规则库有没有这一档」。

**测试**：`tests/verify_validate_feedback_backend.py` 23/23 PASS；
`tests/verify_fail_fast_infer.py` 2/2 PASS；`tests/verify_fuzzy_nested_context.py` PASS。

**前端无需改动**：`DefectFeedback.getLevelOptions` 的 level 取值来自固定词表 `LEVEL_WORDS[kw.fuzzy_level]`，
不存在自由输入，不会有非法值漏到后端。

---

## 10. Step 1（装配推理上下文）落地（2026-10-22）

### 10.1 合并：三个 Step → 一个 Step

原来 `infer()` 里的 Step 1/2/3 是三件事，但它们**是同一件事**——把库里读出来的东西
装配成算法要的输入。中间没有决策点，依赖关系也只是一根绳上的
（Step 2 要用 Step 1 的 `parent_param_orm`，Step 3 要用 Step 1 的 `condition_orm`）。

合并后：

```
Step 0  校验 feedback                    （E1，已落地）
Step 1  装配推理上下文（只读）             ← 本次
Step 2  纯推理
Step 3  原子事务落库
Step 4  组装响应
```

新增 `InferContext`（TypedDict）+ `_assemble_context()`，原三个 helper
（`_resolve_parent` / `_resolve_baseline` / `_extract_*`）降为子步骤。

### 10.2 写回时机的决策（B 方案）

**业务不变式：DB 里的记录必须等于用户实际在用的参数。**

这一条把问题从「记不记录用户改了什么」重新定义成了「DB 跟不跟得上实际」，
并暴露了一个缺口：**`tuning-feedback` 不写 `ProcessParameter`**，
所以只走【保存试模结果】这条路，参数改动是不落库的。

讨论过三个时机：

| 方案 | 内容 | 结论 |
|------|------|------|
| 挂【保存试模结果】 | 改 `tuning-feedback` 契约加 parameter | ❌ **不成立**——用户不会在调优化前先点保存试模结果，该路永远不触发 |
| 挂 infer + 事务外写 | 现状 | ❌ 会造出「参数改了但新轮次没建成」的中间态，且写在事务外无法回滚 |
| **挂 infer + 事务内写（B）** | 写回进 Step 3 事务 | ✅ **已定** |

选 B 的理由：
- infer 是第一个也是唯一接触用户改动的动作 → 写回只能挂它
- 「父记录改写」与「新建轮次」是同一件事的两面，必须同生共死
- 正常路径上 A/B 完全一致；差异只在推理失败时（B：DB 保持上一轮已确认状态，
  用户改动仍在前端 sessionStorage 草稿里，重试即同步）

**一个强论据支撑「必须写回父记录」**：用户把 `inj_pres_1` 从 80 改成 90、
算法建议改成 95 时，若不写回父记录，父记录还是 80、新记录是 95，
**用户那一步 90 在调机树里凭空消失**。写回后链路才是完整的（80→90 人工→95 系统）。

### 10.3 改动清单

| 文件 | 改动 |
|------|------|
| `backend/process/services/parameter_optimize.py` | ① 新增 `InferContext` + `_assemble_context()`（Step 1 编排）② `_resolve_baseline` 去掉 `save()`，改为返回 `(baseline, changed_fields)` ③ 新增 `_sync_user_modified_parameter()`（精确写回）④ `infer()` 重排 Step 1/2/3/4 ⑤ 文件头 docstring 更新 |
| `backend/tests/verify_fail_fast_infer.py` | mock `_resolve_baseline` 返回值改为 `({"dummy": 1}, {})` |
| `backend/tests/verify_user_parameter_sync.py` | **新增**：4 个用例专门验证写回时序 |

### 10.4 附带修掉的一个副作用

原 `_resolve_baseline` 把传入的所有非 None 字段都 `setattr` 一遍再 `save()`，
**值没变的字段也会被写**（触发 `updated_at` 变化 + 写放大）。

现在：Step 1 只在**值确实不同**时计入 `changed_fields`；
Step 3 用 `save(update_fields=[*changed_fields, "updated_at"])` 精确写回。

### 10.5 验证结果

| 测试 | 结果 |
|------|------|
| `verify_user_parameter_sync.py`（新增） | **ALL PASSED**（4 组用例） |
| `verify_validate_feedback_backend.py` | 23/23 PASS |
| `verify_fail_fast_infer.py` | 2/2 PASS |
| `verify_fuzzy_nested_context.py` | PASS |
| `verify_step1_full_dict.py` | PASS |
| `test_optimize_smoke.py` | PASS |
| `verify_provided_smoke.py` | PASS（FromProvided 路径不受影响） |
| `verify_parameter_tree.py` | All tests passed |

新用例的核心断言：
- 用例 1：Step 1 之后 DB 里该记录**未被修改**（只读）
- 用例 3：推理 fail-fast 时父记录**未被改写**、未创建新轮次
- 用例 4：推理成功后父记录 = 用户改后的值；新轮次 = 用户改后的值 + 算法推荐值

---

## 11. 推理链路实测复核（2026-10-22 下午）

### 11.1 结论：推理**已经跑通**，跑不通的是数值

用真实 DB 数据走完整 service 链路（`_dev_refs/diag_infer_e2e.py`）：

```
condition id=1  parameter id=1 seq_idx=1   polymer='PP'  product_category='包装'
machine_info 10 项 / polymer_info 7 项 / mold_info 2 项   ← 三维上下文齐全
→ ParameterOptimizeService.infer_from_provided() 正常返回
   new_parameter（52 字段，4 个被改） + suggestion（4 组，8 条）
→ suggestion.source_type = 'fuzzy'
```

**没有异常、没有 fail-fast、链路是通的**。之前「算法跑不通」的印象不成立。

### 11.2 但产出量级不可信

实测（defect=ABERRATION, level=low，命中 12 条规则）：

| 参数 | 规则写的调整量 | 实际推出 | 差 |
|---|---|---|---|
| IP0 (IP0_add_2) | +2.0 | **+0.0063** | 317× |
| MBP0 (MBP0_add_1) | +1.0 | +0.5074 | 2× |
| MSR0 (MSR0_reduce_2) | −2.0 | −0.4949 | 4× |
| IV0 (IV0_add_2 / IV0_reduce_2 同时命中) | ±2.0 | **0.0000** | 完全抵消 |

### 11.3 逐层拆解（`_dev_refs/diag_numeric_breakdown.py`）

归一化分母 `Σ激活度 = 1.1236`，**11 条规则共享**。

| 规则 | 原始激活度 | 归一化 | 结论 delta | 贡献 |
|---|---|---|---|---|
| `ABERRATION_low AND IP0_low THEN IP0_add_2` | 0.003536 | 0.003147 | +2.0 | **+0.0063** |
| `ABERRATION_low AND MBP0_low THEN MBP0_add_1` | 0.570182 | 0.507445 | +1.0 | **+0.5074** |
| `ABERRATION_low AND MBP0_high THEN MBP0_reduce_1` | 0.000003 | 0.000002 | −1.0 | −0.0000 |
| `ABERRATION_low AND IV0_high THEN IV0_reduce_2` | 0.135335 | 0.120444 | −2.0 | −0.2409 |
| `ABERRATION_low AND IV0_low THEN IV0_add_2` | 0.135335 | 0.120444 | +2.0 | +0.2409 |
| `ABERRATION_low AND BT_low THEN BT_add_2` | 0.000000 | 0.000000 | +2.0 | 0 |

### 11.4 四个根因（与 10-20 文档的 P0 对应，全部仍未修）

| # | 根因 | 今天实测的证据 |
|---|---|---|
| P0-1 | **档位映射错位一档**：`FUZZY_LEVELS[5]=['very_low','low','mid','high','very_high']`（桶 0..4），但 `HS_MAPPING_DICT` 是 3 档语义（`low→0`）。规则写 `IV0_low` 命中的是 **very_low** 桶 | `IV0=30`（域 0–120）的 5 档隶属度 = `[0.135, **1.000**, 0.135, 0.0003, 0]`；但规则 `IV0_low` 取到桶 0 → 0.135，`IV0_high` 取到桶 2 → 0.135。**两者完全对称**，说明命中的是「very_low」与「mid」，不是「low」与「high」 |
| P0-2 | **论域与真实值不符**：`RuleKeyword.range_min/max` 未校准 | `BT` 料筒温度论域 `[0,50]`、真实值 **250** → 5 档隶属度全 0 → 所有 BT 规则激活度恒为 0（`BT2` 的论域 `[150,350]` 是对的，说明 BT 是错的）。`NT` 喷嘴温度同病（`[0,50]` vs 250） |
| P0-3 | **全局归一化 + 直接累加**：分母是全部规则的激活度 | §11.3：IP0 的 +2.0 被摊成 +0.0063 |
| P0-4 | **跳库副本未去重** | 1643 条活跃规则里 **359 组重复、涉及 1062 条记录**；`IF SHORTSHOT_low AND MEL_low THEN MEL_add_2` 一个规则串存在 **7 份** |

### 11.5 修复顺序（沿用 10-20 文档 §5.7）

| 阶段 | 内容 | 依赖 | 本轮状态 |
|---|---|---|---|
| 阶段 1 | P0-1 档位映射 + P0-2 论域校准 | 无 | **待做** |
| 阶段 2 | P0-3/P0-4 分组归一化 + 加权平均 + 跳库去重 | 阶段 1 | 待做（会改变输出量级，需与工艺员对量级） |
| 阶段 3 | P1-1 缺陷档位权重 + 激活度阈值 + confidence 语义 | 阶段 2 | 待做 |

10-20 文档原话：「**阶段 1 是‘止损’**：在档位映射与论域修正之前，所有调参都是在拟合一个错误的激活函数。」

### 11.6 诊断脚本（可重跑）

| 脚本 | 用途 |
|---|---|
| `backend/_dev_refs/diag_fuzzy_pipeline.py` | 规则库体检（数据量 / 前件形态 / 论域 / 命中规则） |
| `backend/_dev_refs/diag_infer_e2e.py` | 走真实 service 链路的端到端推理 |
| `backend/_dev_refs/diag_numeric_breakdown.py` | 数值层逐层拆解（隶属度 → 激活度 → 归一化 → delta） |

---

## 12. 算法语义审计：它算的东西是不是业务要的

> 起因：用户指出「当前最大的问题在于推理算法部分，并不一定符合要求」。
> §11 查的是「跑不跑得通」，本节查的是「算得对不对」。

### 12.1 引擎实际消费了上下文的 4 个字段，其余 13 个白拿

`AlgorithmContext` 声明 5 个维度，service 层确实从 DB 抽了完整三维上下文。

| 引擎实际读的 | 抽了但没读的 |
|---|---|
| `polymer_info.abbreviation` | `machine_info` 全部 10 项（含 6 个 `max_set_*` 设备上限） |
| `mold_info.product_category` | `polymer_info` 6 项（`min/max/recommended_melt_temp`、`min/max_mold_temp`） |
| `feedback.defect[0]` | `mold_info.target_cycle_time` |
| `process_parameter` | `feedback.observations` / `tuning_result` / 第 2 条起缺陷 |

> `machine_info` 在整个 `fuzzy/` 包里只出现 2 次：`specs.py` 定义处 + `fuzzy_algorithm.py` docstring。
> **没有一行代码读它。**

### 12.2 契约已经写好了，引擎没实现

`specs.py` L23-29（2026-10-15 结论）：

> 设备设定上限要标「必填」……上界一旦缺失，算法退回到「当前值×2」自造区间，后果是：
> 同一套参数在 180MPa 与 350MPa 的两台机上被判成同一模糊等级 → 前件命中失真；
> 推荐值可能超出这台机 HMI 能设定的物理范围，操作工根本输不进去。
> 所以「不传设备上限」不是精度略降，而是**结论不可信**。

`specs.py` L170：

> **熔体温度边界（料筒/喷嘴推荐值的物理上界来自材料，不来自机器）**

材料熔体温度窗口（`polymer_info.min/max_melt_temp`）是料筒/喷嘴推荐值的物理上界来源，
但引擎当前不消费这个窗口：`polymer_info` 里抽出来的材料温度上下限没有进入任何
判级、激活度或推荐值计算；建议值也不做上下界校验，按
`recommended_value = current_value + adjusted_delta` 直接返回。

### 12.3 四条业务语义硬伤

| # | 硬伤 | 实证 |
|---|---|---|
| A | **「低/高」的基准是全局量程，不是这个产品该有的正常区间** | 论域只来自 `RuleKeyword.range_min/max`（静态、全库一套）。同一个 `IV0=30 mm/s`，在「包装」与「汽车内饰件」两个产品上得到同一判定——而规则库本来就按 polymer × product 分库，分库只解决了「规则集合不同」，没解决「低高的标准不同」 |
| B | **设备上限没进论域** | `max_set_injection_pressure` 标着「必填 / 注射压力类论域上界」，引擎不读 → 100 MPa 的机与 350 MPa 的机判成同一档 |
| C | **材料温度天花板没被消费** | PP 的 `max_melt_temp=280`，引擎不读 → 料筒温度建议可开到 350℃（烧焦料） |
| D | **建议值不做可行性校验** | `recommended_value = current_value + adjusted_delta` 算完直接返回，全包 0 处 clip/clamp。`MBP0` 论域 `[10,50]`、当前值 4.7 已在论域外，引擎照样推理、照样给建议 |

### 12.4 三个契约层问题（先记着，暂不展开）

| # | 问题 | 表现 |
|---|---|---|
| E | **规则的 level 词空间 > 引擎支持的词空间** | 前端 `RuleMethodForm.vue` 按 `fuzzy_level` 动态取 `LEVEL_WORDS`（3/5/7/9 档），写出的 `very_low/very_high` 引擎不认（`HS_MAPPING_DICT` 只有 low/mid/medium/high + level1..9） |
| F | **缺陷档位可选 5 档，规则库只有 3 档** | `DefectFeedback.vue` 按 `kw.fuzzy_level=5` 给出 5 个选项，用户选 `very_high` → 规则库里无此档 → 0 条规则 → 400「无可用规则」 |
| G | **多缺陷只取第 1 个** | `_extract_defect_context` 只看 `feedback['defect'][0]` |

### 12.5 待拍板的地基问题

> **“注射速度偏低”是相对什么低？**

| 候选基准 | 适用 | 代价 |
|---|---|---|
| 设备 HMI 上限（`max_set_*`）+ 0 | 压力 / 速度 / 转速类 | 温度类不成立（温度上限来自材料） |
| 材料窗口（`polymer.min/max_melt_temp`） | 温度类（料筒 / 喷嘴 / 模温） | 需要材料主数据完整 |
| 该产品 × 该材料的历史分位数 | 最贴近「低/高」的业务含义 | 依赖历史数据量；本库 `ProcessParameter` 仅 49 条 |
| 现状：`RuleKeyword` 静态量程 | 无 | 一个标准走天下 |

**§12.1–12.4 的全部问题都从这一条派生**：论域定了，判级、激活度、调整量、可行性校验才有意义。


