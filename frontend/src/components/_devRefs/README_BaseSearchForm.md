# BaseSearchForm 使用指南

> **组件位置**: `src/components/BaseSearchForm.vue`  
> **创建时间**: 2026-06-10  
> **用途**: 统一的搜索表单基础组件

---

## 📖 快速开始

### 基础用法

```vue
<template>
  <BaseSearchForm
    :query="query_params"
    :items="search_items"
    @search="handleSearch"
    @reset="handleReset"
  />
</template>

<script>
import BaseSearchForm from '@/components/BaseSearchForm.vue'

export default {
  components: { BaseSearchForm },
  data() {
    return {
      // ✅ Data 变量使用下划线命名（与后端一致）
      query_params: {
        mold_no: null,
        mold_name: null,
        category: null
      },
      search_items: [
        { 
          label: "模具编号", 
          prop: "mold_no", 
          type: "autocomplete",
          query: { table: "mold", column: "mold_no" }
        },
        { 
          label: "模具名称", 
          prop: "mold_name", 
          type: "autocomplete",
          query: { table: "mold", column: "mold_name" }
        },
        { 
          label: "模具类别", 
          prop: "category", 
          type: "select",
          options: [
            { label: "注塑模", value: "injection" },
            { label: "压铸模", value: "diecasting" }
          ]
        }
      ]
    }
  },
  methods: {
    // ✅ Methods 方法名使用驼峰命名（JS 惯例）
    handleSearch(query) {
      console.log('搜索条件:', query)
      // 执行搜索逻辑
    },
    handleReset(query) {
      console.log('重置后的条件:', query)
      // 执行重置后的逻辑
    }
  }
}
</script>
```

---

## 🔧 API 文档

### Props

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `query` | Object | ✅ 是 | - | 查询对象（双向绑定） |
| `items` | Array | ✅ 是 | `[]` | 筛选项配置数组 |
| `expandable` | Boolean | ❌ 否 | `false` | 是否支持展开/收起 |

### Events

| 事件名 | 参数 | 说明 |
|--------|------|------|
| `search` | `(query)` | 点击搜索按钮时触发 |
| `reset` | `(query)` | 点击重置按钮时触发 |
| `expand-change` | `(isExpanded)` | 展开/收起状态变化时触发 |

### Items 配置项结构

每个筛选项的配置对象包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `label` | String | ✅ 是 | 字段标签 |
| `prop` | String | ✅ 是 | 字段名（对应 query 对象的键） |
| `type` | String | ✅ 是 | 类型：`autocomplete` / `select` / `input` / `date` / `slot` |
| `level` | String | ❌ 否 | 级别：`basic`（默认）/ `advanced` |
| `options` | Array | ⚠️ select 必填 | 下拉选项数组 `[{ label, value }]` |
| `query` | Object | ⚠️ autocomplete 必填 | 自动完成查询配置 `{ table, column }` |
| `slot_name` | String | ⚠️ slot 必填 | 插槽名称 |

---

## 💡 使用示例

### 示例1：基础搜索表单

```javascript
data() {
  return {
    queryParams: {
      device_no: null,
      brand: null,
      status: null
    },
    searchItems: [
      { 
        label: "设备编号", 
        prop: "device_no", 
        type: "autocomplete",
        query: { table: "machine", column: "device_no" }
      },
      { 
        label: "品牌", 
        prop: "brand", 
        type: "autocomplete",
        query: { table: "machine", column: "brand" }
      },
      { 
        label: "状态", 
        prop: "status", 
        type: "select",
        options: [
          { label: "运行中", value: "running" },
          { label: "停机", value: "stopped" }
        ]
      }
    ]
  }
}
```

---

### 示例2：带展开/收起功能

```vue
<BaseSearchForm
  :query="queryParams"
  :items="searchItems"
  :expandable="true"
  @search="handleSearch"
/>
```

```javascript
data() {
  return {
    queryParams: { /* ... */ },
    searchItems: [
      // 基础项（默认显示）
      { label: "模具编号", prop: "mold_no", type: "autocomplete", level: "basic", ... },
      { label: "模具名称", prop: "mold_name", type: "autocomplete", level: "basic", ... },
      
      // 高级项（展开后显示）
      { label: "模具结构", prop: "structure", type: "select", level: "advanced", ... },
      { label: "模腔布局", prop: "cavity_layout", type: "autocomplete", level: "advanced", ... },
    ]
  }
}
```

---

### 示例3：使用自定义插槽

对于特殊表单项（如日期范围、级联选择器等），可以使用插槽：

```vue
<BaseSearchForm
  :query="queryParams"
  :items="searchItems"
  @search="handleSearch"
>
  <!-- 自定义日期范围 -->
  <template #date-range="{ query }">
    <el-form-item label="日期范围">
      <el-date-picker
        v-model="query.dateRange"
        type="daterange"
        range-separator="-"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
      />
    </el-form-item>
  </template>
</BaseSearchForm>
```

