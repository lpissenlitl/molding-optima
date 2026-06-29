# 搜索表单优化方案

> **版本**: 1.0.0  
> **更新时间**: 2026-06-05  
> **作者**: MoldingX Team

---

## 🎯 优化目标

### 问题背景
1. ❌ 旧版搜索栏采用灰色背景，视觉层次不清晰
2. ❌ 所有筛选项平铺展示，占用大量空间
3. ❌ 无法灵活控制筛选项的显示/隐藏

### 优化方案
1. ✅ **卡片式设计**：替代灰色背景，提升视觉层次
2. ✅ **可展开/收起**：默认显示主要筛选项，高级选项按需展开
3. ✅ **响应式布局**：适配不同屏幕尺寸

---

## 📦 核心组件

### MoldSearchForm.vue

**位置**: `src/views/moldManage/components/MoldSearchForm.vue`

**特性**:
- 🎨 **轻量级设计**：使用自定义 `div.search-container`，避免 `el-card` 的厚重感
- 🔽 展开/收起功能
- 📱 响应式布局
- 🎯 基础项 + 高级项分离
- 🌍 **全局样式**：样式定义在 `src/styles/index.scss`，所有模块复用

---

## 💡 使用示例

### 1. 基础用法

```vue
<template>
  <div class="mold-list-page">
    <!-- 搜索表单 -->
    <MoldSearchForm 
      :query-detail="queryParams"
      @search="handleSearch"
    />
    
    <!-- 数据表格 -->
    <el-table :data="tableData">
      <!-- ... -->
    </el-table>
  </div>
</template>

<script>
import MoldSearchForm from './components/MoldSearchForm.vue'

export default {
  components: {
    MoldSearchForm
  },
  data() {
    return {
      queryParams: {
        mold_no: null,
        mold_name: null,
        category: null,
        structure: null,
        cavity_layout: null,
        manufacturing_method: null,
        page_no: 1
      },
      tableData: []
    }
  },
  methods: {
    handleSearch() {
      // 执行搜索逻辑
      this.fetchData()
    },
    fetchData() {
      // 调用 API 获取数据
      // ...
    }
  }
}
</script>
```

**渲染结果**：

```html
<div class="search-container">
  <el-form class="search-form" :inline="true">
    <!-- 表单项... -->
  </el-form>
</div>
```

---

### 2. 自定义筛选项

如果需要调整默认显示的筛选项，可以修改组件内部的 `basicItems` 和 `advancedItems`：

```javascript
data() {
  return {
    // 基础筛选项（默认显示 3-4 个）
    basicItems: [ 
      { label: "模具编号", prop: "mold_no", type: "autocomplete", query: { table: "mold", column: "mold_no" } },
      { label: "模具名称", prop: "mold_name", type: "autocomplete", query: { table: "mold", column: "mold_name" } },
      { label: "模具类别", prop: "category", type: "select", options: moldCategoryOptions },
    ],
    
    // 高级筛选项（展开后显示）
    advancedItems: [
      { label: "模具结构", prop: "structure", type: "select", options: moldStructureOptions },
      { label: "模腔布局", prop: "cavity_layout", type: "autocomplete", query: { table: "mold", column: "cavity_layout" } },
      { label: "制作方式", prop: "manufacturing_method", type: "autocomplete", query: { table: "project", column: "manufacturing_method" } },
    ]
  }
}
```

**建议**:
- ✅ 基础项：最常用的 3-4 个筛选项
- ✅ 高级项：较少使用的筛选项

---

### 3. 在其他模块中复用

可以将 `MoldSearchForm` 改造为通用组件 `BaseSearchForm`：

```vue
<!-- BaseSearchForm.vue -->
<template>
  <el-card class="search-card" shadow="hover">
    <el-form
      class="search-form"
      :inline="true"
      :model="query"
      size="small"
      label-width="auto"
    >
      <!-- 基础筛选项 -->
      <el-form-item
        v-for="(item, index) in basicItems"
        :key="'visible-' + index"
        :label="item.label"
        :prop="item.prop"
      >
        <!-- 渲染逻辑... -->
      </el-form-item>
      
      <!-- 高级筛选项 -->
      <template v-if="isExpanded">
        <el-form-item
          v-for="(item, index) in advancedItems"
          :key="'advanced-' + index"
          :label="item.label"
          :prop="item.prop"
        >
          <!-- 渲染逻辑... -->
        </el-form-item>
      </template>
      
      <!-- 操作按钮 -->
      <el-form-item class="search-actions">
        <el-button type="primary" icon="el-icon-search" @click="handleSearch">
          搜索
        </el-button>
        <el-button icon="el-icon-refresh" @click="handleReset">
          重置
        </el-button>
        <el-button type="text" @click="toggleExpand">
          {{ isExpanded ? '收起' : '展开' }}
          <i :class="isExpanded ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script>
export default {
  name: "BaseSearchForm",
  props: {
    queryDetail: {
      type: Object,
      required: true
    },
    basicItems: {
      type: Array,
      required: true
    },
    advancedItems: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      query: this.queryDetail,
      isExpanded: false
    }
  },
  methods: {
    toggleExpand() {
      this.isExpanded = !this.isExpanded
    },
    handleSearch() {
      this.$emit("search", this.query)
    },
    handleReset() {
      Object.keys(this.query).forEach(key => {
        if (key !== 'page_no') {
          this.query[key] = null
        }
      })
      this.$emit("reset")
    }
  }
}
</script>
```

