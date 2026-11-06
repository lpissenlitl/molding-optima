# 规则挖掘：候选规则审核流 + 落地接线

> 记录规则挖掘闭环「人工环节」的完整设计与验证结果。
> 上游（样本采集、Apriori 挖掘内核、落地翻译器）见代码注释与本文末「相关模块」。
> **状态**：审核流（mC1）、前端入口（mC2）、落地接线（mC3）、样本触发时机（mC4）
> 全部完成并实测通过；规则库租户隔离与经验晋升见**第九节**；
> 规则库「同编码多记录」修复（9.7 已知限制）见**第十节**；
> 专家引擎的库定位口径（平台级）见**第十一节**；
> 专家规则的「平台公共大库 + 租户私库」分层兼容与写权限口径见**第十二节**。

---

## 一、目标与边界

业务诉求原文：

> 候选规则审核流：API + 前端入口（列表/详情/通过/驳回）
> 落地环节：approved → 写入 RuleMethod(source='rule_miner')，让挖掘出的规则真正参与试模推荐
> **这部分业务应该只有管理员可以访问，这是前提**

### 1.1 三层中间态

```
TuningRecord（业务流水，DB）
    ↓ collect（提炼：调机记录 → 样本）
MiningSample（样本池，JSONL 文件语料，append-only）
    ↓ mine（Apriori 关联规则）
MiningRule（候选规则，DB，pending 待审核）   ← 本文档范围
    ↓ approve（审核通过 → 翻译为规则方法）
RuleMethod（生效规则，DB，source='rule_miner'）  ← 参与 FuzzyEngine 推理
```

### 1.2 数据载体判据

**有人参与 → DB；纯机器追加的事实流 → 文件。**

- 候选规则有审核状态机与审核字段 ⇒ DB
- 训练样本池是只写不改的事实流，追加 O(1) 且抗中断 ⇒ JSONL 文件
  （路径 `{STORE_PATH}/{tenant_slug}/mining/samples/company_{company_id}.jsonl`）

### 1.3 权限前提

**审核流全部端点仅管理员可访问**（`require_admin`：`is_superuser` 或 `is_tenant_admin`）。

三道闸：

| 层 | 位置 | 作用 |
|---|---|---|
| 后端 | `views/mining.py` 4 个端点全部 `@method_decorator(require_admin)` | 唯一的强制点 |
| 路由 | `router/index.ts` 两条路由 `meta.adminOnly = true` | 拦「直接输 URL / 收藏链接」 |
| 菜单 | `sidebar/index.vue` `parseMenu` 消费 `meta.adminOnly` | 非管理员**看不到入口** |

---

## 二、mC1 后端审核流

### 2.1 文件

| 文件 | 作用 |
|---|---|
| `backend/process/services/mining_review.py`（新建，373 行） | 审核流 service：列表 / 详情 / 通过 / 驳回 / 落地预览 |
| `backend/process/views/mining.py`（新建，110 行） | 4 个 HTTP 端点，全部 `require_admin` |
| `backend/process/urls.py` | 注册 4 条路由 |
| `backend/process/exceptions.py` | 新增错误码 91-93 |

### 2.2 路由

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/processes/mining-rules/` | 候选规则列表（分页 + 筛选） |
| GET | `/api/processes/mining-rules/<id>/` | 详情（含落地预览、证据样本、审核记录） |
| POST | `/api/processes/mining-rules/<id>/approve/` | 通过（原子地完成审核 + 落地） |
| POST | `/api/processes/mining-rules/<id>/reject/` | 驳回（**必须**填写意见） |

### 2.3 错误码（process 模块 91-99 段）

```python
ERROR_MINING_RULE_NOT_FOUND    = BizErrorCode.create(MOD_PROCESS, 91, "候选规则不存在")
ERROR_MINING_RULE_REVIEWED     = BizErrorCode.create(MOD_PROCESS, 92, "候选规则已审核")
ERROR_MINING_RULE_NOT_LANDABLE = BizErrorCode.create(MOD_PROCESS, 93, "候选规则无法落地")
```

### 2.4 状态机

```
pending ──approve──> approved（同时落地，事务原子）
        └─reject───> rejected（必须带意见）
```

**关键约束**：

1. **通过与落地在同一个事务里** —— 落地失败要整体回滚，状态保持 `pending`，
   不能出现「通过了但没生效」的中间态。
2. **驳回必须写意见** —— 没有理由的驳回对规则挖掘没有反馈价值
   （缺意见 ⇒ `ERROR_REQUIRED_FIELD` / 100003）。
3. **重复审核被拒** —— 非 `pending` 状态再审核 ⇒ `ERROR_MINING_RULE_REVIEWED` / 107092。
4. **审核状态不被重置** —— 挖掘重算指标时（`_persist_rules`）不把已审核规则打回 `pending`，
   避免审核流程被反复打断。

### 2.5 租户隔离口径

```python
def _scope(queryset, company_id, is_superuser):
    if is_superuser and company_id is None:
        return queryset          # 平台超管未接管 ⇒ 看全部
    return queryset.filter(company_id=company_id)
