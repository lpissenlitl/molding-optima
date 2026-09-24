# RuleMethod 结构化编辑 + 现代化流程图（最终方案 v2）

> 状态：**v2 已确认，待实施**  
> 创建时间：2026-09-16  
> 更新时间：2026-09-16  
> 设计者：项目负责人

---

## 一、背景与目标

### 1.1 问题陈述

当前 [RuleMethodSection.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/rule/components/RuleMethodSection.vue) 的编辑抽屉（drawer 640px）有两大问题：

1. **`rule_description`（机器语言）和 `rule_explanation`（人类语言）是自由文本 textarea**，用户可以填任何语法错误的文本，后端只校验"非空"——填写人员要求过高
2. **drawer 640px 不够宽**，对于结构化编辑（多列控件 + 预览 + 元数据）来说太拥挤

### 1.2 设计目标

| 目标 | 达成方式 |
|---|---|
| **降低填写人员要求** | 用户填结构化字段，系统生成两段预览，用户不直接写 IF-THEN 文本 |
| **提供现代化可视化** | 引入流程图预览（SVG 自绘，节点化思维），让规则结构一目了然 |
| **提升编辑效率** | 整页 page 替代 drawer，左编辑右预览，符合现代 SaaS 习惯 |
| **保持后端兼容** | 不引入字段冗余，不改后端 API，不动 RuleMethod 数据模型 |

### 1.3 借鉴的方法（不抄代码）

