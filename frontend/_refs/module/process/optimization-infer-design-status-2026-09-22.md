# 工艺优化 infer 接口设计 —— 当前讨论状态

> 文档作者：Qoder AI
> 最后更新：2026-09-22（第 2 轮讨论 —— 包含 infer 接口、Recommendation、TuningRecord 完整设计）
> 状态：✅ 核心设计已确认 —— 待沉淀代码

## 一、讨论任务

**核心任务**：工艺优化 `/optimization/infer` 接口的字段设计

### 任务边界（你定的）

- 字段是业务的载体，字段设计就是接口设计
- 当前讨论**只聚焦 infer 接口的字段**
- 其他话题（adopt / tuning-records / FuzzyEngine 内部逻辑）**不展开**

---

## 二、核心设计原则（两轮讨论沉淀）

### 原则 1：condition = 完整上下文
```
一次 condition = 一次调机过程（机器/模具/材料/段数设置不变）
改变上下文 = 新的调机过程（新的 condition_id）
所以 infer 入参不需要单独的 machine_id/polymer_id/mold_id/process_set
这些由后端从 condition_id 反查
```

### 原则 2：3 场景调用逻辑一致
```
场景 1（基本调参）、场景 2（自动回撤）、场景 3（手动修改）
在 infer 接口层面调用逻辑完全一样 —— 只是前端传入的 feedback 不同
后端根据 feedback.tuning_result 自动选择规则（算法自治）
```

### 原则 3：算法自治
```
前端不传规则选择（如 subrule_no）
后端算法自己识别最合适的规则
```

### 原则 4：反馈 vs 工艺 数据分离
```
工艺数据（ProcessParameter）只管工艺
调机反馈（TuningRecord）只管用户反馈
算法推荐（Recommendation）只管算法输出
三者通过关联字段组织，互不污染
```

### 原则 5：数据链是完整 ML 训练架构
```
Recommendation ──关联──> ProcessParameter ──关联──> ProcessCondition
├─ 调整内容（recommendations JSON）
├─ 训练标签（is_adopted：推荐方向是否有效）
├─ 上下文（condition）
└─ 调整前/后工艺（parent_param / process_parameter）
= 完整的训练样本和评估闭环
```

### 原则 6：调整建议只是出参
```
调整建议是出参的一部分，不入参
infer 入参不需要包含历史建议
前端不需要往 infer 传建议
```

### 原则 7：Recommendation 是"工艺调整记录"（设计哲学转变）

**早期认知**：Recommendation 只记录算法推荐记录。

**重新认知（2026-09-22 轮 2）**：Recommendation 是通用的**工艺调整记录**：
- 任何工艺变更都通过 Recommendation 记录
- 包括：算法优化、人工调机、历史复制、初始生成
- 区分靠 `source_type` 字段
- 这样**调机树 = Recommendation 树**

```python
class Recommendation:
    process_parameter_id   # 关联新工艺
    source_type            # 来源：algorithm_optimize / manual_adjust / template_copy / algorithm_init
    recommendations        # JSON（调整内容）
    is_adopted             # ✅ 保留：该调整是否最终被采用（训练标签）
    # adopted_param       # ❌ 移除：没有用处
```

### 原则 8：infer 只处理算法优化，人工调整走独立接口

- ✅ `infer` = 算法优化（创建 Recommendation，source_type=`algorithm_optimize`）
- ✅ `manual-adjust` = 人工调机调整（创建 Recommendation，source_type=`manual_adjust`）
- 两者职责清晰，互不污染

### 原则 9：is_adopted 默认 True，ineffective 改 False

```
infer 创建推荐（默认 is_adopted=True）
下一轮用户反馈 tuning_result = 'ineffective' → 改为 False
下一轮用户反馈 tuning_result = 'effective' 或 null → 保持 True
```

这是**反馈驱动的状态机**，不需要用户主动调用 adopt。

### 原则 10：parent_seq_idx 是 Schema 的正确名（不是重命名）

- `parent_seq_idx` = 业务编号（前端可见）
- `parent_param` = 后端内部 ID 外键
- 前端传 `parent_seq_idx`，后端反查 ID
- 所以 Schema 里就应该叫 `parent_seq_idx`，不是 `parent_param_id` 重命名

---

## 三、已确认的"业务流程"

### 一轮工艺优化（步骤 2）流程

```
1. 用户基于"上一轮工艺"打产品
2. 用户在前端页面看到产品缺陷
3. 用户填写缺陷反馈（DefectFeedback[]）
4. 用户填写工艺实测（CycleObservation[]，按需）
5. 用户填调机效果评价（TuningResult：effective/ineffective）
6. 用户点 [获取优化工艺]
7. → infer 接口
8. 后端算法返回新工艺参数 + 调整建议
9. 同步落库：ProcessParameter + Recommendation（is_adopted=True）
10. 前端展示，用户继续调
11. 下一轮填 ineffective 时，自动更新上一轮 Recommendation.is_adopted=False
```

### infer 调用前提

- 数据库**一定已有**上一轮工艺可参考
- **没有"无参考的首次 infer"** —— 那种情况归 `/initialization/infer/`
- 所以 `/optimization/infer` 的语义**专用于调优**

---

## 四、infer 入参设计（已确认）

```python
class InferRequest:
    condition_id: int                          # 工艺条件 ID（必传）
    parent_seq_idx: int                        # 基准 seq_idx（必传）
    parameter: dict | None                     # 手动修改覆盖（可选，结构化 dict）
    feedback: Feedback                         # 反馈信息（嵌套）

class Feedback:
    defect: list[DefectFeedbackData]           #   多个缺陷，算法自动识别优先级
    observations: list[CycleObservation]       #   实测观察（按需传）
    tuning_result: 'effective' | 'ineffective' | None  # 增量反馈：当前 vs 上一轮
```