```

⚠️ 平台超管**接管租户后**（`company_id` 非空）一律跟租户走，**但不并入系统演示公司**
—— 候选规则是本公司挖掘产物，混入别家规则会让置信度失真。

⚠️ 落地时的公司解析用**规则自身的公司**（`_resolve_company`）：
`RuleKeyword` 是按公司登记的，用 `None` 算会一条参数都查不到。

### 2.6 序列化

**不用 `to_dict()`** —— 那会吐 `company_id` / `is_deleted` 等内部字段，
且不提供 `defect_text` 这类展示聚合字段。改为自写 `serialize_mining_rule()`。

---

## 三、mC2 前端审核台

### 3.1 文件

| 文件 | 作用 |
|---|---|
| `frontend/src/types/mining.ts`（新建） | `MiningRule` / `MiningDefect` / `MiningChange` / `MiningLandingPreview` 等类型 |
| `frontend/src/api/mining.ts`（新建） | 4 个 API 封装 |
| `frontend/src/views/process/mining/pages/MiningRuleList.vue`（新建，328 行） | 审核台列表页 |
| `frontend/src/views/process/mining/pages/MiningRuleDetail.vue`（新建，398 行） | 详情页（含落地预览） |
| `frontend/src/router/index.ts` | 新增 2 条路由（`adminOnly`） |
| `frontend/src/views/layout/components/sidebar/index.vue` | `parseMenu` 消费 `meta.adminOnly` |
| `frontend/src/permission.ts` | `beforeEach` 拦 `adminOnly` |

### 3.2 页面能力

**列表页**：搜索卡片（规则码/关键词/状态/后件）→ `el-table` → 分页 → 行内「通过/驳回」快捷操作。

**详情页**：
- 规则内容（缺陷项含等级、变更项含前后值与方向、后件标签）
- 指标（support / confidence / lift / 样本数）
- **落地预览**（`landing_preview`）：可落地的规则串 + 被跳过的项及原因
- 审核操作区（通过 / 驳回，驳回强制填意见）
- 审核记录（审核人 / 时间 / 意见 / 落地结果）
- 证据样本（evidence）

### 3.3 响应约定（易踩坑）

`request.ts` 拦截器返回 `response.data`（即 `{status, msg, data}`，**不剥离外层**）
⇒ 调用方需用 `res.data?.items || res.items` 兼容。

### 3.4 `RouteMeta` 无项目级扩展声明

vue-router v4 的 `RouteMeta` 默认是 `Record<string | number | symbol, unknown>`
⇒ 只能用 `meta.adminOnly === true` 判等，不能声明新的 meta 类型字段。

---

## 四、mC3 落地接线

### 4.1 落地翻译三件事

`backend/process/services/mining_landing.py` 负责把挖掘规则翻译成 `RuleMethod`：

| 事项 | 说明 |
|---|---|
| **命名空间转换** | 挖掘样本 `changes[].param` 存**业务名**（`inj_pres_1`）；`RuleKeyword.keyword_name` 存**算法名**（`IP0` / `PP0` / `BT1` / `SHORTSHOT`）⇒ 必须先 `to_algo_name` |
| **变更前值 → 档位** | 用**该字段自身**的 `fuzzy_level` 查档位词表（`LEVEL_WORDS_BY_LVL`），不能套用别的字段的词表 |
| **证据均值 → 动作量** | 受 `action_max_val` / `step` 约束 |

### 4.2 只落地「正向 + 有动作」

- 后件 ∈ `POSITIVE_LABELS` = `{qualified, improved}`
- 必须有参数变更
- 动作方向与当前档位不得相悖

⇒ 实测中 `unqualified` / `worse` 后件的候选规则 **不可落地**（approve 返回 107093，状态保持 pending）。

### 4.3 挖掘库自动参与推理

- 新建挖掘专用规则库 `rule_miner`（`library_type='fuzzy'`、`is_active=True`）
- `select_libraries(None, index)` 取**全部** `is_active` 且 `library_type=='fuzzy'` 的库
  ⇒ `rule_miner` **无需额外接线即被推理层加载**（实测共 11 个库，含 `rule_miner`）
- `get_methods(library_id, defect_code)` 按 `rule_library_id` + `defect_code` + `is_active` 过滤

### 4.4 推理层 `process_parameter` 键是**算法名**

实测：`{'IP0': 50}` 命中挖掘规则；`{'inj_pres_1': 50}` 不命中
⇒ 推理层口径与挖掘规则口径**一致**，无需二次转换。

---

## 五、验证记录

### 5.1 mC1 审核流（13 项实测全通过）

用 Django test Client + 真实 token，全程包在事务里、末尾回滚。

| 场景 | 实测结果 |
|---|---|
| 无 token | HTTP 400 / status 101001 / 「请重新登录」 |
| 普通用户 | HTTP 400 / status 104001 / 「需要管理员权限」 |
| 管理员列表 | HTTP 200 / total=4 |
| `status=pending` 过滤 | total=4 |
| `status=bogus` | HTTP 400 / 100002 / 「status 只能是 pending/approved/rejected」 |
| 详情 | `landing_preview.landable=True`；`rules=[IF SHORTSHOT_medium AND IP0_low THEN IP0_add_10]` |
| approve 不可落地（unqualified 后件） | HTTP 400 / 107093；**status 仍 pending** |
| approve 可落地 | HTTP 200；status=approved；reviewed_by=admin；`landed_rule_method_id=1666`；`RuleMethod(source=rule_miner)` 0→1 |
| 重复 approve | HTTP 400 / 107092 |
| reject 无 note | HTTP 400 / 100003 |
| reject 带 note | HTTP 200 / status=rejected / 意见已存 |
| rejected 后 approve | HTTP 400 / 107092 |
| 超管未接管看全部 | total=4 |
| 回滚后 | RuleMethod=0、RuleLibrary=0、4 条候选规则仍 pending ✓ 数据未污染 |

### 5.2 mC2 前端

- `npm run type-check`（`vue-tsc --noEmit`）→ 无错误
- `npm run build` → 成功，产出 `MiningRuleDetail-*.js` / `MiningRuleList-*.js`

### 5.3 mC3 落地接线（关键结论）

```
[1] approve → RuleMethod RM-202611-00001 / lib=rule_miner / defect=SHORTSHOT
    desc = IF SHORTSHOT_medium AND IP0_low THEN IP0_add_10
[2] select_libraries（未指定库 ⇒ 全量模糊库）共 11 个，含 rule_miner ✓
[3] get_rules(SHORTSHOT/medium) 共 62 条，其中含挖掘规则 ✓
[4] FuzzyEngine.recommend(process_parameter={'IP0': 50})
      → IP0 50.0 → 56.405 (increase)      ★ 落地规则真正参与推理
    FuzzyEngine.recommend(process_parameter={'inj_pres_1': 50})
      → 无 IP0 推荐                        ★ 推理层键是算法名