| # | 借鉴点 | 旧版本出处 | 当前实现方式 |
|---|---|---|---|
| 1 | **结构化编辑 → 自动生成文本** | [ruleMethodDetail.vue 511-539 generateRule()](file:///F:/items/inovance-cooperation/HsMoldingWeb/src/views/processMag/optimization/subView/ruleMethodDetail.vue#L511-L539) | 抽屉改造为条件列表 + 动作列表，实时拼接 rule_description / rule_explanation |
| 2 | **条件类型 / 关键字 / 关系 联动下拉** | [ruleMethodDetail.vue 49-124](file:///F:/items/inovance-cooperation/HsMoldingWeb/src/views/processMag/optimization/subView/ruleMethodDetail.vue#L49-L124) | 字段全部从 RuleKeyword 字典拉取，按 category 分组（parameter / defect / defect_position）|
| 3 | **校验后再生成** | [ruleMethodDetail.vue 540-606 validateForm()](file:///F:/items/inovance-cooperation/HsMoldingWeb/src/views/processMag/optimization/subView/ruleMethodDetail.vue#L540-L606) | 提交前强制校验结构化字段齐全 |
| 4 | **节点化思维**（用户原创设计） | molding-optima 已实现 | 流程图节点 = 条件/动作；连线 = 因果关系 |
| 5 | **可视化预览 + 下钻编辑** | [ruleFlow.vue](file:///F:/items/inovance-cooperation/HsMoldingWeb/src/views/processMag/optimization/subView/ruleFlow.vue) 整体设计 | 左侧编辑 + 右侧流程图；点击节点 → 滚动到对应编辑行 + 高亮 |

**不抄的旧版本内容**：

- ❌ ruleSubruleDetail.vue 的字段冗余（`subrule_no` / `rule_type` / `product_small_type` / `polymer_abbreviation` 复制到每条规则）—— molding-optima 已有 RuleLibrary 外键，不需要重复
- ❌ ruleFlow.vue 的传统流程图样式 —— 节点是简单文本框、连线是直线，缺乏现代感
- ❌ 基础库 vs 子规则库分层 —— molding-optima 通过 ExpertRule.conditions JSON 实现同等灵活性
- ❌ 向导式新建 RuleLibrary —— 当前已经做得够好，不需要改

---

## 二、最终方案概览

### 2.1 三视图协同设计

整个页面围绕**同一份数据**（RuleMethod）展示三种视图，**任意一种变化 → 其它两种同步刷新**：

| 视图 | 角色 | 用户主要操作 |
|---|---|---|
| **左侧结构化编辑** | **主编辑区** | 用户**主要在这里操作**——填字段、加条件/动作 |
| **右侧流程图预览** | **只读可视化** | **可点击节点 → 滚动高亮对应编辑行** |
| **文本预览** | 给人看的 IF-THEN 文本 | 只读，实时同步 |

### 2.2 完整 UI 布局（左 70% / 右 30% sticky）

```
┌──────────────────────────────────────────────────────────────┐
│ [← 返回规则库]   编辑规则方法                  [取消] [保存]   │
├──────────────────────────────────────────────┬───────────────┤
│ 主编辑区（70%，max-width 980px）             │ 流程图（30%） │
│                                              │ sticky top:16 │
│  ┌─ 元数据 ──────────────────────────────┐   │               │
│  │ 材料 [____] 产品类别 [____] 缺陷 [飞边▼]│   │  ┌─────────┐│
│  │ 标识 [B006]优先级 [1]  置信度 [1.0]    │   │  │ ⚠ 缺陷触发││
│  │ 来源 [____] 启用 [●]                      │   │  │ 飞边/B006││
│  └────────────────────────────────────┘   │  └─────┬──────┘│
│                                              │        │       │
│  ┌─ 前置条件（IF）─────────────────────┐   │        ▼       │
│  │ [+ 条件]                            │   │  ┌─────────┐│
│  │ [类型▼][关键字▼][关系▼][值][×]   │   │  │ 🔧 参数调整││
│  │ [类型▼][关键字▼][关系▼][值][×]   │   │  │inj_pres_1││
│  └─────────────────────────────────────┘   │  │  +10    ││
│                                              │  └─────────┘│
│  ┌─ 结论动作（THEN）───────────────────┐   │        │       │
│  │ [+ 动作]                            │   │        ▼       │
│  │ [关键字▼][动作▼][值][×]          │   │  ┌─────────┐│
│  └─────────────────────────────────────┘   │  │ 🔧 参数调整││
│                                              │  │hold_time ││
│  ┌─ 文本预览 ─────────────────────────┐   │  │  -5     ││
│  │ 规则描述：IF ... THEN ...            │   │  └─────────┘│
│  │ 规则解释：如果...那么...            │   │              │
│  └─────────────────────────────────────┘   │  (随编辑实时) │
└──────────────────────────────────────────────┴───────────────┘
```

**响应式策略**：< 1100px 时流程图折叠到顶部（仍完整展示，但不再 sticky）。

---

## 三、数据模型（不变）

### 3.1 RuleMethod 字段

参考 [backend/process/models/rules.py187-247](file:///f:/items/moldingx/molding-optima/backend/process/models/rules.py#L187-L247)：

```python
class RuleMethod(BusinessBaseModel):
    rule_library = ForeignKey(RuleLibrary, ...)  # 规则库关联（已有）
    
    # 规则内容（自动生成，不允许用户手填）
    rule_description = CharField(verbose_name="规则描述")   # IF... THEN...
    rule_explanation = CharField(verbose_name="规则解释")   # 如果...那么...
    
    # 适用场景（用户填写，规则的元数据）
    polymer_abbreviation = CharField(...)   # 材料缩写
    product_category = CharField(...)       # 产品类别
    defect_label = CharField(...)           # 缺陷名称（中文）
    defect_code = CharField(...)            # 缺陷标识（code）
    
    # 元数据
    priority = IntegerField(...)            # 优先级
    confidence = FloatField(...)            # 置信度
    source = CharField(...)                 # 来源（手动/学习）
    is_active = BooleanField(...)           # 启用
```

**字段约束**：

- ✅ `rule_description` / `rule_explanation` —— **仅由结构化编辑自动生成，用户不可直接编辑**
- ✅ `polymer_abbreviation` / `product_category` / `defect_label` / `defect_code` —— 规则的**适用场景**，从字典选择
- ❌ **不引入** `subrule_no` / `rule_type` / `applicable_polymer` 等冗余字段

### 3.2 RuleKeyword 作为字典来源

所有下拉选项从 `RuleKeyword` 模型拉取（已存在），按 `category` 分组：

| Category | 用途 | UI 出现位置 |
|---|---|---|
| `parameter` | 工艺参数（注射压力、温度、速度等）| 前置条件关键字、结论动作关键字 |
| `defect` | 缺陷类型（飞边、短射等）| 前置条件关键字、缺陷名称 |
| `defect_position` | 缺陷位置 | 前置条件关键字（可选）|

**字典接入**：通过现有 `/api/processes/rule-keywords/` 接口加载，前端按 category 缓存。

**彻底抛弃** `DEFECT_CODE_MAP` 作为 RuleMethod 字典的用法。`DEFECT_CODE_MAP` 保留在 `expert_service.py` 内部作为算法固定字典，前端不再使用。

### 3.3 不引入字段冗余（约束）

明确**反对**在 RuleMethod 上重复 RuleLibrary 的字段：

| 旧版本字段 | molding-optima 对应 | 处理方式 |
|---|---|---|
| `subrule_no: str` | `rule_library: FK` | **已规范化**，不重复 |
| `rule_type: str` | `library_type: str` (在 RuleLibrary) | **已规范化**，不重复 |
| `product_small_type` (规则上) | `product_category` (规则的适用场景) | **不重复** —— 含义不同 |
| `polymer_abbreviation` (规则上) | `polymer_abbreviation` (规则的适用场景) | **不重复** —— 含义不同 |

**反模式警告**：不要给 RuleLibrary 加 `applicable_polymer` 字段——制造冗余，会和 RuleMethod 的 `polymer_abbreviation` 不一致。

---

## 四、整页 page 设计（替代 drawer）

### 4.1 路由设计

**新增 2 个路由**：

```typescript
// 新建
{ path: '/process/rules/:libraryId/methods/new', component: RuleMethodForm }

// 编辑
{ path: '/process/rules/:libraryId/methods/:methodId/edit', component: RuleMethodForm }

// 详情（只读）
{ path: '/process/rules/:libraryId/methods/:methodId/detail', component: RuleMethodForm }
```

参考现有 [ProcessParameterForm.vue1-90](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/parameter/pages/ProcessParameterForm.vue#L1-L90) 的三模式共用模式。

### 4.2 三模式（new / edit / detail）

参考 ProcessParameterForm.vue 模式：

| 模式 | route | 行为 |
|---|---|---|
| **new** | `/methods/new` | 空 form + 元数据默认值 |
| **edit** | `/methods/:id/edit` | 加载现有数据 + 允许编辑 |
| **detail** | `/methods/:id/detail` | 加载现有数据 + 所有控件 disabled |

**保存后行为**：
- new → 成功后切换到 edit 模式（保留 ID）
- edit → 成功后留在 edit 模式或返回列表（依用户操作）
- detail → 无保存按钮

### 4.3 整体布局

**沿用** molding-optima 全局表单规范：

```scss
.rule-method-form {
  display: flex;
  gap: 24px;
  padding: 16px 16px 96px;   /* 全局表单规范 */
  max-width: 1400px;
  margin: 0 auto;
}

.edit-area {
  flex: 1;
  min-width: 0;              /* 防止 flex 子项溢出 */
  display: flex;
  flex-direction: column;
  gap: 16px;                 /* 卡片间距 */
}

.graph-area {
  width: 360px;              /* 固定30% */
  position: sticky;
  top: 16px;
  align-self: flex-start;
}

@media (max-width: 1100px) {
  .rule-method-form { flex-direction: column; }
  .graph-area { width: 100%; position: static; }
}
```

**复用全局类**：`.form-actions` / `.page-header` / `.custom-form`

### 4.4 字段映射（UI ↔ 数据）

| UI 字段 | 数据模型字段 | 类型 |
|---|---|---|
| 材料缩写 | `polymer_abbreviation` | string |
| 产品类别 | `product_category` | string |
| 缺陷名称 | `defect_label` | string |
| 缺陷标识 | `defect_code` | string |
| 优先级 | `priority` | int |
| 置信度 | `confidence` | float |
| 来源 | `source` | enum |
| 启用 | `is_active` | bool |
| 规则描述 | `rule_description` | **生成** |
| 规则解释 | `rule_explanation` | **生成** |

**前置条件 / 结论动作** 是**纯 UI 字段**（不入库，仅用于生成规则描述/解释）：

```typescript
interface FormData {
  // 元数据（入库）
  polymer_abbreviation: string
  product_category: string
  defect_label: string
  defect_code: string
  priority: number
  confidence: number
  source: string
  is_active: boolean
  
  // 规则文本（自动生成，入库）
  rule_description: string
  rule_explanation: string
  
  // 结构化字段（不入库，纯 UI）
  preconditions: Array<{
    keyword: string      // keyword_name
    operator: '=' | '!=' | '>' | '<' | '>=' | '<='
    value: string | number
  }>
  actions: Array<{
    keyword: string      // keyword_name
    action: 'add' | 'reduce' | 'adjust' | 'set'
    value: string | number
  }>
}
```

---

## 五、左侧编辑区

### 5.1 元数据卡

固定字段（用户下拉选 / 数字输入）：

```vue
<el-card header="元数据">
  <el-form :model="form" inline>
    <el-form-item label="材料缩写">
      <el-select v-model="form.polymer_abbreviation" filterable clearable>
        <el-option v-for="p in polymers" :key="p.id" :label="p.abbreviation" :value="p.abbreviation" />
      </el-select>
    </el-form-item>
    <el-form-item label="产品类别">
      <el-input v-model="form.product_category" placeholder="留空=不限" />
    </el-form-item>
    <el-form-item label="缺陷名称">
      <el-select v-model="form.defect_label" filterable clearable @change="onDefectLabelChange">
        <el-option v-for="d in defectKeywords" :key="d.keyword_name" :label="d.keyword_alias" :value="d.keyword_alias" />
      </el-select>
    </el-form-item>
    <el-form-item label="缺陷标识">
      <el-input v-model="form.defect_code" placeholder="自动联动" disabled />
    </el-form-item>
    <el-form-item label="优先级">
      <el-input-number v-model="form.priority" :min="0" :max="100" />
    </el-form-item>
    <el-form-item label="置信度">
      <el-input-number v-model="form.confidence" :min="0" :max="1" :step="0.1" />
    </el-form-item>
    <el-form-item label="来源">
      <el-select v-model="form.source">
        <el-option label="手动" value="manual" />
        <el-option label="专家经验" value="expert" />
        <el-option label="学习" value="learned" />
      </el-select>
    </el-form-item>
    <el-form-item label="启用">
      <el-switch v-model="form.is_active" />
    </el-form-item>
  </el-form>
</el-card>
```

**联动规则**：选择"缺陷名称"后，从 RuleKeyword 字典查出对应 `keyword_name`，自动填入"缺陷标识"。

### 5.2 前置条件（IF）列表

```vue
<el-card header="前置条件（IF）">
  <template v-for="(cond, i) in form.preconditions" :key="i">
    <div class="condition-row">
      <el-select v-model="cond.keyword" filterable placeholder="关键字" style="width: 200px" @change="onKeywordChange(cond, $event)">
        <el-option-group label="参数">
          <el-option v-for="k in parameterKeywords" :key="k.keyword_name" :label="k.keyword_alias" :value="k.keyword_name" />
        </el-option-group>
        <el-option-group label="缺陷">
          <el-option v-for="k in defectKeywords" :key="k.keyword_name" :label="k.keyword_alias" :value="k.keyword_name" />
        </el-option-group>
        <el-option-group label="缺陷位置">
          <el-option v-for="k in defectPositionKeywords" :key="k.keyword_name" :label="k.keyword_alias" :value="k.keyword_name" />
        </el-option-group>
      </el-select>
      
      <el-select v-model="cond.operator" placeholder="关系" style="width: 100px">
        <el-option label="=" value="=" />
        <el-option label="≠" value="!=" />
        <el-option label=">" value=">" />
        <el-option label="<" value="<" />
        <el-option label="≥" value=">=" />
        <el-option label="≤" value="<=" />
      </el-select>
      
      <el-input v-model="cond.value" placeholder="值" style="width: 120px" />
      
      <el-button type="danger" :icon="Delete" circle @click="removeCondition(i)" />
    </div>
  </template>
  
  <el-button type="primary" plain :icon="Plus" @click="addCondition">+ 添加条件</el-button>
</el-card>
```

**逻辑**：
- `addCondition()` → `form.preconditions.push({ keyword: '', operator: '=', value: '' })`
- `removeCondition(i)` → `form.preconditions.splice(i, 1)`
- 至少需要 1 个条件（IF 不能为空）

### 5.3 结论动作（THEN）列表

```vue
<el-card header="结论动作（THEN）">
  <template v-for="(act, i) in form.actions" :key="i">
    <div class="action-row">
      <el-select v-model="act.keyword" filterable placeholder="关键字" style="width: 200px">
        <el-option v-for="k in parameterKeywords" :key="k.keyword_name" :label="k.keyword_alias" :value="k.keyword_name" />
      </el-select>
      
      <el-select v-model="act.action" placeholder="动作" style="width: 100px">
        <el-option label="增加" value="add" />
        <el-option label="减小" value="reduce" />
        <el-option label="弹窗" value="adjust" />
        <el-option label="设定" value="set" />
      </el-select>
      
      <el-input v-model="act.value" placeholder="值" style="width: 120px" />
      
      <el-button type="danger" :icon="Delete" circle @click="removeAction(i)" />
    </div>
  </template>
  
  <el-button type="primary" plain :icon="Plus" @click="addAction">+ 添加动作</el-button>
</el-card>
```

**逻辑**：
- `addAction()` → `form.actions.push({ keyword: '', action: 'add', value: '' })`
- `removeAction(i)` → `form.actions.splice(i, 1)`
- 至少需要 1 个动作（THEN 不能为空）

### 5.4 文本预览（左侧底部）

```vue
<el-card header="文本预览（自动生成）">
  <el-form-item label="规则描述">
    <el-input v-model="form.rule_description" type="textarea" :rows="2" readonly />
  </el-form-item>
  <el-form-item label="规则解释">
    <el-input v-model="form.rule_explanation" type="textarea" :rows="3" readonly />
  </el-form-item>
</el-card>
```

**自动生成**：通过 `watch([form.preconditions, form.actions], generateRuleText, { deep: true })` 实时刷新。

---

## 六、右侧流程图预览

### 6.1 节点设计（4 类）

| 节点类型 | 标识 | 主题色 | 用途 |
|---|---|---|---|
| **条件触发** | `mdi-alert-circle` | 警告色（橙 `#e6a23c`）| 缺陷 / 缺陷位置 |
| **参数判断** | `mdi-tune-vertical` | 信息色（蓝 `#409eff`）| 参数类条件 |
| **参数调整** | `mdi-tools` | 成功色（绿 `#67c23a`）| 动作节点 |
| **复合动作** | `mdi-cog-outline` | 主题色（紫 `#9c27b0`）| 多步动作（可选）|

**节点组件结构**：

```vue
<div class="graph-node" :class="`node-${type}`">
  <AppIcon :icon="iconMap[type]" :size="20" />
  <div class="node-title">{{ keyword.alias }}</div>
  <div class="node-meta">{{ operator }} {{ value }}</div>
</div>
```

### 6.2 连线策略（全连接）

**条件聚合 + 全连接**：

```
条件区                              动作区
┌─────┐
│cond1│─┐
└─────┘ │
┌─────┐ │                            ┌─────┐
│cond2│─┼──→ （AND）──→  ┌─────┐
└─────┘ │                            │act1 │
...                                └─────┘
┌─────┐ │                              │  ┌─────┐
│condN│─┘                              └──│act2 │
└─────┘                                  └─────┘
```

- 每个条件节点 → 每个动作节点各一条连线（笛卡尔积）
- 节点少时（< 5 条件 + < 5 动作）连线清晰
- 节点多时自动按"动作分组"，简化连线

### 6.3 SVG 自绘方案

**零依赖**：纯 Vue 3 + SVG，不引入 vue-flow / mxgraph 等第三方图库。

```vue
<template>
  <div class="rule-graph">
    <!-- 条件列 -->
    <div class="node-column">
      <div
        v-for="(cond, i) in conditions"
        :key="`c-${i}`"
        :ref="el => setNodeRef('condition', i, el)"
        class="graph-node node-condition"
        @click="$emit('node-click', { type: 'condition', index: i })"
      >
        <AppIcon :icon="iconForCondition(cond)" :size="20" />
        <div class="node-title">{{ aliasOf(cond.keyword) }}</div>
        <div class="node-meta">{{ cond.operator }} {{ cond.value }}</div>
      </div>
    </div>

    <!-- 连线层（绝对定位 SVG）-->
    <svg class="graph-edges">
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0 0 L 8 4 L 0 8 z" fill="#909399" />
        </marker>
      </defs>
      <path
        v-for="(edge, i) in edges"
        :key="`e-${i}`"
        :d="edge.d"
        stroke="#c0c4cc"
        stroke-width="2"
        fill="none"
        marker-end="url(#arrow)"
      />
    </svg>

    <!-- 动作列 -->
    <div class="node-column">
      <div
        v-for="(act, i) in actions"
        :key="`a-${i}`"
        :ref="el => setNodeRef('action', i, el)"
        class="graph-node node-action"
        @click="$emit('node-click', { type: 'action', index: i })"
      >
        <AppIcon :icon="iconForAction(act)" :size="20" />
        <div class="node-title">{{ aliasOf(act.keyword) }}</div>
        <div class="node-meta">{{ actionLabel(act.action) }} {{ act.value }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rule-graph {
  position: relative;
  display: flex;
  gap: 80px;        /* 给 SVG 连线留空间 */
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #fafbfc 100%);
  border-radius: 8px;
  min-height: 240px;
}
.node-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}
.graph-node {
  background: #fff;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 12px;
  border-left: 4px solid;
}
.graph-node:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}
.node-condition { border-left-color: #e6a23c; }
.node-parameter { border-left-color: #409eff; }
.node-action { border-left-color: #67c23a; }
.graph-edges {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
</style>
```

### 6.4 节点 ↔ 编辑行 联动

| 用户动作 | 反馈 |
|---|---|
| **编辑左侧字段** | 右侧流程图节点实时增删/更新 |
| **点击右侧流程图节点** | 滚动到对应左侧编辑行 + 高亮闪烁 2 秒 |
| **流程图节点 hover** | 显示 tooltip（条件/动作的详情）|

**实现方式**：

```typescript
// RuleMethodForm.vue 中
const scrollToRow = (type: 'condition' | 'action', index: number) => {
  const selector = type === 'condition' ? `.condition-row-${index}` : `.action-row-${index}`
  const el = document.querySelector(selector) as HTMLElement
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('highlight-flash')
    setTimeout(() => el.classList.remove('highlight-flash'), 2000)
  }
}
```

---

## 七、关键函数

### 7.1 generateRuleText() —— 自动生成规则文本

```typescript
function generateRuleText(): void {
  // 规则描述（机器语言）：IF cond1 AND cond2 ... THEN act1 AND act2 ...
  const condDesc = form.preconditions
    .filter(c => c.keyword && c.value !== '')
    .map(c => `${c.keyword}${c.operator}${c.value}`)
    .join(' AND ')
  
  const actDesc = form.actions
    .filter(a => a.keyword && a.value !== '')
    .map(a => `${a.keyword}${a.action}${a.value}`)
    .join(' AND ')
  
  form.rule_description = condDesc && actDesc
    ? `IF ${condDesc} THEN ${actDesc}`
    : ''
  
  // 规则解释（人类语言）：如果 A op A_val，B op B_val，那么 A action val。
  const opMap: Record<string, string> = {
    '=': '等于', '!=': '不等于', '>': '大于',
    '<': '小于', '>=': '大于等于', '<=': '小于等于'
  }
  const actionMap: Record<string, string> = {
    add: '增加', reduce: '减小', adjust: '弹窗', set: '设定'
  }
  
  const condExp = form.preconditions
    .filter(c => c.keyword && c.value !== '')
    .map((c, i) => {
      const alias = aliasOf(c.keyword) || c.keyword
      const op = opMap[c.operator] || c.operator
      return `${alias} ${op} ${c.value}`
    })
    .join('，且 ')
  
  const actExp = form.actions
    .filter(a => a.keyword && a.value !== '')
    .map((a, i) => {
      const alias = aliasOf(a.keyword) || a.keyword
      const act = actionMap[a.action] || a.action
      return `${alias} ${act} ${a.value}`
    })
    .join('，')
  
  form.rule_explanation = condExp && actExp
    ? `如果${condExp}，那么${actExp}。`
    : ''
}
```

### 7.2 校验函数

```typescript
function validate(): boolean {
  if (!form.rule_library_id) {
    ElMessage.warning('规则库不能为空')
    return false
  }
  if (form.preconditions.length === 0) {
    ElMessage.warning('请至少添加 1 个前置条件')
    return false
  }
  if (form.actions.length === 0) {
    ElMessage.warning('请至少添加 1 个结论动作')
    return false
  }
  for (const [i, c] of form.preconditions.entries()) {
    if (!c.keyword) { ElMessage.warning(`前置条件 ${i+1} 关键字未填`); return false }
    if (!c.value) { ElMessage.warning(`前置条件 ${i+1} 值未填`); return false }
  }
  for (const [i, a] of form.actions.entries()) {
    if (!a.keyword) { ElMessage.warning(`结论动作 ${i+1} 关键字未填`); return false }
    if (!a.value) { ElMessage.warning(`结论动作 ${i+1} 值未填`); return false }
  }
  return true
}
```

### 7.3 反向解析（编辑现有规则时）

**Phase 1（本次实施）**：仅做"正向生成"。编辑现有规则时，**`preconditions` 和 `actions` 默认为空**，用户在结构化编辑区重新填一遍（旧的 rule_description 仅作参考）。

**Phase 2（后续）**：实现反向解析函数：

```typescript
function parseRuleDescription(text: string): {
  preconditions: Condition[], actions: Action[]
} {
  // 解析 IF A AND B THEN C AND D 格式
  const match = text.match(/^IF\s+(.+?)\s+THEN\s+(.+)$/i)
  if (!match) return { preconditions: [], actions: [] }
  
  const parseItems = (s: string, isAction: boolean) => {
    return s.split(/\s+AND\s+/i).map(item => {
      if (isAction) {
        // keyword + action + value，如 inj_pres_1+10
        const m = item.match(/^(.+?)(add|reduce|adjust|set)(.+)$/i)
        if (m) return { keyword: m[1], action: m[2].toLowerCase(), value: m[3] }
      } else {
        // keyword + operator + value，如 inj_pres_1=100
        const m = item.match(/^(.+?)(=|!=|>=|<=|>|<)(.+)$/)
        if (m) return { keyword: m[1], operator: m[2], value: m[3] }
      }
      return null
    }).filter(Boolean)
  }
  
  return {
    preconditions: parseItems(match[1], false),
    actions: parseItems(match[2], true)
  }
}
```

**降级策略**：解析失败时，结构化编辑区为空，提示用户"请重新填写"。

---

## 八、实施步骤（4 步）

### 8.1 步骤 1：设计文档 ✅（本文档）

### 8.2 步骤 2：新建 RuleMethodForm.vue 主页面

**文件路径**：`frontend/src/views/process/rule/pages/RuleMethodForm.vue`

**结构**：
- `<template>` 三模式共用布局
- `<script setup lang="ts">` 三模式逻辑（new / edit / detail）
- 引用 `<RuleMethodGraph />` 子组件

**预计工作量**：3-4 小时

### 8.3 步骤 3：新建 RuleMethodGraph.vue 流程图组件

**文件路径**：`frontend/src/views/process/rule/components/RuleMethodGraph.vue`

**结构**：
- props: `conditions`, `actions`, `keywords`
- emits: `node-click`
- SVG 自绘 + 节点交互

**预计工作量**：1-2 小时

### 8.4 步骤 4：路由改造 + RuleMethodSection drawer 移除

**改动**：
1. `frontend/src/router/index.ts` 加 3 个路由（new / edit / detail）
2. `frontend/src/views/process/rule/components/RuleMethodSection.vue` drawer 移除，改为 `router.push`

**预计工作量**：30 分钟

---

## 九、约束与边界

### 9.1 不做的部分

| 不做 | 理由 |
|---|---|
| ❌ 流程图直接拖拽编辑 | 易错位，结构化编辑更可靠 |
| ❌ 引入 vue-flow / mxgraph | 零依赖方案足够（节点数 < 10）|
| ❌ 给 RuleMethod 加 conditions/actions 子 Model | 保持后端字段不变 |
| ❌ 改写 DEFECT_CODE_MAP | 内部保留，RuleKeyword 替代 |
| ❌ 重构 RuleLibrary / RuleKeyword / ExpertRule | 只动 RuleMethod |
| ❌ 向导式新建 RuleLibrary | 当前已经做得够好 |
| ❌ 反向解析（Phase 2）| 本次只做正向生成 |
| ❌ 全文搜索 / 自动校验 | 后续 Phase |

### 9.2 沿用的现有规范

- 整页 page 规范：[ProcessParameterForm.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/parameter/pages/ProcessParameterForm.vue)
- 全局样式类：`.form-actions` / `.page-header` / `.custom-form`
- 多租户隔离：company + owner_type
- 业务组件复用：`<AppIcon />` 等全局组件
- API 调用：`/api/processes/rule-keywords/`、`/api/processes/rules/`

### 9.3 风险与回退

| 风险 | 缓解 |
|---|---|
| 现有抽屉突然消失影响用户 | 抽屉**保留为只读模式**（detail 模式直接走新 page，原 drawer 仅作过渡期保留）|
| 反向解析失败导致用户无法编辑现有规则 | Phase 1 接受"重新填一遍"的成本 |
| 流程图节点多时连线密集 | 节点数限制 < 10；超出时提示简化 |

---

## 十、附录

### 10.1 字段命名对照（中文 / 英文）

| 中文 UI 标签 | 英文字段名 | 类型 |
|---|---|---|
| 规则描述 | rule_description | string |
| 规则解释 | rule_explanation | string |
| 材料缩写 | polymer_abbreviation | string |
| 产品类别 | product_category | string |
| 缺陷名称 | defect_label | string |
| 缺陷标识 | defect_code | string |
| 优先级 | priority | int |
| 置信度 | confidence | float |
| 来源 | source | enum (manual / expert / learned) |
| 启用 | is_active | bool |

### 10.2 RuleKeyword category 与 UI 字段对应

| Category | UI 出现位置 | 下拉选项 |
|---|---|---|
| `parameter` | 前置条件关键字 / 结论动作关键字 | 工艺参数列表 |
| `defect` | 前置条件关键字 / 缺陷名称 | 缺陷类型列表 |
| `defect_position` | 前置条件关键字 | 缺陷位置列表 |

### 10.3 关键引用文件

| 文件 | 作用 |
|---|---|
| [backend/process/models/rules.py](file:///f:/items/moldingx/molding-optima/backend/process/models/rules.py) | RuleMethod Model 定义 |
| [backend/process/services/rule_service.py](file:///f:/items/moldingx/molding-optima/backend/process/services/rule_service.py) | RuleMethod CRUD |
| [backend/process/services/expert_service.py:16-34](file:///f:/items/moldingx/molding-optima/backend/process/services/expert_service.py#L16-L34) | DEFECT_CODE_MAP（保留为内部算法字典）|
| [frontend/src/views/process/rule/components/RuleMethodSection.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/rule/components/RuleMethodSection.vue) | 当前抽屉（待改造）|
| [frontend/src/views/process/parameter/pages/ProcessParameterForm.vue](file:///f:/items/moldingx/molding-optima/frontend/src/views/process/parameter/pages/ProcessParameterForm.vue) | 整页 page 模板参考 |
| [F:/items/inovance-cooperation/HsMoldingWeb/.../ruleMethodDetail.vue](file:///F:/items/inovance-cooperation/HsMoldingWeb/src/views/processMag/optimization/subView/ruleMethodDetail.vue) | 旧版本参考（结构化编辑方法）|

---

*文档版本：v2（最终方案，已确认）*  
*下一步：开始实施，新建 RuleMethodForm.vue 主页面*