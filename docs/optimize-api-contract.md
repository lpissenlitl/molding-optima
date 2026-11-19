# 工艺优化接口契约（optimize_from_condition）

> 本文是 `POST /api/processes/algorithms/optimize/` 的**入参与响应契约**。
>
> - 入参 schema：`backend/process/schemas/optimization.py::ProcessOptimizeFromConditionSchema`
> - 端点：`backend/process/views/processes.py::AlgorithmsOptimizeView`
> - 编排：`backend/process/services/parameter_optimize.py::optimize_from_condition`
>
> 代码与本文冲突时以代码为准，并回头修正本文。

---

## 一、端点职责

以工艺条件下**某一轮**的工艺参数为基线，结合本轮缺陷反馈推理出**下一轮**工艺参数，落库成新轮次并给出建议。

一次调用同时完成三件事：记录本轮评价 → 推理下一轮 → 建立父子链。

---

## 二、入参

### 2.1 `condition_id`（必填）

承担双重身份：

1. **本轮调优的上下文锚点** —— 机器 / 材料 / 模具三维信息全部由它反查：
   - 机器：`InjectionMoldingMachine` + 按 `condition.injection_index` 选中的 `InjectionUnit`
   - 材料：`Polymer`
   - 模具：`Mold` + `GatingSystem` + `Cavity` + `Gate`（制品级物理基准：壁厚 / 制品重 / 浇口类型）

   提取按算法 specs 白名单裁剪，只传算法契约所需字段，ORM 元数据不进算法。

2. **所有工艺参数的归属** —— `ProcessParameter.process_condition` 外键，新轮次挂在同一 condition 下。

因此调用方**不需要也不应该**传 `machine_id` / `polymer_id` / `mold_id`。

**上下文契约校验**：三维反查完成后，service 跑一遍算法层契约校验（`OptimizeDataValidator`），失败转 400。当前实际拦截面只有一条 —— **机台没填驱动方式**。

### 2.2 `parent_seq_idx`（必填）

基准轮次的**模次序号**（`ProcessParameter.seq_idx`，condition 内全局递增，**不是数据库 id**）。

与 `condition_id` 联合定位基准行：

```
ProcessParameter.objects.get(process_condition=condition, seq_idx=parent_seq_idx)
```

定位到的那一行同时扮演两个角色：

- **推理基线的来源** —— 库里那一轮的参数值
- **新轮次的父节点** —— 落库时建立 `parent_param` 外键

定位失败 ⇒ `ERROR_DATA_NOT_FOUND`「基准工艺参数不存在」。

### 2.3 `parameter`（可选）

**用户当前实际在用的参数** —— 前端 UI 上可能已经改过，因此与库里的值不一致。

- 不传 ⇒ 基线完全取自库里那一轮
- 传了 ⇒ 见 §三 的合成规则

形状要求：

- 必须是 **flat**（与 `ProcessParameterSchema` 同形）。前端嵌套 `setting_process` → flat 的翻译在前端完成（`parameterToFlat`）
- 字段名必须与 ORM 列名一致，否则**静默丢弃**（不报错、不生效）

校验规则（HTTP 边界）：`parameter` 不为 `None` 时，必须至少含一个**标量工艺字段** —— 拦截「忘翻译」「误传空 dict」。业务元数据字段（编号 / 来源 / 模次序号）不计入该判定。

### 2.4 `feedback`（可选，默认空）

`FeedbackSchema`，三类合一：

| 字段 | 含义 |
|---|---|
| `defect[]` | 缺陷反馈列表（可多个，算法按阶段序选其一驱动优化）|
| `observations[]` | 实测观察 |
| `tuning_result` | **本轮**参数的试模效果评价（`qualified` / `unqualified` / `effective` / `unchanged` / `ineffective`）|

`tuning_result` 描述的是**本次提交的那一轮**（即 `parent_seq_idx` 定位到的那一轮）的试模结果，不是上一轮的。

