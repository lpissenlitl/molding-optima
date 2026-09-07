# Element Plus 表单编码标准

> **目的**：基于 `project/form.vue` 的完整落地实践，给出"大表单（数据录入）"的标准代码骨架与必遵守的代码规范。
> **创建时间**：2026-09-07
> **适用范围**：molding-optima 前端所有 el-form 大表单页（新建 / 编辑 / 详情）
> **配套文档**：[FORM_LAYOUT_DECISION_GUIDE.md](FORM_LAYOUT_DECISION_GUIDE.md)（讲"为什么选 el-row+el-col"）
> **范例**：[`src/views/project/form.vue`](../../src/views/project/form.vue)

---

## 一、标准代码骨架（必须严格遵循）

### 1.1 完整骨架

```vue
<!--
  XxxForm - 业务名 + Form（新建 + 编辑共用）

  路由：
    - /xxx/new           新建模式
    - /xxx/:id/edit      编辑模式（自动加载详情）

  设计要点：
    - 单文件处理两种模式（避免 create / edit 两份重复代码）
    - 通过 useRoute().params.id 判断模式
    - 表单字段、验证规则、提交逻辑只写一次
-->
<template>
  <div class="xxx-form">
    <!-- ① 顶部 page-header：只放"返回"按钮，不放 h2 标题 -->
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
    </div>

    <!-- ② 表单内容：class="custom-form" 触发全局样式 -->
    <el-form
      v-if="loaded"
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      label-position="right"
      v-loading="loading"
      class="custom-form"
    >
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

            <!-- 常规字段：input / select / date / textarea / number -->
            <el-form-item
              v-else-if="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input v-if="item.type === 'input' || item.type === 'number'" ... />
              <el-select v-else-if="item.type === 'select'" ...>...</el-select>
              <el-date-picker v-else-if="item.type === 'date'" ... />
              <el-input v-else-if="item.type === 'textarea'" type="textarea" :rows="item.rows || 4" ... />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-form>

    <!-- ③ 加载占位（与 el-form 互斥） -->
    <div v-else v-loading="true" class="loading-placeholder"></div>

    <!--
      ④ 操作按钮：必须放在 el-form 外部、xxx-form 内部
      三个原因：
        1. DOM 结构：el-form 只管内容，form-actions 只管操作（关注点分离）
        2. CSS 加载：避免 Vite dev 模式 CSS 异步注入导致 button 在 card 下方闪现
        3. v-if="loaded"：与 el-form 显隐同步，避免加载时按钮抢先出现
    -->
    <div v-if="loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ is_edit ? '保存' : '创建' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
// 标准 import（按以下顺序）
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { xxxMethod } from '@/api'
import { groupIntoRows } from '@/utils/form-layout'
import type { FormItem, FormCard } from '@/utils/form-types'

// 路由（核心：通过 useRoute 区分新建/编辑模式）
const route = useRoute()
const router = useRouter()

const is_edit = computed(() => !!route.params.id)
const xxx_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

// 字段定义：flat items 数组 + 自动分行
const formCards: FormCard[] = [
  {
    title: '基本信息',
    items: [
      { label: '编号', prop: 'xxx_code', type: 'input' },
      // ... span 默认 6（4 列布局）
    ],
  },
  // ...更多 card
]

const cardRows = computed(() =>
  formCards.map((card) => ({
    title: card.title,
    rows: groupIntoRows(card.items, { columns: 4 }),
  }))
)

// 表单状态
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const loaded = ref(false)  // 编辑模式：详情是否加载完成

function getDefaultForm(): Record<string, any> { ... }
const form = ref(getDefaultForm())
const rules = computed<FormRules>(() => { ... })

// 生命周期
onMounted(async () => {
  if (is_edit.value && xxx_id.value !== null) {
    await loadDetail()
  } else {
    loaded.value = true
  }
})

async function loadDetail() { ... }
function goBack() { router.push('/xxx/list') }
async function handleSubmit() { ... }
</script>

<style scoped lang="scss">
/* 仅放页面特有样式，全局样式已抽取到 custom-form.scss */
.xxx-form {
  /* padding-bottom: 96px 必须保留，给 fixed form-actions 留位 */
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

### 1.2 骨架的"四段式"结构

| 段 | 作用 | 必含元素 |
|----|------|---------|
| **① 顶部** | 退出路径 | `page-header` + 返回列表按钮（**不加 h2**）|
| **② 表单** | 数据录入 | `el-form.custom-form` + `el-card.custom-form__section` |
| **③ 占位** | 加载状态 | `v-loading` 占位（与 el-form 互斥）|
| **④ 操作栏** | 提交 / 取消 | `div.form-actions`（**在 el-form 外部**）|

---

## 二、强制规范（违反需在 PR 描述中说明）

### 2.1 命名空间（BEM）

| 元素 | 类名 |
|------|------|
| `el-form` 根 | `custom-form` |
| `el-card` 卡片 | `custom-form__section` |
| card header 标题 | `custom-form__title` |
| `el-divider` 分组 | `custom-form__divider` |
| 底部操作栏 | `form-actions`（独立类，不嵌入 .custom-form）|

**禁止**：直接使用 `.form` / `.form-section` / `.section-title` / `.form-divider` 等未命名空间类（会污染全局）。

### 2.2 page-header 不放 h2

```vue
<!-- ❌ 禁止 -->
<div class="page-header">
  <el-button>返回列表</el-button>
  <h2>{{ is_edit ? '编辑项目' : '新建项目' }}</h2>
