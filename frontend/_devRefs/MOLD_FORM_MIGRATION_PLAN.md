# Mold 表单迁移实施计划

> **目的**：基于"渐进式嵌套 + 层级标签化"的设计哲学，把 mold 模块从"3 重 el-tabs 嵌套"重写为"可折叠卡片"，对齐 project/form.vue 的新规范。
> **创建时间**：2026-09-07
> **设计参考**：[mold-migration-design-summary-2026-09-03.md](../../docs/mold-migration-design-summary-2026-09-03.md) §5.2
> **配套规范**：[FORM_CODING_STANDARD.md](FORM_CODING_STANDARD.md)

---

## 一、三个核心决策（已确认）

| 决策 | 选择 | 原因 |
|------|------|------|
| 嵌套展示 | **可折叠卡片**（el-collapse 替代 el-tabs）| 解决 3 重 tabs 嵌套视觉混乱 |
| Cavity / Gate 子组件 | **不拆 vue 文件** | 嵌套层级固定，无需独立复用 |
| 条件显示 | **v-if 动态** | 跟现状一致 |

---

## 二、数据模型摘要

```
Mold（顶层 ~30 字段）
├── 1:N  GatingSystem（~20 字段，含条件显示：热流道/冷流道/热转冷）
│   └── 1:N  Cavity（~12 字段）
│       └── 1:N  Gate（~12 字段，含条件显示：矩形/圆形/梯形/环形）
├── 1:1  CoolingSystem（~14 字段）
└── 1:1  EjectionSystem（~12 字段）
```

**总计 ~100 字段，4 层嵌套，2 处条件显示**。

---

## 三、目标架构

```
views/mold/
├── pages/
│   ├── MoldList.vue (待改：对齐 BaseSearchForm + BaseTable)
│   └── MoldForm.vue (主表单：custom-form 规范)
└── components/
    ├── MoldSearchForm.vue (✅ 已 OK)
    ├── GatingSystemForm.vue (重写：3 层 el-collapse + FormItem 数组)
    ├── CoolingSystemForm.vue (重写：FormItem 数组)
    └── EjectionSystemForm.vue (重写：FormItem 数组)
```

---

## 四、目标 UI 结构

```
┌──────────────────────────────────┐
│  [← 返回列表]                     │ page-header（不加 h2）
├──────────────────────────────────┤
│ ▼ 基本信息                        │ custom-form__section #1
│   Mold 30+ 字段（4 列布局）        │
├──────────────────────────────────┤
│ ▼ 注射成型配置 [N 个注射]          │ custom-form__section #2
│   ▼ 注射 #1 [M 个产品] [×]        │ el-collapse-item
│     GatingSystem 字段（条件显示）   │
│     ▼ 产品 A [K 个浇口] [×]       │ 嵌套 el-collapse-item
│       Cavity 字段
│       ▼ 浇口 #1 [形状] [×]        │ 嵌套 el-collapse-item
│         Gate 字段（条件尺寸字段）
│       [+ 添加浇口]
│     [+ 添加产品]
│   ▼ 注射 #2 ...
│   [+ 添加注射]
├──────────────────────────────────┤
│ ▼ 冷却系统                        │ custom-form__section #3
│   CoolingSystem 字段
├──────────────────────────────────┤
│ ▼ 顶出系统                        │ custom-form__section #4
│   EjectionSystem 字段
├──────────────────────────────────┤
│ [取消] [保存]                      │ form-actions（在 el-form 外）
└──────────────────────────────────┘
```

---

## 五、FormItem 抽象的策略

### 5.1 类型扩展

当前 [`form-types.ts`](../../src/utils/form-types.ts) 支持：`input | select | date | textarea | number | divider`

mold 表单需要扩展：

| 字段类型 | 来源 | 说明 |
|---------|------|------|
| `radio` | GatingSystem/Ejection | 布尔字段（has_sequencing_control / has_pre_ejection）|
| `integer` | 全部子组件 | 整数字段（冷却回路数量、浇口数量、推荐吨位）|
| `autocomplete` | Mold 顶层 | 推荐吨位（带历史输入）|

```typescript
type FormItemType = 
  | 'input' 
  | 'select' 
  | 'date' 
  | 'textarea' 
  | 'number' 
  | 'integer'     // ← 新增（整数）
  | 'radio'       // ← 新增（布尔单选）
  | 'autocomplete' // ← 新增（自动补全）
  | 'divider'
```

**字段扩展**：
- `radio`: 用 el-radio-group 渲染
- `integer`: 复用 number，加 v-number="0" 限制整数
- `autocomplete`: 用 el-autocomplete，需传 `query` 配置