**feedback 校验**（与算法消费口径一致，失败转 400）：

- `defect[]` 每项必须是对象，且 `keyword_name` / `level` / `position` 必填（`level` 必须是合法档位词）
- `DEFECTFREE`（无缺陷）例外：前端不展示程度与位置输入框，这两项免校验
- `defect[]` **可以为空**，前提是给了 `tuning_result = qualified`（合格态产品没有缺陷）；其余评价档位仍要求缺陷列表非空

---

## 三、基线合成规则

```
baseline = 库里基准轮的全量字段  ⊕  用户传入 parameter 的非 None 字段
```

- 合成在**内存**完成，**不写库**（写回父记录属落库阶段）
- **diff 口径**：逐字段比较，**只有与库值确实不同**的字段进 `changed_fields`。值相同的字段不写回，避免写放大与无谓的 `updated_at` 变化
- `changed_fields` 在落库阶段回写父记录，与新建轮次**同事务** ⇒ 不会出现「参数改了但新轮次没建成」的中间态
- 父轮已归档（已有试模评价）时不写回 —— 它的参数是「当时实际用的工艺」这一历史事实；但**不影响**子轮次 —— 基线合成在装配阶段已按用户改值覆盖

---

## 四、关系字段：自动建立，不接受入参

以下字段一律由 service 按业务建立，入参出现**不生效**：

| 字段 | 谁建立 |
|---|---|
| `process_condition`（归属）| `condition_id` 决定 |
| `parent_param`（父子链）| `parent_seq_idx` 定位到的那一行 |
| `seq_idx`（模次序号）| `ProcessParameter.save()` 分配 |
| `parameter_no`（系统编号）| `save()` 按 `PP-{YYYYMMDD}-{HHMMSS}-{NNN}` 生成 |
| `param_source`（来源标记）| service 按场景写入 |

入参契约（`ProcessParameterSchema`）只声明**工艺字段与可写元数据**；写操作另有 `PARAMETER_LOCKED_FIELDS` 锁定清单。

---

## 五、响应

两条路径，**形状不同**，调用方需区分。

### 5.1 正常路径

```json
{
  "parameter": {
    "id": 279,
    "parent_param_id": 278,
    "process_condition_id": 112,
    "seq_idx": 3,
    "parameter_no": "PP-20261117-162732-001",
    "inj_stg": 1, "inj_spd_1": 34.0, "...": "其余工艺字段"
  },
  "suggestion": { "source_type": "fuzzy_rule", "groups": [ "..." ], "recommendation_id": 456 }
}
```

`parameter` 是**落库后的新轮次完整对象**（ORM 镜像）：

| 字段 | 指向 |
|---|---|
| `id` | **新轮次**主键 |
| `parent_param_id` | 基准轮主键 |
| `process_condition_id` | 所属工艺条件 |
| `seq_idx` | 新轮次的模次序号 |
| `parameter_no` | 新轮次的系统编号 |
| 其余工艺字段 | 本轮推理结果（与落库同源）|

### 5.2 合格态短路（`tuning_result = qualified`）

```json
{
  "parameter": null,
  "suggestion": null,
  "skipped": true,
  "skip_reason": "qualified",
  "message": "产品已合格，本轮仅记录评价，未进行工艺优化"
}
```

产品已合格 ⇒ 没有缺陷可驱动优化 ⇒ **不跑推理、不建新轮次**。但本轮评价**仍要落库**（写回手改参数 + 写合格标签 + 丢弃缺陷），提交通道保持可用，为「合格状态下的优化需求」预留扩展点。

---

## 六、落库副作用（单事务）

1. 回写用户手改的参数到父记录
2. 更新父轮的 `TuningRecord`（缺陷反馈 + 试模结果）
3. 更新上一轮 `Recommendation.is_adopted`（训练标签）
4. 新建 `ProcessParameter`（`param_source = system_inferred`，父节点 = 基准轮）
5. 新建 `TuningRecord`（`pending`，等待该轮自身的试模反馈）
6. 新建 `Recommendation`

