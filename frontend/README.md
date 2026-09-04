# molding-optima · 前端

Vue 3 + Vite 5 + TypeScript + Element Plus 智能工艺系统前端。

> 与上游 [molding-expert-web](https://github.com/hsmolding/HsMoldingWeb) 共享 API 契约，独立演进。
> 架构决策详见 [architecture.md](../architecture.md)。

---

## 🎯 角色定位

本前端是 molding-optima 的 SPA 前端，定位：
- **面向工艺工程师**：注塑工艺初始化 + 缺陷驱动调优
- **三大业务模块**：用户管理 / 基础数据 / 工艺管理
- **演进策略**：与 molding-expert-web 并行演进，不主动融合

---

## 🛠 技术栈

| 维度 | 选型 |
|---|---|
| 框架 | Vue 3（Composition API + `<script setup>`）|
| 构建 | Vite 5 |
| 语言 | TypeScript |
| 状态 | Pinia |
| 路由 | Vue Router 4 |
| UI | Element Plus |
| HTTP | axios |
| 图标 | Iconify（[@iconify/vue](https://iconify.design/)）|
| 样式 | SCSS（CSS 变量 + Mixin，详见 §样式系统）|

---

## 🚀 快速开始

```bash
# 安装依赖
npm install

# 开发（默认端口 9527）
npm run dev

# 生产构建
npm run build

# 类型检查（不输出，仅检查）
vue-tsc --noEmit
```

启动后访问 http://localhost:9527/

> 后端默认代理到 `http://127.0.0.1:8200`，配置见 [vite.config.ts](./vite.config.ts)。

---

## 📁 目录结构

```
src/
├── api/                # API 封装（按业务模块拆分）
├── components/         # 公共组件
├── composables/        # 组合式函数
├── directives/         # 自定义指令
├── layouts/            # 布局组件
├── router/             # 路由配置
├── stores/             # Pinia 状态
├── styles/             # 全局样式（详见 §样式系统）
├── utils/              # 工具函数
├── views/              # 业务页面
│   ├── login/
│   ├── 404.vue
│   └── {module}/
├── App.vue
└── main.ts
```

---

## 🎨 样式系统（五层架构）

> **设计原则**：CSS 变量（运行时） + SCSS Mixin（编译时）= 完整工具集。
> 详见 [architecture.md §ADR-004](../architecture.md#adr-004前端样式系统分层架构五层)。

| 文件 | 职责 | 时机 |
|---|---|---|
| `tokens.scss` | 设计令牌（颜色/尺寸/间距/字体）| 运行时（CSS 变量）|
| `mixins.scss` | SCSS 工具集（断点/flex/文本截断）| 编译时（Mixin）|
| `element-plus.scss` | Element Plus 主题色覆盖 | 运行时（CSS 变量）|
| `reset.scss` | CSS Reset | 全局重置 |
| `transition.scss` | Vue 3 过渡动画 | 运行时 |

### 使用约定

```vue
<style scoped lang="scss">

/* ✅ 颜色/尺寸/间距：走 tokens.scss */
.button {
  color: var(--theme-primary);
  padding: var(--spacing-4);
  border-radius: var(--radius-md);
}

/* ✅ 重复样式块：走 mixins.scss */
.row {
  @include flex-between;
}

/* ✅ 响应式：走 mixins.scss（语义化断点）*/
@include breakpoint-down(md) {
  .button { padding: var(--spacing-2); }
}

</style>
```

**规则**：所有 `<style>` 必须 `lang="scss"`；先查 tokens，再查 mixin，两者都不够才写新代码。

---

## 📐 前端代码规范

详见 [CODING_STANDARDS.md](./CODING_STANDARDS.md)（与 molding-expert-web 共享）。

> 注：Vue 3 + Composition API 部分需以本项目实际代码为准（如 `<script setup>`、`ref`/`reactive`、`defineStore`）。

---

## 🔌 关键依赖

| 库 | 用途 | 备注 |
|---|---|---|
| vue@3 | 框架 | Composition API |
| vite@5 | 构建 | Sass Modern Compiler API |
| element-plus | UI 库 | 主题色由 CSS 变量驱动 |
| pinia | 状态 | 替代 Vuex |
| vue-router@4 | 路由 | |
| axios | HTTP | 统一拦截器 |
| @iconify/vue | 图标 | mdi 图标集 |
| sass | SCSS 编译 | Modern API（`api: 'modern-compiler'`）|

历史依赖（已移除）：vuex / vue-print-nb / vue-svgicon / vue-simple-uploader / vuex-module-decorators / jest / ts-jest。

---

## 📝 版本

**当前版本**：v0.5
**最后更新**：2026-09-02