[5] 回滚后 RuleMethod=0 / RuleLibrary=0 / 4 条候选规则仍 pending ✓
```

### 5.4 全量回归

- `manage.py check` → no issues
- `pytest -q` → **71 passed**（与基线一致，无回归）
- `manage.py mine_rules --company-id 11` → 采集 18 条扫描 / 0 新增修订；4 条规则 / 0 新增 4 更新；
  指标与基线逐条一致：

```
· [SHORTSHOT(medium)]      + [inj_pres_1:increase]  -> improved    support=0.278 confidence=1.000 lift=2.250 evidence=5
· [SHORTSHOT(very_low)]    + [hold_pres_1:decrease] -> unqualified support=0.222 confidence=1.000 lift=4.500 evidence=4
· [FLASH(medium)]          + [-]                    -> improved    support=0.167 confidence=1.000 lift=2.250 evidence=3
· [FLASH(medium)]          + [hold_pres_1:decrease] -> improved    support=0.167 confidence=1.000 lift=2.250 evidence=3
```

---

## 六、mC4 样本触发时机

### 6.1 决策结论

| # | 决策点 | 结论 |
|---|---|---|
| 1 | **触发标签集合** | **与采集器口径一致**：`qualified` / `unqualified` / `improved` / `worse`（`unchanged` 与 `pending` 不触发） |
| 2 | **触发方式** | **定时任务批量跑**：项目无任务队列基础设施（无 celery / redis / rq / apscheduler / threading），挖掘走独立调度入口，由运维侧 cron 拉起 |
| 3 | **触发频率** | **攒够最小样本数再挖**：语料可用样本数 ≥ `min_samples` **且** 语料最新样本 > 上次挖掘水位 |

> ⚠️ 决策 1 修正了旧记忆「result 定稿（qualified 或 unqualified）」的口径 ——
> 现行标签体系已扩展为 5 个，且**实测 4 条候选规则中 3 条后件是 `improved`**；
> 若只按 qualified/unqualified 触发，绝大部分经验采不上。

### 6.2 为什么是「定时」而不是「定稿即挖」

挖掘是 Apriori **全量重算**（每次基于整个语料重算指标）：

- 放在定稿请求里会拖慢响应；
- 更会让业务请求承担挖掘失败的连带风险。

⇒ 定稿请求只负责把经验写进调机流水（`TuningRecord`）；挖掘由独立调度入口承担。

### 6.3 触发标签口径 = 采集器口径（零改动）

标签过滤**已在采集器内**（`mining/collect.py`）：

```python
TuningRecord.objects.filter(result__in=VALID_LABELS)
# + SampleRecord.is_usable()  —— 还要求有变更
```

⇒ **采集层面已不收 `pending` / `unchanged`**，调度层**不重复判断**，避免两处口径漂移。

`TUNING_RESULT_MAP`（`services/tuning.py`，唯一真相源）：

| 前端 `tuning_result` | 落库 `TuningRecord.result` | 可挖 |
|---|---|---|
| `effective` | `improved` | ✓ |
| `ineffective` | `worse` | ✓ |
| `qualified` | `qualified` | ✓ |
| `unqualified` | `unqualified` | ✓ |
| `unchanged` | `unchanged` | ✗ 无方向性 |
| （未评价） | `pending` | ✗ 未定稿 |

### 6.4 触发判据（两条都要满足）

1. **样本数门槛**：语料可用样本数 ≥ `min_samples`
   —— 样本不足时 Apriori 挖不出东西，空跑纯属浪费
   （与挖掘内核用同一个参数，口径一致）。
2. **增量水位**：语料最新 `sample_id` > 上次挖掘水位
   —— 没有新经验进来，指标不会变，重算结果是幂等的。

**水位来源**：候选规则表的 `corpus_cursor` 最大值
（`_persist_rules` 把「产出该批规则时的语料游标」写进每条规则）。
样本 id 零填充（`tr:000000000101`）⇒ 字符串比较等价于数值比较。

⚠️ **已知取舍**：产出 0 条规则时水位不前进（`_persist_rules` 只在有规则时才写库）
⇒ 下次调度会再挖一次。代价是一次幂等的 Apriori 全量重算；
在「每天几十条」的语料量级下可接受。若语料量级上来、空跑成为瓶颈，
再引入独立的「挖掘运行记录表」。

### 6.5 实现

| 文件 | 改动 |
|---|---|
| `backend/process/services/mining.py` | 新增 `get_mining_watermark()` / `should_mine()` / `run_scheduled_mining()`（+221 行） |
| `backend/process/management/commands/mine_rules_scheduled.py` | 新增（97 行）：定时调度命令 |

**调度入口**：

```bash
python manage.py mine_rules_scheduled                     # 全部可访问公司
python manage.py mine_rules_scheduled --company-id 11      # 指定公司（可重复）
python manage.py mine_rules_scheduled --min-samples 20     # 提高触发门槛
python manage.py mine_rules_scheduled --force              # 忽略水位强制挖一次
python manage.py mine_rules_scheduled --dry-run            # 只判定不挖
```

**运维侧 cron**（项目无任务队列基础设施）：

```cron
0 * * * * cd /path/to/backend && python manage.py mine_rules_scheduled
```

### 6.6 关键设计约束

- **采集先于判定**：新定稿的样本只有进了语料，`should_mine` 才看得到
  ⇒ 否则「攒够样本数」的判据永远滞后一轮。
- **逐公司失败隔离**：一个公司的语料损坏 / 指标异常不得中断其余公司
  （`try/except` + 日志；有失败时命令以退出码 1 结束，便于 cron / 监控发现）。
- **只处理可访问公司**：激活且未过期（`Company.is_accessible()`）
  —— 过期租户的语料不该再增长，也不该占用调度时间。
- **审核状态不被重置**：挖掘重算指标时（`_persist_rules`）不把已审核规则打回 `pending`。

### 6.7 验证记录（10 场景全通过）

验收脚本用**临时语料目录**（语料是 append-only 文件写入，不受 DB 事务回滚保护）
+ DB 事务末尾强制回滚 ⇒ 数据零污染。

| # | 场景 | 实测结果 |
|---|---|---|
| 0 | 基线 | 候选规则 4 条 / 调机记录 37 条 |
| 1 | 首次 collect + mine | 4 条规则；水位 = `tr:000000000101` |
| 2 | 调度（无新样本） | **skipped** —「无新样本（指标不会变）」 |
| 3 | 造一条新定稿记录 | id=102（result=improved，带变更） |
| 4 | 调度（**有新样本**） | **mined** —「有新样本」；collected=1；samples=19；规则 6 条（新增 2 / 更新 4）；水位推进到 `tr:000000000102` |
| 5 | 再调度（仍无新样本） | **skipped** |
| 6 | `--min-samples 100` | **skipped** —「样本不足（19/100）」 |
| 7 | `--force` | **mined** —「强制执行」；规则 6 条（新增 0 / 更新 6） |
| 8 | 不存在的公司 id | 公司 0 个 / 失败 0 个，无异常 |
| 9 | 事务内规则数 | 4 → 6（新增 2） |
| 10 | **回滚后核对** | 规则 4 → 4、记录 37 → 37 ✓ **DB 无污染** |

**回归**：`manage.py check` 无问题；`pytest -q` → **71 passed**（与基线一致）。

---

## 七、相关模块索引

| 关注点 | 文件 |
|---|---|
| 采集器 | `backend/process/algorithms/mining/collect.py` |
| 样本契约 | `backend/process/algorithms/mining/contracts.py` |
| 样本池（文件） | `backend/process/algorithms/mining/samples.py` |
| 语料路径解析 | `backend/process/algorithms/mining/provider.py` |
| Apriori 内核 | `backend/process/algorithms/mining/rule_miner.py` / `core.py` |
| 编排 service | `backend/process/services/mining.py` |
| 定时调度 service | `backend/process/services/mining.py`（`should_mine` / `run_scheduled_mining`） |
| 落地翻译器 | `backend/process/services/mining_landing.py` |
| 审核流 service | `backend/process/services/mining_review.py` |
| 审核流视图 | `backend/process/views/mining.py` |
| 挖掘命令行 | `backend/process/management/commands/mine_rules.py` |
| 定时调度命令行 | `backend/process/management/commands/mine_rules_scheduled.py` |
| 候选规则模型 | `backend/process/models/mining.py` |
| 调机记录 / 样本组装 | `backend/process/services/tuning.py` |

---

## 八、后续待办：推理层的租户隔离（当前不做）

> **2026-11-05 更新**：本节待办清单的第 1、2、5 项已在**第九节**完成
> （推理层租户隔离 + 经验晋升）；
> 第 3 项（存量全局规则的归属迁移）**经实测核查无需迁移** ——
> 现存 11 个规则库全部 `owner_type='system'` / `company_id=11`（system_demo），
> 1646 条规则的 `company_id` 与其库 `company_id` **完全一致**（mismatched=0），
> 即存量数据本来就没有“租户私库承载全局生效规则”的情况；
> 第 4 项（`owner_type` ⇔ `company` 一致性校验）**仍不做**（见 9.6）。
> 本节以下内容保留为**决策时的原始依据**，不再作为现状描述。

### 8.1 决策

2026-11-05 决策：**暂不处理**。审核流落地保持固定落本公司租户级 `rule_miner` 库，
**不在审核台暴露「系统级 / 租户级」归属选择**。

### 8.2 现状事实（决策依据）

`RuleLibrary.owner_type` ∈ {`system`, `tenant`}，但归属在三处被用到，看的**不是同一个东西**：

| 维度 | 实际依据 | 决定什么 |
|---|---|---|
| 列表可见性 | `company`（本租户 + system_demo） | 谁能**看见**这个库 |
| 编辑/删除/加规则 | `owner_type` | 谁能**改**这个库 |
| **推理生效性** | **两者都不看** | 这条规则**对谁生效** |

推理层全局加载：

```python
# fuzzy/library/rules.py
get_all_libraries()      -> RuleLibrary.objects.filter(is_deleted=False)           # 全库，不按 company
get_methods(lib_id, code) -> filter(rule_library_id=..., defect_code=..., is_active=True)  # 无 company
# fuzzy/library/contracts.py
class RuleQueryContext:   # <- 无 company_id 字段
```

⇒ **系统级库与租户级库的规则，对所有租户的推理效果完全一样**。

⚠️ 同源的两处一致性问题：

- `add_rule_library` 只校验 `owner_type` 枚举，**不校验**它与 `company` 的对应关系
  （模型注释里的「`owner_type='system'` ⇔ `company=system_demo`」只是注释，不是约束）；
- `update_rule_library` **允许改 `owner_type`**（前端 radio 禁用了，后端没禁）。

### 8.3 为什么现在不开「归属选择」这个口

1. **在当前架构下是「假选择」** —— 选「系统级」与选「租户级」对「谁吃到这条规则」毫无差别，
   真正变的只是「谁能编辑它」⇒ 会让使用者误以为选了系统级就全平台生效。
2. **当前样本量撑不起「通用规则」** —— 实测 4 条候选规则 `confidence` 全为 `1.000`，
   但 `support` 只有 `0.167~0.278`、语料总计 18 条。小样本下 Apriori 置信度必然趋近 1，
   这是样本量不足的产物，不是「规律很确定」⇒ 把单租户经验提升为平台通用规则缺乏依据。
3. **技术底座已就绪，不急于开** —— `land_mining_rule(mining_rule, company_id, library=None)`
   的 `library` 参数就是为此留的；真要做时不必改底层。

### 8.4 待办清单（将来要做时）

| # | 事项 | 落点 |
|---|---|---|
| 1 | `RuleQueryContext` 增加 `company_id` 维度 | `fuzzy/library/contracts.py` |
| 2 | `get_all_libraries` / `get_methods` 按 company 过滤 | `fuzzy/library/rules.py` |
| 3 | **存量全局规则的归属迁移**（现在所有库都是全局生效的） | 数据迁移 |
| 4 | 补 `owner_type` ⇔ `company` 的一致性校验（service 层强制，而非仅注释） | `process/services/rule.py` |
| 5 | 归属选择（或「经验晋升」独立动作）在隔离落地后再开 | `services/mining_review.py` |

⚠️ 第 3 项是前置依赖：**在隔离落地前，已有规则库的规则本来就被所有租户吃到**，
隔离改造必须同时处理存量数据，否则会静默改变现有租户的推理结果。

---

## 九、规则库租户隔离与经验晋升（实施记录）

> 本节是第八节待办的落地：从「推理层不看库归属」到「系统库全平台公用、
> 租户私库只对归属租户可见」，并配套一个「把验证过的经验提到全平台」的晋升动作。

### 9.1 可见性判据（唯一定义处）

```
库可见 ⟺ owner_type == 'system'
       OR (owner_type == 'tenant' AND company_id == 当前租户)
