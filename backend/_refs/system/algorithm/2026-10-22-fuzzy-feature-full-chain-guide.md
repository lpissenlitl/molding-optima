# 模糊推理功能全景讲解（14 环节）

> 日期：2026-10-22
> 目的：在动手重写之前，把「缺陷反馈 → 工艺建议」这条链路的每一个环节讲清楚，
> 让后续改造有共同的参照系。
> 范围：从 HTTP 入口到前端展示，覆盖编排层、路由层、推理层、聚合层、落库层。
> 状态：**讲解文档，不含任何改动方案**。方案另议。
>
> ⚠️ **本文是「全景背景参考」，不是当前的工作焦点。**
> 当前只关注算法部分（`process/algorithms/fuzzy/` 包内部），
> 详见 **[2026-10-22-fuzzy-algorithm-internals.md](2026-10-22-fuzzy-algorithm-internals.md)**。
> 本文中第 ⑤⑦⑧⑨⑩⑪ 环的内容已在那份文档中以算法视角重新组织，不要重复看。

---

## 0. 业务闭环一句话

> 工艺员在调机页填「缺陷 + 严重程度 + 位置」→ 后端按缺陷去规则库捞出若干条
> 「IF 条件 THEN 参数调整量」规则 → 用当前工艺参数对每条规则算一个**适用强度**
> → 把强度加权到规则写的调整量上 → 同参数的多条建议合并成一个 → 落库并展示给工艺员。

模糊推理只发生在第 10 环（算强度），其余 13 环都是确定性的工程逻辑。

---

## 1. 全链路总览

| # | 环节 | 代码位置 | 性质 |
|---|---|---|---|
| 1 | 前端填缺陷反馈 | `views/process/optimization/pages/OptimizationCreate.vue` | 交互 |
| 2 | HTTP 入口 + Schema 校验 | `process/views/processes.py::AlgorithmsOptimizeView` | 契约 |
| 3 | Step 0：feedback 防御性校验 | `process/services/parameter_optimize.py::_validate_feedback` | 契约 |
| 4 | Step 1：装配推理上下文（只读 DB） | `_assemble_context` / `_resolve_parent` / `_resolve_baseline` | 数据 |
| 5 | 命名空间翻译（业务名 → 算法名） | `_compose_algorithm_context` / `_normalize_field_name_by_spec` | **翻译** |
| 6 | 引擎注册与调度 | `process/algorithms/base.py::AlgorithmRegistry` + `_call_algorithms` | 调度 |
| 7 | 规则路由（捞规则） | `fuzzy/services/rule_query_service.py::RuleQueryService.get_rules` | 路由 |
| 8 | 词法解析（规则串 → 结构化） | `fuzzy/fuzzy_core/parsing.py::parse_rule` / `split_phase` | **翻译** |
| 9 | 论域装配（RuleKeyword → FuzzyFeature） | `fuzzy_algorithm.py::_load_keyword_dicts` + `adapters.py::RuleKeywordAdapter` | 数据 |
| 10 | **模糊推理四层** | `fuzzy/fuzzy_core/models/nets.py::NumTskRuleNet.tsk_inference` | **算法** |
| 11 | 聚合与合并（→ Recommendation） | `fuzzy_algorithm.py::_merge_layer_results` | **算法** |
| 12 | 规范化 + 应用到 baseline | `_normalize_recommendations` / `_apply_recommendations_to_baseline` | 转换 |
| 13 | 原子落库（3 张表） | `_create_new_parameter` / `_create_new_tuning_record` / `_create_new_recommendation` | 数据 |
| 14 | 前端展示建议 | `views/process/optimization/components/PreviousSuggestion.vue` | 交互 |

**读法**：第 5、8 两环是「翻译」，第 10、11 两环是「算法」，其余是「管道」。
重写只需动第 10、11 两环；第 5、8 两环需要小修；其余可整体保留。

---

## 2. 逐环节详解

### 环节 1：前端填缺陷反馈

用户操作：`OptimizationCreate.vue` 点【获取优化工艺】→ 填缺陷表。

