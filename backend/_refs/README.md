# backend/_refs — 后端开发参考文档

后端（Django）的开发参考资料。

## 📁 目录结构

```
backend/_refs/
├── README.md
├── system/                ← 系统层面：跨模块基础设施
│   ├── algorithm/         ← 物理建模 / 算法重构
│   ├── ai/                ← AI 架构（推理引擎 / 模糊引擎）
│   ├── model/             ← 数据模型
│   └── verify/            ← 验证脚本
└── module/                ← 模块层面：单个业务模块的设计
    ├── process/
    ├── rule/
    └── filecenter/
```

## 📂 system/（25 个文件）—— 跨模块基础设施

### algorithm/（16 篇）—— 物理建模 / 算法重构

| 文件 | 说明 |
|---|---|
| `2026-07-04-algorithm-refactor-roadmap.md` | 算法重构路线图 |
| `algorithm-context-design.md` | 算法上下文设计 |
| `2026-07-04-injection-stroke-physics-design.md` | 注塑行程物理设计 |
| `2026-07-05-cool-time-physics-design.md` | 冷却时间物理设计 |
| `2026-07-05-holding-pressure-physics-design.md` | 保压压力物理设计 |
| `2026-07-05-holding-time-physics-design.md` | 保压时间物理设计 |
| `2026-07-05-holding-velocity-physics-design.md` | 保压速度物理设计 |
| `2026-07-05-injection-pressure-physics-design.md` | 注塑压力物理设计 |
| `2026-07-05-injection-time-physics-design.md` | 注塑时间物理设计 |
| `2026-07-05-injection-velocity-physics-design.md` | 注塑速度物理设计 |
| `2026-07-05-metering-back-pressure-physics-design.md` | 计量背压物理设计 |
| `2026-07-05-metering-pressure-physics-design.md` | 计量压力物理设计 |
| `2026-07-05-metering-speed-physics-design.md` | 计量速度物理设计 |
| `2026-07-05-suckback-decompression-physics-design.md` | 抽吸/释压物理设计 |
| `2026-07-05-temperature-physics-design.md` | 温度物理设计 |
| `2026-07-05-vp-switch-mode-physics-design.md` | VP 切换模式物理设计 |

### ai/（5 篇）—— AI 架构

| 文件 | 说明 |
|---|---|
| `process-ai-architecture-design.md` | 工艺 AI 架构设计 |
| `process-init-rule-design.md` | 工艺初始化规则设计 |
| `fuzzy-engine-migration-design.md` | 模糊引擎迁移设计 |
| `fuzzy-engine-reference.md` | 模糊引擎参考 |
| `infer-input-flattening-design.md` | 推理输入扁平化设计 |

### model/（1 篇）—— 数据模型

| 文件 | 说明 |
|---|---|
| `process-models-design.md` | 工艺数据模型设计 |

### verify/（3 篇）—— 验证脚本

| 文件 | 说明 |
|---|---|
| `verify_parameters_count_fix.py` | parameters_count 字段修复验证 |
| `verify_statistics_service.py` | statistics service 验证 |
| `verify_statistics_url.py` | statistics URL 验证 |

## 📂 module/（22 个文件）—— 模块设计

### process/（8 篇设计文档 + data/ 子目录）

主目录 8 篇设计文档：

| 文件 | 说明 |
|---|---|
| `2026-07-03-refactoring-summary.md` | 工艺重构总结 |
| `2026-09-11-recommendation-tuning-redesign-discussion.md` | 推荐调优重设计讨论 |
| `2026-09-18-optimization-business-flow.md` | 优化业务流程 |
| `init-api-refactor-design.md` | 初始化 API 重构设计 |
| `init-rule-database-migration.md` | 初始化规则库迁移 |
| `process-adjustment-design.md` | 工艺调整设计 |
| `process-data-validator-friendly-error-2026-09-23.md` | 工艺数据校验友好错误 |
| `process-initialization-design-summary-2026-09-22.md` | 工艺初始化设计总结 |

`data/` 子目录（7 个文件 ~3MB）—— **数据迁移快照**：

| 文件 | 说明 |
|---|---|
| `data/Dump20260910.sql` | 2026-09-10 数据库 dump（735 KB） |
| `data/extract_data.py` | 数据提取脚本 |
| `data/group_by_library.py` | 按库分组脚本 |
| `data/rule_keyword_curated.json` | 规则关键词精选 |
| `data/rule_keyword_extracted.original.json` | 规则关键词提取（原始） |
| `data/rule_method_by_library.json` | 规则方法按库 |
| `data/rule_method_extracted.json` | 规则方法提取 |

### rule/（4 篇）

| 文件 | 说明 |
|---|---|
| `rule-if-then-edit-design.md` | 规则 if-then 编辑设计 |
| `rule-keyword-import-design.md` | 规则关键词导入设计 |
| `2026-09-10-rule-keyword-redesign-discussion.md` | 规则关键词重设计讨论 |
| `defect-feedback-none-keyword-design.md` | 缺陷反馈无缺陷关键词设计 |

### filecenter/（2 篇）—— 文件中心

| 文件 | 说明 |
|---|---|
| `FILE_DOWNLOAD_OPTIMIZATION.md` | 文件下载优化 |
| `NGINX_X_ACCEL_REDIRECT_CONFIG.md` | Nginx X-Accel-Redirect 配置 |

## 🎯 分类原则

### system/（系统层面）
- **跨模块**：影响多个业务模块的公共规范、基础设施
- **横向能力**：算法、AI 引擎、数据模型、验证脚本等通用工具
- **典型例子**：`process-models-design.md`、`verify_*.py`

### module/（模块层面）
- **单一模块**：只与某个具体业务模块相关
- **业务功能**：某模块的设计、迁移、重构计划
- **典型例子**：`FILE_DOWNLOAD_OPTIMIZATION.md`（只与 filecenter 相关）

### 跨端 Session 文档的位置
Session 工作记录和交接文档放在 **frontend/_refs/session/**（前端这边），后端开发如需查阅可直接看 `frontend/_refs/session/`。

## 📜 归档记录

- 2026-09-24：从原 `backend/_dev_refs/` 和 `backend/filecenter/_dev_refs/` 合并迁移到 `refs/backend/`
- 2026-09-24：从 `docs/` 迁移 3 个后端相关文档（process）
- 2026-09-24：`refs/backend/` → 移动到 `backend/_refs/`（前后端拆分）
- 2026-09-24：补迁 `backend/process/refs/` 的 7 个主文件到 `module/process/data/`，删除 `_archive/`（按其 README 建议）

## ⚠️ 维护说明

- 原 `backend/_dev_refs/` 和 `backend/filecenter/_dev_refs/` 目录暂未删除，如需清理请先确认所有引用方已切换。
- 新增 dev_ref 文档请按"是否跨模块"放到 `system/<sub>/` 或 `module/<name>/`。
- `process/refs/` 原目录暂未删除（保留 7 个主文件作为追溯）；`_archive/` 已删除（按其 README 建议）。