### 5.2 不抽 BaseFormItem 组件的决策

**不抽** BaseFormItem / RenderFormItem 公共组件，原因：

| 反对抽象的理由 | 说明 |
|----------|------|
| **Vue 生态主流不抽** | Element Plus / Ant Design / Naive UI 业务方都直接用 UI 控件 |
| **抽象成本高** | 10+ 个 v-if 链，200+ 行单文件 |
| **完整性陷阱** | mold 要 7 种，polymer 要 5 种，equipment 要 6 种——难统一 |
| **样式定制难** | 业务方调样式时需穿透抽象 |
| **半年后恶化** | 需求演进会让组件持续膨胀 |

**实际方案**：
- ✅ 保留 `FormItem[]` 数组抽象（字段集中管理，加字段零模板改动）
- ✅ 用 `getPlaceholder` / `getDisabled` 等 helper 函数（详见 [`form-helper.ts`](../../src/utils/form-helper.ts)）
- ✅ 每个 form 模板里写 5-7 个 v-else-if 链（不长，可读）

**模板示例**：

```vue
<!-- mold/components/GatingSystemForm.vue -->
<el-form-item v-for="item in basicItems" :key="item.prop" :label="item.label" :prop="item.prop">
  <el-input v-if="item.type === 'input' || item.type === 'integer'"
    v-model="gating[item.prop]"
    v-number="item.type === 'integer' ? 0 : undefined"
    :placeholder="getPlaceholder(item)"
    :disabled="getDisabled(item)"
  >
    <template #suffix v-if="item.unit">{{ item.unit }}</template>
  </el-input>
  <el-select v-else-if="item.type === 'select'"
    v-model="gating[item.prop]"
    :placeholder="getPlaceholder(item)"
    :disabled="getDisabled(item)"
  >
    <el-option v-for="opt in item.options" :key="opt.value" :label="opt.label" :value="opt.value" />
  </el-select>
  <el-radio-group v-else-if="item.type === 'radio'" v-model="gating[item.prop]">
    <el-radio-button :label="true">是</el-radio-button>
    <el-radio-button :label="false">否</el-radio-button>
  </el-radio-group>
  <el-autocomplete v-else-if="item.type === 'autocomplete'"
    v-model="gating[item.prop]"
    :placeholder="getPlaceholder(item)"
    :fetch-suggestions="$querySuggestions(item.query)"
  />
  <el-input v-else-if="item.type === 'textarea'"
    v-model="gating[item.prop]"
    type="textarea"
    :rows="item.rows || 4"
    :placeholder="getPlaceholder(item)"
  />
</el-form-item>
```

**优点**：
- 模板直观，调试简单
- 业务方加新类型只需加 v-else-if，不需改公共组件
- 抽象成本为零

**可接受的重复**：
- 5-7 个 v-else-if 链在每个 form 写一次（5 个 form × 50 行 = 250 行重复）
- 但都是简单调用，重复成本低
- 真正需要共享的部分（placeholder / disabled）用 helper

---

## 六、字段定义分组（每组件一组 FormItem[]）

### 6.1 GatingSystemForm 字段（按条件显示分组）

```typescript
// 基础字段（始终显示）
const basicItems: FormItem[] = [
  { label: '流道类别', prop: 'runner_type', type: 'select', options: runnerTypeOptions },
  { label: '制品总重量', prop: 'total_product_weight', type: 'number', unit: 'g' },
]

// 热流道字段（runner_type = 热流道/热转冷）
const hotRunnerItems: FormItem[] = [
  { label: '热流道供应商', prop: 'hot_runner_supplier', type: 'input' },
  { label: '热流道类型', prop: 'hot_runner_system_type', type: 'select', options: hotNozzleTypeOptions },
  // ...
]

// 冷流道字段（runner_type = 冷流道/热转冷）
const coldRunnerItems: FormItem[] = [
  { label: '料把重量', prop: 'runner_weight', type: 'number', unit: 'kg' },
  // ...
]

// Cavity 字段
const cavityItems: FormItem[] = [
  { label: '每射成型腔数', prop: 'cavity_count_per_shot', type: 'integer', unit: '腔' },
  { label: '制品名称', prop: 'product_name', type: 'input' },
  // ...
]

// Gate 基础字段（始终显示）
const gateBaseItems: FormItem[] = [
  { label: '浇口类型', prop: 'gate_type', type: 'select', options: gateTypeOptions },
  { label: '浇口数量', prop: 'gate_count', type: 'integer', unit: '个' },
  // ...
]

// Gate 尺寸字段（按 gate_shape 条件显示）
const gateRectItems: FormItem[] = [/* 矩形: length, width */]
const gateCircleItems: FormItem[] = [/* 圆形: diameter */]
const gateAnnulusItems: FormItem[] = [/* 环形: outer_diameter, inner_diameter, gap */]
```

