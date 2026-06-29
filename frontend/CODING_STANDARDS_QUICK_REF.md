# 前端代码规范速查表

> **快速参考指南** - 详细规范请查看 [CODING_STANDARDS.md](./CODING_STANDARDS.md)

---

## 📝 命名规范（最重要！）

### Data/Computed 变量 → 下划线命名

```javascript
// ✅ 正确
data() {
  return {
    mold_no: null,
    query_params: {},
    search_items: [],
    is_expanded: false
  }
}

computed: {
  visible_items() { ... },
  has_advanced_items() { ... }
}
```

### Methods 方法 → 驼峰命名

```javascript
// ✅ 正确
methods: {
  handleSearch() { ... },
  handleReset() { ... },
  toggleExpand() { ... },
  loadDeviceData() { ... }
}
```

### 组件文件名 → PascalCase

```
✅ MoldSearchForm.vue
✅ BaseSearchForm.vue
❌ mold-search-form.vue
```

### 常量 → 全大写下划线

```javascript
const MAX_RETRY_COUNT = 3
export const MOLD_CATEGORY_OPTIONS = [...]
```

---

## 🏗️ 组件结构顺序

```vue
<template>...</template>

<script>
// 1. imports
import BaseSearchForm from '@/components/BaseSearchForm.vue'

export default {
  // 2. name
  name: "MoldSearchForm",
  
  // 3. components
  components: { BaseSearchForm },
  
  // 4. props
  props: { ... },
  
  // 5. data
  data() { return { ... } },
  
  // 6. computed
  computed: { ... },
  
  // 7. watch
  watch: { ... },
  
  // 8. lifecycle
  created() { ... },
  mounted() { ... },
  
  // 9. methods
  methods: { ... }
}
</script>

<style lang="scss" scoped>...</style>
```

---

## 🎨 样式规范

### 必须使用 scoped

```vue
<style lang="scss" scoped>
.card { padding: 16px; }
</style>
```

### 优先使用 CSS 变量

```scss
.card {
  padding: var(--spacing-4);
  border-radius: var(--radius-md);
}
```

### 全局样式在 index.scss

```scss
// src/styles/index.scss
.search-container {
  margin-bottom: var(--spacing-4);
  padding: var(--spacing-4) var(--spacing-5);
}
```

---

## 🔌 API 调用

### 定义 API

```javascript
// src/api/mold.js
import request from './index'

export function getMoldList(params) {
  return request({
    url: '/api/molds/',
    method: 'get',
    params
  })
}
```

### 调用 API

```javascript
async fetchData() {
  try {
    const { results, count } = await getMoldList(this.query_params)
    this.table_data = results
    this.total_count = count
  } catch (error) {
    this.$message.error('获取数据失败')
  }
}
```

---

## 💡 最佳实践

### 1. 避免模板中复杂逻辑

```vue
<!-- ❌ 错误 -->
<div v-if="items.filter(i => i.level === 'basic').length > 0">

<!-- ✅ 正确 -->
<div v-if="has_basic_items">

<script>
computed: {
  has_basic_items() {
    return this.items.filter(i => i.level === 'basic').length > 0
  }
}
</script>
```

### 2. 使用 async/await

```javascript
// ✅ 正确
async fetchData() {
  const data = await apiCall()
}

// ❌ 错误
fetchData() {
  apiCall().then(data => ...)
}
```

### 3. 及时清理资源

```javascript
beforeDestroy() {
  if (this.timer) {
    clearInterval(this.timer)
  }
}
```

### 4. 使用解构赋值

```javascript
const { results, count } = await getMoldList(params)
```

### 5. 常量集中管理

```javascript
// src/constants/mold-const.js
export const MOLD_CATEGORY_OPTIONS = [...]

// 组件中使用
import { MOLD_CATEGORY_OPTIONS } from "@/constants/mold-const"
```

---

## ⚠️ 常见错误

| 错误 | 正确做法 |
|------|---------|
| `queryParams`（驼峰） | `query_params`（下划线） |
| `handle_search()`（下划线） | `handleSearch()`（驼峰） |
| 模板中写复杂逻辑 | 使用 computed |
| 直接修改 props | 通过 $emit 通知父组件 |
| 忘记清理定时器 | beforeDestroy 中清理 |
| 样式不加 scoped | 始终使用 scoped |

---

## 📚 完整文档

详细规范请查看：
- [CODING_STANDARDS.md](./CODING_STANDARDS.md) - 完整代码规范
- [README_BaseSearchForm.md](./src/components/_devRefs/README_BaseSearchForm.md) - BaseSearchForm 使用指南

---

**记住核心原则**：
- 📌 **Data 用下划线**（与后端一致）
- 📌 **Methods 用驼峰**（JS 惯例）
- 📌 **组件要拆分**（单一职责）
- 📌 **样式要 scoped**（避免污染）
