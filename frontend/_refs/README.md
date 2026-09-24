# frontend/_refs — 前端开发参考文档

前端（Vue 3 + Element Plus）的开发参考资料。

## 📁 目录结构

```
frontend/_refs/
├── README.md
├── system/                ← 系统层面：跨模块规范与基础设施
│   ├── FORM_CODING_STANDARD.md
│   ├── FORM_LAYOUT_DECISION_GUIDE.md
│   ├── MAIN_TS_REFACTOR_PLAN.md
│   └── MAIN_TS_REFACTOR_REPORT.md
└── module/                ← 模块层面：单个业务模块的设计
    ├── mold/
    ├── polymer/
    ├── equipment/
    ├── process/
    └── session/           ← 跨端 Session 工作记录（前后端都能查）
```

## 📂 system/（6 篇）—— 跨模块规范

| 文件 | 说明 |
|---|---|
| `FORM_CODING_STANDARD.md` | 表单组件编码规范 |
| `FORM_LAYOUT_DECISION_GUIDE.md` | 表单布局决策指南 |
| `MAIN_TS_REFACTOR_PLAN.md` | main.ts 重构计划 |
| `MAIN_TS_REFACTOR_REPORT.md` | main.ts 重构报告 |
| `README_BaseSearchForm.md` | 基础搜索表单（BaseSearchForm）规范 |
| `MoldSearchForm_Migration_Example.md` | MoldSearchForm 迁移示例 |

## 📂 module/（14 篇）—— 模块设计

| 模块 | 文件 | 说明 |
|---|---|---|
| mold | `mold/MOLD_FORM_MIGRATION_PLAN.md` | 模具表单迁移计划 |
| mold | `mold/mold-migration-design-summary-2026-09-03.md` | 模具迁移总结 |
| polymer | `polymer/POLYMER_FORM_MIGRATION_PLAN.md` | 塑料表单迁移计划 |
| equipment | `equipment/PLAN_EQUIPMENT_2026-09-09.md` | 设备模块重构计划 |
| process | `process/SEARCH_FORM_MIGRATION_PLAN.md` | 搜索表单迁移计划 |
| process | `process/optimization-infer-design-status-2026-09-22.md` | 优化推理设计状态 |
| process | `process/optimization-records-page-2026-09-23.md` | 优化记录页面 |
| process | `process/process-frontend-param-mapping-atomic-2026-09-23.md` | 工艺前端参数映射（原子化） |
| process | `process/process-get-initial-frontend-integration-2026-09-23.md` | 工艺初始接口前端集成 |
| process | `process/process-get-optimized-frontend-integration-2026-09-23.md` | 工艺优化接口前端集成 |
| session | `session/SESSION_2026-09-08.md` | Session 工作记录 |
| session | `session/SESSION_2026-09-09.md` | Session 工作记录 |
| session | `session/SESSION_2026-09-17.md` | Session 工作记录 |
| session | `session/session-handoff-2026-09-23.md` | Session 交接（前后端都能查） |

## 🎯 分类原则

### system/（系统层面）
- **跨模块**：影响多个业务模块的公共规范、基础设施
- **横向能力**：表单规范、main.ts 重构等

### module/（模块层面）
- **单一模块**：只与某个具体业务模块相关
- **业务功能**：某模块的设计、迁移、重构计划

### session/ 的特殊位置
Session 工作记录和交接文档放在**前端**这边（frontend/_refs/session/），但实际上**前后端协作的产物**。后端开发如需查阅，可直接看这里。

## 📜 归档记录

- 2026-09-24：从原 `frontend/_devRefs/` 和 `frontend/src/_devRefs/` 合并迁移到 `refs/frontend/`
- 2026-09-24：从 `docs/` 迁移 5 个前端相关文档（mold / process / session）
- 2026-09-24：`refs/frontend/` → 移动到 `frontend/_refs/`（前后端拆分）
- 2026-09-24：补迁 `frontend/src/components/_devRefs/` 的 2 个组件规范到 `system/`

## ⚠️ 维护说明

- 原 `frontend/_devRefs/` 与 `frontend/src/_devRefs/` 目录暂未删除，如需清理请先确认所有引用方已切换。
- 新增 dev_ref 文档请按"是否跨模块"放到 `system/` 或 `module/<name>/`。