### 6.2 CoolingSystemForm 字段

```typescript
const coolingItems: FormItem[] = [
  { label: '前模（定模）', type: 'divider' },
  { label: '型腔冷却类型', prop: 'cooling_cavity_type', type: 'select', options: coolingTypeOptions },
  // ...（14 字段）
]
```

### 6.3 EjectionSystemForm 字段

```typescript
const ejectionItems: FormItem[] = [
  { label: '顶出类型', prop: 'ejection_type', type: 'select', options: ejectionTypeOptions },
  // ...（含 radio 类型 has_pre_ejection）
]
```

---

## 七、3 层 el-collapse 设计

### 7.1 GatingSystemForm 内的折叠结构

```vue
<template>
  <el-collapse v-model="activeGating">
    <el-collapse-item
      v-for="(gating, gIdx) in gatingSystems"
      :key="gIdx"
      :name="String(gIdx)"
    >
      <template #title>
        <span class="collapse-title">
          注射 #{{ gIdx + 1 }}
          <el-tag size="small">{{ gating.cavities.length }} 个产品</el-tag>
        </span>
        <el-button text type="danger" @click.stop="removeGating(gIdx)">
          <AppIcon icon="mdi:trash-can-outline" />
        </el-button>
      </template>

      <!-- GatingSystem 字段（基础 + 热流道/冷流道 条件显示） -->
      <el-form class="custom-form" :model="gating">
        <el-row :gutter="24">
          <el-col v-for="item in basicItems" :key="item.prop" :span="item.span || 6">
            <el-form-item :label="item.label" :prop="item.prop">
              <el-input
                v-if="item.type === 'input' || item.type === 'integer'"
                v-model="gating[item.prop]"
                v-number="item.type === 'integer' ? 0 : undefined"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>
              <el-select
                v-else-if="item.type === 'select'"
                v-model="gating[item.prop]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
              >
                <el-option v-for="opt in item.options" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <template v-if="showHotRunner(gating)">
          <el-divider content-position="left">热流道</el-divider>
          <el-row :gutter="24">
            <el-col v-for="item in hotRunnerItems" :key="item.prop" :span="item.span || 6">
              <el-form-item :label="item.label" :prop="item.prop">
                <!-- 与上面相同的 v-else-if 链 -->
                <el-input v-if="item.type === 'input' || item.type === 'integer'" ... />
                <el-select v-else-if="item.type === 'select'" ... />
                <el-radio-group v-else-if="item.type === 'radio'" ...>...</el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        <!-- 冷流道同理 -->
      </el-form>

      <!-- Cavity 折叠卡片（嵌套） -->
      <el-divider content-position="left">产品列表</el-divider>
      <el-collapse v-model="gating._activeCavity">
        <el-collapse-item
          v-for="(cavity, cIdx) in gating.cavities"
          :key="cIdx"
          :name="String(cIdx)"
        >
          <template #title>
            <span class="collapse-title">
              产品 #{{ cIdx + 1 }}
              <el-tag size="small">{{ cavity.gates.length }} 个浇口</el-tag>
            </span>
            <el-button text type="danger" @click.stop="removeCavity(gIdx, cIdx)">
              <AppIcon icon="mdi:trash-can-outline" />
            </el-button>
          </template>

          <!-- Cavity 字段 -->
          <el-form class="custom-form" :model="cavity">
            <el-row :gutter="24">
              <el-col v-for="item in cavityItems" :key="item.prop" :span="item.span || 6">
                <el-form-item :label="item.label" :prop="item.prop">
                  <!-- 与 GatingSystem 相同的 v-else-if 链 -->
                  <el-input v-if="item.type === 'input' || item.type === 'integer'" ... />
                  <el-select v-else-if="item.type === 'select'" ... />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <!-- Gate 折叠卡片（嵌套） -->
          <el-divider content-position="left">浇口列表</el-divider>
          <el-collapse v-model="cavity._activeGate">
            <el-collapse-item
              v-for="(gate, gtIdx) in cavity.gates"
              :key="gtIdx"
              :name="String(gtIdx)"
            >
              <template #title>
                <span class="collapse-title">
                  浇口 #{{ gtIdx + 1 }}
                  <el-tag size="small" :type="gate.gate_shape ? 'success' : 'info'">
                    {{ gate.gate_shape || '未选择' }}
                  </el-tag>
                </span>
                <el-button text type="danger" @click.stop="removeGate(gIdx, cIdx, gtIdx)">
                  <AppIcon icon="mdi:trash-can-outline" />
                </el-button>
              </template>

              <!-- Gate 字段 + 条件尺寸字段 -->
              <el-form class="custom-form" :model="gate">
                <el-row :gutter="24">
                  <el-col v-for="item in gateBaseItems" :key="item.prop" :span="item.span || 6">
                    <el-form-item :label="item.label" :prop="item.prop">
                      <el-input v-if="item.type === 'input' || item.type === 'integer'" ... />
                      <el-select v-else-if="item.type === 'select'" ... />
                    </el-form-item>
                  </el-col>
                </el-row>
                <template v-if="gate.gate_shape === '矩形'">
                  <el-divider content-position="left">矩形尺寸</el-divider>
                  <el-row :gutter="24">
                    <el-col v-for="item in gateRectItems" :key="item.prop" :span="item.span || 6">
                      <el-form-item :label="item.label" :prop="item.prop">
                        <el-input v-model="gate[item.prop]" v-number />
                      </el-form-item>
                    </el-col>
                  </el-row>
                </template>
                <!-- 圆形、环形同理 -->
              </el-form>
            </el-collapse-item>
          </el-collapse>

          <el-button text @click="addGate(gIdx, cIdx)">
            <AppIcon icon="mdi:plus" /> 添加浇口
          </el-button>
        </el-collapse-item>
      </el-collapse>

      <el-button text @click="addCavity(gIdx)">
        <AppIcon icon="mdi:plus" /> 添加产品
      </el-button>
    </el-collapse-item>
  </el-collapse>

  <el-button @click="addGating">
    <AppIcon icon="mdi:plus" /> 添加注射
  </el-button>
</template>
```