**使用示例**：

```vue
<template>
  <BaseSearchForm
    :query-detail="queryParams"
    :basic-items="basicItems"
    :advanced-items="advancedItems"
    @search="handleSearch"
    @reset="handleReset"
  />
</template>

<script>
export default {
  data() {
    return {
      queryParams: { /* ... */ },
      basicItems: [
        { label: "设备编号", prop: "device_no", type: "autocomplete", /* ... */ },
        { label: "设备状态", prop: "status", type: "select", /* ... */ }
      ],
      advancedItems: [
        { label: "车间", prop: "workshop", type: "select", /* ... */ },
        { label: "品牌", prop: "brand", type: "autocomplete", /* ... */ }
      ]
    }
  }
}
</script>
```

---

## 🎨 样式说明

### 全局样式定义

**位置**: `src/styles/index.scss`

**设计理念**:
- ✅ **轻量级**：避免 `el-card` 的边框、阴影、固定内边距
- ✅ **现代化**：细边框 + 悬停阴影，视觉层次清晰但不厚重
- ✅ **可复用**：全局定义，所有搜索表单统一风格

```scss
.search-container {
  margin-bottom: var(--spacing-4);       // 16px
  padding: var(--spacing-4);             // 16px
  background-color: var(--color-bg-base); // #ffffff
  border: 1px solid var(--color-border-lighter); // #EBEEF5
  border-radius: var(--radius-base);     // 4px
  transition: all var(--transition-fast); // 150ms
  
  // 悬停时轻微阴影，提升交互反馈
  &:hover {
    box-shadow: var(--shadow-sm);        // 0 2px 4px rgba(0,0,0,0.08)
    border-color: var(--color-border-light); // #E4E7ED
  }
}
```

### 为什么不用 `el-card`？

| 对比维度 | el-card | .search-container |
|---------|---------|-------------------|
| **视觉重量** | ❌ 厚重（默认阴影+边框） | ✅ 轻量（细边框） |
| **内边距** | ❌ 固定 20px，需深度修改 | ✅ 灵活使用 CSS 变量 |
| **悬停效果** | ❌ 需手动添加 `shadow="hover"` | ✅ 自动过渡动画 |
| **代码复杂度** | ❌ 需 `:deep(.el-card__body)` | ✅ 直接样式控制 |
| **语义化** | ❌ 通用容器，语义不明确 | ✅ 专用于搜索区域 |

### 表单布局

```scss
.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-3); // 12px
  
  :deep(.el-form-item) {
    margin-bottom: 0;
    margin-right: 0;
  }
}
```

### 按钮区域

```scss
.search-actions {
  margin-left: auto; // 右对齐
  display: flex;
  gap: var(--spacing-2); // 8px
  align-items: center;
  
  .el-button--text {
    color: var(--theme-primary);
    font-weight: var(--font-weight-medium);
    padding: 0 var(--spacing-2);
    
    &:hover {
      color: var(--theme-primary-light);
      background-color: rgba(37, 67, 115, 0.05);
    }
  }
}
```

---

## 📱 响应式设计

在移动端（≤768px），表单会自动调整为垂直布局：

```scss
@media (max-width: 768px) {
  .search-form {
    flex-direction: column;
    
    .search-actions {
      margin-left: 0;
      width: 100%;
      justify-content: flex-end;
    }
  }
}
```

---

## 🔄 迁移指南

### 从旧版 `.search-area` 迁移到新版 `.search-container`

#### 旧代码

```vue
<template>
  <div class="search-area">
    <el-form class="search-form" :inline="true" :model="query">
      <!-- ... -->
    </el-form>
  </div>
</template>
```

#### 新代码

```vue
<template>
  <div class="search-container">
    <el-form class="search-form" :inline="true" :model="query" size="small">
      <!-- ... -->
    </el-form>
  </div>
</template>
```

**关键变化**:
1. ✅ `<div class="search-area">` → `<div class="search-container">`
2. ✅ `size="mini"` → `size="small"`（更现代的尺寸）
3. ✅ 自动应用全局样式（无需额外 CSS）
4. ✅ 悬停时自动显示轻微阴影

