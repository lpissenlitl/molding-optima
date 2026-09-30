# Infer 算法上下文边界重设计

> 本文档记录 `process/services/optimization_infer.py`（工艺优化 infer 服务）**算法边界划分重构**的讨论过程与设计决策。
> 核心问题：**算法（Engine）应该接什么 / 不应该接什么；编排层（Service）应该做什么 / 不应该做什么**。
>
> 配套文档：
> - [algorithm-context-design.md](file:///f:/items/moldingx/molding-optima/backend/_refs/system/algorithm/algorithm-context-design.md)（算法上下文双重来源设计，2026-07-02）
> - [infer-input-flattening-design.md](file:///f:/items/moldingx/molding-optima/backend/_refs/system/ai/infer-input-flattening-design.md)（输入扁平化设计）

---

## 1. 背景

### 1.1 重构对象

- 文件：`backend/process/services/optimization_infer.py`
- 入口：`OptimizationInferService.infer()`（行 165 附近）
- 对应接口：`POST /api/processes/optimization/infer/`

### 1.2 触发原因

infer 服务的算法上下文（`_build_engine_context`）原本：

- 内部调 `TuningRecord.objects.filter(...)`（违反"编排层不该查业务 DB"）
- 内部调 `analyze_iteration_trend`（编排层替算法做派生决策）
- 接收 `ProcessCondition` ORM 实例（编排方法接对象 → 限制了多种来源输入）
- 含 ORM 主键 `id`（数据访问层概念泄漏到算法层）
- 含算法派生字段 `defect_name` / `rule_library_code`（编排层替算法做决策）

### 1.3 重构目标

**核心目标**：通过**边界划分**让每一层责任明确，**不增加新能力**，只**减代码 + 划责任**。

---

## 2. 核心方法论：边界划分

整个重构的本质是**重新划界**——每一层都有自己的责任：

| 层 | 责任 | 不应做的事 |
|---|---|---|
| **数据访问层** | DB ↔ ORM | 业务决策 |
| **数据标准化层** | ORM → dict | 业务编排 |
| **业务编排层** | dict 流转 | 算法派生 |
| **算法层** | dict → Recommendation（纯函数）| 接触 ORM、查业务 DB |
| **持久化层** | ORM → DB | 业务编排 |

### 2.1 边界判断的通用问题

- 这一层**应不应该**知道 X？
- 这一层**应不应该**有 Y 的能力？
- 上下游调用方**应不应该**懂这一层的细节？

### 2.2 边界越权的反模式（本次重构专门解决的问题）

| 反模式 | 原本位置 | 修正 |
|---|---|---|
| 编排层替算法派生字段（`defect_name`）| `_build_engine_context` 接收 feedback 后擅自计算 | 编排层删除；算法自己从 input 推导 |
| 编排层代算法查私域 DB（`iteration_trend`）| 调 `TuningRecord.objects.filter` | 编排层删除；`tuning_result` 来自 feedback 用户输入 |
| 编排层用 ORM Model 跨 step 传递 | `_build_engine_context(condition: ORM, ...)` | 改为 `_build_engine_context(condition: dict, ...)` |
| 算法要求 ORM 入参 | Engine API | Engine API 不变，纯 dict 入参 |
| 上下文含 `id`（数据访问层概念）| context 含 `condition.id` | 删除；保留 `condition_no`（业务编号）|

---

## 3. 已划定的 7 类边界

### 3.1 服务边界（首次划界）

- **删除伪服务层**：`RecommendationService` 仅服务于 `optimization_infer` 一个调用方
- **命名边界**：`optimization_infer`（编排）+ `engine`（算法）分离
- **不再有**中间抽象层（YAGNI）

### 3.2 算法 vs 编排层

**算法层 = 纯函数**：

```
输入：dict
输出：List[Recommendation]
不查业务 DB
不接触 ORM Model
不需要懂业务逻辑
```

**编排层 = 业务流程编排**：

```
输入：HTTP API / dict
输出：HTTP 响应
业务决策、流程控制
```

**关键边界规则**：

- 算法可以查**自己的私域 DB**（如 FuzzyEngine 的 `RuleLibrary`）
- 算法**不应通过入参**让编排层查业务 DB
- 算法派生字段（`defect_name`、`rule_library_code`）由算法自己处理
- 编排层不替算法做决策（`iteration_trend` 来自用户 `tuning_result`，不是历史统计）

### 3.3 数据访问层 vs 业务编排层

```
数据访问层：DB ↔ ORM（仅 `_resolve_parent` + Step 5 落库）
数据标准化层：ORM → dict（5 个 `_serialize_*` + `_build_condition_data`）
业务编排层：纯 dict 操作（不接触 ORM）
```

**关键边界规则**：

- **编排方法不接 ORM 对象**（接 dict，多种来源兼容）
- ORM 生命周期只在 `infer()` HTTP 入口持有，**不跨 step 传递**
- 编排层可以查 DB（数据准备），但输出必须是 dict（保证算法是纯函数）

### 3.4 数据访问层概念 vs 算法特征

- **不含 `id`**（ORM 主键 = 数据访问层概念，不属于算法特征）
- **保留业务编号**（`condition_no` / `parameter_no`，业务追溯用，不是 `id`）

### 3.5 业务流程边界（6 步框架）

```
Step 0: 防御性校验入参（_validate_feedback）
Step 1: 构建基准参数（反查 + ORM→dict + baseline 构建）
Step 2: 构建算法上下文（business context + feedback → dict）
Step 3: 调用算法（纯函数，无 DB）
Step 4: 构建输出（应用推荐 + 建议展示）
Step 5: 数据落库（事务原子操作）
Step 6: 格式化响应
```

### 3.6 Step 1 内部职责（拆分后，最终状态）

```
- `_resolve_parent(condition_id, parent_seq_idx)` → ORM 二元组（数据访问）
- `_build_baseline(parameter_data, user_override)` → baseline dict（编排层，纯 dict）
- Step 1 直接用 `_to_full_dict(parent_param_orm)` 构造 parameter_data（不再走中间方法）
```

### 3.7 算法私域 vs 业务数据

| 类别 | 提供方 |
|---|---|
| **业务数据**（mold/machine/polymer/condition）| 编排层（`_serialize_*`）|
| **算法私域**（`iteration_trend`、`tuning_history`、`rule_library_code`）| 算法自己管 |
| **算法派生**（`defect_name`）| 算法自己从 input 推导 |
| **用户决策**（`tuning_result`）| 来自 `feedback`，不是历史查询 |

---

## 4. 6 步流程设计原则（业务边界）

### 4.1 Step 0：防御性校验

- 入参齐全性校验
- 失败立即抛异常，不进入后续步骤
- 校验逻辑可以理解为编排层的"前端守卫"

### 4.2 Step 1：构建基准参数（合并反查 + 构建）

- **职责合并**：`_resolve_parent`（反查）+ `_build_baseline`（构建）合并为单步
- **理由**：前端可能直接提供参数，也可能需要反查——本质都是"构建基准"
- **内部拆分**：2 个 helper 组合
  - `_resolve_parent` → ORM
  - `_build_baseline` → baseline dict
  - Step 1 中间直接用 `_to_full_dict(parent_param_orm)`（不再走中间方法）

### 4.3 Step 2：构建算法上下文

- 接收全 dict（condition/parameter/feedback）
- 输出纯 dict（不带任何 ORM 概念）
- 不查 DB（数据准备在 Step 1 完成）

### 4.4 Step 3：调用算法

- 纯函数调用：FuzzyEngine.recommend(context)
- 不接触 ORM
- 不查业务 DB（可查私域 DB）

### 4.5 Step 4：构建输出

- 应用推荐到 baseline
- 构建建议展示 payload

### 4.6 Step 5：数据落库

- ORM 实例（`condition_orm` / `parent_param_orm`）只在 `infer()` 内持有
- 落库直接使用 ORM 实例，不通过 step 之间传递

### 4.7 Step 6：格式化响应

- 输出 API 响应格式

---

## 5. 架构原则（已沉淀到 memory）

### 5.1 memory 索引

| Memory | 内容 |
|---|---|
| `优化推理6步流程设计准则` | 6 步流程设计 + 每步职责 |
| `上下文构建的数据标准化原则` | 数据准备层允许查 DB，输出必须是纯 dict |
| `算法上下文无ID与纯函数原则` | 算法不接触 ORM Model，只接收纯 dict |
| `算法输入禁止包含id字段` | context 不含 ORM 主键 |
| `缺陷反馈中"无缺陷"的业务定义` | DEFECTFREE keyword 处理 |
| `工艺规则关键词 Model 字段设计` | Mold/Polymer 等字段定义 |

### 5.2 核心架构原则（精炼）

1. **数据准备层**（Step 1-2）允许查 DB，负责补全字段完整
2. **算法层**（Step 3）不接触 ORM Model，只接收纯 dict
3. **关键边界**：入参不应让算法查业务 DB
4. **算法可查私域 DB**（如 RuleLibrary），但通过自己的内部机制，不通过入参传递
5. **业务数据**（mold/machine/polymer）由编排层提供
6. **算法派生字段**（defect_name / rule_library_code）由算法自己处理
7. **编排方法接 dict**（多种来源兼容：ORM 序列化、前端直传、其他 service）

---

## 6. 已实施的代码改动

### 6.1 Commit 历史

| Commit | 说明 |
|---|---|
| `a3d3a75` | refactor(process) 消除伪服务层，编排层自包含 -198 行 |

### 6.2 Step 1 实施：合并 `_resolve_parent` + `_build_baseline`

**改动**（已完成）：
- `infer()` 中 `_resolve_parent` + `_build_baseline` 合并为单步调用
- `_build_baseline` 接收 `(condition_id, parent_seq_idx, user_override)`
- 返回 `(condition, parent_param, baseline)` 三元组
- `_resolve_parent` 保留为内部 helper

### 6.3 Step 2 实施（完整重构）

#### 改动 1：`_build_engine_context` 接 dict
- 入参从 `(condition: ORM, parent_param: ORM, feedback)` 改为 `(condition: dict, parameter: dict, feedback)`
- 不再访问 ORM 属性
- 接收来自 `_build_condition_data` + `_serialize_parameter` 的 dict

#### 改动 2：新增 4 个序列化器
- `_serialize_condition(condition)`：condition_no / status / origin_type / shot_index / injection_index
- `_serialize_machine(machine)`：7 字段（按 `parameter_init.py` 命名规范）
- `_serialize_polymer(polymer)`：9 字段（按 `parameter_init.py` 命名规范）
- `_serialize_mold(mold)`：5 字段（Mold 主表字段）

#### 改动 3：删除 `_serialize_record`
- 不再使用（删除 iteration_trend / tuning_history 业务）

#### 改动 4：删除 `TuningService` import
- 不再调 `analyze_iteration_trend`

#### 改动 5：新增 `_build_condition_data(condition_orm)`
- ORM → 4 子 dict（process_condition/machine/polymer/mold）

#### 改动 6：`_build_baseline` 改为接收 dict
- 入参 `(condition_id, parent_seq_idx, user_override)` → `(parameter_data, user_override)`
- 输出：`baseline dict`（不再返回 ORM）

#### 改动 7：`infer()` 内 Step 1 拆分
- `_resolve_parent` → `_build_condition_data` → `_serialize_parameter` → `_build_baseline`
- 4 个 helper 组合完成 Step 1

#### 改动 8：`infer()` 内 Step 5 用 ORM 实例
- ORM 实例（`condition_orm` / `parent_param_orm`）只在 `infer()` 内持有
- Step 5 落库直接使用 ORM 实例，不通过 step 之间传递

### 6.4 字段命名映射（关键）

按 `parameter_init.py` 的 `_MACHINE_TO_MACHINE` / `_POLYMER_TO_POLYMER` 规范：

| ORM 字段 | 算法入参（context 字段名）|
|---|---|
| `machine.max_set_injection_speed` | `machine.max_set_injection_velocity` |
| `machine.max_set_holding_speed` | `machine.max_set_holding_velocity` |
| `polymer.recommended_melt_temp` | `polymer.recommend_melt_temperature` |
| `polymer.recommended_mold_temp` | `polymer.recommend_mold_temperature` |
| `polymer.recommended_shear_line_speed` | `polymer.recommend_shear_linear_speed` |

### 6.5 Step 0 提取越权已修（P1）

**问题**：Step 0（infer() 193-197）原代码从 `feedback` 提取了 3 个值：
```python
defect_feedbacks = feedback.get("defect", []) or []
observations = feedback.get("observations", []) or []
tuning_result = feedback.get("tuning_result")
```

**问题点**：
1. Step 0 的职责是"防御性校验"——提取不属于 Step 0
2. Step 2 内部（`_build_engine_context` 501-503）**又重复提取一次** —— DRY 违反
3. 提取变量跨 Step 1-5 共 ~77 行 —— 跨步共享局部变量是反模式

**改动**（已完成）：
1. **删除 Step 0（193-197）的提取** —— 只保留 `_validate_feedback`
2. **Step 5 入口（245-246）一次性提取** —— 贴近使用方（跨度从 ~77 行缩为 ~28 行）
3. Step 2 `_build_engine_context`（501-503）保留提取 —— 该方法内部需要 defect_feedbacks/observations/tuning_result 构造 context

**净效果**：
- Step 0 职责单一（只校验）
- 总提取从 3 处（Step 0 + Step 2 + Step 5）减为 2 处（Step 2 + Step 5）
- Step 5 提取变量生命周期限定在 Step 5 内

**测试验证**：
- `test_infer_smoke.py` ✅ PASS
- `verify_bug1_validate_feedback.py` ✅ PASS
- `verify_bug2_tuning_record.py` ✅ PASS
- `verify_validate_feedback_backend.py` ✅ PASS

### 6.6 Step 0 校验逻辑修正：keyword_id → keyword_name

**问题**：原 `_validate_feedback` 校验 `keyword_id` 必填，但 schema 注释（`schemas/optimization_infer.py:33`）明确说：
> "keyword_id / keyword_name：可空（用户未选时为 null；后端匹配走 keyword_name）"

这是**校验逻辑与设计意图不一致**——识别缺陷的依据是 `keyword_name`，不是 `keyword_id`（id 只是冗余存的元数据）。

**改动**（已完成）：
1. **后端 `_validate_feedback`**（317-321 行）：`keyword_id is None` → `keyword_name is None`
2. **前端 `validateFeedback`**（`OptimizationCreate.vue:738-740`）：`keyword_id == null` → `keyword_name == null`
3. **测试更新**：
   - `verify_bug1_validate_feedback.py`：交换 "缺 id" / "缺 name" case 的预期值
   - `verify_validate_feedback_backend.py`：交换 "缺 id" / "缺 name" case 的预期值

**净效果**：
- 校验逻辑与 schema 注释一致
- keyword_id 可空（仅冗余存），符合设计

**测试验证**：
- `test_infer_smoke.py` ✅ PASS
- `verify_bug1_validate_feedback.py` ✅ 19/19 PASS
- `verify_validate_feedback_backend.py` ✅ 13/13 PASS

### 6.7 （已撤销）算法字段白名单设计

> ⚠️ **状态**：本次实验已被 §6.8 取代。用户反馈："我并没有明确告诉你算法需要什么样格式的参数，所以你怎么做都是错的"，同时指出 Step 1 的 4 个 `_serialize_*` 才是真正的越权问题。
>
> 本节描述的 `_ALGORITHM_PARAM_FIELDS` 白名单 + Step 2 显式挑选已被**完全撤销**（用户手动从工作目录删除）。Step 2 字段选择待后续明确算法入参格式后再讨论。
>
> --- 历史记录（保留供参考）---

**原问题**：原 `_build_engine_context` 直接把 baseline dict 喂给算法，baseline 可能含 ORM 元数据 / FK 对象 / 业务索引字段——这些都会**泄漏到算法上下文**。

**原改动**（已撤销）：
1. 新增 `_ALGORITHM_PARAM_FIELDS`（模块级 frozenset）：83 个工艺字段，按 prefix 分组。
2. `_build_engine_context` 显式挑选白名单字段喂算法。

**被取代原因**：
- 白名单方案"算法需要哪些字段"是用户尚未明确的——盲目设计是错的。
- 真正的越权在 Step 1：4 个 `_serialize_*` 已做字段选择 + 字段重命名。
- 修复重点应是 Step 1 取消越权，字段选择留给 Step 2。

---

### 6.8 Step 1 取消越权字段选择（4 个 _serialize_* 删除）

**问题**：Step 1 的 4 个 `_serialize_*`（`_serialize_condition` / `_serialize_machine` / `_serialize_polymer` / `_serialize_mold`）越权做了**字段选择**：
- `_serialize_machine` 重命名 ORM 字段（`_speed` → `_velocity`）——这不是转换职责
- 4 个都手动挑了业务需要的字段子集——越权（业务字段选择是 Step 2 的事）

**边界重划**（Step 1 vs Step 2）：
| Step | 职责 | 示例 |
|---|---|---|
| Step 1 | ORM → 完整 dict（仅排除关系字段）| `_to_full_dict(condition)` 返回全部非 FK 字段 |
| Step 2 | dict → dict（字段选择 + 重命名 + 组装）| 未来 Step 2 才决定哪些字段喂算法、是否重命名 |

**改动**（已完成）：
1. **新增模块级 helper `_to_full_dict(instance)`**：
   ```python
   def _to_full_dict(instance):
       if instance is None:
           return {}
       return {
           f.name: getattr(instance, f.name)
           for f in instance._meta.fields
           if not f.is_relation
       }
   ```
   - 仅排除 ORM 关系字段（避免 ORM 对象嵌套到 dict）
   - 不裁剪元数据 / 业务字段 ——留给 Step 2 决定
2. **`_build_condition_data` 改为调用 `_to_full_dict`**：
   ```python
   return {
       'process_condition': _to_full_dict(condition),
       'machine': _to_full_dict(condition.injection_machine),
       'polymer': _to_full_dict(condition.polymer),
       'mold': _to_full_dict(condition.mold),
   }
   ```
3. **`_serialize_parameter` 改为一行委托**：
   ```python
   @staticmethod
   def _serialize_parameter(parameter):
       return _to_full_dict(parameter)
   ```
4. **删除 4 个越权的 `_serialize_*`**（总计 -72 行）。

**未改动**：Step 2 `_build_engine_context`（暂不做字段选择，等明确算法入参格式后再调整）。

**净效果**：
- Step 1 只做 ORM → dict 转换，不再越权做业务字段选择
- 字段选择 = Step 2 的单一职责（但 Step 2 尚不动）
- 原 4 个序列化器名称与未来可能的重新划分不冲突

**测试验证**：
- `test_infer_smoke.py` ✅ PASS
- `verify_bug1_validate_feedback.py` ✅ 19/19 PASS
- `verify_validate_feedback_backend.py` ✅ 13/13 PASS
- `verify_bug2_tuning_record.py` ✅ Bug 2 验证通过
- `verify_step1_full_dict.py` ✅ ALL PASSED（7 个新用例）
  - `_to_full_dict(None)` → `{}`
  - FK 字段被排除
  - 元数据 / 业务字段 / 工艺字段都保留
  - `_serialize_parameter` 不裁剪字段
  - `_build_condition_data` + 4 个越权 `_serialize_*` 已删除

### 6.9 "build condition" 职责迁移到 Step 2（_build_engine_context）

**问题**：`optimization_infer.py` 原 `_build_condition_data`（Step 1）有逻辑越权。

> 用户原话："我们的 condition 是能够确定模具的哪个浇注系统、也能够确定注塑机的哪个射台，**所以 build condition 这一部分代码我建议放在 build context 中**"

**关键字段**：
- `ProcessCondition.injection_index`：决定注塑机的哪个射台
- `ProcessCondition.shot_index`：决定模具的哪一射（哪条浇注系统）
- `ProcessCondition.process_context_snapshot`：模具嵌套字段快照

**这意味着** `_build_condition_data` 不能是 Step 1 的职责——Step 1 只做 ORM → dict，不知道算法需要什么子维度。

**边界重划**：
| Step | 职责 | 与 build condition 关系 |
|---|---|---|
| Step 1 | 反查 ORM + ORM → dict（_to_full_dict） | 不该 build condition |
| Step 2 (_build_engine_context) | 接 condition ORM，自己构造 4 子 dict | **build condition 是 build context 的一部分** |

**改动**（已完成）：
1. **删除 `_build_condition_data` 方法**（Step 1 不该有 build condition 逻辑）。
2. **`_build_engine_context` 签名变更**：`condition: ProcessCondition`（接 ORM）。
3. **Step 2 内部构造 4 子 dict**：
   ```python
   context = {
       'process_condition': _to_full_dict(condition),
       'machine': _to_full_dict(condition.injection_machine),
       'polymer': _to_full_dict(condition.polymer),
       'mold': _to_full_dict(condition.mold),
       'process_parameter': parameter,
       ...
   }
   ```
   `process_condition` 含 `shot_index` / `injection_index` / `process_context_snapshot` ——未来 Step 2 根据这些字段决定 machine/mold 的精细子维度。
4. **infer() Step 1 调整**：`parameter_data = _to_full_dict(parent_param_orm)`，直接传 `condition_orm` 给 Step 2。
5. **删除过时的 `verify_algorithm_whitelist.py`**（untracked 文件，对应 §6.7 已撤销的代码）。
6. **更新 `verify_step1_full_dict.py`**：移除对 `_build_condition_data` 的测试用例。
7. **新增 `verify_build_context.py`**（7 个用例验证 Step 2 自负责 build condition）。

**净效果**：
- "build condition" 职责从 Step 1 迁移到 Step 2 ——职责清晰。
- Step 2 能看到 condition 完整字段（injection_index / shot_index / process_context_snapshot）——为未来精细化算法入参预留接口。
- Step 1 只做反查 + ORM → dict（最简）。

**测试验证**：
- `test_infer_smoke.py` ✅ PASS
- `verify_bug1_validate_feedback.py` ✅ 19/19 PASS
- `verify_validate_feedback_backend.py` ✅ 13/13 PASS
- `verify_bug2_tuning_record.py` ✅ Bug 2 验证通过
- `verify_step1_full_dict.py` ✅ ALL PASSED（5 个用例）
- `verify_build_context.py` ✅ ALL PASSED（7 个新用例）：
  - context 含关键字段
  - process_condition 含决定子维度的字段（shot_index / injection_index / process_context_snapshot）
  - machine / polymer / mold 是 dict（_to_full_dict 已调）
  - None 子对象安全处理
  - process_parameter 透传
  - feedback 字段透传
  - `_build_condition_data` 已删除

---

### 6.10 Step 2 精细化：优化算法与初始化算法的 context 需求差异

**问题**：`optimization_infer.py` 之前用 `_to_full_dict` 简化版占位，导致：
1. `machine` 传整台机器（含所有射台）——未按 `condition.injection_index` 选
2. `mold` / `polymer` / `process_condition` 都透传完整 dict ——优化算法不需要这些细节
3. `process_condition` 在 context 里 ——但它只是索引和元数据，不是输入特征

> 用户原话：“工艺参数优化算法实际上不关心模具、材料，但是关心注塑机当前的设定范围，这也是一个关键点，和工艺参数初始化还不一样”

**关键洞察**：优化算法 vs 初始化算法对 context 的需求差异：

| 字段 | 初始化（`parameter_init`） | 优化（`optimization_infer`） |
|---|---|---|
| mold 嵌套（产品重量/浇口/壁厚） | ✅ 必填 | ❌ 不关心 |
| polymer 完整（推荐温度/缩写） | ✅ 必填 | ❌ 不关心 |
| **machine HMI 范围**（`max_set_*`） | ⚠️ 部分需要 | ✅ **核心约束** |
| `process_parameter`（baseline） | ❌ 没有 | ✅ **核心输入** |
| `defect_feedbacks` | ❌ 没有 | ✅ **核心输入** |

**优化算法的 context 关键决策**（与用户确认）：
- `machine`：按 `condition.injection_index` 选 `InjectionUnit`、全字段透传（让算法自挑 HMI 范围字段）
- `polymer_abbreviation` / `product_category`：RuleQueryService 的四级特异性匹配参数——None 时不参与规则搜索（仅匹配通用规则）；填具体值才启用 polymer/product 维度的精确 → 通用 fallback 匹配链
- 不传 `process_condition` / `mold` / `polymer` 完整 dict

**改动**（已完成）：
1. **`_resolve_parent` 加 `prefetch_related` 避免 N+1**：
   ```python
   condition = (
       ProcessCondition.objects
       .select_related('injection_machine', 'polymer', 'mold')
       .prefetch_related('injection_machine__injection_units')
       .get(id=condition_id)
   )
   ```
2. **`_build_engine_context` 重构**：
   - 不含 `process_condition` / `mold` / `polymer` 三个 key
   - `machine`：调 `_extract_machine_unit(condition)` 按 `injection_index` 选 `InjectionUnit`
   - 新增 `polymer_abbreviation` / `product_category` 两个单字段（供 `RuleQueryService`）
3. **新增 `_extract_machine_unit(condition)` helper**：
   - 按 `condition.injection_index or 0` 选 `InjectionUnit`
   - 越界 返回 `{}` + warning（不抛错，由下游 fail-fast 守卫阻断）
   - `machine=None` 返回 `{}`

**覆盖语义**：user input：“process_context 应该包含这些信息，condition 只在创建/更新时快照，工艺优化时应该不存在” —— 明确 `process_context` 不参与运行时工艺优化。

**净效果**：
- Step 2 context 从 8 个字段（`process_condition` / `machine` / `polymer` / `mold` / `process_parameter` / 3× feedback）减为 5 个（`machine` / `process_parameter` / `feedback` / `polymer_abbreviation` / `product_category`）
- context 不再传递优化算法不关心的字段，算法输入更清晰
- 避免深层查询（GatingSystem/Cavity/Gate 嵌套），减少 ORM 负担

**后续简化（feedback 整体透传）**：
> 用户原话：“整个 feedback 传给算法不就可以了？”

feedback 本质上是**业务输入包**，内部字段（`defect` / `observations` / `tuning_result`）是同一回事的不同部分，原本可以在 context 里统一传 `feedback: feedback` 而不是拆三个字段。

**改动**（已完成）：
1. **`_build_engine_context` 取消三件套拆分**：
   ```python
   # 原来（拆 3 个字段）
   'defect_feedbacks': feedback.get('defect', []),
   'observations': feedback.get('observations', []),
   'tuning_result': feedback.get('tuning_result'),
   # 现在（整体透传）
   'feedback': feedback,
   ```
2. **`FuzzyEngine` 同步调整**：两处 `context.get('defect_feedbacks')` → `(context.get('feedback') or {}).get('defect')`
   - `recommend` 方法
   - `is_available` 方法
3. **`FuzzyEngine` docstring 更新**：context 接口契约同步

**净效果**：
- Step 2 context 从 5 字段减为 5 字段（不过只是从拆 3 合 1），但代码净减 4 行（不需提取三件套）
- 语义清晰：feedback 是“业务输入包”，传一个 dict 即可
- 未来 feedback 加新字段不需改动 _build_engine_context（向后兼容）

**后续简化（context 字段顺序与本质理解）**：

> 用户原话：“本质上逻辑还是没变，一次工艺还是包含注塑机、材料、模具信息，然后基于当前的工艺参数、反馈信息调用算法进行工艺参数优化。但是在优化阶段，材料、模具信息就不重要了，我们本质是根据设备的可调整范围和规则进行调整”

context 字段顺序按业务语义重排：注塑机 → 规则匹配器 → 参照工艺参数 → 反馈

```python
context = {
    'machine': machine,                    # 注塑机（按 injection_index 选 InjectionUnit）
    'polymer_abbreviation': ...,           # 规则匹配参数（RuleQueryService 四级特异性）
    'product_category': ...,               # 规则匹配参数（RuleQueryService 四级特异性）
    'process_parameter': parameter,        # 参照工艺参数 baseline
    'feedback': feedback,                  # 业务输入包（缺陷反馈 + 观察 + 试模结果）
}
```

**业务本质（边界总结）**：
- **工艺条件（业务实体）** = 注塑机 + 材料 + 模具
- **优化阶段（算法入参）** = 注塑机可调整范围 + 规则 + 工艺参数 + 反馈
- **不关心** 模具嵌套细节（GatingSystem/Cavity/Gate）、材料固有属性 ——这些是工艺初始化的入参

**后续扩展（Port-Adapter 模式：算法侧声明约束 + 数据准备层翻译）**：

> 用户原话：“最主要的原因其实是规则部分的约束，所以必须做转换，要么在算法部分做转换，但是那样职责不清晰，可以让算法提供约束的格式，在上一层做转换”（2026-09-30）
>
> 用户补充：“noz_temp 并不是没有映射，对应的映射是 NT”（2026-09-30）
>
> 用户补充：“cool_t 也有映射 CT”（2026-09-30）
>
> 用户原则：“映射字段不是以 parameter 为准，而是应该以算法侧的 keyword 为准”（2026-09-30）
>
> 用户补充：“理论上我们 ProcessParameter 的字段和算法中的字段我们都会全部定义好的，不存在遗漏的情况，所以理论上是不会出现原样保留的场景，除非传给后端的字段就已经是算法所需的字段”（2026-09-30）

**设计原则（以算法侧为准则）**：

- **以算法侧（RuleKeyword.keyword_name）为权威源**：表中每个 mapping 都对应实际存在的算法 keyword
- **理论上 ProcessParameter 中每个工艺字段都能在此找到映射**（验证：当前 70/71 已覆盖，仅 `met_lim_t` 为边界 case）
- **未映射场景只发生在**：业务控制字段（如 `_stg` / `_mode`）或算法未启用的边界 case（如嫧胶延时 `met_lim_t`）
- **业务控制字段**（如 `inj_stg` / `hold_stg` / `pre_met_decomp_mode` 等）不属于 fuzzy rule 输入范畴，不会出现在 process_parameter dict 中（即使出现也原样保留）

**问题背景**：fuzzy rule 用的字段名（来自 `RuleKeyword.keyword_name`）是**稳定的业务专家约定**。在 molding-optima 中，业务命名（ProcessParameter 模型）与算法命名（RuleKeyword 主数据）**实际上是不一致的**：

| 业务字段 | 算法字段（RuleKeyword） | 类型 |
|---|---|---|
| `inj_pos_1` | `IL1` | 前缀映射 |
| `inj_spd_1` | `IV1` | 前缀映射 |
| `inj_pres_1` | `IP1` | 前缀映射 |
| `noz_temp` | `NT` | 完整字段名映射 |
| `cool_t` | `CT` | 完整字段名映射 |
| `vps_pos` | `VPTL` | 完整字段名映射 |
| `met_pos_1` | `ML1` | 前缀映射 |

**设计**：采用 **Port-Adapter 架构**——算法侧负责**声明约束**，数据准备层负责**适配翻译**，业务编排层只懂业务。

```
业务编排层（service）──[1]──> 数据准备层（adapter）──[2]──> 算法层（port）
业务命名                                       算法命名
inj_pos_1 / inj_spd_1 / noz_temp            IL1 / IV1 / NT
```

**1. 算法侧（Port）**：声明字段命名约定

```python
# process/engines/fuzzy/fuzzy_engine.py
class FuzzyEngine(AIEngineBase):
    # 以算法侧 RuleKeyword 为准则
    FIELD_NAME_ALIAS: Dict[str, str] = {
        "inj_pos":   "IL",   # 注射位置 1-6 → IL1-IL6
        "inj_spd":   "IV",   # 注射速度 1-6 → IV1-IV6
        "inj_pres":  "IP",   # 注射压力 1-6 → IP1-IP6
        "noz_temp":  "NT",   # 喷嘴温度 → NT
        "cool_t":    "CT",   # 冷却时间 → CT
        "vps_pos":   "VPTL", # VP 切换位置 → VPTL
        # ... 完整映射表（含 hold/met/嫧胶动作/注射耗时等）
    }
```

**2. 数据准备层（Adapter）**：按约束翻译

```python
# process/services/optimization_infer.py
def _normalize_field_name_by_spec(params, field_spec):
    """业务命名 → 算法命名（按算法侧声明的 FIELD_NAME_ALIAS 翻译）"""
    if not field_spec:
        return dict(params)  # 快路径

    normalized = {}
    for key, value in params.items():
        # 优先 1：完整字段名映射（如 noz_temp → NT）
        if key in field_spec:
            normalized[field_spec[key]] = value
            continue
        # 优先 2：前缀 + 数字后缀映射（如 inj_pos_1 → IL1）
        # 注意：必须保证后缀是纯数字，避免 noz_temp 被拆成 noz + temp
        prefix, sep, suffix = key.rpartition('_')
        if sep and suffix.isdigit() and prefix in field_spec:
            normalized[f"{field_spec[prefix]}{suffix}"] = value
        else:
            normalized[key] = value
    return normalized
```

**3. `_build_engine_context` 调用**：业务 → 算法的唯一翻译边界

```python
algorithm_params = _normalize_field_name_by_spec(
    parameter, FuzzyEngine.FIELD_NAME_ALIAS,
)
context['process_parameter'] = algorithm_params
```

**好处**：

| # | 优点 | 解释 |
|---|------|------|
| 1 | **规则稳定** | fuzzy rule 用的字段名（`FIELD_NAME_ALIAS`）与规则一起维护 |
| 2 | **算法不耦合业务** | FuzzyEngine 不知道 `inj_pos_1` 这种东西存在（纯函数） |
| 3 | **可扩展多算法** | ExpertEngine 等也可声明自己的 `FIELD_NAME_ALIAS` |
| 4 | **可演进性** | 前端改命名 → 只改 helper（业务/算法/规则都不动） |

**当前状态**：`FuzzyEngine.FIELD_NAME_ALIAS` 已填入完整映射表（基于 RuleKeyword + ProcessParameter 实际数据），业务命名 → 算法命名 翻译生效。**70/71 业务字段已覆盖**（仅 `met_lim_t` 为边界 case）。

**完整性检查**：通过脚本（`tmp_check_mapping.py`，已删）扫了 ProcessParameter 中 71 个工艺字段，仅 `met_lim_t`（嫧胶延时，算法侧未启用）未映射。

**改动**（已完成）：
1. **`FuzzyEngine.FIELD_NAME_ALIAS`**：填入完整映射表（25 项映射），以算法侧 RuleKeyword 为准则
2. **`_normalize_field_name_by_spec`**：升级 helper 支持两种翻译模式（完整字段名 + 前缀 + 数字后缀）
3. **`_build_engine_context`**：调用 helper（Step 2 作为唯一翻译边界）
4. **`FuzzyEngine` 顶层 import**：从 lazy 提到顶层（FIELD_NAME_ALIAS 类变量需顶层可见）
5. **`verify_build_context.py`**：新增 [10]-[14] 测试

**测试验证**：
- `verify_step1_full_dict.py` ✅ ALL PASSED（5 个用例）
- `verify_build_context.py` ✅ ALL PASSED（14 个用例）：
  - 原 9 个用例不变
  - 新增 5 个字段名翻译用例：
    - [10] 空 FIELD_NAME_ALIAS → 快路径原样输出
    - [11] 非空 spec → 按 prefix 映射重命名（`inj_pos_1 → IL1` 等）
    - [12] 完整映射下所有工艺字段都被翻译 + `met_lim_t` 边界 case 原样保留
    - [13] 原 dict 不被修改（防御性拷贝）
    - [14] FuzzyEngine.FIELD_NAME_ALIAS 实际生效（`_build_engine_context` 业务→算法 真实转换）
- `test_infer_smoke.py` ✅ PASS

`_serialize_parameter` 是 Step 1 拆分期间的遗留方法，现在已无调用方（Step 1 直接用 `_to_full_dict`）。

> 用户原话：“我们好像是有全局方法 to_dict，序列化数据，你看看是否不需要自己再定义？”

全局 `to_dict()`（`AbstractBaseModel.to_dict`）与 `_to_full_dict` 有实质差异：
- `_to_full_dict`：**直接排除** FK 字段（不含 `_id` 后缀）
- 全局 `to_dict()`：FK 转 `{name}_id`（如 `process_condition_id` / `parent_param_id`）

**不能用 `to_dict()` 替换 `_to_full_dict`**——`_create_new_parameter` 用 `**parameters_dict` 展开传给 `ProcessParameter.objects.create(process_condition=condition, parent_param=parent_param, ...)`。若 `parameters_dict` 含 `process_condition_id`，会与显式传入的 ORM 冲突，运行报 `TypeError`（这正是 §6.8 注释里强调的字段冲突点）。

**改动**（已完成）：
1. 删除 `_serialize_parameter` 死方法（Step 1 改用 `_to_full_dict`）
2. 更新 `_build_baseline` docstring（移除 `_serialize_parameter` 引用）
3. 更新 `verify_step1_full_dict.py`：移除 `_serialize_parameter` 测试用例，新增“已删除”回归检查（[4]）

**测试验证**：
- `verify_step1_full_dict.py` ✅ ALL PASSED（5 个用例）
  - `_to_full_dict(None)` → `{}`
  - FK 字段被排除（`process_condition` / `parent_param` 不在结果中）
  - ORM 元数据 / 业务字段 / 工艺字段都保留
  - `_serialize_parameter` 已删除（回归检查）
  - `_build_condition_data` + 4 个越权 `_serialize_*` 已删除
- `verify_build_context.py` ✅ ALL PASSED（9 个用例）：
  - context 含 5 关键字段 + feedback 整体透传
  - machine 按 `injection_index` 选 `InjectionUnit`（含 HMI 范围字段）
  - `injection_index=1` → 选第二台
  - `injection_index` 越界 → `{}` + warning
  - `injection_index=None` → 默认选第一台
  - `injection_machine=None` → `{}`
  - `polymer_abbreviation` / `product_category` 单字段提取（含 None 安全）
  - `process_parameter` / `feedback` 整体透传
  - `_build_condition_data` 已删除（回归检查）
- `test_infer_smoke.py` ✅ PASS

---

### 6.11 Step 3 接口契约清晰化（EngineContext TypedDict）

> 用户原话：“先确定好接口格式，虽然算法的接口一般不会限制那么严格，但是还是应该有对应的格式”（2026-09-30）

**问题**：

`_call_engines(context: Dict[str, Any])` 使用隐式契约——Step 2 构造了 5 字段（machine / polymer_abbreviation / product_category / process_parameter / feedback），但 Step 3 完全没有 schema 约束：
- Step 2 改了字段名 → Step 3 不会报错（运行时 key missing 才暴露）
- IDE / 类型检查不能提示需要的字段
- 算法侧 `AIEngineBase.recommend` 接口文档已过时（列了 9 字段，实际只给 5 字段）

**设计**：采用 `TypedDict`（PEP 589）：

```python
from typing import TypedDict

class EngineContext(TypedDict):
    """算法引擎输入 context 的标准格式（Step 2 构造，Step 3 使用）"""
    machine: Dict[str, Any]                  # 设备信息（InjectionUnit HMI 范围）
    polymer_abbreviation: Optional[str]      # 材料简称（RuleQueryService L1/L2 匹配）
    product_category: Optional[str]          # 产品类别（RuleQueryService L1/L3 匹配）
    process_parameter: Dict[str, Any]        # 工艺参数（已翻译为算法侧命名）
    feedback: Dict[str, Any]                 # 反馈信息（整体透传）

# 运行期 fail-fast 验证集合
_REQUIRED_CONTEXT_KEYS = frozenset(EngineContext.__annotations__.keys())
```

**为什么用 TypedDict**：
- 保留 `Dict` 调用风格（`context['machine']` 不用改成 `context.machine`）
- 提供 IDE / mypy 类型提示
- 0 运行成本（不像 dataclass 需实例化）

**入口验证（fail-fast）**：在 `_call_engines` 入口校验 5 字段齐全性：

```python
def _call_engines(self, context: EngineContext) -> Dict[str, Any]:
    # ---- 入口验证：5 字段 schema 完整性 ----
    if not context:
        _logger.warning("[optimization_infer] _call_engines context 为空")
        return self._empty_engine_result()
    missing = _REQUIRED_CONTEXT_KEYS - set(context.keys())
    if missing:
        _logger.warning(
            "[optimization_infer] _call_engines context 缺字段: %s", missing,
        )
        return self._empty_engine_result()
    # ... 后续调用
```

**改动**（已完成）：
1. **`EngineContext` TypedDict**：定义 5 字段 schema（模块级常量）
2. **`_REQUIRED_CONTEXT_KEYS`**：从 `EngineContext.__annotations__` 推导，保持同步
3. **`_call_engines`**：类型 `Dict[str, Any]` → `EngineContext` + 入口验证
4. **`_empty_engine_result`**：提取空返回结构（消除重复字面量）
5. **`AIEngineBase.recommend` 文档**：更新为 5 字段 schema（原 9 字段列表已过时）

**测试验证**：
- `verify_build_context.py` ✅ ALL PASSED（17 个用例，**新增 [15]-[17]**）：
  - [15] EngineContext schema 定义（5 字段） + `_REQUIRED_CONTEXT_KEYS` 同步
  - [16] `_call_engines` 空 context → 返回空结果（`_empty_engine_result`）
  - [17] `_call_engines` 缺字段 context → 返回空结构 + warning 日志
- `verify_step1_full_dict.py` ✅ ALL PASSED（5 个用例）
- `test_infer_smoke.py` ✅ PASS

---

## 7. 当前文件状态

### 7.1 文件结构

```
backend/process/services/
├── optimization_infer.py       ← 主入口（已重构）
├── parameter_init.py           ← ExpertEngine 走这里（独立路径）
└── （已删除 RecommendationService.py）
```

### 7.2 当前 `optimization_infer.py` 方法清单

**Step 实现**：
- `_validate_feedback(feedback)` — Step 0
- `_resolve_parent(condition_id, parent_seq_idx)` — Step 1a（数据访问 + select_related/prefetch_related）
- `_to_full_dict(instance)` — 模块级 helper（ORM → 完整 dict，仅排除关系字段）
- `_build_baseline(parameter_data, user_override)` — Step 1c（编排层）
- `_build_engine_context(condition_orm, parameter, feedback)` — Step 2（接 condition ORM，按 injection_index 选 InjectionUnit）
- `_extract_machine_unit(condition)` — Step 2 子方法（machine 提取 helper）
- `_snapshot_parameter(parameter)` — baseline snapshot

**Step 3-4**：
- `_call_engines(engine_context)` — Step 3
- `_apply_recommendations_to_baseline(...)` — Step 4a
- `_build_suggestion_payload(...)` — Step 4b

**Step 5 落库**：
- `_update_previous_tuning_record(...)`
- `_update_previous_recommendation_is_adopted(...)`
- `_create_new_parameter(...)`
- `_create_new_tuning_record(...)`
- `_create_new_recommendation(...)`

### 7.3 未提交状态

```
M backend/process/services/optimization_infer.py   ← 当前所有改动未提交
M backend/process/engines/expert/expert_engine.py  ← 上轮 ExpertEngine bug 修复
M backend/process/engines/expert/algorithm_engine.py
M backend/process/engines/expert/param_types.py
M backend/process/engines/expert/tests/test_vp_switch_mode_smoke.py
M backend/process/schemas/__init__.py
?? backend/process/schemas/tuning.py
```

---

## 8. 待续事项

按"一步步"原则，本次重构**未做完**的事项：

| 优先级 | 项目 | 说明 |
|---|---|---|
| **新 P0** | `_build_engine_context` 显式选择算法字段 | 不在 Step 1 做白名单约束，在 Step 2（算法 context 构建环节）明确算法依赖的字段子集——这是"清晰数据"环节（边界划分原则） |
| **新 P0** | 修复 `verify_fail_fast_infer.py` 过期 mock | mock `_recommendation_service` 已不存在（Step 1 消除伪服务层后未更新），需改为 mock `_call_engines` |
| **P1** | Step 0 提取越权已修 | ✅ 2026-09-30：删除 Step 0（193-197）提取；Step 5 入口（245-246）一次性提取；总提取从 3 处减为 2 处（Step 2 + Step 5） |
| P1 | Mold 嵌套字段 | `gate_type` / `ave_thickness` / `product_weight` 在 `condition.process_context_snapshot` 里，需要 `_strip_ids` 工具 + snapshot 路径 |
| P1 | `_resolve_parent` 加 `select_related` | 避免 lazy load（N+1 查询） |
| P2 | ExpertEngine 处理 | `backend/process/engines/expert/expert_engine.py` 当前是死代码——`parameter_init.py:896` 直接调 `ProcessInitializer`，不走 ExpertEngine 注册中心 |
| P2 | Step 4 拆分 | `_apply_recommendations_to_baseline` + `_build_suggestion_payload` 是合并为单步还是保留 2 个 helper |
| P2 | fail-fast 守卫位置 | 当前在 Step 3 之后，新流程下要不要移到 Step 4 之前 |
| P2 | 提交当前未提交的改动 | 决定 commit 粒度（一次性还是按 Step 拆） |

---

## 9. 新对话快速恢复上下文

开启新对话时，可贴以下内容快速恢复：

```
我正在重构 molding-optima 项目的 process/services/optimization_infer.py。

核心思路：边界划分（不增加新能力，只减代码 + 划责任）。

已完成：
1. 消除伪服务层（commit a3d3a75）
2. Step 1 拆分（4 helper 组合：_resolve_parent / _build_condition_data / _serialize_parameter / _build_baseline）
3. Step 2 重构（_build_engine_context 接 dict，业务上下文完整，8 字段，不含 id）

待续：
- _serialize_parameter 改显式白名单
- Mold 嵌套字段（gate_type / ave_thickness / product_weight）从 snapshot 取
- _resolve_parent 加 select_related 避免 N+1
- ExpertEngine 是否删除（当前是死代码）

架构原则（已沉淀到 memory）：
- 数据访问层 / 数据标准化层 / 编排层 / 算法层 分界
- 编排方法接 dict（多种来源兼容）
- 算法 = 纯函数，不接触 ORM
- 不传 algorithm 派生字段（defect_name / rule_library_code）
- 不传 algorithm 私域（iteration_trend / tuning_history）

详见：backend/_refs/system/algorithm/2026-09-30-infer-context-boundary-redesign.md
```

---

## 10. 关键文件位置

| 文件 | 路径 |
|---|---|
| 主服务 | `backend/process/services/optimization_infer.py` |
| ExpertEngine | `backend/process/engines/expert/expert_engine.py` |
| ExpertEngine 算法 | `backend/process/engines/expert/algorithm_engine.py` |
| FuzzyEngine | `backend/process/engines/fuzzy/fuzzy_engine.py` |
| 引擎注册 | `backend/process/engines/base_engine.py` |
| 工艺初始化 | `backend/process/services/parameter_init.py` |
| 工艺模型 | `backend/process/models/condition.py`、`parameter.py` |
| 工艺视图 | `frontend/src/views/process/optimization/` |
| 算法上下文设计 | `backend/_refs/system/algorithm/algorithm-context-design.md` |
| 输入扁平化设计 | `backend/_refs/system/ai/infer-input-flattening-design.md` |

---

## 11. 讨论决策时间线

| 时间 | 决策 | 边界问题 |
|---|---|---|
| 阶段 1 | 删除伪服务层 | **服务边界**（推荐服务无独立调用方）|
| 阶段 2 | Step 1 合并反查 + 构建 | **内部职责边界**（合并对外统一）|
| 阶段 3 | Step 2 重构：4 个序列化器 + 接 dict | **数据标准化层 vs 编排层** |
| 阶段 4 | Step 2 重构：编排方法接 dict | **ORM vs 编排层** |
| 阶段 5 | Step 2 重构：算法不含 id | **数据访问层 vs 算法特征** |
| 阶段 6 | Step 2 重构：算法不含派生字段 | **编排层 vs 算法边界** |
| 阶段 7 | Step 2 重构：算法私域自管 | **DB 查询边界** |

---

**最后更新**：2026-09-30（feedback 整体透传：删除 defect_feedbacks/observations/tuning_result 三件套拆分，改为 'feedback': feedback；同步调整 FuzzyEngine 两处引用 + docstring）