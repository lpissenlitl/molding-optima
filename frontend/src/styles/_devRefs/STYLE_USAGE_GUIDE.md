# 样式系统使用指南

> **版本**: 2.0.0  
> **更新时间**: 2026-06-05  
> **作者**: MoldingX Team

---

## 📚 目录

1. [架构概览](#架构概览)
2. [快速开始](#快速开始)
3. [设计令牌](#设计令牌)
4. [主题类使用](#主题类使用)
5. [工具类使用](#工具类使用)
6. [迁移指南](#迁移指南)
7. [最佳实践](#最佳实践)

---

## 🏗️ 架构概览

新的样式系统采用分层架构，从底层到上层依次为：

```
src/styles/
├── variables/
│   └── tokens.scss          # 设计令牌（CSS 变量）
├── theme/
│   └── custom.scss          # 自定义主题类（.theme-moldingx）
├── utilities/
│   ├── spacing.scss         # 间距工具类
│   └── typography.scss      # 排版工具类
└── index.scss               # 入口文件
```

### 核心原则

✅ **非侵入性**：不直接修改 Element UI 组件样式  
✅ **可配置性**：通过 CSS 变量轻松调整主题  
✅ **语义化**：变量名表达业务含义  
✅ **渐进增强**：保留 Element UI 默认值作为降级方案  

---

## 🚀 快速开始

### 1. 启用主题

在 `App.vue` 根元素添加 `theme-moldingx` 类：

```vue
<template>
  <div id="app" class="theme-moldingx">
    <router-view />
  </div>
</template>
```

### 2. 使用工具类

```vue
<template>
  <div class="p-4 mb-4">
    <h2 class="text-lg font-bold text-primary">标题</h2>
    <p class="text-sm text-secondary">描述文字</p>
    <el-button class="mt-3">按钮</el-button>
  </div>
</template>
```

### 3. 使用表格变体

```vue
<template>
  <!-- 紧凑型表格 -->
  <el-table class="table-compact" :data="data">
    <!-- ... -->
  </el-table>
  
  <!-- 朴素风格表格 -->
  <el-table class="table-simple" :data="data">
    <!-- ... -->
  </el-table>
</template>
```

---

## 🎨 设计令牌

### 字体系统

```scss
// 可用字号
--font-size-xs: 12px;      // 辅助文字
--font-size-sm: 13px;      // 次要信息
--font-size-base: 14px;    // 正文（Element UI 默认）
--font-size-md: 16px;      // 业务常用
--font-size-lg: 18px;      // 小标题
--font-size-xl: 20px;      // 大标题

// 字重
--font-weight-light: 300;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;
```

**使用示例**：

```vue
<span class="text-xs">辅助文字</span>
<span class="text-sm">次要信息</span>
<span class="text-base">正文</span>
<span class="text-md">强调文字</span>
<h3 class="text-lg font-semibold">小标题</h3>
<h2 class="text-xl font-bold">大标题</h2>
```

---

### 颜色系统

#### 主题色

```scss
--theme-primary: #254373;           // 主品牌色
--theme-primary-light: #3a5a8f;     // 悬停状态
--theme-primary-dark: #1a2d4d;      // 激活状态
```

#### 功能色

```scss
--color-success: #67C23A;   // 成功
--color-warning: #E6A23C;   // 警告
--color-danger: #F56C6C;    // 危险/错误
--color-info: #909399;      // 信息
```

#### 中性色

```scss
--color-text-primary: #303133;      // 主要文字
--color-text-regular: #606266;      // 常规文字
--color-text-secondary: #909399;    // 次要文字
--color-text-placeholder: #C0C4CC;  // 占位文字
```

**使用示例**：

```vue
<p class="text-primary">主题色文字</p>
<p class="text-success">成功提示</p>
<p class="text-danger">错误信息</p>
<p class="text-secondary">次要说明</p>
```

---

### 间距系统

基于 **4px 网格系统**：

```scss
--spacing-1: 4px;
--spacing-2: 8px;
--spacing-3: 12px;
--spacing-4: 16px;
--spacing-5: 24px;
--spacing-6: 32px;
--spacing-8: 48px;
--spacing-10: 64px;
```

**使用示例**：

```vue
<!-- Margin -->
<div class="m-4">全方向外边距 16px</div>
<div class="mt-2 mb-4">上 8px，下 16px</div>
<div class="mx-auto">水平居中</div>

<!-- Padding -->
<div class="p-3">全方向内边距 12px</div>
<div class="px-4 py-2">左右 16px，上下 8px</div>

<!-- Gap (Flex/Grid) -->
<div class="flex gap-3">
  <div>项目1</div>
  <div>项目2</div>
</div>
```

---

### 表单控件宽度

```scss
--form-control-width-xs: 6rem;    // 超短输入（如数量）
--form-control-width-sm: 8rem;    // 短输入（如编号）
--form-control-width-md: 12.5rem; // 标准输入（默认）
--form-control-width-lg: 16rem;   // 长输入（如名称）
--form-control-width-xl: 24rem;   // 超长输入（如描述）
--form-control-width-full: 100%;  // 全宽输入
```

**使用示例**：

```vue
<!-- 工具类方式 -->
<el-input class="input-sm" v-model="code" placeholder="编号" />
<el-input class="input-md" v-model="name" placeholder="名称" />
<el-input class="input-full" v-model="description" placeholder="描述" />

<!-- 或在 form 内自动应用默认宽度 -->
<el-form>
  <el-form-item label="设备编号">
    <el-input v-model="deviceNo" /> <!-- 自动应用 input-md -->
  </el-form-item>
</el-form>
```

---

## 🎭 主题类使用

### `.theme-moldingx` 的作用范围

当在根元素添加 `.theme-moldingx` 类后，以下组件会自动应用自定义样式：

| 组件 | 定制内容 |
|------|---------|
| **Tabs** | 标签颜色、激活态加粗、底部边框颜色 |
| **Card** | 标题颜色、头部底边线、圆角、阴影 |
| **Dialog** | 标题栏背景、标题颜色、关闭按钮样式 |
| **Table** | 表头背景、表头底边线、行悬停效果 |
| **Collapse** | 面板标题颜色、边框颜色 |
| **Drawer** | 标题栏背景、标题颜色、底边线 |
| **Form** | 标签颜色、表单项间距、Inline 表单优化 |
| **Button** | 主按钮颜色、悬停/激活态、圆角 |

### 局部禁用主题

如果某些区域需要保持 Element UI 原生样式，可以移除该类：

```vue
<template>
  <div class="theme-moldingx">
    <!-- 这部分应用自定义主题 -->
    <el-tabs>...</el-tabs>
    
    <!-- 这部分保持原生样式 -->
    <div class="">
      <el-tabs>...</el-tabs>
    </div>
  </div>
</template>
```

---

## 🛠️ 工具类使用

### 间距工具类

#### Margin（外边距）

```scss
// 全方向
.m-0, .m-1, .m-2, .m-3, .m-4, .m-5, .m-6, .m-8, .m-10

// 垂直方向
.my-0, .my-1, .my-2, .my-3, .my-4, .my-5, .my-6

// 水平方向
.mx-0, .mx-1, .mx-2, .mx-3, .mx-4, .mx-5, .mx-6, .mx-auto

// 单方向
.mt-*, .mb-*, .ml-*, .mr-*  // 同上，支持 0-10
```

#### Padding（内边距）

```scss
// 全方向
.p-0, .p-1, .p-2, .p-3, .p-4, .p-5, .p-6, .p-8, .p-10

// 垂直方向
.py-0, .py-1, .py-2, .py-3, .py-4, .py-5, .py-6

// 水平方向
.px-0, .px-1, .px-2, .px-3, .px-4, .px-5, .px-6

// 单方向
.pt-*, .pb-*, .pl-*, .pr-*  // 同上，支持 0-6
```

### 排版工具类

#### 字体大小

```scss
.text-xs, .text-sm, .text-base, .text-md, .text-lg, .text-xl
```

#### 字重

```scss
.font-light, .font-normal, .font-medium, .font-semibold, .font-bold
```

#### 文字颜色

```scss
// 主题色
.text-primary, .text-primary-light, .text-primary-dark

// 功能色
.text-success, .text-warning, .text-danger, .text-info

// 中性色
.text-primary-text, .text-regular, .text-secondary, 
.text-placeholder, .text-disabled
```

#### 文字对齐

```scss
.text-left, .text-center, .text-right, .text-justify
```

#### 文字溢出处理

```scss
.truncate     // 单行省略号
.break-word   // 自动换行
.no-wrap      // 不换行
```

---

## 🔄 迁移指南

### 从旧样式迁移到新样式

#### 示例 1：表格样式

**旧代码**：

```vue
<template>
  <el-table :data="data">
    <!-- ... -->
  </el-table>
</template>

<style scoped>
::v-deep .el-table__header th {
  background-color: lightblue;
}
</style>
```

**新代码**：

```vue
<template>
  <el-table class="table-themed" :data="data">
    <!-- ... -->
  </el-table>
</template>

<!-- 无需额外样式，已在 theme/custom.scss 中定义 -->
```

#### 示例 2：卡片标题

**旧代码**：

```vue
<template>
  <el-card>
    <div slot="header" class="clearfix">
      <span style="color: #254373; font-size: 19px; font-weight: bold;">
        标题
      </span>
    </div>
  </el-card>
</template>
```

**新代码**：

```vue
<template>
  <el-card>
    <div slot="header" class="clearfix">
      <span class="text-md font-semibold text-primary">标题</span>
    </div>
  </el-card>
</template>
```

#### 示例 3：表单布局

**旧代码**：

```vue
<template>
  <el-form>
    <el-form-item label="设备编号">
      <el-input style="width: 200px" v-model="deviceNo" />
    </el-form-item>
  </el-form>
</template>
```

**新代码**：

```vue
<template>
  <el-form>
    <el-form-item label="设备编号">
      <el-input class="input-md" v-model="deviceNo" />
      <!-- 或直接在 form 内自动应用默认宽度 -->
    </el-form-item>
  </el-form>
</template>
```

---

## ✅ 最佳实践

### 1. 优先使用工具类

❌ **不推荐**：

```vue
<div style="margin-top: 16px; padding: 12px; color: #254373;">
  内容
</div>
```

✅ **推荐**：

```vue
<div class="mt-4 p-3 text-primary">
  内容
</div>
```

### 2. 避免全局样式覆盖

❌ **不推荐**：

```scss
.el-button {
  font-size: 16px; // 影响所有按钮
}
```

✅ **推荐**：

```scss
.theme-moldingx {
  .el-button {
    font-size: var(--font-size-md); // 仅在主题内生效
  }
}
```

### 3. 语义化类名

❌ **不推荐**：

```vue
<div class="box-1">...</div>
```

✅ **推荐**：

```vue
<div class="card-header">...</div>
```

### 4. 响应式设计

使用媒体查询结合工具类：

```vue
<template>
  <div class="px-4 md:px-6 lg:px-8">
    响应式内边距
  </div>
</template>
```

---

## 🔍 常见问题

### Q1: 为什么我的样式没有生效？

**检查清单**：

1. ✅ 确认 `App.vue` 根元素有 `theme-moldingx` 类
2. ✅ 确认浏览器缓存已清除（硬刷新：Ctrl+Shift+R）
3. ✅ 检查是否有更高优先级的样式覆盖
4. ✅ 确认 SCSS 文件已正确导入到 `index.scss`

### Q2: 如何临时禁用主题？

移除 `theme-moldingx` 类即可：

```vue
<template>
  <div id="app"> <!-- 移除 class="theme-moldingx" -->
    <router-view />
  </div>
</template>
```

### Q3: 如何自定义某个组件的样式？

在组件的 `<style scoped>` 中使用 `:deep()`：

```vue
<style scoped lang="scss">
.my-component {
  :deep(.el-input__inner) {
    border-color: var(--theme-primary);
  }
}
</style>
```

### Q4: 工具类和自定义样式冲突怎么办？

工具类使用了 `!important`，优先级最高。如需覆盖，可以在自定义样式中也使用 `!important`，或提高选择器优先级。

---

## 📖 参考资料

- [CSS Variables Guide](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Element UI Documentation](https://element.eleme.cn/)
- [Design Tokens](https://www.designsystem.com/design-tokens/)

---

**最后更新**: 2026-06-05  
**维护者**: MoldingX Team