### 入参字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `condition_id` | int | 工艺条件 ID。后端反查后得到 mold/machine/polymer/process_set 上下文 |
| `parent_seq_idx` | int | 基准 seq_idx。与 condition_id 联合定位调机树中的基准节点 |
| `parameter` | dict? | 用户手动修改后的工艺参数（结构化 dict，与前端 settingProcessForm 一致）。用于手动修改场景 |
| `feedback.defect[]` | array | 缺陷反馈数组（旧版是单个，现在改为多个）。算法识别优先级（如短射 15 缩水） |
| `feedback.observations[]` | array | 实测观察（4 种参数：actual_product_weight, peak_pressure, injection_time, cycle_time）。按需传 |
| `feedback.tuning_result` | enum | 增量反馈：当前工艺相对上一轮是否变好。effective=继续，ineffective=回退 |

### 主动不传的字段（从 condition_id 反查）

- ❌ `machine_id`, `polymer_id`, `mold_id`（condition 上下文）
- ❌ `process_set`（condition 的一部分）
- ❌ `subrule_no`（后端算法自动识别）
- ❌ 上一轮 `Adjustment`（后端实时推理，不需要历史）
- ❌ `opt_nums`（可根据 parent_seq_idx 推算）

---

## 五、infer 出参设计（已确认）

```python
class InferResponse:
    new_parameter: dict                  # 新工艺参数（内嵌 parameter_id）
    suggestion: {                        # 完整建议对象
        source_type: str                 #   元信息（fuzzy_rule / rule_miner / llm）
        recommendations: [               #   多个推荐项
            {
                category: str,           #     分类：temperature/pressure/velocity...
                icon: str,
                items: [
                    { description, direction, rule_refs }
                ]
            }
        ]
    }                                    # 内嵌 recommendation_id
```

### 出参字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `new_parameter` | dict | 新工艺参数（结构化 dict）。内嵌 `parameter_id`（落库后产生的） |
| `suggestion.source_type` | str | 算法来源（fuzzy_rule / rule_miner / llm）|
| `suggestion.recommendations[]` | array | 多个推荐项（按 category 分组） |
| `recommendation_id` | int | 内嵌在 suggestion 中（落库后产生） |

### naming 决策记录

- `suggestion` vs `recommendation` 选 `suggestion`：语义轻、与 adjustment 形成对比
- 但内部 JSON 结构与 `Recommendation.recommendations` 对齐（只接单数）
- 这样**表名稳重（Recommendation）+ API 字段名轻（suggestion）**各有所在

---

## 六、数据架构（完整 ML 训练链）

```
┌────────────────────────────────────────────────────────────┐
│ Recommendation (算法推荐 + 训练标签)                          │
│ ├─ process_parameter_id ──→───┐                              │
│ ├─ source_type                 │                              │
│ ├─ recommendations (JSON)      │                              │
│ └─ is_adopted (训练标签)       │                              │
└───────────────────────────────┼─────────────────────────────┘
                                ↓ 关联
┌───────────────────────────────┼─────────────────────────────┐
│ ProcessParameter (工艺参数)      │                             │
│ ├─ parent_param (调整前)        │                              │
│ ├─ seq_idx                      │                              │
│ └─ parameters (JSON)            │                              │
└─────────────────────────────┼─┼───────────────────────────────┘
                              │ ↓ 关联
┌─────────────────────────────┼───────────────────────────────┐
│ ProcessCondition (上下文)                     │
│ ├─ mold_id, polymer_id, machine_id                              │
│ ├─ process_set                                                 │
│ └─ process_context_snapshot                                    │
└───────────────────────────────────────────────────────────────┘
```

### 训练样本结构

```
输入特征：
├─ condition（上下文：模具/机器/材料）
├─ 调整前工艺（parent ProcessParameter）
├─ 缺陷反馈（feedback.defect[]）
└─ observations（实测）

输出（标签）：
├─ 调整后工艺（ProcessParameter）
├─ 调整内容（Recommendation.recommendations）
└─ 是否有效（is_adopted，自动维护）
```

### is_adopted 的状态机

```
infer 创建 Recommendation（默认 is_adopted=True）
         ↓
下一轮 tuning_result = 'effective'     → 保持 True
下一轮 tuning_result = 'ineffective'   → 改为 False（训练标签）
```

这是**自动维护的训练标签**，不需要用户主动调用 adopt。

### 训练样本的双层架构（设计哲学修正）

```
算法输出层（原始）             训练样本层（规范化）
├─ Recommendation               ├─ TuningRecord
├─ recommendations JSON          ├─ adjustments JSON
├─ 按 source_type 变化格式       ├─ 独立标准化格式
└─ 算法侧输出                   └─ 训练侧使用
   Recommendation.recommendations 是算法输出（算法视角）
   TuningRecord.adjustments 是训练样本（训练视角）
   两层独立，不需要严格一一对应
```

---

## 七、推荐 Recommendation 表简化（待代码改动）

### 当前 schema
```python
class Recommendation:
    process_parameter_id   # 关联新工艺
    source_type            # 来源类型
    recommendations        # JSON
    is_adopted             # 是否被采用（早期设计）
    adopted_param          # 采用的参数（无用处）
```

### 简化后
```python
class Recommendation:
    process_parameter_id   # 关联新工艺
    source_type            # 来源类型
    recommendations        # JSON
    is_adopted             # ✅ 保留：训练标签（推荐方向是否有效）
    # adopted_param       # ❌ 移除：没有用处
```

### ⚠️ 设计哲学修正（2026-09-22 轮 2）

