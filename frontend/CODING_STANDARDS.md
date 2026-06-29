# MoldingX 前端代码规范

> **版本**: 1.0.0  
> **更新时间**: 2026-06-10  
> **适用范围**: molding-expert-web 项目

---

## 📋 目录

- [1. 命名规范](#1-命名规范)
- [2. 组件开发规范](#2-组件开发规范)
- [3. Vue 组件结构规范](#3-vue-组件结构规范)
- [4. 样式规范](#4-样式规范)
- [5. API 调用规范](#5-api-调用规范)
- [6. 注释规范](#6-注释规范)
- [7. 文件组织规范](#7-文件组织规范)
- [8. 最佳实践](#8-最佳实践)

---

## 1. 命名规范

### 1.1 变量命名

#### Data/Computed 变量：使用下划线命名法（snake_case）

**原则**：与后端 Django 字段保持一致，便于数据映射。

```javascript
// ✅ 正确
data() {
  return {
    mold_no: null,              // 模具编号
    machine_model: null,        // 机器型号
    setting_process: null,      // 设定工艺
    query_params: {},           // 查询参数
    search_items: [],           // 搜索项配置
    is_expanded: false          // 展开状态
  }
}

computed: {
  visible_items() {             // 可见项
    return this.items.filter(...)
  },
  has_advanced_items() {        // 是否有高级项
    return this.items.some(...)
  }
}

// ❌ 错误
data() {
  return {
    moldNo: null,               // 驼峰命名
    machineModel: null,
    queryParams: {},
    searchItems: []
  }
}
```

#### Methods 方法名：使用驼峰命名法（camelCase）

**原则**：符合 JavaScript/Vue 惯例，提高可读性。

```javascript
// ✅ 正确
methods: {
  handleSearch() { ... },           // 处理搜索
  handleReset() { ... },            // 处理重置
  toggleExpand() { ... },           // 切换展开
  loadDeviceData() { ... },         // 加载设备数据
  updateInjectionTable() { ... },   // 更新注射表格
  formatDateTime() { ... }          // 格式化日期时间
}

// ❌ 错误
methods: {
  handle_search() { ... },          // 下划线命名
  handle_reset() { ... },
  toggle_expand() { ... }
}
```

### 1.2 组件命名

#### 组件文件名：PascalCase（大驼峰）

```
✅ 正确：
- MoldSearchForm.vue
- BaseSearchForm.vue
- InjectionMachineList.vue

❌ 错误：
- mold-search-form.vue
- moldSearchForm.vue
```

#### 组件 name 属性：与文件名一致

```javascript
export default {
  name: "MoldSearchForm",  // ✅ 与文件名一致
  // ...
}
```

### 1.3 Props 和 Events 命名

#### Props：简洁通用，避免风格冲突

```javascript
// ✅ 正确：简洁通用
props: {
  query: { type: Object, required: true },
  items: { type: Array, default: () => [] },
  expandable: { type: Boolean, default: false }
}

// ⚠️ 避免：刻意迎合某种风格
props: {
  query_params: { ... },     // 不必要
  search_items: { ... },     // 不必要
  is_expandable: { ... }     // 不必要
}
```

#### Events：kebab-case（短横线）

```vue
<!-- ✅ 正确 -->
<BaseSearchForm
  @search="handleSearch"
  @reset="handleReset"
  @expand-change="handleExpandChange"
/>

<!-- ❌ 错误 -->
<BaseSearchForm
  @onSearch="handleSearch"
  @on-reset="handleReset"
/>
```

### 1.4 常量命名

#### 常量：UPPER_SNAKE_CASE（全大写下划线）

```javascript
// ✅ 正确
const MAX_RETRY_COUNT = 3
const API_BASE_URL = 'http://127.0.0.1:8200'
const DEFAULT_PAGE_SIZE = 20

// 导出常量对象
export const MOLD_CATEGORY_OPTIONS = [
  { label: "注塑模", value: "injection" },
  { label: "压铸模", value: "diecasting" }
]

// ❌ 错误
const maxRetryCount = 3
const apiBaseUrl = 'http://127.0.0.1:8200'
```

---

## 2. 组件开发规范

### 2.1 组件拆分原则

#### 单一职责原则

每个组件只负责一个功能模块：

```
✅ 推荐结构：
MoldList.vue              # 模具列表页面
├── MoldSearchForm.vue    # 搜索表单
├── MoldTable.vue         # 数据表格
└── MoldDetailDialog.vue  # 详情弹窗

❌ 避免：
MoldList.vue              # 包含所有逻辑（500+ 行）
```

#### 复用性原则

可复用的组件提取到 `src/components/`：

```
src/components/
├── BaseSearchForm.vue       # 基础搜索表单
├── UploadFile.vue           # 文件上传
├── ColumnFilter.vue         # 列过滤
└── DialogWrapper.vue        # 弹窗包装器
```

### 2.2 组件通信规范

#### Props 向下传递

```vue
<!-- 父组件 -->
<MoldSearchForm
  :query-detail="queryParams"
  @search="fetchData"
/>

<!-- 子组件 -->
<script>
export default {
  props: {
    queryDetail: {
      type: Object,
      default: () => ({})
    }
  }
}
</script>
```

#### Events 向上传递

```javascript
// 子组件
methods: {
  handleSearch() {
    this.$emit("search", this.query_params)
  }
}

// 父组件
<MoldSearchForm @search="handleSearch" />
```

#### 避免直接修改 Props

```javascript
// ❌ 错误：直接修改 prop
methods: {
  handleInput(prop, value) {
    this.query[prop] = value  // 违反单向数据流
  }
}

// ✅ 正确：通过事件通知父组件
methods: {
  handleInput(prop, value) {
    this.$emit('update:query', { ...this.query, [prop]: value })
  }
}
```

### 2.3 组件生命周期

#### 常用钩子函数顺序

```javascript
export default {
  // 1. 组件创建
  created() {
    // 初始化数据，调用 API
  },
  
  // 2. DOM 挂载
  mounted() {
    // DOM 操作，初始化第三方库
  },
  
  // 3. 数据更新
  updated() {
    // DOM 更新后的操作
  },
  
  // 4. 组件销毁
  beforeDestroy() {
    // 清理定时器、事件监听器等
  }
}
```

---

## 3. Vue 组件结构规范

### 3.1 标准组件结构

```vue
<template>
  <!-- 模板内容 -->
</template>

<script>
// 1. 导入依赖
import BaseSearchForm from '@/components/BaseSearchForm.vue'
import { moldCategoryOptions } from "@/constants/mold-const"

export default {
  // 2. 组件名称
  name: "MoldSearchForm",
  
  // 3. 注册子组件
  components: { BaseSearchForm },
  
  // 4. Props 定义
  props: {
    queryDetail: {
      type: Object,
      default: () => ({})
    }
  },
  
  // 5. Data 函数
  data() {
    return {
      query_params: this.queryDetail,
      search_items: [...]
    }
  },
  
  // 6. Computed 属性
  computed: {
    visible_items() {
      return this.search_items.filter(...)
    }
  },
  
  // 7. Watch 监听
  watch: {
    query_params: {
      handler(newVal) {
        // 处理变化
      },
      deep: true
    }
  },
  
  // 8. 生命周期钩子
  created() {
    this.initData()
  },
  
  // 9. Methods 方法
  methods: {
    initData() {
      // 初始化逻辑
    },
    handleSearch() {
      this.$emit("search")
    },
    handleReset() {
      this.$emit("reset")
    }
  }
}
</script>

<style lang="scss" scoped>
/* 样式 */
</style>
```

### 3.2 代码顺序说明

| 顺序 | 部分 | 说明 |
|------|------|------|
| 1 | imports | 导入依赖 |
| 2 | name | 组件名称 |
| 3 | components | 子组件注册 |
| 4 | props | Props 定义 |
| 5 | data | 响应式数据 |
| 6 | computed | 计算属性 |
| 7 | watch | 监听器 |
| 8 | lifecycle | 生命周期钩子 |
| 9 | methods | 方法 |

---

## 4. 样式规范

### 4.1 样式语言

**统一使用 SCSS**：

```vue
<style lang="scss" scoped>
.search-container {
  padding: var(--spacing-4);
  
  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
}
</style>
```

### 4.2 Scoped 样式

**必须使用 `scoped`**，避免样式污染：

```vue
<!-- ✅ 正确 -->
<style lang="scss" scoped>
.mold-list {
  padding: 20px;
}
</style>

<!-- ❌ 错误 -->
<style lang="scss">
.mold-list {
  padding: 20px;  /* 可能影响其他组件 */
}
</style>
```

### 4.3 全局样式

全局样式定义在 `src/styles/index.scss`：

```scss
// src/styles/index.scss

// 搜索容器
.search-container {
  margin-bottom: var(--spacing-4);
  padding: var(--spacing-4) var(--spacing-5);
  background: linear-gradient(to bottom, #fafbfc, #ffffff);
  border: 1px solid var(--color-border-extra-light);
  border-radius: var(--radius-md);
}

// 搜索表单
.search-form {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  
  &.el-form--inline {
    .el-form-item {
      margin-bottom: 8px;
      margin-right: 16px;
      
      &:last-child {
        margin-right: 0;
      }
    }
  }
}
```

### 4.4 CSS 变量使用

优先使用 CSS 变量，保持主题一致性：

```scss
// ✅ 正确
.card {
  padding: var(--spacing-4);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
}

// ❌ 错误
.card {
  padding: 16px;
  border-radius: 4px;
  color: #333;
}
```

### 4.5 Element UI 样式覆盖

在全局 SCSS 中覆盖 Element UI 样式，不使用 `:deep()`：

```scss
// ✅ 正确：全局样式文件
.search-form {
  .el-form-item {
    margin-bottom: 8px;
  }
}

// ❌ 错误：scoped 样式中使用 :deep()
<style scoped>
.search-form {
  :deep(.el-form-item) {
    margin-bottom: 8px;
  }
}
</style>
```

---

## 5. API 调用规范

### 5.1 API 请求封装

使用 axios 实例：

```javascript
// src/api/index.js
import axios from 'axios'

const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API,
  timeout: 30000
})

// 请求拦截器
service.interceptors.request.use(config => {
  // 添加 token
  const token = localStorage.getItem('token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
service.interceptors.response.use(
  response => response.data,
  error => {
    // 统一错误处理
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default service
```

### 5.2 API 调用方式

```javascript
// src/api/mold.js
import request from './index'

// 获取模具列表
export function getMoldList(params) {
  return request({
    url: '/api/molds/',
    method: 'get',
    params
  })
}

// 创建模具
export function createMold(data) {
  return request({
    url: '/api/molds/',
    method: 'post',
    data
  })
}
```

### 5.3 组件中调用 API

```javascript
methods: {
  async fetchData() {
    try {
      const response = await getMoldList(this.query_params)
      this.table_data = response.results
      this.total_count = response.count
    } catch (error) {
      this.$message.error('获取数据失败')
    }
  }
}
```

---

## 6. 注释规范

### 6.1 组件注释

```javascript
/**
 * 模具搜索表单组件
 * @description 提供模具列表页面的搜索功能
 * @author MoldingX Team
 * @version 1.0.0
 */
export default {
  name: "MoldSearchForm",
  // ...
}
```

### 6.2 方法注释

```javascript
methods: {
  /**
   * 查询列表数据
   * @param {boolean} reset - 是否重置查询条件
   */
  async queryListData(reset = false) {
    if (reset) {
      // 重置逻辑
    }
    this.$emit("search")
  },
  
  /**
   * 切换展开/收起状态
   */
  toggleExpand() {
    this.is_expanded = !this.is_expanded
  }
}
```

### 6.3 复杂逻辑注释

```javascript
computed: {
  /**
   * 可见的筛选项
   * - 基础项始终显示
   * - 高级项仅在展开时显示
   */
  visible_items() {
    if (!this.expandable) {
      return this.search_items
    }
    
    return this.search_items.filter(item => {
      return item.level !== 'advanced' || this.is_expanded
    })
  }
}
```

---

## 7. 文件组织规范

### 7.1 目录结构

```
src/
├── api/                    # API 接口
│   ├── index.js           # axios 实例
│   ├── mold.js            # 模具相关接口
│   └── machine.js         # 设备相关接口
├── components/            # 公共组件
│   ├── BaseSearchForm.vue
│   ├── UploadFile.vue
│   └── README_BaseSearchForm.md
├── constants/             # 常量定义
│   ├── mold-const.js
│   ├── machine-const.js
│   └── project-const.js
├── views/                 # 页面组件
│   ├── moldManage/
│   │   ├── MoldList.vue
│   │   └── components/
│   │       ├── MoldSearchForm.vue
│   │       └── MoldDetailDialog.vue
│   └── machineManage/
├── styles/                # 样式文件
│   ├── index.scss         # 全局样式
│   ├── variables/         # CSS 变量
│   └── devRefs/           # 样式开发文档
├── utils/                 # 工具函数
├── router/                # 路由配置
└── store/                 # Vuex 状态管理
```

### 7.2 组件存放位置

| 类型 | 位置 | 示例 |
|------|------|------|
| **公共组件** | `src/components/` | BaseSearchForm.vue |
| **页面组件** | `src/views/{module}/` | MoldList.vue |
| **页面子组件** | `src/views/{module}/components/` | MoldSearchForm.vue |

---

## 8. 最佳实践

### 8.1 避免在模板中写复杂逻辑

```vue
<!-- ❌ 错误：模板中复杂逻辑 -->
<template>
  <div v-if="items.filter(item => item.level === 'basic').length > 0">
    ...
  </div>
</template>

<!-- ✅ 正确：使用 computed -->
<template>
  <div v-if="has_basic_items">
    ...
  </div>
</template>

<script>
computed: {
  has_basic_items() {
    return this.items.filter(item => item.level === 'basic').length > 0
  }
}
</script>
```

### 8.2 使用可选链操作符

```javascript
// ✅ 正确
const moldName = this.mold_info?.mold_name || '未知'

// ❌ 错误
const moldName = this.mold_info && this.mold_info.mold_name ? this.mold_info.mold_name : '未知'
```

### 8.3 异步操作使用 async/await

```javascript
// ✅ 正确
async fetchData() {
  try {
    const response = await getMoldList(this.query_params)
    this.table_data = response.results
  } catch (error) {
    this.$message.error('获取数据失败')
  }
}

// ❌ 错误
fetchData() {
  getMoldList(this.query_params).then(response => {
    this.table_data = response.results
  }).catch(error => {
    this.$message.error('获取数据失败')
  })
}
```

### 8.4 及时清理资源

```javascript
export default {
  data() {
    return {
      timer: null
    }
  },
  
  mounted() {
    this.timer = setInterval(this.refreshData, 5000)
  },
  
  beforeDestroy() {
    // ✅ 清理定时器
    if (this.timer) {
      clearInterval(this.timer)
    }
  }
}
```

### 8.5 使用解构赋值

```javascript
// ✅ 正确
const { results, count } = await getMoldList(params)
this.table_data = results
this.total_count = count

// ❌ 错误
const response = await getMoldList(params)
this.table_data = response.results
this.total_count = response.count
```

### 8.6 常量集中管理

```javascript
// src/constants/mold-const.js
export const MOLD_CATEGORY_OPTIONS = [
  { label: "注塑模", value: "injection" },
  { label: "压铸模", value: "diecasting" }
]

export const MOLD_STRUCTURE_OPTIONS = [
  { label: "两板模", value: "two_plate" },
  { label: "三板模", value: "three_plate" }
]

// 组件中使用
import { MOLD_CATEGORY_OPTIONS } from "@/constants/mold-const"

data() {
  return {
    category_options: MOLD_CATEGORY_OPTIONS
  }
}
```

---

## 📚 相关文档

- [BaseSearchForm 使用指南](./src/components/_devRefs/README_BaseSearchForm.md)
- [搜索表单优化方案](./src/styles/devRefs/SEARCH_FORM_OPTIMIZATION.md)
- [样式系统使用指南](./src/styles/devRefs/STYLE_USAGE_GUIDE.md)
- [MoldSearchForm 改造示例](./src/components/_devRefs/MoldSearchForm_Migration_Example.md)

---

## 🔄 更新记录

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|---------|------|
| 1.0.0 | 2026-06-10 | 初始版本，包含命名规范、组件规范、样式规范等 | MoldingX Team |

---

**最后更新**: 2026-06-10  
**维护者**: MoldingX Team
