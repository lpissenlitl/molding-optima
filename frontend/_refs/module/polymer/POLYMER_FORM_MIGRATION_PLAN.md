# PolymerForm 迁移实施计划

> **状态**：📋 计划阶段（决策已确认，未开始实施）
> **创建时间**：2026-09-08
> **关键决策**：不扩展 FormFieldRenderer，手写 v-else-if 链（遵循 [MOLD_FORM_MIGRATION_PLAN.md § 5.2](MOLD_FORM_MIGRATION_PLAN.md#L118)）
> **设计参考**：[MOLD_FORM_MIGRATION_PLAN.md](MOLD_FORM_MIGRATION_PLAN.md)（已完成范例）
> **配套规范**：[FORM_CODING_STANDARD.md](FORM_CODING_STANDARD.md) / [FORM_LAYOUT_DECISION_GUIDE.md](FORM_LAYOUT_DECISION_GUIDE.md)
> **改造对象**：[`src/views/polymer/pages/PolymerForm.vue`](../../src/views/polymer/pages/PolymerForm.vue)（615 行，Vue 2 选项式 API）

---

## 一、当前 PolymerForm 与标准的差距

### 1.1 现状问题

| 问题 | 位置 | 影响 |
|------|------|------|
| **选项式 API**（Vue 2 风格）| 全文 | 不符合 [CODING_STANDARDS.md](../../CODING_STANDARDS.md) Composition API 规范 |
| **`:inline="true"`** 布局 | `<el-form :inline="true">` (L10) | 长短字段混排会有 label 宽度共享问题 |
| **6 段重复 v-else-if 链** | L22-50 / L73-96 / L110-117 / L139-160 / L184-190 / L214-220 | 约 100 行重复代码 |
| **`slot="suffix"` / `slot="header"`**（Vue 2 语法）| L13 / L27 / L79 / L101 等 | Element Plus 2.x 已用 `#suffix` / `#header`，需升级 |
| **`createValidateAndFocus` helper** | L291 / L553 | 不是 Element Plus 标准 validate() |
| **`viewContext` props 模式** | L295-305 | 与 ProjectForm / MoldForm 的 `useRoute` 单一入口不一致 |
| **4 种模式混在一起**（新增/编辑/复制/导入 Excel）| L513-533 | 入口判断复杂，未拆分 |
| **未暴露 formRef / defineExpose** | 全文 | 无法被父组件统一验证 |
| **未用 `FormItem` / `FormCard` 类型** | 全文 | 字段定义没有 TypeScript 类型约束 |
| **`allow_create: true` 字段控制不一致** | L312 / L319 等 | 部分硬编码 select 允许创建，部分不允许 |

### 1.2 当前文件结构（6 个 el-card）

```
PolymerForm.vue（615 行）
├── 基本信息（10 字段）                  ← basic_form_items
├── 推荐工艺参数（27 字段 + 5 divider）   ← process_form_items
├── PVT 属性（13 字段）                  ← pvt_form_items
├── 流变属性（17 字段 + 6 divider）       ← rheology_form_items
├── 机械属性（7 字段 + 2 divider）        ← mechanical_form_items
└── 收缩属性（6 字段 + 3 divider）        ← shrinkage_form_items
```

**总计 ~80 字段，16 个 divider**，数据模型比 MoldForm 简单（无嵌套），但单字段数量更多。

---

## 二、三个核心决策（已确认）

| 决策 | 选择 | 原因 |
|------|------|------|
| API 风格 | **Composition API + `<script setup>`** | 与 ProjectForm / MoldForm 保持一致 |
| 布局方案 | **el-form + el-row + el-col + groupIntoRows** | 字段多且密集（80+ 字段），需要精确栅格控制 |
| 模式入口 | **`useRoute` 单一入口**（移除 viewContext props）| 与 ProjectForm / MoldForm RESTful 风格一致；如需 dialog 调用，可保留兼容 |
| 字段渲染 | **手写 v-else-if 链**（不引入 FormFieldRenderer）| 遵循 [MOLD_FORM_MIGRATION_PLAN.md § 5.2](MOLD_FORM_MIGRATION_PLAN.md#L118) 决策；PolymerForm 仅 1 处复用，抽象成本大于收益 |

---

## 三、数据模型摘要

```
Polymer（单层，~80 字段）
├── 基本信息（10 字段）                  ← polymer_info.*
├── 推荐工艺参数（27 字段）               ← polymer_info.*
├── PVT 属性（13 字段）                  ← polymer_info.pvt.* ⚠️ 嵌套
├── 流变属性（17 字段）                   ← polymer_info.rheology.* ⚠️ 嵌套
├── 机械属性（7 字段）                    ← polymer_info.mechanical.* ⚠️ 嵌套
└── 收缩属性（6 字段）                    ← polymer_info.shrinkage.* ⚠️ 嵌套
```

**重要发现**：4 类属性（PVT / 流变 / 机械 / 收缩）是嵌套在 `polymer_info.*` 下的子对象。这与 MoldForm 的“嵌套子组件”不同 —— PolymerForm 是**单层嵌套**（子对象直接挂载在 polymer_info 上）。

**改造策略**：
- 基本信息 + 推荐工艺参数：使用 `getCardModel('基本信息')` 返回 `polymer_info`
- PVT / 流变 / 机械 / 收缩 4 段：使用 `getCardModel('PVT 属性')` 等返回对应的嵌套对象
- v-else-if 链通过 `v-model="getCardModel(title)[item.prop!]"` 访问各 section 的 model

---

## 四、目标架构

```
src/views/polymer/
├── pages/
│   └── PolymerForm.vue（重写，~450 行）
└── components/
    ├── PolymerSearchForm.vue（⚠️ P1 批次待迁移）
    └── FillerSearchForm.vue（保持现状）

src/utils/
└── form-helper.ts（新增 querySuggestions helper）
```

### 4.1 目标 UI 结构

```
┌──────────────────────────────────┐
│  [← 返回列表]                     │ page-header（不加 h2）
├──────────────────────────────────┤
│ ▼ 基本信息                        │ custom-form__section #1
│   10 字段（4 列布局）              │
├──────────────────────────────────┤
│ ▼ 推荐工艺参数                    │ custom-form__section #2
│   5 个分组 divider + 27 字段       │
├──────────────────────────────────┤
│ ▼ PVT 属性                        │ custom-form__section #3
│   13 字段（4 列布局）              │
├──────────────────────────────────┤
│ ▼ 流变属性                        │ custom-form__section #4
│   6 个分组 divider + 17 字段       │
├──────────────────────────────────┤
│ ▼ 机械属性                        │ custom-form__section #5
│   2 个分组 divider + 7 字段        │
├──────────────────────────────────┤
│ ▼ 收缩属性                        │ custom-form__section #6
│   4 个分组 divider + 6 字段        │
├──────────────────────────────────┤
│ [取消] [保存]                      │ form-actions（在 el-form 外）
└──────────────────────────────────┘
```

---

## 五、字段渲染策略（遵循 plan 5.2 决策）

### 5.1 决策：不扩展 FormFieldRenderer，直接写 v-else-if 链

**依据**：[MOLD_FORM_MIGRATION_PLAN.md § 5.2](MOLD_FORM_MIGRATION_PLAN.md#L118) — “**不抽** BaseFormItem / RenderFormItem 公共组件”。

| 理由 | 说明 |
|------|------|
| **复用场景不足** | PolymerForm 仅 1 处复用（单文件），不像 MoldForm 有 MoldForm + Cooling + Ejection 三处跨组件复用场景 |
| **抽象成本大于收益** | 为 PolymerForm 独有的 `autocomplete` 扩展 FormFieldRenderer 会让抽象组件越来越胖（“半年后恶化”） |
| **类型差异大** | mold 要 7 种、polymer 要 5 种、equipment 要 6 种——难统一 |
| **样式定制难** | 业务方调样式时需穿透抽象 |

> **FormFieldRenderer 保留**：作为 mold 模块的专用抽象组件（不删除），不推广到其他 form。

### 5.2 直接写 v-else-if 链的模板示例

`PolymerForm.vue` 模板里写 5 个 v-else-if 链（input / number / select / autocomplete / divider），覆盖 PolymerForm 所需的全部字段类型：

```vue
<!-- PolymerForm.vue -->
<el-form-item v-for="item in card.items" :key="item.prop" :label="item.label" :prop="item.prop">
  <!-- divider：分组标题 -->
  <el-divider
    v-if="item.type === 'divider'"
    content-position="left"
    class="custom-form__divider"
  >
    {{ item.label }}
  </el-divider>

  <!-- input：纯文本 -->
  <el-input
    v-else-if="item.type === 'input'"
    v-model.trim="getCardModel(card.title)[item.prop!]"
    :placeholder="getPlaceholder(item)"
    :disabled="getDisabled(item)"
  >
    <template #suffix v-if="item.unit">{{ item.unit }}</template>
  </el-input>

  <!-- number / integer：v-number 限制小数位 -->
  <el-input
    v-else-if="item.type === 'number'"
    v-model.trim="getCardModel(card.title)[item.prop!]"
    v-number="getPrecision(item)"
    :placeholder="getPlaceholder(item)"
    :disabled="getDisabled(item)"
  >
    <template #suffix v-if="item.unit">{{ item.unit }}</template>
  </el-input>

  <!-- select：单选下拉 -->
  <el-select
    v-else-if="item.type === 'select'"
    v-model="getCardModel(card.title)[item.prop!]"
    :placeholder="getPlaceholder(item)"
    :disabled="getDisabled(item)"
    clearable
    filterable
    :allow-create="item.allowCreate !== false"
  >
    <el-option
      v-for="(opt, oIdx) in item.options"
      :key="oIdx"
      :label="opt.label"
      :value="opt.value"
    />
  </el-select>

  <!-- autocomplete：自动补全（PolymerForm 独有） -->
  <el-autocomplete
    v-else-if="item.type === 'autocomplete'"
    v-model="getCardModel(card.title)[item.prop!]"
    :placeholder="getPlaceholder(item)"
    :disabled="getDisabled(item)"
    clearable
    :debounce="0"
    :fetch-suggestions="querySuggestions(item.query)"
  />
</el-form-item>
```

### 5.3 `querySuggestions` helper（新增于 `form-helper.ts`）

```typescript
// src/utils/form-helper.ts
export function querySuggestions(query: any) {
  const instance = getCurrentInstance()
  // string 形式（如 { table, column }）走全局 mixin
  if (typeof query === 'object' && query !== null) {
    const fn = (instance?.proxy as any)?.$querySuggestions
    return fn ? fn(query) : () => {}
  }
  // function 形式直接调用
  return query
}
```

> **使用提示**：在 `<script setup>` 中，`getCurrentInstance()` 返回的 instance 仅用于访问全局 mixin，不保留引用。

### 5.4 v-else-if 链长度的可接受范围

5 个 v-else-if 分支（input / number / select / autocomplete / divider）不长，可读性高。**如果未来 PolymerForm 需要添加新类型（如 `radio`），只需加一个 v-else-if，不需改公共组件**。

### 5.5 PolymerForm 中被 FormFieldRenderer 覆盖能力的检查清单

虽然不引入 FormFieldRenderer，以下能力需要手写支持：

| 能力 | 处理 |
|------|------|
| `placeholder` 自动生成 | `getPlaceholder(item)` helper（已存在） |
| `disabled` 控制 | `getDisabled(item)` helper（已存在） |
| `precision` 小数位 | `getPrecision(item)` helper（已存在） |
| `allowCreate` select | `:allow-create="item.allowCreate !== false"` |
| `required` 视觉 | `:required="item.required"`（el-form-item 原生支持） |
| `rules` 验证 | el-form-item `:rules="item.rules"` |

> 这些 helper 都能复用，不需要为 PolymerForm 新增任何抽象。

---

## 六、字段定义分组（每段一组 FormItem[]）

### 6.1 6 段 FormItem 数组

```typescript
// 1. 基本信息（10 字段，4 列布局）
const basicItems: FormItem[] = [
  // 硬编码分类 select 显式 allowCreate: false
  { label: '塑料简称', prop: 'abbreviation', type: 'select', options: polymerAbbreviationOptions, allowCreate: false, required: true },
  { label: '牌号', prop: 'grade', type: 'input', required: true },
  { label: '塑料类别', prop: 'category', type: 'select', options: polymerCategoryOptions, allowCreate: false },
  { label: '塑料厂商', prop: 'manufacturer', type: 'autocomplete', query: { table: 'polymer', column: 'manufacturer' } },
  { label: '系列', prop: 'series', type: 'input' },
  { label: '数据来源', prop: 'data_source', type: 'select', options: polymerDataSourceOptions, allowCreate: true },
  { label: '内部编号', prop: 'internal_id', type: 'input' },
  { label: '等级代码', prop: 'level_code', type: 'input' },
  { label: '供应商代码', prop: 'vendor_code', type: 'input' },
]

// 2. 推荐工艺参数（5 divider + 27 字段）
const processItems: FormItem[] = [
  { label: '熔体与固体密度', type: 'divider' },
  { label: '熔体密度', prop: 'melt_density', type: 'number', unit: 'g/cm³', precision: 4 },
  { label: '固体密度', prop: 'solid_density', type: 'number', unit: 'g/cm³', precision: 4 },
  { label: '熔体温度', type: 'divider' },
  { label: '最小熔体温度', prop: 'min_melt_temp', type: 'number', unit: '℃' },
  // ...
]

// 3. PVT 属性（13 字段，flat，4 列布局）
const pvtItems: FormItem[] = [
  { label: 'Tait b5', prop: 'tait_b5', type: 'number', unit: 'K', precision: 8 },
  // ...
]

// 4. 流变属性（6 divider + 17 字段）
const rheologyItems: FormItem[] = [
  { label: '粘度模型', type: 'divider' },
  { label: '粘度模型', prop: 'model_type', type: 'select', options: [{ label: 'Cross-WLF', value: 'cross_wlf' }], allowCreate: false },
  { label: 'Cross-WLF 参数', type: 'divider' },
  // ...
]

// 5. 机械属性（2 divider + 7 字段）
const mechanicalItems: FormItem[] = [
  { label: '弹性性能', type: 'divider' },
  { label: '弹性模量 E1', prop: 'elastic_modulus_1', type: 'number', unit: 'MPa', precision: 4 },
  // ...
]

// 6. 收缩属性（4 divider + 6 字段）
const shrinkageItems: FormItem[] = [
  { label: '平均收缩率', type: 'divider' },
  { label: '平行收缩率', prop: 'ave_h_shrink', type: 'number', unit: '%', precision: 4 },
  // ...
]
```

### 6.2 自动分行 computed

```typescript
const basicRows = computed(() => groupIntoRows(basicItems, { columns: 4 }))
const processRows = computed(() => groupIntoRows(processItems, { columns: 4 }))
const pvtRows = computed(() => groupIntoRows(pvtItems, { columns: 4 }))
const rheologyRows = computed(() => groupIntoRows(rheologyItems, { columns: 4 }))
const mechanicalRows = computed(() => groupIntoRows(mechanicalItems, { columns: 4 }))
const shrinkageRows = computed(() => groupIntoRows(shrinkageItems, { columns: 4 }))
```

---

## 七、路由模式迁移（viewContext → useRoute）

### 7.1 当前模式（L295-305）

```javascript
props: {
  viewContext: {
    type: Object,
    default: () => ({
      id: null, is_dialog: false, mode: null, excel_data: null
    })
  }
}
```

4 种入口：
1. **新增**：无 id
2. **编辑**：通过 `viewContext.id` 或 `$route.query.id`
3. **复制**：编辑后清空 `id` 和 `grade`
4. **导入 Excel**：`mode='import'` + `excel_data`

### 7.2 目标模式（与 ProjectForm 一致）

```typescript
// 路由：
//   /polymer/new           新建模式
//   /polymer/:id/edit      编辑模式
//   /polymer/:id/copy      复制模式（清空 id 和 grade）

const route = useRoute()
const is_edit = computed(() => !!route.params.id && !is_copy.value)
const is_copy = computed(() => route.name === 'PolymerCopy' || route.query.copy === 'true')

// excel 导入走单独的 dialog，不在主表单中处理
```

**兼容方案**（如果必须保留 dialog 调用）：
- 保留 `viewContext` props 作为可选输入
- 新增 `useRoute` 作为默认入口
- viewContext.id 优先级 > route.params.id

> **建议**：直接删除 viewContext 模式，与 ProjectForm / MoldForm 完全统一。dialog 调用场景改为"打开新路由页面"。

---

## 八、验证规则迁移

### 8.1 当前 rules（L433-479）

```javascript
rules: {
  abbreviation: [{ required: true, message: '材料名称缩写为空!' }],
  grade: [{ required: true, message: '材料牌号为空!' }],
  // ... 大量注释掉的必填项
}
```

### 8.2 目标 rules

保持当前 2 个必填（abbreviation + grade）。注释中的必填项（max_melt_temp 等）按业务需求后续补充，与 MoldForm 保持一致的"先实现架构，按需补充"策略。

```typescript
const rules: FormRules = {
  abbreviation: [{ required: true, message: '材料名称缩写为空!', trigger: 'change' }],
  grade: [{ required: true, message: '材料牌号为空!', trigger: 'blur' }],
}
```

> **注意**：原文件没写 `trigger`，Element Plus 默认 trigger 是 `'blur'`（input）或 `'change'`（select）。显式声明更清晰。

---

## 九、模板骨架（目标）

```vue
<template>
  <div class="polymer-form">
    <!-- ① 顶部 page-header -->
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
    </div>

    <!-- ② 表单内容 -->
    <el-form
      v-if="loaded"
      ref="formRef"
      :model="polymer_info"
      :rules="rules"
      v-loading="loading"
      class="custom-form"
      label-width="120px"
    >
      <!-- 6 个 el-card section（v-for 渲染 formCards） -->
      <el-card
        v-for="(card, cIdx) in formCards"
        :key="`card_${cIdx}`"
        shadow="never"
        class="custom-form__section"
      >
        <template #header>
          <span class="custom-form__title">{{ card.title }}</span>
        </template>

        <el-row
          v-for="(row, rIdx) in cardRows[cIdx].rows"
          :key="`row_${cIdx}_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`field_${cIdx}_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <!-- divider：分组标题 -->
            <el-divider
              v-if="item.type === 'divider'"
              content-position="left"
              class="custom-form__divider"
            >
              {{ item.label }}
            </el-divider>

            <!-- 常规字段：手写 v-else-if 链（不引入 FormFieldRenderer） -->
            <el-form-item
              v-else
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'input'"
                v-model.trim="getCardModel(card.title)[item.prop!]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>

              <el-input
                v-else-if="item.type === 'number'"
                v-model.trim="getCardModel(card.title)[item.prop!]"
                v-number="getPrecision(item)"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>

              <el-select
                v-else-if="item.type === 'select'"
                v-model="getCardModel(card.title)[item.prop!]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
                filterable
                :allow-create="item.allowCreate !== false"
              >
                <el-option
                  v-for="(opt, oIdx) in item.options"
                  :key="oIdx"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>

              <el-autocomplete
                v-else-if="item.type === 'autocomplete'"
                v-model="getCardModel(card.title)[item.prop!]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
                :debounce="0"
                :fetch-suggestions="querySuggestions(item.query)"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-form>

    <!-- ③ 加载占位 -->
    <div v-else v-loading="true" class="loading-placeholder"></div>

    <!-- ④ 操作按钮（fixed bottom） -->
    <div v-if="loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        :disabled="!hasPermission('update_polymer')"
        @click="handleSave"
      >
        {{ is_edit ? '保存' : (is_copy ? '保存为新条目' : '创建') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { polymerMethod } from '@/api'
import { polymerInfoForm } from '@/constants/polymer-const'
import { groupIntoRows } from '@/utils/form-layout'
import { getPlaceholder, getDisabled, getPrecision, querySuggestions } from '@/utils/form-helper'
import { hasPermission } from '@/utils/permission'
import type { FormCard } from '@/utils/form-types'

// 路由模式
const route = useRoute()
const router = useRouter()

const is_edit = computed(() => !!route.params.id && route.name !== 'PolymerCopy')
const is_copy = computed(() => route.name === 'PolymerCopy')
const polymer_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

// 状态
const polymer_info = ref<any>(structuredClone(polymerInfoForm))
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const loaded = ref(false)

// 字段定义（6 段）
// ... basicItems / processItems / pvtItems / rheologyItems / mechanicalItems / shrinkageItems

const formCards: FormCard[] = [
  { title: '基本信息', items: basicItems },
  { title: '推荐工艺参数', items: processItems },
  { title: 'PVT 属性', items: pvtItems },
  { title: '流变属性', items: rheologyItems },
  { title: '机械属性', items: mechanicalItems },
  { title: '收缩属性', items: shrinkageItems },
]

const cardRows = computed(() =>
  formCards.map((card) => ({
    title: card.title,
    rows: groupIntoRows(card.items, { columns: 4 }),
  }))
)

// 不同 section 绑定不同 model
function getCardModel(title: string) {
  switch (title) {
    case 'PVT 属性': return polymer_info.value.pvt
    case '流变属性': return polymer_info.value.rheology
    case '机械属性': return polymer_info.value.mechanical
    case '收缩属性': return polymer_info.value.shrinkage
    default: return polymer_info.value
  }
}

// 验证规则
const rules: FormRules = {
  abbreviation: [{ required: true, message: '材料名称缩写为空!', trigger: 'change' }],
  grade: [{ required: true, message: '材料牌号为空!', trigger: 'blur' }],
}

// 操作
function goBack() {
  router.push('/polymer/list')
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请检查必填项')
    return
  }

  submitting.value = true
  try {
    let res: any
    if (polymer_id.value !== null && !is_copy.value) {
      res = await polymerMethod.edit(polymer_info.value, polymer_id.value)
    } else {
      // 新增 / 复制模式：清空 id 和 grade
      polymer_info.value.id = null
      polymer_info.value.grade = null
      res = await polymerMethod.add(polymer_info.value)
    }

    if (res.status === 0) {
      ElMessage.success(is_edit ? '材料信息编辑成功！' : '材料信息新增成功！')
      goBack()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (err: any) {
    ElMessage.error(err?.message || '提交异常')
  } finally {
    submitting.value = false
  }
}

// 生命周期
onMounted(async () => {
  if (polymer_id.value !== null) {
    await loadDetail(polymer_id.value)
  } else {
    loaded.value = true
  }
})

async function loadDetail(id: number) {
  loading.value = true
  try {
    const res: any = await polymerMethod.getDetail(id)
    if (res.status === 0) {
      polymer_info.value = res.data
      if (is_copy.value) {
        polymer_info.value.id = null
        polymer_info.value.grade = null
      }
      loaded.value = true
    } else {
      ElMessage.error(res.msg || '未读取到相关材料信息')
      router.push('/polymer/list')
    }
  } catch (err: any) {
    ElMessage.error(err?.message || '加载材料详情异常')
    router.push('/polymer/list')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.polymer-form {
  padding: 16px 16px 96px;
  max-width: 1400px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 16px;
}

.loading-placeholder {
  height: 400px;
}
</style>
```

---

## 十、实施步骤（按依赖顺序）

### Step 1：新增 `querySuggestions` helper（前置）
- 预计改动：[`src/utils/form-helper.ts`](../../src/utils/form-helper.ts)
- 添加 `querySuggestions(query: any)` 函数（见 § 5.3）
- 通过 `getCurrentInstance().proxy.$querySuggestions` 访问全局 mixin
- TypeScript 类型检查通过

### Step 2：迁移 PolymerSearchForm.vue（P1 批次）
- 不在本次计划范围内，但需要单独处理
- 参考 BaseSearchForm 规范

### Step 3：重写 PolymerForm.vue ✅ 主任务
- 预计改动：[`src/views/polymer/pages/PolymerForm.vue`](../../src/views/polymer/pages/PolymerForm.vue)（重写 615 行 → ~450 行）
- Composition API + `<script setup>`
- 6 个 FormItem[] 数组 + formCards
- formCardRow 自动分行
- **手写 5 个 v-else-if 链**（input / number / select / autocomplete / divider），不引入 FormFieldRenderer
- custom-form / custom-form__section / form-actions 命名空间
- useRoute 单一入口（移除 viewContext props）
- rules: abbreviation + grade 必填

### Step 4：路由配置
- 预计改动：router/index.ts
- 新增 `/polymer/new`、`/polymer/:id/edit`、`/polymer/:id/copy` 三个路由
- 移除 / 兼容原 viewContext 调用方式

### Step 5：父组件调用方迁移
- 检查 PolymerList.vue / FillerList.vue 是否用 viewContext 模式打开 PolymerForm
- 改为路由跳转

### Step 6：验证
- TypeScript 编译零错误
- 3 种模式（新建 / 编辑 / 复制）功能正常（Excel 导入不在本次范围）
- 与 MoldForm 视觉一致

---

## 十一、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| viewContext 模式被父组件依赖，删除后破坏调用方 | 中 | 高 | 先扫描调用方，按需提供兼容层 |
| `querySuggestions` helper 访问不到全局 mixin | 中 | 中 | 通过 `getCurrentInstance().proxy.$querySuggestions` 访问，在 Step 1 验证 |
| 嵌套 model（pvt / rheology / mechanical / shrinkage）的 rules 无法触发 | 低 | 中 | 这些 section 的字段都是 number 类型，不强制必填，影响小 |
| Excel 导入功能（`mode='import'` + `excel_data`）迁移复杂 | 中 | 中 | 单独保留为 dialog 模式，不在主表单中处理 |
| 6 段字段合计 80+，渲染性能可能下降 | 低 | 低 | Vue 3 渲染性能足够 |
| PolymerForm.vue 一次性重写风险 | 中 | 中 | 沿用 MoldForm 模板骨架，逐段迁移而非整体重写 |
| v-else-if 链增长到 8+ 个时难以维护 | 低 | 中 | plan 5.2 决策说明：5-7 个可接受，超出时再考虑抽象 |

---

## 十二、验证 checklist

### 模板结构
- [ ] `<el-form class="custom-form">`（不是 `.form`）
- [ ] `<el-card class="custom-form__section">`
- [ ] card header 用 `<span class="custom-form__title">`
- [ ] divider 用 `class="custom-form__divider"`
- [ ] form-actions 在 **el-form 外部**
- [ ] form-actions 加 `v-if="loaded"`
- [ ] page-header **没有 h2** 标题

### 样式
- [ ] form 容器 `padding: 16px 16px 96px`
- [ ] form 容器 `box-sizing: border-box`
- [ ] scoped 块只放页面特有样式

### 代码
- [ ] 使用 `FormItem` / `FormCard` 类型
- [ ] 使用 `groupIntoRows` 自动分行
- [ ] `is_edit` / `is_copy` / `polymer_id` 通过 `useRoute()` 派生
- [ ] `loaded` / `loading` / `submitting` 三个状态都正确维护
- [ ] Composition API + `<script setup>`

### 数据
- [ ] 6 个 FormItem[] 数组定义完整
- [ ] 硬编码分类 select 显式 `allowCreate: false`
- [ ] 必填字段（abbreviation + grade）有 rules
- [ ] el-form-item 原生支持 `required` 视觉（`:required="item.required"`）
- [ ] `querySuggestions` helper 能正常访问 `$querySuggestions` mixin

### 验证
- [ ] `npm run type-check` 通过
- [ ] 4 种模式（新建 / 编辑 / 复制）功能正常
- [ ] 父组件调用方已迁移到路由模式
- [ ] 与 MoldForm / ProjectForm 视觉一致

---

## 十三、相关参考

- [MOLD_FORM_MIGRATION_PLAN.md](MOLD_FORM_MIGRATION_PLAN.md) —— mold 模块迁移范例（已完成）
- [FORM_CODING_STANDARD.md](FORM_CODING_STANDARD.md) —— 大表单编码规范
- [FORM_LAYOUT_DECISION_GUIDE.md](FORM_LAYOUT_DECISION_GUIDE.md) —— 布局决策
- [`src/utils/form-types.ts`](../../src/utils/form-types.ts) —— FormItem / FormCard 类型
- [`src/utils/form-layout.ts`](../../src/utils/form-layout.ts) —— groupIntoRows 算法
- [`src/utils/form-helper.ts`](../../src/utils/form-helper.ts) —— getPlaceholder / getDisabled / getPrecision / **querySuggestions** helper
- [`src/views/mold/components/FormFieldRenderer.vue`](../../src/views/mold/components/FormFieldRenderer.vue) —— mold 模块专用抽象组件（**仅 mold 使用**，不推广）
- [`src/views/project/pages/ProjectForm.vue`](../../src/views/project/pages/ProjectForm.vue) —— 路由模式范例
- [`src/views/mold/pages/MoldForm.vue`](../../src/views/mold/pages/MoldForm.vue) —— 嵌套表单范例

---

## 十四、文档维护

- 本文档随实施进展更新（每完成一个 Step 更新状态）
- 任何字段定义变更同步更新第六节
- 验证完成后更新第十节实施步骤标记为 ✅