缺陷反馈结构（`DefectFeedback.vue` 产出）：

```json
{
  "defect": [
    { "keyword_id": 12, "keyword_name": "SHORTSHOT",
      "level": "medium", "position": "DLSHORTSHOT1" }
  ],
  "tuning_result": null
}
```

三个字段的语义完全不同，**这是全链路第一个语义分叉**：

| 字段 | 语义 | 取值来源 | 消费方 |
|---|---|---|---|
| `keyword_name` | 缺陷**种类**（SHORTSHOT/FLASH/...） | 用户选 | 路由（环节 7） |
| `level` | 缺陷**严重程度**（low/medium/high） | 用户选 | 路由（环节 7，选哪一套规则） |
| `position` | 缺陷**位置**（`DL` + 缺陷名 + 段号） | 用户选 | 上下文透传，**本期不参与筛选** |

> 关键：`level` 是**缺陷的严重度**，不是工艺参数的档位。
> 它决定"命中哪一套调整方案"，多档规则是多套完全不同的方案，不能混用。

### 环节 2：HTTP 入口

```
POST /api/processes/algorithms/optimize/
body: { condition_id, parent_seq_idx, parameter?, feedback? }
```

- `views/processes.py::AlgorithmsOptimizeView.post` → `ParameterOptimizeService().infer(...)`
- `schemas/optimization.py::ProcessOptimizeFromConditionSchema` 负责类型与结构校验
- 另有一个纯推理入口 `POST /api/processes/algorithms/optimize-from-provided/`（第三方集成 / dry-run），不查库不落库

`parameter` 是**用户在前端手动改过的工艺参数**（扁平 dict，业务字段名），
用于覆盖 DB 里的基准值 —— 这正是"用设备真实值和传入参修正"落地的位置。

### 环节 3：Step 0 — feedback 防御性校验

`_validate_feedback` 与前端 `validateFeedback` 是**同一套约束的镜像**：

- `defect` 非空、每项是对象
- `keyword_name` 必填（缺了必然查不到规则）
- `level` 必填且必须是合法档位词
- `position` 必填
- 例外：`DEFECTFREE`（无缺陷）免校验 level / position

失败抛 `BizException(ERROR_REQUIRED_FIELD)`。

### 环节 4：Step 1 — 装配推理上下文（只读 DB）

`_assemble_context` 回答一个问题：**本轮推理的起点是什么？**

```
condition + parent_param  ← 从 DB 反查（调机树当前节点）
baseline                  ← 以 parent_param 为底，用 user_parameter 覆盖（仅内存）
machine_info              ← 按 specs 白名单从 InjectionMoldingMachine + 选中的 InjectionUnit 取
polymer_info              ← 按 specs 白名单从 Polymer 取
mold_info                 ← 按 specs 白名单从 Mold 取
user_changed_fields       ← 用户手改且与库中原值确实不同的字段（供落库阶段精确写回）
```

`_extract_orm_fields_by_spec` 严格按 `specs.py` 的白名单取字段，**ORM 元数据不传给算法**。

### 环节 5：命名空间翻译（业务名 → 算法名）

**这是最容易出错的一环。** 业务侧和规则库侧不是同一个命名空间：

```
业务侧（DB / 前端）        翻译              算法侧（规则库 / RuleKeyword）
inj_spd_1  ──────────►  FIELD_INDEX_OFFSET  ──►  IV0
inj_spd_2  ──────────►  （offset = -1）      ──►  IV1
brl_temp_1 ──────────►  FAMILY_FIELD_ALIAS   ──►  BT
brl_temp_3 ──────────►  （段1→家族名）        ──►  BT3
noz_temp   ──────────►  FIELD_NAME_ALIAS     ──►  NT
```

三条映射规则（`_normalize_field_name_by_spec`）：
1. **完整字段名**：`noz_temp` → `NT`
2. **分段前缀 + 序号偏移**：`inj_spd_1` → `IV0`（业务 1-based → 规则库 0-based，offset = -1）
3. **整段族**：`brl_temp_1` → `BT`（段 1 用家族名本身，段 N 用 `BT`+N）