---

## ✅ 最佳实践

### 1. 筛选项分类原则

| 类别 | 数量 | 示例 |
|------|------|------|
| **基础项** | 3-4 个 | 编号、名称、类别、状态 |
| **高级项** | 不限 | 日期范围、创建人、备注等 |

### 2. 输入框宽度

统一使用 `.input-md` 类（12.5rem）：

```vue
<el-autocomplete class="input-md" />
<el-select class="input-md" />
```

### 3. 按钮顺序

推荐顺序：**搜索** → **重置** → **展开/收起**

```vue
<el-button type="primary" icon="el-icon-search">搜索</el-button>
<el-button icon="el-icon-refresh">重置</el-button>
<el-button type="text">展开</el-button>
```

### 4. 图标使用

- 🔍 搜索：`el-icon-search`
- 🔄 重置：`el-icon-refresh`
- ⬇️ 展开：`el-icon-arrow-down`
- ⬆️ 收起：`el-icon-arrow-up`

---

## 🎯 视觉效果对比

### 旧版（灰色背景）

```
┌─────────────────────────────────────┐
│ 背景: #f7f6f6                       │
│ 边框: 无                            │
│ 阴影: 无                            │
│ 问题: 视觉层次不清，与页面融合      │
└─────────────────────────────────────┘
```

### 旧版改进（el-card）

```
┌─────────────────────────────────────┐
│ ╔═══════════════════════════════╗   │
│ ║ 背景: #ffffff                 ║   │
│ ║ 边框: 1px solid #ebeef5      ║   │
│ ║ 阴影: 0 2px 12px (较重)      ║   │
│ ║ 内边距: 20px (固定)          ║   │
│ ╚═══════════════════════════════╝   │
│ 问题: 视觉过重，像独立卡片         │
└─────────────────────────────────────┘
```

### 新版（轻量级 .search-container）✨

```
┌─────────────────────────────────────┐
│ ─────────────────────────────────   │
│ 背景: #ffffff                       │
│ 边框: 1px solid #EBEEF5 (极浅)     │
│ 圆角: 4px                           │
│ 阴影: hover 时 0 2px 4px (轻微)    │
│ 内边距: 16px (CSS 变量)            │
│ ─────────────────────────────────   │
│ 优势: 轻量、现代、不抢眼           │
└─────────────────────────────────────┘
```

**设计理念**:
- ✅ **轻量级**：细边框 + 轻微阴影，不抢内容风头
- ✅ **交互反馈**：悬停时阴影加深，提示可操作
- ✅ **视觉统一**：与其他页面元素和谐共存
- ✅ **现代化**：符合 Material Design 和 Ant Design 的设计趋势

---

## 📚 相关文档

- [样式系统使用指南](./STYLE_USAGE_GUIDE.md)
- [Element UI 样式重构方案](./ELEMENT_UI_STYLE_REFACTOR.md)

---

## 🔧 间距与布局优化（2026-06-10 新增）

### 问题背景

在实际使用中发现以下问题：

1. ❌ **垂直间距过大**：表单项之间的上下间距显得松散，不够紧凑
2. ❌ **水平间距控制失效**：尝试使用 `:deep()` 在全局样式中控制间距无效
3. ❌ **搜索区域偏左**：表单项整体靠左，视觉上可以更向右靠近

### 根本原因分析

#### 为什么 `:deep()` 不生效？

```scss
// ❌ 错误做法：在全局样式文件中使用 :deep()
.search-container {
  .search-form {
    :deep(.el-form-item) {
      margin-bottom: 0 !important;
      margin-right: 12px !important;
    }
  }
}
```

**原因**：
- `:deep()` 是 Vue 3 **scoped 样式**的特性，用于穿透组件作用域
- `index.scss` 是**全局样式文件**，没有 scoped 作用域
- 在全局样式中，`:deep()` 会被编译成普通选择器，无法实现预期效果

#### 正确的做法

```scss
// ✅ 正确做法：直接嵌套选择器
.search-container {
  .search-form {
    &.el-form--inline {
      .el-form-item {
        margin-bottom: 8px;   // 直接设置垂直间距
        margin-right: 16px;   // 直接设置水平间距
        
        &:last-child {
          margin-right: 0;    // 最后一项无右边距
        }
      }
    }
  }
}
```

**原理**：
- Element UI 的 inline 表单通过 `.el-form-item` 的 `margin-right` 和 `margin-bottom` 控制间距
- 在全局样式中，直接使用 CSS 选择器覆盖即可
- 不需要 `!important`，因为选择器优先级足够

### 优化方案

#### 方案 A：调整容器内边距（推荐用于整体右移）

```scss
.search-container {
  padding: var(--spacing-4) var(--spacing-6);  // 左右从 20px → 24px
}
```

