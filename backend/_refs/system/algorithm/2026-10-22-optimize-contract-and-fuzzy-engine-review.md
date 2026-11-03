# 工艺优化链路契约与模糊推理引擎现状走查

- 日期：2026-10-22
- 前置文档：`2026-10-20-fuzzy-inference-review-and-roadmap.md`（模糊推理评估与改良路线）
- 性质：**讨论记录**。本文只记录已核实的代码事实与待决问题，不含实现改动。

---

## 0. 已确认的决策（跨轮累积）

| # | 决策 | 状态 |
|---|------|------|
| D1 | 初始化参数（initialize）响应改为 **flat 格式**，与 optimize 的 `new_parameter` 对齐；参数形态转换统一由前端负责 | ✅ 用户已认可 |
| D2 | `observations` 与 `tuning_result` 需参与模糊推理 | ✅ 用户已认可（语义待定） |
| D3 | 模糊推理引擎现状需先讨论清楚再改造 | 🔶 进行中 |
| D4 | 多引擎结果处理：**汇总后选优**（经验推理只作兜底 —— 模糊推理有产出就用模糊推理的） | ✅ 用户已认可（2026-10-28，实施记录见 §14） |
| D5 | optimize 路径数值精度：**值层统一量化到 2 位小数**（与建议文案口径一致；不采用量化 delta 方案） | ✅ 用户已认可（2026-10-28，实施记录见 §15） |
| D6 | 模糊推理走查沉淀为**可离线复现的案例数据集**（`process/algorithms/fuzzy/examples/`）：真实案例输入 + 期望输出 + 离线 runner | ✅ 用户已认可（2026-10-28，实施记录见 §16） |

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

   > ⚠️ **状态已更新（2026-10-28）**：
   > ① **P0-1 已修**（E2）—— 全局表已弃用，档位→桶改为按**字段自身词表**定位，
   >    `X_very_low` 在 5 档字段上正常落桶；若在 3 档字段上**填不进**，
   >    按「**整条规则激活度 0**」处理（不再 KeyError，也**不再**「只跳过该前件」）。
   > ② 「**规则库侧的问题**」这一定性**有误** —— 实测规则库侧**零缺陷**
   >    （全库 3440 个可判级前件与所属参数档位数**零不兼容**）；病根在**引擎解释层**
   >    用了全局静态表。见 `2026-10-22-fuzzy-engine-design-defect-review.md` §1.2.3。

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

### 11.4 四个根因（与 10-20 文档的 P0 对应）

| # | 根因 | 今天实测的证据 |
|---|---|---|
| P0-1 | **档位映射错位一档**：`FUZZY_LEVELS[5]=['very_low','low','mid','high','very_high']`（桶 0..4），但 `HS_MAPPING_DICT` 是 3 档语义（`low→0`）。规则写 `IV0_low` 命中的是 **very_low** 桶 | `IV0=30`（域 0–120）的 5 档隶属度 = `[0.135, **1.000**, 0.135, 0.0003, 0]`；但规则 `IV0_low` 取到桶 0 → 0.135，`IV0_high` 取到桶 2 → 0.135。**两者完全对称**，说明命中的是「very_low」与「mid」，不是「low」与「high」 |
| P0-2 | **论域与真实值不符**：`RuleKeyword.range_min/max` 未校准 | `BT` 料筒温度论域 `[0,50]`、真实值 **250** → 5 档隶属度全 0 → 所有 BT 规则激活度恒为 0（`BT2` 的论域 `[150,350]` 是对的，说明 BT 是错的）。`NT` 喷嘴温度同病（`[0,50]` vs 250） |
| P0-3 | **全局归一化 + 直接累加**：分母是全部规则的激活度 | §11.3：IP0 的 +2.0 被摊成 +0.0063 |
| P0-4 | **跳库副本未去重** | 1643 条活跃规则里 **359 组重复、涉及 1062 条记录**；`IF SHORTSHOT_low AND MEL_low THEN MEL_add_2` 一个规则串存在 **7 份** |

> ⚠️ **状态已变（2026-10-28 更新）**：上表的「今天实测的证据」是 **2026-10-22 当时的快照**，
> 保留用于追溯。四个根因现均已处理：
>
> | 根因 | 现状 | 依据 |
> |---|---|---|
> | P0-1 档位映射错位一档 | ✅ **已修** | E2：`resolve_bucket` 改为**按字段自身词表定位**（`2026-10-22-fuzzy-engine-paradigm-decision.md`） |
> | P0-2 论域与真实值不符 | ⚠️ **部分做** | `2026-10-27` 文档 §18.3：设备实测值补全论域上界 + 推测论域 `lvl` 3→5 + `step` 随跨度；**经验域本身未校准** |
> | P0-3 全局归一化 + 直接累加 | ✅ **已修** | `2026-10-27` 文档 批 B：分组归一化 + 组内加权平均 + 绝对激活度下限 |
> | P0-4 跳库副本未去重 | ✅ **已修** | `RuleAssembler` 跨库副本去重 |
>
> 当前状态与遗留待办见 §11.5。

### 11.5 修复顺序（沿用 10-20 文档 §5.7）

| 阶段 | 内容 | 依赖 | 本轮状态 |
|---|---|---|---|
| 阶段 1 | P0-1 档位映射 + P0-2 论域校准 | 无 | P0-1 ✅ **已修**（E2，档位→桶按字段词表定位）；P0-2 ⚠️ **部分做**（设备值补论域上界 + 推测论域 `lvl` 3→5；经验域未校准） |
| 阶段 2 | P0-3/P0-4 分组归一化 + 加权平均 + 跳库去重 | 阶段 1 | ✅ **已做**（批 B 分组归一化/加权平均/绝对激活度下限 + `RuleAssembler` 去重）。**已改变输出量级**（旧版建议被全局分母压成 1/N，新版恢复作者所写量级），已与工艺员对过量级 |
| 阶段 3 | P1-1 缺陷档位权重 + 激活度阈值 + confidence 语义 | 阶段 2 | 激活度阈值 ✅ **已做**（绝对激活度下限 `MIN_ACTIVATION_THRESHOLD`）；confidence 语义 ✅ **已做**（置信度用**原始激活度**，不含 priority/specificity 乘数）；**P1-1 缺陷档位权重 ❌ 待做**（当前口径：档位进推理网络、不再硬过滤，且**不额外加权**） |

10-20 文档原话：「**阶段 1 是'止损'**：在档位映射与论域修正之前，所有调参都是在拟合一个错误的激活函数。」

> ✅ 阶段 1 的「止损」已完成（档位映射）。**当前遗留待办只有 P0-2 经验域校准与 P1-1 缺陷档位权重**。
> ⚠️ 另有一项**新增待办**（2026-10-28）：改 `fuzzy_level` 时应提示「引用该关键字的 N 条规则门槛会变」——
> 当前完全静默。详见 §17.4 第 2 条与 `_refs/system/algorithm/fuzzy-level-semantics-design.md`。

### 11.6 诊断脚本（⚠️ 脚本已删除）