</div>

<!-- ✅ 正确 -->
<div class="page-header">
  <el-button>返回列表</el-button>
</div>
```

**原因**：页面标识由 navbar 面包屑 + URL 路径承担，h2 是信息冗余。
**参考**：[`polymer/PolymerForm.vue`](../../src/views/polymer/pages/PolymerForm.vue) / `admin/RoleCreate.vue` 等已有页面均无 h2 标题。

### 2.3 form-actions 必须在 el-form 外部

```vue
<!-- ❌ 禁止 -->
<el-form>
  <el-card>...</el-card>
  <div class="form-actions">...</div>
</el-form>

<!-- ✅ 正确 -->
<el-form>
  <el-card>...</el-card>
</el-form>
<div v-if="loaded" class="form-actions">...</div>
```

**三个原因**：
1. **关注点分离**：el-form 只管内容，form-actions 只管操作
2. **避免 FOUC**：Vite dev 模式 CSS 异步注入时，button 在 el-form 内部会按 DOM 流渲染在 card 下方
3. **v-if="loaded"**：与 el-form 显隐同步，加载时不出现空按钮

### 2.4 form-actions 必须 v-if="loaded"

```vue
<!-- ❌ 禁止 -->
<div class="form-actions">...</div>  <!-- 加载时显示空按钮 -->

<!-- ✅ 正确 -->
<div v-if="loaded" class="form-actions">...</div>
```

**注**：功能上 handleSubmit 有 `if (!formRef.value) return` 防御，不加也不会出错——**v-if 是 UX 增强，不是 bug 修复**。

### 2.5 全局 SCSS 禁止使用 `:deep()`

```scss
/* ❌ 禁止：:deep() 仅在 <style scoped> 中有效 */
.form-actions :deep(.el-button) { min-width: 100px; }

/* ✅ 正确：全局 SCSS 直接用后代选择器 */
.form-actions .el-button { min-width: 100px; }
```

**原因**：`:deep()` 是 Vue 3 scoped CSS 的编译期语法糖，全局 SCSS 不在 Vue 编译流程里，`:deep()` 写出来就是字面字符串，浏览器忽略整个选择器。

**抽取到全局的检查清单**：
```bash
# 抽取前自检（必查）
grep -E ':deep|>>>::v-deep' <被抽取的文件>
```

### 2.6 form 容器 padding-bottom 必须保留

```scss
/* form 容器必须预留底部空间（96px） */
.xxx-form {
  padding: 16px 16px 96px;  /* ← 96px 不能省 */
}
```

**原因**：form-actions 是 `position: fixed; bottom: 0`，不占布局空间；form 必须预留 96px 防 textarea / date-picker 被遮挡。
**计算**：96px = 操作栏高度 (48px) + 顶部呼吸间隔 (32px) + 16px 保险。

### 2.7 模板用 flat items 数组 + 自动分行

```typescript
// ✅ 正确：flat items，自动分行
const formCards: FormCard[] = [
  {
    title: '项目信息',
    items: [
      { label: '编号', prop: 'code', type: 'input' },
      { label: '名称', prop: 'name', type: 'input' },  // span 默认 6
      { label: '备注', prop: 'remarks', type: 'textarea', span: 24 },  // 整行
    ],
  },
]
const cardRows = computed(() => formCards.map((card) => ({
  rows: groupIntoRows(card.items, { columns: 4 }),
})))