**适用场景**：希望整个搜索区域的内容都向右移动

#### 方案 B：使用 Flexbox 对齐（✅ 本次采用）

```scss
.search-form {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;  // 默认左对齐，可调整为 center/flex-end
  
  .search-actions {
    margin-left: auto;  // 按钮区域自动靠右
  }
}
```

**适用场景**：灵活控制表单项的对齐方式

#### 方案 C：调整表单项最小宽度

```scss
.search-form {
  .el-form-item {
    min-width: 200px;  // 增加最小宽度，让表单项更"饱满"
  }
}
```

**适用场景**：希望表单项在宽屏下占据更多空间

### 最终实施方案（2026-06-10）

结合用户需求，采用**方案 B + 间距优化**的组合：

```scss
.search-container {
  margin-bottom: var(--spacing-4);
  padding: var(--spacing-4) var(--spacing-5);
  background: linear-gradient(to bottom, #fafbfc, #ffffff);
  border: 1px solid var(--color-border-extra-light);
  border-radius: var(--radius-md);
  transition: all var(--transition-base);
  
  &:hover {
    box-shadow: 0 2px 8px rgba(37, 67, 115, 0.08);
  }
  
  .search-form {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;  // 表单项从左开始排列
    
    // Inline 表单优化
    &.el-form--inline {
      .el-form-item {
        margin-bottom: 8px;    // 垂直间距：10px → 8px（更紧凑）
        margin-right: 16px;    // 水平间距：统一为 16px
        
        &:last-child {
          margin-right: 0;     // 最后一项无右边距
        }
      }
    }
  }
  
  .search-actions {
    margin-left: auto;
    display: flex;
    gap: var(--spacing-3);
    align-items: center;
    padding-left: var(--spacing-4);
    border-left: 1px solid var(--color-border-extra-light);
    
    .el-button {
      min-width: 5.5rem;
      font-weight: var(--font-weight-medium);
    }
    
    .el-button--text {
      color: var(--theme-primary);
      font-weight: var(--font-weight-semibold);
      padding: 0 var(--spacing-3);
      min-width: auto;
      
      &:hover {
        color: var(--theme-primary-light);
        background-color: rgba(37, 67, 115, 0.08);
      }
      
      i {
        margin-left: var(--spacing-1);
      }
    }
  }
}
```

### 关键改进点

| 改进项 | 优化前 | 优化后 | 说明 |
|--------|--------|--------|------|
| **垂直间距** | `margin-bottom: 10px` | `margin-bottom: 8px` | 更紧凑，减少松散感 |
| **水平间距** | 未明确设置（依赖 Element UI 默认值） | `margin-right: 16px` | 统一控制，避免不一致 |
| **最后一项间距** | 未处理 | `&:last-child { margin-right: 0 }` | 避免右侧多余空白 |
| **Flexbox 对齐** | 仅 `display: flex` | 添加 `justify-content: flex-start` | 明确对齐策略，便于后续调整 |
| **`:deep()` 误用** | 尝试使用但无效 | 移除，改用直接选择器 | 符合全局样式规范 |

### 视觉效果对比

#### 优化前
```
┌─────────────────────────────────────┐
│ [标签] [输入框]  [标签] [输入框]   │ ← 垂直间距 10px（偏大）
│ [标签] [输入框]  [标签] [输入框]   │ ← 水平间距不统一
│                    [搜索] [重置]    │
└─────────────────────────────────────┘
```

#### 优化后
```
┌─────────────────────────────────────┐
│ [标签] [输入框] [标签] [输入框]    │ ← 垂直间距 8px（紧凑）
│ [标签] [输入框] [标签] [输入框]    │ ← 水平间距统一 16px
│                   [搜索] [重置]     │ ← 按钮靠右对齐
└─────────────────────────────────────┘
```

### 注意事项

1. **不要在全局样式中使用 `:deep()`**
   - ✅ 正确：`.search-form .el-form-item`
   - ❌ 错误：`.search-form :deep(.el-form-item)`

2. **Inline 表单的间距由 `margin` 控制**
   - 水平间距：`margin-right`
   - 垂直间距：`margin-bottom`
   - 需要手动处理 `:last-child` 避免多余间距

3. **Flexbox 布局的优势**
   - `margin-left: auto` 可以让按钮区域自动靠右
   - `justify-content` 可以灵活调整整体对齐方式
   - 响应式友好，易于适配不同屏幕尺寸

4. **如需进一步调整**
   - 更紧凑：`margin-bottom: 6px`
   - 更宽松：`margin-bottom: 12px`
   - 整体右移：增加 `.search-container` 的左右 `padding`
   - 居中对齐：`justify-content: center`

---

**最后更新**: 2026-06-10  
**维护者**: MoldingX Team