> ⚠️ **2026-10-28 核对**：以下 3 个脚本已随 commit `f181df6` 一次性清理，
> **当前仓库中不存在**（`_dev_refs/` 下已无任何 `diag_*` 文件）。表中结论仍然有效，
> 但**不能直接复跑**。

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
| E | **规则的 level 词空间 > 引擎支持的词空间** | 前端 `RuleMethodForm.vue` 按 `fuzzy_level` 动态取 `LEVEL_WORDS`（3/5/7/9 档），写出的 `very_low/very_high` 引擎不认（`HS_MAPPING_DICT` 只有 low/mid/medium/high + level1..9）<br>✅ **已修（2026-10-23，E2）**：全局表已弃用，档位→桶按**字段自身词表**定位；填不进词表时**整条规则激活度 0**，不报错、不中断 |
| F | **缺陷档位可选 5 档，规则库只有 3 档** | `DefectFeedback.vue` 按 `kw.fuzzy_level=5` 给出 5 个选项，用户选 `very_high` → 规则库里无此档 → 0 条规则 → 400「无可用规则」<br>✅ **已修（`2026-10-27` 文档 批 C4）**：缺陷档位**不再硬过滤**，档位进推理网络由激活度承担 |
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

---

## 13. D1 实施记录：flat 契约统一（2026-10-28）

> §0 的 D1 决策在 2026-10-22 已拍板、§2.2 也给出了改造点清单，但**一直没有实施**。
> 本节记录 2026-10-28 的实施：触发症状 → 根因 → 改动 → 验证 → 遗留。
> 本文性质从「纯走查」升级为「走查 + 施工日志」，§1~§12 的内容仍是评审当时状态的快照。

### 13.1 触发症状

前端「智能调机」页提交优化后：

- `POST /api/processes/algorithms/optimize/` 返回 **200**；
- 底部「上一轮调整建议」**正常渲染**（如「注射参数 → 提高一段注射速度：30 → 32」）；
- 但**工艺参数表格整片空白**。

即：接口通、建议有，唯独参数表没有值。

### 13.2 根因（三层叠加，缺一不可）

| # | 位置 | 事实 |
|---|------|------|
| 1 | `OptimizationCreate.vue::getOptimizedProcess` | 只从 `new_parameter` 取 `parameter_id` / `seq_idx` 两个元数据字段，**其余 88 个工艺字段全部丢弃** |
| 2 | `OptimizationCreate.vue::makeRound` | 新轮次的 `parameter` 来自 `structuredClone(settingProcessForm)` —— **全 null 空模板**；表格 `:setting-process="activeRound.parameter"` 绑的就是它 |
| 3 | 形状不匹配 | 后端 `new_parameter` 是 **flat**（`inj_spd_1`…），前端表格要的是 **nested**（`table_data[].sections[]`）；`parameterTransform.ts` 注释里指向的 `parameterFromFlat` **从未实现**，取而代之的 `mapInferResultToParameter` 读的是 initialize 形态的 `result.process.inj_pres_steps` |

因为 `hasNewParameter` 只校验 `parameter_id != null`，**结构不匹配不会报错** —— 接口 200、参数表静默空白。

### 13.3 关键澄清：不是 key 名问题，是形状问题

曾考虑把响应字段从 `new_parameter` 改名为 `parameter`（与 initialize 命名对齐）。**结论：不可改**：

- `OptimizationCreate.vue` L751 硬编码读 `inferData.new_parameter`；改 key 会走到「推荐算法暂不可用，请联系管理员」的分支并 `return`，**连建议都不显示** —— 比现状更糟；
- 要对齐的是**值的形状**（flat ↔ nested），不是 key 名。响应字段名保持 `new_parameter` / `result.process` 不变。

### 13.4 改动清单

**后端** `backend/process/services/parameter_initialize.py`：

| 位置 | 改动 |
|---|---|
| L737-762 | 抽出模块级 `_FLAT_SINGLE_VALUE_FIELDS`（25 个单值字段）/ `_FLAT_STEPS_MAPPINGS`（11 组段位映射） |
| L765 | 抽出纯函数 `process_params_to_flat(proc_dict) -> Dict[str, Any]`（nested → flat） |
| L815 | `_create_process_parameter` 改为 `{..., **process_params_to_flat(proc_dict)}` —— 落库字段集合**零变化** |
| L508 / L649 | `infer`（from_masterdata）与 `infer_from_provided` 的 `result['process']` 统一替换为 flat |

`_infer_kernel` 内部**保持 nested**（算法侧零改动），只在**响应边界**拍扁。

**前端** `frontend/src/views/process/optimization/components/parameterTransform.ts`：

| 位置 | 改动 |
|---|---|
| L46 | `import { settingProcessForm }` —— 由 `import type` 改为**值导入**（见 §13.6） |
| L326-410 | 新增 `parameterFromFlat(flat) -> SettingProcessForm` —— flat → nested 唯一翻译器 |
| L418-430 | 新增 `PROCESS_FLAT_FIELDS`（83 个工艺字段白名单） |
| L438-442 | 新增 `hasFlatParameterContent(flat)` —— 响应内容有效性校验 |

**前端** `frontend/src/views/process/optimization/pages/OptimizationCreate.vue`：

| 位置 | 改动 |
|---|---|
| L213 | import 补 `parameterFromFlat` / `hasFlatParameterContent` |
| — | **删除** `padSteps`（11 行）与 `mapInferResultToParameter`（79 行），净减 93 行 |
| L603 | `applyInferResultToForm`：`activeRound.parameter = parameterFromFlat(data.process)` |
| L756 | `getOptimizedProcess`：`newRound.parameter = parameterFromFlat(inferData.new_parameter)` |
| L758-760 | 响应无工艺内容时 `ElMessage.warning` 提示，避免再次静默空白 |

### 13.5 顺带修正：料筒温度段位错位一格

后端 nested 的 `brl_temp_steps[0]` 是**料筒 1 段**，前端 nested 的 `sections[0]` 是**喷嘴** —— initialize 路径的温度表整体错位一格（料筒 9 落在「8 段」列）。

统一 flat 后 `noz_temp` 与 `brl_temp_1..9` 成为两个独立字段，歧义消失：前端 `sections = [noz_temp, brl_temp_1..9]`，与 `parameterToFlat` 严格互逆（实测往返 44 个非 null 工艺字段完全一致）。

### 13.6 踩坑：`import type` 的运行时陷阱

`parameterTransform.ts` 原为 `import type { settingProcessForm }`（编译期擦除）。新增的 `parameterFromFlat` 需要它作为**运行时模板底**（label / unit / max_stage）⇒ 运行时 `ReferenceError: settingProcessForm is not defined`。

⚠️ **`vue-tsc --noEmit` 不报错**（type-check EXITCODE=0）—— 这是 type-check 的覆盖盲区，最终由 node 真代码验证脚本抓到。
**涉及运行时值的新导入，必须有运行时实测兜底。**

### 13.7 验证矩阵