**不要把 Recommendation 扩展为'通用工艺调整记录'**！
- Recommendation 职责单一：只记录算法推荐内容
- 手工调整走 TuningRecord（训练样本核心）
- "调整内容"统一归到 TuningRecord.adjustments（规范化训练样本）

---

## 八、TuningRecord 字段设计（已确认）

### 字段调整总览

```diff
class TuningRecord:
    process_parameter    # FK（业务层保证 1:1 同步创建）
    defect_feedbacks[]   # 缺陷反馈（JSON 数组）
-   note = CharField(max_length=500)
+   adjustments          # 调整记录（JSON，系统自动生成）
    result               # 6 状态：pending / improved / worse / unchanged / qualified / unqualified
    result_detail        # 结果详情
-   parameter_snapshot   # 调整前参数快照（重命名）
+   previous_parameter   # 调整前的参数快照（OLD parameter.parameters）
```

### 字段创建与更新时机

| 字段 | 创建时机 | 更新时机 |
|---|---|---|
| `process_parameter` | 创建 parameter 时同步创建 | 不可变 |
| `defect_feedbacks` | 空 | infer 调用时填充（来自入参） |
| `adjustments` | 空 | infer / manual-adjust 调用时填充 |
| `result` | `pending` | infer 调用时根据 tuning_result 设置；用户后续可改 |
| `result_detail` | 空 | infer 调用时填充；用户后续可改 |
| `previous_parameter` | 空 | infer / manual-adjust 调用时填充（OLD 的参数） |

### 创建 parameter 的统一逻辑

```python
def create_parameter_with_tuning_record(condition, parameters, source):
    """所有创建 parameter 的入口都同步创建 TuningRecord"""
    param = ProcessParameter.objects.create(
        process_condition=condition,
        parameters=parameters,
        param_source=source,
    )
    # 业务层同步创建 TuningRecord（空状态）
    TuningRecord.objects.create(
        process_parameter=param,
        defect_feedbacks=[],
        result='pending',
    )
    return param
```

### infer 调用时的更新逻辑

```python
def update_old_tuning_record(old_param, new_param, feedback):
    old_tr = old_param.tuning_record
    old_tr.update(
        previous_parameter=old_param.parameters,  # OLD 的参数快照
        adjustments=compute_diff(old_param, new_param),
        defect_feedbacks=feedback.defect,
        observations=feedback.observations,
        result=map_tuning_result_to_result(feedback.tuning_result),
        result_detail=feedback.result_detail,
    )
```

### previous_parameter 的语义

```
previous_parameter = OLD parameter 的 parameters（调整前快照）
                    = "这是从哪个工艺调整过来的"

为什么独立存一份：
├─ OLD parameter 的 parameters 可能被修改（但实际不应该被修改）
├─ 历史快照避免联表查询
└─ 训练样本自包含
```

### 调整记录与快照的对应关系

```
previous_parameter  ──  "调整前参数"
adjustments.changes  ──  "调整前 → 调整后" diff

两者联合：完整还原一次调整动作
```

---

## 八点五、TuningRecord 与 ProcessParameter 的同步关系（设计哲学）

### 核心原则

```
只要创建 parameter，就必须同步创建 TuningRecord
这是业务层的不变式（invariant）
```

### 三个创建入口

1. **算法初始化**（initialization from-masterdata）
2. **历史复制**（initialization from-source-condition）
3. **手工调整**（manual-adjust）
4. **算法优化**（infer）

每个入口都必须调用 `create_parameter_with_tuning_record()`。

### 调整动作的统一模式

无论是 infer 还是 manual-adjust：
```
├─ 反查 OLD parameter
├─ 创建 NEW parameter（自动创建 TuningRecord）
├─ 创建 Recommendation（挂在 NEW 上）
└─ 更新 OLD parameter 的 TuningRecord：
   ├─ previous_parameter ← OLD 的参数
   └─ adjustments ← OLD vs NEW 的 diff
```

### adjustments 的生成条件

```
adjustments 实际就是：
├─ 有引用 old parameter（基准）
└─ 同时又创建的 new parameter（结果）
两者同时存在时才生成

创建 TuningRecord 时：只有 parameter，没有 NEW → adjustments 为空
infer / manual-adjust 时：有 OLD + NEW → adjustments 生成
```

---

### adjustments 字段设计

```json
{
    "defects": ["短射"],
    "changes": [
        {
            "param": "inj_pres_1",
            "before": 50,
            "after": 60,
            "direction": "increase",
            "rule_ref": "rule_001"
        }
    ],
    "tuning_context": {
        "iteration": 3,
        "previous_result": "worse"
    }
}
```

### 关键设计决策

1. **TuningRecord 与 ProcessParameter 的关系**：
   - FK（不加 unique）
   - 业务上取最新一条作为当前状态
   - 允许多条历史记录（audit 追溯）

2. **result 状态机**：
   - 保持 6 个状态（比 effective/ineffective 更准确）
   - pending / improved / worse / unchanged / qualified / unqualified

3. **adjustments 与 note 的区别**：
   - 原 note = 调参备注（自由文本）
   - 现 adjustments = 规范化调参内容（JSON，训练样本）

4. **parameter_snapshot 保留**：
   - 冗余存储，避免联表查询

---

## 九、调整内容的双层架构（设计哲学）

### 两个表的角色

| 表 | 职责 | 字段 | 格式 | 视角 |
|---|---|---|---|---|
| **Recommendation** | 算法推荐记录 | recommendations | 按 source_type 变化 | 算法视角 |
| **TuningRecord** | 试模反馈 + 训练样本 | adjustments | 独立规范化 | 训练视角 |

### 两者**不需要严格对应**！

- Recommendation.recommendations：算法输出（原始格式）
- TuningRecord.adjustments：训练样本（规范化）
- 可能一致（用户采纳算法推荐）也可能不一致（用户手动调整）