反向翻译 `FuzzyEngine.to_business_name()` 用于把算法推荐写回业务字段。
**不翻译就永远匹配不上 baseline，推荐值会被静默丢弃**（表现为"算法有推荐，但参数没变"）。

> ⚠️ 已知盲区：`IPOS` / `CUSION` 这类规则库专用参数在 `ProcessParameter` 里没有对应列，
> `to_business_name` 返回 None，其推荐会在环节 12 被过滤掉 —— **静默丢弃，无日志**。

### 环节 6：引擎注册与调度

`_ensure_engines_registered()` 幂等注册两个 `optimization` 引擎：

| subtype | 实现 | 角色 |
|---|---|---|
| `fuzzy` | `FuzzyEngine` | 规则库驱动（主） |
| `empirical` | `EmpiricalReasoning` | 硬编码经验表（兜底） |

`_call_algorithms` 按 `AlgorithmRegistry.get_priority(subtype)` 排序后逐个调 `recommend(context)`，
**单个引擎异常只记 warning 不影响其他引擎**（`except Exception` → `recs = []`）。

### 环节 7：规则路由（捞规则）

`RuleQueryService.get_rules(context)`：

**7.1 选库**（`get_libraries`，按 priority 降序）
1. 用户显式指定的 `library_code`
2. 按 `product_category` 匹配（精确产品类 + 大类映射表）
3. **兜底库 `library_code='base'`**（`library_type='fuzzy'`, `priority=100`）
   > 历史实现找的是 `'general'`，该 code 库里不存在 → 兜底库永远找不到 → 整条链路拿不到规则

**7.2 四级特异性匹配**

| specificity | polymer | product |
|---|---|---|
| 1 | 指定 | 指定 |
| 2 | 指定 | None |
| 3 | None | 指定 |
| 4 | None | None |

查询条件固定含 `defect_code=context.defect_name` + `is_active=True`。

**7.3 缺陷档位过滤**（`_match_defect_level`）

规则库里每个缺陷都有多档规则，档位写在**第一个前件**里
（`IF SHORTSHOT_medium AND IV0_low THEN ...`）。反馈的 `level` 决定命中哪一档 —— 不匹配直接剔除。

**7.4 去重**：跨库用 `seen_ids` 去重（`RuleMethod.id`）。

**7.5 按结论形态分流**（`classify_conclusion_kind`）

| kind | 判定 | 数量（全库） |
|---|---|---|
| `numeric` | 结论全是 `add`/`reduce` + 数值 | 1544 条 |
| `advisory` | 含 `adjust`/`popup`（提示文本） | 99 条 |
| （档位结论 `X_add_low`） | —— | **0 条** |

> ⇒ **Mamdani 推理层实际是死代码**（`FuzzyRuleNet` 从未产出真实结论）。

### 环节 8：词法解析（规则串 → 结构化）

`parse_rule(rule_str)` 把 `IF A AND B THEN C` 拆成：

```python
{'preconditions': [{'name': 'IV0', 'level': 'low', 'kind': 'precondition'}, ...],
 'solutions':     [{'name': 'IV0', 'action': 'add', 'value': '2', 'kind': 'solution'}, ...]}
```

`split_phase` 的判定顺序（**顺序即优先级，先命中先返回**）：

1. 含 `=` → 代数结论（预留）
2. 某段是 `popup` → 弹窗结论
3. 某段是 `add`/`reduce`/`adjust` → 标准结论
4. **从右往左**找第一个已知档位词 → 前提词
5. 兜底：`parts[0]` + `parts[1]`

> ⚠️ 情形 4 从右往左取**第一个**档位词，只处理单段档位词。
> `IV0_very_low` 会解析成 `name='IV0_very', level='low'` —— 名字被污染。
> 正确做法是按词长降序取**最长可匹配后缀**。

### 环节 9：论域装配