### 7.2 折叠状态默认值

```typescript
// activeGating 决定哪些 GatingSystem 默认展开
const activeGating = ref(['0'])  // 默认展开第一个

// 每个 GatingSystem 内的 _activeCavity / 每个 Cavity 内的 _activeGate
// 同样默认展开第一个
```

**但是**：`_activeCavity` 是 GatingSystem 对象上的字段，会被序列化到后端。
**解决**：用 `markRaw` 或单独的本地 state（不放在数据对象上）。

```typescript
// 折叠状态用单独的 ref（不放在 gatingSystem 数据对象上）
const activeGating = ref(['0'])
const activeCavityMap = ref<Record<number, string[]>>({ 0: ['0'] })
const activeGateMap = ref<Record<string, string[]>>({ '0-0': ['0'] })
```

---

## 八、添加/删除操作

```typescript
function addGating() {
  mold_info.value.gating_systems.push(structuredClone(gatingSystemForm))
  activeGating.value.push(String(mold_info.value.gating_systems.length - 1))
}

function removeGating(gIdx: number) {
  mold_info.value.gating_systems.splice(gIdx, 1)
  activeGating.value = activeGating.value
    .map(s => Number(s) > gIdx ? String(Number(s) - 1) : s)
    .filter(s => Number(s) !== gIdx)
}

function addCavity(gIdx: number) {
  mold_info.value.gating_systems[gIdx].cavities.push(structuredClone(cavityForm))
  // activeCavityMap 更新...
}

function removeCavity(gIdx: number, cIdx: number) {
  mold_info.value.gating_systems[gIdx].cavities.splice(cIdx, 1)
  // activeCavityMap 更新...
}

function addGate(gIdx: number, cIdx: number) {
  mold_info.value.gating_systems[gIdx].cavities[cIdx].gates.push(structuredClone(gateForm))
  // activeGateMap 更新...
}

function removeGate(gIdx: number, cIdx: number, gtIdx: number) {
  mold_info.value.gating_systems[gIdx].cavities[cIdx].gates.splice(gtIdx, 1)
  // activeGateMap 更新...
}
```

---

## 九、实施步骤（按依赖顺序）

### Step 1：扩展 form-types.ts
**预计改动**：[`src/utils/form-types.ts`](../../src/utils/form-types.ts)
- 添加 type 联合：`integer | radio | autocomplete`
- 完善 FormItem 字段（添加 `query` for autocomplete）
- **不抽** BaseFormItem 组件（见 5.2 说明）