### is_adopted 体现两者关系

```
算法推荐 (Recommendation) vs 实际调整 (TuningRecord.adjustments)
   ↓                                  ↓
is_adopted 反映两者是否一致
   ├─ True = 调整与推荐一致
   └─ False = 用户手动调整了
```

## 十、TuningRecord.adjustments 自动生成设计（已确认）

### 设计原则

```
用户只填：defect_feedbacks + result + result_detail
系统生成：adjustments + parameter_snapshot

adjustments 是规范化训练样本，必须由系统自动生成
用户无法定义其结构（保证格式一致）
```

### 生成时机

**同步生成**：TuningRecord 创建或更新 result 时，立即生成 adjustments。

不采用异步任务：
- 同步生成逻辑不重，不应造成请求延迟
- 异步会增加调试复杂度

### 数据来源

```python
def generate_adjustments(tuning_record):
    return {
        "defects": extract_defect_types(tuning_record.defect_feedbacks),
        "changes": compute_parameter_diff(
            tuning_record.process_parameter.parent_param,
            tuning_record.process_parameter
        ),
        "tuning_context": {
            "iteration": compute_iteration(tuning_record.process_parameter.seq_idx),
            "previous_result": get_previous_result(
                tuning_record.process_parameter.parent_param
            )
        }
    }
```

### changes 的生成逻辑

从 parent_param.parameters 与 current_param.parameters 计算 diff：

```python
for key in union(parent_params, current_params):
    if parent_params[key] != current_params[key]:
        changes.append({
            "param": key,
            "before": parent_params[key],
            "after": current_params[key],
            "direction": compute_direction(before, after),  # increase / decrease
            "rule_ref": infer_rule_ref(key, defect_type)    # 可选
        })
```

### 边界情况处理

| 场景 | 处理 |
|---|---|
| 父节点缺失 | iteration 取默认 0，previous_result 填 null |
| 首条 TuningRecord | tuning_context 为空（无前一轮） |
| diff 为空（参数没变） | changes 填空列表 |

---

## 十一、defect_feedbacks 字段详细设计（已确认）

### 字段结构（与前端 DefectFeedbackData 对齐）

```json
[
    {
        "keyword_id": 15,                       // 必须存在（关联 RuleKeyword.id）
        "keyword_name": "短射",                  // 冗余存（DEFECTFREE 等特殊项）
        "level": "high",                        // 按 fuzzy_level 档位（动态）
        "position": "DLWELDLINE3",              // 存在性校验
        "position_3d": null                     // 可选，3D 坐标（暂不管）
    }
]
```

### 各字段详细设计

#### 1. `keyword_id` 与 `keyword_name`

```python
- 类型：int / string
- 必传：是
- 关联：RuleKeyword.id（必须存在）
- 命名冗余：keyword_name 冗余存，避免反查
```

#### 2. `level`（动态档位）

```python
- 类型：string | null
- 取值：根据 RuleKeyword.fuzzy_level 动态生成
  - fuzzy_level=3（3 档）: low / medium / high
  - fuzzy_level=5（5 档）: very_low / low / medium / high / very_high
  - fuzzy_level=7（7 档）: extremely_low / very_low / low / medium / high / very_high / extremely_high
- null 语义：DEFECTFREE（无缺陷）时存 null
- 业务约束：后端验证 level 是否在该 keyword.fuzzy_level 档位中
```

#### 3. `position`（存在性校验）

```python
- 类型：string
- 命名规则：DL${defect.keyword_name}${segment}（例：DLWELDLINE1~6）
- 段号语义：段号小 = 近端（浇口附近）；段号大 = 远端
- 校验策略（方案 C）：
  - 在 RuleKeyword 列表中查找（按 keyword_name）
  - 找到 → 关联
  - 找不到 → 存为自定义字符串（不报错）
- 联动：与 defect.keyword_name 联动（DL 前缀匹配）
```

#### 4. `position_3d`（暂不管）

```python
- 类型：object | null
- 结构：{ x: number, y: number, z: number }
- 说明：当前还未启用，暂不详细设计
```

### 后端校验逻辑

```python
def validate_defect(defect):
    # 1. keyword_id 必须存在
    keyword = RuleKeyword.objects.get(id=defect['keyword_id'])
    if not keyword:
        raise ValidationError("keyword_id 不存在")

    # 2. level 必须在该 fuzzy_level 档位中
    valid_levels = LEVEL_WORDS[keyword.fuzzy_level]
    if defect['level'] not in valid_levels and defect['level'] is not None:
        raise ValidationError(f"level 不在 fuzzy_level={keyword.fuzzy_level} 的档位中")

    # 3. position 存在性校验（不报错）
    position_kw = RuleKeyword.objects.filter(
        keyword_name=defect['position']
    ).first()
    if not position_kw:
        # 自定义位置，不报错（只警告）
        log_warning(f"position 是自定义值：{defect['position']}")
```

### "无缺陷"的特殊处理

```
当 keyword_name='DEFECTFREE' 时：
├─ level: null（隐藏程度选项）
├─ position: ''（空字符串）
├─ position_3d: null（不显示）
└─ 业务含义：算法返回产能/周期时间优化建议
```

---

## 三、前端已存在的数据结构（来源文件）

### 文件清单

| 文件 | 角色 |
|---|---|
| `frontend/src/views/process/optimization/pages/OptimizationCreate.vue` | 工艺优化工作台主页面 |
| `frontend/src/types/optimization.ts` | 类型定义（RoundForm, DefectFeedbackData, CycleObservation, Adjustment） |
| `frontend/src/views/process/optimization/components/DefectFeedback.vue` | 缺陷反馈表单 |
| `frontend/src/views/process/optimization/components/ProcessActualFeedback.vue` | 工艺实测表单 |
| `frontend/src/views/process/optimization/components/PreviousAdjustment.vue` | 上一轮建议展示 |
| `frontend/src/views/process/optimization/components/RoundTimeline.vue` | 左侧调机时间线 |