`_collect_keyword_names` 收集规则涉及的全部参数名（前件 + 结论），
用 `collect_param_names` 剔除缺陷名与 `DL*` 位置名。

> 剔除缺陷名是**必须的**：缺陷没有数值，若当成参数建论域，
> 缺陷前件会被当成可判级条件求值，激活度被 EPSILON 压到 ~0，**整类规则全部失活**。

`_load_keyword_dicts` 拉 `RuleKeyword` 元数据：

```python
{'keyword': 'IV0', 'lvl': 5, 'min_val': 0.0, 'max_val': 120.0, 'step': 10.0}
```

| 字段 | 来源 | 含义 |
|---|---|---|
| `lvl` | `RuleKeyword.fuzzy_level` | 该参数自己的模糊档位数（3/5/7/9） |
| `min_val`/`max_val` | `range_min`/`range_max` | 论域（**通用默认值，不是设备物理极限**） |
| `step` | `RuleKeyword.step` | 去模糊化输出粒度（推理输出取整到 step 的整数倍） |

**兜底分支**：`RuleKeyword` 里找不到该参数时，用实时值自造一个：

```python
{'keyword': name, 'lvl': 3, 'min_val': 0.0, 'max_val': current * 2, 'step': current * 0.1}
```

> ⚠️ 这个兜底会引入 `lvl=3` 的**异构档位**，与规则的 5 档语义不一致。

`RuleKeyword` 模型自身的注释已写明：

> 取值范围是通用默认值/模拟推荐值，非设备物理极限。
> 实际推理时：设备真实范围 > RuleKeyword 默认值。

### 环节 10：模糊推理四层（`NumTskRuleNet.tsk_inference`）

### 第一层：隶属度层

每个参数按自己的 `lvl` 铺桶：

```python
σ    = (hi - lo) / (2 * (lvl - 1))
means = [lo, quantile(lo,hi,1/(lvl-1)), ..., hi]
```

以 `IV0`（论域 [0,120]，`lvl=5`）为例：`σ=15`，`means=[0,30,60,90,120]`。

`IV0 = 30` 时的隶属度向量：

| 桶 | very_low | low | mid | high | very_high |
|---|---|---|---|---|---|
| μ | 0.1353 | **1.0000** | 0.1353 | 0.0003 | ~0 |

### 第二层：规则层（门控）

`connected_matrix` 是 one-hot 门控矩阵（行=规则，列=(参数,桶)），
作用只有一个：**广播乘取出门控位置的隶属度**。

```python
rule_matrix = connected_matrix * membership_degrees
conditions = rule_matrix[i, rule_matrix[i] != 0]
rule_activations[i] = np.prod(conditions)     # TSK 风格连乘
```

> **连乘意味着"全部条件都要满足"** —— 一个条件 μ=0.1、另一个 μ=0.9 ⇒ 激活度 0.09。
> 这是 TSK 的标准语义，与 Mamdani 的 min（弱连接）不同。

门控位置由**全局静态表**决定：

```python
p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[level]
```

`HS_MAPPING_DICT = {'low': 0, 'mid': 1, 'medium': 1, 'high': 2, ...}`

> ⚠️ `+0` 指向的是 `means[0]`（下界 = very_low 桶），而不是 `means[1]`（low 桶）。
> 5 档参数上，"low" 被当成"very_low" 取隶属度。**档位与桶错位一档。**

### 第三层：归一化 + priority 加权

```python
activations_sum = np.sum(rule_activations)              # 全部规则的总和
new_activations[i] = rule_activations[i] / max(activations_sum, EPSILON)
activations_with_priority = new_activations * priority_array
```

> ⚠️ **分母是所有参数的所有规则的总和**，不是"某个参数内部的规则之和"。
> ⇒ 参数 A 的激活度会被参数 B 的规则稀释。A 有 10 条规则、B 有 1 条时，A 被摊薄 10 倍。
> 归一化后 activation 变成「在全部规则里占多少份额」，而它本该是「这条规则有多适用」。

### 第四层：结论层

