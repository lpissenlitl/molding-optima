# Element Plus 表单布局决策指南

> **目的**：基于项目历史踩坑经验，给出"大表单（数据录入）"与"搜索表单（查询筛选）"的布局方案选择依据。
> **创建时间**：2026-09-07
> **适用范围**：molding-optima 前端所有 el-form 页面

---

## 一、核心判断

| 场景 | 推荐方案 | 一句话理由 |
|------|---------|----------|
| **大表单**（数据录入，字段 ≥ 6 或含长字段）| `el-form + el-row + el-col` | 行内精确填满 24 栅格，长短字段混排不浪费 |
| **搜索表单**（字段 ≤ 5 且都是短字段）| `el-form + :inline="true"` | 简洁、字段短时无视觉问题 |

---

## 二、历史踩坑：inline 方案的两个结构性缺陷

### 2.1 label-width 在 el-form 级别共享

inline 模式下 `label-width` 是 `el-form` 级别统一设置。一旦长短字段混排，必然出现以下两种"都不好看"的局面：

```text
label-width: 120px（按长字段设）
├── 项目编号 [input ]     ← 输入区被压缩
├── 项目名称      [input] ← 短字段 label 后面大量留白
└── 项目状态      [select]

label-width: 80px（按短字段设）
├── 产品描述 [textarea...] ← 长字段 label 被截断
└── ...
```

**el-row + el-col 的解决方案**：
- `label-width` 可以统一，但**"输入区宽度"由 `span` 决定**
- 短字段 `span=6`、长字段 `span=12`——输入区宽度自然合理

### 2.2 inline 自动换行导致右侧大量留白

inline 本质是 `flex-wrap: wrap`——浏览器"放不下就换行"，**但不会主动把行填满**：

```text
大屏：
[项目编号] [项目名称] [项目状态] [项目来源] [客户名称] [应用行业] ← 一行 6 个
[量产地] [制作方式] [重要程度] [项目经理] [← 右侧空一大片]

小屏：
[项目编号] [项目名称] [项目状态] [项目来源]    ← 一行 4 个
[客户名称] [应用行业] [量产地] [制作方式]
[重要程度] [项目经理] [← 右侧空一大片]
```

**el-row + el-col 的解决方案**：
- 每行 col 总和精确等于 24，要么自然填满，要么主动用大 `span` 字段占满
- 短字段一行 4 个（span=6），长字段自动换行后占满——不会留空白

---

## 三、推荐列宽档位（24 栅格，el-col span）

| 字段类型 | span | 典型示例 |
|---------|------|---------|
| 短字段（4 列布局默认）| **6** | 编号、状态、日期、来源 |
| 中字段（3 列布局默认）| **8** | 名称、负责人、客户 |
| 长字段（跨 2 列）| **12** | 项目名称、客户全称、合同号 |
| 较长字段（跨 2-3 列）| **16** | 较长名称、详细地址 |
| 整行字段 | **24** | textarea、备注、分组标题 divider |

> **算法支撑**：当前项目 `groupIntoRows(items, { columns: 4 })` 默认 span=6（一行 4 个），`columns: 3` 默认 span=8（一行 3 个）。

---

## 四、项目现状对照

| 文件 | 方案 | 评估 |
|------|------|------|
| `components/BaseSearchForm.vue` | `:inline="true"` | ✅ 所有 SearchForm（7 个）都基于它，字段短，方案合适 |
| `views/project/form.vue` | `el-form + el-row + el-col` | ✅ 大表单范例，已迁移完成 |
| `views/mold/pages/MoldForm.vue` | `:inline="true"`（旧代码）| ⚠️ 字段多且复杂，**待迁移** |
| `views/polymer/pages/PolymerForm.vue` | `:inline="true"`（旧代码）| ⚠️ 同上，**待迁移** |
| `views/equipment/pages/InjectionMachineForm.vue` | `:inline="true"`（旧代码）| ⚠️ 同上，**待迁移** |

---

## 五、迁移建议

1. **大表单优先迁移**到 `el-row + el-col`——`project/form.vue` 已是范例
   - 复用 `src/utils/form-types.ts` 的 `FormItem` / `FormCard` 类型
   - 复用 `src/utils/form-layout.ts` 的 `groupIntoRows` 自动分行算法
2. **保留 inline 仅用于搜索表单**——`BaseSearchForm.vue` 的架构无需变动
3. **mold 表单**由于嵌套结构（`Mold → GatingSystem → Cavity → Gate`），将真正考验 `el-row + el-col` 的灵活度，是迁移计划中的关键里程碑

---

## 六、相关参考

- `src/utils/form-types.ts`：flat items 类型定义
- `src/utils/form-layout.ts`：自动分行算法 `groupIntoRows`
- `src/views/project/form.vue`：迁移范例
- `_devRefs/SEARCH_FORM_MIGRATION_PLAN.md`：搜索表单的统一改造方案