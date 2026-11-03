# expert `runner_type` 契约方案（待拍板）

> **日期**：2026-10-27
> **归属**：模糊推理重构收尾 · expert 基线定性（对应 `2026-10-27-fuzzy-post-refactor-review.md` §11.3 ② / §11.6）
> **状态**：**方案文档，不动代码**（用户已明确：本项先出方案文档）
> **一句话结论**：`runner_type` 被 spec 标为「无条件必填」，但 ORM 是 `null=True` 的自由文本；
> 算法层本身已有**同值兑底**（第 3 级推断），因此**契约降级的数值影响 = 0**；
> 但 `runner_weight` 的条件必填必须**配套改**（`__nin` → `__in` 列举），否则降级不成立。

---

## 1. 问题陈述

### 1.1 现象

新建 / 编辑模具时，若 `GatingSystem.runner_type` 为空（ORM 允许），工艺参数初始化接口**直接报错**：

```
ValueError: mold_info 校验失败: mold_info.runner_type (流道类型（热流道/冷流道/热转冷）)
  → BizException(ERROR_PROCESS_INSUFFICIENT_FIELDS) → HTTP 400
```

### 1.2 事实链

| # | 环节 | 事实 | 位置 |
|---|---|---|---|
| 1 | ORM | `runner_type = models.CharField(null=True, max_length=50, verbose_name="流道类型（热流道/冷流道/热转冷）")` —— **可空、无 `choices`** | `masterdata/models/mold.py:123` |
| 2 | 快照层 | `_build_mold_info_from_snapshot` 按 `MOLD_INFO_SPEC` **全字段提取（含 None）** ⇒ `runner_type=None` 原样直达算法层，**不做任何兜底** | `process/services/parameter_initialize.py:225-284` |
| 3 | spec | `runner_type`：`'condition': '必填'`（**无条件**） | `expert/specs.py`（`MOLD_INFO_SPEC`） |
| 4 | 契约校验 | `not info_dict.get(key)` ⇒ `None` 判缺失 ⇒ 抛 `ValueError` | `algorithms/field_contract.py`（`audit_field_completeness`） |
| 5 | 业务层 | 只捕 `ValueError` ⇒ 转 400 | `parameter_initialize.py:693` |
| 6 | 算法层 | `_get_runner_factor` 有 **4 级兑底**，第 3 级按 `runner_weight` 推断 | `expert/algorithm_engine.py:1057-1078` |

### 1.3 当前库现状（实测）

`GatingSystem` 4 条：`runner_type` **NULL = 0、空串 = 0**，取值 `热流道`×2 / `冷流道`×2
⇒ **当前库安全** —— 但这是**存量恰好填全**，不是**设计上不会为空**。

---

## 2. 影响面

| 维度 | 影响 |
|---|---|
| 功能 | 新建模具（未填流道类型）⇒ 工艺参数接口 400，用户无法继续 |
| 数据 | ORM 允许 NULL ⇒ 任何绕过前端写入的路径（脚本 / 导入 / 迁移）都能造出必炸的数据 |
| 存量 | 当前 4 条都安全 ⇒ 无需数据清洗即可改契约 |
| fuzzy | **零影响**（expert 与 fuzzy 零 import 耦合） |

---

## 3. 候选方案

### 方案 A：ORM 加 `choices` + 字段非空 + 前端强制下拉

| 项 | 内容 |
|---|---|
| 改动 | `runner_type = models.CharField(max_length=50, choices=[...])`（去掉 `null=True`）+ 前端改下拉必选 + 数据迁移 |
| 优点 | 从数据层根治，取值域受控，③（`gate_shape`）也能照此办理 |
| 缺点 | 需要 Django migration + 存量清洗 + 前端联动；改 ORM 字段可空性**影响所有写入路径**（含 `init_demo` 等命令） |
| 风险 | 迁移期间旧数据与新约束的兼容性 |
| 评价 | **长期正解，但不适合单独立项**（与 ③ 强耦合，宜合并做） |

### 方案 B：契约降级 + `runner_weight` 条件必填配套改（**推荐**）

**改动点（2 处，均在 `expert/specs.py`）**：

1. `runner_type`：`'condition': '必填'` → `'condition': '推荐'`（缺失不报错）
2. `runner_weight`：`'condition_when': {'runner_type__nin': ['热流道']}` → `{'runner_type__in': ['冷流道', '热转冷']}`

**为什么第 2 处必须一起改**：
`field_contract.py:74` 的注释明确 —— **None 视为「不在列表中」**。
⇒ 若只降级 `runner_type` 而不动 `runner_weight`：
`runner_type=None` ⇒ `None not in ['热流道']` 为**真** ⇒ `runner_weight` 条件必填**仍然触发**
⇒ 而热流道合法 `runner_weight = 0/None` ⇒ `not get()` 判缺失 ⇒ **仍然 400** ⇒ 降级白做。

改成 `__in: ['冷流道','热转冷']` 后：
`runner_type=None` ⇒ 条件**不成立** ⇒ `runner_weight` 不再必填；
`runner_type='冷流道'/'热转冷'` ⇒ 条件成立 ⇒ **仍然强制要求流道重量**（这正是业务上真正需要的约束）。

**数值影响 = 0（已逐条核验）**：