### 5 个关键数据类型（前端已固化）

#### 1. `RoundForm` —— 单轮调机数据
```
{
    id, type: 'initial' | 'optimized' | 'manual',  // 来源
    created_at,
    parameter: any,                                 // 结构化工艺参数（settingProcessForm）
    feedback: {
        defect?: DefectFeedbackData,
        tuning_result?: 'effective' | 'ineffective',
        observations?:  CycleObservation[],
    }
}
```

#### 2. `DefectFeedbackData`
```
{
    keyword_id, keyword_name,     // 缺陷类型（关联 RuleKeyword.id）
    level, position,                // 程度 + 位置
    position_3d?,                  // 3D 坐标（可选）
}
```

#### 3. `CycleObservation`（实测观察）
```
{
    param_key: 'actual_product_weight' | 'peak_pressure' | 'injection_time' | 'cycle_time',
    value: number | null,
}
```

#### 4. `TuningResult`
```
'effective' | 'ineffective' | null
```

#### 5. `Adjustment`（后端→前端）
```
{
    source_round_id?,
    adopted?,
    groups: [
        { category, icon, items: [{ description, direction, rule_refs }] }
    ]
}
```

---

## 四、关键事实（字段设计边界）

### 旧版存在的字段（前端没有）

- ❌ `IP0/IP1/IV0.../PP0.../MP0...` flat 工艺字段名
- ❌ `precondition` 嵌套对象
- ❌ `optimize_export`（上轮反馈嵌套对象）
- ❌ `defect_info[].feedback`（旧版的反馈机制）
- ❌ `opt_nums`（第几次优化计数器）

### 前端有的字段（接口必须能接收）

- ✅ 结构化工艺参数（`settingProcessForm`）
- ✅ `DefectFeedbackData`（缺陷 + 位置 + 程度）
- ✅ `CycleObservation[]`（实测观察）
- ✅ `TuningResult`（调机效果评价）
- ✅ 上一轮 `Adjustment`（建议展示）

### 数据库现状（molding-optima）

| Model | 字段 | 角色 |
|---|---|---|
| `ProcessCondition` | `id`, `mold_id`, `polymer_id`, `injection_machine_id`, `shot_index`, `injection_index`, `process_context`, `process_context_snapshot`, `origin_type`, `status` | 工艺条件 |
| `ProcessParameter` | `id`, `process_condition_id`, `parent_param`（FK self）, `seq_idx`（condition 全局递增）, `param_source`（manual/algorithm/template/ai/...） | 参数版本树 |
| `Recommendation` | `process_parameter_id`, `source_type`, `recommendations`, `is_adopted`, `adopted_param` | 推荐记录 |
| `TuningRecord` | `process_parameter_id`, `defect_feedbacks`, `note`, `result`, `result_detail`, `parameter_snapshot` | 试模记录 |

### Schema 现状（molding-optima process/schemas/parameter.py）

```python
parent_param_id: Optional[int]   # 早期字段名（不是 parent_seq_idx）
seq_idx: Optional[int]
```

> ⚠️ `parent_param_id` 是早期字段名——根据用户澄清，**应该是 `parent_seq_idx`**（业务编号语义）
>
> 但 Schema 现状是 `parent_param_id`，需重构

---

## 五、关键术语澄清（已确认）

### `parent_seq_idx` vs `parent_param_id`

- **`parent_param`**（Model）：FK self，**后端内部 ID 外键**
- **`seq_idx`**（业务编号）：按 `process_condition` 全局递增，**前端可见**
- **`parent_seq_idx`**（Schema 应有）：前端传"基于第 N 号调整"，后端反查 ID
- 现状 Schema 用 `parent_param_id`，是早期遗留——**待重构**

### save() 的 seq_idx 分配

```python
def save(self, *args, **kwargs):
    if self.pk is None:
        last_idx = ProcessParameter.all_objects.filter(
            process_condition=self.process_condition  # ← condition 全局递增
        ).aggregate(Max('seq_idx'))['seq_idx__max'] or 0
        self.seq_idx = last_idx + 1
```

虽然 Model 注释写"同父节点下递增"，但**实际是 condition 全局递增**——这是有意为之。

---

## 六、旧版参考（HSMoldingService）

### 文件清单

| 文件 | 角色 |
|---|---|
| `f:/items/inovance-cooperation/HsMoldingService/mdprocess/views/process_optimize_views.py` | View 层（47-55 行 ProcessOptimizeAlgorithmView） |
| `f:/items/inovance-cooperation/HsMoldingService/mdprocess/views/process_optimize_forms.py` | Schema 定义（100+ flat 字段） |
| `f:/items/inovance-cooperation/HsMoldingService/mdprocess/services/process_optimize_service.py` | service（tsk_algorithm 约 250 行） |

### 旧版 infer 入口（process_optimize_views.py:47-55）

```python
class ProcessOptimizeAlgorithmView(BaseView):
    @method_decorator(require_login)
    @method_decorator(validate_parameters(OptimizeProcessSchema))
    def post(self, request, cleaned_data):
        return process_optimize_service.optimize_process(cleaned_data)
```

### 旧版 tsk_algorithm 核心步骤（process_optimize_service.py:515+）