```python
if self.rule_classify[i] == 1:      # 百分比规则
    cur_params[i] = x[k]             # 取当前值
sol_matrix = self.solution_matrix.T * cur_params
```

`solution_matrix` 存的是规则写的调整量（`add_2` → +2.0；`reduce_30%` → 当前值的 -30%）。

### 回到上层：摊薄落点

`fuzzy_algorithm.py::_infer_numeric_layer`：

```python
'delta': float(value) * float(activation)     # 绝对工艺知识 × 相对强度
```

> ⚠️ `activation` 来自第三层（已归一化 + priority）。
> ⇒ **一个满激活（μ=1.0）的规则，调整量也会被归一化摊薄**。

### 环节 11：聚合与合并（`_merge_layer_results`）

**同参数内：delta 直接相加，不是加权平均。**

```python
merged[p]['delta'] += rec['delta']         # 同参数多条规则直接相加
merged[p]['activation_sum'] += rec['activation']
merged[p]['rule_count'] += 1
```

**跨层规则**：数值层胜出，提示层只作 `advisory_reference` 注释。

**最终推荐值**：

```python
adjusted_delta = info['delta'] * adjustment_factor     # factor 来自 _trend_to_factor(trend)
recommended_value = current_value + adjusted_delta
confidence = min(activation_sum / rule_count, 1.0)
```

`adjustment_factor` 取自 `context['iteration_trend']`：
`worsening→0.5`、`improving→1.2`、`stable/unknown/final→1.0`。

> ⚠️ `current_value` 取自 `current_params.get(p)`，**算法命名空间**；
> 若该参数没有业务字段（`IPOS`），推荐值仍会生成，但在环节 12 被过滤。

### 环节 12：规范化 + 应用到 baseline

`_normalize_recommendations` 三件事：
1. `param` 从算法名译回业务名
2. **丢弃零变化项**（`recommended_value == current_value`）
   > 注释写明：这些来自激活度 ~0 的规则，是数值噪声（置信度 1e-32 量级）
3. `reason` 重写为业务文案（`降低一段注射压力：70 → 60`）

`_apply_recommendations_to_baseline`：把推荐值覆盖到 baseline（**仅覆盖 baseline 中存在的字段**）。

`_build_suggestion_payload`：按参数前缀分组（注射/保压/熔胶/VP/料筒温度/冷却/...），
产出 `{source_type, groups: [{category, icon, items: [...]}]}`。

### 环节 13：原子落库（FromCondition 路径，事务内）

| 顺序 | 动作 | 表 |
|---|---|---|
| 3.1 | 写回用户手改的参数到父记录 | `ProcessParameter`（UPDATE） |
| 3.2 | 更新上一轮缺陷反馈 + 试模结果 | `TuningRecord`（UPDATE） |
| 3.3 | 上一轮 `is_adopted` 改 False（当本轮 ineffective） | `Recommendation`（UPDATE） |
| 3.4 | 创建新轮次参数（`param_source='system_inferred'`） | `ProcessParameter`（INSERT） |
| 3.5 | 创建新 `TuningRecord`（`result='pending'`） | `TuningRecord`（INSERT） |
| 3.6 | 创建新 `Recommendation`（`is_adopted=True`） | `Recommendation`（INSERT） |

**写库只在 Step 3** —— 「父记录改写」与「新建轮次」同生共死，
避免造出"参数改了但新轮次没建成"的中间态。

`FromProvided` 路径（`infer_from_provided`）不查库不落库，只做纯推理。

### 环节 14：前端展示

`OptimizationCreate.vue` 收到响应后：

```javascript
previousSuggestion.value = {
  source_round_id: previousRoundId,
  adopted: null,
  groups: inferData.suggestion.groups,
}
```

`PreviousSuggestion.vue` 按 group 渲染：分类图标 + 分类名 + 每条建议的方向图标 + 文案 + 规则引用。

> `rule_refs` 目前**永远是空数组**（`_extract_rule_refs` 注释：算法侧 Recommendation 无规则引用字段，预留接口）。
> ⇒ 工艺员看到建议，但**看不到依据哪条规则** —— 这是可用性上的一个空洞。