```

| 要素 | 落点 | 口径 |
|---|---|---|
| **谓词实现** | `backend/process/algorithms/fuzzy/library/assembly.py::RuleAssembler.is_library_visible` | **只此一处** —— 数据库来源与文件来源共用，不分叉 |
| 归属信息传递 | `LibraryRecord.owner_type` / `LibraryRecord.company_id`（`library/contracts.py`） | ORM → `LibraryRecord` 由 `adapters.py::to_record` 带出；文件 → dict 由 `from_dict` 带出（两侧口径逐条对齐） |
| 上下文来源 | `RuleQueryContext.company_id`（`library/contracts.py`） | 由 `fuzzy/engine.py` 从推理 context 透传 |
| 过滤收口 | `RuleAssembler.select_libraries(candidates, index, context)` | 两条来源都走这一个函数 |

三条**不改变既有行为**的兜底：

1. **`company_id is None` ⇒ 不过滤**（返回 True）
   —— 第三方集成（`infer_from_provided`）、离线 runner、examples 导出都**没有租户上下文**
   ⇒ 缺上下文时保持现状全量，不静默改变结果。
2. **按「库归属」判定，不按「规则归属」**
   —— 规则的 `company_id` 保留原租户值作溯源（晋升后仍记着来自哪家租户），
   **不参与可见性**。
3. **归属类型缺失 ⇒ 按 system 处理**（`or 'system'`）
   —— 不因字段缺失而静默踢掉整库规则（那会让某个租户的推荐全空）。

### 9.2 实施：三批次（每批独立验收）

| 批次 | 内容 | 主要落点 |
|---|---|---|
| **1（零行为变化）** | 算法层加租户维度，但**没有任何入口传 company_id** ⇒ 全部 `None` ⇒ 行为逐条不变 | `library/contracts.py`、`library/adapters.py`、`library/assembly.py`、`library/files/export.py`、`fuzzy/engine.py` |
| **2（隔离生效）** | 两条算法入口供给 `company_id` | `services/parameter_optimize.py`、`services/condition.py` |
| **3（公共库 + 晋升）** | 公共挖掘规则库 + 晋升 service + API + 前端入口 | `services/mining_landing.py`、`services/rule_promotion.py`（新建）、`views/rules.py`、`urls.py`、前端 3 个文件 |

⚠️ **批次 2 两条入口都要传**，否则同一条规则在不同入口的可见性不一致
—— 不报错，只是结果悄悄不同：

| 入口 | `company_id` 来源 |
|---|---|
| `parameter_optimize.infer()` | `condition_orm.company_id` |
| `condition._build_optimization_context()` | `condition.company_id` |
| `parameter_optimize.infer_from_provided()` | **None**（第三方集成 / 算法试算 / 烟测 ⇒ 无租户上下文 ⇒ 不过滤） |

### 9.3 公共库与晋升

| 事项 | 口径 |
|---|---|
| **公共库** | `library_code='rule_miner_public'`、`owner_type='system'`、`company=system_demo`（**通过 `code` 反查 id，不硬编码**）、`library_type='fuzzy'`、`priority=0` |
| **为何不用 `base`** | `base` 是通用兜底库（被显式指定库时的兜底），语义与“挖掘产出”不同 ⇒ 独立建库 |
| **公共库编码的全局唯一性** | 决策时**要求**全局唯一，理由是：算法侧取库索引时同编码**只保留第一条**（`library/rules.py::get_library_index` 用 `setdefault`）⇒ 公共库若与租户私库同码会被静默挤掉。<br>**2026-11-06 更新**：该前提**已解除**（索引改「同码多记录」，见**第十节**）⇒ 公共库编码现已**不必**全局唯一；此处保留为决策时的原始依据 |
| **晋升语义** | **移动**（不是复制）：规则的 `rule_library` 改指向公共库；原私库**不再保留**该规则 |
| **`company_id` 处理** | **保留原租户值**（溯源）；可见性只看库归属 ⇒ 保留它不造成越权可见 |
| **权限** | 平台超管专用（view 层 `require_superuser` + service 层再校验一次）；公共库是全平台资产，租户不得自助塞入 |
| **可晋升范围** | 仅**租户私库**里的**模糊规则**；已在系统库（含公共库）的规则跳过、专家规则库跳过、不存在的 id 跳过 |

**新增端点**：

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/processes/rule-promotions/` | 规则晋升到公共库（body: `rule_method_ids`） |