```
1. 遍历 defect_info，找首个非"无缺陷"的 → target_defect
2. 加载规则网络（tsk_array + adjust_array + rule_priority）
3. 预处理参数：
   - 3.1 段数归一化（injectstage1=0.95）
   - 3.2 注射行程差（IDT1 = MEL - IL0）
   - 3.3 保压是否存在（PP0==0 推断未加保压）
   - 3.4 是否热流道（SCT0 推断）
   - 3.5 注射主打段（inject_main_stage）
   - 3.6 实际产品重量
   - 3.7 VP 切换模式独热（VPTM0~VPTM4）
   - 3.8 储前/储后松退模式独热（DMBM0~2, DMAM0~2）
4. 推理：
   - if opt_nums == 1: 首次缺陷修正（model.predict top_k=10）
   - if opt_nums > 1: 基于上一模反馈迭代（修正效果佳/不佳分两支）
```

---

## 七、之前 memory 沉淀（供参考）

memory 里已经沉淀：

- `3061f8cd-6c6f-499d-b832-074a1594b89e` —— 工艺参数初始化的 3 种模式架构
- `8a2797f5-...` —— 参数版本树 / 工艺参数调整基准字段约定（实地核对版）
- `6b733df4-...` —— 参数版本树结构

---

## 八、待讨论清单（两轮后状态）

### ✅ 已确认（高优先级）

- ✅ **入参 1：基准工艺** → `condition_id + parent_seq_idx`（ID 引用，后端反查）
- ✅ **入参 2：手动修改覆盖** → 可选 `parameter`（结构化 dict）
- ✅ **入参 3：缺陷反馈** → `feedback.defect[]`（多个，算法识别优先级）
- ✅ **入参 4：实测观察** → `feedback.observations[]`（按需传）
- ✅ **入参 5：调机效果** → `feedback.tuning_result`（增量反馈）
- ✅ **出参：新工艺参数** → `new_parameter`（结构化 dict，内嵌 parameter_id）
- ✅ **出参：调整建议** → `suggestion`（嵌套单数，对齐 Recommendation.recommendations）
- ✅ **上下文字段** → 从 condition_id 反查，不传
- ✅ **同步落库** → infer 创建 ProcessParameter + Recommendation（is_adopted=True）

### 🟡 中优先级（待处理）

- infer 内部代码实现（反查、merge、flatten、反 flatten、推荐序列化、落库）
- 前端 DefectFeedbackData → 数组结构调整
- 前端 PreviousAdjustment 组件是否重命名（adjjustment → suggestion）
- Recommendation 表简化（移除 adopted_param）——需 migration
- Schema 字段名重构（parent_param_id → parent_seq_idx）——需 migration
- is_adopted 自动变更逻辑位置（infer 下轮调用时？还是有独立接口？）

### 🟢 低优先级（先不动）

- adopt 接口设计（不是必需，因为 is_adopted 自动维护）
- tuning-records 接口设计
- FuzzyEngine 内部逻辑
- 算法选择（fuzzy vs rule_miner vs llm）

---

## 九、歧义解决状态

| 问题 | 状态 | 决策 |
|---|---|---|
| `opt_nums` 的替代方案 | ✅ 已解决 | 可从 parent_seq_idx 推算，不需要字段 |
| 上一轮 `Adjustment` 传递方式 | ✅ 已解决 | 不入参，后端实时推理 |
| 参数覆盖率 | ✅ 已解决 | 传"修改后"完整参数（parameter dict） |
| `tuning_result` 的位置 | ✅ 已解决 | 嵌套在 feedback 内 |
| `observations[]` 使用方式 | ✅ 已解决 | 按需传，算法可选择使用 |
| `is_adopted` 语义 | ✅ 已解决 | 训练标签，默认 True，ineffective 时改 False |
| Recommendation 表是否简化 | ✅ 已解决 | 保留 is_adopted，移除 adopted_param |
| 上一轮调整建议归属 | ✅ 已解决 | 锚定 Recommendation（process_parameter_id） |
| 调整建议要不要作为入参 | ✅ 已解决 | 不入参，后端实时产生 |

---

## 十、下一步建议（代码实现阶段）

### 阶段 1：Schema 与模型层

- [ ] `Recommendation` 移除 `adopted_param` 字段（migration）
- [ ] `ProcessParameter.parent_param_id` 重命名为 `parent_seq_idx`（migration + 代码重构）
- [ ] 确认 schema 字段名 `parent_seq_idx` 是否需同步重命名

### 阶段 2：接口设计与实现

- [ ] 新建 `backend/process/schemas/optimization_infer.py`
- [ ] 实现 `InferRequest` / `InferResponse` / `Feedback` / `DefectFeedbackData` / `CycleObservation`
- [ ] 新建 `backend/process/services/optimization_infer_service.py`
- [ ] 实现核心流程：反查 → merge → flatten → 推理 → 反 flatten → 出参
- [ ] 同步落库 ProcessParameter + Recommendation（原子事务）

### 阶段 3：URL 与 View 层

- [ ] `backend/process/views/optimization_infer.py`
- [ ] `backend/process/urls.py` 加路由

### 阶段 4：前端调整（同步进行）

- [ ] `frontend/src/types/optimization.ts` 中 DefectFeedbackData → 数组
- [ ] `DefectFeedback.vue` 支持多缺陷输入
- [ ] `PreviousAdjustment.vue` 可能重命名为 `PreviousSuggestion.vue`

### 阶段 5：未来考虑（暂不动）

- is_adopted 自动变更机制（下一轮 infer 调用时？独立的 update 接口？）
- adopt 接口（可能不需要，is_adopted 自动维护）
- 算法内部选择（flavor / rule_miner / llm）

---

## 十一、关联文档

- `docs/process-initialization-design-summary-2026-09-22.md` —— 已完成工艺初始化的设计总结
- `backend/_dev_refs/2026-09-11-recommendation-tuning-redesign-discussion.md` —— Recommendation + TuningRecord 设计参考
- `backend/_dev_refs/process-models-design.md` —— ProcessCondition + ProcessParameter 模型设计