| 层 | 脚本 | 结果 |
|---|---|---|
| L1 离线 | `backend/tests/verify_fuzzy_algo_offline.py` | 37 项断言 PASS |
| L2 连 DB | `backend/tests/verify_fuzzy_algo_db.py` | D1~D6 全过；实测产出 `inj_spd_1: 32.0 → 34.0`（正是空白那一格） |
| flat 映射 | `backend/tests/verify_initialize_flat.py` | A1~A5 / B1~B3 / C1 全过（落库字段 == 响应 flat） |
| 回归 | `backend/tests`（pytest） | **19 passed** |
| 契约回归 | `verify_bug2_tuning_record.py` / `verify_provided_smoke.py` | EXITCODE=0 |
| 前端类型 | `npm run type-check` | EXITCODE=0 |
| 前端真代码 | `frontend/scripts/verify-param-from-flat.mjs` | 5 项断言 PASS（含 flat → nested → flat 往返一致） |

### 13.8 遗留

| # | 项 | 说明 |
|---|---|---|
| 1 | 建议数值量级 | §11~§12 的 P0-1~P0-4 未动；本次只保证「值能正确送达前端」 |
| 2 | `new_parameter` 带父记录元数据 | §8.2 F2 未修（响应仍含 `created_at` / `param_source` 等） |
| 3 | `source_type` 与 schema 描述不符 | §1.3 S3 未修 |
| 4 | eslint 配置本身损坏 | `.eslintrc.json` 的 `indent` 规则值 `{"SwitchCase":1}` 非法 ⇒ 项目 lint 命令跑不起来（与本次改动无关） |


## 14. 多引擎结果处理：由「并列合并」改为「汇总选优」（2026-10-28）

> 触发：用户在智能调机页看到「上一轮调整建议」里同一参数出现两条
> （「模糊推理建议提高一段注射速度：30 → 32」+「经验推理建议提高一段注射速度」）。
> 结论：**问题不在前端展示，而在编排层的结果处理策略**。

### 14.1 症状

用户看到 7 条建议（注射参数 5 条 + 保压参数 2 条）：

| # | 文案 | 来源 | 有无数值 |
|---|---|---|---|
| 1 | 模糊推理建议提高一段注射速度：30 → 32 | fuzzy | 有 |
| 2 | 模糊推理建议提高注射时间：4 → 4.5 | fuzzy | 有 |
| 3 | 经验推理建议提高一段注射压力 | empirical | 无 |
| 4 | 经验推理建议提高一段注射速度 | empirical | 无 |
| 5 | 经验推理建议提高注射时间 | empirical | 无 |
| 6 | 模糊推理建议提高一段保压速度：24 → 26 | fuzzy | 有 |
| 7 | 模糊推理建议提高一段保压压力：44 → 46 | fuzzy | 有 |

其中 #4 / #5 与 #1 / #2 **是同一参数**（`inj_spd_1` / `inj_t`）—— 既是重复，也可能方向相反。

### 14.2 两层「聚合」的语义差异

走查发现建议里其实有两层含义完全不同的聚合：

| 层 | 位置 | 语义 | 产物形态 |
|---|---|---|---|
| fuzzy 内部 | `fuzzy/fuzzy_core/models/nets.py::tsk_inference` + `fuzzy/recommendations.py::aggregate` | **真聚合**：同参数的多条规则按「组内占比」加权平均（占比和恒为 1 ⇒ 裸累加 ≡ 加权平均） | 每个参数 **1 条**带数值的建议 |
| 引擎之间 | `parameter_optimize._call_algorithms` | **无聚合**：`all_recommendations.extend(recs)` 直接拼接，fuzzy 与 empirical 并列 | 同一参数可能 **多条** |

⇒ 用户看到的 7 条 = **4 条 fuzzy 参数级聚合结果 + 3 条经验查表条目**，不是 7 条规则。

经验引擎本身也没有聚合能力：`empirical_algorithm.py::recommend` 只按 `EMPIRICAL_HINTS[首个缺陷]`
逐条列出 `increase/decrease` 的参数码，`recommended_value=None`（经验只给方向、不给数）。

### 14.3 决策（用户拍板，2026-10-28）

> 「经验推理只作为兜底，目前我们如果模糊推理有结果就用模糊推理就可以，逻辑简单即可」

⇒ 引擎层**仍然并行调用**（各引擎各自算，互不阻塞），但**结果必须经选优收敛成唯一一份**。
与既有「多引擎并行调用策略」的差异只在**结果处理**这一步，调用策略不变。

| 候选策略 | 处置 |
|---|---|
| 展示层去重（同一参数已有数值建议就丢掉经验项） | ✗ 未采纳 —— 展示层 hack，语义仍是「并列」 |
| 改 `empirical.is_available` 让它只兜底 | ✗ 未采纳 —— `is_available` 在调用**前**判断，那时还不知道 fuzzy 有没有结果，做不到 |
| **汇总后按引擎优先级选优** | ✅ **已实施** |

### 14.4 实现

新增 `parameter_optimize._select_algorithm_result(algorithm_sources)`，
`_call_algorithms` 的合并动作由「extend 全量」改为「取优先级最高的那个有产出的引擎」：

```python
for subtype, payload in sorted(
    algorithm_sources.items(),
    key=lambda kv: AlgorithmRegistry.get_priority(kv[0]),
):
    if payload:
        return payload
return []
```

- 优先级沿用既有约定 `AlgorithmRegistry._priorities`：fuzzy=1 → llm=2 → empirical=3
- `algorithm_sources` 仍保留**全部**引擎产出（供 `_resolve_primary_source` 判定 `source_type` + 日志留痕）
- 落选引擎的产出不再进入建议集 ⇒ 落库的 `Recommendation.recommendations`、
  响应 `suggestion.groups`、参数改值三处口径统一

**改动面**：仅 `backend/process/services/parameter_optimize.py`（一个 helper + `_call_algorithms` 内部一处）。
前端零改动（`PreviousSuggestion.vue` 只渲染后端拼好的 `description`）。

### 14.5 安全性：参数结果不受影响

经验推理项本就没有 `recommended_value`，`_apply_recommendations_to_baseline` 早就跳过它们
⇒ 选优只影响「建议集」，`new_parameter` 逐字段不变。

实测对拍（一次性脚本，用完即删）：

| 场景 | 各引擎原始产出 | 选优后 | new_parameter 差异 |
|---|---|---|---|
| fuzzy 有产出 | `{'fuzzy': 5, 'empirical': 3}` | 5 条全 fuzzy，建议列表已无「经验推理」文案 | **无** |
| fuzzy 无产出 | `{'fuzzy': 0, 'empirical': 3}` | 3 条全 empirical，`source_type` 自动变 `empirical` | 不适用（经验项本就无数值） |

回归：`pytest tests -q` ⇒ **19 passed**（改造前同样 19 passed）。

### 14.6 遗留

| # | 项 | 说明 |
|---|---|---|
| 1 | `source_type` 与 schema 描述不符 | §1.3 S3 仍未修；`Recommendation.SOURCE_TYPE_CHOICES` 是 `fuzzy_rule`，而落库值是 `fuzzy`（既有不一致，本次未动 —— `source_type` 仍取 `_resolve_primary_source` 的结果） |
| 2 | 落选引擎的产出不再进库 | 只存在于进程内的 `algorithm_sources` 与选优日志里（`algorithm_sources` 不落库）；如需按引擎做效果对比，需另加留痕字段 |
| 3 | 建议数值量级 | §13.8 遗留 1 仍未动 |
| 4 | 缺陷程度档位偏低 | 实测 `level='high'` → 缺陷维度取值 `0.75`；用户当时的日志是 `{'SHORTSHOT': 0.0}` ⇒ 填的不是 high 档，值得确认前端的缺陷程度取值 |