以上六步与回写同属一个 `atomic` 事务，任一步失败整体回滚。

---

## 七、明确不做的事

- 不接收 `machine_id` / `polymer_id` / `mold_id` / `process_set` —— 从 `condition_id` 反查
- 不接收 `subrule_no` —— 后端算法自动识别
- 不接收上一轮 `suggestion` —— 后端实时推理
- 不接受入参指定关系字段（见 §四）
- 合格态下不建新轮次（见 §5.2）

---

## 八、与 initialize 的形状一致性

四个同族端点统一用 `parameter` 作为工艺参数的 key，形状按**是否落库**分两种：

| 端点 | 落库 | `parameter` 的内容 |
|---|---|---|
| `POST .../algorithms/initialize/` | ✅ | 完整对象（含 `id` / `seq_idx` / `parameter_no` / `parent_param_id`）|
| `POST .../algorithms/initialize-from-condition/` | ✅ | 完整对象（同上）|
| `POST .../algorithms/optimize/` | ✅ | 完整对象（同上）|
| `POST .../algorithms/initialize-from-provided/` | ❌ | 仅工艺字段（无 `id` / `seq_idx`）|

⇒ **有 `id` ⇔ 已落库**：落库型端点的 `parameter` 一律是 ORM 镜像，主键不再另置顶层（顶层也没有 `parameter_id` 别名）。

### 8.1 `condition` 键

落库型端点同时返回 `condition`（ORM 镜像），承载本次工艺条件的完整对象：

| 端点 | `condition` |
|---|---|
| `initialize/` | ✅ 新建的 condition（`id` / `condition_no` / `shot_index` / `injection_index` ...）|
| `initialize-from-condition/` | ✅ 新建的 condition（从源参数复制而来）|
| `initialize-from-provided/` | ❌ 不落库 ⇒ 无 condition |
| `optimize/` | ❌ 不新建 condition ⇒ 无 condition |

顶层不再给零散 id（`condition_id` / `shot_index` / `injection_index`）—— 它们都在 `condition` 镜像里，顶层再放一份就是同值别名。

### 8.2 顶层不保留的键

| 键 | 原因 |
|---|---|
| `process` | parameter 的 nested 形态；对外只留 flat 的 `parameter` |
| `param_source`（落库型端点）| 与 `parameter.param_source` 同值 |
| `source_condition_id` / `source_parameter_id` | 溯源写在 `condition.process_context` 里 |
| `parameter_id` | 与 `parameter.id` 同值 |

⚠️ `initialize-from-provided/` 不落库 ⇒ 顶层保留 `param_source`（`parameter` 里没有这个字段承载）。

---

## 九、相关文件

| 关注点 | 位置 |
|---|---|
| 端点 | `backend/process/views/processes.py::AlgorithmsOptimizeView` |
| 入参 schema | `backend/process/schemas/optimization.py::ProcessOptimizeFromConditionSchema` |
| 工艺参数契约 | `backend/process/schemas/parameter.py::ProcessParameterSchema` |
| 编排与落库 | `backend/process/services/parameter_optimize.py::optimize_from_condition` |
| 初始化同族端点 | `backend/process/services/parameter_initialize.py::ParameterInitializeService` |
| parameter 展开出口 | `backend/extensions/models.py::BaseModel.to_dict`（ORM 镜像；FK 输出 `{name}_id`）|
| 数据模型 | `backend/process/models/parameter.py::ProcessParameter` |
| 前端形态翻译 | `frontend/src/views/process/optimization/components/parameterTransform.ts::parameterToFlat`（入参方向）| `frontend/src/views/process/optimization/components/parameterTransform.ts::parameterFromFlat`（响应方向）|