**前端入口**：`RuleLibraryDetail.vue` → 规则库详情页 → 规则列表多选 → 「晋升到系统库」
（仅**平台超管 + 租户级私库 + 模糊规则库**时显示；后端 `require_superuser` 是硬门槛）。

### 9.4 验证记录

**批次 1（20 用例对拍全等）**：参照系 = 脚本内逐字复刻的改造前 `select_libraries`。
生产现状（入口不传 company_id）5 个缺陷 + 显式传 company_id=1/9/11 各 5 个缺陷
⇒ **20/20 逐条相等**；三租户可见库集合完全一致（10 个 system 库）。

**批次 2（15 存量对拍全等 + 反例成立）**：

| 项 | 实测 |
|---|---|
| 存量对拍（3 租户 × 5 缺陷） | 15/15 逐条相等（存量库全在 system_demo ⇒ 可见集合不变） |
| 反例（给公司 1 建私库 + 一条规则） | company=1 可见 62 条含新规则（命中）；company=9/11 可见 61 条（不命中） |
| 引擎层效果 | 公司 1 的 IV0 推荐 142.0 vs 公司 9 的 97.9673 ⇒ 不同 |
| 回滚后 | 残留私库 0 条 / 残留规则 0 条 ✓ |

**批次 3（33 项断言全通过）**：

| 验收项 | 实测 |
|---|---|
| 晋升前可见性 | A（租户 1）可见测试私库 + 新规则；B（租户 9）**不可见** |
| 非超管调用 | 抛 `BizException`（“仅平台超管可将规则晋升到公共库”），且**规则未移动** |
| 移动语义 | 规则改挂公共库；`company_id` 保留原租户值；原私库不再保留该规则 |
| 公共库属性 | `owner_type='system'` / `company=system_demo(id=11)` / `library_type='fuzzy'` / 编码正确 / `is_active=True` |
| 晋升后可见性 | A 的可见规则集合**逐条不变**（11 库/62 条 → 12 库/62 条）；B = 原集合 **+ 新规则**（10 库/61 条 → 11 库/62 条） |
| 端到端推理 | A 的推荐列表晋升前后**逐条相等**；B 的推荐因新规则生效而变化 |
| 跳过项 | 重复晋升 / 不存在的 id / 专家规则库 ⇒ 均进 `skipped` 且不移动数据；空 id 列表被拒 |
| 回滚后 | 测试私库 / 测试专家库 / 两条测试规则 / 本次新建的公共库 **全部无残留** ✓ |

**全量回归**：

- `manage.py check` → no issues
- `pytest -q` → **72 passed**（基线 71 + 批次 2 新增的 1 条护栏）
- `npm run type-check`（`vue-tsc --noEmit`）→ 无错误

**唯一的 pytest 护栏**（批次 2 新增，其余改造不新增用例）：

`backend/process/algorithms/fuzzy/library/tests/test_visibility.py`
—— 零 ORM 的独立参照系（直接构造 `LibraryRecord`）：系统库人人可见、私库只对归属租户可见、
无上下文不过滤。

### 9.5 相关模块索引（新增）

| 关注点 | 文件 |
|---|---|
| 可见性谓词（唯一定义处） | `backend/process/algorithms/fuzzy/library/assembly.py` |
| 归属字段契约 | `backend/process/algorithms/fuzzy/library/contracts.py` |
| 归属字段转换（两侧口径） | `backend/process/algorithms/fuzzy/library/adapters.py` |
| 公共挖掘库 | `backend/process/services/mining_landing.py`（`ensure_public_mining_library`） |
| 晋升 service | `backend/process/services/rule_promotion.py`（新建） |
| 晋升视图 | `backend/process/views/rules.py`（`RulePromotionView`） |
| 晋升前端 | `frontend/src/api/rule.ts`、`.../rule/components/RuleMethodSection.vue`、`.../rule/pages/RuleLibraryDetail.vue` |

### 9.6 明确不做的事

| # | 不做什么 | 原因 |
|---|---|---|
| 1 | 不改审核流的落地目标 | 审核通过仍落**本公司私库** `rule_miner` —— “本公司验证过的经验”先在本租户生效，晋升是**另一个独立动作** |
| 2 | 不补 `owner_type` ⇔ `company` 一致性校验 | 存量 11 个库已全部自洽；补校验会拦住“超管建系统库但 company 非 system_demo”这类用法 |
| 3 | 不动存量规则数据 | 实测存量全部在 system_demo 且归属自洽 ⇒ 隔离落地**不改变**任何现有租户的推理结果（已逐条对拍） |
| 4 | 不做晋升的二次审批 | 晋升端点已是平台超管专用；再叠一层审批流会拉长链路且不增加实质约束 |

### 9.7 已知限制（**既存**，非本次改造引入）

> **2026-11-06 更新**：本节描述的缺陷（**同编码规则库只保留第一条**）
> **已修复** —— 实施与验证记录见**第十节**。
> 本节以下内容保留为**决策时的原始依据**，不再作为现状描述。

**同编码规则库只保留第一条**：

```python
# fuzzy/library/rules.py::get_library_index
for lib in RuleQueryService.get_all_libraries():   # 按 id 升序
    record = LibraryRecordAdapter.to_record(lib)
    index.setdefault(record.library_code, record)  # 同码只留第一条
```