## 15. optimize 路径数值精度：值层量化（2026-10-28）

> 触发：用户在智能调机页看到参数表里出现 `32.053805467920334` 这类浮点尾数。
> 结论：**不是精度溢出，是量化口径缺失** —— 建议文案量化了，参数值没有。

### 15.1 症状

参数表里 5 个被调整的字段：

```
32.053805467920334 / 4.52980073050553 / 6 / 46.11920292202212 / 26.11920292202212
```

而同一轮的**建议文案**是正常的：「模糊推理建议提高一段注射速度：30 → 32.05」。
⇒ 同一件事，**两处口径不一致**。

### 15.2 根因（三层）

| 层 | 事实 | 位置 |
|---|---|---|
| 算法层 | 推荐值 = `当前值 + Σ(规则结论值 × 组内占比)`，加权平均的产物天然带长小数 | `fuzzy/recommendations.py::to_recommendations` |
| 文案层 | 建议文案走 `_format_value`（最多 2 位小数）⇒ 文案正常 | `parameter_optimize._format_value` |
| **值层** | `new_parameter` 是全精度 float 直接透传，且 `_create_new_parameter` 原样落库 ⇒ 参数表与 DB 都是脏的 | `parameter_optimize._apply_recommendations_to_baseline` / `_create_new_parameter` |

⇒ **呈现层量化了，值层没量化**。

### 15.3 存量影响面（DB 查证）

`ProcessParameter` 共 57 行，逐字段统计：

| 字段 | 非整数行数 | 超过 2 位小数行数 |
|---|---|---|
| `inj_spd_1` | 1 | 1 |
| `inj_t` | 18 | 1 |
| `hold_pres_1` | 1 | 1 |
| `hold_spd_1` | 1 | 1 |
| `inj_pres_1` | 0 | 0 |

⇒ **只有最新一轮（模糊推理产出）是脏的**；历史轮次来自专家引擎（initialize），本来就是整数/短小数。
⇒ initialize 路径**不需要**额外处理。

### 15.4 决策（用户拍板，2026-10-28）

| 项 | 取值 | 说明 |
|---|---|---|
| 精度口径 | **2 位小数** | 与建议文案 `_format_value` 现有口径完全一致 ⇒ 文案与参数表数字长得一样 |
| 改造范围 | **只改 optimize 路径** | 存量数据显示 initialize 历史产出本来就干净 |

被否方案：

- **量化 delta**（在 fuzzy 的 `to_recommendations` 里先 round 调整量）⇒ 能得到整数档（`30 → 32`），更符合工艺心智，但改的是**算法输出语义**
- **两条路径都加** ⇒ initialize 无实际脏数据支撑，改动面无谓扩大

### 15.5 实现

新增 `parameter_optimize._quantize_numeric_fields(params, ndigits=2)`，
在 `_apply_recommendations_to_baseline` 返回前调用 —— 该函数是 optimize 路径**唯一的值出口**
（落库 `_create_new_parameter` 与响应 `new_parameter` 同源于此）⇒ 量化一次，DB / 响应 / 文案三处对齐。

细节：

- 只动**数值**字段；`str` / `datetime` / `None` 原样保留
- `bool` 是 `int` 的子类，必须先排除（否则 `True` 被量化成 `1`）
- `-0.0` 归一为 `0.0`（否则渲染成 `-0`）
- 作用于**整个返回 dict**（不只是被覆盖的字段）⇒ 存量脏 baseline 会在下一轮被自动洗白，不需要清库

### 15.6 验证

| 项 | 结果 |
|---|---|
| 量化函数单元行为 | `32.053805467920334 → 32.05`；`bool` 不受影响；`-0.001 → 0.0` |
| 端到端精度 | `new_parameter` 全部字段 ≤ 2 位小数 |
| 存量脏值洗白 | 脏 baseline → 输出已量化 |
| 文案一致性 | 「84 → 86.12」与参数表 `86.12` 逐位一致 |
| 回归 | `pytest tests -q` ⇒ **19 passed** |

### 15.7 遗留

| # | 项 | 说明 |
|---|---|---|
| 1 | 用户手改参数的精度 | `_sync_user_modified_parameter` 写回父记录不经过量化入口 ⇒ 用户手输什么就存什么（属用户输入，不处理） |
| 2 | 存量脏记录 | 库中仍有 1 条带长小数的记录（当场跑的那轮）⇒ 下一轮推理时会被自动洗白；不主动改历史数据 |
| 3 | 建议数值量级 | §13.8 遗留 1 仍未动（那是“调整量是否合理”，本节是“小数位”） |

---

## 16. 模糊推理输出内容走查 + 案例数据集（2026-10-28）

> 触发：用户问「模糊推理推荐的规则是什么逻辑？是聚合输出吗？就是一次根据几条规则输出给出调整结果？」
> ⇒ 本节把**算法输出内容**逐层拆开（基于真实数据实测），并沉淀为可离线复现的案例数据集。

### 16.1 结论：聚的是「同一个参数的多条规则」

不是「一条规则 → 一条建议」，而是：

```
规则库 1643 条（全库：base 585 + 9 个补充库 1058）
   ↓ 按缺陷+材料+产品 匹配谓词 + 跨库副本去重
本次进池 30 条（SHORTSHOT，特异级全是 4=通用）
   ↓ 前件隶属度连乘 → 激活度 → 两道闸 → 按「输出参数」分组归一化
命中 10 条
   ↓ 同参数 delta 累加（组内占比和=1 ⇒ 等价加权平均）
5 组
   ↓ 每组 1 条建议
5 条建议（每参数 1 条）
```

**「一次根据几条规则输出」要拆成两层看**：

| 层 | 事实 |
|---|---|
| 算法层 | 一次推理**命中 10 条**规则，这 10 条**确实同时参与**计算 |
| 输出层 | 10 条**不变成 10 条建议**，而是按「结论参数」**折叠成 1 条**（本次 10 → 5） |

⇒ 命中数 ≠ 输出数；每条建议背后是 1~3 条规则的加权结果。

### 16.2 五层流水线（实测）

| 层 | 位置 | 做什么 | 本次实测 |
|---|---|---|---|
| ① 读取 | `library/rules.py::RuleQueryService` | 按「库+缺陷+聚合物+产品」匹配谓词查 `RuleMethod` | SHORTSHOT 全库 109 条 → 只取到 **30 条** |
| ② 契约化 | `library/rules.py::RuleAdapter` | `RuleMethod` → `RuleProfile`（带 priority/specificity） | 30 条 |
| ③ 适用性 | `library/repository.py::get_rules` | 跨库副本去重（`(缺陷码, 规则串)` 为键）；特异级 = 规则标签 vs 上下文逐维比对 | 去重后 30 条，**特异级全为 4** |
| ④ 拆解分类 | `fuzzy_core/rules_filter.py` | 规则串只拆一次 → 分流 numeric / mamdani / advice / skipped | numeric 30，skipped 0 |
| ⑤ 推理 | `fuzzy_core/models/nets.py::tsk_inference` | 隶属度 → 激活度 → 分组归一化 → 结论层 | 命中 10 条 |