| 兑底点 | 有 `runner_type` | 无 `runner_type` | 是否同值 |
|---|---|---|---|
| `_get_runner_factor`（保压压力/时间系数） | 查表：热流道 **0.95** / 热转冷 1.00 / 冷流道 **1.05** | 第 3 级推断：`runner_weight==0` → **0.95**（inferred_hot）/ `>0` → **1.05**（inferred_cold） | ✅ **完全同值**（仅 level 标签不同，无断言依赖） |
| `_get_suckback_runner_factor`（松退距离系数） | 查表：热流道 **1.60** / 热转冷 1.15 / 冷流道 1.00 | 第 3 级推断：`==0` → **1.60** / `>0` → **1.00** | ✅ **完全同值** |

⇒ 算法侧**早已具备**「`runner_type` 缺失也能算出正确结果」的能力，契约是**多余的一层**。

**残留风险（必须写进前端提示）**：
`runner_type` 与 `runner_weight` **都**缺失时，`_apply_multi_stage` 的 `runner_weight = prod.get('runner_weight') or 0`
⇒ 按热流道（0）处理 ⇒ 若实际是冷流道：
- 保压/松退因子按热流道取（0.95 / 1.60），而冷流道应为 1.05 / 1.00
- `total_weight = product_weight + 0` ⇒ 少算流道重量 ⇒ `total_len` 偏小 ⇒ `inj_stg` 可能少一段

⇒ 缓解：**前端在用户选择「冷流道 / 热转冷」时，强制要求填写流道重量**（与方案 B 的 `__in` 条件必填形成闭环）。

### 方案 C：给默认值（如缺失即 `'热流道'`）—— **不可取**

| 项 | 说明 |
|---|---|
| 机制 | `runner_type` 缺失 ⇒ 自动填 `'热流道'` |
| 致命处 | 把「**冷流道但漏填**」静默当成热流道 ⇒ 保压系数 1.05→**0.95**（偏 9.5%）、松退距离系数 1.00→**1.60**（偏 60%） |
| 结论 | **静默数值错比 400 更危险** —— 400 是显式失败，数值错是隐式质量事故 ⇒ 排除 |

### 方案 D：不动

维持现状 ⇒ 新建模具漏填即 400。可作为「不做」的兜底选项，但与「模型允许 NULL」的事实长期不自洽。

---

## 4. 推荐

**采用方案 B（契约降级 + `runner_weight` 条件必填改 `__in` 列举）**，理由：

1. **数值影响 = 0**（两条兑底链逐条核验为同值）⇒ 不动任何算法逻辑；
2. **改动面最小**：`expert/specs.py` 两个字段的 `condition` / `condition_when`，零 migration、零数据清洗、零前端强改；
3. **业务约束没有放松**：真正的业务约束（「冷流道/热转冷必须给流道重量」）被 `__in` 列举**更准确地表达**了；
4. **不掩盖问题**：缺失时算法仍按 `runner_weight` 推断并照常出结果，前端可另加提示引导补录。

**与方案 A 的关系**：方案 A（ORM `choices` + 非空）**不与 B 冲突**，可作为后续独立批次；
两者叠加后效果 = 「B 保证接口不炸 + A 保证数据规范」。

---

## 5. 实施步骤（**待确认后执行**）

> 当前状态：**未执行**。以下为拟执行步骤，需用户确认后逐步实施。

| 步 | 动作 | 落点 | 风险 |
|---|---|---|---|
| 1 | `runner_type`：`'必填'` → `'推荐'` | `expert/specs.py::MOLD_INFO_SPEC` | 无（算法有兑底） |
| 2 | `runner_weight`：`condition_when` 由 `{'runner_type__nin': ['热流道']}` 改为 `{'runner_type__in': ['冷流道', '热转冷']}` | 同上 | 需确认「热转冷」是否也要流道重量 |
| 3 | 同步修正 `specs.py` 中 `runner_type` 的 desc（说明缺省时的推断口径） | 同上 | 无 |
| 4 | 回归：expert 全量 pytest（预期 13 failed 不增） + fuzzy 41 passed 不变 | — | — |
| 5 | 查库复验：构造 `runner_type=NULL` 的快照，确认接口从 400 变为正常出参 | — | 需临时脚本，用完即删 |

---

## 6. 验证方式

| 项 | 判据 |
|---|---|
| 契约层 | `audit_field_completeness` 对 `runner_type=None` 不再报缺失；对 `runner_type='冷流道'` 且 `runner_weight` 缺失**仍报缺失** |
| 数值层 | 同一模具在 `runner_type` 有值 / 缺失两种入参下，产出的保压压力、保压时间、松退距离、注射行程**逐项相等** |
| 回归 | `pytest process/algorithms/expert/tests -q`（当前 13 failed / 64 passed）**不得新增失败**；`pytest process/algorithms/fuzzy tests -q` 保持 **41 passed** |

---

## 7. 风险与回滚

| 风险 | 缓解 |
|---|---|
| 「热转冷」是否必须有流道重量未定义 | 实施前确认；若不需要，步骤 2 的列表改为 `['冷流道']` |
| 降级后老数据的 `runner_type` 缺失不再被发现 | 前端列表页加「流道类型未填写」标记（建议项，非本方案范围） |
| 回滚 | 改动仅在 `expert/specs.py` 两处 `condition` / `condition_when` ⇒ 回滚 = 改回原值，**无数据副作用** |