---

## 3. 四个命名空间（最容易搞混的地方）

| # | 命名空间 | 例子 | 归属 |
|---|---|---|---|
| 1 | **业务字段名** | `inj_spd_1` | DB（`ProcessParameter`）/ 前端 |
| 2 | **算法字段名** | `IV0` | 规则库 / `RuleKeyword.keyword_name` |
| 3 | **规则串词法单元** | `IV0_low` | `RuleMethod.rule_description` 文本 |
| 4 | **档位词** | `low` / `very_low` / `medium` | 前端 `LEVEL_WORDS` / 后端 `FUZZY_LEVELS` / 引擎 `HS_MAPPING_DICT` |

**翻译关系**：

```
业务名 ──(环节5)──► 算法名 ──(环节8)──► 词法单元 ──(拆后缀)──► 档位词
  ▲                                        │
  └────────(环节12 反向翻译)────────────────┘
```

**第 4 层目前有三份互不一致的定义**（档位类缺陷的全部来源）：

| 位置 | 内容 | 档位数 |
|---|---|---|
| 前端 `constants/rule-const.ts::LEVEL_WORDS` | 3/5/7 档，**per-parameter** | 3/5/7 |
| 后端 `fuzzy_core/macros.py::FUZZY_LEVELS` | 3/5 档，**全局** | 3/5 |
| 引擎 `fuzzy_core/macros.py::HS_MAPPING_DICT` | 3 档语义（low/mid/high） | 3 |

前端已按 `keyword.fuzzy_level` 动态取词表（**per-parameter**），
引擎却用全局静态表 ⇒ **档位与桶错位一档**。

---

## 4. 端到端例子

**输入**：缺陷 `SHORTSHOT` / 严重度 `medium` / 位置 `DLSHORTSHOT1`；
当前 `IV0 = 30`（注射速度 1 段）；`IV0` 的 `RuleKeyword`：`range=[0,120]`, `fuzzy_level=5`, `step=10`。

**规则**（路由捞到的其中一条）：
```
IF SHORTSHOT_medium AND IV0_low THEN IV0_add_2
```

**逐环走一遍**：

| 环 | 发生了什么 | 结果 |
|---|---|---|
| 1-4 | 前端填表 → Schema 通过 → 校验通过 → 从 DB 反查 condition/parent_param，baseline 拿到 `IV0=30` | context 就绪 |
| 5 | `inj_spd_1` → `IV0`；`inj_pres_1` → `IP0` | `process_parameter = {'IV0': 30, 'IP0': 70, ...}` |
| 6 | `fuzzy` 引擎优先级高于 `empirical`，先跑 | — |
| 7 | 选库 `base` → 四级匹配 → `defect_code='SHORTSHOT'` → 档位过滤（`medium`）→ 去重 → 分流（numeric） | 拿到 N 条规则 |
| 8 | `parse_rule` 拆成前件 `[SHORTSHOT/medium, IV0/low]`、结论 `[IV0/add/2]` | 结构化 |
| 9 | 收参数名 `{IV0}`（剔除 SHORTSHOT）→ 查 `RuleKeyword` → `{lvl:5, min:0, max:120, step:10}` | 论域就绪 |
| 10-① | `σ=15`，`means=[0,30,60,90,120]`，`IV0=30` | μ = [0.1353, **1.0**, 0.1353, 0.0003, ~0] |
| 10-② | 门控定位 `index + HS_MAPPING_DICT['low'] = index + 0` → 指向 **very_low 桶** | 缺陷前件因非参数被剔除 ⇒ 只剩 1 个条件 ⇒ μ=0.1353（**本应是 1.0**） |
| 10-③ | `activations_sum` = 全部规则激活度和 | `activation = 0.1353 / sum × priority` |
| 10-④ | `solution_matrix[IV0] = +2.0` | 调整量 +2.0 |
| 11 | `delta = 2.0 × activation`；同参数多条规则 **直接相加** | `recommended_value = 30 + delta` |
| 12 | 译回 `inj_spd_1`；文案 `模糊推理建议提高一段注射速度：30 → 30.x`；按 `inj_` 前缀分到「注射参数」组 | suggestion.groups |
| 13 | 写回父记录 → 新 ProcessParameter → 新 TuningRecord(pending) → 新 Recommendation | 3 张表 |
| 14 | `PreviousSuggestion.vue` 显示「注射参数」组 + 方向图标 + 文案 | 工艺员看到 |