之后：`engine._infer_numeric_layer` → `recommendations.aggregate` → `to_recommendations`
→ `_apply_machine_limits`（机台物理上限裁剪）出最终建议。

### 16.3 实测解剖：一次推理的完整过程

**输入翻译**（业务名 → 算法名；缺陷档位 → 论域桶中心）：

```
inj_spd_1 → IV0=30   inj_t → IT=4   hold_pres_1 → PP0=44
hold_spd_1 → PV0=24  met_back_pres_1 → MBP0=5
SHORTSHOT = 0.25   ← low 档的桶中心（该档隶属度恰为 1.0）
```

各输入变量的隶属度向量（论域分桶）：

| 变量 | 值 | low | medium | high |
|---|---|---|---|---|
| SHORTSHOT | 0.25 | **1.0000** | 0.1353 | 0.0003 |
| IV0 | 30 | **0.6065** | 0.6065 | 0.0111 |
| IT | 4 | **0.9231** | 0.0561 | 0.0001 |
| PP0 | 44 | 0.3150 | **0.8912** | 0.0462 |
| PV0 | 24 | **0.9231** | 0.2780 | 0.0015 |
| MBP0 | 5 | **0.0504** | 0.9060 | 0.0001 |

**命中 10 条**（规则串形如 `IF {缺陷}_{档位} AND {参数}_{档位} THEN {参数}_add_{值}`）：

| # | 规则 | 原始激活度 | 组内占比 | 结论值 |
|---|---|---|---|---|
| 1 | `IF SHORTSHOT_low AND MBP0_low THEN MBP0_add_1` | 0.050406 | **1.000000** | MBP0 +1.0 |
| 2 | `IF SHORTSHOT_low AND PV0_low THEN PV0_add_2` | 0.923116 | 0.880797 | PV0 +2.0 |
| 3 | `IF SHORTSHOT_low AND IT_low THEN IT_add_0.5` | 0.923116 | 0.880797 | IT +0.5 |
| 4 | `IF SHORTSHOT_low AND PP0_low THEN PP0_add_2` | 0.314995 | 0.880797 | PP0 +2.0 |
| 5 | `IF SHORTSHOT_low AND IV0_low THEN IV0_add_2` | 0.606531 | 0.866813 | IV0 +2.0 |
| 6 | `IF SHORTSHOT_medium AND PV0_low THEN PV0_add_3.0` | 0.124930 | 0.119203 | PV0 +3.0 |
| 7 | `IF SHORTSHOT_medium AND IT_low THEN IT_add_0.75` | 0.124930 | 0.119203 | IT +0.75 |
| 8 | `IF SHORTSHOT_medium AND PP0_low THEN PP0_add_3.0` | 0.042630 | 0.119203 | PP0 +3.0 |
| 9 | `IF SHORTSHOT_medium AND IV0_low THEN IV0_add_3.0` | 0.082085 | 0.117310 | IV0 +3.0 |
| 10 | `IF SHORTSHOT_low AND IV0_high THEN IV0_reduce_2` | 0.011109 | 0.015876 | IV0 **−2.0** |

**折叠成 5 条建议**：

| 参数（业务名） | 命中规则 | Σdelta | 当前 → 推荐 | confidence |
|---|---|---|---|---|
| IV0（`inj_spd_1` 一段注射速度） | 3 | **+2.053805** | 30 → 32.053805 | 0.2332 |
| IT（`inj_t` 注射时间） | 2 | **+0.529801** | 4 → 4.529801 | 0.5240 |
| PP0（`hold_pres_1` 一段保压压力） | 2 | **+2.119203** | 44 → 46.119203 | 0.1788 |
| PV0（`hold_spd_1` 一段保压速度） | 2 | **+2.119203** | 24 → 26.119203 | 0.5240 |
| MBP0（`met_back_pres_1` 熔胶背压） | 1 | **+1.000000** | 5 → 6.0 | 0.0504 |

以 IV0 为例的完整算式：

```
delta = (+2.0 × 0.866813) + (+3.0 × 0.117310) + (−2.0 × 0.015876)
      = +1.733627 + 0.351931 − 0.031752 = +2.053805
      ⇒ 30 + 2.053805 = 32.053805   ✅ 与线上输出逐位一致
```

**核心公式**：

```
rawᵢ       = 激活度 × priority × specificity_weight
组内占比ⱼ  = rawᵢ / Σraw(同一输出参数组)      # 同组和恒为 1
deltaᵢ     = 结论值 × 组内占比ⱼ
聚合       = 同参数 delta 裸累加               # ≡ 加权平均（因占比和=1）
confidence = min(Σ原始激活度 / 命中规则条数, 1.0)
```

两道闸门（缺一不可）：`MIN_ACTIVATION_THRESHOLD = 0.01001` 同时作用于
**原始激活度**（绝对强度）与**组内占比**（相对份额）；剔除后**重新归一化**。

### 16.4 输出的内容边界

`AlgorithmRecommendation` 只有 7 个字段：

| 字段 | 实测值 | 说明 |
|---|---|---|
| `param_name` | `IV0` | 算法侧名（业务名在 service 层翻译） |
| `current_value` / `recommended_value` | 30 / 32.053805 | 当前值与推荐值 |
| `confidence` | 0.2332 | 见上 |
| `direction` | `increase` | 增/减/持/查 |
| `source` | `fuzzy.numeric` | `fuzzy.numeric` / `fuzzy.advisory` / `fuzzy.check` |
| `reason` | `模糊推理 (sources=['numeric'])` | **文案里没有规则串** |

⚠️ **输出不携带「依据哪几条规则」** —— `rule_refs` 字段恒为空数组
（`parameter_optimize.py::_extract_rule_refs` 只是预留接口，算法侧从未填）。
工艺员看到建议，但**看不到依据**。
（已登记于 `2026-10-22-fuzzy-algorithm-internals.md` L5、`2026-10-23-fuzzy-entry-refactor-execution.md` §2.11）

### 16.5 五个值得注意的点

| # | 发现 | 影响 |
|---|---|---|
| 1 | **自动选库必然落空** —— `product_to_library_codes` 的映射表指向 `packaging` / `auto_parts` / `medical` 等 code，库里不存在 ⇒ 只加载 `base` 库 | 9 个补充库共 1058 条规则（**占全库 64%**）从不参与推理；SHORTSHOT 109 条只用上 30 条 |
| 2 | **特异级权重在本场景完全失效** —— 30 条全是特异级 4，权重统一 0.25 ⇒ 组内归一化后相互抵消 | 特异级只在**同组内混有不同特异级**时才有区分度 |
| 3 | **缺陷程度只影响激活度，不影响选规则** | `level=low` 时 `SHORTSHOT_medium` 的规则照样进池（占比 0.119）—— 这是「越严重越激进」的表达方式 |
| 4 | **同参数反向规则静默相消** | IV0 组里混着 `IV0_reduce_2`（占比 0.016），净结果仍为 +2.05，**不会提示「存在争议」** |
| 5 | **MBP0 组内占比 1.0 但 confidence 仅 0.05** | 它独占该参数组 ⇒ 组内占比满分（看起来「很确定」），但绝对激活度只有 0.0504（勉强过闸）⇒ 匹配置信度 0.05（其实「很不确定」） |