```javascript
data() {
  return {
    queryParams: {
      mold_no: null,
      dateRange: null
    },
    searchItems: [
      { label: "模具编号", prop: "mold_no", type: "autocomplete", ... },
      { slot_name: "date-range" },  // 占位符，会在该位置渲染插槽
      { label: "状态", prop: "status", type: "select", ... }
    ]
  }
}
```

---

### 示例4：混合使用多种类型

```javascript
searchItems: [
  // 自动完成
  { 
    label: "模具编号", 
    prop: "mold_no", 
    type: "autocomplete",
    query: { table: "mold", column: "mold_no" }
  },
  
  // 下拉选择
  { 
    label: "模具类别", 
    prop: "category", 
    type: "select",
    options: moldCategoryOptions
  },
  
  // 普通输入
  { 
    label: "备注关键词", 
    prop: "remark_keyword", 
    type: "input"
  },
  
  // 日期选择
  { 
    label: "创建日期", 
    prop: "create_date", 
    type: "date"
  },
  
  // 自定义插槽
  { slot_name: "custom-field" }
]
```

---

## 🔄 迁移指南

### 从 MoldSearchForm 迁移到 BaseSearchForm

#### 改造前

```vue
<template>
  <div class="search-container">
    <el-form class="search-form" :inline="true" :model="query" size="mini">
      <el-form-item label="模具编号">
        <el-autocomplete v-model.trim="query.mold_no" ... />
      </el-form-item>
      <!-- ... 更多表单项 -->
      <el-form-item class="search-actions">
        <el-button @click="queryListData(false)">搜索</el-button>
        <el-button @click="queryListData(true)">重置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: { mold_no: null, ... },
      allItems: [ /* ... */ ]
    }
  },
  methods: {
    queryListData(reset) {
      if (reset) { /* 重置逻辑 */ }
      this.$emit("search")
    }
  }
}
</script>
```

#### 改造后

```vue
<template>
  <BaseSearchForm
    :query="queryParams"
    :items="allItems"
    @search="handleSearch"
    @reset="handleReset"
  />
</template>

<script>
import BaseSearchForm from '@/components/BaseSearchForm.vue'

export default {
  components: { BaseSearchForm },
  props: {
    queryDetail: { type: Object, default: () => ({}) }
  },
  data() {
    return {
      queryParams: this.queryDetail,
      allItems: [ /* ... */ ]
    }
  },
  methods: {
    handleSearch() {
      this.$emit("search")
    },
    handleReset() {
      this.$emit("reset")
    }
  }
}
</script>
```

**关键变化**：
1. ✅ 模板简化：从 70+ 行减少到 10 行以内
2. ✅ 逻辑简化：无需手动编写 reset 逻辑
3. ✅ 样式统一：自动应用全局 `.search-container` 样式

---

## ⚠️ 注意事项

### 1. Query 对象的双向绑定

**重要**：BaseSearchForm 直接修改 `query` prop 的属性值，这是有意为之的设计。

**原因**：
- `query` 是一个对象，Vue 允许修改对象的属性（保持响应式）
- 直接使用 `v-model` 比使用 `$emit('update:query')` 更简洁高效
- 避免了不必要的对象拷贝和事件传递

**实现方式**：
```vue
<!-- 组件内部直接使用 v-model -->
<el-input v-model="query[item.prop]" />

<!-- 清空时使用 $set 确保响应式 -->
this.$set(this.query, prop, null)
```

**ESLint 配置**：
组件顶部已添加 `<!-- eslint-disable vue/no-mutating-props -->` 注释，禁用该规则。

**父组件调用**：
```vue
<!-- ✅ 正确：直接传递对象 -->
<BaseSearchForm
  :query="query_params"
  @search="handleSearch"
/>

<!-- 无需使用 .sync 或 v-model:query -->
```

### 2. 清空操作的处理

组件内部已经处理了清空逻辑，会自动将对应字段设置为 `null`。

### 3. 展开/收起功能

只有当 `expandable=true` 且存在 `level: "advanced"` 的表单项时，才会显示展开/收起按钮。

### 4. 插槽的位置控制

通过 `slot_name` 占位符可以精确控制自定义表单项的位置：

```javascript
searchItems: [
  { label: "字段1", prop: "field1", type: "input" },
  { slot_name: "custom-1" },  // 自定义字段会在这里渲染
  { label: "字段2", prop: "field2", type: "input" },
]
```

---

## 🎨 样式说明

搜索表单的样式已在全局 `src/styles/index.scss` 中定义，包括：

- `.search-container`：容器样式（渐变背景、边框、悬停效果）
- `.search-form`：表单布局（Flexbox、间距控制）
- `.search-actions`：按钮区域（右对齐、分隔线）

**无需在组件中添加额外样式**。

---

## 📚 相关文档

- [搜索表单优化方案](./SEARCH_FORM_OPTIMIZATION.md)
- [样式系统使用指南](./STYLE_USAGE_GUIDE.md)

---

**最后更新**: 2026-06-10  
**维护者**: MoldingX Team