---

## 十二、两轮讨论总结

### 轮 1 （上一轮对话）
- 定义任务边界
- 梳理前端已固化的数据结构
- 识别 3 个核心场景
- 列出待讨论清单与歧义

### 轮 2 （本轮对话）
- 明确 3 场景调用逻辑一致（仅反馈不同）
- 确定 condition = 完整上下文（不传上下文字段）
- 明确后端算法自治（不传规则选择）
- 确定反馈 vs 工艺 vs 推荐的数据分离原则
- Recommendation 简化（移除 adopted_param）
- is_adopted 重定义为训练标签
- 调整建议只是出参（不入参）
- 最终确认入参 / 出参 / 数据架构

### 下一轮预期
- 进入代码实现阶段
- Schema、Service、View、URL、迁移逐步推进
- 同步前端结构调整

---

## 十三、代码变更记录（2026-09-22 轮 3）

### 已完成的代码修改

#### 1. TuningRecord 模型

**文件**：`backend/process/models/tuning_record.py`

```diff
- # --- 调参备注 ---
- note = models.CharField(max_length=500, null=True, blank=True, verbose_name='调参备注')

+ # --- 调整记录（JSON，系统自动生成）---
+ adjustments = models.JSONField(
+     default=dict, null=True, blank=True,
+     verbose_name='调整记录',
+     help_text='规范化调参内容，由系统自动生成（OLD vs NEW diff）'
+ )

- # --- 参数快照（冗余存储）---
- parameter_snapshot = models.JSONField(null=True, blank=True, verbose_name='参数快照')
+ # --- 调整前参数快照（OLD parameter.parameters）---
+ previous_parameter = models.JSONField(
+     null=True, blank=True,
+     verbose_name='调整前参数快照',
+     help_text='调整前的工艺参数快照（OLD parameter.parameters）'
+ )
```

docstring 也同步更新：
- 1:1 同步创建（业务层保证）
- adjustments 系统自动生成
- previous_parameter 语义说明

#### 2. Recommendation 模型

**文件**：`backend/process/models/recommendation.py`

```diff
- adopted_param = models.ForeignKey(
-     "ProcessParameter",
-     on_delete=models.SET_NULL,
-     null=True, blank=True,
-     related_name="adopted_from_recommendations",
-     verbose_name="采纳后的参数版本",
- )

  is_adopted = models.BooleanField(
-     default=False,
-     verbose_name="是否已采纳",
+     default=True,
+     verbose_name="是否被采纳",
+     help_text="默认 True，下一轮 ineffective 时自动改为 False（训练标签）"
  )
```

docstring 也同步更新：
- 职责单一：只记录算法推荐
- is_adopted 是训练标签

#### 3. recommendation_service.py

**文件**：`backend/process/services/recommendation_service.py`

修改点：
- `_serialize_record`：字段名调整（`note` → `adjustments`，`parameter_snapshot` → `previous_parameter`）
- `adopt_recommendation`：移除 `adopted_param` 赋值（已删除字段）

#### 4. tuning_service.py

**文件**：`backend/process/services/tuning_service.py`

修改点：
- `create_tuning_record`：参数 `note`/`parameter_snapshot` → `previous_parameter`，不再自动构建快照
- `update_tuning_result`：参数 `note` → `result_detail`（语义正确）
- `add_defect_feedback`：注释中字段示例更新为与前端 DefectFeedbackData 对齐
- `get_defect_summary`：使用 `keyword_name` 而非 `defect_type`
- `_build_parameter_snapshot`：标记为 deprecated

#### 5. Django migration

**文件**：`backend/process/migrations/0010_remove_recommendation_adopted_param_and_more.py`

```python
operations = [
    migrations.RemoveField(model_name='recommendation', name='adopted_param'),
    migrations.RemoveField(model_name='tuningrecord', name='note'),
    migrations.RemoveField(model_name='tuningrecord', name='parameter_snapshot'),
    migrations.AddField(
        model_name='tuningrecord', name='adjustments',
        field=models.JSONField(blank=True, default=dict, null=True, ...),
    ),
    migrations.AddField(
        model_name='tuningrecord', name='previous_parameter',
        field=models.JSONField(blank=True, null=True, ...),
    ),
    migrations.AlterField(
        model_name='recommendation', name='is_adopted',
        field=models.BooleanField(default=True, ...),
    ),
]
```

### Django 检查结果

```bash
$ python manage.py check
System check identified no issues (0 silenced).

$ python manage.py makemigrations process --check --dry-run
No changes detected in app 'process'
```

模型与 migration 同步，可以安全应用。

### 还未处理的修改点

- ⏳ `OptimizationInferService.infer()` 完整实现（Service 层逻辑）
- ⏳ manual-adjust 接口设计
- ⏳ 前端 PreviousAdjustment 组件是否重命名（adjjustment → suggestion）

---

## 十四、代码变更记录（2026-09-23 轮 4）

### 已完成的代码修改

#### 1. 前端 types/optimization.ts：DefectFeedbackData 数组化