⚠️ 点 1 是本轮最有价值的发现 —— 它意味着补充规则库形同虚设，需单独深挖。

### 16.6 案例数据集：可离线复现的输入数据（2026-10-28）

> 触发：用户提出「每次走查都要连数据库 ⇒ 应记录 demo 案例的输入数据，建 examples 目录存放」。
> 目录选定为**算法包内**（`process/algorithms/fuzzy/examples/`），不污染项目根。

```
process/algorithms/fuzzy/examples/
├── README.md                    ← 目录说明 · 怎么跑 · 怎么更新
├── export_case.py               ← 数据导出工具（开发期，**需要连库**）
├── run_demo.py                  ← 离线 runner（**不连库**）
└── cases/
    └── fuzzy_shortshot_low.json ← 案例数据（自持）
```

**案例文件结构**：`context`（输入，业务字段名）+ `rules`（RuleProfile 字段）
+ `keywords`（RuleKeyword 原始元数据）+ `expected`（期望输出，回归基线）。

**三个关键设计约束**：

| # | 约束 | 理由 |
|---|---|---|
| 1 | 存**数据源原始形态**，不存裁剪后的中间态 | 论域上界按设备实测值裁剪这一步发生在**引擎里**；离线复现必须走同一条路径，否则是「拿裁剪结果喂回去」 |
| 2 | **复用生产适配器**（`RuleKeywordAdapter` / `field_names.to_algo_params`） | 案例目录里**没有**第二份口径，`step` 为空时的 `span/3` 推导逻辑不在案例侧重写 |
| 3 | 通过 `AlgorithmResourceRepository` 协议**替换数据源** | 引擎本就支持注入；离线只是换实现（`tests/_verify_e2_offline.py` 已有同款先例） |

**「不连库」是可证的**：`run_demo.py` 把 `CursorWrapper.execute` 换成会抛异常的版本 ——
链路上出现任何 SQL 立刻炸；每次运行末尾打印「全程 0 次 SQL 执行」。

**验证**：

| 项 | 结果 |
|---|---|
| 案例导出 | 规则 30 条 / 关键词 10 条 / 期望建议 5 条 / 工艺参数 44 项 |
| 离线复现 | `[PASS]` 与期望输出逐位一致（`repr` 比对，不用容差） |
| 离线性自证 | 全程 **0 次 SQL 执行** |
| **证伪**（断言有效性） | 故意把期望值 +0.01 ⇒ `[FAIL] MBP0.recommended_value 不一致：期望 6.01，实际 6.0`，**退出码 1** |
| 回归 | `pytest tests -q` ⇒ **19 passed**（examples/ 未接进 pytest） |

⚠️ runner **未**接进 pytest（遵循「默认不新增测试用例」）：它是**手动跑**的回归基线 ——
改了算法后跑一次 `run_demo.py --check`，退出码非 0 即说明行为漂移。

### 16.7 本节遗留

| # | 项 | 说明 |
|---|---|---|
| 1 | 补充规则库不参与推理（§16.5 点 1） | 1058 条规则（64%）形同虚设；根因是 `product_to_library_codes` 的 code 映射与库里实际的 `library_code`（`R2024xxxx` 系列）对不上 —— 需单独深挖并定方向 |
| 2 | `rule_refs` 恒空 | 已有登记（§16.4），未修；`RuleProfile.source_ref` 已有溯源信息（`RuleMethod:<id>`），只差传到输出层 |
| 3 | 案例只覆盖 numeric 层 | 提示层（mamdani / advice）与「多引擎选优」未进案例；待需要时再补 |

---

## 17. 档位级数不对齐的实测定性（2026-10-28）

> 触发：用户提问「关键字默认 5 级模糊等级，规则从历史导入的都是 3 级，算法匹配时应该匹配不到 1 和 5 级，这部分是正确的吗？」
> 用户口径：这是**故意保留**的问题，用来测算法。

**结论先行**：预期与实际行为不符 —— **没有任何规则「匹配不到」**；实际发生的是「**档位词按字段自身词表落格**」。

> ⚠️ **措辞已更新（2026-10-28）**：本节原写「实际发生的是『**档位语义平移**』」——
> 该措辞已被 §17.3 的定性修正取代：**落格随字段档数变化是正常语义，不是缺陷、也不是「漂移」**。
> 档位词是**绝对词义**（`low` 就是「偏低」这一档），落在哪一格由**该字段切了几格**决定
> （5 档 ⇒ 桶 1，3 档 ⇒ 桶 0）——**两者都是正确实现**。
> 规则**不需要**声明自己属于哪套档位体系，算法无需知道这件事。
> 详见 `_refs/system/algorithm/fuzzy-level-semantics-design.md` 决策 D1 / D3。

### 17.1 实测数据（连库核对，2026-10-28）

| 项 | 实测值 |
|---|---|
| `RuleKeyword.fuzzy_level` 分布 | 全部 311 个：`{5: 310, 3: 1}`；parameter 183 个全 5 级、defect 17+1、defect_position 110 个全 5 级 |
| 唯一的 3 级关键字 | `DEFECTFREE`（category=defect，「无缺陷」sentinel，**不参与规则匹配**）⇒ 现状无害 |
| `RuleMethod` 总行数 | 1646 |
| 前件档位词分布 | `low` 1516 / `medium` 493 / `high` 1437；另有 `worse` 154（不可判级词） |
| **在 lvl=5 下解析失败** | **0 条**（low/medium/high 全部能解析） |
| 案例 30 条规则的前件桶分布 | `{桶1: 37, 桶2: 10, 桶3: 13}` ⇒ **桶0 / 桶4 = 0** |

### 17.2 为什么不会「匹配不到」

`macros.LEVEL_WORDS_BY_LVL` 的**硬约束 2** 明确写着：每张词表都必须含 low / medium / high 三个核心词
—— 现有规则库 1646 条用的就是这三个词，缺一个就整类规则无法解析。

词表下标 = 桶索引，因此：

| lvl | 词表 | low | medium | high |
|---|---|---|---|---|
| 3 | `('low','medium','high')` | 桶0 = **0%** | 桶1 = 50% | 桶2 = **100%** |
| 5 | `('very_low','low','medium','high','very_high')` | 桶1 = **25%** | 桶2 = 50% | 桶3 = **75%** |
| 7 | 7 词 | 33.3% | 50% | 66.7% |
| 9 | 9 词 | 25% | 50% | 75% |

⇒ 「1 档和 5 档」在 5 档词表里是 `very_low` / `very_high`，**规则库压根没有这两个词**
⇒ 不是「匹配不到」，而是**没有任何规则引用它们** ⇒ 桶 0 / 桶 4 是**死桶**（无害：
没规则指向，推理时那一列的隶属度根本不会被取用）。

### 17.3 真正发生的事：档位词按字段自身词表落格（**正常语义，不是缺陷**）