// ❌ 禁止：手写 el-row / el-col（散落在 template 里）
```

**类型定义**：[`src/utils/form-types.ts`](../../src/utils/form-types.ts) 的 `FormItem` / `FormCard`。
**分行算法**：[`src/utils/form-layout.ts`](../../src/utils/form-layout.ts) 的 `groupIntoRows`（按 span 总和=24 自动换行）。

### 2.8 span 档位（24 栅格，4 列布局默认）

| 字段类型 | span | 典型示例 |
|---------|------|--------|
| 短字段（4 列布局默认）| **6** | 编号、状态、日期、来源 |
| 长字段（跨 2 列）| **12** | 项目名称、客户全称 |
| 较长字段（跨 2-3 列）| **16** | 较长名称、详细地址 |
| 整行字段 | **24** | textarea、备注、分组标题 divider |

`groupIntoRows(items, { columns: 4 })` 默认 span=6；`columns: 3` 默认 span=8。

---

## 三、style 块的边界（什么放 scoped，什么放全局）

| 样式内容 | 位置 | 原因 |
|---------|------|------|
| `.xxx-form` 容器布局 | **scoped** | 页面特有（如 max-width、padding）|
| `.page-header` 边距 | **scoped** | 页面特有 |
| `.loading-placeholder` 高度 | **scoped** | 页面特有 |
| `.search-container` / `.search-actions` | **全局**（`custom-form.scss`）| 7 个搜索表单共用 |
| `.form-actions` 固定底部 | **全局**（`custom-form.scss`）| 所有大表单共用 |
| `.custom-form` / `.custom-form__*` | **全局**（`custom-form.scss`）| 所有大表单共用 |
| `@media` 响应式 Grid 接管 | **全局**（`custom-form.scss`）| 所有 el-form 自动继承 |

**判断标准**：是否被 2+ 个页面用？是 → 全局；否 → scoped。

---

## 四、关键工具与文件

| 文件 | 作用 |
|------|------|
| [`src/utils/form-types.ts`](../../src/utils/form-types.ts) | `FormItem` / `FormCard` 接口 |
| [`src/utils/form-layout.ts`](../../src/utils/form-layout.ts) | `groupIntoRows` 自动分行算法 |
| [`src/utils/form-helper.ts`](../../src/utils/form-helper.ts) | 表单辅助函数 |
| [`src/styles/utilities/custom-form.scss`](../../src/styles/utilities/custom-form.scss) | form 全局公共样式（4 个模块：搜索 / 响应式 / 操作栏 / 大表单）|
| [`src/styles/utilities/custom-tag.scss`](../../src/styles/utilities/custom-tag.scss) | 自定义标签样式 |
| [`src/views/project/form.vue`](../../src/views/project/form.vue) | 迁移范例（已落地）|

---

## 五、项目现状对照

| 文件 | 状态 | 备注 |
|------|------|------|
| `views/project/form.vue` | ✅ **已迁移**，作为标准范例 | 完整落地所有规范 |
| `views/mold/pages/MoldForm.vue` | ⚠️ 待迁移 | 嵌套结构（`Mold → GatingSystem → Cavity`），将考验规范灵活度 |
| `views/polymer/pages/PolymerForm.vue` | ⚠️ 待迁移 | 旧 `:inline="true"` 写法 |
| `views/equipment/pages/InjectionMachineForm.vue` | ⚠️ 待迁移 | 旧 `:inline="true"` 写法 |
| `views/admin/pages/RoleCreate.vue` 等 | ✅ 无 page-header h2 | 与本规范一致 |
| `components/BaseSearchForm.vue` | ✅ 搜索表单规范 | 7 个 SearchForm 都基于它 |

---

## 六、迁移 checklist

每迁移一个表单，按以下 checklist 验证：

### 模板结构
- [ ] `<el-form class="custom-form">`（不是 `.form`）
- [ ] `<el-card class="custom-form__section">`（不是 `.form-section`）
- [ ] card header 用 `<span class="custom-form__title">`（不是 `.section-title`）
- [ ] divider 用 `class="custom-form__divider"`
- [ ] form-actions 在 **el-form 外部**
- [ ] form-actions 加 `v-if="loaded"`
- [ ] page-header **没有 h2** 标题

### 样式
- [ ] form 容器 `padding: 16px 16px 96px`（96px 不能省）
- [ ] form 容器 `box-sizing: border-box`
- [ ] scoped 块只放页面特有样式
- [ ] 重复样式已抽取到 `custom-form.scss`

### 代码
- [ ] 使用 `FormItem` / `FormCard` 类型（不要在 template 里写新结构）
- [ ] 使用 `groupIntoRows` 自动分行（不要手写 el-row / el-col）
- [ ] `is_edit` / `xxx_id` 通过 `useRoute().params` 派生
- [ ] `loaded` / `loading` / `submitting` 三个状态都正确维护

### 验证
- [ ] 类型检查通过（`npm run type-check`）
- [ ] dev 模式无 FOUC 闪烁（button 不在 card 下方闪现）
- [ ] 浏览器实际打开 / 关闭 / 提交流程正常

---

## 七、相关参考

- [FORM_LAYOUT_DECISION_GUIDE.md](FORM_LAYOUT_DECISION_GUIDE.md) — 布局方案选择（为什么用 el-row+el-col）
- [SEARCH_FORM_MIGRATION_PLAN.md](SEARCH_FORM_MIGRATION_PLAN.md) — 搜索表单统一改造
- [`src/utils/form-types.ts`](../../src/utils/form-types.ts) — flat items 类型
- [`src/utils/form-layout.ts`](../../src/utils/form-layout.ts) — 自动分行算法
- [`src/views/project/form.vue`](../../src/views/project/form.vue) — 落地范例
- [mold-migration-design-summary-2026-09-03.md](../../docs/mold-migration-design-summary-2026-09-03.md) — mold 迁移背景

---

## 八、文档维护

- **本规范变更需要 PR 评审**——所有遵循本规范的表单都需同步调整
- **新增强制规范**时：在第二节加条目，并在第六节 checklist 加对应项
- **范例代码更新**时：同步更新 [`src/views/project/form.vue`](../../src/views/project/form.vue) 作为标杆