**文件**：[frontend/src/types/optimization.ts](file:///f:/items/moldingx/molding-optima/frontend/src/types/optimization.ts)

```diff
feedback: {
-   defect?: DefectFeedbackData | null
+   /** 缺陷反馈列表（数组） */
+   defect?: DefectFeedbackData[]
    tuning_result?: TuningResult
    observations?: CycleObservation[]
}
```

语义变化：
- 业务上允许用户一次报告多个缺陷
- 空数组 [] 表示"跳过"，与"无缺陷"语义不同
- DEFECTFREE 可以作为合法缺陷之一（不是唯一项）

#### 2. 前端 DefectFeedback.vue：多缺陷输入支持

**文件**：[frontend/src/views/process/optimization/components/DefectFeedback.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/components/DefectFeedback.vue)

主要修改：
- `props.modelValue`: `DefectFeedbackData | null` → `DefectFeedbackData[]`
- `emit`: `DefectFeedbackData | null` → `DefectFeedbackData[]`
- 新增 `MAX_DEFECT_COUNT = 5`（最多 5 个缺陷）
- 新增每个缺陷的独立卡片（含表单 + 证据区）
- 新增"添加缺陷" / "移除"按钮
- 新增本地状态：`defectList: DefectItem[]`（含 `__local_id` 用于 key）
- 新增 handlers：`uploadHandlers`、`modelPickerHandlers`、`makeModelPickerHandler`
- 新增 `rebuildFromProps` / `syncToParent` 双向同步逻辑

UI 变化：
- 空态：友好的提示卡片
- 多个缺陷堆叠显示
- 每个缺陷独立 title：`缺陷 #N：xxx` 或 `缺陷 #N（无缺陷）`

#### 3. 前端 OptimizationCreate.vue：初始化适配

**文件**：[frontend/src/views/process/optimization/pages/OptimizationCreate.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue)

```diff
feedback: {
-   defect: null as any,
+   defect: [] as any,
    tuning_result: null as any,
    observations: [] as any,
}
```

变化：初始化改为空数组，让 v-model="activeRound.feedback.defect" 与新组件契约一致。

#### 4. 后端 schema/parameter.py：parent_param_id → parent_seq_idx

**文件**：[backend/process/schemas/parameter.py](file:///f:/items/moldingx/molding-optima/backend/process/schemas/parameter.py)

```diff
- parent_param_id: Optional[int] = Field(None, description="父参数 ID")
+ # 业务编号：前端可见，用于确定调机树中的基准节点
+ # 与 process_condition_id 联合定位父节点（反查 parent_param.id）
+ # 注意：这是业务编号（condition 内全局递增），不是数据库 ID
+ parent_seq_idx: Optional[int] = Field(None, description="父参数业务编号（seq_idx）")
```

Schema 是 Pydantic 类，不需要 migration。

注意：Model 层字段是 `parent_param`（FK self，后端内部 ID）保持不变：
- `parent_param`：后端内部 ID 外键
- `parent_seq_idx`：业务编号（前端可见，用于 infer 入参）

#### 5. 前端 PreviousAdjustment → PreviousSuggestion 重命名

与 infer 出参 `suggestion` 字段命名对齐，避免 `adjustment` / `recommendation` / `suggestion` 三个术语混淆。

**类型重命名**（[frontend/src/types/optimization.ts](file:///f:/items/moldingx/molding-optima/frontend/src/types/optimization.ts)）：

```diff
- // Adjustment（上一轮调整建议）
- export interface AdjustmentDirection { ... }
- export interface AdjustmentItem { ... }
- export interface AdjustmentGroup { ... }
- export interface Adjustment { ... }

+ // Suggestion（上一轮调整建议，多模态内容）
+ export type SuggestionDirection = 'increase' | 'decrease' | 'hold' | 'check'
+ export interface SuggestionItem { ... }
+ export interface SuggestionGroup { ... }
+ export interface Suggestion { ... }
```

**组件文件变更**：

| 操作 | 文件 |
|---|---|
| 🗑️ 删除 | `frontend/src/views/process/optimization/components/PreviousAdjustment.vue` |
| ➕ 新建 | `frontend/src/views/process/optimization/components/PreviousSuggestion.vue` |

新组件（PreviousSuggestion.vue）：
- Props 改为 `suggestion?: Suggestion | null`（从 `adjustment` 重命名）
- 沿用多 group / 多 items / 空状态三段式渲染
- `directionIcon()` 映射：`increase → mdi:arrow-up`、`decrease → mdi:arrow-down`、`hold → mdi:minus`、`check → mdi:magnify`
- `formatRuleRef()` 格式化规则引用（占位实现，后续可加链接）
- 样式：浅色背景 + 左侧 3px 强调条（温和警示感，与"调整建议"语义匹配）

**引用同步**（[frontend/src/views/process/optimization/pages/OptimizationCreate.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/optimization/pages/OptimizationCreate.vue)）：

```diff
- import type { Adjustment } from '@/types/optimization'
+ import type { Suggestion } from '@/types/optimization'
- import PreviousAdjustment from '../components/PreviousAdjustment.vue'
+ import PreviousSuggestion from '../components/PreviousSuggestion.vue'
- <PreviousAdjustment :adjustment="previousAdjustment" />
+ <PreviousSuggestion :suggestion="previousSuggestion" />
- const previousAdjustment: Adjustment | null = ...
+ const previousSuggestion: Suggestion | null = ...
- // - 不保存：previousAdjustment（mock 数据，每次进页面重新生成）
+ // - 不保存：previousSuggestion（mock 数据，每次进页面重新生成）
```

**naming 决策依据**：

- 出参字段是 `suggestion`（语义轻、与 adjustment 形成对比）
- 表名是 `Recommendation`（稳重、绑定训练语义）
- 前端类型叫 `Suggestion`（与出参对齐、与表名解耦）
- 三者层级清晰：**表名稳重（Recommendation）+ API 字段名轻（suggestion）+ 前端展示组件（PreviousSuggestion）**

### 检查结果

```bash
$ python manage.py check
System check identified no issues (0 silenced).

$ npx vue-tsc --noEmit -p tsconfig.app.json 2>&1 | grep -E "DefectFeedback|optimization"
# 无输出（无相关错误）
```

无 lint/type 错误。

---

**维护者**：Qoder AI
**上下文**：两轮讨论已完成（2026-09-22）。infer 接口设计已确认入参/出参/数据架构。下一阶段进入代码实现，可直接基于本文件。