> ⚠️ **定性已修正（2026-10-28）**：本节原标题为「档位语义平移（门槛被静默放宽）」，
> **该定性有误**，会把后续开发引向错误的"修复"方向。经与用户对齐口径确认：
>
> **档位词是绝对词义** —— 规则写 `low` 就是「偏低」这一档，它落在向量的哪一格由
> **向量自己切了几格**决定。5 档体系里多一个 `very_low` 在 `low` 之下 ⇒ `low` 自然上移一格
> （落桶 1，论域 25% 分位）—— **这是正确实现，不是「门槛被放宽」，也不是「漂移」**。
> 规则**不需要**声明自己属于哪套档位体系，算法无需知道这件事。
>
> ⇒ **落格随字段档数变化不列为风险。** 下表数据（实测）本身仍然有效，只是解读方式要改。
> 详见 `_refs/system/algorithm/fuzzy-level-semantics-design.md` 决策 D1 / D3。
> 同理，`2026-10-27` 文档 §4.3 提到的「两条论域来源 `lvl` 不一致」才是真问题（已由 §18.3 关闭）。

同一个规则串 `X_low`，在 3 档字段上要求「接近论域下界」，在 5 档字段上只要求「低于 25% 分位」。

实测（案例数据）：

| 前件 | 5 档下的桶中心 | 3 档语义下应是 |
|---|---|---|
| `IV0_low`（论域 [0,120]） | 30 | 0 |
| `IV0_high` | 90 | 120 |
| `SHORTSHOT_low`（论域 [0,1]） | 0.25 | 0.0 |
| `SHORTSHOT_high` | 0.75 | 1.0 |

缺陷维度同样被平移：程度 `low` → 0.25（3 档语义应是 0.0）；**缺陷位置恒取 high 档中心** → 0.75。

与 §16 的实测吻合：`SHORTSHOT` 反馈 low ⇒ 论域值 0.25 ⇒ low 隶属度 1.0、medium 0.1353。

> 这不是 bug —— `macros.py` 已在注释中写明「3 档 low/high 落在两端，5/7/9 档落在中间；
> 同一个 `X_high` 在 3 档字段上要求接近论域上界，在 5 档字段上只要求高于中位。
> 不是错误，但会影响跨级数字段的规则激活严格程度」。

### 17.4 风险与边界

| # | 项 | 说明 |
|---|---|---|
| 1 | `fuzzy_level` 是**字段级**属性，档位语义是**规则级**假设 | 规则串里的 `X_low` 本身不带级数信息，它落在哪个桶由该字段的 `fuzzy_level` 决定。（与 §17.3 修正后的口径一致：**算法无需知道规则属于哪套档位体系**） |
| 2 | 改 `fuzzy_level` 会**改变受影响规则的门槛**（正常语义，但当前**无提示**） | 把某关键字从 5 改成 3 ⇒ 同一批规则的落格从桶1/桶3 变成桶0/桶2，门槛从 25%/75% 收紧到 0%/100%。**这是正常语义**（见 §17.3 定性修正），不是缺陷；但**当前完全静默**，改档的人不会知道有多少条规则引用了它 ⇒ 真正的待办是**加提示**，不是改算法 |
| 3 | 现状安全是**巧合不是保障** | 310/311 都是 5 级、唯一的 3 级（DEFECTFREE）不参与匹配 ⇒ 当前口径一致，但没有任何机制保证它不被改坏 |
| 4 | `worse` 154 处不是「匹配不到」 | 不可判级词 ⇒ 前件**不作门控**，规则仍可命中（与 §19 路径①一致），不是整条被丢 |

### 17.5 如果要真正测「匹配不到」，得换样本

| 方案 | 做法 | 预期行为 |
|---|---|---|
| A | 规则里写**越界编号** `level6` / `level7`（lvl=5） | `resolve_bucket` 抛 ValueError ⇒ `_resolve_bucket_safe` 记 warning ⇒ **整条规则激活度 0，不参与推理** |
| B | 某关键字设 `fuzzy_level=3`，规则用 `very_low` / `very_high` | 同上（词表不含该词 ⇒ ValueError） |

⚠️ **行为已变更（2026-10-28）**：原文写「该前件不作门控」，**已改**：
档位词**填不进**字段词表 ⇒ 该条件**无法判定** ⇒ 该条规则**整条激活度 0**（不参与结论）。

**不再**是「只删掉这个前件、其余条件照常作门控」—— 那种做法会让门控乘数变少、
**匹配度不降反升**（实测：删掉填不进去的 `very_low` 后，激活度从 0 变成 1.0）。
改动见 `_refs/system/algorithm/fuzzy-level-semantics-design.md` 决策 D5。

⚠️ **勿与另外两种「不作门控」混淆**（这两者仍是「只跳过该前件，规则其余条件照常作门控」）：
- `worse` 等人工判断词（本来就没有隶属度可言）
- `pre_dict` 里没有该维度（建不了论域，如缺陷反馈未给程度）

而「`pre_dict` 有档案但**输入无值**」才是「整条规则被丢」的另一条路径。

### 17.6 这组数据的真实价值

它测的**不是**「匹配失败」，而是 E2 档位映射改造后最该被盯住的**跨级数一致性**（同一份规则在
3 档 / 5 档字段上的落格与激活度）—— 建议把它固化为案例数据集的第 2 个案例
（「规则按 3 档语义撰写 + 字段 5 档」回归基线），当前案例集只有 `fuzzy_shortshot_low` 一个，
覆盖面偏窄。

> ⚠️ 2026-10-28 补充：原措辞「档位语义平移」已不再使用（定性见 §17.3 修正）。
> 该案例的价值也不在于「发现漂移」，而在于**锁住落格口径** ——
> 档位词是绝对词义，5 档里 `low` 落桶 1 是正确实现；这个基线能防止后来者
> 误把它当成 bug 去"修正"成桶 0。

---

## 18. 文件来源通道（2026-10-28）

### 18.1 起因与目标

`library/` 原先**只有数据库一个数据源**。目标：

1. 把 `RuleLibrary` / `RuleMethod` / `RuleKeyword` **导出成本地文件**；
2. 打通**第二条路径**：从本地文件读关键词与模糊规则；
3. 目的不是「多一个备份」，而是**脱离数据库探讨关键词与规则的问题** ——
   改一个 JSON、立刻看到推理结果变化。

> 附带解决了 README 里记的一条历史悬案：2026-10-27 `RuleMethodAdapter`
> 曾以「为文件来源预留」为由保留，但它所在的 `library/files/` 当时是
> **预留空壳** ⇒ 预留理由不成立。2026-10-28 文件来源真正落地。

### 18.2 分层重构（核心）

打通两条路径的最大风险不是「能不能读文件」，而是**两条路径悄悄分叉**：
选库口径、适用性谓词、去重键、排序 —— 任何一条写法不同，
同一批规则在两条路径下的命中集合就会不同，而且**不报错，只是结果悄悄不同**。

因此把 `library/` 拆成**来源无关**与**来源相关**两层：

| 模块 | 职责 | 依赖 ORM |
|---|---|---|
| `contracts.py` | `RuleQueryContext` / `LibraryRecord` / `RuleRecord` / 协议 | 零 |
| `semantics.py` | `RuleService` —— 规则语义判定的**唯一口径** | 零 |
| `adapters.py` | 来源记录 → 内核契约的转换（`to_record` / `from_dict`） | 零 |
| `assembly.py` | `RuleAssembler` / `KeywordAssembler` —— **来源无关**的编排 | 零 |
| `provider.py` | 来源选择器（配置开关 + 延迟导入） | 延迟 |
| `rules.py` / `keywords.py` | 数据库来源的**取数**（查询线） | 有 |
| `repository.py` | 数据库来源的资源仓库 | 有 |
| `files/loader.py` / `files/repository.py` | 文件来源（读取线 + 仓库） | 零 |
| `files/export.py` | 开发期导出工具 | 有（仅脚本） |