而 `ensure_mining_library(company_id)` 是**按公司**建挖掘私库
（`library_code='rule_miner'`）⇒ **多个租户各有一个 `rule_miner`**
⇒ 同码多记录 ⇒ 只有 id 最小的那一个进入推理索引，
其余租户的挖掘规则**静默不参与推理**（不报错，只是结果少了一批）。

| 项 | 实测现状（2026-11-05） |
|---|---|
| 现存 `rule_miner` 私库 | **0 个** ⇒ 尚未触发该问题 |
| 同码重复的库 | **0 组**（11 个系统库编码全部唯一）⇒ 系统库不受影响 |
| 隔离落地后 | 可见性收窄反而**缩小**了它的影响面（原先 A 的挖掘规则会扩散给所有租户，现在不会） |

⚠️ 本次改造**未触碰**该口径（它不在计划范围内，且改了会静默改变现有租户的推理结果）。
若将来多租户都建起挖掘私库，处置方向有二（**均未实施**）：
把私库编码改为**按公司唯一**（如 `rule_miner_c{company_id}`），
或让库索引改用 `(library_code, company_id)` 组合键。

**后续（2026-11-06）**：选了第二种方向并已实施 —— 索引改为
「`library_code` → **同码全部** `LibraryRecord`」，
同时规则归档键从**库编码**改为**库主键**（否则同码两库会互相覆盖）。
详见**第十节**。

---

## 十、规则库「同编码多记录」修复（实施记录）

> 本节是 9.7 已知限制的修复：**规则库索引不再按编码去重**，
> 同一编码下的多个库（分属不同租户）全部保留，并各自参与推理。

### 10.1 缺陷回顾与根因

| 项 | 内容 |
|---|---|
| **现象** | 各租户各建一个 `rule_miner` 挖掘私库 ⇒ 只有主键最小的那一个进入推理索引，其余租户的挖掘规则**静默不参与推理**（不报错，只是推荐少了一批） |
| **直接原因** | `library/rules.py::get_library_index` 用 `setdefault` 建索引 ⇒ 同编码只留第一条 |
| **更深一层** | `methods_by_library` 按**库编码**归档 ⇒ 即便索引保留了同码两库，取规则时后取的那库会**顶掉**前一个（张冠李戴） |
| **为何是合法状态** | `RuleLibrary.library_code` 是**业务分类编码**，模型注释明写跨租户可重复；`add_rule_library` 只校验**同公司内**不重复 ⇒ 跨租户同码是常规可达路径 |
| **为何此前未触发** | 实测现存 11 个库编码全唯一、`rule_miner` 私库 0 个 ⇒ 未触发；租户隔离落地反而**缩小**了它的影响面 |

⚠️ **两处必须一起改**：只改索引而不改归档键 ⇒ 同码且**都可见**的场景
（无租户上下文的全量路径、系统库与租户私库同码）
仍会互相覆盖规则 —— 表现为「别家的规则被算成自己的」，同样不报错。

### 10.2 实施内容

| # | 改动 | 落点 | 口径 |
|---|---|---|---|
| 1 | **索引形状** | `library/contracts.py`、`library/rules.py` | `LibraryIndex = Dict[str, List[LibraryRecord]]`（编码 → **同码全部**记录）；`get_libraries_by_codes` 不再 `qs.first()`，改为 `qs.order_by('id')` 逐条并入 |
| 2 | **规则归档键** | `library/assembly.py`、`library/repository.py`、`library/files/repository.py` | `methods_by_library` 由 `Dict[str, ...]`（库编码）改为 `Dict[int, ...]`（**库主键**）⇒ 同码两库互不覆盖 |
| 3 | **文件来源对称** | `library/files/loader.py`、`library/files/export.py` | 库清单同码全保留；规则文件在**同码多库**时按 `<库码>__<库主键>.json` 分文件（库编码唯一时仍是 `<库码>.json` ⇒ 已导出的数据目录保持有效） |
| 4 | **选库** | `library/assembly.py::select_libraries` | 同码多记录全部进入候选，**由可见性判据裁决**谁该被看到（`is_library_visible` 仍是唯一定义处，未新增第二套判据） |

**取舍**：不动 `library_code` 的可重复性（不改模型、不加唯一约束），
不改 `ensure_mining_library` 的 `rule_miner` 编码 ⇒ **存量数据零迁移**。

### 10.3 验证记录

**A 段：对拍（现状数据零行为变化）** —— 参照系 = 脚本内**逐字复刻**的改造前实现
（索引按编码去重 + 规则按编码归档）。

| 项 | 实测 |
|---|---|
| 对拍组合 | 5 缺陷 × 4 租户上下文（company ∈ {None, 1, 9, 11}）× 3 指定库（None / `R20240516093115` / `base`）= **60 组** |
| 选库与规则 | **60/60 逐条相等**（选库序列 + 规则集签名均相同） |
| 索引条目数 | 改造前后均 **11** 条（现状编码全唯一，每码 1 条） |

**B 段：端到端实证**（两个租户各建一个同名 `rule_miner` 私库，事务内造数后回滚）

| # | 验收项 | 实测 |
|---|---|---|
| B1 | 索引内同码两库都在 | ✅ 2 条，按主键升序 |
| B2 | 公司 1 只命中自己的挖掘规则 | ✅ 含 `IV0_add_2`，**不含**别家的 `IV0_add_7` |
| B2 | 公司 9 只命中自己的挖掘规则 | ✅ 含 `IV0_add_7`，**不含**别家的 `IV0_add_2` |
| B2 | 无租户上下文 ⇒ 两家都在 | ✅（保持现状全量） |
| B3 | **引擎层推荐因各自的挖掘规则而不同** | ✅ 公司 1 → `('IV0', 'increase', 52.0)`；公司 9 → `('IV0', 'increase', 57.0)` |
| B4 | 回滚后零残留 | ✅ 私库 0 条 / 测试规则 0 条 |

**回归**：`manage.py check` → no issues；`pytest -q` → **74 passed**（基线 72 + 本轮新增 2 条护栏）。

**本轮新增的 2 条护栏**（有独立参照系 ⇒ 值得固化）：

| 用例 | 断言 |
|---|---|
| `library/tests/test_visibility.py::test_same_code_libraries_are_kept_and_split_by_owner` | 同码两库都被索引；各自只对归属租户可见；无租户上下文时都可见 |
| `library/files/tests/test_file_source.py::test_same_code_libraries_read_their_own_rule_file` | 同码两库在文件侧各读各的规则文件（`<库码>__<库主键>.json`） |

### 10.4 口径联动

| 位置 | 变化 |
|---|---|
| 9.3「公共库编码的全局唯一性」 | **前提已解除** —— 索引支持同码多记录 ⇒ 公共库编码不必全局唯一 |
| 9.7「同编码规则库只保留第一条」 | **已修复**（本节） |
| 9.6「不动存量规则数据」 | 仍然成立 —— 本轮**零数据迁移**、零行为变化（60 组对拍逐条相等） |

### 10.5 文件来源的运维口径（同码库出现后必读）

