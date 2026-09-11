# 设备管理整理计划（2026-09-09）

> **范围**：前端 only（后端 `injection-machines` / `auxiliary-equipments` API 完整，已就绪）
> **目标目录**：`views/injection/`、`views/auxiliary/`（按用户指示拆分）
> **路由风格**：参考 [material/polymer](file:///F:/items/moldingx/molding-optima/frontend/src/router/index.ts#L141-L197) —— 统一前缀 `equipment/`，list / new / :id/edit / :id/copy 四种路由复用同一组件

---

## 一、现状摘要

### 后端（已完整，无需改动）

| 模型 / 视图 | 路径 |
|------|------|
| 注塑机 | `backend/masterdata/models/injection.py` + `schemas/injection.py` + `services/injection_service.py` + `views/injections.py` |
| 辅助装置 | `backend/masterdata/models/auxiliary.py` + `schemas/auxiliary.py` + `services/auxiliary_service.py` + `views/auxiliaries.py` |
| URL | `/api/injection-machines/`、`/api/auxiliary-equipments/` |

### 前端代码（已存在但未接入路由）

```
src/views/equipment/
├── components/
│   ├── InjectionSearchForm.vue   ← 未引用
│   ├── InjectionUnitForm.vue     ← 未引用（且 Import 路径坏）
│   └── UnitConversion.vue        ← 未引用
└── pages/
    ├── AuxiliaryEquipmentList.vue  ← 用 dialog 模式（缺表单）
    ├── InjectionMachineForm.vue    ← viewContext props + is_dialog 模式
    └── InjectionMachineList.vue    ← dialog 模式
```

### 关键问题

1. **InjectionMachineForm.vue 的 import 路径错误**（line 322）：
   ```javascript
   import InjectionUnitForm from "./components/InjectionUnitForm.vue"
   ```
   Form 在 `pages/`，components 在**上级目录** `equipment/components/`。实际路径应是 `../components/InjectionUnitForm.vue`。当前 import 会在运行时失败。

2. **缺少 AuxiliaryEquipmentForm.vue**：List 页里 `addAuxiliary` / `editAuxiliary` 用 `view_context.mode` 切 dialog，但模板里**没有任何 form 引用**——dialog 永远显示不出表单。

3. **路由还是占位**：`/equipment/injection`、`/equipment/auxiliary` 都引用 `BusinessPlaceholder`。

4. **API 散落**：
   - `api/index.ts:56-63` 三个函数式 `injectionMachineList/Create/Detail`
   - `api/index.ts:303-304` 两个 BaseRequest `machineMethod`/`auxiliaryMethod`
   - （参考 polymer/filler 同样混合写法，保持现状不动）

---

## 二、目标结构

### 物理目录

```
src/views/
├── injection/
│   ├── components/
│   │   ├── InjectionSearchForm.vue
│   │   ├── InjectionUnitForm.vue
│   │   └── UnitConversion.vue
│   └── pages/
│       ├── InjectionMachineForm.vue
│       └── InjectionMachineList.vue
└── auxiliary/
    ├── components/   (留空备用)
    └── pages/
        ├── AuxiliaryEquipmentForm.vue   ← 新建
        └── AuxiliaryEquipmentList.vue
```

`views/equipment/` 目录整体删除。

### 路由（参考 material/polymer）

```typescript
{
  path: 'equipment',
  component: ParentView,
  redirect: '/equipment/injection/list',
  meta: { title: '设备管理', icon: 'mdi:factory', alwaysShow: true },
  children: [
    // 注塑机
    {
      path: 'injection/list',
      name: 'equipment-injection-list',
      component: () => import('@/views/injection/pages/InjectionMachineList.vue'),
      meta: { title: '机器列表', icon: 'mdi:server-outline' },
    },
    {
      path: 'injection/new',
      name: 'equipment-injection-new',
      component: () => import('@/views/injection/pages/InjectionMachineForm.vue'),
      meta: { title: '新建注塑机', hidden: true },
    },
    {
      path: 'injection/:id/edit',
      name: 'equipment-injection-edit',
      component: () => import('@/views/injection/pages/InjectionMachineForm.vue'),
      meta: { title: '编辑注塑机', hidden: true },
    },
    {
      path: 'injection/:id/copy',
      name: 'equipment-injection-copy',
      component: () => import('@/views/injection/pages/InjectionMachineForm.vue'),
      meta: { title: '复制注塑机', hidden: true },
    },
    // 辅助装置
    {
      path: 'auxiliary/list',
      name: 'equipment-auxiliary-list',
      component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentList.vue'),
      meta: { title: '辅助装置', icon: 'mdi:tools' },
    },
    {
      path: 'auxiliary/new',
      name: 'equipment-auxiliary-new',
      component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentForm.vue'),
      meta: { title: '新建辅助装置', hidden: true },
    },
    {
      path: 'auxiliary/:id/edit',
      name: 'equipment-auxiliary-edit',
      component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentForm.vue'),
      meta: { title: '编辑辅助装置', hidden: true },
    },
    {
      path: 'auxiliary/:id/copy',
      name: 'equipment-auxiliary-copy',
      component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentForm.vue'),
      meta: { title: '复制辅助装置', hidden: true },
    },
  ],
},
```

---

## 三、改动文件清单

| 类别 | 文件 | 改动 |
|------|------|------|
| 移动 | `views/equipment/pages/InjectionMachineList.vue` | → `views/injection/pages/` |
| 移动 | `views/equipment/pages/InjectionMachineForm.vue` | → `views/injection/pages/` |
| 移动 | `views/equipment/pages/AuxiliaryEquipmentList.vue` | → `views/auxiliary/pages/` |
| 移动 | `views/equipment/components/InjectionSearchForm.vue` | → `views/injection/components/` |
| 移动 | `views/equipment/components/InjectionUnitForm.vue` | → `views/injection/components/` |
| 移动 | `views/equipment/components/UnitConversion.vue` | → `views/injection/components/` |
| 删 | `views/equipment/` 目录 | 整体删除 |
| 改 | `router/index.ts` | 设备管理路由块改写为 material 风格 |
| 修 | `views/injection/pages/InjectionMachineForm.vue` | 修 import 路径 + 适配路由驱动模式 |
| 改 | `views/injection/pages/InjectionMachineList.vue` | 跳转改 `router.push` |
| 改 | `views/auxiliary/pages/AuxiliaryEquipmentList.vue` | 去掉 dialog 模式，跳转改 `router.push` |
| 新建 | `views/auxiliary/pages/AuxiliaryEquipmentForm.vue` | 参考 polymer 风格 |

---

## 四、关键设计决策

### 4.1 表单从 dialog 改成路由驱动

**原因**：
- polymer/mold 都是路由驱动（new/edit/copy 三种路由复用同一 Form）
- 路由驱动天然支持浏览器后退、刷新、复制链接
- 与 sidebar 菜单、面包屑集成更自然

**实现模式**（参考 polymer）：
```javascript
mounted() {
  // 从 query.mode 读模式：create / edit / copy
  this.mode = this.$route.query.mode || 'create'
  // 从 params.id 读目标对象 id
  this.id = this.$route.params.id
  if (this.id) {
    this.loadDetail()
  }
}

methods: {
  loadDetail() {
    if (this.mode === 'copy') {
      // 复制模式：拉详情但清空 id
      machineMethod.getDetail(this.id).then(res => {
        const { id, ...rest } = res.data
        Object.assign(this.machine, rest)
      })
    } else {
      // 编辑模式：拉详情保留 id
      machineMethod.getDetail(this.id).then(res => {
        Object.assign(this.machine, res.data)
      })
    }
  },
  async save() {
    if (this.mode === 'edit') {
      await machineMethod.edit(this.machine, this.machine.id)
    } else {
      await machineMethod.add(this.machine)
    }
    this.$router.push('/equipment/injection/list')
  }
}
```

### 4.2 InjectionMachineForm 的特殊处理

**保留**：
- `view_context.is_dialog` 判断逻辑 —— 因为重构第一版可能仍需要兼容调用方；但实际上**调用方都已重构**，所以**直接干掉**

**简化**：
- 删 `props: { viewContext: ... }`
- 删 `view_context.is_dialog` 判断按钮
- 改 `mounted()` 从 `this.$route.query` 取 mode，从 `this.$route.params` 取 id
- 改 `import InjectionUnitForm from "./components/..."` → `"../components/..."`

### 4.3 AuxiliaryEquipmentForm 新建

**字段来源**：参考 `machine-const.js`，新建 `constants/auxiliary-const.js` 定义字段 schema（品牌、型号、类别、规格参数等）

**简化策略**：
- 第一版只支持核心字段（设备名称、品牌、型号、类型、规格、备注）
- 复杂规格参数（加热功率、控制精度等）放到扩展 JSON 字段
- 保持表单简单可运行

---

## 五、验证清单

- [ ] `npm run type-check` 无 request.ts / injection / auxiliary 相关错误
- [ ] 启动 dev server，能进入 `/equipment/injection/list` 看到列表
- [ ] 列表页"添加机器"按钮跳转到 `/equipment/injection/new` 并显示表单
- [ ] 表单"保存"成功后返回列表
- [ ] 列表页双击行进入 `/equipment/injection/:id/edit` 显示编辑表单
- [ ] 辅助装置四个路由同样工作

---

## 六、不做的事

- **不**拆 `api/equipment.ts` —— 保持项目现有"单文件 API"风格（参考 polymer/filler）
- **不**改后端任何东西 —— API 已完整
- **不**调整 InjectionMachineForm 的字段结构 —— 仅修 import + 适配路由
- **不**做国际化适配 —— 与项目现有风格保持一致
- **不**做单元测试 —— 项目暂无组件测试规范

---

## 七、后续清理（同日追加，PolymerList ElOnlyChild 警告定位与衍生重构）

> **范围**：设备管理整理过程中，手动刷新 dev server 验证时控制台出现大量警告，顺手清理
> **起点**：刷新 `/material/polymer/list`（BaseTable 驱动的列表页）时控制台报 9 次 `[ElOnlyChild] no valid child node found`

### 7.1 警告分类

| # | 警告文本 | 次数 | 触发原因 |
|---|----------|------|----------|
| 1 | `ElementPlusError: [props] [API] type.text is about to be deprecated in version 3.0.0, please use link instead` | 5 | `<el-button type="text">`（element-plus 3.0 弃用） |
| 2 | `ElementPlusError: [ElOnlyChild] no valid child node found` | 9 | `<el-popover>` 用 Vue 2 风格的 `slot="reference"`，导致 default slot 多根 |

### 7.2 警告 #1：`<el-button type="text">` → `type="link"`

**范围**：13 个 vue 文件 22 处

**修复方式**：PowerShell 批量替换，分两轮（单行 + Singleline 跨行）

```powershell
# 轮 1：同行匹配
$content.Replace('<el-button type="text"', '<el-button type="link"')
# 轮 2：跨行匹配（需要 Singleline 选项，否则 \s 不跨行）
[regex]::Replace($content, '<el-button\s+type="text"', '<el-button type="link"', [System.Text.RegularExpressions.RegexOptions]::Singleline)
```

**绕过 `<el-input type="text">` 等合法用法**：匹配字符串限定为 `<el-button ... type="text"`，避免误伤 el-input / el-upload list-type。

**不动的合法用例**：`<el-input type="text">`（7 处）、`list-type="text"`（el-upload 3 处）、`<el-button class="custom-btn-text">` 自定义按钮、注释中的说明文本。

### 7.3 警告 #2：`ElOnlyChild` 定位

**调试手段**：`main.ts` 临时 hook `console.warn`，把 `[ElOnlyChild]` 警告改 throw。刷新浏览器后第一个红屏 stack trace 指向触发组件。

```typescript
// main.ts 临时 hook（仅 DEV，后续已删除）
if (import.meta.env.DEV) {
  const _origWarn = console.warn
  console.warn = function (...args: unknown[]) {
    const msg = args[0] instanceof Error ? args[0].message : String(args[0] ?? '')
    if (msg.includes('[ElOnlyChild]')) {
      throw new Error('[DEBUG] ElOnlyChild triggered', { cause: args[0] })
    }
    _origWarn.apply(console, args as never)
  }
}
```

**定位结果**：stack trace 显示 `<ColumnFilter> → <ElPopover> → <ElTooltip> → <ElPopper> → <ElTooltipTrigger> → <ElPopperTrigger> → <ElOnlyChild>`。

**根因**：[ColumnFilter.vue](file:///F:/items/moldingx/molding-optima/frontend/src/components/ColumnFilter.vue) 第 76-80 行使用了 Vue 2 风格的 `slot="reference"`：

```vue
<el-popover ...>
  <div class="filter-content">...</div>
  <i slot="reference" ...></i>   <!-- Vue 2 写法，导致 default slot 多根 -->
</el-popover>
```

Element Plus 内部 `ElOnlyChild` 检查 default slot 必须是单一根节点，发现多根后报 warning。

### 7.4 ColumnFilter 重构（借炉取暖）

**用户决策**：选择"全部按 [molding-expert-web/ColumnFilter.vue](file:///F:/items/moldingx/molding-expert/molding-expert-web/src/components/ColumnFilter.vue) 重写"，包括升级触发器样式与三态接口设计。

**项目边界**：根据用户偏好（多项目 bug 只修 molding-optima），**只重写 molding-optima 的 ColumnFilter，不同步修改 molding-expert-web**。

#### 7.4.1 改动清单

| 文件 | 改动 | 行数变化 |
|------|------|----------|
| `components/ColumnFilter.vue` | 整体重写：SVG 漏斗图标 + `hasActive` 高亮 + `#reference` slot + `type="link"` | 296 → 442 |
| `components/ColumnFilterHeader.vue` | **删除**（历史残留，0 引用，与 ColumnFilter 功能重复） | -333 |

#### 7.4.2 重写要点

| 设计项 | 重写前 | 重写后 |
|--------|--------|--------|
| 触发器 | `<i class="el-icon-arrow-down">` | SVG 漏斗图标 + 下拉小三角 |
| 激活高亮 | 无 | `.filter-trigger.active` 蓝色（`hasActive` computed） |
| reference 写法 | `<i slot="reference">` (Vue 2) | `<template #reference>` (Vue 3) |
| button type | `type="text"`（已弃用） | `type="link"` |
| 数据接口 | `values`（include only） | `values`（include）+ `exclude`（向后兼容 `Array \| Boolean`） |
| 状态管理 | 简单 v-model `internalValues` | `el-checkbox-group v-model="checked_values"`，watch + created 同步 props |
| 全选/反选 | 不考虑搜索结果 | 仅作用于 `filteredValues`（保留搜索外已选项） |
| emit payload | `{ include, exclude: [] }` | `{ include, exclude }`（兼容 BaseTable `filter-change` 接口） |

#### 7.4.3 保留 molding-optima 约定的部分（区别于 molding-expert-web）

- prop 名 `all_values`（snake_case）保持，BaseTable 调用方式不变
- 不引入 `value_map` / `internal_states`（简化为 el-checkbox-group v-model）
- UI 不暴露三态（数据结构预留，UI 当前只支持 include）

### 7.5 顺手发现的同款问题：ColumnFilterHeader.vue

- `slot="reference"` 同款问题，搜索结果发现是死代码（`grep -r "ColumnFilterHeader"` 只匹配自身 name 声明）
- 用户确认："这其实是历史残留，和 ColumnFilter 已经合并了"
- 已在 7.4.1 中删除

### 7.6 验证清单

- [x] 全局 `grep 'slot="reference"'` 0 命中（`_devRefs/` 备份目录除外）
- [x] 全局 `grep '<el-button\s\+type="text"'` 0 命中（`_devRefs/` 备份目录除外）
- [x] `npm run type-check` RC=0
- [x] 调试 hook（main.ts console.warn throw）已删除
- [x] git status: `D ColumnFilterHeader.vue` + `M ColumnFilter.vue` + 13 个 type="text" 修改文件 + 4 个 injection/auxiliary 重构文件

### 7.7 经验沉淀（memory 列表）

| 类别 | 标题 | 用途 |
|------|------|------|
| `common_pitfalls_experience` | el-popover 用 #reference 模板 slot 避免 ElOnlyChild 警告 | 看到 Vue 2 风格的 `slot="reference"` 时迁移到 `<template #reference>` |
| `common_pitfalls_experience` | PowerShell 正则跨行匹配需 Singleline 选项 | 批量替换多行属性时用 `RegexOptions::Singleline` |
| `common_pitfalls_experience` | Vue 项目相对路径导入失败与死代码清理 | 路径搬迁后兜底扫描 `@/views/equipment\|./components` 残留引用 |
| `development_practice_specification` | 路径搬迁时的 import 扫描策略 | git mv 后必须扫描旧路径 + 相对路径残留 |
| `development_practice_specification` | 前端 Form 组件不绑定 dialog/drawer 容器 | Form 用路由驱动（create/edit/copy mode），不嵌在 dialog/drawer 里 |
| `user_behavior` | 多项目下 bug 修复只关注当前项目 | molding-expert-web 仅作设计参考，不同步修改 |

### 7.8 风险评估

| 项 | 状态 |
|----|------|
| BaseTable 调用 ColumnFilter 接口 | 完全兼容（prop 名 + emit 事件 + payload 形态未变） |
| 已有的 PolymerList 等 9 个 filterable 列 | 应当正常工作（建议手动刷新验证） |
| 用户可能存在的旧 exclude=true 行为 | 向后兼容（视为所有 values 为排除，emit exclude 列表） |
| Vue dev server HMR | 应当自动应用，若有诡异问题硬刷新一次 |