关键动作：

1. **语义类迁出**：`RuleService` 从 `rules.py` → `semantics.py`。
   理由：文件来源必须**零 ORM** 地复用它，否则会把 Django ORM 拖进文件通道
   （依赖倒置的实质检验 = 高层不被低层实现拖住）。
2. **转换类迁出**：`RuleAdapter` / `RuleKeywordAdapter` → `adapters.py`，
   并补 `from_dict` 入口（文件来源直接吃 JSON）。
3. **新增来源无关中间层**：`LibraryRecord` / `RuleRecord` 两个 dataclass ——
   两侧各自规约到这两种记录，再由共用编排层组装。
4. **新增 `assembly.py`**：选库 / 特异级 / 契约校验 / 缺陷名闸门 / 跨库去重 /
   排序，全部收为来源无关。
5. **匹配谓词收敛到一处**：`RuleService.matches_context`（纯函数）。
   旧实现是 ORM 的 `Q(poly__isnull=True) | Q(poly=ctx)`，文件来源只能用 Python
   表达 —— 两份实现一旦分叉就是静默错误。**现改为：来源侧只取「候选」，
   谓词由编排层统一施加**。
6. **关键字契约校验也收敛**：`KeywordAssembler.filter_valid` 共用。

⚠️ **等价性论证**（匹配谓词）：旧 SQL 谓词在 SQL 三值逻辑下
`NULL = 'ABS'` 为 NULL（假），Python `None == 'ABS'` 同样为假；「通用」侧
SQL 认 `IS NULL`、Python 认 `is None` ⇒ **逐条等价**。

⚠️ **排序口径**：数据库侧 `ORDER BY priority DESC, id ASC`；
文件侧用 `(-原始 priority, id)` —— 必须用**原始值**而非契约里的
`or 1.0` 归一值，否则 `priority=0` 的规则排序位置会分叉。
（已写成单元测试 `test_priority_zero_sorts_last`。）

### 18.3 文件布局与格式

```
backend/process/algorithms/fuzzy/library/files/data/
├── libraries.json          规则库清单（11 条）
├── keywords.json           关键字元数据（311 条）
└── rules/
    ├── base.json           585 条
    ├── expert_rules.json   0 条（专家库无模糊规则）
    └── R2024*.json         9 个补充库，合计 1061 条
```

每条规则保留**导出所需的原始字段**（`id` / `defect_code` / `rule_description` /
`priority` / `polymer_abbreviation` / `product_category` / `is_active`），
另附 `rule_explanation` / `defect_label` / `source` 供人阅读。

⚠️ **导出口径必须与数据库来源逐条一致**：

| 环节 | 导出时 | 数据库侧 |
|---|---|---|
| 库 | 导 `is_deleted=False` 的全部库（含停用，带 `is_active`） | `get_libraries_by_codes` 过滤 `is_active=True, is_deleted=False` |
| 同码多库 | **只导第一条**（按主键升序） | `qs.first()` |
| 规则 | 导 `is_deleted=False` 的全部规则（含停用，带 `is_active`） | `get_methods` 过滤 `is_active=True, is_deleted=False` |
| 关键字 | **全量导**（不带过滤） | `RuleKeyword.objects.filter(keyword_name__in=...)` 不带过滤 |

⇒ 实测：11 个库、1646 条规则、311 条关键字。

### 18.4 导出工具

```bash
cd backend
..\.venv\Scripts\python.exe process\algorithms\fuzzy\library\files\export.py
..\.venv\Scripts\python.exe -m process.algorithms.fuzzy.library.files.export --out-dir D:\tmp\rules
```

⚠️ **开发期工具，不是运行时组件**：它 import ORM 模型，只能作脚本单独跑；
运行时代码（`files/loader.py`、`files/repository.py`）**绝不 import 它**。

### 18.5 切换方式（配置开关 + 显式注入双支持）

```python
# _moldx/settings.py
FUZZY_LIBRARY_SOURCE = 'db'      # 'db' | 'file'
FUZZY_LIBRARY_FILE_DIR = ''      # 空 = 用 library/files/data/ 默认目录
```

```python
# 显式注入（优先级高于配置）
from process.algorithms.fuzzy.library.files.repository import FileResourceRepository
engine = FuzzyEngine(repository=FileResourceRepository())
```

`engine._get_repository()` 改走 `library/provider.py::resolve_repository()`，
**延迟导入**：只有真走某条来源时才 import 它 ⇒ 「用文件来源」不会把 ORM 拖进来。

⚠️ **自动重载**：文件通道按 **mtime** 缓存 ⇒ 改完 JSON 立即生效，不用重启进程
（`auto_reload=False` 可关掉）。这是这条路径的核心便利性。

### 18.6 对拍结果（实测）

`_dev_refs/_verify_sources_parity.py`（现役验收工具）：

| 比对项 | 规模 | 结果 |
|---|---|---|
| 选库（库编码 + 顺序） | 7 组上下文 | **一致** |
| 规则（规则串 / 优先级 / 结论形态 / 特异级 / **顺序**） | 17 个缺陷码 × 6 组上下文 = **102 组**，累计命中 **3631** 条 | **一致** |
| 关键字（论域 / 档位 / 步长） | 4 组（含不存在名字） | **一致** |
| 引擎级端到端（同一输入 ⇒ 同一建议） | 案例 `fuzzy_shortshot_low` | **一致**（db=5 条 / file=5 条，浮点逐位相同） |

⚠️ **自证「文件来源不碰数据库」**：跑文件来源时**拦截所有 SQL 执行**
（`CursorWrapper.execute` 抛异常）⇒ 实测 **0 次 SQL**，且引擎输出与数据库侧一致。

回归：`pytest process/algorithms/fuzzy tests -q` ⇒ **65 passed**
（原 49 + 文件来源新增 16）。

### 18.7 已知边界

| # | 项 | 说明 |
|---|---|---|
| 1 | 文件是**快照**，不是实时 | 库里改了规则不会自动同步到文件 ⇒ 需重跑导出；反之文件改了库不会变 ⇒ 切换开关前请确认用的是哪一份 |
| 2 | 关键字**不做** `is_active` 过滤 | 与数据库侧查询口径一致（那边也不过滤）；若将来要过滤，**两侧必须同时改** |
| 3 | 文件来源**不含**专家规则（`ExpertRule`） | 本轮只打通模糊规则与关键词；专家规则走 `library/expert` 另一条线 |
| 4 | 数据目录在**包内** | `library/files/data/` 已随仓库落地；若不希望入库需自行加 `.gitignore` |
| 5 | 关键字顺序 | 数据库侧 `__in` 查询**无序**（历史上如此）；文件侧按文件顺序 ⇒ 两者顺序可能不同，但内核按名建索引（`known_keywords` 是 set）⇒ 不影响结果 |


