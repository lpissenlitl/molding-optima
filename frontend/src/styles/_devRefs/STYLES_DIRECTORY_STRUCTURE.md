# Styles 目录结构说明

## 📁 当前结构

```
src/styles/
├── _devRefs/                    # 开发参考文档
│   └── BUTTON_STYLING_BEST_PRACTICES.md
├── variables/                   # 设计令牌（Design Tokens）
│   └── tokens.scss              # CSS 变量定义（运行时）
├── theme/                       # 主题定制
│   ├── custom.scss              # 自定义主题样式
│   └── _devRefs/
├── utilities/                   # 工具类
├── index.scss                   # 主入口文件
├── variables.scss               # ⚠️ 遗留的 SCSS 变量（待迁移）
├── element-variables.scss       # Element UI 主题变量（必需）
├── element-variables.scss.d.ts  # TypeScript 声明文件
├── mixin.scss                   # SCSS Mixins
├── svgicon.scss                 # SVG 图标样式
└── transition.scss              # 过渡动画
```

---

## 📋 文件分类说明

### 1. **Element UI 主题变量**（必需）

#### `element-variables.scss`
**位置：** `src/styles/element-variables.scss`  
**作用：** 自定义 Element UI 组件的主题色  
**类型：** SCSS 变量（编译时）

```scss
// 覆盖 Element UI 默认变量
$--color-primary: #1890ff;
$--color-success: #13ce66;

// 引入 Element UI 样式
@import '~element-ui/packages/theme-chalk/src/index';

// 导出给 TypeScript 使用
:export {
  theme: $--color-primary;
}
```

**为什么必须在根目录？**
- Element UI 官方推荐的位置
- webpack/vite 配置中通常硬编码了这个路径
- 被 `settings.ts` 引用获取主题色

#### `element-variables.scss.d.ts`
**位置：** `src/styles/element-variables.scss.d.ts`  
**作用：** TypeScript 声明文件，让 TS 识别 scss 导出的内容

```typescript
export interface IScssVariables {
  theme: string
}

export const variables: IScssVariables
export default variables
```

**为什么需要它？**
- TypeScript 无法直接理解 `.scss` 文件的导出
- 需要在 `settings.ts` 中使用：`import elementVariables from "@/styles/element-variables.scss"`
- 提供类型提示和编译检查

---

### 2. **设计令牌（Design Tokens）**（新建）

#### `variables/tokens.scss`
**位置：** `src/styles/variables/tokens.scss`  
**作用：** 全局 CSS 变量定义，支持运行时动态切换  
**类型：** CSS 变量（运行时）

```scss
:root {
  --theme-primary: #254373;
  --font-size-base: 14px;
  --radius-sm: 4px;
  // ...
}
```

**优点：**
- ✅ 支持运行时动态切换主题
- ✅ 可以被 JavaScript 读取和修改
- ✅ 符合现代前端最佳实践

**使用方式：**
```scss
// 在任何 SCSS 文件中使用
.button {
  color: var(--theme-primary);
}
```

```typescript
// 在 JavaScript/TypeScript 中读取
const primaryColor = getComputedStyle(document.documentElement)
  .getPropertyValue('--theme-primary')
```

---

### 3. **遗留 SCSS 变量**（待迁移）

#### `variables.scss`
**位置：** `src/styles/variables.scss`  
**状态：** ⚠️ 遗留文件，建议迁移到 `variables/` 目录

```scss
// 当前的内容
$sideBarWidth: 200px;
$subMenuBg: #1f2d3d;
$loginBg: #2d3a4b;
```

**建议操作：**
1. 创建 `variables/layout.scss` - 布局相关变量
2. 创建 `variables/login.scss` - 登录页变量
3. 迁移完成后删除 `variables.scss`

---

### 4. **主题定制**

#### `theme/custom.scss`
**位置：** `src/styles/theme/custom.scss`  
**作用：** 基于设计令牌的自定义样式

```scss
.theme-moldingx {
  .el-button {
    // 使用 CSS 变量
    color: var(--theme-primary);
  }
}
```

**注意：** 
- ❌ 不要直接覆盖 `.el-button`（参见 BUTTON_STYLING_BEST_PRACTICES.md）
- ✅ 使用 CSS 变量或精确选择器

---

## 🔄 变量使用优先级

### 推荐使用顺序

1. **CSS 变量（首选）** → `variables/tokens.scss`
   ```scss
   color: var(--theme-primary);
   ```

2. **SCSS 变量（次选）** → 仅用于编译时确定的值
   ```scss
   width: $sideBarWidth;
   ```

3. **Element UI 变量（特殊）** → 仅用于 Element UI 主题定制
   ```scss
   $--color-primary: #1890ff;
   ```

---

## 📊 对比总结

| 特性 | CSS 变量 | SCSS 变量 |
|------|---------|----------|
| **定义位置** | `variables/tokens.scss` | `variables/*.scss` |
| **生效时机** | 运行时 | 编译时 |
| **动态切换** | ✅ 支持 | ❌ 不支持 |
| **JS 访问** | ✅ 可以 | ❌ 不可以 |
| **浏览器支持** | 现代浏览器 | 所有浏览器（编译后） |
| **推荐场景** | 主题色、间距、字号等 | 固定值、布局尺寸等 |

---

## ✅ 最佳实践

### 1. 新变量定义

```scss
// ✅ 推荐：放在 variables/tokens.scss
:root {
  --new-variable: value;
}

// ❌ 不推荐：创建新的 SCSS 变量文件
```

### 2. 变量使用

```scss
// ✅ 推荐：优先使用 CSS 变量
.button {
  color: var(--theme-primary);
}

// ⚠️ 次选：如果必须是编译时确定，使用 SCSS 变量
.sidebar {
  width: $sideBarWidth;
}
```

### 3. Element UI 主题定制

```scss
// ✅ 推荐：在 element-variables.scss 中定义
$--color-primary: var(--theme-primary);  // 结合 CSS 变量

// ❌ 不推荐：在 custom.scss 中直接覆盖 .el-button
```

---

## 🚀 未来优化计划

### 短期（1-2 周）
1. ✅ 保持 `element-variables.scss` 不变（必需）
2. 🔄 迁移 `variables.scss` 到 `variables/` 目录
   - `variables/layout.scss` - 布局变量
   - `variables/login.scss` - 登录页变量
3. 📝 更新引用路径

### 中期（1-3 个月）
1. 🔄 逐步将 SCSS 变量转换为 CSS 变量
2. 🔄 统一使用 `variables/tokens.scss`
3. 🗑️ 删除旧的 `variables.scss`

### 长期（3-6 个月）
1. 🔄 考虑升级到 Element Plus（Vue 3）
2. 🔄 全面使用 CSS 变量
3. 🗑️ 移除 `element-variables.scss`（Element Plus 原生支持 CSS 变量）

---

## 📚 相关文档

- [BUTTON_STYLING_BEST_PRACTICES.md](./_devRefs/BUTTON_STYLING_BEST_PRACTICES.md) - 按钮样式定制最佳实践
- [tokens.scss](../variables/tokens.scss) - 设计令牌定义
- [custom.scss](../theme/custom.scss) - 主题定制样式

---

**最后更新：** 2026-06-10  
**维护人员：** MoldingX Team