`library/files/data/` 是**入库到 git 的历史数据目录**（库编码全唯一 ⇒ 规则文件名一律 `<库码>.json`）。

| 场景 | 要求 |
|---|---|
| 库编码仍然全唯一 | 不用管 —— 文件名口径不变，历史数据目录继续有效 |
| **出现同码库** | **必须重跑导出**：`export.py` 会先清空 `rules/` 目录，再按 `<库码>__<库主键>.json` 分文件写入 |
| 同码库出现但**没重跑导出** | `loader._rules_path` 找不到分文件 ⇒ **回退**到 `<库码>.json` ⇒ 两个同码库会读到**同一份**规则（不报错，只是结果悄悄不同） |

⚠️ 回退是**兼容手段**（让旧数据目录不失效），不是正确路径 ⇒ 同码库一旦出现，
导出工具就是**必须重跑**的那一步。

### 10.6 「显式指定规则库」的语义变化

`RuleQueryContext.rule_library_code` 是**按编码**指定的（不是按库主键）：

| | 改造前 | 改造后 |
|---|---|---|
| 指定编码 X | 只用「X 的**第一条**库」（id 最小） | 用「X 的**全部可见库**」（同码多库都进候选，再由可见性判据过滤） |

- 对**单个租户**通常无变化：租户只看得到自己的库 + 系统库，而同码跨租户时
  别家的库本来就被可见性判据挡掉了。
- 真正会变的是**同码且都可见**的场景（无租户上下文的全量路径、系统库与租户私库撞码）。
- 当前**没有前端入口**（只能靠后端 `process_context_snapshot.rule_library_code` 写入）
  ⇒ 影响面很小，但语义确实变了，先记在这里。

---

## 十一、专家引擎的库定位口径（平台级）

> 口径（2026-11-06 用户明确）：**专家规则是平台级的公共逻辑**；
> **私有库**才与各租户的使用场景有关。

### 11.1 改造前的口径问题

`process/algorithms/expert/rule_matcher.py::InitRuleMatcher._load_from_db` 改造前：

```python
library = RuleLibrary.objects.filter(
    library_code=self.library_code,   # 默认 'expert_rules'
    is_active=True,
).first()                            # ⚠️ 同码取第一条
```

| 问题 | 说明 |
|---|---|
| **同码取第一条** | 靠「id 最小的那条」碰运气 —— 租户建一个同码的专家库、或超管在另一个公司下建同码系统库，都可能被**静默吞掉**（不报错，只是它的专家规则不参与计算） |
| **不表达归属口径** | 「专家规则是平台级」这条口径**只存在于口头**，代码里没有 `owner_type` 约束 ⇒ 现状正确纯属「平台库 id 最小」的运气 |

> ⚠️ **更正一条早前判断**：软删的库**不会**被加载 —— `RuleLibrary.objects` 用的是
> `SoftDeleteManager`（默认过滤 `is_deleted=False`）⇒ 这条不是问题。

### 11.2 改动

| 项 | 改造前 | 改造后 |
|---|---|---|
| 归属 | 不筛选 | **`owner_type='system'`**（缺失/为空按 system 处理，与模糊引擎同一口径） |
| 库类型 | 不筛选 | **`library_type='expert'`**（专家规则只挂在专家规则库上，`add_expert_rule` 即按此校验） |
| 同码多个系统库 | `.first()` 只取一条 | **全部加载并合并**（系数按 key 深度合并、`priority` 决定谁覆盖） |

租户私库（哪怕编码同名）**永不参与**专家引擎 —— 私有库承载各租户自己的使用场景。

### 11.3 验证记录

| 段 | 项 | 实测 |
|---|---|---|
| A 段对拍 | 取到的专家规则逐条相等 | ✅ 现状 8 条，改前改后一致 |
| A 段对拍 | `match()` 命中序列 + 系数输出逐键相等 | ✅ |
| B1 | 租户同码私库的规则不参与专家引擎 | ✅ |
| B2 | 改造前：第二个系统级同码库被**静默丢弃** | ✅（证明缺陷真实存在） |
| B2 | 改造后：同码系统库全部加载并合并 | ✅ |
| B2 | 引擎层：第二个系统库的规则被命中且系数生效 | ✅ |
| B3 | 平台库停用 ⇒ 其规则不再加载 | ✅ |
| B4 | 回滚后零残留、平台库状态复原 | ✅ |

**回归**：`pytest -q` → **74 passed**；专家引擎 smoke 批量（`tests/_verify_expert_smoke.py`）→ **10/10 PASS**。

### 11.4 遗留决策点（已决策 → 见第十二节）

**「建了不生效」的陷阱**：`add_expert_rule` 允许向**租户私库**加专家规则
（只拦 `owner_type='system'` 的库），但专家引擎只读系统级专家库
⇒ 租户在自己专家库里加的规则**永远不会被计算**（不报错，只是没效果）。

| 选项 | 说明 |
|---|---|
| 保持现状 | 靠文档提示 |
| service 层拦截 | 禁止向租户私库新增专家规则（会把「租户有专家规则」这条路彻底封死） |
| ~~引擎也读租户库~~ | 与「专家规则是平台级公共逻辑」的口径冲突，**已否决** |

> ✅ **决策结果**：不封死这条路，也不无脑合并 —— 改为**分层叠加**
> （平台层 + 租户层，租户层叶子级覆盖平台层），并同步放开
> 「公共大库由超管维护」的写权限。详见**第十二节**。

---

## 十二、专家规则的「平台公共大库 + 租户私库」分层兼容

> 起因：第十一节把专家引擎定位为「只读平台级专家库」后，
> 遗留了一个「建了不生效」的陷阱（11.4）。本节给出兼容方案并落地。

### 12.1 产品口径

用户口径原文：

> 专家库是一个公共大库，因为靠用户维护不实际，但是……确实有可能存在用户自己的私有库，
> 有什么兼容的方案可以解决这个问题？

⇒ **公共大库是主形态**（平台维护，租户不维护）；**租户私库是例外形态**
（个别租户有自己的场景）。两个形态**共存**，而不是二选一。

### 12.2 方案：分层叠加（平台层 + 租户层）

```
生效规则集 = 平台层（owner_type='system' 的专家库，全平台共用，**基线**）
           ⊕ 租户层（owner_type='tenant' 且 company_id = 当前租户 的专家库）
```

| 决策点 | 口径 |
|---|---|
| 兼容关系 | **分层叠加**（不封死租户私库，也不无脑合并） |
| 覆盖粒度 | **叶子级 key 覆盖** —— 租户只写要改的那个值，平台同组的其它值全部保留 |
| 租户层取用范围 | **该租户名下全部专家私库**（不限库编码；与模糊引擎「租户私库全部可见」同构） |
| 覆盖方向 | **租户层覆盖平台层** |
| 层与 priority 的关系 | **层优先于 priority** —— 租户规则即使 `priority` 更小也照样覆盖 |
| 无租户上下文 | **只用平台层**（`company_id=None`：第三方集成 / 离线 runner / 烟测），保持现状 |