**注意第 10-② 环**：用户写的是 `IV0_low`（"速度偏低"），
引擎去 `very_low`（"极低"）桶取了隶属度，拿到 0.1353 而不是 1.0。
**调整量被摊薄到 13.5%**，而用户期望的是"速度确实偏低，该加"。

---

## 5. 各环节"谁能改 / 改什么"速查

| 环 | 现状 | 可动性 |
|---|---|---|
| 1 前端 | per-parameter 词表已正确 | 不动 |
| 2 HTTP | 契约清晰 | 不动 |
| 3 校验 | 与前端镜像 | 不动 |
| 4 装配 | 只读，设计清晰 | 不动 |
| 5 翻译 | 三条规则，有已知盲区（IPOS） | 小修 |
| 6 调度 | 单引擎异常被吞成空列表 | 可观察性 |
| 7 路由 | 去重已有；`base` 兜底已有 | 补日志 |
| 8 词法 | 档位词从右往左取第一个 | **小修（最长后缀）** |
| 9 论域 | per-parameter `lvl` 已正确；兜底造 `lvl=3` | 兜底策略 |
| 10 推理 | 档位→桶用全局表；归一化跨参数共享分母 | **重写核心** |
| 11 聚合 | 同参数 delta 直接相加 | **重写核心** |
| 12 规范化 | 零变化项丢弃 | 可动 |
| 13 落库 | 事务边界正确 | 不动 |
| 14 展示 | `rule_refs` 永远为空 | 补字段 |

---

## 6. 名词表

| 名词 | 含义 |
|---|---|
| 论域 | 参数的取值区间 `[min_val, max_val]`，隶属度铺桶的基准 |
| 档位 / level | 一组有序的模糊词（low/medium/high…），由 `RuleKeyword.fuzzy_level` 决定档位数 |
| 桶 / bucket | 论域被切成 `fuzzy_level` 段，每段一个隶属度函数 |
| 隶属度 μ | 某个值对某个桶的归属程度，[0,1] |
| 前件 / precondition | 规则的 IF 部分（条件） |
| 结论 / solution | 规则的 THEN 部分（调整量） |
| 门控 | 由规则前件决定"取哪个桶的隶属度"的一行 one-hot 向量 |
| 激活度 activation | 一条规则在当前工况下的适用强度 |
| 缺陷严重度 | 用户填的 `level`，决定命中哪一套规则（**不是**参数档位） |
| 缺陷位置 | `DL` + 缺陷名 + 段号 |
| specificity | 规则库匹配特异性，1=最精确 |

---

## 7. 本文档未回答的问题（留待讨论）

1. 缺陷前件应当是**路由条件**（精确匹配，命中/不命中）还是**连续门控**（参与加权）？
   现状是后者，但缺陷没有数值 ⇒ 实际被静默剔除 ⇒ 行为上等于前者，却付出了"看似在算、实际没算"的代价。
2. 激活度应该是**绝对强度**（μ 的某种聚合）还是**相对份额**（归一化后）？现状两者混用。
3. 同参数多条规则应**相加**还是**加权平均**？
4. `adjustment_factor`（trend 系数）应该乘在 delta 上还是只影响 confidence？
5. 建议值的单位：`add_2` 是绝对值、`reduce_30%` 是相对值 —— 两者最终都加到 `current_value` 上，语义是否自洽？
6. 规则库专用参数（`IPOS`/`CUSION`）的推荐该往哪里去？当前静默丢弃。