### Step 2：重写 CoolingSystemForm.vue
**预计改动**：[`src/views/mold/components/CoolingSystemForm.vue`](../../src/views/mold/components/CoolingSystemForm.vue)（重写）
- Composition API + `<script setup>`
- FormItem[] 数组
- el-row + el-col + v-else-if 链（参考 5.2 模板示例）
- ElPlus 2.x 语法（`#suffix` 替代 `slot="suffix"`）

### Step 3：重写 EjectionSystemForm.vue
**预计改动**：[`src/views/mold/components/EjectionSystemForm.vue`](../../src/views/mold/components/EjectionSystemForm.vue)（重写）
- 同上 + radio 类型（has_pre_ejection）

### Step 4：重写 GatingSystemForm.vue（重头戏）
**预计改动**：[`src/views/mold/components/GatingSystemForm.vue`](../../src/views/mold/components/GatingSystemForm.vue)（重写 16.9KB）
- 3 层 el-collapse 嵌套
- 条件显示（runner_type / gate_shape）
- 添加/删除操作
- 字段数组按条件分组

### Step 5：重写 MoldForm.vue
**预计改动**：[`src/views/mold/pages/MoldForm.vue`](../../src/views/mold/pages/MoldForm.vue)（重写 21KB）
- 完整对齐 [FORM_CODING_STANDARD.md](FORM_CODING_STANDARD.md)
- custom-form / custom-form__section / form-actions
- 集成 GatingSystemForm / CoolingSystemForm / EjectionSystemForm

### Step 6：MoldList.vue 验证
- 检查是否需要对齐 BaseSearchForm + BaseTable
- 如果搜索/列表是好的，只改 style 即可

### Step 7：验证 4 种弹性填写场景
| 场景 | Mold | GatingSystem | Cavity | Gate | 验证方式 |
|------|------|--------------|--------|------|---------|
| 极简 | 1 | 1 | 1 | 1 | 手动测试 |
| 简单 | 1 | 1 | 1 (count=N) | 1 | 手动测试 |
| 中等 | 1 | 1 | N | N | 手动测试 |
| 复杂 | 1 | N | N | N | 手动测试 |

---

## 十、风险与缓解

| 风险 | 缓解 |
|------|------|
| 嵌套折叠状态不持久化 | 暂时用内存 state，未来加 localStorage |
| "删除"按钮误触 | 用二次确认（el-popconfirm）|
| Cavity/Gate 内 el-form 嵌套 | 每个嵌套层用独立 el-form + el-form-item |
| 默认展开第一个 | 避免用户进入页面看到全部折叠 |
| 4 种弹性填写场景的 UI 一致性 | 同一套组件，按数据驱动渲染 |
| 用户已习惯 tabs | 提供"展开全部"快捷按钮（如有需要）|
| v-else-if 链较长（5-7 个分支）| 简单且可读，不抽 BaseFormItem |

---

## 十一、验证 checklist

### 类型检查
- [ ] `npm run type-check` 通过

### UI 视觉
- [ ] 嵌套层级清晰（标题 + 标签 + 折叠按钮）
- [ ] 添加/删除按钮位置合理
- [ ] 删除有二次确认
- [ ] 条件显示（runner_type / gate_shape）正确

### 数据正确性
- [ ] 极简场景：1/1/1 默认值正确
- [ ] 添加/删除后数据同步
- [ ] 折叠状态不影响数据
- [ ] 提交后端接收正确

### 与规范对齐
- [ ] 顶部无 h2 标题
- [ ] form-actions 在 el-form 外
- [ ] form-actions v-if="loaded"
- [ ] custom-form / custom-form__section 类名
- [ ] padding-bottom: 96px
- [ ] Composition API + `<script setup>`

---

## 十二、相关参考

- [mold-migration-design-summary-2026-09-03.md](../../docs/mold-migration-design-summary-2026-09-03.md) — mold 迁移设计哲学
- [FORM_CODING_STANDARD.md](FORM_CODING_STANDARD.md) — 表单编码规范
- [FORM_LAYOUT_DECISION_GUIDE.md](FORM_LAYOUT_DECISION_GUIDE.md) — 布局决策
- [src/utils/form-types.ts](../../src/utils/form-types.ts) — FormItem / FormCard 类型
- [src/utils/form-layout.ts](../../src/utils/form-layout.ts) — groupIntoRows 算法
- [src/views/project/form.vue](../../src/views/project/form.vue) — 范例

---

## 十三、文档维护

- 本文档随实施进展更新（每完成一个 Step 更新状态）
- 任何字段定义变更同步更新第六节
- 验证完成后更新第八节的实施步骤标记为 ✅