### 12.3 改动对照

| 层 | 位置 | 改造前 | 改造后 |
|---|---|---|---|
| 加载 | `expert/rule_matcher.py::_load_from_db` | 只认 `owner_type='system'` | 平台层（system）+ 租户层（tenant 且 company 匹配），**租户层后加载** |
| 合并 | `expert/rule_matcher.py::match` | 按 `priority` 升序 | 按 **`(layer, priority)`** 升序 ⇒ 层优先于 priority |
| 构造 | `expert/rule_matcher.py::InitRuleMatcher.__init__` | `(library_code='expert_rules')` | `(library_code=None, company_id=None)`；`library_code` 降为**可选过滤**（默认不限编码） |
| 上下文 | `services/parameter_initialize.py::_infer_kernel` | 无 `company_id` | 新增 `company_id` 形参 ⇒ 透传给 `InitRuleMatcher` |
| 入口 | `services/parameter_initialize.py::infer` | —— | 传入 `company_id`（view 已有 `request.user.company_id`） |

> ⚠️ `infer_from_condition` **不跑推理算法**（Step 3 跳过，直接拷贝源参数）
> ⇒ 无需传 `company_id`；`infer_from_provided`（第三方集成 / 离线）
> **无租户上下文** ⇒ 只用平台层。

### 12.4 写权限口径（配套改动，否则方案 A 落不了地）

排查权限链路时发现三个缺口 —— 不补上，租户层**永远没有生产者**，
公共大库也**无法维护**：

| # | 改造前 | 影响 | 改造后 |
|---|---|---|---|
| ① | service 层对 `owner_type=='system'` **一律拦截**（增/改/删三处） | **超管也不能**往平台公共专家库加/改/删规则 ⇒ 公共大库只能靠 bootstrap 脚本维护（现有 8 条就是这么来的） | **仅平台超管**可写系统级库；非超管仍拒（纵深防御，view 层也是 `require_superuser`） |
| ② | 专家规则 view 全部 `require_superuser` | 租户**无法自助**维护专家规则 | **保持**（本轮口径 X：写权限仍限超管） |
| ③ | `add_rule_library` 强制 `company_id = 调用者公司` | 超管代办建租户库时，库落在超管的公司（系统演示）名下 ⇒ 对目标租户**永远不生效** | 新增 `target_company_id`（**仅超管**）：代办建库直接挂到目标租户名下；且**只能建租户级库**（系统级库归平台） |

配套改动清单：

| 文件 | 改动 |
|---|---|
| `process/services/rule.py` | `add_rule_library` / `update_rule_library` / `delete_rule_library` / `add_expert_rule` / `update_expert_rule` / `delete_expert_rule` 全部加 `is_superuser` 参数（默认 `False`） |
| `process/views/rules.py` | 6 个调用点透传 `is_superuser=getattr(request.user, "is_superuser", False)` |
| `frontend/src/types/rule.ts` | `RuleLibraryCreatePayload` 加 `target_company_id?: number \| null` |
| `frontend/.../RuleLibraryFormDrawer.vue` | 新增「归属租户」下拉（**仅超管 + 新建 + 租户级**时出现，必填） |
| `frontend/.../RuleLibraryTab.vue` | 传 `:is-superuser`、新建时重置 `target_company_id` |

**库编码唯一性**也跟着改了：按**最终归属公司**校验（代办建库后查的是目标租户，
不是超管的公司）。

### 12.5 验证记录

**分层语义**（A 段对拍 + B 段实证，事务内造数据 → 回滚）：

| 段 | 项 | 实测 |
|---|---|---|
| A 段对拍 | 无租户上下文时，取到的规则集合逐字段全等（含顺序） | ✅ |
| A 段对拍 | `match()` 系数逐键相等 + 命中规则序列相等 | ✅ |
| A 段对拍 | 无租户上下文时全部标记为平台层 | ✅ |
| B1 | 租户私库**覆盖**平台同名 key | ✅ |
| B1b | 平台基线值未被污染 | ✅ |
| B2 | **叶子级覆盖**：平台同组其它 key / 其它分组整体保留 | ✅ |
| B3 | **层优先于 priority**（租户 priority=100 < 平台 DEFAULT=9999 仍覆盖） | ✅ |
| B4 | **租户隔离**：别的租户仍是平台值 | ✅ |
| B5 | 无租户上下文 ⇒ 只用平台层 | ✅ |
| B6 / B7 / B8 | 租户私库停用 / 软删 / 规则停用 ⇒ 均不参与 | ✅ |
| B9 | 该租户**所有**专家私库都参与（不限编码） | ✅ |
| B10 | 规则带层标记，租户层排在平台层之后 | ✅ |
| B11 | `_infer_kernel` 已加 `company_id` 形参并透传 | ✅ |
| C1 | 回滚零残留 | ✅ |

**权限矩阵**（P1 系统库 / P2 代办建库 / P3 端到端）：

| 段 | 项 | 实测 |
|---|---|---|
| P1.1–P1.6 | 超管可增/改/删系统库专家规则；非超管三种操作均拒 | ✅ |
| P1.7–P1.9 | 超管可改系统库属性；非超管改 / 删均拒 | ✅ |
| P2.1 | 超管代办建的租户级库**挂在目标租户名下** | ✅ |
| P2.2 | 非超管不可为别的租户代办建库 | ✅ |
| P2.3 | 代办建库仅限租户级库 | ✅ |
| P2.4 | 不传归属租户 ⇒ 落在调用者公司名下 | ✅ |
| P2.5 | 唯一性按**最终归属公司**校验 | ✅ |
| P3.1–P3.4 | 代办建的租户库，其规则在目标租户生效 / 其它租户不受影响 / 平台基线未污染 | ✅ |

**回归**：`pytest -q` → **74 passed**；`manage.py check` → **no issues**；
专家引擎 smoke 批量 → **10/10 PASS**；前端 `npm run type-check` → **EXIT=0**。

### 12.6 遗留与边界

| 项 | 说明 |
|---|---|
| 前端提示 | 租户专家规则会**覆盖**平台同名系数 —— UI 上还没写这句提示（表单里已有「租户级库必须挂到目标租户」的说明） |
| 租户自助 | 本轮口径是「写权限限超管」；若将来要放开租户自助，改动点：`ExpertRuleListView` / `ExpertRuleDetailView` 的 `require_superuser` + service 层按库归属校验 |
| **模糊侧的口径不一致** | 模糊侧 `add_rule_method` **完全不校验库的归属** ⇒ 任何登录用户都能往系统级模糊库加规则方法；专家侧反而比模糊侧严得多。**本轮未动**，另记 |
| 删除系统级库 | 已放开给超管（软删除可恢复）；删了全平台会失去该库的专家规则 —— 需谨慎 |
| `specs.py` 的两条 TODO | 温度类字段条件必填 + `engine.py` 的 `max_set_*` 兜底口径，与本节无关 |
