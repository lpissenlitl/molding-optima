# 推荐结果与调参记录 - 设计参考

**日期**: 2026-09-11
**状态**: 📌 待定 - 前端 UI 优先

---

## 1. 当前模型状态（待保留参考）

### Recommendation 模型
位置: `backend/process/models/recommendation.py`

```python
class Recommendation(BusinessBaseModel):
    process_parameter = FK(ProcessParameter, related_name='recommendations')
    source_type = CharField(choices=[
        ('fuzzy_rule', '模糊规则推理'),
        ('rule_miner', '规则挖掘学习'),
        ('llm', '大语言模型'),
        ('doe', '实验设计优化'),
        ('genetic', '遗传算法'),
    ])
    recommendations = JSONField(default=list)
    is_adopted = BooleanField(default=False)
    adopted_param = FK(ProcessParameter, related_name='adopted_from_recommendations',
                        null=True, on_delete=SET_NULL)
```

**字段数**: 6（含 FK + 元数据）

### TuningRecord 模型
位置: `backend/process/models/tuning_record.py`

```python
class TuningRecord(BusinessBaseModel):
    process_parameter = FK(ProcessParameter, related_name='tuning_records')
    defect_feedbacks = JSONField(default=list)  # 缺陷列表
    note = CharField(max_length=500, null=True)
    result = CharField(choices=[
        ('pending', '待验证'),
        ('improved', '有改善'),
        ('worse', '效果变差'),
        ('unchanged', '无变化'),
        ('qualified', '合格'),
        ('unqualified', '不合格'),
    ], default='pending')
    result_detail = CharField(max_length=500, null=True)
    parameter_snapshot = JSONField(null=True, blank=True)
```

**字段数**: 6

### 已知问题

1. **Recommendation 直接关联 ProcessParameter**，没有锁定具体参数版本（参数是树结构）
2. **TuningRecord.parameter_snapshot 冗余** — ProcessCondition.process_context_snapshot 已经存储
3. **没有直接记录"参数变更的 diff"**（旧值→新值）—— 这是数据挖掘最关键的字段
4. **result 状态字段语义合理**，但与变更逻辑分离

---

## 2. 推荐方向（重构方案）

### 核心观点

> 不管是人工还是人工智能，**核心都离不开参数的变更**
> **参数变更历史**是数据挖掘的来源

### 建议的新模型

#### 2.1 ParameterChange（参数变更日志）— **核心数据源**

```python
class ParameterChange(BusinessBaseModel):
    """
    参数变更记录 - 数据挖掘的核心数据源

    每次参数调整都产生一条记录，包含：
    - 变更前/后参数值（diff）
    - 变更原因（缺陷/优化/AI/手工）
    - 变更来源
    """
    process_parameter = FK(ProcessParameter)
    parent_change = FK('self', null=True)  # 形成变更链

    # 变更内容（diff 列表）
    change_data = JSONField(default=list)
    # 示例: [
    #     {'param': 'inj_pres_1', 'old': 50, 'new': 60, 'delta': 10},
    #     {'param': 'hold_pres_1', 'old': 30, 'new': 35, 'delta': 5},
    # ]

    # 变更原因
    REASON_CHOICES = [
        ('defect_fix', '缺陷修复'),
        ('optimization', '优化'),
        ('ai_suggest', 'AI 推荐'),
        ('manual', '人工调整'),
        ('equipment', '设备同步'),
        ('initial', '初始化'),
    ]
    reason = CharField(choices=REASON_CHOICES)

    # 变更来源
    source = CharField()  # expert/ai/algorithm/manual

    # 关联（可空）
    recommendation = FK(Recommendation, null=True)
    trial_feedback = FK(TrialFeedback, null=True)
```

#### 2.2 TrialFeedback（试模反馈）

```python
class TrialFeedback(BusinessBaseModel):
    """试模反馈 - 缺陷 + 结果"""
    parameter_change = FK(ParameterChange)  # 关联到具体的参数变更

    defect_feedbacks = JSONField(default=list)  # 缺陷列表
    result = CharField(choices=[
        ('pending', '待验证'),
        ('improved', '有改善'),
        ('worse', '效果变差'),
        ('unchanged', '无变化'),
        ('qualified', '合格'),
        ('unqualified', '不合格'),
    ])
    result_detail = CharField(max_length=500, null=True)
    note = CharField(max_length=500, null=True)
    # 删除 parameter_snapshot（冗余）
```

#### 2.3 Recommendation（可选重构）

```python
class Recommendation(BusinessBaseModel):
    """
    推荐方案 - AI/算法生成的建议
    """
    # 改为关联 ParameterChange（而非 ProcessParameter）
    parameter_change = FK(ParameterChange, null=True)  # 实际应用的变更

    source_type = CharField(choices=[
        ('fuzzy_rule', '模糊规则推理'),
        ('rule_miner', '规则挖掘学习'),
        ('llm', '大语言模型'),
        ('doe', '实验设计优化'),
        ('genetic', '遗传算法'),
    ])
    recommendations = JSONField(default=list)
    is_adopted = BooleanField(default=False)

    # 删除 adopted_param（冗余，已通过 parameter_change 关联）
```

---

## 3. 推荐方案的核心优势

| 优势 | 说明 |
|------|------|
| **变更可追溯** | 每次参数调整都形成一条记录，可串联成变更链 |
| **数据挖掘友好** | `change_data` 直接包含 old → new，可直接用于训练 |
| **避免冗余存储** | TrialFeedback 不再重复存参数快照 |
| **推荐闭环** | Recommendation → ParameterChange（推荐被采纳）|
| **历史完整** | 通过 `parent_change` 形成"调参演化树" |
| **符合核心观点** | 参数变更 = 数据挖掘的金矿 |

---

## 4. 决策记录

### 决策：暂不重构

**原因**：
1. 当前业务尚未涉及自动学习/数据挖掘
2. 前端 UI（工艺参数、规则库）功能优先
3. 模型设计应基于实际使用场景迭代

### 后续行动

1. ✅ 保留当前模型（Recommendation + TuningRecord）
2. 🔄 前端 UI 开发（工艺参数、规则库）
3. 📌 当 AI 推荐 / 数据挖掘功能上线时，回顾本设计
4. 📌 届时根据实际数据量、使用场景评估是否需要重构

---

## 5. 关键问题讨论（未来回顾时）

- ParameterChange 是否需要独立的变更日志表？
- 变更链（parent_change）是否必要？还是用 seq_idx 即可？
- Recommendation 改为关联 ParameterChange 后，adopted_param 是否还需要？
- TrialFeedback.parameter_snapshot 是否冗余？
- 数据挖掘模型如何从 change_data 提取训练样本？

---

**维护者**: molding-optima 后端
**最后更新**: 2026-09-11