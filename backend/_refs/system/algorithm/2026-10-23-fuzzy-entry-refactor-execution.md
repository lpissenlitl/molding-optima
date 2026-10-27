# 模糊推理入口重构 · 执行记录

> **日期**：2026-10-23
> **来源**：用户第 16~18 轮对 `backend/process/algorithms/fuzzy/fuzzy_algorithm.py`（686 行）结构的质疑
> **状态**：**E1 + E2 + E3 + E4-a + E4-b + E5 + E6 + E7 + E7-b1 + E7-b2 + E7-c + E7-d + E7-e + E8 + E9 + E10 + E11 + E12 + E13 + E14 + E15 + E16 + E17 + E18 + E19 + E20 + E21 + E22 + E23 + E24 已完成** —— 命名对照表见 §3；故障边界落地见 §2.5；中间态与聚合层见 §2.7；命名契约归位见 §2.8；段号口径修正见 §2.9；**命名契约双向闭合见 §2.10**；**同名消歧（`AlgorithmRecommendation` 改名）见 §2.11**；**算法输入契约见 §2.12**；**契约接线（标准输入参数落地）见 §2.13**；**算法包分层与两层改名见 §2.13.7**；**来源层归位（建 `sources/`）见 §2.13.9**；**`sys.path` 治理见 §2.14**；**`fuzzy_core` 改名讨论存档见 §2.15**；**内核输入契约归位见 §2.16**；**端口归位见 §2.17**；**规则库适配层归位（`sources/` → `library/`）见 §2.18**；**来源层类职责对称化见 §2.19**；**来源层文件级对齐（「查询是查询、管理是管理」）见 §2.20**；**来源轴补刀（来源无关 / 来源特有）见 §2.21**；**端口搬入 `library/` + 改名瘦身见 §2.22**；**`library/` 内部重组（`policy.py` 消亡、`repository.py` 落地）见 §2.23**；**契约层文件改名（`ports.py` → `contracts.py`）见 §2.24**；**`library/` 注释精简见 §2.25**；**`sanity_check.py` 迁入 pytest 后删除见 §2.26**；**契约归属对齐见 §2.27**；**跨包命名对齐见 §2.28**；**双文件改名见 §2.29**；**推荐结果层改名见 §2.30**；**内核论域实例与隶属度类型层清理见 §2.31**；验收见 §5
> **重构原则**：**每轮工作完成后统一跑一次现成验证**，不为每步新写测试脚本（用户第 18 轮明确）
> **靶子文件**：`backend/process/algorithms/fuzzy/fuzzy_algorithm.py`
> **起点 commit**：`06d4a12`（工作区干净）

---

## 0. 一页速览

| 项 | 内容 |
|---|---|
| **触发问题** | 用户三条原话：①「我完全不知道这个类想干什么」②「某一部分有问题，代码就崩了」③「各种命名完全莫名其妙」 |
| **用户诉求** | **流程清晰** > **局部失败不扩散** > **命名可理解** |
| **验收标准** | R1~R4（§1.2）+ 故障隔离三层边界（§1.3） |
| **本轮产出** | **§3 命名对照表**（E1-b）＋ **§2.7 中间态与聚合层**（E3）＋ **§2.8 命名契约归位**（E4-a）＋ **§2.9 段号口径修正**（E4-b）＋ **§2.10 命名契约双向闭合**（E5）＋ **§2.11 同名消歧**（E6）＋ **§2.12 算法输入契约**（E7）＋ **§2.13 契约接线·标准输入参数落地**（E7-b1/b2）＋ **§2.13.7 算法包分层与两层改名**（E7-d）＋ **§2.13.9 来源层归位·建 `sources/`**（E7-e）＋ **§2.14 `sys.path` 治理**（E8）＋ **§2.15 `fuzzy_core` 改名存档**（结论：不改）＋ **§2.16 内核输入契约归位**（E9）＋ **§2.17 端口归位**（E10）＋ **§2.18 规则库适配层归位**（E11，`sources/` → `library/`）＋ **§2.19 来源层类职责对称化**（E12，查库与转换分离）＋ **§2.20 来源层文件级对齐**（E13，「**查询是查询，管理是管理**」：`RuleQueryService` / `RuleRoutingService` ↔ `KeywordQueryService` / `RuleKeywordAdapter`）＋ **§2.21 来源轴补刀**（E14，「**碰 ORM 的 = 来源特有，不碰 ORM 的 = 来源无关**」：新建 `library/policy.py`（`RulePolicy`，零 ORM），`RuleRoutingService` 退回 DB 来源门面）＋ **§2.22 端口搬入 `library/` + 改名瘦身**（E15，`fuzzy/ports.py` 消亡 → `library/ports.py`，`RuleRepository` → **`AlgorithmResourceRepository`** 且瘦身为 2 个取资源方法；3 个加工方法上提内核）＋ **§2.23 `library/` 内部重组**（E16，**`library/policy.py` 消亡**、`library/repository.py` 落地为资源集合层、`library/rules.py` 接收规则串语义）＋ **§2.24 契约层文件改名**（E17，`library/ports.py` → **`library/contracts.py`**，与仓库「契约」词汇统一）＋ **§2.25 `library/` 注释精简**（E18，删设计用语与轮次考古，**代码零改动**）＋ **§2.26 `sanity_check.py` 迁入 pytest 后删除**（E19，顺带修掉 `return bool` 假通过）＋ **§2.27 契约归属对齐**（E20，转换器归位到来源适配层：新增 `RuleAdapter`、消除 `to_fuzzy_dict` 裸 dict 中转层）＋ **§2.28 跨包命名对齐**（E21，`fuzzy/input_specs.py` → `fuzzy/specs.py`，与 `expert/specs.py` 同层同名）＋ **§2.29 双文件改名**（E22，`fuzzy/naming.py` → `fuzzy/field_names.py`、`fuzzy/fuzzy_algorithm.py` → `fuzzy/engine.py`）＋ **§2.30 推荐结果层改名**（E23，`fuzzy/aggregation.py` → `fuzzy/recommendations.py`）＋ **§2.31 内核论域实例与隶属度类型层清理**（E24，`features.py` 只写不读属性 + 死方法 + 假参数清理、`functional.py` 迁移粘贴重复段清理、tri 分支退役与 `MEMBERSHIP_TYPES` 收紧、桶中心抽有名纯函数 + 补 3/5/7/9 档断言） |
| **轮次划分** | E1 命名契约 → E2 故障边界+去 DB 依赖 → E3 中间态类型化+拆聚合 → E4-a 命名契约归位 → E4-b 段号口径修正 → E4-c 抽字段上下文+瘦身+改名 → **E5 命名契约双向闭合** → **E6 同名消歧** → **E7 算法输入契约** → **E7-b1 契约加能力** → **E7-b2 契约接线（切换使用点）** → **E7-c 标准化输入参数层改名** → **E7-d 算法包分层 + 两层改名（input_specs / elements）** → **E7-e 来源层归位（建 `sources/`，按业务 5 层重组）** → **E8 `sys.path` 治理（包目录退出搜索路径）** → **E9 内核输入契约归位（`elements.py` → `fuzzy_core/profiles.py`）** → **E10 端口归位（`RuleRepository` 回到包根 `ports.py`）** → **E11 规则库适配层归位（`sources/` → `library/`，收尾一轮断在半成品的改造）** → **E12 来源层类职责对称化（查库与转换分离）** → **E13 来源层文件级对齐（「查询是查询、管理是管理」：`RuleQueryService` 查询 / `RuleRoutingService` 管理 + 端口门面）** → **E14 来源轴补刀（来源无关 / 来源特有再切一刀：`RulePolicy` 零 ORM 抽出 + 护栏锁死）** → **E15 端口搬入 `library/` + 改名瘦身**（`AlgorithmResourceRepository`，2 方法；加工方法上提内核）→ **E16 `library/` 内部重组**（`policy.py` 消亡；`repository.py` 落地为「算法实际要用的资源」）→ **E17 契约层文件改名**（`library/ports.py` → `library/contracts.py`）→ **E18 `library/` 注释精简**（删设计用语 / 轮次考古，代码零改动）→ **E19 `sanity_check.py` 迁入 pytest 后删除**（消除 `return bool` 假通过）→ **E20 契约归属对齐**（转换器归位来源适配层 + 消除 dict 中转层）→ **E21 跨包命名对齐**（`input_specs.py` → `specs.py`，与 expert 包同名同层）→ **E22 双文件改名**（`naming.py` → `field_names.py`；`fuzzy_algorithm.py` → `engine.py`，落地 §0 早已拍板但一直未执行的「入口改名」）→ **E23 推荐结果层改名**（`aggregation.py` → `recommendations.py`，用户指出「这层是推理完成后格式化输出结果」）→ **E24 内核论域实例与隶属度类型层清理**（`features.py` 只写不读属性 + 死方法 + 假参数清理、`functional.py` 迁移粘贴重复段清理、tri 分支退役与 `MEMBERSHIP_TYPES` 收紧、桶中心抽有名纯函数 + 补 3/5/7/9 档断言） |
| **入口改名** | `fuzzy_algorithm.py` → **`engine.py`** —— ✅ **E22 已执行**（E4 执行时最终确认，本轮落地；类名 `FuzzyEngine` 不动） |
| **不做** | 不动 `llm` / `empirical` / `expert` 三个算法包；不动算法语义（激活度公式、聚合公式、阈值） |
| **不做** | 不新写测试框架；只复用现成 `fuzzy_core/tests` / `backend/tests` / 黄金快照脚本（**E19 起 `sanity_check.py` 已并入 pytest，不再单独跑**） |

---

## 1. 目标与验收标准

### 1.1 用户的核心主张（重构的出发点）

> 「好的代码结构首先流程清晰，即使某个方法的功能没有完全实现，也不影响整体。」
> —— 由此推出两条设计原则：

- **原则 A（流程清晰）**：主流程能从上往下线性读完，每一步的输入输出有名字，每一步失败的后果可见。
- **原则 B（局部失败不扩散）**：故障半径由**设计**决定，而不是由「哪一行恰好有 `try`」决定。

### 1.2 可读性验收标准（R1~R4）

| # | 标准 | 检验方法 |
|---|---|---|
| **R1** | 前 30 行讲清意图 | 打开 `engine.py` 第一屏能说出「输入什么 / 输出什么 / 分几步」 |
| **R2** | 中间状态有名字 | 匿名 dict → dataclass；IDE 可补全、拼错即报错 |
| **R3** | 主流程是一条直线 | `recommend()` 内可见完整 5 步，每步一行，不跳转即可读懂 |
| **R4** | 一个类只做一件事 | `FuzzyEngine` 只做编排；命名契约 / 字段上下文 / 聚合各自独立文件 |

### 1.3 故障隔离三层边界（原则 B 的落地）

```
第 0 层｜编排层 recommend()
  兜底：任何未预期异常 → 记 error + 返回 []，不让算法炸掉整条 condition 链
  关键：必须区分两种「空」
     · 「没有适用规则」 → info  （业务正常，流程继续）
     · 「算法执行失败」 → error （要人看）      ← 现状两者无法区分

第 1 层｜层间（numeric / advisory 互不影响）      现状基本达标
  数值层失败 → 数值层归零，提示层继续
  提示层失败 → 提示层归零，数值层继续

第 2 层｜条目级（单条规则）                       ← 完全缺失，本轮补
  1 条规则算错 → 跳过这 1 条 + 记原因 + 计数，其余 N-1 条正常推理
```

### 1.4 一条关键设计推论

> **安全性不取决于「实现了多少」，取决于「失败了怎么办」。**

实证：现状里「没实现」的部分反而是安全的（`load_rules` 是 `pass`、`TskRuleNet` 抛 `NotImplementedError` 但无人调用）—— 因为没人调用，异常不会发生。
**真正会崩的，是「实现得挺完整但没有边界」的部分**（`get_rules` 直接打 DB，零 `try`）。

---

## 2. 现状基线（E1 起点，HEAD = `06d4a12`）

### 2.1 入口结构现状

```
fuzzy_algorithm.py（686 行）
├─ L44    class FuzzyEngine(AlgorithmBase)
│  ├─ L73-134    3 张类属性数据表（33 + 10 + 1 条）      ← 与"推荐"无关
│  ├─ L139-190   to_business_name()（反向命名映射）        ← 与"推荐"无关
│  ├─ L193-196   __init__（含未用的 self._rule_net）
│  ├─ L198-292   recommend()          ← 唯一入口，95 行
│  ├─ L294-310   is_available() / run()
│  └─ L316-672   9 个私有方法（数据准备 + 格式转换碎活）
├─ L678-681 load_rules()（兼容占位，pass）
└─ L685     AlgorithmRegistry.register('fuzzy', FuzzyEngine())
```

### 2.2 故障边界现状 —— **4 种互不一致的策略**

| 位置 | 策略 | **故障半径** | 等级 |
|---|---|---|---|
| `rule_query_service.py` L204 `RuleMethod.objects.filter(...)` | 裸奔（零 `try`） | 🔴 **整条 optimize 链 500** | 最糟 |
| `fuzzy_algorithm.py` L478 `except Exception → return []` | 整层归零 | 🟠 **整个数值层归零** | 粗暴 |
| `fuzzy_algorithm.py` L555 `except Exception → return out` | 整层归零（文本建议保住） | 🟡 该层归零 | 可接受 |
| `fuzzy_algorithm.py` L380 `except Exception → 猜论域` | 字段级降级 | 🟢 **仅该字段降级** | 最好 |
| `nets.py` 缺元数据字段 | 静默跳过（debug 日志） | 🟡 门控消失，激活度虚高 | 已由 L444 提升到 warning |
| `nets.py` L692 / L717 矩阵越界 | 记 error 后继续 | 🟠 **结果错，无人知道** | 隐患 |
| `macros.resolve_bucket` `ValueError` | `nets.py` L68 兜为 `None` + warning | 🟢 **仅该条** | 条目级雏形 |

**结论**：故障半径**不是设计出来的，是由「哪一行恰好有 `try`」决定的**。

### 2.5 E2 落地后的故障边界（2026-10-23）

| 边界 | 位置 | E2 后的策略 | 状态 |
|---|---|---|---|
| **第 0 层**（编排层） | `recommend()` | 任何未预期异常 → `logger.exception` + 返回 `[]`，**异常止步于算法层** | ✅ E2 |
| **第 0 层**（规则查询） | `_recommend()` 的 `repo.get_rules()` | DB 异常 → `logger.exception`（**error 级，要人看**）+ 返回 `[]`；与「无适用规则」的 **info 级**明确区分 | ✅ E2 |
| **第 1 层**（层间） | `_infer_numeric_layer` / `_infer_advisory_layer` | 一层失败 → 该层归零，另一层继续 | ✅ 原有 |
| **第 2 层**（条目级） | `_precheck_numeric_rules()` | 不可推理的规则（混合结论等）**逐条跳过** + 记入 `self._diagnostics`，其余规则照常推理 | ✅ E2 |
| 字段元数据失败 | `_load_keyword_dicts` | `except Exception` → 降级为推测论域 | ✅ 原有（最好的一处） |
| 矩阵越界 | `nets.py` L692/L717 | 仅 `logger.error` 后继续 ⇒ **结果错** | ❌ 未修（属内核清理） |

### 2.6 E2 的实际收益边界（如实记录，不夸大）

**做到的**：
- `FuzzyEngine` 的**全部数据访问收敛到一个可替换的端口**（`RuleRepository`）⇒ 可注入 `FakeRepository` **完全离线调用**，不连数据库（见 `_dev_refs/_verify_e2_offline.py`）
- 规则库查询失败（DB 挂）不再向上冒泡，**整条 optimize 链不会因模糊算法而 500**
- 一条脏规则不再拖垮整个数值层

**E3 实测纠正（2026-10-23）**：上面那条限制**已经不存在了**——
E2 把 `fuzzy_algorithm.py` 的 ORM 依赖去掉后，`process/algorithms/__init__.py` 的
eager import（fuzzy / llm / empirical 三个引擎）**在无 Django 环境下全部成功**：

```
$ python -c "import process.algorithms.fuzzy.fuzzy_algorithm"   # 不设 DJANGO_SETTINGS_MODULE
IMPORT OK -> <class 'process.algorithms.fuzzy.fuzzy_algorithm.FuzzyEngine'>
```

⇒ 现在是「**导入**与**调用**都可离线」。原 §6 L8 相应关闭。
⚠️ 这条限制是 E2 当时**推测**的（未实测就写进了文档），E3 实测后纠正 ——
记此一笔，避免后续再被当成事实引用。

**降级方向仍不一致（E2 后）**：同样「规则库出问题」这个事实 —— 字段元数据挂了 → **降级继续**（推测论域）；数值推理挂了 → **归零**（该层无结果）；规则查询挂了 → **降级为空推荐**（整条 optimize 链不 500）。三个后果依然毫无关联，只是都不崩了。

**已核实排除**：`parse_rule` / `split_phase`（`parsing.py` L34-102、L179-203）是纯字符串处理，**不抛异常** ⇒ 畸形规则串不会崩。崩源只在 DB 层与推理层。

### 2.7 E3 落地后的中间态与聚合层（2026-10-23）

**改前**：中间态是裸 dict，字段名一词多义；聚合逻辑（95 行）藏在
`FuzzyEngine._merge_layer_results` 里，与「AlgorithmRecommendation 契约转换」混在一起：

```python
{'source': 'numeric', 'param': 'IV0', 'delta': 1.2, 'activation': 0.9, 'rule': '...'}
```

**改后**：

```
RuleAdjustment（逐条） ── aggregate() ──► AggregatedAdjustment（参数级） ── to_recommendations() ──► AlgorithmRecommendation[]
```

| 层 | 位置 | 职责 | 依赖 |
|---|---|---|---|
| 中间态类型 | `recommendations.py`（E23 改名，原 `aggregation.py`） | `RuleAdjustment` / `AggregatedAdjustment` 两个 dataclass | 无 |
| 聚合 | `recommendations.py`（E23 改名，原 `aggregation.py`） | `aggregate()`：同参数累加 + 跨层覆盖 + 分离文本建议 | 无 |
| 契约转换 | `recommendations.py`（E23 改名，原 `aggregation.py`） | `to_recommendations()`：算 delta / confidence / direction | `base.AlgorithmRecommendation` |
| 编排 | `engine.py`（E22 改名，原 `fuzzy_algorithm.py`） | 只负责“调一下” | `recommendations`（E23 改名，原 `aggregation`） |

**收益**：
- `fuzzy_algorithm.py` 776 → **697 行**（-79）
- 中间态字段名彻底类型化：`'param'` → `param_name`、`'source'` → `layer` / `meta_source`
- 公式从“隐含在代码里”变成“显式写在 docstring 里”（`recommended = current + delta * factor`）

⚠️ **N3 被排除的理由（必须记下来）**：
`'lvl'` 不只是“适配层的字典 key”，它同时是**内核 `nets.py` 的输入契约**：

- `nets.py` L254 / L257 / L261：`item['lvl']`（从 keyword_array 读取）
- `nets.py` L276：`f_level=k_dict['lvl']`
- `FuzzyFeature.__init__(f_level=...)` + `self.f_level`（内核内部 6 处引用）

改名为 `level_count` 必须同步改内核 ⇒ 与 E2 确立的「内核不动」边界冲突，
且它对用户提的三个问题（流程清晰 / 失败隔离 / 命名可理解）没有直接贡献
（`lvl` 只出现在一个 dict 的 key 位置，不影响流程可读性）⇒ **降级为遗留项 L9**。

⚠️ **顺带发现：`sanity_check.py` CASE 3 测的是「复刻品」且已经漂移**
原 CASE 3 内嵌了一份 `_merge_layer_results` 的复刻版，但复刻版**漏了
「文本建议分离」这条规则**（真函数有 `if rec.get('advice')` 分支）⇒
真实现改了测试也不会发现。E3 已改为**直接调用真函数**，
并补上了文本建议用例（另外还补了 `to_recommendations()` 层的公式与对外字符串断言，
旧复刻版只测到 merged dict，没测到 AlgorithmRecommendation）。

### 2.8 E4-a 落地后的命名契约层（2026-10-23）

**问题**：命名契约（3 张表 + 反向映射，137 行）是**静态数据**，却挂在 `FuzzyEngine` 类里
—— 读者要在几十个行为方法之间找「这个字段到底叫什么」，
且类名承诺的「引擎」职责被静态配置稀释。

**处置**：新建 `process/algorithms/fuzzy/naming.py`（230 行，零 ORM / 零 Django 依赖）：

| 迁出物 | 新位置 | 说明 |
|---|---|---|
| `FIELD_NAME_ALIAS`（23 条） | `naming.FIELD_NAME_ALIAS` | = 前缀表(10) + 完整表(13) 合并，**顺序与历史一致** |
| `FIELD_INDEX_OFFSET`（10 条） | `naming.FIELD_INDEX_OFFSET` | 分段参数序号偏移 |
| `FAMILY_FIELD_ALIAS`（1 条） | `naming.FAMILY_FIELD_ALIAS` | 整段族映射 |
| `to_business_name()` | `naming.to_business_name()` | 模块级函数（原 classmethod） |

**同时做的一处逻辑收敛（行为不变）**
原 `to_business_name()` 第 3 段是「遍历 `FIELD_NAME_ALIAS`，再用排除法跳过前缀类 key」。
排除法依赖「前缀映射必然同时登记在 `FIELD_INDEX_OFFSET`」这个**口头约定** ——
以后有人加了一条前缀映射却忘了同步偏移表，那条映射就会被当成完整字段名处理，段号整体错位。
现改为**只查完整字段名表**（`FULL_FIELD_ALIAS`），并把「前缀映射」显式独立成表
⇒ 前缀表与偏移表的 key 集合必须一一对应，由 **import 时自检**兜底
（`_validate_tables()` 不一致直接抛 `RuntimeError`，不留到运行期才发现）。

**对外零改动**：`FuzzyEngine` 保留兼容别名与兼容入口 ⇒
`parameter_optimize.py` L245（`FuzzyEngine.to_business_name(...)`）
与 L534-536（读 3 张类属性）**一行不改**。

**等价性验证**（搬移类改动的唯一验收标准 = 行为不变）：
- 三张表**逐条比对（含顺序）**与 HEAD 版完全一致
- `to_business_name()` **262 个输入**（全部算法名 + 变体 + 边界）新旧对拍，结果全一致
- `FuzzyEngine.FIELD_NAME_ALIAS is naming.FIELD_NAME_ALIAS` ⇒ 编排层读到的就是同一份

**规模**：`fuzzy_algorithm.py` 697 → **582 行**（-115）。

### 2.9 E4-b 落地后的段号口径修正（2026-10-23）

**问题（用户指出）**：早期算法里料筒温度是「统一 + 或统一 −」，
所以规则库只出现 `BT`（334 次）而没有段号 ⇒ 用户判断这种表达**不合理**，
要求把 `BT` 并入分段前缀表，让 `brl_temp_1..9` 与 `BT1..BT9` 段号对齐。

**实测依据（跑出来的，不是推理）**

| 项 | 实测事实 |
|---|---|
| `RuleKeyword` | `BT`=料筒温度 **0~50℃**；`BT1`=一段…`BT9`=九段 **150~350℃**；**无 BT0** |
| 规则正文（1646 条） | 前件含 `BT` 的 **169 条**；其中**结论含 BT 的 169 条、结论不是 BT 的 0 条**；`BT1`~`BT9` 仅 3 条 |
| 业务侧字段 | `brl_temp_1..9`（9 段，**无 brl_temp_0**）—— `condition.py` L192-196、`parameter_initialize.py` L398-399/L775 |
| 旧翻译结果 | 族映射使 `brl_temp_1 → BT`（无号）、`brl_temp_2..9 → BT2..BT9` ⇒ **BT1 段号空缺** |
| 内核实测 | `BT` 值 250（0~50 区间外）⇒ `BT_low` / `BT_high` **均不命中** ⇒ 那 169 条规则**恒不激活**（死规则） |
| 内核实测 | `BT1` 值 250（150~350）⇒ `BT1_low` / `BT1_high` **正常命中**（强度 1.0） |

⇒ **两个后果同源**：段号空缺 ⇒ `BT1` 永远拿不到值；
`BT` 拿到 230~250℃ 的料筒温度却按 0~50℃ 判档位 ⇒ 规则恒不命中。段号对齐后一并消失。

**处置**

| 改动 | 内容 |
|---|---|
| `naming.PREFIX_FIELD_ALIAS` | 新增 `"brl_temp": "BT"`（**11 条**） |
| `naming.FIELD_INDEX_OFFSET` | 新增 `"brl_temp": 0`（1-based 同构，不平移） |
| `naming.FULL_FIELD_ALIAS` | 删除 `"brl_temp"`（13 → **12 条**） |
| `naming.FAMILY_FIELD_ALIAS` | **整表删除** —— 族映射这个概念不再存在 |
| `naming.to_business_name()` | 删族分支；`BT1` → `brl_temp_1`；`BT`（无号）→ **None**（退役） |
| `parameter_optimize._normalize_field_name_by_spec()` | 删 `family_spec` 参数与两处族分支（三类映射 → **两类**） |
| `FuzzyEngine.FAMILY_FIELD_ALIAS` | **兼容别名一并删除**（唯一引用方已同步；5 个 dev 诊断脚本同步改） |
| `empirical/hints.py` | 7 处历史写法 `"BT"` → `"BT1"`（语义等价：原意就是「第一段」，写回目标仍是 `brl_temp_1`） |

**对外契约零变化**：`FIELD_NAME_ALIAS` 仍是 **23 条**（前缀 11 + 完整 12），
`FIELD_INDEX_OFFSET` 11 条 ⇒ 编排层键查表翻译口径不变。

**验收**
- 黄金快照：49 样本，`summary`（`count_changed` / `set_changed` / `order_changed` / `delta_changed`）
  与 `only_before` / `only_after` / `changed_delta` **新旧完全一致** ⇒ 推荐集合与顺序零变化；
  逐条 diff 735 处 = **196** 参数名（`BT`→`BT1`）+ **98** 文案（`reason` 内嵌 param_code）+ **441** 处 1e-7 浮点尾数
- **浮点尾数归因**：同代码重跑一次快照 diff = **0**（快照确定性已验证）⇒ 尾数差来自
  「参与加权平均的候选规则链」变化（169 条 BT 规则 → 3 条 BT1 规则，激活度均为 0）
  ⇒ 累加序列不同 ⇒ 尾数不同，**语义无影响**
- `sanity_check` 全绿 / pytest 17 + 5 passed / 离线验证 7 项 PASS

### 2.10 E5：命名契约双向闭合（正向映射归位，2026-10-23）

**触发**：用户第 20 轮 ——「正向应该是接口传入参数时，调用算法时用的，否则前端传入的格式是
`inj_pos_1` 这种，不适配算法的格式，所以肯定是会用到的，只是之前的代码遗漏了」。

**问题的准确定性**（此前表述不够准，此处更正）：

| 说法 | 对不对 |
|---|---|
| 「正向映射没实现」 | ❌ 不对 —— 正向翻译**一直在跑**（住在 service 层 `parameter_optimize._normalize_field_name_by_spec`） |
| 「正向映射被遗漏了」 | ⚠️ 部分对 —— 被遗漏的是**契约层**：`naming.py` 只兑现了反向（算法 → 业务），正向住在 service 层 ⇒ **命名契约被劈成两半** |

⇒ 真正的缺陷不是「少一个函数」，而是**同一份命名规则有两处实现、两个归属**：
契约层一份（反向），编排层一份（正向）。改一处忘另一处 ⇒ 段号错位 ⇒ 规则恒不命中。

**处置**

| 改动 | 内容 |
|---|---|
| `naming.to_algo_name()` | **新增**：业务字段名 → 算法字段名（单名） |
| `naming.to_algo_params()` | **新增**：整份参数字典批量翻译（无对应算法字段的键**原样保留**） |
| `naming._validate_round_trip()` | **新增**：import 时自检 —— 正向译出的算法名，反向必须能译回原名 |
| `parameter_optimize._normalize_field_name_by_spec()` | **删除**（重复实现）⇒ 编排层改调 `naming.to_algo_params` |
| `parameter_optimize._to_business_param_name()` | 改调 `naming.to_business_name`（不再经 `FuzzyEngine` 类属性） |
| `FuzzyEngine.to_algo_name()` / `to_algo_params()` | **新增兼容入口**（与既有 `to_business_name` 同风格）⇒ 外部调用方零改动 |
| 5 个 dev 诊断脚本 | 同步改调 `naming.to_algo_params`（不再从 service 层 import 私有 helper） |

**为什么正向必须存在**：接口入参路径是「前端业务名 → 算法名」这一跳。
前端传 `inj_pos_1`，模糊推理只认 `IL0`；不翻译 ⇒ 引擎取不到该参数 ⇒ 相关规则**恒不命中**
（静默失效，最难查的一类 bug）。

**对拍结论**（独立参照系：旧实现**原样冻结**在 `_dev_refs/_verify_naming_forward_parity.py` 里，
不从生产代码 import，避免“改了源头就没得比”）：

| 输入集合 | 差异 |
|---|---|
| `ProcessParameter` 全部 84 个数值字段（**真实入参集合**） | **0**（逐键一致） |
| 越界段号（`inj_spd_0` / `inj_spd_10` / `brl_temp_10` …） | **0** |
| 前后空白（`' inj_spd_1 '`） | **0**（新实现**不做 trim**，避免两个键塌缩成同一算法名 ⇒ 静默丢值） |
| **裸前缀**（`inj_spd` / `brl_temp` …，11 个） | **11 处有意差异**：旧 → 算法前缀（`inj_spd`→`IV`）；新 → **原样保留** |
| 非字符串键（`None` / `123`） | 旧**抛 AttributeError**；新**原样保留**（健壮性提升） |

**裸前缀为何有意不同**：裸前缀（没有段号）不是有效参数字段（`ProcessParameter` 里不存在），
而旧实现按合并表查表会把它翻译成算法前缀 —— 其中 `brl_temp → BT` 正是 **E4-b 明确退役**的那条
错配路径（料筒温度灌进 0~50℃ 的 `BT` 档位 ⇒ 169 条规则恒不命中）。新契约不复活它：
裸前缀原样保留 ⇒ 引擎匹配不到关键字 ⇒ 等同丢弃（**结果一致，口径更干净**）。

**验收**

- 黄金快照：49 样本 **整棵 JSON 逐条 diff = 0**（vs `_golden_E4b.json`；该脚本走**真实编排层**
  `_compose_algorithm_context` ⇒ 覆盖 service 层改动）
- 往返闭合：70 个翻译字段 **0 处不闭合**（`import` 时自检已覆盖同一条性质）
- `sanity_check` 全绿 / pytest 17 + 5 passed / 离线验证 7 项 PASS

### 2.11 E6：同名消歧 —— `Recommendation` → `AlgorithmRecommendation`（2026-10-23）

**触发**：用户第 22 轮 ——「我看到很多代码用来写 Recommendation，但实际上现在算法输出什么我还没确定，
你建议是先移除 Recommendation 还是保留不动？我是担心改动的过程中会频繁改动 Recommendation」。

**结论：保留，不移除。** 依据：

| 说法 | 判断 |
|---|---|
| 「先移除，等输出形态定了再加」 | ❌ 不该做 —— 它不是「形态猜测」，而是**已落库 + 已给前端消费**的契约 |
| 「输出形态会变 ⇒ 这个类会反复改」 | ⚠️ 混淆了两件事：**业务侧形态**（落点 = service 层 `_build_suggestion_payload` + 前端 schema）与**引擎侧形态**（落点 = `to_dict()` 的 7 个 key，**已定**） |
| 「真实成本是改这个类」 | ⚠️ 真成本在**同名冲突**：`base.Recommendation`（算法契约）与 `models.Recommendation`（ORM 表）同名 ⇒ 编排层只能靠 `as AlgoRecommendation` 别名区分 |

**为什么不移除**：`to_dict()` 的 7 个 key 已是两个下游的既成契约 —— 落库
（`models.Recommendation.recommendations`，JSONField）与前端（suggestion groups）。移除 dataclass 后
这 7 个 key **一个都不会少**，只是「保证齐全」从**一处**散成**三处**（fuzzy / empirical / llm 各写一遍
dict 字面量）⇒ 拼错 key 要到运行时才发现（与 E3 轮 R2「中间态有名字、拼错即报错」相反）。

**「加」与「改/删」的成本差**（这就是降频手段）：

- **加**字段便宜：dataclass 加带默认值字段 + `to_dict()` 加键 + 消费方 `.get()` 兜底；
  落库是 JSONField ⇒ **加键向后兼容**（历史行没新键不影响读）。
- **改/删**已有字段才贵（落库历史数据 + 前端 schema + 3 个引擎同步）。

⇒ 要防的是**破坏性修改**，不是「字段会变」。

**本轮处置：只做改名消歧，不动结构**

| 改动 | 内容 |
|---|---|
| `base.Recommendation` | **改名** `AlgorithmRecommendation`（类定义 + `process/algorithms/__init__.py` 的 `__all__`） |
| 6 个实现方 import | `fuzzy_algorithm` / `aggregation` / `empirical_algorithm` / `llm_algorithm` / `parameter_optimize` / `tests/verify_provided_smoke` 同步 |
| `parameter_optimize` | `as AlgoRecommendation` 别名**取消** —— ORM 侧 `models.Recommendation` 保持原名，两侧不再撞名 |
| 代码内文字引用 | `condition.py` ×2 / `sanity_check.py` ×1 / 3 个 dev 脚本 ×4 同步更正 |
| `to_dict()` 的 7 个 key | **不动**（对外契约） |

**⚠️ 破坏性变更**：对外导出面 `process.algorithms.Recommendation` → `process.algorithms.AlgorithmRecommendation`，
**旧名不再导出**（仓库内零使用已核；外部若 import 旧名需同步改）。

**遗留（未做）**：`to_dict()` 把 `activation_sum` / `rule_count` / **`rule_str`** / `sources` / `advice` 全丢了 ——
service 层 `_extract_rule_refs` 的注释写着「算法侧 Recommendation 无规则引用字段，预留接口」，
而引擎的 `RuleAdjustment.rule_str` **明明有规则串**，只是传不过来。将来若要让「这条建议来自哪条规则」进 UI，
需加一个带默认值的 typed 字段（如 `rule_refs: List[str]`），**不是**用 `meta: Dict[str, Any]` 半结构化载荷
（会丢 IDE 补全，与 R2 反面）。

### 2.12 E7：算法输入契约 —— 数据来源可插拔的锚点（2026-10-23）

**触发**：用户第 24~26 轮 —— ①「`ports.py` 这个叫 ports 我觉得有歧义」②「这些接口的提供方不在 algorithm，
所以定义在外面很奇怪，像一个割裂的文件」③「`rule_query_service` 过于狭窄，可以在 fuzzy 文件夹下设计一个
加载的服务，既可以从数据库加载关键字和规则、也可以从文件加载关键字和规则，这属于将输入数据格式标准化」。

**问题定性（与前几轮不同）**：前几轮是**命名**问题；本轮是**架构**问题 ——
「代码结构给人的感觉是必须查库」。根因：`RuleQueryService` 的 9 个方法里，
**3 个耦合 ORM、6 个是纯业务逻辑**，却在同一个类里：

| 方法 | 性质 |
|---|---|
| `get_libraries` | 查库 + 选库业务 |
| `get_rules` | 查库 + 四级特异级匹配 + 档位过滤 |
| `get_keywords_by_names` | 查库（转发 ORM） |
| `_match_defect_level` / `classify_conclusion_kind` / `split_by_conclusion_kind` / `to_rule_array` / `get_priority_array` / `_product_to_library_codes` | **纯逻辑**（与来源无关） |

⇒ 取数方式与业务逻辑**焊死**：换个来源，6 个纯逻辑方法要么重写、要么每处加分支。

**用户的三处修正（已采纳）**：

1. 契约必须**提前定义**（算法真正消费什么），来源实现是后续的「解析过程」；
2. **library 只是归类维度**，不进标准格式；
3. 命名取 `FuzzyKeyword` / `FuzzyRule` 族。

**命名决策（消歧）**：用户建议的 `FuzzyRule` 与内核 `fuzzy_core.models.nets.FuzzyRule`（L156，
规则串**解析器**）**同名不同物** ⇒ 改用 `FuzzyKeywordSpec` / `FuzzyRuleSpec`：

- `*Spec` = **数据契约**；内核的 `FuzzyFeature` / `FuzzyRule` / `NumTskRule` = **行为体** ⇒ 命名规则自洽；
- 不改内核名（它是 fuzzykit 移植内核的公开类名，6 处引用，且是与上游 fuzzykit 的对应名，改了就失去溯源）。

**本轮产出**：`fuzzy/elements.py`（**零外部依赖**；初版名 `rule_spec.py` → E7-c 改名 `algorithm_inputs.py` → **E7-d 再改名 `elements.py`**，见 §2.13.7）

| 内容 | 说明 |
|---|---|
| `FuzzyKeywordSpec` | `keyword` / `lvl` / `min_val` / `max_val` / `step` / `meta_source` |
| `FuzzyRuleSpec` | `rule_description` / `priority` / `conclusion_kind` / `specificity` / `source_ref` |
| `to_keyword_array` / `to_rule_array` / `to_priority_array` | 标准格式 → 内核输入数组（两数组等长同序） |
| `validate_keyword_specs` / `validate_rule_specs` | 数据来源产出的**关口**（脏数据在边界被拦下，不拖到内核算隶属度时才炸） |

**关键事实：keyword 侧标准格式事实上早已存在**（本轮只是**显式化 + 加校验**，未新增约定）：
`{'keyword','lvl','min_val','max_val','step'}` 在三处完全一致 ——
`adapters.to_fuzzy_dict`（ORM/dict → 格式）、`fuzzy_algorithm._guess_keyword_domains`（推测 → 同格式 + `meta_source`）、
`nets.py` L251-265（消费点，用 `item['lvl']` **下标访问** ⇒ 键名与数量固定，不可增删）。

**method 侧缺口（已定位，本轮未接）**：`to_rule_array` + `get_priority_array` 是**两个平行数组**；
`ResolvedRule.method: Any` 装着 **ORM 实例** ⇒ 全链路**唯一残留的来源耦合点**
（生产代码不读它，仅 dev 脚本 `diag_fuzzy_fix_simulation.py` L227-228 读）。

**本轮不动现有链路**：`adapters.py` / `nets.py` / `rule_query_service.py` / `fuzzy_algorithm.py` **一行未改**
⇒ **行为零变化**。⚠️ 契约层暂时**未接线**（新文件，无生产调用方）—— 接线属下一轮。

**后续（未做）**：

1. ✅ **接线**（**E7-b1 + E7-b2 已完成**，详见 §2.13）：现有链路已改为产出 / 消费标准格式 —— `ResolvedRule` **已退役**，`ResolvedRule.method`（ORM 实例）→ `FuzzyRuleSpec.source_ref`（溯源字符串），**来源耦合点消除**；
2. **数据源抽象**：`RuleSource` 协议 + `DbRuleSource` / `FileRuleSource`；
   库只作**检索维度**（`list_library_codes()` / `load_rules(lib, poly, product, defect)`），
   选库的业务映射留在构建层（不污染数据源）；
3. **本地规则文件**：`fuzzy/rules/`（空壳子包，docstring 已写「模糊引擎规则种子数据子包」）——
   文件格式与字段形状**待定**（不属标准格式的一部分）；
4. **`ports.py` 去留**（未决）：`RuleRepository` 协议是「构建层能力」，`FuzzyRuleSpec` 是「数据契约」，**不同层**；
   E7-b2 已把 `ResolvedRule` 并入 `FuzzyRuleSpec`（重叠消除）⇒ `ports.py` 现只剩
   `RuleQueryContext` + `RuleRepository` 两样东西，**文件命名 / 是否合并仍未决**
   （用户历史质疑：「ports 这个叫法有歧义」「这些放回 service 里就行」）。

### 2.13 契约接线：标准输入参数落地（E7-b1 + E7-b2）

**触发**（用户第 27 轮）：

> 「可以，实施吧，这一层是标准化输入参数」

**这一层的定位**：`elements` 是**算法内部数据对象层**（数据来源 → 算法的中间格式，E7-d 改名见 §2.13.7）—— 数据来源（DB / 本地文件 / 内存）
负责把原始数据**解析**成 `FuzzyKeywordSpec` / `FuzzyRuleSpec`；业务层（选库、特异级匹配、
档位过滤、结论分流）只认这两种类型，**不感知来源**。

#### 2.13.1 两拍走法

| 拍 | 内容 | 性质 |
|---|---|---|
| **E7-b1** | `FuzzyRuleSpec` 扩为 5 字段（`rule_description`/`priority`/`conclusion_kind`/`specificity`/`source_ref`）+ 校验扩充；`adapters.RuleKeywordAdapter.to_keyword_specs()` 解析出口 | **加能力**：不动任何现有调用点 |
| **E7-b2** | `ResolvedRule` **退役**；生产链路改产 / 消费 `FuzzyRuleSpec`；转换逻辑收敛到契约层 | **切换使用点** |

> 关键便利：`FuzzyKeywordSpec` 的字段名与 `adapters.to_fuzzy_dict` 的输出 key
> **天然一一对应**（`keyword`/`lvl`/`min_val`/`max_val`/`step`）⇒ 解析出口零映射成本。

#### 2.13.2 字段映射（退役的 `ResolvedRule` → `FuzzyRuleSpec`）

| 旧 `ResolvedRule` | 新 `FuzzyRuleSpec` | 说明 |
|---|---|---|
| `method: Any`（ORM 实例） | `source_ref: str` | **来源耦合点消除**：装溯源字符串（`RuleMethod:{id}`）而非 ORM 对象 |
| `rule_str: str` | `rule_description: str` | 与内核 `rule_array` 的 key 同名 |
| `specificity: int` | `specificity: int` | 不变 |
| `conclusion_kind: str` | `conclusion_kind: str` | 不变 |
| `priority: float` | `priority: float` | 不变 |

#### 2.13.3 转换逻辑收敛（消除重复实现）

`RuleQueryService.to_rule_array` / `get_priority_array` 原先各自手写一遍转换，
现**只做端口转发**，唯一实现落在 `elements`（E7-d 改名）：

```python
from process.algorithms.fuzzy.elements import (
    FuzzyRuleSpec,
    to_priority_array as specs_to_priority_array,
    to_rule_array as specs_to_rule_array,
)

@classmethod
def to_rule_array(cls, rules: List[FuzzyRuleSpec]) -> List[Dict[str, Any]]:
    return specs_to_rule_array(rules)
```

#### 2.13.4 波及面（12 个文件）

| 层 | 文件 | 改动 |
|---|---|---|
| 契约 | `elements.py`（E7-d 改名） | 数据流图更新（`ResolvedRule` 一环合并进 `FuzzyRuleSpec`） |
| 契约 | `ports.py` | **删** `ResolvedRule`；`RuleRepository` 协议改用 `FuzzyRuleSpec` |
| 构建层 | `services/rule_query_service.py` | 构造改 `FuzzyRuleSpec`；`source_ref=f'RuleMethod:{rm.id}'`；数组转换委托契约层 |
| 编排层 | `fuzzy_algorithm.py` | 7 处类型标注 + 6 处 `r.rule_str` → `r.rule_description` |
| 自检 | `sanity_check.py` | 遗留 mock（**零调用**）标注为「字段已不一致」，namedtuple 改名 `MockRule` |
| 测试 | `tests/test_fuzzy_field_report.py` | `_FakeRule.rule_str` → `rule_description` |
| 验证 | `_dev_refs/_verify_e2_offline.py` | import / 构造 / `FakeRepo.to_rule_array` |
| 诊断 | 5 个 `diag_fuzzy_*.py` | 字段名同步（`level_word_crash` / `fix_simulation` / `pipeline` / `rule_journey` / `field_registry_regression`） |

⚠️ **未动**：`RuleAdjustment.rule_str`（`aggregation.py`）是**另一个类型**的字段（属推理层产出，
带 `activation` / `delta`），不在本轮范围；`rule_str` 作为**领域概念名**（规则字符串）
仍作为函数参数名保留（`parse_rule(rule_str)` / `_match_defect_level(rule_str, ...)`）。

#### 2.13.5 验收

| 项 | 结果 |
|---|---|
| 残留引用扫描 | ✅ 全仓 `ResolvedRule` **0 处**；`.rule_str` **访问点 0 处** |
| 未使用 import（AST 自查） | ✅ **0** |
| sanity_check | ✅ 全绿 |
| pytest | ✅ **22 passed**（17 fuzzy_core + 5 backend/tests） |
| 离线验证 `_verify_e2_offline.py` | ✅ **8 PASS / 0 FAIL** |
| provided_smoke | ✅ PASSED |
| **零依赖（E2 成果保持）** | ✅ `import ...fuzzy.ports` / `import ...fuzzy.fuzzy_algorithm` 后 `process.models` **未进** `sys.modules`，`rule_query_service` **未加载** |
| **端到端（真实 DB）** | ✅ 命中 10 条；类型 `FuzzyRuleSpec`；`source_ref='RuleMethod:20'`；**无 ORM 属性泄漏**（`hasattr(x,'method')` = False）；`to_rule_array` / `get_priority_array` 输出正确 |
| 改动面审计（mtime） | ✅ 本轮仅 13 个文件（12 个代码 + 文档），全在预期清单内 |

**行为零变化**：本轮是**字段改名 + 去来源耦合**，不触碰任何算法语义
（激活度公式、聚合公式、阈值、特异级匹配、档位过滤口径全部原样）。

**新发现的既有问题（非本轮引入）**：`RuleAdjustment.rule_str`（`aggregation.py` L53）是
**只写不读**字段 —— 构造时赋值，`aggregation.py` 从不读取。待后续确认是否删。

#### 2.13.6 命名修正：`rule_spec.py` → `algorithm_inputs.py`（E7-c）

**触发**（用户第 28 轮）：

> 「这个我的本意是想说明这是算法中用到的 keyword 和 method 对象，我们不管是从数据库读取还是从文件读取，最终都会格式化成这里定义的格式，但是当前这个文件名叫 rule_spec，是否符合要求？」

**诊断：`rule_spec` 不符合，三条硬理由**

| # | 理由 | 事实 |
|---|---|---|
| 1 | **名不副实（只覆盖一半）** | 文件里 keyword 侧（`FuzzyKeywordSpec` / `to_keyword_array` / `validate_keyword_specs`）与 rule 侧各占一半；用户本意是 keyword **和** method 两个都覆盖，名字只说了 rule |
| 2 | **与同包 `specs.py` 语义撞车**（最要命） | `fuzzy/specs.py`（已占用，394 行）= **调优入参契约**（`machine_info`/`polymer_info`/`mold_info` 三维字段字典 + 必填等级 + 档位词表），且 `fuzzy/__init__.py` docstring 已把它登记为“spec”的代表；两者**正交**（一个讲上下文入参，一个讲数据格式），读者看到 `rule_spec` 会本能以为它是 `specs` 的近亲 —— 与当初「ports 叫法有歧义」是同类问题 |
| 3 | **漏掉「标准化格式」这个核心语义** | 用户原话是「不管从数据库读取还是从文件读取，最终都会格式化成这里定义的格式」⇒ 重点在**格式**与**算法消费什么**，“rule” 只是内容之一 |

**命名候选对比**

| 候选 | 覆盖 keyword+rule | 体现「标准化格式 / 算法输入」 | 避开 `specs.py` | 结论 |
|---|---|---|---|---|
| **`algorithm_inputs.py`** | ✅ | ✅「算法输入」 | ✅ `specs`=入参契约 / `inputs`=算法消费的数据 | **采用** |
| `algo_inputs.py` | ✅ | ✅ | ✅ | 备选（缩写不如全称清楚） |
| `input_specs.py` | ✅ | ⚠️ | ❌ 仍是 spec 家族 | 否 |
| `contracts.py` | ✅ | ⚠️ | ❌ 撞 `algorithms/field_contract.py` | 否 |
| `models.py` | ✅ | ⚠️ | ❌ 撞内核 `fuzzy_core/models/` | 否 |

**类名 `FuzzyKeywordSpec` / `FuzzyRuleSpec` 不变** —— `*Spec` 后缀的作用是**与内核 `FuzzyRule`（规则串解析器）消歧**，
不是跟文件名一一对应（`field_contract.py` 里也没有 `FieldContract` 类）。

**改动量**：1 次文件重命名 + **5 个 import 路径** + 6 处文字提及。
历史行（§4 / §5 / §7 的 E7、E7-b1 记录）**保留原文件名**（那是当时的事实），本行记录改名。

**验收**：模块路径引用 **0 处**；残留 `rule_spec` 仅剩函数名 `validate_rule_specs`
与错误定位串 `rule_specs[{idx}]`（语义正确，保留）；pytest **22 passed** + sanity 全绿 +
契约层自检（`algorithm_inputs 模块结构正常加载`）+ 离线验证 **8 PASS / 0 FAIL** +
provided_smoke PASSED + **零依赖保持**（ORM 与 `rule_query_service` 均未加载）。

⚠️ **本层还差一块**（用户已定：下轮随来源抽象一起做）：**来源解析层**尚未独立 ——
DB 侧解析现在混在 `adapters.py`（`to_fuzzy_dict` / `to_keyword_specs`），
文件侧解析还不存在。完整形态应为：

```
数据来源 (DB / 文件) ──解析──> FuzzyKeywordSpec / FuzzyRuleSpec   ← elements.py（算法内部数据对象层）
                                       │
                                validate_*_specs（脏数据在边界拦下）
                                       │
                                构建层筛选 / 分流 / 排序
                                       │
                                to_*_array ──> 内核 nets
```

#### 2.13.7 算法包分层与两层改名（E7-d）

**触发**（用户第 29~31 轮，连续三次命名质疑）：

> 第 29 轮：「`algorithm_inputs.py` 1-271 你这个命名很明显有错误，算法输入给人的感觉像是入参
> 但是这个实际是构建算法的模糊关键词和模糊规则，有什么建议？」
>
> 第 30 轮：「我觉得其实统一放在 specs 中没什么问题，这些都是算法内部自己定义的接口和使用方法，你觉得呢？」
>
> 第 31 轮：「我们先讨论清楚各自的职责……原来的 specs，定义了算法的入参格式，我觉得 specs 也挺有歧义；
> 刚刚的 algorithm_inputs，定义的其实是算法内部使用的 class 和 interface，
> 其实我是从算法层面一层层定义服务层，要么将所有外部接口格式定义在一个文件，要么按照服务类型每一层单独定义，
> 所以我才叫停了刚才的合并，因为我发现我把算法内部的对象和入参接口糅合在一起了」

**结论：两个文件都改名，且按「层」分开** —— 用户第 31 轮自己识别出根因：
把**对外接口格式**（边界契约）与**算法内部对象**（对内实现）糅合在一起。

##### 2.13.7.1 fuzzy 包的 6 层分层

| 层 | 职责（一句话） | 载体 | 命名 |
|---|---|---|---|
| **0 · 对外接口** | 算法**对外承诺**的调用格式：调优入参选哪些字段 / 必填到什么等级、缺陷档位合法词、入参校验器 | `specs.py`（E7-d 曾名 `input_specs.py`，**E21 改回**） | `specs` = 对外接口格式 |
| **1 · 编排** | 引擎流程与纯函数：5 步主流程、建议聚合、字段名双向映射 | `engine.py`（E22，原 `fuzzy_algorithm.py`） / `recommendations.py`（E23，原 `aggregation.py`） / `field_names.py`（E22，原 `naming.py`） | 已自解释 |
| **2 · 端口** | 编排层 ↔ 数据源 的接口：`RuleRepository`（Protocol）+ `RuleQueryContext` | `sources/__init__.py`（E7-e 由 `ports.py` 迁入） | 已自解释 |
| **3 · 内部对象** | 来源解析出的**标准素材格式**：`FuzzyKeywordSpec` / `FuzzyRuleSpec` + 转换 + 校验 | `elements.py`（原 `algorithm_inputs.py`） | `elements` = 算法内部数据对象 |
| **4 · 数据源适配** | ORM ↔ 算法结构互转、端口默认实现 | `sources/db.py` / `sources/text.py`（E7-e 由 `adapters.py` + `services/rule_query_service.py` 迁入） | 已自解释 |
| **5 · 内核** | 隶属度计算、规则串解析（fuzzykit 移植，公开类名被外部锁定） | `fuzzy_core/` | 已自解释（锁定） |

**6 层里只有 2 层需要改名**（层 0、层 3）—— 用户「一层层定义」的思路与实际改名需求完全重合。

##### 2.13.7.2 两层为什么不能合并（合并方案已被否决并回退）

第 30 轮曾尝试把层 3 合并进层 0（`specs.py`），**第 31 轮被用户叫停**，理由是
「把算法内部的对象和入参接口糅合在一起了」。复盘确认该判断成立，三条硬理由：

| # | 理由 |
|---|---|
| 1 | **方向相反，不是同类**：`specs.py` = 外部 → 算法的**边界契约**（字段带 `source_model`/`attr_name`/`condition`）；`algorithm_inputs` = 来源 → 算法的**中间格式**（带 `source_ref`/`conclusion_kind`）。用户原话「都是算法内部自己定义的接口**和使用方法**」——「接口」与「使用方法」本就是两件事 |
| 2 | **文件级契约只能表达一种身份**：`__all__` 只有一份、docstring 首句只有一句、git blame 的变更类型只有一种。靠「【一】【二】」分节注释去区分是**约定**，不是**机制** |
| 3 | **对外属性被稀释**：「算法入参契约——调优需要哪些字段（接口格式 + 必填等级）」这句话同时说清了受众 + 内容 + 性质；改成「算法包规格总账」更宽但更空 |

⚠️ 合并尝试已**完整回退**：`specs.py` 恢复为改动前内容（字节级校验通过），未留下任何痕迹。

##### 2.13.7.3 `specs` 歧义的根源与解法

**根源**不是「spec 这个词不好」，而是 **Python 生态里 `spec` 被超载**：
它既指「接口的字段契约」，又指「数据类的字段规格」（dataclass / TypedDict / pydantic Model 都叫 spec）。
本包**同时存在这两类 spec** ⇒ `specs.py` 单独看无法自解释是哪一种。

**解法**：让 spec 词根在整个包里**只指向一层** ——
层 0 = `specs.py`（**E21 由 `input_specs.py` 改回** —— 限定词「入参」当初是为消歧而加，
      而其前提「包内有两类 spec」已随层 3 改名 `elements.py`（`FuzzyKeywordSpec` /
      `FuzzyRuleSpec` → `FuzzyFeature` / `FuzzyRule` / `NumTskRule`）而消失 ⇒ 限定词冗余，
      且造成与 `expert/specs.py` 的**跨包不一致**）；
层 3 = `elements.py`（避开 spec 词根）。

命名规则一句话（**E21 更新**）：**`specs` = 对外接口格式（对外承诺，改它是契约变更）；
`profiles` = 内核输入契约；`elements` = 算法内部数据对象（对内实现，改它只影响本包）**。

##### 2.13.7.4 改动量与验收

| 项 | 结果 |
|---|---|
| 文件重命名 | 2 次（`specs.py` → `input_specs.py`；`algorithm_inputs.py` → `elements.py`） |
| import 路径 | 层 0：5 处（`fuzzy/__init__.py` / `parameter_optimize.py` / `schemas/optimization.py` 注释 / `tests/test_optimize_smoke.py` / `tests/verify_demo_machine_fields.py`）；层 3：6 处（`ports` / `adapters` / `fuzzy_algorithm` / `rule_query_service` / `sanity_check` / `_verify_e2_offline`） |
| 内容改动 | `elements.py` docstring 首句改写 + 措辞统一（「标准输入参数」→「素材格式」）；`fuzzy/__init__.py` docstring 改成分层清单 |
| 公共 API 表面 | `input_specs.__all__` **10 个对外符号零变化**；层 3 符号**不导出**（包内可见） |
| 字节级校验 | `input_specs.py` 与改动前 `specs.py` **字节完全一致**（规范化行尾后仅 2 处差异，均为**前几轮**已做的 `naming.to_algo_params` 说明更新，非本轮引入） |
| 残留扫描 | 代码 `algorithm_inputs` **0 处**；`fuzzy.specs` **0 处**（`expert/` 的 `from .specs` 属专家引擎独立模块，不动）；残留仅函数名 `validate_rule_specs` 与错误定位串 `rule_specs[{idx}]`（语义正确，保留） |
| 零依赖 | `import ...fuzzy.ports` / `import ...fuzzy.fuzzy_algorithm` 后 `process.models` 仍**未进** `sys.modules`，`rule_query_service` 仍**未加载** |
| pytest / sanity | ✅ 22 passed / ✅ 全绿 |
| 离线验证 / provided_smoke | ✅ 8 PASS / 0 FAIL / ✅ PASSED |
| 端到端（真实 DB） | ✅ 命中 10 条；类型 `FuzzyRuleSpec`；`source_ref='RuleMethod:20'`；无 ORM 属性泄漏（`method`/`id`/`rule_content`/`_state` 全 **0 命中**）；`validate_rule_specs` 真实数据**通过**；分流 `{'numeric': 10, 'advisory': 0}` |
| 未使用 import（AST 对照 HEAD） | ✅ 工作区与 HEAD 的未使用 import 集合**完全一致** —— `rule_query_service.Optional` / `optimization.Any` / `test_optimize_smoke` 的 4 个 schema，共 **6 个**，属**既有遗留**（非本轮引入）；`elements.py` / `input_specs.py` 均 **0** |

**行为零变化**：本轮是**纯改名 + 措辞统一**，不触碰任何算法语义。

⚠️ **E21 更正**：本节表格里的 `input_specs.py` 是 **E7-d 当时的文件名**，现已于
**E21 改名为 `specs.py`**（详见 §2.28）—— 历史事实保留，不回改。

⚠️ **仍然未做**（与 §2.12 后续清单一致）：

1. **数据源抽象**（`RuleSource` 协议 + `DbRuleSource` / `FileRuleSource`），库只作**检索维度**；
2. **本地规则文件**：`fuzzy/sources/files/` 空壳（E7-e 由 `fuzzy/rules/` 迁入），文件格式待定；
3. **keyword 侧接线**：`fuzzy_algorithm._load_keyword_dicts` 仍产 dict，未走 `FuzzyKeywordSpec`；
4. ~~**`ports.py` 去留**~~：✅ **E7-e 已决并执行** —— `ports.py` 并入 `sources/__init__.py`（端口协议归位到「读取算法依赖」层，见 §2.13.9）。

#### 2.13.8 讨论存档：`elements` 与 `adapters` 是否合并（**结论：不合并**）

**触发**（用户第 32 轮）：

> 「adapters 我认为是读取并构建内部规则的部分，我在想 `elements.py` 要不要并入 adapters 算了，
> 这一层的职能就是读取和解析关键词和规则」

**结论：暂不合并**（用户「我大概理解你意思，那暂时不动」）。本节存档**讨论依据与实测事实**，未动一行代码。

##### 2.13.8.1 实测事实（2026-10-26）

| # | 事实 | 证据 |
|---|---|---|
| 1 | 编排层**直接** import `elements`，不只经 `ports` | `fuzzy_algorithm.py` import 段同时有 `from ...ports import (` 与 `from ...elements import FuzzyRuleSpec` |
| 2 | `adapters` **顶层** import ORM | `adapters.py` L14 `from process.models.rules import RuleKeyword` |
| 3 | `import adapters` 在**无 `django.setup()`** 时直接抛错 | 实测：`django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.` |
| 4 | **读规则的不是 adapters** | `RuleQueryService.get_rules` 直接查 `RuleMethod.objects.filter(...)` 并直接构造 `FuzzyRuleSpec`，**不经过 adapters** |
| 5 | `RuleMethodAdapter` 是**纯文本双向转换**（规则串 ↔ JSON），不碰 DB | `adapters.py` L21~L191 |
| 6 | `RuleMethodAdapter` **零生产调用方** | 全仓 grep 仅命中定义 + 自检块 + `rule_query_service.py:119` 的历史说明 docstring；参考文档 `2026-10-22-fuzzy-algorithm-internals.md` L262 本就列在「**删**」清单 |
| 7 | `to_keyword_specs` **零生产调用方** | 全仓 grep 仅命中定义 + 自检块（等 keyword 侧接线，见 §2.13.7.4 第 3 项） |
| 8 | 让 `adapters` 变零依赖**技术上可行** | `RuleKeyword` 仅用于类型标注（L232）⇒ 改 `TYPE_CHECKING` 守卫后实测 ORM **未进** `sys.modules` |

##### 2.13.8.2 不合并的三条理由

| # | 理由 | 依据 |
|---|---|---|
| 1 | **合并会摧毁 E2 轮成果**（硬性） | 合并后链路 `fuzzy_algorithm → elements/adapters → ORM` ⇒ 编排层从「能离线 import」变成「直接崩」（事实 1+2+3）。`_verify_e2_offline.py`（8 项 PASS 的回归工具）当场失效 |
| 2 | **`elements` 的零依赖是「来源可插拔」的前提** | 遗留清单第 1、2 项要建 `RuleSource` + `FileRuleSource` + 本地规则文件；**文件来源实现方要 import `FuzzyKeywordSpec`/`FuzzyRuleSpec`** —— 素材格式若住在 `adapters`，文件来源就被迫拖着 DB 适配代码 ⇒ 合并等于把 E7 轮花两拍消除的「来源耦合」装回去 |
| 3 | **职责方向不同**（语义） | `elements` = 「来源 → 算法」的素材格式（来源无关）；`adapters` = 「ORM ↔ 算法结构」的来源适配（来源有关）。且「读取并解析关键词和规则」这个职能横跨**层 4 + 层 5**，把层 3 塞进去等于把层 3 往来源细节里埋 |

> 补充：用户第 31 轮亲手给 `elements` 下的定义正是「**算法内部使用的 class 和 interface**」——
> 2 个 dataclass 是 class，`to_*_array`/`validate_*` 是 interface。合并 = 把这层重新糅进来源实现。

##### 2.13.8.3 讨论暴露的真问题：`adapters` 名不副实（**待办，未执行**）

> ⚠️ **2026-10-26 修正**：本小节原先写「`RuleMethodAdapter` 是死代码，建议删除」，**该结论错误，已作废**。
> 用户第 32 轮指出「这个不一定」，成立。`RuleMethodAdapter` 是**规则定义的结构化表示 ↔ 内核规则串**的双向翻译器，
> **来源无关**；而用户第 3 层明说「从文件读取关键字、规则」——**文件里的规则大概率就是结构化 JSON**，
> 那时 `to_rule_string` 正是文件来源需要的解析器 ⇒ 它不是遗留，而是**为文件来源预留、当前 DB 路径绕过**的能力。
>
> 真正的问题不是「它死了」，而是 **`adapters.py` 按来源相关性劈成了两半**：
> `RuleKeywordAdapter` = **DB 专属**；`RuleMethodAdapter` = **来源无关** ⇒ 两者同住一文件是混装。

`adapters.py` 319 行的实际构成：

| 内容 | 状态 |
|---|---|
| `RuleMethodAdapter`（194 行） | 零生产调用，但**不是死代码** —— 来源无关的规则格式翻译器，为文件来源预留 |
| `RuleKeywordAdapter.to_keyword_specs` | 零生产调用（等 keyword 侧接线） |
| `RuleKeywordAdapter.to_fuzzy_dict` + `get_keywords_by_names` | **唯一活代码**（→ `rule_query_service` → `fuzzy_algorithm.py:310`） |

⇒ 真正的结构问题 = **第 3 层「读取算法依赖」的载体分裂在 3 处，且三个名字互不相干**：
`adapters.py`（裸文件）/ `services/`（名字说「服务」，实际是来源实现）/ `rules/`（名字说「规则数据」，实际预留给文件来源）。
用户第 32 轮的 5 层模型里第 3 层是「读取算法依赖（数据库 / 文件 / 等等）」= **多个来源并列** ⇒ 应住在一个目录、并列排列。

**候选清理方案（已由用户拍板，见 E7-e）**：建 `sources/` 目录，把第 3 层收拢进去。**已于 E7-e 执行完毕**，见 §2.13.9。

#### 2.13.9 来源层归位：建 `sources/` 目录（E7-e）

**触发**（用户第 33 轮）：给出一个**业务视角**的 5 层模型，并指出文件结构需要重新组织：

> ① 定义算法的入参、出参 ② 定义算法内部使用的数据结构
> ③ 读取算法依赖，如从数据库读取关键字、规则，从文件读取关键字、规则等等
> ④ 构建模糊核心 ⑤ 推理

**关键结论：业务 5 层 ≡ 依赖方向 6 层** —— 只有两处差异：
① 用户的模型**多切了「端口」层**（`ports.py`），它可以并入 ③；
② 用户的排序（先说「干什么」，再说依赖方向）更适合当读者第一入口。

**因此确立「逻辑分层 ≠ 物理目录」**：只有第 ③ 层需要目录（多个来源并列），
其余层留在包根 —— `field_names.py`（E22 改名，原 `naming.py`） / `specs.py`（E21 改名，原 `input_specs.py`）被外部直接 import，
搬进子目录 = 改公共路径，收益与风险不成比例。

##### 2.13.9.1 目标结构与搬移对照

| 旧载体 | 新载体 | 说明 |
|---|---|---|
| `fuzzy/ports.py`（97 行） | **`fuzzy/sources/__init__.py`** | 端口协议（`RuleRepository`）+ 查询上下文（`RuleQueryContext`），**零依赖** |
| `fuzzy/adapters.py` 的 `RuleKeywordAdapter` | **`fuzzy/sources/db.py`** | DB 专属：ORM → 内核 dict + `to_keyword_specs()` 解析出口 |
| `fuzzy/adapters.py` 的 `RuleMethodAdapter` | **`fuzzy/sources/text.py`** | **来源无关**：规则结构化表示 ↔ 内核规则串（为文件来源预留） |
| `fuzzy/services/rule_query_service.py`（282 行） | **`fuzzy/sources/db.py`** | `RuleQueryService`（与 `RuleKeywordAdapter` 同属 DB 来源） |
| `fuzzy/rules/`（空壳） | **`fuzzy/sources/files/`** | 文件来源预留 |
| `fuzzy/services/`（目录） | **消失** | 「service」名不副实，它其实是**来源实现** |

**消亡 5 个路径**：`ports.py` / `adapters.py` / `services/` / `rules/` / `services/rule_query_service.py`。

##### 2.13.9.2 两条必须守住的约束

| # | 约束 | 保障方式 |
|---|---|---|
| 1 | **`sources/__init__.py` 绝不 import `sources.db`** | `db` 依赖 Django ORM，包初始化时 import 会把 ORM 拖进编排层 ⇒ 破坏「编排层可脱离 DB 导入与验证」。`fuzzy_algorithm._get_repository()` 采取**延迟导入** |
| 2 | **`sources/text.py` 必须零依赖** | 它翻译的是「规则**长什么样**」而非「规则**从哪来**」，是未来文件来源的解析器 ⇒ 不能被 DB 依赖污染，故独立成文件 |

##### 2.13.9.3 附带修正

- ✅ **`RuleMethodAdapter` 不是死代码**（纠正 §2.13.8.3 的误判）—— 它是**来源无关**的规则格式翻译器，文件来源会用它。
- ✅ **`verify_fuzzy_nested_context.py` 从坏的修成好的**：它 patch 的是 `fuzzy_algorithm.RuleQueryService.get_rules`，
  但 `RuleQueryService` 在 `fuzzy_algorithm` 里是**函数内延迟导入**（模块级无此属性）⇒ 改前必然抛
  `AttributeError`（**既有遗留**，非本轮引入，HEAD 版同样报错）。已把 patch 目标指向真实定义处
  `process.algorithms.fuzzy.sources.db.RuleQueryService.get_rules`（3 处），现 **PASSED**。
- 随 `rule_query_service.py` 删除，**顺带消除**一个既有的未使用 import（`Optional`）。

##### 2.13.9.4 验收

| 项 | 结果 |
|---|---|
| 残留扫描（代码） | ✅ `fuzzy.ports` / `fuzzy.adapters` / `rule_query_service` / `fuzzy.rules` / `fuzzy.services` 各 **0 处**（`process/models/__init__.py` 的 `from .rules import` 是 ORM 模型包自己的，不动） |
| import 路径更新 | ✅ 4 个代码文件 + 9 个 dev 脚本 + 1 个测试文件 |
| 零依赖（E2 成果保持） | ✅ `import fuzzy_algorithm` / `import sources` / `import sources.text` / `import elements` 后 `django` / `process.models` / `sources.db` 均**未进** `sys.modules` |
| 未使用 import（AST 对照 HEAD） | ✅ 4 个新文件均 **0**；`fuzzy_algorithm.py` / `sanity_check.py` 与 HEAD **完全一致**；随旧文件删除消除 `Optional` 1 个 |
| pytest | ✅ **22 passed**（17 fuzzy_core + 5 backend/tests） |
| sanity_check | ✅ 全绿 |
| 离线验证 `_verify_e2_offline.py` | ✅ **8 PASS / 0 FAIL** |
| provided_smoke | ✅ **PASSED**（6/6） |
| `sources/text.py` 自检 | ✅ JSON ↔ 规则串双向正确 |
| 端到端（真实 DB） | ✅ 命中 10 条；类型 `FuzzyRuleSpec`；`source_ref='RuleMethod:20'`；无 ORM 属性泄漏；`validate_rule_specs` 通过 |
| `verify_fuzzy_nested_context.py` | ✅ **PASSED**（3/3，改前是坏的） |

**行为零变化**：本轮是**纯搬移**（只改 import 路径 + docstring 措辞），不触碰任何算法语义。

**仍然未做**（沿用 §2.13.7.4 清单，更新后）：

1. **数据源抽象**：`RuleSource` 协议 + `DbRuleSource` / `FileRuleSource`（**加能力**拍，与搬移分开）；
2. **本地规则文件**：`fuzzy/sources/files/` 空壳，文件格式待定；
3. **keyword 侧接线**：`fuzzy_algorithm._load_keyword_dicts` 仍产 dict，未走 `FuzzyKeywordSpec`；
4. ~~**`fuzzy_algorithm.py` → `engine.py`**（§3.4 P1，在 `fuzzy/` 包内 `fuzzy_` 前缀冗余）~~ ✅ **E22 已执行**；
5. **`__init__.py` docstring 改业务 5 层**（读者第一入口）。

### 2.14 E8：`sys.path` 治理（把「包目录」从搜索路径里拿掉）

**触发**（用户第 35 轮）：

> 「`sys.path.insert(0, FUZZY_DIR)` 这个做法一看就容易带来风险」
> 「那这个实际上是用法错误？」

**结论**：`sys.path.insert` 这个 **API 不算错**（标准做法），错的是**把「包目录」当「顶层包搜索根」**。

> **判据一句话**：`sys.path` 里应该放**包的父目录**（让包以 `a.b.c` 被找到），
> **不能放包目录本身**（那等于宣布「这个目录下每个子模块都是顶层模块」）。

##### 2.14.1 实测事实（2026-10-26）

| # | 事实 | 证据 |
|---|---|---|
| 1 | `find_spec('core')` → **None** | 当前改名不会立刻撞名 |
| 2 | `find_spec('sources')` → **命中 `fuzzy/sources/__init__.py`** | `fuzzy/` 目录进了 `sys.path` ⇒ 子模块泄漏成顶层名 |
| 3 | `find_spec('elements')` → **命中 `fuzzy/elements.py`** | 同上 |
| 4 | `import fuzzy` → `ImportError: attempted relative import beyond top-level package` | `fuzzy/specs.py:39` 的 `from ..field_contract import` 越界 |
| 5 | 顶层裸导入 `from fuzzy_core...` 共 **27 处** | `sanity_check.py` 13 + 内核测试 6 + dev 脚本 8 |
| 6 | pytest prepend 插入的是 **`backend/`**（`backend/` 无 `__init__.py`，而 `process/`→`tests/` 全有） | ⇒ 顶层 `import fuzzy_core` 在 pytest 下**失败** ⇒ 测试文件里的 `sys.path.insert` 是**必要的** |

##### 2.14.2 两类风险：一静默一硬崩

`sanity_check.py`（改前）L42-45 逐行判定：

| 行 | 插入目录 | 泄漏的顶层名 | 判定 |
|---|---|---|---|
| L42 `BACKEND_ROOT` | `backend/` | — | ✅ **正确**（放父目录） |
| L43 `dirname(BACKEND_ROOT)` | 项目根 `molding-optima/` | `backend` / `frontend` | ⚠️ 勉强（也是父目录，但副作用大） |
| **L44 `FUZZY_DIR`** | `fuzzy/` | `fuzzy_core` `sources` `elements` `specs` `recommendations` `field_names` | 🔴 **静默劫持**（这些能成功加载，撞名时行为诡异难查） |
| **L45 `dirname(FUZZY_DIR)`** | `process/algorithms/` | `fuzzy` `llm` `empirical` | 🔴 **硬崩**（`fuzzy` 带 `..` 相对导入，见事实 4） |

两行都是 `insert(0, ...)` **前插** ⇒ 优先级最高 ⇒ 一旦有同名包，**永远**先命中它们。

##### 2.14.3 为什么 Python 要这么设计

`__init__.py` + 相对导入机制，正是为了保证「**包只以完整点分路径被加载**」。

| 模块 | `..` 指向 | 能否当顶层包 |
|---|---|---|
| `fuzzy_core/models/nets.py` L32-42 | `fuzzy_core` 自身 | ✅ 能（**因此必须用独特的顶层名**，见 §2.15） |
| `fuzzy/specs.py` L39 | `process.algorithms` | ❌ 不能（**`fuzzy` 包不自包含**） |
| `expert/specs.py` L19 | `process.algorithms` | ❌ 不能 |

##### 2.14.4 改法（实测可行，零 Django 保持）

| 现状 | 改成 | 实测 |
|---|---|---|
| 顶层 `import fuzzy_core` | `from process.algorithms.fuzzy.fuzzy_core.models.nets import ...` | ✅ 成功；`django loaded? False`、`process.models loaded? False` |

**只插包的父目录**即可：`backend/`（`sanity_check.py` 本来就插了）+ `backend/`（pytest prepend 自动插）。

**实际改动 7 个文件**：

| 文件 | 改动 |
|---|---|
| `process/algorithms/fuzzy/sanity_check.py` | 删 L44/L45 两行插入 + `FUZZY_DIR` 变量；13 处裸导入改绝对 |
| `fuzzy_core/tests/test_nets.py` | `sys.path.insert` 目标从 `fuzzy/` 改为 `backend/`；4 处裸导入改绝对 |
| `fuzzy_core/tests/test_macros.py` | 同上；2 处裸导入改绝对 |
| `_dev_refs/diag_fuzzy_bucket_shift_impact.py` | 删 `_FUZZY_DIR` 插入；3 处改绝对 |
| `_dev_refs/diag_fuzzy_design.py` | `sys.path.insert` 目标 `FUZZY_DIR` → `BACKEND`；3 处改绝对 |
| `_dev_refs/diag_fuzzy_level_design.py` | 同上；1 处改绝对 |
| `_dev_refs/diag_fuzzy_word_table_alignment.py` | 删插入行；1 处改绝对 |

**顺带修正**：`test_nets.py` docstring 里的运行路径 `backend/process/engines/fuzzy/fuzzy_core` → `backend/process/algorithms/fuzzy/fuzzy_core`（原路径写错了，`engines` 应为 `algorithms`）。

##### 2.14.5 验收

| 项 | 结果 |
|---|---|
| 残留扫描（代码） | ✅ 顶层裸导入 `from fuzzy_core` / `import fuzzy_core` **0 处**；`sys.path.insert` 带 `fuzzy` 包目录 **0 处** |
| **顶层名泄漏**（新增验收项） | ✅ `fuzzy` / `fuzzy_core` / `sources` / `elements` / `specs` / `aggregation`（E23 后为 `recommendations`） / `naming`（E22 后为 `field_names`）—— **全部未进** `sys.modules`（改前 `sources` / `elements` 已泄漏） |
| 零依赖（E2 成果保持） | ✅ `django` / `process.models` / `sources.db` 均**未进** `sys.modules` |
| 未使用 import（AST 对照 HEAD） | ✅ 7 个文件与 HEAD **集合完全一致**（`defuzz` / `LEVEL_WORDS_BY_LVL` / `LEGACY_HS_MAPPING_DICT` 3 个**既有遗留**，非本轮引入） |
| BOM 完整性 | ✅ `sanity_check.py` / `test_nets.py` 的 UTF-8 BOM **保持不变** |
| pytest | ✅ **22 passed**（17 fuzzy_core + 5 backend/tests） |
| 内核测试**独立跑法** | ✅ `python -m tests.test_nets` → 11/11 PASS；`python -m tests.test_macros` → 6/6 PASS（两种跑法都通） |
| sanity_check | ✅ 全绿 |
| 离线验证 `_verify_e2_offline.py` | ✅ **8 PASS / 0 FAIL** |
| provided_smoke | ✅ **PASSED**（6/6） |
| 端到端（真实 DB） | ✅ 命中 10 条；`validate_rule_specs` 通过；分流 `{'numeric': 10, 'advisory': 0}` |
| dev 脚本行为对照（HEAD 字节级副本） | ✅ `diag_fuzzy_design.py`：「6/7 个 case 正常执行」exit=1 **与 HEAD 一致**；`diag_fuzzy_level_design.py`：同样 UnicodeEncodeError（GBK 控制台）**与 HEAD 一致**；`diag_fuzzy_word_table_alignment.py`：「1 处不一致 —— 需要收敛」exit=1 **与 HEAD 一致** ⇒ 三者 exit=1 均为**既有行为**，非本轮引入 |

**行为零变化**：本轮只改 **导入方式 + 搜索路径**，不触碰任何算法语义、不改任何业务逻辑。

### 2.15 讨论存档：`fuzzy_core` 是否改名 `core`（**结论：不改**）

**触发**（用户第 34 轮）：

> 「`F:\...\backend\process\algorithms\fuzzy\fuzzy_core` 这个已经在 fuzzy 下了，
> 是不是直接叫 core 就可以？还是说可能会有冲突？」

**结论：保留 `fuzzy_core`**（用户第 35 轮批准先做 §2.14 治理，本节存档依据）。

**核心理由：`fuzzy_core` 与 `fuzzy_algorithm.py` 的 `fuzzy_` 前缀性质完全不同。**

| 模块 | 是否被当**顶层包** import | 前缀性质 |
|---|---|---|
| `fuzzy_algorithm.py` | ❌ 从不（全仓都是 `from process.algorithms.fuzzy.fuzzy_algorithm import`） | `fuzzy_` **真冗余** ⇒ 拍 3 改 `engine.py` 安全 |
| `fuzzy_core/` | ✅ **天天**（27 处裸导入，见 §2.14.1 事实 5） | `fuzzy_` **不是冗余**，是它的**全局唯一性护栏** |

⇒ 立下的通用规范：

> **顶层包名按「全局唯一」标准命名；只有纯模块名才按「包内简洁」标准命名。**
> `fuzzy_core` 虽是包内目录，但它被当顶层包用 ⇒ 名字要经得起全局碰撞
> （改名 `core` ⇒ 27 处裸导入会把 `core` 变成顶层模块名，而 `core` 是 Python/Django
> 生态里最高频的通用名之一：`django.core` / `sklearn.core`…）。

**另两条理由**：

1. **`core` 太泛**：`fuzzy/sources/`、`fuzzy/elements.py` 是不透明命名但无歧义；`fuzzy/core/` 属于**半透明** —— 知道是核心，但不知道是「模糊推理内核」。
2. **断掉上游溯源**：`fuzzy_core` 源自 `old/mdprocess/utils/fuzzykit/fuzzy_core/`，每个文件 docstring 都写着「从 xxx 迁来」⇒ 目录名本身是溯源链的一环。

### 2.16 E9：内核输入契约归位（`elements.py` → `fuzzy_core/profiles.py`）

**触发**（用户连续四问）：

> 「我认为对外的服务，属于外层，但是keyword和method应该由core定义，
> 否则就需要将fuzzy_core平铺，而不是单独定义文件夹」
>
> 「nets.py 84-208 这不就是以前算法定义的RuleInput和KeywordInput吗？
> 就是名字应该是因为避免和模型一致，特意换了名称」
>
> 「所以我的意思是 nets.py 80-209 这两个应该实现成真正的算法契约，
> 而不是再重新定义一份……算法内部就可以完全使用算法定义的契约对象了，而不是一个dict」
>
> 「我的意思不是删除dict，我只是想表明要规范算法中的对象」

**诊断：三个被忽略的事实**

| # | 事实 | 证据 |
|---|---|---|
| 1 | `FuzzyFeature` / `FuzzyRule` **从来不是输入契约**，而是内核 `__init__` 内部由裸 dict 构造出的**产物** | 旧 `nets.py` L244 `FuzzyRule(rule.get('rule_description'))`；旧 L274 / L285 `k_dict['memberships'] = FuzzyFeature(...)` |
| 2 | `elements.py` 想立的契约被**自己的** `to_*_array()` 掐死 —— Spec 转一圈又变回内核的裸 dict | ⇒ 现状是「没有契约 + 两套半成品」 |
| 3 | 真正的输入契约一直**无类型**：三个裸 list | `NumTskRuleNet.__init__(self, rule_array: list, keyword_array: list, priority_array: list)` |

**决策：契约归内核所有**。否决「内核定义最小输入 + 外层 Spec 继承」的骑墙方案
（用户：「否则就需要将fuzzy_core平铺」）；同时**不消灭内核内部的 dict**
（`pre_dict` / `sol_dict` / 矩阵是 E5 已定的实现结构）—— 消灭的只是「边界上的隐式契约」。

**命名**：`KeywordProfile` / `RuleProfile`。用户否决 `*Input` / `*Spec`
（「input或者specs都不想对象的感觉」）⇒ `*Profile` = 档案，刻意避开
ORM 模型名（`RuleKeyword` / `RuleMethod`）、内核内部产物名
（`FuzzyFeature` / `FuzzyRule` / `NumTskRule`）与项目既有 `*_specs`（专指对外接口契约）。

**结构变更（分层清单由 6 层并为 5 层）**

| 新位置 | 内容 | 来源 |
|---|---|---|
| `fuzzy_core/profiles.py` | `KeywordProfile` / `RuleProfile` + `to_keyword_array` / `to_rule_array` / `to_priority_array` + `validate_keyword_profiles` / `validate_rule_profiles` | `fuzzy/elements.py` 整体迁入 + 改名 |
| `fuzzy_core/models/features.py` | `FuzzyFeature` | `nets.py` 原样搬出 |
| `fuzzy_core/models/rules.py` | `FuzzyRule` / `NumTskRule` / `ParticularRules` | `nets.py` 原样搬出 |
| `fuzzy_core/models/nets.py` | `FuzzyRuleNet` / `NumTskRuleNet` / `TskRuleNet` | 只留 net |

**消亡路径**：`fuzzy/elements.py`（**从未提交** ⇒ 删除无 git 历史风险）。
连带把 §2.13.8「`elements` 与 `adapters` 是否合并（结论：不合并）」的二选一作废 ——
`elements.py` 消亡、`adapters.py` 已在 E7-e 拆为 `sources/db.py` + `sources/text.py`。

**⚠️ 如实边界：本轮只是「搬 + 改名」，内核 net 仍吃裸 dict。**
`to_keyword_array` / `to_rule_array` / `to_priority_array` 仍在 `profiles.py` 里，
`NumTskRuleNet` 仍是 3 参（`rule_array` / `keyword_array` / `priority_array`）。
「内核完全使用契约对象」要等下一轮：net 直接吃 `RuleProfile` / `KeywordProfile`，
`priority_array` 这条人造平行数组随之消失（见 §6 L13）。

**验收**：见 §5 E9 行。

### 2.17 E10：端口归位（`RuleRepository` 从 `sources/` 回到包根）

**触发**（用户连续三问）：

> 「F:\...\fuzzy\sources 我觉得这个sources命名不恰当，
> 这好像是想说算法的source一样，但是我们这究竟想表明什么？」
>
> 「所以本质是外层管理数据，将数据传给内核，而不是内核自己管理数据，
> 这样层次才清晰？」

**诊断：`sources` 这个名字三重不合适**

| # | 问题 | 说明 |
|---|---|---|
| 1 | 词义歧义 | 软件语境里 `sources` 第一联想是 "source code / 源文件" |
| 2 | 覆盖不全 | 目录里 4 件事，只有 2 件是"来源" |
| 3 | 粒度误导 | 看上去像"多种来源并列"，但里面的业务逻辑不属于任何来源 |

目录实际承担 4 件事：

| 文件 | 真实职责 | 是"来源"吗 |
|---|---|---|
| `sources/__init__.py` | `RuleRepository` **端口协议** + `RuleQueryContext` | ❌ 是接口 |
| `sources/db.py` | 查库 **+ 四级特异级匹配 + 档位过滤 + 结论分流**（领域逻辑） | ⚠️ 一半是 |
| `sources/text.py` | 规则格式翻译（它自己都写明"来源无关"） | ❌ |
| `sources/files/` | 文件来源空壳 | ✅ |

**根因：目录内职责不同质** —— 用 I/O 词（source）去命名一个**同时装着领域逻辑**的目录，
是名不副实的根因；领域逻辑不属于任何来源（换来源它也不变）。
⇒ 单纯改名解决不了，必须把杂物分出去。

**决策（方向 B，用户批准）**

| 内容 | 去处 | 理由 |
|---|---|---|
| `RuleRepository` + `RuleQueryContext` | **`fuzzy/ports.py`**（包根） | 依赖倒置：**端口属消费方**，消费方是编排层 ⇒ 端口与消费方同层，不与实现同层 |
| `db.py` + `files/` | 留在 `sources/` | 这才是真"来源"，名字恢复名副其实 |
| `text.py` | **暂不动** | 它的真正归宿是与内核 `parsing.py` 合流（Step 4），动解析逻辑风险高一档 |

**附带好处**：编排层拿端口不再需要 import 整个来源包 ——
依赖「端口」与「实现」在 import 路径上就分开了。

**顺带修掉**：`fuzzy_core/profiles.py` 的 docstring 原先反向引用外层模块路径
（`fuzzy.sources.db` / `fuzzy.sources.text`）⇒ 改为中性表述（依赖方向：外层 → 内核）。

**本轮是"走回头路"但不是原样复原**：E7-e 把 `ports.py` 迁进 `sources/__init__.py`，
本轮带着「端口属消费方」这条明确理由搬回包根；`ports.py` 在 HEAD 中本就存在
（E7-e 之前的版本），本轮是**复活 + 更新**（`FuzzyRuleSpec` → `RuleProfile`）。

**验收**：见 §5 E10 行。

### 2.18 E11：规则库适配层归位（`sources/` → `library/`）

**触发**：本轮由用户提出 —— 「`fuzzy/library` 是历史任务中需要解决的部分，但看起来没完成，检查一下并完成剩余任务」。

**诊断：一轮「开了头就断了」的搬移**

`library/` 目录在工作区里已存在（未跟踪），但**完全跑不起来**。逐项核对后发现 7 处未完成：

| # | 位置 | 问题 | 实测后果 |
|---|---|---|---|
| D1 | `library/keywords.py` | 是 `rules.py` 的整份过期副本（含 `RuleQueryService`），且缺 `RuleQueryContext` / `RuleLibrary` / `RuleMethod` / `parse_rule` / `normalize_level_word` / `logger` 导入 | **import 即 `NameError`**（L127） |
| D2 | `library/rules.py` L39-114 | 自带一份 `RuleKeywordAdapter` 类定义，遮蔽了 L27 从 `library.keywords` 的 import | 死 import；连带被 D1 拖死 |
| D3 | `library/rules.py` | `KeywordProfile` 未导入，但 `to_keyword_profiles` 在用 | 修好 D2 后调用即 `NameError` |
| D4 | `library/files/__init__.py` | 缺失 | `library/files/` 不是包 |
| D5 | 全仓 12 处 import | 仍指向 `sources.db`（生产 1 + 测试 3 + dev 脚本 8） | `library/` 是死代码 |
| D6 | `sources/` 4 个文件 | 未删 | 与 `library/` 职责重复 |
| D7 | 6 处 docstring | 目录名过时（`fuzzy/__init__.py` L11、`ports.py` L11/12/74、`fuzzy_core/parsing.py` L14、`input_specs.py` L311、`sanity_check.py` L120、`models/rules.py` L243） | 文档与实现不符 |

**卡住的根因（已定位到具体一行）**

上一轮把拆分动作写成了脚本 `_dev_refs/_tmp_split.py`，但段标记写错了：

```python
A = '# ====\n# RuleKeywordAdapter'      # ← 与真实分隔线不匹配
```

而文件里的分隔线是 **78 个 `=`**（`'# ====' + '='*74`）⇒ `'# ====\n'` 匹配不上
⇒ `k.index(S)` 抛 `ValueError` ⇒ **脚本在写盘前就崩了** ⇒ 拆分**从未发生**
⇒ 两个文件各自留着两份类 ⇒ 后续（接线 / 删旧 / 改 docstring）自然也没做。

⇒ **一个标记不匹配的 `str.index()`，把一整轮改造卡在了“文件已生成、内容未拆分”的半成品状态。**

**决策（用户本轮确认）**

| 项 | 决定 |
|---|---|
| 范围 | 完成 E11 全程（修好 `library/` → 接线 12 处 → 删 `sources/` → 改 docstring） |
| 验收 | 全套现成验收（见 §5 E11 行） |
| 不做 | 不动 `ports.py`（端口属消费方，E10 已定）、不动 `fuzzy_core/` 内核、不碰 `RuleQueryService` 内部业务逻辑（E7 遗留的 `RuleSource` 协议抽象属另一轮）、**不新写测试脚本** |

**终态**：`library/` 完全取代 `sources/`，按「一个目录名不同时指代两样东西」拆开：

```
fuzzy/library/
├── __init__.py        分层说明（不 import 任何子模块 ⇒ ORM 不进编排层）
├── rules.py           RuleQueryService  （规则来源：选库 + 四级特异级 + 档位过滤 + 结论分流）
├── keywords.py        RuleKeywordAdapter（关键字元数据来源：RuleKeyword ↔ KeywordProfile）
└── files/
    ├── __init__.py    文件来源空壳（预留）
    └── rule_format.py RuleMethodAdapter （规则格式翻译，来源无关）
```

**关键不变量**：`library/rules.py` 与 `library/keywords.py` 的**类体逐字未改** ——
搬迁前 `git diff --no-index sources/db.py library/rules.py` 的差异只有 **8 insertions / 9 deletions**，
且全部落在 **docstring + import 行**（删 `KeywordProfile` / `RuleKeyword` 两个 import，
加 `from ...library.keywords import RuleKeywordAdapter`）⇒ **零个方法体改动**。

**拆分执行**：修正 `_tmp_split.py` 的段定位（改为「按行扫分隔线 + 看下一行标题」，
不写死 `=` 的个数）⇒ 拆出 `keywords.py` 105 行（仅适配器）/ `rules.py` 278 行（仅服务），
两个文件 `noBOM`。

**验收**：见 §5 E11 行。

### 2.19 E12：来源层类职责对称化（查库与转换分离）

**触发**：用户对 E11 终态提问 —— 「`rules.py` 这个查询服务中有查询 keywords 吗？
keywords 和 methods 都是算法的一部分」。

**诊断：文件级对称了，类级没有**

E11 把 `sources/` 拆成 `library/rules.py` + `library/keywords.py`（**文件级**对称），
但**类级**仍不对称：

| | 规则（methods） | 关键字（keywords） |
|---|---|---|
| 承载类 | `RuleQueryService`（**服务**） | `RuleKeywordAdapter`（**适配器**） |
| 查库在哪 | 服务内，直接 ORM | **适配器内**，直接 ORM |
| 转换在哪 | 内核 `fuzzy_core/profiles.py` | **适配器内** |
| 端口暴露 | `RuleRepository.get_rules` | `RuleRepository.get_keywords_by_names`（同一端口） |

⇒ 关键字侧的「查库」被塞进了「转换器」—— 这正是 E7 给 `RuleQueryService` 开的
同一个病（「取数与业务逻辑焊死」），只是搬到了另一个类。

⇒ 另有一处**文档兑现了、实现没兑现**：`library/__init__.py` L30-32 早就写明
「**输出**是 `RuleProfile` / `KeywordProfile`（内核输入契约）」，
但关键字侧实际吐的是**裸 dict**（`RuleKeywordAdapter.get_keywords_by_names`）。

⇒ 而**端口那一层其实是对的**：`RuleRepository` 同时暴露 `get_rules` 与
`get_keywords_by_names` ⇒ 「两类输入是同一个算法依赖的两面」这个判断早就做过了，
**歪的是实现层的类边界与命名**。

**决策（用户本轮确认）**

| 项 | 决定 |
|---|---|
| 对称化范围 | **类级对称化**：新增 `KeywordQueryService` 承担查库，`RuleKeywordAdapter` 退化为纯转换器；`RuleQueryService` 保留门面转发 |
| 命名 | **先只改 docstring**：`RuleRepository` / `RuleQueryService` 名不动（改名影响端口 + 编排层 + 多个诊断脚本），在 docstring 里写明它同时承载两类算法输入 —— 改名登记为 **L17** |
| 端口 / 编排层 | **零改动**（`RuleRepository.get_keywords_by_names` 的签名与返回结构不变） |

**终态**

```
fuzzy/library/
├── rules.py       RuleQueryService      查规则（选库 + 四级特异级 + 档位过滤 + 结论分流）
│                  └─ get_keywords_by_names → 门面转发（KeywordProfile → 内核 keyword_array 元素）
├── keywords.py    KeywordQueryService   查关键字（ORM 查库 → KeywordProfile）
│                  RuleKeywordAdapter    纯转换（ORM/dict → KeywordProfile / fuzzy dict，不碰数据库）
└── files/
```

两侧一一对应：

| | 规则 | 关键字 |
|---|---|---|
| 查库 | `RuleQueryService.get_rules` | `KeywordQueryService.get_keywords_by_names` |
| 出口 | `List[RuleProfile]` | `List[KeywordProfile]` |
| 转换 | 内核 `fuzzy_core.profiles` | `RuleKeywordAdapter` |

**改动清单**

| 文件 | 改动 |
|---|---|
| `library/keywords.py` | 新增 `KeywordQueryService`；`RuleKeywordAdapter` 摘掉 `get_keywords_by_names`（退化为纯转换器）；模块 docstring 补对称结构说明 |
| `library/rules.py` | `get_keywords_by_names` 改门面转发（`KeywordProfile` → `to_net_dict()`）；import 换 `KeywordQueryService`；类 docstring 写明同时承载两类算法输入 |
| `ports.py` | `RuleRepository` docstring 写明覆盖两类输入；`get_keywords_by_names` docstring 的键名 `'source'` **修正为 `'meta_source'`**（旧文档写错了键名） |
| `library/__init__.py` | 补两侧对称结构表 |
| `_dev_refs/diag_fuzzy_rule_journey.py` | 改走生产门面 `RuleQueryService.get_keywords_by_names`（更贴近它自己写的「完全复用生产路径」），摘掉 `RuleKeywordAdapter` import |
| `process/algorithms/fuzzy/naming.py` | 清掉 **E5 遗留**的未使用 import `List` / `Tuple`（本轮 AST 全包扫描发现） |

**新增验收脚本**

| 脚本 | 作用 |
|---|---|
| `_dev_refs/_verify_kw_parity.py` | 关键字路径**新旧对拍**（真实 DB）：旧实现（内联复刻）逐元素、逐键、含**键序**、含**类型**与新实现对拍 + 契约校验 + ORM 泄漏检查 + 空入参/不存在名字边界 |
| `_dev_refs/_verify_zero_dep.py` | 零依赖不变量（E10 口径） |
| `_dev_refs/_audit_unused_imports.py` | AST 未使用 import 审计（支持 `noqa` 口径：**只有 `F401` / 裸 `noqa` 才豁免，`E402` 不豁免**） |

**验收**：见 §5 E12 行。

**顺带查出的历史遗留**（登记为 **L18**）：`fuzzy` 包内 3 个未使用 import，
均为 **HEAD（E4-b）就有**的既有遗留 —— `functional.py` 的 `Tuple`、
`test_nets.py` 的 `defuzz`、`translate.py` 的 `np`。

⚠️ 顺带**修正前几轮验收记录的口径失真**：E9~E11 记的「AST 未使用 import 0」
是因为那几轮的 AST 检查**只扫了本轮改动的文件**；本轮起改为**全包扫描**
（`process/algorithms/fuzzy` + `tests`）⇒ 数字与前几轮**不可直接比较**。

### 2.20 E13：来源层文件级对齐 —— 「查询是查询，管理是管理」

**触发**：用户对 E12 终态提问 —— 「同样的 `rules.py` 1-291 / `keywords.py` 1-142
这两文件也应该对齐，查询是查询，管理是管理」。

**诊断：E12 只对称了类，规则侧的文件内部还是「一个类九个方法」**

E12 把**关键字侧**拆成了两条线（`KeywordQueryService` 查询 + `RuleKeywordAdapter` 管理），
但**规则侧**原封不动 —— `library/rules.py` 里仍然是**一个** `RuleQueryService` 类，
9 个方法里**查库与业务判断焊在一起**：

| 方法 | 性质 | 是否碰 ORM |
|---|---|---|
| `get_libraries` | 取数 | ✅ |
| `get_rules` | 取数 + **选库策略 + 四级特异级 + 档位过滤 + 结论分流 + 契约构造** | ✅ |
| `_product_to_library_codes` | **纯业务判断**（产品类 → 库编码映射） | ❌ |
| `_match_defect_level` | **纯业务判断**（规则前件档位 vs 反馈档位） | ❌ |
| `classify_conclusion_kind` | **纯业务判断**（结论形态判定） | ❌ |
| `split_by_conclusion_kind` | **纯业务判断**（分流） | ❌ |
| `to_rule_array` / `get_priority_array` | 契约构造（转发内核） | ❌ |
| `get_keywords_by_names` | 门面转发（关键字侧） | ❌ |

⇒ **9 个方法里只有 2 个真正查库，其余 7 个是管理动作**，
却和查库挤在同一个类里 ⇒ 与 E12 落地的关键字侧**不对等**。

⇒ 另一个后果：`get_rules` 既是「查库入口」又是「业务编排器」，
**无法单独替换数据源**（DB → 本地文件）—— 换源必须连业务逻辑一起重写。

**引用面调研（决定 blast radius）**

| 引用方 | 处数 | 说明 |
|---|---|---|
| 生产代码 | **1 处** | `fuzzy_algorithm.py` `_get_repository()` 的延迟导入 + 实例化 |
| 测试 | **3 处** | `tests/verify_fuzzy_nested_context.py` 的 patch 目标 |
| dev 脚本 | **11 个文件** | 用到的全是**门面方法**（`get_rules` / `split_by_conclusion_kind` / `to_rule_array` / `get_priority_array` / `get_keywords_by_names`）⇒ 纯改名 |
| **零外部调用方** | **6 个方法** | `get_libraries` / `_product_to_library_codes` / `_match_defect_level` / `classify_conclusion_kind` / `select_libraries` / `get_methods` —— 实测**只出现在 `library/rules.py` 内部** |

⇒ 拆类的真实风险面只在**生产 1 处 + 测试 3 处**；dev 脚本 11 个文件是纯改名。

**决策：2v2 对称**

| | 规则（`library/rules.py`） | 关键字（`library/keywords.py`） |
|---|---|---|
| **查询**（只碰数据库） | `RuleQueryService` | `KeywordQueryService` |
| **管理**（不碰数据库） | `RuleRoutingService` | `RuleKeywordAdapter` |

**三处必须保持的行为等价（拆分时的地雷）**

1. **选库必须逐个查库，不能改成批量 `library_code__in`** —— 命中结果最终按 `priority`
   降序**稳定**排序，同 priority 时**候选顺序**决定先后。改成一次查完会改变同 priority
   库的相对顺序 ⇒ 下游规则遍历顺序变化 ⇒ 同特异级规则的产出顺序可能变化。
2. **规则库以 ORM 实例传递，不能改用 `library_code` 字符串** —— 同一 `library_code`
   可能对应多条库记录（不同 company），改字符串会改变 SQL 语义与命中条数。
3. **兜底库 `base` 单独一次查询并带 `library_type='fuzzy'`**（其余查询不带该过滤）
   —— 保持原「三步选库」语义不变。

**终态**

```
fuzzy/library/
├── rules.py       RuleQueryService     查询侧：get_libraries_by_codes / get_methods（只碰 ORM）
│                  RuleRoutingService   管理侧 + RuleRepository 端口门面（不碰 ORM）
├── keywords.py    KeywordQueryService  查询侧：get_keywords_by_names（只碰 ORM）
│                  RuleKeywordAdapter   管理侧：ORM/dict → KeywordProfile（纯转换）
└── files/
```

⇒ `RuleRoutingService` 既是「管理侧」又是「`RuleRepository` 端口的默认实现（门面）」——
这是**刻意的**：端口横跨查询与管理两侧（`get_rules` 要先查后判、`get_keywords_by_names` 是转发），
编排层只跟端口打交道 ⇒ 门面天然属于**管理侧**（它做的是「编排」，不是「取数」）。

**改动清单**

| 文件 | 改动 |
|---|---|
| `library/rules.py` | `RuleQueryService` 收缩为纯查询（2 个方法）；新增 `RuleRoutingService`（管理侧 + 门面，9 个方法）；模块 docstring 加「查询 / 管理」对称表。291 → **357** 行 |
| `library/keywords.py` | docstring 对称表更新 + 3 处类名引用（142 行） |
| `library/__init__.py` | 对称结构表改为「查询 / 管理」两行 + 门面说明（42 → **45** 行） |
| `library/files/rule_format.py` | L46 docstring 改为 `library.rules.RuleRoutingService.get_rules()` |
| `ports.py` | Protocol 说明 + L79 默认实现改为 `RuleRoutingService` |
| `fuzzy_algorithm.py` | L87 docstring + L101-102 延迟导入改 `RuleRoutingService` + L578 注释 |
| `sanity_check.py` | L2 / L111 docstring |
| `input_specs.py` | L311 docstring |
| `process/models/rules.py` | L243 索引注释 |
| `tests/verify_fuzzy_nested_context.py` | L12 docstring + 3 处注释 + **3 处 patch 目标** |
| 11 个 dev 脚本 | import 与调用改名 |

**护栏：把「查询是查询、管理是管理」变成可执行断言**

新增 `backend/_dev_refs/_chk_library_layout.py`（**只读**）—— 用 AST 断言：

1. 四个类各在其位（存在性）；
2. **交叉污染**：一个类不得同时出现在两个文件里；
3. **管理侧不发起 ORM 查询**：管理类方法体里**不得出现 `.objects`**；
4. **查询侧确实在查库**：查询类方法体里**必须**出现 `.objects`（防止查询侧被掏空成空壳）；
5. `fuzzy/sources/` 旧目录已消亡（E11）。

⚠️ 同时**删除 `_dev_refs/_tmp_split.py`** —— 它是 E11 的**写盘型**脚本，
会按段标记**改写** `library/keywords.py` 与 `library/rules.py`；E13 后段标题已变，
重跑会**摧毁本轮成果** ⇒ 属地雷脚本，删除并以只读自检替代其诊断价值。

⚠️ 批量改名**不能用编辑工具的「全部替换」**：实测在部分历史脚本上**只命中第一处**
（编码已核实为 UTF-8 无 BOM，非编码问题）⇒ 改用 `_dev_refs/_rename_to_routing.py`
（Python `str.replace` 全量 + `newline=''` 保留 CRLF + 补回多行 import 的尾逗号），
并以 `git grep` 残留扫描收尾（首轮 TARGETS 漏了 2 个文件，第二轮补扫）。

**验收**：见 §5 E13 行。

**如实边界**
- L14（第二套规则串解析器）/ L15 / L16 **本轮仍未动**。
- L17（命名）本轮**部分兑现**：`RuleQueryService` 语义已变为「纯查询类」，
  端口默认实现改为 `RuleRoutingService` ⇒ 名字与职责不再矛盾；
  但 `RuleRepository` **同时承载规则与关键字**这件事仍未改名（L17 的后半段仍未关闭）。

### 2.21 E14：来源轴补刀 —— 「碰 ORM 的 = 来源特有，不碰 ORM 的 = 来源无关」

**触发**：用户审 E13 终态时打开 `library/rules.py` 问 ——

> 「你之前的方案中不是会在 library 中新增一个文件管理 repository 吗？这是换房干了？」

**核查结论：E13 确实换了轴，但不是替代原方案（有一处真冲突）**

原方案**三轮都记着**，一字未改：

| 出处 | 原文 |
|---|---|
| §2.12 后续清单第 2 项（L416-418） | 「**数据源抽象**：`RuleSource` 协议 + `DbRuleSource` / `FileRuleSource`；库只作**检索维度**（`list_library_codes()` / `load_rules(lib, poly, product, defect)`），**选库的业务映射留在构建层（不污染数据源）**」 |
| §2.13.7.3 遗留清单第 1 项（L634） | 「**数据源抽象**（`RuleSource` 协议 + `DbRuleSource` / `FileRuleSource`），库只作**检索维度**」 |
| §2.13.9 遗留清单第 1 项（L761） | 「**数据源抽象**：`RuleSource` 协议 + `DbRuleSource` / `FileRuleSource`（**加能力**拍，与搬移分开）」 |

⇒ 该方案**至今未做**（E11~E13 三轮都在搬文件、改类边界，没有一轮落它）。

E13 切的是**「查询 / 管理」**轴，与「来源」轴**正交** ⇒ 不是替代；
且 E13 的 `RuleQueryService.get_libraries_by_codes` / `get_methods`
**恰好就是**原方案里 `DbRuleSource` 的「库只作检索维度」那一半 ⇒ **不白做**。

⚠️ **但有一处真冲突**（本轮要修的就是它）：

- `RuleRoutingService` 住在**按内容域命名**的 `library/rules.py` 里，
  名字叫 **Routing（来源无关的意味）**，实现却**返回 ORM 实例**、**直接调 `RuleQueryService`**
  ⇒ 它是**数据库专属**的，却**占了来源无关的位置**；
- 原方案明确约束「**选库的业务映射留在构建层（不污染数据源）**」，
  而 `_product_to_library_codes` 却住在 `library/` 里 ⇒ **违反**。

**代码里的明文证据（这一层的轴是「来源」而不是「内容域」）**

| 位置 | 原文 |
|---|---|
| `library/files/__init__.py` L5 | 「与**数据库来源**的关系」 |
| `library/files/rule_format.py` L3 | 「**层定位**：`library` 层（第 ③ 层「读取算法依赖」）的**来源无关**部分。」 |
| `library/files/rule_format.py` L15 | 「⇒ 它与来源**正交**，故独立成文件，**不塞进 `library.rules`**。」 |

⚠️ `rule_format.py` L15 那句「**不塞进 `library.rules`**」在 E14 之前**与事实不符** ——
`library/rules.py` 里明明住着 3 个纯判断方法（`product_to_library_codes` /
`match_defect_level` / `classify_conclusion_kind`），它们**同样不碰 ORM**，
与 `rule_format.py` 是**同一类东西** ⇒ 本轮把它们搬去了「不塞进 `library.rules`」该去的地方。

**决策（用户拍板：只补这一刀）**

给用户三选项：

1. **只补「管理侧的来源无关 / 来源特有」这一刀** —— 新建 `library/policy.py`，
   **不动目录结构、不落 `RuleSource` 协议、不改名** ⇒ **用户选定**；
2. 一次做完来源轴重排 + `RuleSource` 协议（涉及目录重排 + 端口重定义，工作量大）；
3. 先不动代码只修正命名与文档。

⇒ 选 1 的理由：**来源轴的收益在「文件来源真落地那天」**，
而眼下最紧迫的是「**别让 DB 专属逻辑占着来源无关的位置**」；
先做「逻辑抽离 + 护栏锁死」，协议与目录留到真有第二个来源时再动
（那时才知道协议该长什么样）。

**判据（与「查询是查询、管理是管理」同源）**

> **碰 ORM 的 = 来源特有（source-specific）；不碰 ORM 的 = 来源无关（source-neutral）。**

⇒ 两条轴**正交**：`library/` 顶层轴 = **来源**（DB / 文件 / …），
来源内部次级轴 = **查询 / 管理**。

**改动清单**

| 文件 | 改动 |
|---|---|
| `library/policy.py` | **新建**（179 行）：`RulePolicy` —— 6 个方法，**零 ORM**（只 import `fuzzy_core.profiles` / `fuzzy_core.parsing` / `fuzzy.ports`） |
| `library/rules.py` | `RuleRoutingService` 由 9 方法瘦身为 **6 方法**（3 个改为门面转发）；`RuleQueryService` 不动（2 方法）；**3 个方法体搬到 `policy.py`**，本文件现 **280** 行 |
| `library/keywords.py` | 对称表措辞 + 「规则侧比关键字侧多一层（来源无关）」说明 |
| `library/__init__.py` | 结构表改为「① 先按来源分」+「② 数据库来源内部再按查询/管理分」两张表；本文件现 **60** 行 |
| `ports.py` | `RuleRepository` 默认实现说明改为「数据库来源的门面 …… `library.policy.RulePolicy` 的**来源无关**判断」 |
| `input_specs.py` | L311 注释指向 `library.policy.RulePolicy.match_defect_level` |
| `_dev_refs/_chk_library_layout.py` | 新增 `policy.py` 期望项 + `_imports_orm()` + 第三个 role `source_neutral`（137 → **约 175** 行） |
| `_dev_refs/_verify_zero_dep.py` | `_BANNED` 增 `process.algorithms.fuzzy.library.policy`（来源无关层也**不许**被编排层直接依赖） |
| `diag_fuzzy_design.py` / `diag_fuzzy_rule_journey.py` | 2 处输出串改指 `RulePolicy` |

**引用面调研（决定 blast radius）**

| 方法 | 外部调用方 | 处置 |
|---|---|---|
| `split_by_conclusion_kind` | 编排层（经端口）+ 5 个 dev 脚本 | **保留门面转发**（端口协议要求） |
| `to_rule_array` / `get_priority_array` | 同上 | **保留门面转发** |
| `product_to_library_codes` | 仅 `library/rules.py` 内部 | 直接搬走 |
| `match_defect_level` / `classify_conclusion_kind` | 仅 `library/rules.py` 内部 | 直接搬走 |

⇒ **可见性变更**（`_x` → `x`）：因需**跨类调用**（`RuleRoutingService` → `RulePolicy`），
3 个原私有方法提升为公开静态方法 ⇒ **端口协议零改动**（`RuleRepository` 的 5 个方法签名不变）。

**护栏升级：把「来源无关」变成可执行断言**

`_chk_library_layout.py` 新增第三个 role `source_neutral`，比 E13 的「管理侧不得出现 `.objects`」**更强**：

1. 方法体不得出现 `.objects`（同 E13）；
2. **整个文件连 `process.models` 的 import 都不许有**（`_imports_orm()`）
   ⇒ 保证它**真的能脱离数据库独立 import**，而不只是「运行时没查库」。

实测：`import process.algorithms.fuzzy.library.policy` ⇒ `django=False` / `process.models=False` ✓

⚠️ 护栏脚本自身踩过一个坑：role 循环写死 `('query','manage','source_neutral')` ⇒
`policy.py` 没有 `query` 键 ⇒ `KeyError: 'query'` ⇒ 改为 `for role, cls_name in EXPECT[fname].items()`。

**验收**：见 §5 E14 行。

**如实边界**

- **`RuleSource` 协议抽象仍未做**（遗留清单第 1 项，§2.12 L416 / §2.13.7.3 L634 / §2.13.9 L761）
  ⇒ **文件来源仍未落地**，`library/files/` 仍是空壳；
- **`library/` 目录未按来源重排**（仍是 `rules.py` / `keywords.py` / `files/` 三个平级文件，
  而非 `db/` / `files/` 两个来源目录）⇒ 留待真要落文件来源时；
- **L14 / L15 / L16 本轮仍未动**；
- **L17 仍未关闭**：`RuleRepository` 同时承载规则与关键字这件事**仍未改名**
  ⇒ 本轮把它写进了 `RuleRoutingService` 的 docstring（明确标注「这是刻意设计」），
  但**改名留到与 `RuleSource` 抽象一起做**。

### 2.22 E15：端口搬入 `library/` + 改名瘦身 ——「算法只从 repository 取信息」

**触发**：用户连续四问（2026-10-26）

> ① 「我们确实有规则库的概念，但是每次进行推理的时候，我们可能需要从不同的规则库中整理规则，最后才能获取到我们实际算法中使用的规则和关键词，这部分是在rules中管理，还是再创建一个文件管理，这很关键，其实我觉得可能放在rules中比较合适。所以policy文件，我没看到它存在的定位。所以我对repository的定位其实是算法用的keyword和rule，就是算法实际要用的资源。keyword负责加载关键词，并提供相关服务，同理rule也是，但是rule可能会涉及到library和method，我认为这样是有层次的」
> ② 「或者将rule的编排放在repository中也可以，rule只负责规则部分的，你觉得呢？」
> ③ 「然后算法就只需要从repository中获取需要的信息即可，你觉得呢？」
> ④ 「另外还有一点，ports.py 1-106 这个不适合放在外层，放在 ...\backend\process\algorithms\fuzzy\library 比较合适」

**核查结论：E14 的 `policy.py` 定位确实站不住**

用户把它理解为「来源轴上的一层」，但它实际只是「**规则串语义判定**」这一个函数簇 ⇒ 它是**内容域轴**，不是来源轴 ⇒ 与用户心里「rule / keyword / repository 三层」不匹配。而 `RuleRoutingService` 这个名字（Routing = 来源无关的意味）实指「**数据库来源特有的编排**」⇒ **名实不符**（E14 自己登记过「它是 DB 专属的，却占了来源无关的位置」，但只把 3 个纯判断方法搬走，**没解决名字与职责的矛盾**）。

**用户拍板的终态（内容域三段 + 各自的职责）**

| | 名字 | 职责 | 碰 ORM？ |
|---|---|---|---|
| ① | **keyword**（`library/keywords.py`） | 加载关键词，并提供相关服务 | ✅ |
| ② | **rule**（`library/rules.py`） | 加载规则，并提供相关服务；**涉及 library（规则库分组）/ method（规则条目）两层** | ✅ |
| ③ | **repository**（`library/repository.py`） | **算法实际要用的资源**（= rule + keyword 的组合）+ 编排 | ✅（转手） |

⇒ 「**算法只从 repository 获取信息**」这条**在代码里已经成立**：`fuzzy_algorithm.py` 的 import 段只有 `ports`（+ `fuzzy_core` 零依赖模块 + `naming` / `aggregation`），**从不 import `library/` 的实现** ⇒ 本轮要做的只是「**把默认实现换到正确的位置**」，不是「改造调用链」。

**⚠️ E10 的「端口属消费方」被推翻了**

E10 的判据是**位置规则**（「端口文件必须放在调用方目录」）；而依赖倒置的**实质检验**是「**高层不被低层实现拖住**」⇒ `library/ports.py` **零 ORM 依赖** ⇒ 编排层 import 它不会把 Django 拖进来 ⇒ **结论不变，位置变**。这条已写进 `library/ports.py` 的 docstring。

**E15 改动清单**（**纯路径 + 协议变更 ⇒ 行为零变化**）

| 文件 | 改动 |
|---|---|
| `fuzzy_core/profiles.py` | **新增** `split_by_conclusion_kind`（+34 行）—— 按 `RuleProfile.conclusion_kind` 分流；**纯字段分组**，不解析规则串 ⇒ 零依赖可放内核 |
| `library/ports.py` | **新建**（103 行）：`AlgorithmResourceRepository`（Protocol，**2 个方法**）+ `RuleQueryContext` |
| `fuzzy/ports.py` | **消亡** —— `RuleRepository` 改名为 `AlgorithmResourceRepository`，并由 **5 方法瘦身为 2 方法**（只剩 `get_rules` / `get_keywords_by_names` 两个**取资源**的方法） |
| `library/policy.py` | 删 3 个已入内核的方法（179 → 149 行） |
| `library/rules.py` | 删 3 个门面转发（281 → 259 行） |
| `fuzzy_algorithm.py` | 4 处加工调用改调内核（`split_by_conclusion_kind` / `to_rule_array` / `to_priority_array`）+ import 改指 `library.ports` |
| `fuzzy/__init__.py` | 分层图（**端口层从包根消失**，编号 0/1/2/3） |
| `library/__init__.py` | 结构表同步 |
| `_dev_refs/_verify_zero_dep.py` | L41 改 `from process.algorithms.fuzzy.library import ports` |
| 5 个 dev 脚本 + 1 个测试 | `RuleRoutingService.xxx` 加工调用改调内核 |

**判据：端口只管「取资源」，不管「加工」**

`split_by_conclusion_kind` / `to_rule_array` / `to_priority_array` 是对**已取回的档案**的加工，与「数据从哪来」无关 ⇒ 归**内核输入契约层**（`fuzzy_core/profiles.py`），编排层直接调用，不必绕经数据源层。这一刀同时消掉了「加工方法挂在数据源实现上」的历史包袱（E14 为此专门建了 `policy.py`，而它随 `policy.py` 一并消亡 ⇒ **E14 的结构没站住**）。

**验收**：见 §5 E15 行。

**如实边界**

- `RuleSource` 协议抽象仍未做 ⇒ `library/files/` 仍是空壳；
- 本轮只解决「**位置与命名**」，未解决「**编排本身随来源走**」（留给 E16）。

---

### 2.23 E16：`library/` 内部重组 —— `policy.py` 消亡，`repository.py` 落地

**触发**：承接 §2.22，用户 ②③ 明确「**编排放 repository，rule 只负责规则部分**」。

**终态结构（五个文件，按「契约 → 资源 → 资源集合」排）**

| | 落点 | 职责 | 碰 ORM？ |
|---|---|---|---|
| ① **契约** | `library/ports.py` | `AlgorithmResourceRepository`（Protocol）+ `RuleQueryContext` —— 本层**对外**唯一出口 | ❌ |
| ② **rule 资源** | `library/rules.py` | 取数（**library** 分组 / **method** 条目 两层）+ 规则串语义判定 | ✅ |
| ③ **keyword 资源** | `library/keywords.py` | 取数 + 格式转换 | ✅ |
| ④ **资源集合** | `library/repository.py` | 编排：选库 → 按四级特异级收集 → 组装；组合 rule + keyword | ✅（转手） |
| ⑤ **文件来源** | `library/files/` | 本地规则文件 + 规则格式翻译（预留） | — |

**E16 改动清单**

| 文件 | 改动 |
|---|---|
| `library/repository.py` | **新建**（181 行）：`ResourceRepository`（3 方法：`select_libraries` / `get_rules` / `get_keywords_by_names`）—— 承接原 `RuleRoutingService` 的**编排**职责 |
| `library/rules.py` | **重写**（259 → 218 行）：`RuleQueryService`（2 方法，碰 ORM）+ `RuleService`（3 方法，**零 ORM**：档位匹配 / 结论形态 / 库编码映射）—— 承接原 `RulePolicy` 的**语义**职责 |
| `library/policy.py` | **消亡**（149 行）—— 语义并入 `library/rules.py::RuleService` |
| `library/keywords.py` | docstring 对称表同步（`RuleRoutingService` → `RuleService`）+ 补「组织成资源在 `repository.py`」说明 |
| `library/files/__init__.py` / `rule_format.py` | docstring 同步（指向 `library.repository.ResourceRepository`） |
| `fuzzy_algorithm.py` | 延迟导入改指 `library.repository.ResourceRepository` |
| `library/__init__.py` | **重写**（现 37 行）：五文件结构表 + 三条依赖方向 |
| `_dev_refs/_chk_library_layout.py` | **重写**：新增 `contract` / `resource_set` 两个 role + `_imports_sibling_impl()`（契约层不得 import 同层实现）+ `policy.py` 消亡断言 |
| `_dev_refs/_verify_zero_dep.py` | `_BANNED`：`library.policy` → **`library.repository`**；`_LEAKED_TOPLEVEL` 加 `repository` |
| `_dev_refs/_chk_enc.py` | 主线从「查旧名次数」改为「**扫已废弃类名残留**」（`RuleRoutingService` / `RulePolicy` / `library.policy`） |
| `_dev_refs/_rename_to_routing.py` | **硬禁用**（`sys.exit(0)`）—— 重跑会把全仓改成谁都不认识的名字 |
| 13 个 dev 脚本 / 测试 | `RuleRoutingService` → `ResourceRepository`；import 路径 `library.rules` → `library.repository` |

**顺手修好的 3 处（都在本轮改动集内）**

| 文件 | 症状 | 处置 |
|---|---|---|
| `tests/verify_fuzzy_nested_context.py` | 3 处 patch 目标 `library.rules.ResourceRepository` —— 类已搬走 ⇒ **patch 失败** | 改指 `library.repository.ResourceRepository` |
| `_dev_refs/diag_fuzzy_level_word_crash.py` | patch 目标同样指错；且 `finally` 里把 **bound method** 当普通类属性还原 ⇒ 后续调用参数错位 | 改指 `library.repository`；改用 `classmethod(__func__)` 还原 |
| `_dev_refs/diag_fuzzy_field_registry_regression.py` | `NameError: name 'registry' is not defined`（**自 E11 起的既有 bug**，L16） | `_build_field_context` 现返回 `(keyword_dicts, classification)` ⇒ 改调 `classification`（名字列表字典） |

**⚠️ 如实边界：编排本身随来源走**

`ResourceRepository` 要**转手 ORM**（`RuleLibrary` / `RuleMethod` 实例）⇒ 它是**数据库来源特有**的。文件来源落地时会有**自己的编排实现** ⇒ 「判断逻辑」（`RuleService`）可共用，**「编排」不可共用**。

若要连编排也共用，得把「库 / method」换成**契约级载体（DTO）**而不是 ORM 实例 ⇒ 那是**另一轮的事**（登记 L20，**本轮不做**）。

**验收**：见 §5 E16 行。

### 2.24 E17：契约层文件改名 —— `library/ports.py` → `library/contracts.py`

**触发**：用户问「`library/ports.py` 这个文件命名我觉得不恰当，适合改成什么名称？」

**核查结论：「port」是 DDD 六边形架构的术语词，本仓库不用这套词汇**

全仓（含隔壁 `molding-expert`）扫 `ports.py` / `contract.py` / `contracts.py` / `protocol.py` / `interface.py` / `api.py`
⇒ **`library/ports.py` 是唯一的 `ports.py`**；而本仓库描述「对外承诺什么」的既有词是**「契约」**：

| 已有文件 | 它自称什么 |
|---|---|
| `process/algorithms/field_contract.py` | 「算法入参契约的**通用机制**」 |
| `process/algorithms/fuzzy/input_specs.py` | 「算法入参契约 —— 调优需要哪些字段」 |
| `process/algorithms/fuzzy/fuzzy_core/profiles.py` | 「**内核输入契约层**」 |
| `process/algorithms/expert/specs.py` | 另一套 spec |

⇒ `contracts.py` 与仓库既有词汇一致，且与同层的 `repository.py`（资源集合）形成对称读法。

**候选对比与取舍**

| 候选 | 结论 |
|---|---|
| **`contracts.py`** | ✅ **选定**：仓库词汇一致、内容准确（能力契约 + 契约入参类型）、与 `repository.py` 对称、不绑定架构流派 |
| `protocols.py` | 语义更精确（确实是 `Protocol`），但与 `ports` 同义、改名收益小，且仓库无先例 |
| `resource_contracts.py` | 更精确但偏长，且与 `repository.py` 的「资源」语义轻微打架 |
| ~~`specs.py`~~ | ❌ 本项目 `*_specs` **专指「对外接口契约」**（`input_specs.py` 那种对外 schema），而这是**对内**能力契约，方向相反 |
| ~~`api.py`~~ | ❌ 含义偏：这是内部能力契约，不是对外 API |
| ~~`interface.py`~~ | ❌ 泛，无信息量 |

**改动清单**（19 个文件）

| 类别 | 文件 | 改动 |
|---|---|---|
| **改名** | `library/ports.py` → **`library/contracts.py`** | 文件重命名（内容仅 docstring 措辞） |
| **import 路径** | `fuzzy_algorithm.py` / `library/repository.py` / `library/rules.py` / `tests/verify_fuzzy_nested_context.py` + **8 个 dev 脚本** | `library.ports` → `library.contracts`（共 13 处） |
| **docstring 词汇** | `library/contracts.py`（8 处「端口」→「契约」）/ `library/repository.py`（4 处）/ `library/files/__init__.py` / `library/__init__.py`（3 处）/ `fuzzy_algorithm.py`（2 处）/ `fuzzy/__init__.py` / `process/schemas/optimization.py`（1 处） | 术语统一 |
| **护栏** | `_dev_refs/_chk_library_layout.py` | `EXPECT` 的键名 `'ports.py'` → `'contracts.py'` + docstring 3 处 |
| | `_dev_refs/_verify_zero_dep.py` | `_LEAKED_TOPLEVEL` 的 `'ports'` → `'contracts'`（2 处）+ import 形式 + docstring 措辞 |
| | `_dev_refs/_chk_enc.py` | 旧名扫描清单**新增 `library.ports`** ⇒ 改名后的旧路径成为受监控对象 |

**⚠️ 施工中踩到的两个坑（如实记录）**

1. **一次性脚本的分支漏洞**：脚本按「该文件有专属 edits」还是「只有 import 路径」二选一分支，
   `fuzzy_algorithm.py` 与 `library/repository.py` 走了**前者** ⇒ 它们的 import 路径**被漏掉**
   ⇒ 靠**事后残留扫描**发现并补齐（不是靠脚本自检）。
2. **断言拦下一处真实重复**：`的取用端口 ——` 在契约文件里出现 **2 次**（类说明 + 方法说明），
   首次脚本按「1 次」断言 ⇒ 直接报错退出（**未写盘**）⇒ 合并成一条替换。

**⚠️ 历史事实保留不动**：`contracts.py` docstring 里的「本模块由 `fuzzy/ports.py` 搬入本包」
与 `_dev_refs/_rename_to_routing.py`（**已硬禁用**的历史一次性工具）里的 `library/ports.py`
**都保留原样** —— 它们记的是**当时的事实**，改了就篡改历史。

**验收**：见 §5 E17 行。

### 2.25 E18：`library/` 注释精简（删设计用语与轮次考古）

**触发**：用户要求「`backend/process/algorithms/fuzzy/library` —— 检查一下这个功能模块，将无用的注释全部精简，不需要那么多设计用语」。

**判定标准（先立标准，再动手）**

| 删 | 留 |
|---|---|
| 分层术语（第 ② 层 / 契约→资源→资源集合 / 层定位 / 资源集合门面） | 每文件「是干什么的」一句话 |
| 轮次考古（E2/E7/E15/E17、0005 迁移、「历史实现必然 AttributeError」） | 字段 / 返回值格式（真契约） |
| 决策辩论（为什么用 Protocol 不用 ABC / 为什么契约与实现同层） | 看代码猜不出来的坑 |
| 重复 3 次的对照表 | 行内短注释 |
| 护栏脚本已在监控的不变量复述 | — |

**改动清单**（7 个文件，**945 → 727 行，净减 218 行**）

| 文件 | 改前 | 改后 |
|---|---|---|
| `library/__init__.py` | 37 | 15 |
| `library/contracts.py` | 103 | 67 |
| `library/rules.py` | 218 | 175 |
| `library/keywords.py` | 151 | 109 |
| `library/repository.py` | 181 | 144 |
| `library/files/__init__.py` | 19 | 2 |
| `library/files/rule_format.py` | 236 | 215 |

**⭐ 代码零改动的硬校验**：剥离全部 docstring（模块 / 类 / 函数的首个字符串表达式）后逐文件 `ast.dump(..., include_attributes=False)` 比对 ⇒ **7 个文件全 IDENTICAL** ⇒ 严格证明「只动注释、代码一字未改」。

**踩坑（如实记录）**：① 一次性脚本按「行号区间 + 首尾锚点断言」定位，两处行号记录偏移（`repository.py` 的 `get_rules` docstring 实为 101-110、`get_keywords_by_names` 实为 164-176）⇒ **首轮断言拦下、未写盘**（两遍式设计生效）⇒ 核实真实行号后修正；② 路径拼接重复（EDITS 的 key 已含 `library/` 前缀，又与目录常量拼接）⇒ `FileNotFoundError` ⇒ 改 key。

**复查补刀（5 处）**：`rules.py` 两处 `# ====` 分隔条与其余 4 个文件的 `# --- 标题 ---` 不一致（统一）；`repository.py` 两处措辞去掉「来源无关」「历史实现」；`files/rule_format.py` 一处措辞精简（保留「兼容旧 fuzzykit 惯例」这个真信息）。

**验收**：见 §5 E18 行。

### 2.26 E19：`sanity_check.py` 迁入 pytest 后删除（消除 `return bool` 假通过）

**触发**：用户问「`sanity_check.py` 1-603 这个文件干什么用的？」→ 再问「可以移除掉吗？因为其实我们在调整代码结构，这个后续肯定也是要改的」。

**它的作用**：与 pytest **并行**的第二套测试体系（603 行、独立入口、自制 mock、不依赖 ORM），14 个 case 分 6 组（CASE 1/2/3/4 + B1~B7 + C1~C3）。

**⚠️ 它有一个真缺陷：`return bool` 假通过**
pytest 只在返回值非 None 时发警告，**返回 False 仍算 passed** ⇒ 断言失败被静默吞掉（实测 pytest 报 **17 个** `PytestReturnNotNoneWarning`）。`test_fuzzy_rule_net` 更把异常吞成 `[SKIP]` 并 `return True`。

**覆盖缺口**（删除前逐条比对 pytest 收集清单 ⇒ 22 个用例）

| sanity_check case | pytest 等价物 | 判定 |
|---|---|---|
| CASE 1 / 2 / 4 | 无 | **缺口** |
| CASE 3 | 无（只测 `resolve_bucket` 函数，不验网络实际连桶） | **缺口** |
| B1 / B2 / B5 | 部分（只测 `resolve_bucket` 返回值） | 弱覆盖 |
| B3 / B4 / B7 / C1 / C2 / C3 | 无 | **缺口**（6 个） |
| `test_numtsk_inference_priority` | 断言一次排序、**无反转验证 ⇒ 可能空转** | 空转风险 |

**三条无等价物的真实缺陷回归锁**（C1 / C2 / C3，必须原样迁入 pytest）

- **C1**：旧实现把「隶属度为 0 的门控」从乘积里踢出 ⇒「门控不满足」被当成「门控不存在」⇒ **规则反而激活**
- **C2**：TSK 主路径缺 `MIN_ACTIVATION_THRESHOLD` 过滤 ⇒ 激活度≈0 的规则以 delta≈0 混进推荐列表（实测 conf=1.68e-282）
- **C3**：Mamdani 路径同一问题
- 构造难点：高斯隶属度下 μ 最小值约 1.27e-14（=exp(-32)）**永不为 0** ⇒ 必须 monkeypatch 强制置 0

**迁移方案**（用户拍板「迁移成 pytest 后删除」+「一起修 `return bool` 假通过」）

| 源 | 去向 | 用例数 |
|---|---|---|
| CASE 1/2/4 + B1~B7 + C1~C3 | `fuzzy_core/tests/test_inference_gates.py`（**新建**） | 13 |
| CASE 3 | `tests/test_fuzzy_aggregation.py`（**新建**，**零 Django 依赖** —— 实测 import 后 `django` / `process.models` 均未进 `sys.modules`） | 6 |

**顺带修掉的假通过**（`fuzzy_core/tests/test_nets.py` + `test_macros.py`）

- `_assert_eq` / `_assert_close` / `_assert_raises` 由 `return bool` 改为 `raise AssertionError`
- 删 `ok = True` / `return ok` / `ok &= ` 前缀（**pytest 警告 17 → 0**）
- `test_fuzzy_rule_net` 的「`except Exception` → 打印 `[SKIP]` → `return True`」改为直接抛
- `test_numtsk_inference_priority` **补优先级反转验证** ⇒ 堵住「断言空转」
- 两个 `main()` 改为 try/except 汇总（保留独立跑法）

**⭐ 端到端证明假通过已消除**：临时探针 `tests/test_tmp_fail_probe.py` 故意让断言失败 ⇒ pytest **1 failed**（改前会静默 passed）⇒ 探针用完即删。

**删除与引用清理**

- `git rm process/algorithms/fuzzy/sanity_check.py`（603 行，git 追踪）
- 残留引用扫描：**代码级 import / call = 0**；文字提及仅 `_dev_refs/diag_fuzzy_bucket_shift_impact.py` **5 处** ⇒ 已改指新位置（原 `case_numeric_layer` → `fuzzy_core/tests/test_inference_gates.py`）

**验收**：见 §5 E19 行。

### 2.27 E20：契约归属对齐（转换器归位到来源适配层）

**触发**：用户对照 `fuzzy_core/profiles.py`（契约定义）与 `library/keywords.py` / `library/rules.py` 提问 ——「`profiles.py` 1-306 这才是标准结构，`keywords.py` 40-62 你转换器不是应该转换到 `KeywordProfile` 吗？`rules.py` 86-171 同理 rule 不是应该也是转换成 `RuleProfile`？」

**核查结论**（三处，与直觉的偏差一并记下）

| 用户所指 | 核查结果 |
|---|---|
| `keywords.py` 的转换器应转 `KeywordProfile` | **方向对，但出口本就存在**：转换器本就有 `to_keyword_profiles`；真问题是 `to_fuzzy_dict` 这个**裸 dict 中转层**（外部零调用、只在内部被用一次）—— 绕路 `KeywordProfile(**to_fuzzy_dict(kw))` 让 dict 当中间商，且**丢掉了 `meta_source`**（dict 输入路径无法携带推测论域标记） |
| `rules.py` 86-171 的 rule 应转 `RuleProfile` | **对象看岔了**：该处 `RuleService` 是**规则串语义判定器**（`product_to_library_codes` / `match_defect_level` / `classify_conclusion_kind`），不产出 Profile、也不该产出 |
| —— | **但直觉命中了真问题**：真正造 `RuleProfile` 的地方在 `library/repository.py` L110-119 —— **编排层越位做了来源适配**，且规则侧**没有**与 `RuleKeywordAdapter` 对称的转换器 |

**两侧不对称（改动前的真实形态）**

| | 查库（ORM） | 产出契约 |
|---|---|---|
| keyword | `KeywordQueryService` | `RuleKeywordAdapter.to_keyword_profiles` ✅ 有专门转换器 |
| rule | `RuleQueryService` | **无** —— `repository.py` 里直接 `RuleProfile(...)` ❌ |

**改动（3 个生产文件）**

| 文件 | 改动 | 行数 |
|---|---|---|
| `library/keywords.py` | `to_fuzzy_dict` / `_orm_to_fuzzy_dict` / `_dict_to_fuzzy_dict` **三个出口消亡**，改为 `_orm_to_profile` / `_dict_to_profile` **直接构造 `KeywordProfile`**（不再经 dict 中转）；dict 输入路径**补 `meta_source` 透传**；分隔条与 docstring 修正（原文写「`RuleKeyword` ↔ FuzzyFeature 输入 dict」，而 `FuzzyFeature` 是内核内部产物，此处产出的是 `KeywordProfile`） | 109 → 96 |
| `library/rules.py` | **新增 `RuleAdapter`**（与 `RuleKeywordAdapter` 成对）—— `RuleMethod` → `RuleProfile`；结论形态判定仍归 `RuleService`（adapter 只搬字段）；规则串为空返回 `None` | 171 → 209 |
| `library/repository.py` | 编排层不再构造契约，改为调 `RuleAdapter.to_rule_profile(rm, specificity)`；只保留过滤（去重 / 档位匹配 / 空串跳过） | 144 → 139 |

**边界：本轮不动内核签名**（用户拍板「归属对齐」）—— `NumTskRuleNet` 仍吃裸 dict，契约对象在进内核前仍经 `to_net_dict()` / `to_rule_array()` 拆回 dict ⇒ **契约层目前是中途站，不是终点**（见 §6 L13 / L21）。

**⭐ 行为等价的直接证明**：一次性脚本从备份目录加载**改前**的 `keywords.py`，与改后的 `to_keyword_profiles` 逐字段对拍（12 个案例：ORM 正常 / step 兜底 / span=0 兜底 / lvl 兜底 / dict 三种形态 / numeric 结论 / advisory 结论 / 百分比结论 / 规则串为空 / 规则串 None）⇒ **0 处差异**；唯一有意差异 = dict 输入的 `meta_source` 透传（改前丢弃、改后保留）。

**连带修好的 2 个 dev 脚本**（都因旧出口消失而失效）

| 脚本 | 问题 | 处理 |
|---|---|---|
| `_dev_refs/_verify_kw_parity.py` | 旧基线挂在 `RuleKeywordAdapter.to_fuzzy_dict`（生产代码的历史出口）⇒ 出口一删就 `AttributeError` | **旧基线冻结进脚本**（`_legacy_to_fuzzy_dict`），与生产代码解耦；对拍关系不变 ⇒ 现 PASS |
| `_dev_refs/diag_fuzzy_fix_simulation.py` | 同上（`to_fuzzy_dict`） | 改用新接口 `to_keyword_profiles([kw])[0].to_net_dict()`；**并顺带修好 E16 遗留**（L15）：`rules` 元素早已从 `(rm, desc)` 变成 `(source_ref, rule_description)`（都是 str），但 L144 / L174 仍取 `rm.priority` ⇒ 改为显式把 priority 带进元组，6 处解包点机械对齐 ⇒ **脚本从 exit=1 变成 exit=0** |

**验收**：见 §5 E20 行。
### 2.28 E21：跨包命名对齐（`input_specs.py` → `specs.py`）

**触发**：用户问「`input_specs.py` 这个文件定义了算法入参，但是我觉得 input_specs 这种命名还是太奇怪了，有什么更合适的？」

**诊断：为什么"奇怪"（三条，按重要性）**

| # | 来源 | 证据 |
|---|---|---|
| 1 | **跨包不一致**（最核心） | `expert/specs.py` 与 `fuzzy/input_specs.py` 是**同层（对外接口契约）、同类物（字段字典 + 必填等级）、同一套机制**（都从 `..field_contract` 取同一批纯函数）；两文件 docstring 首句几乎一字不差（「算法入参契约——(调优/fuzzy)需要哪些字段（接口格式 + 必填等级/必填项）」）⇒ 读者在两个算法包之间切换时看到**同物异名** |
| 2 | **限定词 `input` 的消歧前提已失效** | E7-d（§2.13.7.3）给 `specs.py` 加「入参」限定词，理由是「包内同时有两类 spec（层 3 的 `FuzzyKeywordSpec` / `FuzzyRuleSpec`）」。**实测**：层 3 已改名 `elements.py`，类名为 `FuzzyFeature` / `FuzzyRule` / `NumTskRule` / `ParticularRules` ⇒ **fuzzy 包内 spec 词根只剩层 0 一个** ⇒ 消歧前提消失，限定词成为冗余 |
| 3 | **`input` 在本包内撞义** | 「input」在 fuzzy 包内有**两义**：层 0 的「对外接口入参」 vs 内核 `fuzzy_core/profiles.py` 的「**内核输入契约**」（`KeywordProfile` / `RuleProfile`）。后者才真配叫"输入契约"，层 0 抢用 `input` 反而与之竞争 |

**选定 `specs.py`**（用户拍板；4 个候选对比）

| 候选 | 优点 | 顾虑 | 判定 |
|---|---|---|---|
| **`specs.py`** | 与 `expert/specs.py` **跨包对齐**（同层同物同名）；消歧前提已消失；最短 | 单独看不如 `input_specs` 具体，需靠 `fuzzy/__init__.py` 分层清单补语境 | ✅ **选定** |
| `field_specs.py` | 明确「字段规格」，与 `field_contract.py`（通用机制）成对 | 仍与 `expert/specs.py` 不一致；`field` 词根与 `field_contract.py` 混用 | 否 |
| `input_contract.py` | 换成仓库主词汇「契约」 | 同包内出现**两个不同义的 contract**（`library/contracts.py` 是「library 层能力契约」，层 0 是「算法接口契约」）；`input` 撞义仍在 | 否 |
| `fields.py` | 最直白 | 名不副实 —— 文件里还有 `OptimizeDataValidator` 与缺陷档位词表，不止字段 | 否 |

**改动（1 个重命名 + 8 处 import/注释 + 2 处 dev 脚本；字节级操作：BOM / 行尾 / 编码零变化）**

| 类别 | 处数 | 位置 |
|---|---|---|
| 文件重命名 | 1 | `fuzzy/input_specs.py` → `fuzzy/specs.py`（393 行，**内容一字未改**） |
| import 路径 | 4 + 1 注释 | `fuzzy/__init__.py` / `services/parameter_optimize.py` / `tests/test_optimize_smoke.py` / `tests/verify_demo_machine_fields.py` / `schemas/optimization.py`（注释） |
| 注释 / 分层清单 | 3 | `fuzzy/__init__.py` L7（层 0 载体名）+ L18（命名约定 `*_specs` → `specs`）+ `fuzzy_core/profiles.py` L20（命名避让段） |
| dev 脚本 | 2 | `_verify_zero_dep.py`（顶层名泄漏清单 `input_specs` → `specs`）/ `_verify_e2e_db.py`（docstring 记录完整改名链） |

**对外影响：零** —— `__all__` 的 **10 个符号一个不动**（`OPTIMIZE_*_INFO_FIELDS` / `REQUIRED_*` / `OptimizeDataValidator` / `VALID_DEFECT_LEVEL_WORDS*` / `is_valid_defect_level_word`）⇒ 外部调用方零改动。

**验收**：见 §5 E21 行。

**如实边界（本轮明确不做）**：**结构未对齐** —— `expert` 是 `specs.py`（字典）+ `data_validator.py`（校验器）**分文件**，而 `fuzzy` 仍把「字段字典 + `OptimizeDataValidator` + 缺陷档位词表」三者合一于一个 `specs.py`（393 行）⇒ 文件名仍只覆盖其中一样 ⇒ 登记 §6 **L22**，留待下一轮拆分。

### 2.29 E22：双文件改名（`naming.py` → `field_names.py`；`fuzzy_algorithm.py` → `engine.py`）

**触发**：用户两条消息 ——①「`naming.py` 这个文件我建议叫 fields 可能更合适一点」②「`fuzzy_algorithm.py` 这个叫 fuzzy_algorithm 不太合适，看看有没有更合适的名称」。

**诊断 1：`naming.py` → 选定 `field_names.py`（用户拍板）**

| # | 判据 | 结论 |
|---|---|---|
| 1 | `naming` 是否偏泛 | ✅ 是 —— 该文件只管**字段名**的双向映射（3 张表 + 3 个函数 + import 时自检），`naming`（命名）过于宽泛 |
| 2 | 用户建议的 `fields.py` 是否可行 | ⚠️ 有**包内撞名** —— 同包 `specs.py`（E21 刚改名）定义的是**字段字典**（哪些字段 / 必填等级 / 来源模型），层 1 若再叫 `fields.py` ⇒ 包内出现**两个都叫「字段」但管不同东西**的文件；另 `process/algorithms/field_contract.py`（通用机制层）已占用 `field` 词根 |
| 3 | 跨包是否已占名 | ✅ 无 —— 全仓 `naming.py` 仅 fuzzy 一处（expert 包无同类文件）⇒ 改名不涉及跨包一致性 |
| 4 | 选定方案 | **`field_names.py`** —— 保留用户要的 `field` 词根 + 加 `names` 限定「名」，与 `specs.py`（字段**规格**）形成互补而非冲突 |

**诊断 2：`fuzzy_algorithm.py` → 选定 `engine.py`（用户拍板；§0 早已拍板但一直未执行）**

| # | 判据 | 结论 |
|---|---|---|
| 1 | 是否名不副实 | ✅ 是 —— 文件内是类 `FuzzyEngine`（589 行主流程），文件名说 algorithm、类名说 engine |
| 2 | 历史决定 | §0「入口改名」一行在 **E4 执行时即已拍板** `engine.py`，但之后一直没执行 ⇒ **本轮落地** |
| 3 | 包名冗余 | ✅ `fuzzy.fuzzy_algorithm` 的 `fuzzy_` 前缀真冗余（`fuzzy.engine` 更干净） |
| 4 | **跨包分叉（代价，如实记录）** | ⚠️ 4 个算法包入口命名本就是 3+1 分裂：`fuzzy_algorithm.py`（类 `FuzzyEngine`）/ `llm_algorithm.py`（类 `LLMEngine`，**与 fuzzy 完全同构**）/ `empirical_algorithm.py`（类 `EmpiricalReasoning`）/ `expert/algorithm_engine.py`（类 `AlgorithmEngine`）⇒ 改 fuzzy 后它成为**唯一不用 `*_algorithm.py` 的包**。判断：llm 那个「文件说 algorithm、类说 Engine」的组合**本身就不自洽**，fuzzy 改 `engine.py` 后**文件↔类名严格对应** ⇒ 净收益为正；但**全仓统一与否需另行拍板**（登记 §6 **L4 / L23**） |

**改动（3 个文件重命名 + `naming` 72 处 + `fuzzy_algorithm` 44 处引用同步；字节级操作：BOM / 行尾 / 编码零变化）**

| 类别 | 处数 | 位置 |
|---|---|---|
| 文件重命名 | 3 | `fuzzy/naming.py` → `fuzzy/field_names.py`（353 行，BOM=False）/ `fuzzy/fuzzy_algorithm.py` → `fuzzy/engine.py`（588 行，**BOM=True**）/ `_dev_refs/_verify_naming_forward_parity.py` → `_dev_refs/_verify_field_names_forward_parity.py` |
| 引用同步（`naming` → `field_names`） | 72 | 生产 4 文件（`fuzzy/__init__.py` / `services/parameter_optimize.py` ×7 / `fuzzy/specs.py` ×2 / `field_names.py` 自身错误前缀 ×5）+ dev 脚本 8 个 + 执行文档 |
| 引用同步（`fuzzy_algorithm` → `engine`） | 44 | 生产 7 文件（`process/algorithms/__init__.py` / `fuzzy/__init__.py` ×2 / `engine.py` 自身 / `fuzzy/specs.py` ×2 / `fuzzy_core/parsing.py` / `fuzzy_core/models/nets.py` ×2 / `fuzzy/library/__init__.py` ×2）+ 测试 3 个 + dev 脚本 9 个 |
| 包 docstring 润色 | 1 | `fuzzy/__init__.py` L18 命名约定补 `field_names` / `engine` 两条 |

**对外影响：零** —— `field_names` 的 6 个公开符号（3 张表 + 3 个函数）一个不动；`engine.py` 的 `FuzzyEngine` 类名与 `__all__` 一个不动 ⇒ `from process.algorithms.fuzzy import FuzzyEngine` 这条**主链路零影响**。

**⭐ 行为等价的最强证明**：不止与历史快照比，而是**用改前备份还原出完整 backend 副本**，在**同一份生成器脚本**下分别跑改前 / 改后 —— `_golden_E22_baseline.json`（改前，221409 字节）vs `_golden_E22.json`（改后，221409 字节）⇒ **整棵 JSON 逐条 diff = 0**；且与上一轮 `_golden_E21.json` 的 `details` 也**逐条相等**（49 样本）。

**对拍副口径说明（如实记录，避免后人误读为回归）**：`_verify_field_names_forward_parity.py` 会报 **36 处差异**，但它们**全部落在 §2「边界输入」段** —— 旧冻结实现（合并表口径）把裸前缀 `BT` / `IV` / `PP` 等**直接映射**，新契约（拆分表口径）按 **E5/E6 既定语义**（裸前缀退役、`brl_temp` 归前缀表、`FAMILY_FIELD_ALIAS` 整族删除）**保持原样**。同一脚本的 **§1 真实入参集合（84 字段）逐键差异 0**、**§4 往返闭合不吻合 = 无**、**§3 非字符串键两侧行为一致** ⇒ **真实业务路径零差异**；这 36 处是 E5~E6 累计的既有口径差，**与本轮无关**（本轮未触碰任何映射表与函数体，仅改模块名与错误信息前缀）。

**验收**：见 §5 E22 行。

### 2.30 E23：推荐结果层改名（`aggregation.py` → `recommendations.py`）

**触发**：用户消息 ——「`aggregation.py` 这个文件命名也有点问题，这个应该是推理完成后算法格式化输出结果，叫 aggregation 有点问题」。

**模块实际职责（读全文核实，224 行）**

| 出口 | 做什么 | 性质 |
|---|---|---|
| `aggregate()` | 同参数的多条规则调整量归并：数值层裸累加 / 提示层跨层覆盖 / 文本建议单独分流 | **带业务策略的语义归并**（不是纯格式化） |
| `to_recommendations()` | → `AlgorithmRecommendation`：算 `recommended_value` / `confidence` / `direction` / `reason` / `source` | **格式化输出**（用户所指的半边） |

外加两个中间态 dataclass：`RuleAdjustment`（推理层产出）→ `AggregatedAdjustment`（归并后）。

**诊断：现名只覆盖了一半**

| # | 判据 | 结论 |
|---|---|---|
| 1 | 用户判断是否成立 | ✅ 成立 —— `aggregation` 覆盖了「归并」，**完全没体现「产出对外推荐契约」这半**；`engine.py` 把它当作出口直接用（L221-225），读代码的人只知它「把同参数合并」，不知它就是产出 `AlgorithmRecommendation[]` 的那层 |
| 2 | 「格式化输出」是否完整 | ⚠️ 只覆盖一半 —— `aggregate()` 做的是**带策略的语义归并**（数值层裸累加 vs 提示层覆盖是业务决策），纯「格式化」不足以描述它 |
| 3 | 命名锚点 | 用**「这层产出什么」**命名最准：出口就是 `AlgorithmRecommendation[]`，service 层也一律称它「推荐」（`all_recommendations` / `_recommendations_to_adjustments`） |
| 4 | 复数风格 | ✅ 与本仓主流一致（`specs` / `contracts` / `profiles` / `elements` / `sources` / `nets` / `rules` / `keywords`） |
| 5 | **词根撞名（如实记录代价）** | ⚠️ 仓库已有 `process/models/recommendation.py`（ORM 模型 `Recommendation`），且 **E6 曾为消解与它的同名冲突把算法层 `Recommendation` 改名 `AlgorithmRecommendation`**。本次是**模块名**（不同目录，Python 层面不冲突），但仓库内出现两个「recommendation」词根的模块（ORM 持久化 vs 算法层产出）⇒ 登记 §6 **L24** |

**候选对比（用户拍板 `recommendations.py`）**

| 候选 | 覆盖归并 | 覆盖格式化输出 | 评价 |
|---|---|---|---|
| **`recommendations.py`** | ✓（产出即归并后结果） | ✓ | **选定** —— 与 `AlgorithmRecommendation` / `to_recommendations()` / `all_recommendations` 四者词根统一；复数风格与 `specs.py` / `contracts.py` 一致 |
| `output.py` | ✗ | ✓ | 太泛；`output` 在 Python 生态里常指输出流/输出目录 |
| `formatter.py` | ✗ | ✓ | 只覆盖格式化半边，丢掉归并语义；「格式化」字面偏轻 |
| `presenter.py` | ✓ | ✓ | 语义完整但本仓无 DDD 词汇先例，团队可读性下降 |
| `advice.py` | ✗ | ✗ | ❌ 与模块内 `advice`（文本建议子概念：`RuleAdjustment.advice` / `advice_items`）撞名 |
| 不改名，仅澄清 docstring | — | — | 用户明确指出命名有问题，已排除 |

**改动（2 个文件重命名 + `aggregation` 9 处引用同步；字节级操作：BOM / 行尾 / 编码零变化）**

| 类别 | 处数 | 位置 |
|---|---|---|
| 文件重命名 | 2 | `fuzzy/aggregation.py` → `fuzzy/recommendations.py`（224 行，BOM=False）/ `tests/test_fuzzy_aggregation.py` → `tests/test_fuzzy_recommendations.py`（151 行，BOM=False） |
| 引用同步（`\baggregation\b` → `recommendations`） | 9 | 生产 3 文件（`fuzzy/engine.py` ×3：import + 2 处注释；`fuzzy/__init__.py` ×1：分层说明；`fuzzy_core/tests/test_inference_gates.py` ×1：注释）+ 测试 1 文件（×3）+ dev 脚本 1 个（`_verify_zero_dep.py` ×1：顶层名泄漏清单） |
| 手工润色 | 3 | `recommendations.py` docstring 首句「聚合层」→「推荐结果层」/ `fuzzy/__init__.py` L9 分层措辞「建议聚合」→「推荐结果产出」+ L18 命名约定补 `recommendations` 一条 / `engine.py` 两处注释由「聚合逻辑已抽到」改为「归并与格式化逻辑已抽到」/ 测试 docstring 首句 |

> ⚠️ 替换用正则 `\baggregation\b`，**不会**命中 `aggregate()`（函数名）/ `AggregatedAdjustment`（类名）/ `aggregated`（变量名）—— 三者一律不动。

**对外影响：零** —— `aggregate()` / `to_recommendations()` / `RuleAdjustment` / `AggregatedAdjustment` 四个公开符号一个不动；`engine.py` 的 import 路径同步后行为完全一致 ⇒ `FuzzyEngine.recommend()` 主链路零影响。

**⭐ 更强的等价证明（比 E22 多一层）**：① 用备份还原「改前」完整 backend 副本，**同一生成器脚本**分别跑改前 / 改后 ⇒ 整棵 JSON **逐条 diff = 0**（两份均 221409 字节），且与 `_golden_E22.json` 的 `details` 逐条相等；② 另做**逐行 diff**（改后 vs 改前备份）⇒ `recommendations.py` **仅 docstring 首句 1 行不同**（224 → 224 行），其余 5 个受影响文件共 22 行差异，**逐条可解释为改名/措辞，零逻辑改动**。

**验收**：见 §5 E23 行。



### 2.31 E24：内核论域实例与隶属度类型层的清理（`features.py` 瘦身 + tri 退役 + 桶中心收口）

**触发**：用户消息 ——「`features.py` 1-92 这个我那件我觉得需要改造一下，你觉得呢？」（E23 终态下的 92 行版本）。

**为什么这一轮值得动**：E9 把 `FuzzyFeature` 从 `nets.py` 拆出来时只是**搬移**；本轮是第一次回头**审内核自身的类**。审下来四类问题叠在一起：

| # | 问题 | 证据 | 性质 |
|---|---|---|---|
| 1 | `functional.py` 里 5 组隶属度函数**同名实现前后段覆盖** | 文件末尾 L246-357 又完整重写了一遍 `gaussian_mf` / `triangular_mf` / `trapezoidal_mf` / `bell_mf` / `singleton_mf`（**迁移时的粘贴事故**） | **死代码** —— 后写的覆盖先写的，先写的那份**从未被执行过** |
| 2 | `features.py` 4 个实例属性**只写不读** + 1 个死方法 | `f_type` / `f_name` / `f_interval` / `f_membership_type` 在生产代码里**零读取点**；`get_all_value()` **全仓零调用** | **假契约** —— 看着像契约，实际没人用 |
| 3 | `tri` 是**死分支**，而 `MEMBERSHIP_TYPES` 声明了三种类型 | `features.py` 实现 `gauss` + `tri`，但 `tri` 在生产 / 回归 / 规则库中**零调用**；`trap` **从未实现**；`MEMBERSHIP_TYPES` 更是**定义了零使用** | **声明与实现对不上** |
| 4 | 桶中心**内联**在 `features.py`，与 `LEVEL_WORDS_BY_LVL` 的对应关系只写在注释里 | 7/9 档的桶位置**零断言覆盖** | **两处定义靠人工保持一致** |

**分 4 批做、每批独立验收**（用户拍板「按 1→2→3 全做，每批验收」）：

| 批次 | 内容 | 净变化（内容行） |
|---|---|---|
| **E24-1** | `functional.py` 删 L246-356 重复段 | 356 → **245** |
| **E24-2** | `features.py` 瘦身（删 4 只写不读属性 + `get_all_value` + 2 个从未被读取的**参数**） | 91 → **90** |
| **E24-5** | 删 tri 分支 + 收紧 `macros.MEMBERSHIP_TYPES` | `features.py` 90 → **82**；`macros.py` 232 → **236** |
| **E24-6** | 桶中心抽有名纯函数 + 补 3/5/7/9 档直接断言 | `macros.py` 236 → **275**；`features.py` 82 → **78**；pytest 30 → **32**（收尾精简 1 个同义反复用例） |

#### E24-1：`functional.py` 的迁移粘贴事故（删 L246-356 重复段）

**问题**：文件末尾 L246-357 又把 5 个隶属度函数**完整重写了一遍**。Python 的**后定义覆盖先定义** ⇒ 前半段那 5 个实现**从未被执行过**。

**⭐ 而且重复段不是「等价副本」—— 它是另一套实现**：

| 函数 | 改前**实际生效**的版本（重复段） | 改前**从未生效**的版本（前段） | 差异 |
|---|---|---|---|
| `triangular_mf` | 纯数组版（`np.zeros_like` + 掩码） | `tri_mf` 委托版（scalar / list / ndarray 通用，**带 `a<=b<=c` 断言**） | **scalar / list 输入抛 `TypeError`**；断言丢失 |
| `trapezoidal_mf` | 同上（纯数组版） | `trap_mf` 委托版（**带 `a<=b<=c<=d` 断言**） | 同上 |
| `gaussian_mf` | `np.exp(-((x-mean)**2)/(2*sigma**2))` | `gauss_mf` 委托版 | 数值**完全相同** |
| `bell_mf` | 逐字相同 | 逐字相同 | 无 |
| `singleton_mf` | 逐字相同（多一句「清晰化用」） | 逐字相同 | 无 |

**改后（唯一版本生效）的实测行为差**（改前副本 vs 改后，逐项实跑）：

| 输入 | 改前 | 改后 |
|---|---|---|
| `triangular_mf(scalar)` | ❌ `TypeError: 'float' object is not subscriptable` | ✅ `array(1.)` |
| `triangular_mf(list)` | ❌ `TypeError: '>' not supported between instances of 'list' and 'int'` | ✅ `array([0., 1., 0.])` |
| `triangular_mf(ndarray)` | ✅ `array([0., 1., 0.])` | ✅ **完全相同** |
| `trapezoidal_mf(scalar / list)` | ❌ `TypeError` | ✅ 正常返回 |
| `trapezoidal_mf(ndarray)` | ✅ 正常 | ✅ **完全相同** |

⇒ **本轮唯一的真实行为修复**：`triangular_mf` / `trapezoidal_mf` 从「只吃 ndarray」变「scalar / list / ndarray 通用」，且**端点序断言恢复**。
⇒ **生产链路零影响**：`features.py` 只用 `gauss_mf`，`nets.py` 的输入全是 ndarray ⇒ 快照 diff 恒为 0。

**改动**：1 个文件、**删 1 段（L246-356）、零新增**；`tri_mf` **本体保留**（`trap_mf` 内部 `lambda x: tri_mf(x, a, b, b)` 依赖它）。

#### E24-2：`features.py` 瘦身（删只写不读属性 + 死方法 + 假参数）

**取证**（改前）：4 个属性在生产代码里**只有写入点**，唯一读取点是 `_dev_refs/_probe_features2.py`（临时探针）；`get_all_value()` **全仓零调用**（只在历史设计文档 `_refs/system/ai/fuzzy-engine-migration-design.md` L182 提及）。

**决策**：走**路线 B** —— 不只删属性，连 `f_name` / `f_type` 两个**从未被读取的参数**一起删（消灭「假契约」：调用方被迫传一个内核根本不看的值）；`nets.py` 3 处构造同步去掉首个位置实参。

**改动**：`features.py`（91 → 90 行）+ `nets.py`（3 处构造点，677 行不变）。

**符号面断言**（4 条全过）：构造签名收缩 / 死方法 `get_all_value` 移除 / 只写不读属性 4 → **0** / 每个保留属性都有真实读取方。

**等价性**：**三方对拍** —— A（改前）/ B（改后）/ C（上一轮留存的基线 JSON）两两 diff = **0**（数值面 / 推理链路 / 反模糊化三面全等）。

#### E24-5：tri 分支退役 + `MEMBERSHIP_TYPES` 收紧（声明与实现同源）

**问题**：`macros.MEMBERSHIP_TYPES = ['gauss','tri','trap']` —— **定义了零使用**；而 `features.py` 只实现了 `gauss` 与 `tri`，`trap` **从未实现** ⇒ 一张表和实现对不上。

**改动**：
- `MEMBERSHIP_TYPES` 收紧为**元组** `('gauss',)`（不可变，防外部改写）；
- `features.py` `from ..macros import MEMBERSHIP_TYPES` 做**成员校验** ⇒ 类型不在白名单 ⇒ 直接 `ValueError`（错误信息附当前支持列表）⇒ **声明与实现从此同源**；
- `features.py` 删 `tri` 分支（**90 → 82 行**）；`tri_mf` **保留在 `functional.py`**（`trap_mf` 内部依赖）。

**等价性**：数值面 diff = **0**；行为面差异**恰 2 项**，且**都是「tri 可用 → 明确拒绝」**（这是本轮唯一的有意行为变化）。全仓 AST 扫 `FuzzyFeature` 构造点 = **4 个，全是 gauss**，非 gauss = **0**。

#### E24-6：桶中心抽有名纯函数 + 补 3/5/7/9 档直接断言

**问题**：桶有两套必须对齐的定义 —— ① 桶**位置**（论域上的中心）内联在 `features.py`；② 桶**语义**（档位词）= `LEVEL_WORDS_BY_LVL` 的词序。此前 ① 与 ② 的对应关系**只写在注释里**，全靠人工保持一致 ⇒ **没有任何断言兜底**（7/9 档零覆盖）。

**改动**：
- `macros.py` 新增模块级**纯函数** `bucket_centers(f_interval, lvl)`（桶 0 = 下界、桶 `lvl-1` = 上界、中间桶 = 等分位点）；
- `features.py` 改调该函数（`means = bucket_centers(f_interval, f_level)`）；
- `test_macros.py` 补 **2 个用例**（`test_bucket_centers_direct_values` 直接断言 3/5/7/9 档的**具体数值**、`test_bucket_centers_align_with_word_table` 断言「词表第 i 个词 ↔ 第 i 个桶中心」的百分比口径）；
- `test_nets.py` 曾补 **1 个跨模块用例**（`test_feature_means_match_bucket_centers`）—— **收尾时删除**（理由见下方「收尾精简」）。

**7 档的桶位置（易错）**：桶 1 = `q(1/6)` = 200/6 = 33.33，**不是** 200/3 —— 第一版期望值就写错了，被新断言**当场拦下**（pytest 1 failed）⇒ 证明断言真在起作用，改对后 32 passed。

**等价性**：用备份还原「改前」完整 backend 副本 ⇒ **同一生成器脚本**改前 / 改后各跑一次 ⇒ 整棵 JSON 逐条 diff = **0**；其中 `params|lvlN|...|d` 项就是**桶中心 + sigma**，共 **96 项逐项相等**。

**收尾精简（用户反馈后）**：用户消息 ——「你写这么多测试干什么？后续修改可以不用写那么多测试」。复核本轮补的 3 个用例：

| 用例 | 参照系 | 处置 |
|---|---|---|
| `test_bucket_centers_align_with_word_table` | **业务口径**（词表下标 ↔ 论域百分比，独立于实现） | ✅ 保留 |
| `test_bucket_centers_direct_values` | 桶中心**定义**本身（3/5/7/9 档写死数值） | ✅ 保留 |
| `test_feature_means_match_bucket_centers` | **无** —— `features.py` 正是调 `bucket_centers`，两者不可能不一致 ⇒ 同义反复 | ❌ **删除** |

⇒ `test_nets.py` 同步删掉 `bucket_centers` 的 import；pytest 33 → **32**。

**⭐ 本轮沉淀的四条方法论**

| # | 结论 | 证据 |
|---|---|---|
| 1 | 「删死代码」在本仓**不会**破坏行为 —— 但必须**用改前副本同脚本对跑**来证明，不能靠推理 | 4 批全过：数值面 / 推理链路 / 反模糊化 diff 恒为 0 |
| 2 | 行为差异必须**逐条列出来**，不能只报「等价」 | E24-5 唯一的有意差异是「tri 可用 → 明确拒绝」，恰好 2 项，均已列明 |
| 3 | **断言要写具体数值**，不能只写关系（`>` / `<`） | E24-6 的 7 档期望值写错时被当场拦下 ⇒ 断言确实在起作用 |
| 4 | 测试用例要有**独立参照系** —— 「实现 = 实现」的同义反复断言是零价值护栏 | `test_feature_means_match_bucket_centers` 断言 `FuzzyFeature` 均值 == `bucket_centers`，而 `features.py` 正是调它 ⇒ 收尾时删除 |

**验收**：见 §5 E24 行。

### 2.32 E25：隶属度函数层重组（`functional.py` → `memberships.py` + `defuzz.py` + 统一签名）

**触发**：用户连续四条消息 ——①「接下来我们回到这一部分 …fuzzy_core，首先我们讨论这部分是干什么的」②「`functional.py` 1-246 先回到这个文件，首先文件命名是否正确？……其实这个文件我觉得应该叫 functions，你觉得呢？」③「可以留在这里，另外，对于实际应用中，一般有哪些隶属度函数？这才是关键问题，目前不能因为我们只用了 gauss_mf 而不考虑别的」④「我的建议是先解决 functional 这里的问题，另外还有一点需要确定，就是解模糊是否应该放在这里？如果不放在这里，那么 functional 应该改名成 memberships，主要看怎么调整结构，我计划是这个文件主要就是存放隶属度函数」+ 拍板「**1. 走统一签名 2. 可以正名**」。

**诊断（三条，与用户判断一致）**：

1. **命名**：`functional.py` 既不是「函数」也不是「功能」，它装的是**隶属度函数** ⇒ 应叫 `memberships.py`（复数风格与仓库既有 `macros.py` / `profiles.py` / `nets.py` / `rules.py` 一致）。
2. **解模糊不该同处** —— 三条硬理由：**推理阶段不同**（隶属度 = 推理链第 1 步，反模糊化 = 最后 1 步，中间还隔着蕴含与聚合两步）；**输入范式不同**（`(标量/数组, 中心, 宽)` → [0,1] vs `(采样序列, 隶属度序列)` → 实数）；**扩展节奏不同**（`macros.DEFUZZ_METHODS` 已列 `centroid/bisector/mom/som/lom` 5 种只实现 1 种，而 0/1 阶 T-S **根本不需要**反模糊化）⇒ 拆出 `defuzz.py`。
3. **「按推理类型分节」是错的分类轴**（用户提的 mamdani / 0阶TSK / 1阶TSK）：那是**推理代数**轴，而仓库已有**结论形态**轴（numeric / advisory）；隶属度函数是**横跨三类的公共模糊化层** ⇒ 按推理类型分节会出现「3 节里 2 节是空」。

**E25-1：拆文件改名**

- `functional.py`（245 行）→ **`memberships.py`**（隶属度族）+ **`defuzz.py`**（反模糊化）；4 处 import 同步（`features.py` / `nets.py` / `fuzzy_core/__init__.py` / `test_nets.py`）。
- ⚠️ **踩坑：模块与函数同名遮蔽** —— `from .defuzz import *` 把**函数** `defuzz` 绑到包顶层，**覆盖了同名子模块** `fuzzy_core.defuzz` ⇒ `from fuzzy_core import defuzz` 拿到的是函数 ⇒ 对拍脚本报 `AttributeError: 'function' object has no attribute 'centroid'` ⇒ 改为 `from .defuzz import centroid`（只导出函数，`defuzz` 保留模块语义）。

**E25-2：统一签名 + 9 形状族**

- 统一签名 **`mf(x, center, width, shape=None)`**，`width` = 该形状在论域上的**总跨度**（高斯 = 2σ、三角 = c-a、梯形 = d-a）。
- ⭐ **高斯的 2 因子陷阱**：老 fuzzykit = `exp(-(x-μ)²/(2σ²))`（σ = 标准差），教材标准广义高斯 = `exp(-|((x-μ)/σ)|^p)` ⇒ **差一个 2**（`μ(c±σ)` 从 0.6065 变 0.3679）⇒ 以 **p=2 对齐老口径**为锚点：p=2 走老式原式（**逐位相等**），p≠2 走通用式。
- ⭐ **数值等价性证明**：现状 `σ = 论域宽/(2*(lvl-1))`，而等分位点相邻间距 = `论域宽/(lvl-1)` ⇒ 恒有 `σ = 间距/2`；`features.py` **保留原 σ 推导式**、`width = 2σ`（乘 2 精确）、函数内 `σ = width/2`（精确还原）⇒ **逐位相等**。
- 9 个形状：高斯 / 双高斯 / 三角 / 梯形 / 广义钟形(exp 型) / 代数钟形 / S 型 / Z 型 / 单点（**按领域完备性补齐**，而非按当前调用点补齐 —— 用户明确「不能因为我们只用了 gauss_mf 而不考虑别的」）。
- **正名**：老 `bell_mf` 实为 Sugeno **代数型**（公式 `1/(1+z^{2b})`）却叫「钟形」⇒ 改名 `algebraic_bell_mf`；真正的广义钟形（exp 型 `exp(-|z|^{2m})`）另起 `bell_mf`。
- **修掉 2 个真 bug**：① 老 `bell_mf` 缺 `|·|` ⇒ b<1 且 x<center 时隶属度 **> 1**（实测 2 个越界点）；② 老 `singleton_mf` 对 list 输入 `x == center` 得标量 `False` ⇒ **结果全 0**（能跑但算错）。
- `assert` 当校验 ⇒ 改 `ValueError`（`python -O` 下 assert 被优化掉，等于没校验）。

**E25-3：白名单由分派表派生**

- `macros.MEMBERSHIP_TYPES = tuple(MEMBERSHIP_SPECS.keys())` ⇒ **声明与实现同源**（新增形状只需加一行分派，白名单自动跟上）。
- 新增 `DEFAULT_MEMBERSHIP_TYPE = 'gauss'`；`nets.py` 3 处硬编码 `'gauss'` 改用常量。
- `defuzz.py` 补 `__all__`。

**E25-4：分派收尾**

- `features.py` 改分派：`spec = MEMBERSHIP_SPECS[type]` ⇒ `membership_func` / `membership_shape` / `membership_dict` 三者同源于一份登记项。
- `membership_shape` 取自 `spec.default_shape` ⇒ **形状参数的单一真源**（原先函数内默认值与分派表各写一份，迟早漂移）。
- 论域**退化 / 倒挂**时打 warning（不改数值 —— 改数值会动到生产推理结果）。

**⭐ 本轮踩坑（四条）**

| # | 坑 | 表现 | 修法 |
|---|---|---|---|
| 1 | 模块与函数同名遮蔽 | `from fuzzy_core import defuzz` 拿到函数而非模块 | `__init__.py` 只导出 `centroid`，保留 `defuzz` 为模块语义 |
| 2 | 高斯的 2 因子陷阱 | 照抄教材标准式 ⇒ `μ(c±σ)` 从 0.6065 变 0.3679 | 以 p=2 对齐老口径为锚点，p=2 走老式原式 |
| 3 | **标量 vs 数组的除零语义不同** | Python float 除零 → `ZeroDivisionError`；numpy 标量除零 → `inf`/`nan`。改前老实现把桶中心/σ 以 **numpy 标量**传入 ⇒ 退化论域产出 nan；新实现若把标量转成 Python float ⇒ 同一场景**从「静默 nan」变成「内核崩溃」**（实测退化论域差异 153 处） | `_prepare` 的标量统一转 `np.float64`；对拍脚本两侧都用**标量**调用（否则比的是两种范式） |
| 4 | **上游论域可能倒挂 / 退化** | `engine.py` 推测论域 = `max_val = 当前值 * 2` ⇒ 当前值为**负** ⇒ 区间倒挂；为 **0** ⇒ 区间退化。改前 σ **带符号**（高斯只用 σ² ⇒ 正常出数），改后 `width` 为负 ⇒ 会被校验拦下 | 在 `features.py` 层把跨度**取绝对值**（对高斯**逐位等价**，因为只用 σ²）+ 退化/倒挂各打一条 warning |

**验收**：见 §5 E25 行。

**对拍脚本**：`_dev_refs/_e25_diffcheck.py`（内嵌改前 `functional.py` 的权威基线）—— 5 档对拍：① 严格档（高斯 / centroid / defuzz，atol=0）② 参数化重述档（rtol=1e-12）③ 有意行为变化档（5 项）④ 手算参照系（12 解析性质 + 9 形状值域 + 统一签名契约）⑤ FuzzyFeature 端到端（4 种论域 × 2 档 × 51 点逐点，含倒序与退化论域）。⇒ **保留为归档资产**（与 `_golden_E5.json` ~ `_golden_E23.json` 同一先例），供后续轮次复跑对照。

**临时文件处置**：

- ✅ **删除 4 个 E24 轮一次性取证产物** —— `_probe_features.py`（依赖已删除的 `functional` 模块 ⇒ 现在必然 `ImportError`）、`_probe_features.txt`、`_probe_features2.py`（调 `f_membership_type='tri'`，而 `tri` 在 E24-5 已退役 ⇒ 必然报错）、`_probe_features2.txt`；四者的取证能力已被上面对拍脚本的 `feature_suite()` 完全覆盖。
- ✅ **保留** `_e25_diffcheck.py`（内嵌旧实现基线，是唯一「可直接运行」的旧实现对照资产）。



### 2.3 引用点全景（改名成本评估，2026-10-23 实测）

| 引用点 | 形式 | 性质 |
|---|---|---|
| `process/algorithms/__init__.py` L29 | `from .fuzzy import engine` | 仅触发 `register` |
| `process/algorithms/fuzzy/__init__.py` L22 | `from .engine import FuzzyEngine` | 包级导出 |
| `process/services/parameter_optimize.py` L36 / L68 | `from process.algorithms.fuzzy import FuzzyEngine` | ✅ 走包级导出 |
| `process/services/parameter_optimize.py` L245 | `FuzzyEngine.to_business_name(...)` | 类方法引用 |
| `process/services/parameter_optimize.py` L534-536 | `FuzzyEngine.FIELD_NAME_ALIAS` 等 3 张表 | 类属性引用 |
| `process/services/condition.py` | 仅注释中出现 `FuzzyEngine` 字样 | 无 import |
| `_dev_refs/diag_fuzzy_bucket_shift_impact.py` L56 | `from ...fuzzy.engine import FuzzyEngine` | 开发脚本 |
| `_dev_refs/diag_fuzzy_rule_journey.py` L467 | 同上 | 开发脚本 |
| `_dev_refs/diag_fuzzy_level_word_crash.py` L42 | 同上 | 开发脚本 |
| 注释引用 × 6 | `nets.py` L6/L17、`specs.py` L21/L370、`sanity_check.py` L134 | 文档字符串 |

**关键事实**：**生产代码中零处 import 模块路径 `...fuzzy.engine`**，全部走包级导出。
⇒ 改名的全部成本 = **1 处生产 import + 3 处 dev_refs + 6 处注释 = 10 处**，其中生产路径只有 1 行。
⇒ **包级导出 `from process.algorithms.fuzzy import FuzzyEngine` 保持不变 ⇒ 外部调用方零影响。**

### 2.4 命名问题现状 —— 10 类

见 §3.3 台账（N1~N12）。

---

## 3. 命名对照表（E1-b 交付物）★

### 3.1 三套命名空间（必须先分清，这是最易出错的地方）

| 命名空间 | 示例 | 谁产出 | 谁消费 | 转换点 |
|---|---|---|---|---|
| **业务字段名** | `inj_spd_1`、`brl_temp_3`、`noz_temp` | 前端 / DB | `parameter_optimize` 层 | `field_names.py` 翻译（E22，原 `naming.py`） |
| **算法字段名** | `IV0`、`BT3`、`NT` | `field_names.py` 翻译后 | **模糊推理内部全部** | `to_business_name()` 反向出口 |
| **规则库缺陷码** | `SHORTSHOT`、`FLASH` | 反馈 `keyword_name` | 规则查询 `defect_code` | 直接对应 |

**规则（写死，不可违反）**：

1. `context['process_parameter']` **进入 `recommend()` 后已经是算法命名空间**
   （由 `parameter_optimize._normalize_field_name_by_spec` 翻译完成）。
   ⇒ 算法内部一律使用算法名，**禁止**在算法层出现业务名。
2. `to_business_name()` 是**唯一的反向出口**，只允许编排层调用。
3. 业务名 ↔ 算法名的映射表**只有一份**（`FIELD_NAME_ALIAS` / `FIELD_INDEX_OFFSET`），
   双向共用，禁止出现第二份硬编码映射。
   （E4-b 起不再有「整段族」映射表 —— 段号口径统一为 1-based 对齐，见 §2.9）

> ⚠️ 现状风险点：`specs.py` L14 已明确写「工艺参数走的是**另一套**命名空间」，但这条规则**只写在注释里**，
> 代码里没有任何机制保证混用会被发现。**E4-a 抽 `naming.py`（E22 已改名 `field_names.py`）时要把这条规则变成可执行的约束**
> （已落地：表间一致性 import 时自检，见 §2.8）。

### 3.2 术语总表

| 概念（中文） | 当前代码标识 | 目标标识 | 所在层 | 说明 |
|---|---|---|---|---|
| 模糊推理引擎 | `FuzzyEngine` | **不变** | 编排层 | 包级导出唯一符号 |
| 业务→算法字段名映射 | `FIELD_NAME_ALIAS` | ✅ → `field_names.py` | 契约层 | **23 条**（⚠️ 原写 33 条，实测为 23 条 = 前缀 11 + 完整 12；E4-a/E4-b 已改） |
| 段号偏移（1-based→0-based） | `FIELD_INDEX_OFFSET` | ✅ → `field_names.py` | 契约层 | 11 条（E4-a/E4-b 已改；`brl_temp` 偏移 **0**，料筒温度为 1-based 同构） |
| 整段族映射 | ~~`FAMILY_FIELD_ALIAS`~~ | ⛔ **已删除** | — | E4-b 整表删除（族映射概念消失，段号统一 1-based 对齐，见 §2.9） |
| 算法→业务字段名 | `to_business_name()` | ✅ → `field_names.py` | 契约层 | 唯一反向出口（E4-a 已改；`FuzzyEngine` 保留兼容入口） |
| 规则查询上下文 | `RuleQueryContext` | 不变 | 服务层 | 6 字段 |
| 已解析规则 | `ResolvedRule` | 不变 | 服务层 | 5 字段 |
| 结论形态 | `conclusion_kind` = `'numeric'`/`'advisory'` | 不变 | 服务层 | ⚠️ 非规则库层级 |
| 规则特异级 | `specificity` = 1~4 | 不变 | 服务层 | ⚠️ docstring 写「三级」实为四级 |
| 档位词 | `level` = `'low'`/`'very_low'` | 不变 | 内核 | 词，不是数字 |
| 模糊等级数 | `lvl` / `f_level` | 统一 `level_count` | 适配层/内核 | ⛔ E3 **不做**（`'lvl'` 是内核输入契约 key，见 §6 L9） |
| 论域区间 | `min_val`+`max_val` / `f_interval` | 统一 `interval` | 适配层/内核 | ⚠️ 现在两种表达 |
| 隶属度函数类型 | `f_membership_type` = `'gauss'`/`'tri'` | 不变 | 内核 | |
| 参数名（算法侧） | `'param'` | **`param_name`** | 中间态 | ✅ E3 已统一（`to_dict()` 的 `'param'` 是对外契约，不动） |
| 调整量（中间态） | `'delta'` | `delta` | 中间态 | 最终态无此概念，见 N4 |
| 原始激活度 | `'activation'` | `activation` | 中间态 | 单条规则的激活度 |
| 激活度之和 | `'activation_sum'` | `activation_sum` | 中间态 | 同参数多规则累加 |
| 置信度 | `confidence` | `confidence` | 输出态 | 语义 = **平均激活度**（见 §3.5） |
| 元数据来源 | `'source'` | **`meta_source`** | 适配层 | ✅ E3 已改 |
| 推理层归属 | `'source'` | **`layer`** | 中间态 | ✅ E3 已改 |
| 字段体检分类 | `classification` = `authority`/`guessed`/`unknown` | 不变 | 编排层 | |
| 推测论域标记 | `FIELD_SOURCE_GUESSED` = `'guessed'` | 不变 | 编排层 | |
| 算法侧关键字规格 | 散落在 `adapters` dict / `nets.py` 输入 | **`FuzzyKeywordSpec`** | 契约层 | ✅ E7 显式化（三处形状本就一致，见 §2.12） |
| 算法侧规则规格 | `ResolvedRule.rule_str` + 两个平行数组 | **`FuzzyRuleSpec`** | 契约层 | ✅ E7 显式化（⚠️ 内核 `FuzzyRule` 是**解析器**，非本概念） |

### 3.3 同名不同义 / 语义冲突台账

| # | 冲突描述 | 位置 | 处置 | 执行轮次 |
|---|---|---|---|---|
| **N1** | **`'source'` 一词两义**：元数据来源（`'guessed'`）vs 推理层（`'numeric'`）；两个 dict **会一起传进** `net.predict()` | `adapters` 产出 / `fuzzy_algorithm.py` L402 / L487 / L534 | 元数据侧 → `meta_source`；结果侧 → `layer` | **E3** ✅ 已修 |
| **N2** | **同一东西三个名字**：`rec['param']` / `AlgorithmRecommendation.param_name` / `to_dict()` 输出 key `'param'` | L599 / base.py dataclass | 中间态与 dataclass 统一 `param_name`；**`to_dict()` 保持 `'param'`**（对外契约，不动） | **E3** ✅ 已修 |
| **N3** | **等级两种叫法**：`lvl`（适配层 dict）/ `f_level`（`FuzzyFeature`）；且 `'level'` 又指档位词（`'low'`） | `keyword_dicts` / `nets.py` L110 | 统一 `level_count`；`level` 保留给档位词 | ⛔ **不做**（`'lvl'` 是内核输入契约 key，改名必动内核，见 §6 L9） |
| **N4** | **`'delta'` 中间态有、最终态无**（被折进 `recommended_value`） | L489 / L642 | 中间态保留 `delta`；`to_recommendations()` 显式写明 `recommended = current + delta * factor` | **E3** ✅ 已修 |
| **N5** | **`layer` 三义**：结论形态（推理）/ 结论形态（`_build_field_context` 参数）/ 规则库层级（`RuleQueryService` docstring） | `rule_query_service.py` L172 / L258 / L289 | 规则库层级一律改称「**特异级**」；结论形态保留 `layer` | **E1** ✅ 已修 |
| **N6** | **文档与实现矛盾**：docstring 与注释写「三级特异性匹配」，实现是 L1~L4 **四级** | `rule_query_service.py` L172 / L187 | 改为「四级」 | **E1** ✅ 已修 |
| **N7** | **`'rule'` 字段在 advisory 路径被硬编码为 `'advisory'`**（不是规则标识） | L565 | 改为 `rule_str`（真实串）或 `None` | **E3** ✅ 已修 |
| **N8** | **`extra` 接了从未使用** —— ⚠️ **原判断有误**：它不是「诊断通道」，而是**弹窗文本通道**（`nets.py` L721/L825 收集 `r_extra` 并回传），不能往里塞诊断信息 | L477 / L554 | 诊断信息另起通道：`self._diagnostics`（编排层自建） | **E2** ✅ 已修 |
| **N9** | **`RuleMethodAdapter` import 了从未使用**，名字却像主适配器（实际在用的是 `RuleKeywordAdapter`） | L18 | 删除 import | **E1** ✅ 已修 |
| **N10** | **`self._rule_net` 从未使用**，注释却描述「工厂级网络和兜底层网络」 | L192-194 | 删除属性；注释改写为「无状态」 | **E1** ✅ 已修 |
| **N11** | **注释引用了不存在的文件名** `fuzzy_engine.py`（E22 后真实文件名为 `engine.py`） | `sanity_check.py` L134（该文件已于 E19 删除） | 随 E4 改名一并修正 | **已消解**（E22 改名为 `engine.py`；引用的 `sanity_check.py` 本身已于 E19 删除 ⇒ 现全仓无 `fuzzy_engine` 引用） |
| **N12** | **`load_rules()` 兼容占位**（`pass`），长得像正经 API | L678-681 | **待定**（见 §3.4） | **E4**（待） |
| **N13** | **文档引用路径不完整**：代码里写 `fuzzy-engine-reference.md`，实际在 `_refs/system/ai/` 下 | `fuzzy_algorithm.py` L6/L199、`rule_query_service.py` L6、`adapters.py` L26 | 补全目录前缀（文件存在，非失效链接） | **E4**（待） |
| **N14** | **`ParticularRules` import 了从未使用**（AST 审计：生产侧零引用） | `fuzzy_algorithm.py` L25 | 删除 import | **E1** ✅ 已修 |
| **N15** | **`'level'` 一词两义**：前件里的**档位词**（`'low'`）vs 结论里的**数值**（`2` / `'30%'`）—— `NumTskRule._rule_process` 把结论值存进了 `'level'` key | `nets.py` L505 vs L486 | 结论值改存 `'value'`（内核改动，需同步 `nets.py` 结论层与 `solution_matrix` 构造） | **E4**（待，属内核） |
| **N16** | **料筒温度段号错位**：族映射使 `brl_temp_1 → BT`（无号）、`brl_temp_2..9 → BT2..BT9` ⇒ **BT1 段号空缺**；`BT` 又按 0~50℃ 判档位而实值 230~250℃ ⇒ 169 条规则恒不激活 | `naming.FAMILY_FIELD_ALIAS` / `empirical/hints.py` | 族表删除 + `brl_temp` 并入前缀表（偏移 0）+ hints 的 `"BT"`→`"BT1"` | **E4-b** ✅ 已修 |

### 3.4 待定项（需在对应轮次前拍板）

| # | 待定内容 | 候选 | 建议 | 拍板时机 |
|---|---|---|---|---|
| **P1** | **入口文件名** | `engine.py`（推荐）/ `fuzzy_engine.py` / 不改 | `engine.py` | E4 前 |
| **P2** | `load_rules()` 是否删除 | 删 / 保留 | **保留**（public API，外部可能有未知调用方；改为明确抛 `NotImplementedError` 而非 `pass`） | E4 前 |
| **P3** | `llm/llm_algorithm.py`、`empirical/empirical_algorithm.py` 同类冗余 | 一并改 / 只改 fuzzy | **只改 fuzzy**，另两个记入 §6 遗留 | 已定（本次不动） |
| **P4** | `to_business_name()` 的归属 | 留 `FuzzyEngine` 类方法 / 移到 `naming.py` | 移到 `naming.py`，`FuzzyEngine` 保留**兼容类属性别名**（`parameter_optimize.py` L245/L534 零改动） | ✅ **已拍板并执行**（E4-a，见 §2.8） |
| **P5** | **「料筒温度统一 +/−」这个业务能力怎么表达**（用户第 19 轮提出：早期算法只有 `BT`，不合理） | ① 规则库改成 `BT1..BT9` 分段（规则量 ×9）② 保留族级 `BT` + 引入「整体料筒温度」输入 + 写回按**梯度联动**（旧项目先例：`BT1=NT+5`、`BT2=BT1-10`…）③ 不支持（族级规则退役） | ②（族语义最贴合业务，169 条现有规则不用重写） | **待产品/工艺拍板**（需先定：整体温度口径 = 9 段均值？最低段？梯度链覆盖到第几段？旧项目只到 BT5，业务侧有 9 段） |

### 3.5 两个易被误读的语义（写进代码 docstring）

1. **`confidence` 不是"置信度"**：`confidence = min(Σactivation / max(rule_count, 1), 1.0)`
   ⇒ 实际是**同参数所有命中规则的平均激活度**。命名应体现这一点，或至少在 docstring 写明。
2. **`activation` 与 `activation_sum` 不是同一个量**：
   `activation` 是单条规则的激活度；`activation_sum` 是同参数多条规则激活度之和（参与 `confidence` 计算）。

---

## 4. 轮次计划

| 轮次 | 名称 | 内容 | 行为变化 | 验收方式（轮末跑一次） |
|---|---|---|---|---|
| **E1** | 命名契约 | ① 本文档 §3 ② N5/N6/N9/N10 的零风险修正 ③ 死代码清理（`RuleMethodAdapter` import、`self._rule_net`） | **无** | 黄金快照 diff + `sanity_check` + pytest |
| **E2** | 故障边界 + 去 DB 依赖 | ① 新建 `ports.py`（`RuleRepository` 协议 + `RuleQueryContext`/`ResolvedRule` 搬迁）② `RuleQueryService` 改为从 ports 导入 + 新增 `get_keywords_by_names` ③ `FuzzyEngine(repository=...)` 依赖注入（默认实现延迟导入）④ `recommend()` 拆为「兜底壳 + `_recommend()` 主流程」⑤ 规则查询异常单独捕获（error 级）⑥ `_precheck_numeric_rules()` 条目级预检 + `self._diagnostics` | **正常路径零变化**；异常路径**有意修复**（见 §2.5） | 同上 + 离线验证脚本 7 项 PASS |
| **E3** ✅ | 中间态类型化 + 拆聚合 | ① `RuleAdjustment` / `AggregatedAdjustment` 两个 dataclass ② 抽 `aggregation.py`（`aggregate()` + `to_recommendations()`）③ 落地 N1/N2/N4/N7（**N3 排除**，见 §2.7） | **无** | 同上 + CASE 3 改测真函数 |
| **E4-a** ✅ | 命名契约归位 | ① 抽 `naming.py`（P4：3 张表 + `to_business_name()` + import 时一致性自检）② `FuzzyEngine` 保留兼容别名 + 兼容入口 ⇒ 外部零改动 ③ `fuzzy/__init__.py` 导出 `naming` | **无** | 同上 + 命名契约等价性对拍（三张表逐条含顺序 + 262 个输入行为对拍） |
| **E4-b** ✅ | 段号口径修正 | ① `brl_temp` 并入 `PREFIX_FIELD_ALIAS`（偏移 0，1-based 同构）② `FULL_FIELD_ALIAS` 去重 ③ **删 `FAMILY_FIELD_ALIAS` 整表** ④ `to_business_name()` 删族分支、`BT`（无号）退役 ⑤ 编排层 `_normalize_field_name_by_spec` 删 `family_spec` ⑥ `empirical/hints.py` 7 处 `"BT"`→`"BT1"` | **推荐输出零变化**（`summary` / `only_before` / `only_after` / `changed_delta` 全同）；仅参数名与文案 `BT`→`BT1` + 1e-7 浮点尾数 | 同上 + 黄金快照逐条 diff 归因（735 = 196 + 98 + 441 尾数） |
| **E4-c** | 抽字段上下文 + 瘦身 + 改名 | ① 抽 `field_context.py` ② 入口改名 `engine.py`（P1）③ 删 `load_rules` 或改抛（P2）④ 修 N11 注释 | **无** | 同上 + 全量 import 点复查 |
| **E5** ✅ | 命名契约双向闭合 | ① `naming.py` 补 `to_algo_name()` / `to_algo_params()` + import 时往返自检 ② 编排层删重复的正向实现，改调契约层 ③ `FuzzyEngine` 补正向兼容入口 ④ 5 个 dev 脚本同步 | **无**（真实入参 84 字段逐键 0 差异） | 同上 + 新旧正向实现逐条对拍（独立参照系）+ 往返闭合自检 |
| **E6** ✅ | 同名消歧（改名） | ① `base.Recommendation` → **`AlgorithmRecommendation`**（类定义 + `process/algorithms/__init__.py` 的 `__all__`）② 6 个实现方 import 同步 ③ `parameter_optimize` 取消 `as AlgoRecommendation` 别名 ④ 代码内文字引用更正（`condition.py` ×2 / `sanity_check.py` ×1 / 3 个 dev 脚本 ×4） | **无**（纯标识符重命名，`to_dict()` 的 7 个对外 key 不动） | diff 逐行审计（确认零逻辑变更）+ sanity + pytest + 离线验证 + provided_smoke + 导出面验证 |
| **E7** ✅ | 算法输入契约 | ① 新增 `fuzzy/rule_spec.py`（`FuzzyKeywordSpec` / `FuzzyRuleSpec` + 转换 + 校验，零外部依赖）② 命名消歧：与内核 `fuzzy_core.models.nets.FuzzyRule` 同名不同物 ⇒ 统一加 `Spec` 后缀 | **无**（新文件，无生产调用方，现有链路一行未改） | 同上 + 契约层零依赖导入检查（`process.models` 未进 `sys.modules`）+ 模块自检 |
| **E7-e** ✅ | 来源层归位（建 `sources/`） | ① `ports.py` → `sources/__init__.py`（端口协议归位到「读取算法依赖」层，零依赖）② `adapters.py` 拆成 `sources/db.py`（`RuleKeywordAdapter` + `RuleQueryService`，DB 专属）+ `sources/text.py`（`RuleMethodAdapter`，**来源无关**）③ `services/` 目录消失、`rules/` → `sources/files/` ④ `fuzzy/__init__.py` docstring 分层清单同步 ⑤ 顺带修 `verify_fuzzy_nested_context.py` 的 patch 目标（改前是坏的） | **无**（纯搬移，只改 import 路径 + docstring 措辞） | 同上 + 残留扫描 0 + 零依赖保持（`sources` / `sources.text` 导入后 ORM 未加载）+ 端到端真实 DB 复验 |
| **E8** ✅ | `sys.path` 治理 | ① `sanity_check.py` 删「把 `fuzzy/` 与 `process/algorithms/` 加进 `sys.path`」两行 + 13 处顶层裸导入改绝对 ② 内核测试 `sys.path.insert` 目标从 `fuzzy/` 改为 `backend/` + 6 处改绝对 ③ 4 个 dev 脚本同步（8 处）④ 每处补「不要把包目录加进 sys.path」的警示注释 ⑤ 顺带修 `test_nets.py` docstring 的错误运行路径 | **无**（只改导入方式 + 搜索路径，不触碰算法语义） | 同上 + **顶层名泄漏检查（新增）** + BOM 完整性 + dev 脚本 HEAD 字节级副本行为对照 |

**每轮的通用验收（不新写脚本，只跑现成）**：

```
# 1) 黄金快照（现成脚本，需先加一个只读比对模式）
..\.venv\Scripts\python.exe _dev_refs\diag_fuzzy_bucket_before_after.py --json _dev_refs\_golden_after.json
#    ⇒ 与 _golden_before.json 逐条 diff，after 段必须完全为空

# 2) 现成 pytest
..\.venv\Scripts\python.exe -m pytest process\algorithms\fuzzy\fuzzy_core\tests -q
..\.venv\Scripts\python.exe -m pytest tests -q
```

---

## 5. 每轮验收记录

| 轮次 | 日期 | 黄金快照 diff | sanity | pytest | 验收结论 |
|---|---|---|---|---|---|
| E1 | 2026-10-23 | **49 样本 diffs = 0**（vs `_before_after_db.json` 基线，逐条比 `after_count` / `after_params` / `after_head`） | ✅ 全绿（B1~B7 + C1~C3） | ✅ 17 + 5 passed | **通过** —— 行为零变化，命名契约已落地；存档 `_dev_refs/_golden_E1.json` |
| E2 | 2026-10-23 | **49 样本 diffs = 0**（vs `_golden_E1.json`） | ✅ 全绿 | ✅ 17 + 5 passed | **通过** —— 正常路径行为零变化；离线验证 7 项 PASS（V1 注入 FakeRepo 离线跑通 / V2 脏规则未拖垮整层 + 对照组证明必要性 / V3 DB 异常降级不冒泡） |
| E3 | 2026-10-23 | **49 样本 diffs = 0**（vs `_golden_E2.json`） | ✅ 全绿（CASE 3 已改为**测真函数**，并补上文本建议用例） | ✅ 17 + 5 passed | **通过** —— 正常路径行为零变化；`fuzzy_algorithm.py` 776 → 697 行；离线验证 7 项 PASS 仍绿；存档 `_dev_refs/_golden_E3.json` |
| E4-a | 2026-10-23 | **49 样本 diffs = 0**（vs `_golden_E3.json`；**全 JSON 逐条相等** —— 比前几轮的 3 字段口径更强） | ✅ 全绿 | ✅ 17 + 5 passed | **通过** —— 行为零变化；命名契约等价性对拍 ALL PASS（三张表逐条含顺序 + `to_business_name` 262 输入对拍全一致）；离线验证 7 项 PASS 仍绿；`fuzzy_algorithm.py` 697 → 582 行；存档 `_dev_refs/_golden_E4.json` |
| E4-b | 2026-10-23 | **49 样本：推荐集合/条数/顺序/变化量全同**（`summary` 与 `only_before`/`only_after`/`changed_delta` 新旧一致）；逐条 diff 735 = 196 参数名 + 98 文案 + **441 处 1e-7 浮点尾数**（同代码重跑 diff=0 ⇒ 快照确定性已验证；尾数差来自候选规则链变化，激活度均为 0，语义无影响） | ✅ 全绿 | ✅ 17 + 5 passed | **通过** —— 推荐输出零变化；段号对齐后 `BT1` 拿到值（内核实测可命中），169 条 BT 规则由「恒不激活」变为「无输入退役」；离线验证 7 项 PASS 仍绿；存档 `_dev_refs/_golden_E4b.json` |
| **E5** | 2026-10-23 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E4b.json`；脚本走**真实编排层** `_compose_algorithm_context` ⇒ 覆盖 service 层改动） | ✅ 全绿 | ✅ 17 + 5 passed | **通过** —— 行为零变化；正向映射归位到契约层（`naming.to_algo_name` / `to_algo_params`），编排层重复实现删除；新旧正向实现逐条对拍：真实入参 84 字段 **0 差异**（唯一差异 = 11 个裸前缀，旧会翻成已退役的 `BT`，新不再复活该路径）；往返闭合 70 字段 **0 不闭合**；离线验证 7 项 PASS 仍绿 |
| **E6** | 2026-10-23 | 不适用（纯改名，未重跑快照生成） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；11 个纯本轮文件 **diff 逐行审计：全部为 `Recommendation`→`AlgorithmRecommendation` 标识符替换，零逻辑行变更**；离线验证 7 项 PASS 仍绿；`verify_provided_smoke` **6/6 PASS**（覆盖编排层 + 改过的 import）；导出面验证：`process.algorithms.AlgorithmRecommendation` 可用、旧名不再导出 |
| **E7** | 2026-10-23 | 不适用（新增未接线文件，未触及任何现有链路） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（现有链路一行未改）；契约层**零外部依赖**：`import ...fuzzy.rule_spec` 后 `process.models` 与 `rule_query_service` 均**未进** `sys.modules`，可脱离 Django 独立 `python rule_spec.py` 运行；模块自检：转换正确（两数组等长同序）+ 非法规格一次拦全 4 项；离线验证 7 项 PASS 仍绿；provided_smoke **6/6 PASS** |
| **E7-b1** | 2026-10-23 | 不适用（加能力，未切换任何现有调用点） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；① `FuzzyRuleSpec` 扩为 5 字段（新增 `conclusion_kind` / `specificity`，完整覆盖 `ResolvedRule` 的 4 个有值字段）+ 校验扩充（`conclusion_kind` ∈ {numeric,advisory}、`specificity` ∈ 1~4）② `adapters` 新增 `to_keyword_specs()`（数据来源的解析出口，字段名天然对齐 `to_fuzzy_dict` 输出）；契约层自检：非法规则规格一次拦全 3 项；`adapters` 自检：dict → `FuzzyKeywordSpec` 正确；零依赖导入检查：`rule_spec` 导入后 `process.models` 未进 `sys.modules`（`adapters` 仍需 settings，与改前一致） |
| **E7-b2** | 2026-10-26 | 不适用（纯字段改名 + 去来源耦合，不改算法语义） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；`ResolvedRule` **退役**（全仓 0 处残留），生产链路改产/消费 `FuzzyRuleSpec`（`rule_str`→`rule_description`、`method`(ORM)→`source_ref` 字符串）；转换逻辑收敛到契约层（`to_rule_array`/`get_priority_array` 改为端口转发）；12 个文件同步（含 pytest 套件内的 `test_fuzzy_field_report.py` 与 5 个 dev 诊断脚本）；**E2 零依赖成果保持**（`fuzzy_algorithm` 导入后 ORM 与 `rule_query_service` 均未加载）；**端到端真实 DB 验证**：命中 10 条、类型 `FuzzyRuleSpec`、`source_ref='RuleMethod:20'`、**无 ORM 属性泄漏**；残留扫描 0 + AST 未使用 import 0 |
| **E7-c** | 2026-10-26 | 不适用（纯文件改名 + 措辞统一，无逻辑变更） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；`rule_spec.py` → **`algorithm_inputs.py`**（用户第 28 轮质疑后改名，诊断见 §2.13.6：名不副实只覆盖一半 + 与同包 `specs.py`「调优入参契约」语义撞车 + 漏掉「标准化格式」核心语义）；类名 `FuzzyKeywordSpec` / `FuzzyRuleSpec` 不变；改动 = 1 次重命名 + 5 个 import 路径 + 6 处文字；模块路径引用 0 处 + 残留 `rule_spec` 仅剩函数名/错误定位串；pytest 22 passed + sanity 全绿 + 契约层自检 + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + 零依赖保持 |
| **E7-d** | 2026-10-26 | 不适用（纯文件改名 + 措辞统一，无逻辑变更） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；按 6 层分层改名（详见 §2.13.7）：层 0 `specs.py` → **`input_specs.py`**（对外接口格式）、层 3 `algorithm_inputs.py` → **`elements.py`**（算法内部数据对象）；类名 `FuzzyKeywordSpec` / `FuzzyRuleSpec` 不变；改动 = 2 次重命名 + 外部 import 5 处 + 包内 import 6 处 + docstring 措辞统一 + `__init__.py` 分层清单；**字节级校验**：`input_specs.py` 与改前 `specs.py` 字节一致（规范化行尾后仅 2 处差异，均为前几轮已做的说明更新）；公共 API 表面 10 个对外符号零变化；残留 `algorithm_inputs` / `fuzzy.specs` 各 **0 处**；pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + 零依赖保持 + 端到端真实 DB 复验 |
| **E7-e** | 2026-10-26 | 不适用（纯搬移，只改 import 路径 + docstring 措辞） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；按用户第 33 轮的**业务 5 层**模型重组文件结构（详见 §2.13.9）：建 `sources/` 目录收拢第 ③ 层「读取算法依赖」—— `ports.py`→`sources/__init__.py`（零依赖）、`adapters.py` 拆为 `sources/db.py`（DB 专属）+ `sources/text.py`（来源无关）、`services/rule_query_service.py`→`sources/db.py`、`rules/`→`sources/files/`；**消亡 5 个路径**；**纠正 §2.13.8.3 的误判**（`RuleMethodAdapter` 不是死代码，是为文件来源预留的格式翻译器）；顺带修好 `verify_fuzzy_nested_context.py`（**改前就是坏的**，patch 目标指向了不存在的模块属性）；残留扫描各 **0 处**；零依赖保持（`sources`/`sources.text` 导入后 `process.models` 未进 `sys.modules`）+ AST 新文件未使用 import 0 + pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + `sources/text.py` 自检 + 端到端真实 DB 复验（命中 10 条 / `RuleMethod:20`） |
| **E8** | 2026-10-26 | 不适用（只改导入方式 + 搜索路径，不改业务逻辑） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；**`sys.path` 治理**（详见 §2.14）：把「包目录」（`fuzzy/` 与 `process/algorithms/`）从搜索路径里拿掉（7 个文件 / 27 处顶层裸导入改绝对导入）；**顶层名泄漏清零**（`sources` / `elements` 改前已泄漏为顶层名，改后 `fuzzy`/`fuzzy_core`/`sources`/`elements`/`input_specs`/`aggregation`/`naming` 全部未进 `sys.modules`）；零依赖保持（`django`/`process.models`/`sources.db` 均未加载）；AST 未使用 import 与 HEAD **集合完全一致**（3 个既有遗留）；BOM 保持；pytest 22 passed + **内核测试两种跑法**（pytest 22 + 独立 `python -m tests.test_nets` 11/11 + `test_macros` 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + 端到端真实 DB 复验（命中 10 条） |
| **E9** | 2026-10-26 | 不适用（纯搬移 + 改名 + import 路径，不改业务逻辑） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；**内核输入契约归位**（详见 §2.16）：`fuzzy/elements.py` 消亡 → `fuzzy_core/profiles.py`（`KeywordProfile` / `RuleProfile`）；`nets.py` 拆出 `models/features.py`（`FuzzyFeature`）与 `models/rules.py`（`FuzzyRule` / `NumTskRule` / `ParticularRules`），net 只留 3 个；分层清单 6 层并为 5 层；**零依赖保持**（`django` / `process.models` / `sources.db` 均未进 `sys.modules`）；pytest 22 passed + **内核测试两种跑法**（pytest 17 + 独立 `python -m tests.test_nets` 11/11 + `test_macros` 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL（exit=0）+ provided_smoke PASSED + 端到端真实 DB 复验（命中 10 条 / 类型 `RuleProfile` / `source_ref='RuleMethod:20'` / 无 ORM 泄漏 / 契约校验通过）+ 残留扫描 0 + `profiles.py` 独立自检 |
| **E10** | 2026-10-26 | 不适用（纯搬移 + import 改写 + docstring 措辞，不改业务逻辑） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化；**端口归位**（详见 §2.17）：`RuleRepository` + `RuleQueryContext` 从 `sources/__init__.py` 移到包根 **`fuzzy/ports.py`**（依赖倒置：端口属消费方）；`sources/` 退回纯来源实现目录（`db` / `text` / `files`），名字恢复名副其实；改动 = 新建 `ports.py` + `sources/__init__.py` 瘦身（110 → 13 行，纯 docstring）+ 4 处 import 改写（`fuzzy_algorithm` / `sources.db` / `tests/verify_fuzzy_nested_context` / `_dev_refs/_verify_e2e_db`）+ `fuzzy/__init__.py` 分层清单 + `profiles.py` docstring 反向引用修正；**零依赖保持**（import `ports` / `sources` / `fuzzy_algorithm` 后 `django`/`process.models`/`sources.db` 均未进 `sys.modules`）；残留扫描 0 + AST 未使用 import 0 + pytest 22 passed + **内核测试两种跑法**（pytest 17 + `python -m tests.test_nets` 11/11 + `test_macros` 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL（exit=0）+ provided_smoke PASSED + 端到端真实 DB 复验（命中 10 条 / 无 ORM 泄漏 / 契约校验通过，exit=0） |
| **E11** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E5.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（纯搬移 + import 改写 + docstring 措辞）；**收尾了一轮断在半成品状态的改造**（详见 §2.18）：`library/` 拆分修好（`keywords.py` 105 行仅适配器 / `rules.py` 278 行仅服务）+ 补 `library/files/__init__.py` + 接线 12 处 import + 删 `sources/` + 改 6 处 docstring；**类体逐字未改**（搬迁前 diff 仅 8 ins / 9 del，全在 docstring + import 行）⇒ **零个方法体改动**；**内核测试两种跑法**（pytest 17 + `python -m tests.test_nets` 11/11 + `test_macros` 6/6）+ sanity 全绿 + **离线验证 8 PASS/0 FAIL**（exit=0）+ provided_smoke 6/6 PASSED + `verify_fuzzy_nested_context` PASSED（改过 patch 目标）+ **真实 DB 端到端**（命中 10 条 / `source_ref='RuleMethod:20'` / ORM 泄漏 0 / 契约校验通过 / exit=0）+ **零依赖保持**（import `ports` / `library` / `fuzzy_algorithm` 后 `django` / `process.models` / `library.rules` / `library.keywords` 均未进 `sys.modules`，顶层名泄漏 NONE）+ 残留扫描 **0** + AST 未使用 import **0** + BOM 保持 |
| **E12** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E11.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（纯搬移 + 门面转发 + docstring 措辞）；**来源层类职责对称化**（详见 §2.19）：新增 `KeywordQueryService` 承担查库、`RuleKeywordAdapter` 退化为纯转换器（**治的是 E7 同一个病「取数与业务逻辑焊死」在关键字侧的对应症状**），`RuleQueryService.get_keywords_by_names` 改门面转发（`KeywordProfile` → `to_net_dict()`）⇒ **端口与编排层零改动**；两侧出口统一为内核契约（`List[RuleProfile]` / `List[KeywordProfile]`）；**关键字路径新旧对拍 PASS**（真实 DB，逐元素/逐键/含键序/含类型全等 + 契约校验通过 + ORM 泄漏 0 + 边界正确）；**零依赖保持**（`django`/`process.models`/`library.rules`/`library.keywords` 均未进 `sys.modules`，顶层名泄漏 NONE）；pytest 22 passed + **内核测试两种跑法**（11/11 + 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0 + 命名契约对拍 PASS + **AST 全包扫描**：清掉 E5 遗留的 `naming.py` 2 个，`fuzzy` 包剩 3 个 **HEAD 既有遗留**（登记 L18） |
| **E13** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E12.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（**类拆分 + 改名 + docstring 措辞**）；**来源层文件级对齐**（详见 §2.20）：`library/rules.py` 按「**查询是查询，管理是管理**」拆成 `RuleQueryService`（查询侧，2 个方法，只碰 ORM）+ `RuleRoutingService`（管理侧 + `RuleRepository` 端口门面，9 个方法，**不碰 ORM**），与 `library/keywords.py` 的 `KeywordQueryService` / `RuleKeywordAdapter` 形成 **2v2 对称**；**引用面**：生产 1 处 + 测试 3 处 + dev 脚本 11 个文件；**零外部调用方的 6 个方法**（`get_libraries` / `_product_to_library_codes` / `_match_defect_level` / `classify_conclusion_kind` / `select_libraries` / `get_methods`）⇒ 拆类风险面极小；**三处行为等价地雷已避开**（逐个查库保序 / ORM 实例传递 / `base` 兜底单查带 `library_type='fuzzy'`）；**新增只读 AST 护栏** `_chk_library_layout.py`（管理侧不得出现 `.objects` + 查询侧必须出现 `.objects` + 交叉污染 + 旧目录消亡）并**删除写盘型地雷脚本** `_tmp_split.py`；pytest 22 passed + **内核测试两种跑法**（11/11 + 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED（3 处 patch 目标已改）+ 真实 DB 端到端 exit=0（numeric 10 / advisory 0 / 契约校验通过）+ **关键字路径新旧对拍 PASS**（ORM 泄漏 0）+ **零依赖保持**（`django`/`process.models`/`library.rules`/`library.keywords` 全未进 `sys.modules`，顶层名泄漏 NONE）+ **library/ 布局自检 PASS** + AST 全包扫描 13 个（**全为 HEAD 既有**，`library/` 下 **0** 个，登记 L18） |
| **E14** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E12.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（**逻辑抽离 + 可见性放宽 + docstring 措辞**）；**来源轴补刀**（详见 §2.21）：新建 `library/policy.py`（`RulePolicy`，**零 ORM**）接管 6 个纯判断方法（`product_to_library_codes` / `match_defect_level` / `classify_conclusion_kind` / `split_by_conclusion_kind` / `to_rule_array` / `get_priority_array`）⇒ `RuleRoutingService` 由 9 方法瘦身为 **6 方法**（3 个保留门面转发以满足 `RuleRepository` 端口协议）；**判据**：**碰 ORM 的 = 来源特有，不碰 ORM 的 = 来源无关**；**护栏升级**：`_chk_library_layout.py` 新增第三个 role `source_neutral` + `_imports_orm()`（**连 ORM import 都不许有**，比「不出现 `.objects`」更强）；**零依赖加强**：`_verify_zero_dep.py` 的 `_BANNED` 增 `library.policy`（编排层只跟端口打交道，不直接依赖任何实现）；pytest 22 passed + **内核测试两种跑法**（11/11 + 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0（numeric 10 / advisory 0 / 契约校验通过）+ **关键字路径新旧对拍 PASS**（ORM 泄漏 0）+ **零依赖保持**（`django`/`process.models`/`library.rules`/`library.keywords`/`library.policy` 全未进 `sys.modules`，顶层名泄漏 NONE）+ **library/ 布局自检 PASS**（含 `policy.py` 新断言）+ AST 全包扫描 **13** 个（扫 42 文件，比 E13 多 1 个 = 新增 `policy.py` ⇒ **`policy.py` 贡献 0**）；**如实边界**：`RuleSource` 协议抽象与 `library/` 来源轴目录重排**本轮仍未做**（用户选择「只补一刀」），L14/L15/L16 未动，L17 仍未关闭 |
| **E15** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E14.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（**纯路径 + 协议变更**）；**端口搬入 `library/` + 改名瘦身**（详见 §2.22）：`fuzzy/ports.py` **消亡** → `library/ports.py`（`RuleRepository` → **`AlgorithmResourceRepository`**，并由 5 方法瘦身为 **2 个取资源方法**）；**3 个加工方法上提内核**（`split_by_conclusion_kind` → `fuzzy_core/profiles.py`，`to_rule_array` / `to_priority_array` 同步）；`library/policy.py` 由 179 → 149 行、`library/rules.py` 由 281 → 259 行；**零依赖保持**（`django`/`process.models`/`library.rules`/`library.keywords`/`library.policy` 全未进 `sys.modules`，顶层名泄漏 NONE）；pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0 + 关键字路径新旧对拍 PASS + **library/ 布局自检 PASS** + AST 全包扫描 13 个（**全为 HEAD 既有**，`library/` 下 0 个） |
| **E16** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E15.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（**纯重组 + 改名**）；**`library/` 内部重组**（详见 §2.23）：**新建 `library/repository.py`**（`ResourceRepository`，3 方法：选库 / 收集组装 / 组合 keyword，181 行）、**`library/policy.py` 消亡**（149 行，语义并入 `library/rules.py::RuleService`）、`library/rules.py` 由 259 → **218 行**、`library/__init__.py` **重写**（现 37 行，五文件结构表）；**护栏重写** `_chk_library_layout.py`（新增 `contract` / `resource_set` role + `_imports_sibling_impl()` + `policy.py` 消亡断言）、`_verify_zero_dep.py` 的 `_BANNED` 改禁 `library.repository`、`_chk_enc.py` 主线改为扫**已废弃类名**残留、`_rename_to_routing.py` 硬禁用；**顺手修好 3 个 dev 脚本/测试**（`verify_fuzzy_nested_context.py` 3 处 patch 目标、`diag_fuzzy_level_word_crash.py` patch 目标 + classmethod 还原、`diag_fuzzy_field_registry_regression.py` 的 `registry` NameError ⇒ **L16 关闭**）；pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0（numeric 10 / advisory 0 / 契约校验通过）+ 关键字路径新旧对拍 PASS（ORM 泄漏 0）+ **零依赖保持** + **library/ 布局自检 PASS** + AST 全包扫描 13 个（**全为 HEAD 既有**，`library/` 下 0 个）+ U+FFFD 扫描 92 文件 **0** + 4 个 diag 脚本全部 exit=0 |
| **E17** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E16.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（**纯文件改名 + 术语统一**）；**契约层文件改名**（详见 §2.24）：`library/ports.py` → **`library/contracts.py`**（与仓库既有「契约」词汇统一；`port` 是 DDD 六边形术语，本仓库**独苗**）；13 处 import 路径改写 + 2 个护栏脚本 + 3 处结构表 + 16 处 docstring 措辞；`_chk_enc.py` 旧名扫描清单**新增 `library.ports`**；pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0（numeric 10 / advisory 0 / 契约校验通过）+ 关键字路径新旧对拍 PASS（ORM 泄漏 0）+ **零依赖保持** + **library/ 布局自检 PASS**（`contracts.py` 已在位）+ AST 全包扫描 13 个（**全为 HEAD 既有**，`library/` 下 0 个）+ 6 个 diag 脚本全部 exit=0 + 残留扫描：`ports` / `端口` 仅剩**历史记录**（执行文档历史章节 + 已硬禁用的 `_rename_to_routing.py`） |
| **E18** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E17.json`，脚本走真实编排层） | ✅ 全绿 | ✅ 22 passed（17 + 5） | **通过** —— 行为零变化（**纯注释**）；`library/` 7 文件 **945 → 727 行（净减 218）**；**代码零改动的硬校验**：剥离全部 docstring 后 `ast.dump` 逐文件比对 ⇒ **7 个全 IDENTICAL**；判定标准：删分层术语 / 轮次考古 / 决策辩论 / 重复对照表，留真契约与「看代码猜不出来的坑」；复查补刀 5 处（分隔条风格统一 + 3 处措辞）；零依赖保持 + library/ 布局自检 PASS + 编码扫描 exit=0 + U+FFFD 0 |
| **E19** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E18.json`） | ✅ 全绿（**删除前最后一跑**） | ✅ **41 passed**（22 + 13 + 6） | **通过** —— 行为零变化（**只动测试与文档，零生产代码改动**）；**`sanity_check.py` 迁入 pytest 后删除**（603 行 → 2 个新文件 19 个用例）：CASE 1/2/4 + B1~B7 + C1~C3 → `fuzzy_core/tests/test_inference_gates.py`（13）、CASE 3 → `tests/test_fuzzy_aggregation.py`（6，零 Django）；**顺带修掉 `return bool` 假通过**（pytest 警告 **17 → 0**；Mamdani 的 `[SKIP]` 假通过改为直接抛；priority 断言**补反转验证**堵空转）⇒ 端到端探针证明 pytest 会因断言失败变红；代码级 `sanity_check` 引用 **0**；真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 零依赖保持 + library/ 布局自检 PASS + AST 全包扫描 13 个（**全为 HEAD 既有**，`library/` 下 0 个）+ U+FFFD 0 + diag 脚本 **31/31 正常 exit=0**（**5 个在 GBK 控制台 `UnicodeEncodeError` 属既有环境问题，UTF-8 下全绿**）|
| **E20** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E19.json`） | 不适用（sanity 已于 E19 并入 pytest） | ✅ **41 passed**（30 + 11） | **通过** —— 行为零变化（**只搬职责，不改逻辑**）；**契约归属对齐**（详见 §2.27）：`keywords.py` 去掉 `to_fuzzy_dict` 裸 dict 中转层（三个旧出口消亡、直接构造 `KeywordProfile` + 补 `meta_source` 透传）、`rules.py` **新增 `RuleAdapter`**（与 `RuleKeywordAdapter` 成对）、`repository.py` 编排层不再越位构造契约；**⭐ 行为等价直接证明**：从备份加载改前模块与改后逐字段对拍 **12 案例 0 差异**（唯一有意差异 = `meta_source` 透传）；**连带修好 2 个 dev 脚本**（`_verify_kw_parity.py` 旧基线冻结进脚本后 PASS / `diag_fuzzy_fix_simulation.py` **E16 遗留 L15 一并关闭**，exit=1 → exit=0）；真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE）+ library/ 布局自检 PASS + compileall exit=0 + diag 脚本 **32/34 exit=0**（余 2 个为「诊断发现问题」的既有行为） |
| **E21** | 2026-10-26 | **49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E20.json`） | 不适用（sanity 已于 E19 并入 pytest） | ✅ **41 passed**（30 + 11） | **通过** —— 行为零变化（**纯文件改名 + import 路径同步**）；**跨包命名对齐**（详见 §2.28）：`fuzzy/input_specs.py` → **`fuzzy/specs.py`**（与 `expert/specs.py` 同层同名）；8 处 import/注释 + 2 处 dev 脚本同步；**⭐ 改名理由**：① `expert/specs.py` 与 `fuzzy/input_specs.py` 是**同层同物**（docstring 首句几乎一字不差、同一套 `field_contract` 机制）却两个名字 ② E7-d 给 `input` 限定词的消歧前提（包内有两类 spec）**已随层 3 改名 `elements.py` 而消失** ③ `input` 在本包内与内核 `profiles.py`「内核输入契约」撞义；**导出符号零变化**（`__all__` 10 个不动）⇒ 外部调用方零影响；验收：黄金快照 diff=0 + pytest 41 passed + 真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE，含新增 `specs` 检查项）+ library/ 布局自检 PASS + compileall exit=0 + 残留扫描：代码级 0 处 |

| **E22** | 2026-10-26 | **改前/改后同脚本对跑，整棵 JSON 逐条 diff = 0**（`diag_fuzzy_bucket_before_after.py --json`，改前用备份还原的完整 backend 副本） | 不适用（sanity 已于 E19 并入 pytest） | ✅ **41 passed**（30 + 11） | **通过** —— 行为零变化（**纯文件改名 + 引用同步**）；**双文件改名**（详见 §2.29）：`fuzzy/naming.py` → **`fuzzy/field_names.py`**（用户建议 `fields.py`，因与同包 `specs.py`「字段字典」撞名而加 `names` 限定）、`fuzzy/fuzzy_algorithm.py` → **`fuzzy/engine.py`**（§0 早已拍板，E22 落地；类名 `FuzzyEngine` 不动）+ dev 脚本 `_verify_naming_forward_parity.py` → `_verify_field_names_forward_parity.py`；3 个重命名 + `naming` **72 处** + `fuzzy_algorithm` **44 处**引用同步（30 个文件，**BOM / 行尾 / 编码零变化**）；**⭐ 最强等价证明**：用备份还原「改前」完整副本，**同一生成器脚本**分别跑 ⇒ 逐条 diff = **0**（且与 `_golden_E21.json` 的 details 逐条相等）；**预先存在的 77 个 expert 测试失败已用基线对照实验证明与本轮无关**（改前同样 77 failed，栈全在 `expert/data_validator.py`）；pytest 41 passed（`tests` + `process/algorithms/fuzzy`）+ 真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 字段名对拍主口径 84 字段逐键差异 0（副口径 36 处差异**全在边界输入段**、真实入参与往返闭合均 0 差异，详见 §2.29） + 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE，含新增 `field_names` / `engine` 检查项）+ library/ 布局自检 PASS + compileall exit=0 + 残留扫描（代码级 0 处） |

| **E23** | 2026-10-26 | **改前/改后同脚本对跑，整棵 JSON 逐条 diff = 0**（`diag_fuzzy_bucket_before_after.py --json`，改前用备份还原的完整 backend 副本） | 不适用（sanity 已于 E19 并入 pytest） | ✅ **41 passed**（30 + 11） | **通过** —— 行为零变化（**纯文件改名 + 引用同步**）；**推荐结果层改名**（详见 §2.30）：`fuzzy/aggregation.py` → **`fuzzy/recommendations.py`**（用户指出「这层是推理完成后格式化输出结果」；候选 `output.py` / `formatter.py` / `presenter.py` 均未覆盖「归并」半边，`advice.py` 与模块内 `advice` 子概念撞名）；+ 测试文件 `tests/test_fuzzy_aggregation.py` → `tests/test_fuzzy_recommendations.py`；2 个重命名 + `aggregation` **9 处**引用同步（5 个文件，**BOM / 行尾 / 编码零变化**）+ 3 处手工润色；**公开符号零变化**（`aggregate()` / `to_recommendations()` / `RuleAdjustment` / `AggregatedAdjustment` 一个不动）；**⭐ 双重等价证明**：① 基线对照实验（改前副本 + 同脚本对跑）逐条 diff = **0**（两份均 221409 字节，且与 `_golden_E22.json` 的 details 逐条相等）；② **逐行 diff**（改后 vs 改前备份）⇒ `recommendations.py` **仅 docstring 首句 1 行不同**（224 → 224 行），全部 6 个受影响文件共 22 行差异且逐条可解释为改名/措辞 ⇒ **零逻辑改动**；pytest 41 passed + 真实 DB 端到端 exit=0（numeric 10 / advisory 0，契约层校验通过）+ 字段名对拍主口径 84 字段逐键差异 0 + 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE，含新增 `recommendations` 检查项）+ library/ 布局自检 PASS + compileall exit=0 + 残留扫描（代码级 0 处） |

| **E24** | 2026-10-26 | **同脚本对拍，整棵 JSON 逐条 diff = 0**（`_dev_refs/_snapshot_core.py`；改前用备份还原的完整 backend 副本；覆盖面：gauss 面 2016 项 / params 96 项 / tri 面 63 项 / defuzz 面 12 项 / 推理 15 场景 / 激活度 45 组） | 不适用（sanity 已于 E19 并入 pytest） | ✅ **43 passed**（32 + 11） | **通过** —— 行为零变化（**唯一有意行为差异 = 「tri 可用 → 明确拒绝」2 项**）；**内核论域实例与隶属度类型层清理**（详见 §2.31）：① `functional.py` 删 L246-356 迁移粘贴重复段（356 → 245 行；`triangular_mf` / `trapezoidal_mf` 的 scalar / list 调用从 `TypeError` 修复为正常值，ndarray 路径完全不变）② `features.py` 删 4 个只写不读属性 + 死方法 `get_all_value()` + 从未被读取的 `f_name` / `f_type` 两个**参数**（91 → 90 行；`nets.py` 3 处构造同步）③ 删 `tri` 死分支 + `macros.MEMBERSHIP_TYPES` 收紧为元组 `('gauss',)` 并由 `features.py` 消费（声明与实现同源；`features.py` 90 → 82 行）④ 桶中心抽 `macros.bucket_centers()` 纯函数 + 补 3/5/7/9 档直接断言（`macros.py` 236 → 275 行；`features.py` 82 → 78 行；pytest 30 → **32**）；真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 字段名对拍主口径 84 字段逐键差异 0 + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE）+ library/ 布局自检 PASS + compileall exit=0 |

| **E25** | 2026-10-26 | **五档对拍，逐点零差异**（`_dev_refs/_e25_diffcheck.py`，内嵌改前 `functional.py` 原文为基线；① 严格档 21 组 ② 参数化重述档 17 组 ③ 有意行为变化档 5 项 ④ 手算参照系 12 个解析性质 + 9 形状值域 + 统一签名契约 ⑤ FuzzyFeature 端到端 4 种论域 × 2 档 × 51 点逐点对拍） | 不适用（sanity 已于 E19 并入 pytest） | ✅ **43 passed**（32 + 11） | **通过** —— 行为零变化（**唯一有意行为差异 = 5 项「老实现有缺陷 → 新实现正确」**）；**隶属度函数层重组**（详见 §2.32）：① `functional.py` → **`memberships.py`** + **`defuzz.py`**（解模糊移出）② **统一签名 `mf(x, center, width, shape=None)`** + **9 形状族**（高斯/双高斯/三角/梯形/广义钟形/代数钟形/S 型/Z 型/单点）+ **正名**（`bell_mf` → `algebraic_bell_mf`，exp 型另起 `bell_mf`）③ `MEMBERSHIP_TYPES` 改由 `MEMBERSHIP_SPECS` **派生**（声明与实现同源）+ `DEFAULT_MEMBERSHIP_TYPE` 替掉 `nets.py` 3 处硬编码 ④ `features.py` 改分派 + `membership_shape` 取自分派表（形状参数单一真源）+ 退化/倒挂论域 warning；**⭐ 数值零变化证明**：高斯 **p=2 逐位相等**（atol=0）+ `FuzzyFeature` 端到端 4 种论域（正序/负区间/**倒挂**/**退化**）逐点差异 0；**修掉 3 个真 bug**：老 `bell_mf` 缺 `|·|` 算出 **>1** 的隶属度 / 老 `singleton_mf` 对 list 输入结果全 0 / `assert` 当校验（`python -O` 下失效）⇒ 改 `ValueError`；pytest 43 passed（32 + 11）+ 对拍零差异 + 零依赖保持 + library/ 布局自检 PASS + compileall exit=0 |



---

## 6. 遗留问题台账

| # | 问题 | 来源 | 状态 |
|---|---|---|---|
| L1 | 聚合公式语义（`confidence` = 平均激活度）是否合理 | E1 讨论 | 待评估（属算法语义，本轮不动） |
| L2 | 激活度阈值 `MIN_ACTIVATION_THRESHOLD` 需按规则数标定 | 上一轮 D+B 遗留 | 待定（需业务标定） |
| L3 | 规则库重复项（同名规则多条命中）需去重口径 | 上一轮遗留 | 待定 |
| L4 | `llm/llm_algorithm.py` / `empirical/empirical_algorithm.py` 目录名冗余 | P3 | 待定（**E22 后情况变化**：fuzzy 已改 `engine.py`，二者与 fuzzy 风格分叉；用户本轮只授权改 fuzzy ⇒ 是否全仓统一待定，另见 L23） |
| L5 | `functional.py` **5 组同名实现前后段覆盖**（`gaussian_mf` / `triangular_mf` / `trapezoidal_mf` / `bell_mf` / `singleton_mf`），其中 `triangular_mf` 两版**语义不同**（后版无 `a<=b<=c` 断言）；且无 `__all__` ⇒ `from .functional import *` 会污染命名空间 | AST 审计 / §2.16 / §2.31 | **部分关闭**（E24-1 删掉 L246-356 重复段 ⇒ 前半「同名覆盖」已消亡，5 个别名从「被覆盖」变「唯一定义」；**E25 拆成 `memberships.py` + `defuzz.py` 且各自带 `__all__`** ⇒ 后半「无 `__all__`」也消亡；`fuzzy_core/__init__.py` 改为 `from .defuzz import centroid`（不再 `import *`）⇒ `np` / `Union` / `ArrayLike` 不再泄漏进 `fuzzy_core` 顶层） |
| L6 | `nets.py` L692/L717 矩阵越界只记日志 | §2.2 | 待定（属内核清理） |
| L7 | 文档引用路径不完整（`fuzzy-engine-reference.md` 未写目录） | N13 | 待定（E4 随改名一并修） |
| L8 | ~~`import process.algorithms.fuzzy.fuzzy_algorithm` 仍需 Django setup（父包 `process/algorithms/__init__.py` 会 import 全部引擎触发注册）⇒ 目前是「调用可离线」而非「导入可离线」~~ | §2.6 | ✅ **已关闭**（E3 实测：E2 去 ORM 依赖后，导入与调用均可离线） |
| L9 | 等级两种叫法（`lvl` / `f_level`）未统一为 `level_count` | N3 / §2.7 / §2.16 | 待定（输入契约已定为 `KeywordProfile.lvl`，改名要连带改内核取值处；归属下一轮契约接线） |
| L10 | **169 条族级 `BT` 规则失去输入** —— `BT` 退役后前件拿不到值 ⇒ 规则库「统一调温」能力目前空缺（`BT1`~`BT9` 分段规则仅 3 条） | §2.9 / P5 | 待定（需产品/工艺拍板「统一 +/−」的表达方式，见 P5） |
| L11 | **`fuzzy/specs.py` 反向依赖上层包**（E21 改名，原 `input_specs.py`）—— L39 `from ..field_contract import` ⇒ 层 0「对外接口格式」依赖了 `process.algorithms` 父包；`expert/specs.py` L19 同样 | §2.14.3 | 待议（不影响正确性；但层 0 作为「对外契约」反向依赖上层包与分层意图略有张力） |
| L12 | ~~**`sys.path` 仍有 2 行插父目录** —— `sanity_check.py` L43 插项目根（`molding-optima/`）⇒ `backend` / `frontend` 变顶层名~~ | §2.14.2 | ✅ **已关闭**（E19 删除 `sanity_check.py`，该文件连同其 2 行 `sys.path` 插入一并消失） |
| L13 | **内核 net 仍吃裸 dict** —— `NumTskRuleNet` 仍是 3 参（`rule_array` / `keyword_array` / `priority_array`）；`priority_array` 是「内核只认裸 dict」逼出的人造平行数组（`nets.py` 需手工维护 `kept_priorities` 同步，长度错位会静默算错） | §2.16 / §2.27 | 待办（下一轮：net 直接吃 `RuleProfile` / `KeywordProfile`，平行数组随之消失）。**E20 已把「谁产出契约」归位到位**（转换器在来源适配层、编排层不再越位构造）⇒ **剩下的只是「契约吃到哪一层」**；本轮用户拍板只做归属，贯穿留待下一轮） |
| L14 | **`library/files/rule_format.py` 是第二套规则串解析器** —— `from_rule_string`（L124-197）自己切词（`parts[0]/parts[1]/parts[2]`），与内核 `parsing.py` 的 `split_phase` 并存；且**带着内核 2026-10-22 E1 修过的同一个 bug**：多段词被误拆（`IV0_very_low` ⇒ level='very'；`inj_pres_1_low` ⇒ name='inj'） | §2.16 | 待办（Step 4：让它复用 `fuzzy_core.parsing`，不自己再写一套；**本轮 E11 只搬位置未改逻辑**，路径已更新） |
| L15 | **`diag_fuzzy_fix_simulation.py` 自 E7-b2 起就是坏的** —— L225 `rules = [(r.source_ref, r.rule_description) ...]` 把 `source_ref`（**字符串**）当对象用，但 L144 / L172 仍按老 ORM 实例读 `rm.priority` ⇒ `AttributeError: 'str' object has no attribute 'priority'`（exit=1） | §2.13 / §2.18 / §2.27 | ✅ **已关闭**（E20 顺手修：把 `priority` 显式带进 `rules` 元组（取 `RuleProfile.priority`），6 处解包点机械对齐 ⇒ 脚本 exit=1 → **exit=0**，诊断结论完整输出） |
| L16 | **`diag_fuzzy_field_registry_regression.py` 脚本内变量未定义** —— `NameError: name 'registry' is not defined`（exit=1） | §2.18 实跑 | ✅ **已关闭**（E16 顺手修：`_build_field_context` 现返回 `(keyword_dicts, classification)`，`classification` 是**名字列表**字典（`authority`/`guessed`/`unknown`）；旧代码写的是更早一版 API 的 `registry.report()` ⇒ 改调 `classification`；脚本现已 exit=0，场景 A/B 全部 PASS） |
| L17 | **端口 / 服务命名只说了 "Rule"** —— `RuleRepository` 实际同时承载**规则**与**关键字元数据**两类算法输入（docstring 早已写明「规则与字段元数据的读取端口」，但名字只提规则） | §2.19 | **部分关闭**（E13：`RuleQueryService` 语义已变为「**纯查询类**」、端口默认实现改为 `RuleRoutingService` ⇒ **名字与职责不再矛盾**；但 `RuleRepository` 同时承载两类输入这件事**仍未改名** —— 建议与 `RuleSource` 抽象一起做。E14：已在 `RuleRoutingService` 的 docstring 里**明确标注「这是刻意设计、不是历史包袱」**（规则与关键字在算法侧是**同级**输入）。**E15：端口已改名为 `AlgorithmResourceRepository` ⇒ L17 关闭**） |
| L18 | **全包 AST 扫描 13 个未使用 import**（`fuzzy` 包 3 个 + `tests` 10 个）—— `fuzzy_core/functional.py` 的 `Tuple`、`fuzzy_core/tests/test_nets.py` 的 `defuzz`、`fuzzy_core/utils/translate.py` 的 `np`、`tests/test_optimize_smoke.py` ×4、`tests/test_smoke_masterdata.py` 的 `Any`、`tests/verify_parameter_tree.py` 的 `Max`、`tests/verify_step1_full_dict.py` ×4 | §2.19 / §2.20 全包 AST 扫描 | 待办（**均为 HEAD（E4-b）就有的既有遗留**，非 E5~E13 引入；E8 曾记「与 HEAD 集合一致 = 3 个」—— 那是**只扫 `fuzzy` 包**的口径，**全包口径（`fuzzy` + `tests`）为 13 个**；**`library/` 下 0 个**） |
| L19 | **`_dev_refs/_tmp_split.py` 是写盘型地雷脚本** —— 它按段标记**改写** `library/keywords.py` 与 `library/rules.py`；E13 后段标题已变，重跑会**摧毁拆分成果** | §2.20 | ✅ **已关闭**（E13 **删除**该脚本，改以只读 AST 护栏 `_dev_refs/_chk_library_layout.py` 替代其诊断价值） |
| L20 | **编排本身随来源走** —— `ResourceRepository` 要**转手 ORM 实例**（`RuleLibrary` / `RuleMethod`）⇒ 它是**数据库来源特有**的；文件来源落地时会有**自己的编排实现** ⇒ 「判断逻辑」（`RuleService`）可共用，**「编排」不可共用**。要连编排也共用，得把「库 / method」换成**契约级载体（DTO）**而非 ORM 实例 | §2.23 | 待办（**与 `RuleSource` 协议一起做**；届时才知道 DTO 该长什么样。E16 已把这条边界写进 `library/repository.py` 的 docstring） |
| L21 | **契约未贯穿到内核** —— `profiles.py` docstring 说 `KeywordProfile` / `RuleProfile` 是内核「**唯一**接受的输入对象」，但内核 `NumTskRuleNet.__init__` 收到的仍是**裸 dict**（契约对象在进内核前被 `to_net_dict()` / `to_rule_array()` 拆回 dict）⇒ **契约层目前是中途站，不是终点**。配套三处不一致：① `contracts.py` 协议两侧不对称（`get_rules → List[RuleProfile]` 但 `get_keywords_by_names → List[Dict]`）② `fuzzy_algorithm._load_keyword_dicts` 的「推测论域」兜底分支直接拼裸 dict，**完全绕过 `KeywordProfile`** ③ `priority_array` 是裸 dict 逼出的人造平行数组（见 L13） | §2.27 | 待办（**与 L13 是同一件事的两面**：L13 = 内核签名，L21 = 协议与引擎侧的不一致；下一轮一起做，届时需把 `KeywordProfile.meta_source` 在推测论域路径上补齐） |
| L22 | **fuzzy 层 0 与 expert 层 0 结构未对齐** —— `expert` 是 `specs.py`（字段字典）+ `data_validator.py`（校验器）**分文件**；`fuzzy` 把「字段字典 + `OptimizeDataValidator` + 缺陷档位词表」**三样塞在一个 `specs.py`**（393 行）⇒ 文件名只覆盖了其中一样 | §2.28 | 待办（**下一轮**：拆出 `validator.py`，档位词表另置；本轮用户明确「只改文件名」，改名已完成，此为**结构**对齐项） |

| L23 | **算法包入口命名跨包分叉** —— E22 后 `fuzzy/engine.py`（类 `FuzzyEngine`）与 `llm/llm_algorithm.py`（类 `LLMEngine`）/ `empirical/empirical_algorithm.py`（类 `EmpiricalReasoning`）/ `rule_miner/rule_miner_algorithm.py` 风格不一致；且 `process/algorithms/__init__.py` 顶层现绑定名 `engine`（指向 `process.algorithms.fuzzy.engine`） | §2.29 | 待办（**下一轮拍板**：是否把 `llm` / `empirical` 一并改为 `*_engine.py` 以全仓统一；本轮用户明确「只改 fuzzy 两个文件」⇒ 未动。另 `field_names`（字段**名**）与 `specs`（字段**规格**）的分工已写进 `fuzzy/__init__.py` 命名约定） |

| L24 | **「recommendation」词根在仓库内有两个模块** —— E23 后 `fuzzy/recommendations.py`（算法层产出，`AlgorithmRecommendation`）与 `process/models/recommendation.py`（ORM 模型 `Recommendation`）**同词根、不同目录**。注意 **E6 已为消解同名冲突把算法层 `Recommendation` 改名 `AlgorithmRecommendation`**；本次是**模块名**层面，Python 层面不冲突（同 `fuzzy/specs.py` 与 `expert/specs.py` 先例） | §2.30 | 待办（**低优先级**：若将来 ORM 侧也要动，优先统一为 `models/advice.py` 之类；**当前不动** —— 改名涉及 migration 引用，风险远大于收益） |

| L25 | **非高斯隶属度函数全仓零外部调用点** —— E25 后 `memberships.py` 提供 **9 个形状**（高斯/双高斯/三角/梯形/广义钟形/代数钟形/S 型/Z 型/单点），但生产只走 `gauss`（`nets.py` 恒用 `DEFAULT_MEMBERSHIP_TYPE`）⇒ 其余 8 个是**已备好但未接线**的能力 | §2.31 / §2.32 | **部分关闭**（E25 给了统一签名 + `MEMBERSHIP_SPECS` 分派表 ⇒ 「加一个形状」的成本降到 **1 行分派**；**但「接线到生产」仍未做** —— 需要业务侧确定各工艺字段该用哪种形状，属另一轮） |

| L26 | **上游论域可能倒挂 / 退化** —— `engine.py` 的推测论域兜底是 `max_val = 当前值 * 2`，于是**当前值为负 ⇒ 区间倒挂**（`[0, -6]`）、**当前值为 0 ⇒ 区间退化**（`[0, 0]` ⇒ σ=0 ⇒ 隶属度恒 0/nan）；改前靠「σ 带符号 + 高斯只用 σ²」硬抗下来，E25 已在 `features.py` 层把跨度取绝对值并加 warning | §2.32 踩坑 4 | 待办（**上游修**：`engine.py` 推测论域应给一个**正下限**（如 `max(current*2, 0.01)`）；但那会改变「当前值为 0/负」场景的推理结果 ⇒ 需单独一轮评估影响面） |

| L27 | **隶属度形状的选择策略缺失** —— E25 让 9 个形状全部可用，但**「哪个工艺字段该用哪种形状」没有任何依据**（当前恒用高斯）；且不同形状的 `width` 语义不同（高斯 = 2σ、三角 = 底边跨度、梯形 = 含平顶、S/Z 型 = 过渡带尺度） | §2.32 | 待办（**需要业务输入**：各参数的分布形态（对称/偏斜/单调）与过渡带宽度要求；可先在 `_dev_refs` 做参数扫描对比，而不是直接改生产默认值） |



---

## 7. 变更记录

| 日期 | 轮次 | 变更 |
|---|---|---|
| 2026-10-23 | E1-b | 新建本文档；产出 §3 命名对照表（术语总表 22 项 + 冲突台账 N1~N14 + 待定项 P1~P4）；完成引用点全景调研（§2.3） |
| 2026-10-23 | E1 | 代码侧零风险修正：`rule_query_service.py` 8 处 docstring（「三级」→「四级」N6、规则库层级→组织维度 N5、过期术语「工厂级/兜底层」→`NumTskRuleNet`/`FuzzyRuleNet`）；`fuzzy_algorithm.py` 删死 import（`RuleMethodAdapter` N9 / `ParticularRules` N14）+ 删死属性 `self._rule_net`（N10）。验收：sanity 全绿 + pytest 17/5 + 黄金快照 49 样本 diffs=0。新增存档 `_dev_refs/_golden_E1.json` |
| 2026-10-23 | E2 | **故障边界 + 去 DB 依赖**（详见 §2.5 / §2.6）。新增 `ports.py`（`RuleRepository` 协议 + 数据类搬迁，零 ORM 依赖）；`rule_query_service.py` 改为从 ports 导入并新增 `get_keywords_by_names`；`fuzzy_algorithm.py` 支持 `FuzzyEngine(repository=...)` 注入（默认实现延迟导入）、`recommend()` 拆为兜底壳 + `_recommend()` 主流程、规则查询异常单独捕获（error 级）、新增 `_precheck_numeric_rules()` 条目级预检与 `self._diagnostics`。修正 N8 判断错误（`extra` 是弹窗文本通道）；新增 N15（`'level'` 一词两义）。验收：黄金快照 49 样本 diffs=0 + sanity 全绿 + pytest 17/5 + 离线验证 7 项 PASS。新增 `_dev_refs/_verify_e2_offline.py`（可复用的离线回归工具）与 `_dev_refs/_golden_E2.json` |
| 2026-10-23 | E3 | **中间态类型化 + 拆聚合**（详见 §2.7）。新增 `aggregation.py`（224 行）：`RuleAdjustment` / `AggregatedAdjustment` 两个 dataclass + `aggregate()` + `to_recommendations()`。`fuzzy_algorithm.py` 776 → 697 行：中间态裸 dict → dataclass（`'param'`→`param_name`、`'source'`→`layer` / `meta_source`），删除 `_merge_layer_results`（95 行，混聚合+契约两事），`_recommend()` 第 5 步改为调 `aggregate()` + `to_recommendations()`。落地 N1/N2/N4/N7；**N3 排除**（`'lvl'` 是内核输入契约 key，见 §6 L9）。修正 advisory 路径硬编码的 `'rule': 'advisory'` → `rule_str=None`。`sanity_check.py` CASE 3 从**复刻品**改为**直接测真函数**（复刻品已漂移：漏了「文本建议分离」规则），并补上文本建议用例与 `to_recommendations()` 公式/对外字符串断言；`backend/tests/test_fuzzy_field_report.py` 随 `'source'`→`'meta_source'` 同步。实测纠正 §2.6：导入已可离线（原写「仍需 Django setup」是 E2 时的推测，未实测）。验收：黄金快照 49 样本 diffs=0 + sanity 全绿 + pytest 17/5 + 离线验证 7 项 PASS。新增存档 `_dev_refs/_golden_E3.json` |
| 2026-10-23 | E4-a | **命名契约归位**（详见 §2.8）。新建 `process/algorithms/fuzzy/naming.py`（230 行）：3 张表（`FIELD_NAME_ALIAS` 23 条 / `FIELD_INDEX_OFFSET` 10 条 / `FAMILY_FIELD_ALIAS` 1 条）+ `to_business_name()` + import 时表间一致性自检（`_validate_tables()`）。`fuzzy_algorithm.py` 697 → 582 行：`FIELD_NAME_ALIAS` 拆为「前缀表 10 条 + 完整表 13 条」再合并（**对外结构与顺序不变**），`to_business_name()` 第 3 段由「遍历总表 + 排除法」改为「只查完整表」，消除「新增前缀映射忘同步偏移表 ⇒ 段号错位」的隐患。`FuzzyEngine` 保留兼容别名 + 兼容入口 ⇒ `parameter_optimize.py` L245/L534 **零改动**；`fuzzy/__init__.py` 导出 `naming`。实测纠正 §3.2：表的条数是 **23 条**（原写 33 条）。验收：黄金快照 49 样本 diffs=0（vs `_golden_E3.json`，全 JSON 逐条相等）+ sanity 全绿 + pytest 17/5 + 离线验证 7 项 PASS + 命名契约等价性对拍 ALL PASS（三张表逐条含顺序一致、`to_business_name` 262 输入对拍全一致）。新增存档 `_dev_refs/_golden_E4.json` |
| 2026-10-23 | E4-b | **段号口径修正**（详见 §2.9）。`brl_temp` 由 `FULL_FIELD_ALIAS` 移入 `PREFIX_FIELD_ALIAS`（偏移 0，1-based 同构）⇒ `brl_temp_1..9` ↔ `BT1..BT9` 段号对齐（**修复 BT1 段号空缺**）；`FAMILY_FIELD_ALIAS` **整表删除**，`to_business_name()` 删族分支、`BT`（无号）退役返回 None；编排层 `_normalize_field_name_by_spec` 删 `family_spec` 参数与两处族分支（三类映射 → 两类）；`FuzzyEngine.FAMILY_FIELD_ALIAS` 兼容别名一并删除（5 个 dev 诊断脚本同步改）；`empirical/hints.py` 7 处历史写法 `"BT"`→`"BT1"`（语义等价，写回目标仍是 `brl_temp_1`）。新增 N16（段号错位）、P5（「统一 +/−」怎么表达，待拍板）、L10（169 条族级规则失去输入）。实测证据：内核实测 `BT` 值 250（0~50 区间）⇒ `BT_low`/`BT_high` **均不命中**（169 条规则恒不激活）；`BT1` 值 250（150~350）⇒ **正常命中强度 1.0**。验收：黄金快照 `summary`/`only_before`/`only_after`/`changed_delta` 新旧全同（推荐输出零变化）+ sanity 全绿 + pytest 17/5 + 离线验证 7 项 PASS。新增存档 `_dev_refs/_golden_E4b.json` |
| 2026-10-23 | E5 | **命名契约双向闭合**（详见 §2.10）。`naming.py` 新增 `to_algo_name()`（单名）+ `to_algo_params()`（批量，无对应算法字段的键原样保留）+ `_validate_round_trip()`（import 时自检：正向译出的算法名必须能反向译回）。编排层 `parameter_optimize._normalize_field_name_by_spec()` **删除**（重复实现）⇒ `_compose_algorithm_context` 改调 `naming.to_algo_params`；`_to_business_param_name` 改调 `naming.to_business_name`。`FuzzyEngine` 补 `to_algo_name()` / `to_algo_params()` 兼容入口（外部零改动）。5 个 dev 诊断脚本同步改调契约层。新增 `_dev_refs/_verify_naming_forward_parity.py`（旧实现冻结为独立参照系，逐条对拍）与 `_dev_refs/_compare_golden.py`（黄金快照整棵 JSON 逐条 diff）。验收：黄金快照 49 样本逐条 diff=0 + sanity 全绿 + pytest 17/5 + 离线验证 7 项 PASS + 往返闭合 0 不闭合 |
| 2026-10-23 | E6 | **同名消歧**（详见 §2.11）。算法层 `base.Recommendation` **改名** `AlgorithmRecommendation` —— 消解与 ORM `models.Recommendation` 的同名冲突（编排层此前只能靠 `as AlgoRecommendation` 别名区分，而编排层正是高频改动区）。6 个实现方 import 同步（`fuzzy_algorithm` / `aggregation` / `empirical_algorithm` / `llm_algorithm` / `parameter_optimize` / `tests/verify_provided_smoke`），`parameter_optimize` 的 `AlgoRecommendation` 别名取消；代码内文字引用更正（`condition.py` ×2 / `sanity_check.py` ×1 / 3 个 dev 脚本 ×4）。**`to_dict()` 的 7 个对外 key 不动**。⚠️ 破坏性变更：`process.algorithms.Recommendation` 不再导出（旧名 → `AlgorithmRecommendation`）。验收：diff 逐行审计（零逻辑变更）+ sanity 全绿 + pytest 22 passed + 离线验证 7 项 PASS + provided_smoke 6/6 + 导出面验证 |
| 2026-10-23 | E7 | **算法输入契约**（详见 §2.12）。新增 `fuzzy/rule_spec.py`：`FuzzyKeywordSpec` / `FuzzyRuleSpec` 两个 dataclass（算法输入契约）+ `to_keyword_array` / `to_rule_array` / `to_priority_array`（标准格式 → 内核输入数组）+ `validate_keyword_specs` / `validate_rule_specs`（数据来源产出的关口）。命名消歧：用户建议的 `FuzzyRule` 与内核 `fuzzy_core.models.nets.FuzzyRule`（规则串解析器）**同名不同物** ⇒ 统一加 `Spec` 后缀（`*Spec` = 数据契约，内核同名类 = 行为体）。**零外部依赖**（不 import Django / ORM，可 `python rule_spec.py` 独立自检）。本轮**不动现有链路** ⇒ 行为零变化。验收：sanity 全绿 + pytest 22 passed + 离线验证 7 项 PASS + provided_smoke 6/6 + 零依赖导入检查 |
| 2026-10-23 | E7-b1 | **接线·第一步（加能力）**。① `FuzzyRuleSpec` 扩为 5 字段：新增 `conclusion_kind`（numeric/advisory）+ `specificity`（1~4）⇒ **完整覆盖** 旧 `ResolvedRule` 的全部有值字段（`rule_str`→`rule_description`、`method`→`source_ref`）；校验同步扩充（新增 `VALID_CONCLUSION_KINDS` / `VALID_SPECIFICITY`）。② `adapters.RuleKeywordAdapter` 新增 `to_keyword_specs()` —— 数据来源的**解析出口**（ORM 实例 / dict → `FuzzyKeywordSpec`），字段名与 `to_fuzzy_dict` 输出天然对齐，无需额外映射表。**未切换任何现有调用点** ⇒ 行为零变化。验收：契约层自检（非法规则规格一次拦全 3 项）+ `adapters` 自检 + sanity 全绿 + pytest 22 passed + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + 零依赖导入检查 |
| 2026-10-26 | E7-b2 | **契约接线（切换使用点）**（详见 §2.13）。`ResolvedRule` **退役** —— 删掉 `ports.py` 里的定义，`RuleRepository` 协议改用 `FuzzyRuleSpec`；`RuleQueryService.get_rules` 改产 `FuzzyRuleSpec`（`source_ref=f'RuleMethod:{rm.id}'`）；`fuzzy_algorithm` 7 处类型标注 + 6 处 `r.rule_str`→`r.rule_description`。**转换逻辑收敛**：`to_rule_array` / `get_priority_array` 改为端口转发，唯一实现落在 `rule_spec`（消除重复）。**12 个文件**同步（含 pytest 套件内的 `tests/test_fuzzy_field_report.py`、`_verify_e2_offline.py`、5 个 `diag_fuzzy_*.py`、`sanity_check.py` 遗留 mock 标注）。⚠️ 未动 `RuleAdjustment.rule_str`（另一个类型的字段）。验收：残留 `ResolvedRule` 0 处 + `.rule_str` 访问点 0 处 + AST 未使用 import 0 + sanity 全绿 + pytest 22 passed + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + **E2 零依赖成果保持** + 真实 DB 端到端（`source_ref` 已填、无 ORM 泄漏） |
| 2026-10-26 | E7-c | **标准化输入参数层改名**（详见 §2.13.6）。`fuzzy/rule_spec.py` → **`fuzzy/algorithm_inputs.py`** —— 起因是用户第 28 轮质疑「这个我的本意是想说明这是算法中用到的 keyword 和 method 对象……但当前这个文件名叫 rule_spec，是否符合要求？」。诊断三条：① 名不副实（keyword 侧与 rule 侧各占一半，名字只说 rule）② **与同包 `fuzzy/specs.py`（调优入参契约，已被 `__init__.py` docstring 登记为“spec”代表）语义撞车**，两者正交却同名族 ③ 漏掉「不管 DB 还是文件最终都格式化成这里定义的格式」这个核心语义。**类名 `FuzzyKeywordSpec` / `FuzzyRuleSpec` 不变**（`*Spec` 后缀的作用是与内核 `FuzzyRule` 消歧，不对齐文件名）。改动 = 1 次重命名 + 5 个 import 路径 + 6 处文字提及 + docstring 措辞统一（「算法输入契约」→「标准化输入参数」）。历史行保留原文件名（记录当时事实）。验收：模块路径引用 0 + pytest 22 passed + sanity 全绿 + 契约层自检 + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + 零依赖保持 |
| 2026-10-26 | E7-e | **来源层归位·建 `sources/`**（详见 §2.13.9）。起因是用户第 33 轮给出**业务视角 5 层**模型（定义入参出参 / 定义内部数据结构 / 读取算法依赖 / 构建模糊核心 / 推理）并指出文件结构需要重组。结论：业务 5 层 ≡ 依赖方向 6 层（只差「端口」层与排序）；**逻辑分层 ≠ 物理目录**——只有第 ③ 层（多来源并列）需要目录，其余留包根（`naming.py` / `input_specs.py` 被外部直接 import，搬进子目录要改公共路径）。新建 `fuzzy/sources/`：`__init__.py`（`RuleRepository` 协议 + `RuleQueryContext`，**零依赖**）/ `db.py`（`RuleKeywordAdapter` + `RuleQueryService`，DB 专属，依赖 ORM）/ `text.py`（`RuleMethodAdapter`，**来源无关**的规则格式翻译器，零依赖）/ `files/`（文件来源空壳）。**消亡 5 个路径**：`ports.py` / `adapters.py` / `services/` / `rules/` / `services/rule_query_service.py`。两条约束：`sources/__init__.py` 绝不 import `sources.db`（否则 ORM 进编排层，破坏 E2 成果）；`sources/text.py` 必须零依赖（它是未来文件来源的解析器）。**纠正误判**：`RuleMethodAdapter` **不是死代码**（§2.13.8.3 原写「建议删除」作废）——它翻译的是「规则**长什么样**」而非「规则**从哪来**」，文件来源会用它。**顺带修好** `tests/verify_fuzzy_nested_context.py`（**改前就是坏的**：patch 目标 `fuzzy_algorithm.RuleQueryService` 在模块级不存在，因该类是函数内延迟导入；HEAD 版同样报 `AttributeError`）⇒ 3 处 patch 目标改指 `sources.db.RuleQueryService.get_rules`，现 PASSED。验收：残留扫描各 0 处 + 零依赖保持 + AST 新文件未使用 import 0（并随旧文件删除消除既有 `Optional` 1 个）+ pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + `sources/text.py` 自检 + 端到端真实 DB 复验（命中 10 条 / `RuleMethod:20` / 无 ORM 泄漏） |
| 2026-10-26 | E8 | **`sys.path` 治理**（详见 §2.14）。起因是用户第 35 轮质疑「`sys.path.insert(0, FUZZY_DIR)` 这个做法一看就容易带来风险」。诊断：`sys.path.insert` API 本身不错，错在**把「包目录」当「顶层包搜索根」** ⇒ `fuzzy/` 下的 `fuzzy_core`/`sources`/`elements`/`input_specs`/`aggregation`/`naming` 泄漏成顶层模块名（**静默劫持**）；`process/algorithms/` 更让 `fuzzy` 看起来像顶层包，而它带 `from ..field_contract import` 相对导入 ⇒ 一旦被顶层导入必抛 `attempted relative import beyond top-level package`（**硬崩**）。改动 7 个文件：`sanity_check.py`（删 2 行插入 + 13 处）/ 内核测试 2 个（改插 `backend/` + 6 处）/ dev 脚本 4 个（8 处），每处补「不要把包目录加进 `sys.path`」警示注释；顺带修 `test_nets.py` docstring 的错误运行路径（`engines`→`algorithms`）。**同时归档** §2.15「`fuzzy_core` 不改名 `core`」的讨论结论：顶层包名按「全局唯一」标准命名，纯模块名才按「包内简洁」标准命名。验收：残留扫描各 0 处 + **顶层名泄漏清零** + 零依赖保持 + AST 未使用 import 与 HEAD 集合一致 + BOM 不变 + pytest 22 passed + 内核测试两种跑法 + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke PASSED + dev 脚本与 HEAD 字节级副本行为一致（3 个脚本 exit=1 均为既有行为）+ 端到端真实 DB 复验 |
| 2026-10-26 | E9 | **内核输入契约归位**（详见 §2.16）。起因是用户连续四问：「keyword和method应该由core定义，否则就需要将fuzzy_core平铺」＋「nets.py 84-208 这不就是以前算法定义的RuleInput和KeywordInput吗」＋「这两个应该实现成真正的算法契约，而不是再重新定义一份」＋「我的意思不是删除dict，我只是想表明要规范算法中的对象」。诊断三条：① `FuzzyFeature` / `FuzzyRule` **从来不是输入契约**，而是内核内部由裸 dict 构造出的产物（旧 L244 / L274 / L285）② `elements.py` 想立的契约被**自己的** `to_*_array()` 掐死 ⇒ 现状是「没有契约 + 两套半成品」③ 真契约一直无类型（三个裸 list）。**决策**：契约归内核所有（否决「内核最小输入 + 外层继承」的骑墙方案）；**不消灭内核内部的 dict**（消灭的只是边界上的隐式契约）。**命名** `KeywordProfile` / `RuleProfile`（否决 `*Input` / `*Spec`：「input或者specs都不想对象的感觉」）。改动：新建 `fuzzy_core/profiles.py`（契约 + 转换 + 校验）、`fuzzy_core/models/features.py`、`fuzzy_core/models/rules.py`；`nets.py` 只留 3 个 net；`models/__init__.py` 改三来源导出；`utils/translate.py` 改从 `..macros` 取 `DEFECT_CONST`（不走 nets 绕路）；**消亡 `fuzzy/elements.py`**（从未提交）；外层 6 处 import 改指 core（`sources/db.py` / `sources/__init__.py` / `fuzzy_algorithm.py` / 2 个 dev 脚本）+ 2 处残留（`sources/files/__init__.py` docstring / `diag_fuzzy_level_word_crash.py`）；`fuzzy/__init__.py` 分层清单 6 层并为 5 层。验收：pytest 22 passed + 内核测试两种跑法 + sanity 全绿 + 离线验证 8 PASS/0 FAIL（exit=0）+ provided_smoke PASSED + 端到端真实 DB 复验 + 零依赖保持 + 残留扫描 0 + `profiles.py` 独立自检。**如实边界**：本轮只是搬 + 改名，内核 net 仍吃裸 dict（见 §6 L13） |
| 2026-10-26 | E10 | **端口归位**（详见 §2.17）。起因是用户质疑「`sources` 命名不恰当，这好像是想说算法的 source 一样，但是我们这究竟想表明什么？」，并确认「外层管理数据传给内核，而不是内核自己管理数据」。诊断：`sources` 三重不合适（词义歧义 / 覆盖不全 / 粒度误导），根因是**目录内职责不同质** —— 用 I/O 词命名一个同时装着领域逻辑（`db.py` 里的四级特异级匹配、档位过滤、结论分流）的目录。决策（方向 B，用户批准）：**端口属消费方**（依赖倒置）⇒ `RuleRepository` + `RuleQueryContext` 从 `sources/__init__.py` 移到包根 **`fuzzy/ports.py`**；`sources/` 退回纯来源实现目录，名字恢复名副其实；`text.py` 暂不动（归宿是与内核 `parsing.py` 合流，属 Step 4）。改动 = 新建 `ports.py`（99 行）+ `sources/__init__.py` 瘦身（110 → 13 行，纯 docstring）+ 4 处 import 改写 + `fuzzy/__init__.py` 分层清单 + `profiles.py` docstring 反向引用修正。**这是"走回头路"但非原样复原**：E7-e 迁走过，本轮带着「端口属消费方」的明确理由搬回，且内容已更新（`FuzzyRuleSpec` → `RuleProfile`）。验收：pytest 22 passed + 内核测试两种跑法 + sanity 全绿 + 离线验证 8 PASS/0 FAIL（exit=0）+ provided_smoke PASSED + 端到端真实 DB 复验（exit=0）+ 零依赖保持 + 残留扫描 0 + AST 未使用 import 0 |
| 2026-10-26 | **E11** | **规则库适配层归位**（详见 §2.18）。起因：用户指出 `fuzzy/library` 是历史任务未完成的部分。诊断：`library/` 已生成但**完全跑不起来** —— 7 处未完成（D1 `keywords.py` 是过期副本且 import 即 `NameError` / D2 `rules.py` 自带适配器遮蔽 import / D3 缺 `KeywordProfile` / D4 缺 `library/files/__init__.py` / D5 12 处 import 仍指 `sources.db` / D6 `sources/` 未删 / D7 6 处 docstring 过时）。**根因定位到具体一行**：上一轮的拆分脚本 `_dev_refs/_tmp_split.py` 段标记写成 `'# ====\n# RuleKeywordAdapter'`，而真实分隔线是 78 个 `=` ⇒ `index()` 抛 `ValueError` ⇒ **脚本写盘前就崩了** ⇒ 拆分从未发生 ⇒ 两个文件各留两份类。**修复**：段定位改为「按行扫分隔线 + 看下一行标题」，不写死 `=` 个数 ⇒ 拆出 `keywords.py` 105 行（仅 `RuleKeywordAdapter`）/ `rules.py` 278 行（仅 `RuleQueryService`）+ 补 `library/files/__init__.py`。**接线**：12 处 import 改指 `library.rules` / `library.keywords`，其中 `RuleQueryContext` 统一取自 `fuzzy.ports`（跟随 E10「端口属消费方」，与 `_verify_e2e_db.py` 已有写法一致）；**删 `sources/` 4 文件**（该目录本就是未跟踪的，与 `library/` 同批）+ 改 6 处 docstring 措辞 + 6 处注释里的模块名举例。**关键不变量**：搬迁前 `git diff --no-index` 差异仅 8 ins / 9 del，**全在 docstring + import 行** ⇒ **零个方法体改动**。验收：**黄金快照 49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E5.json`）+ pytest 22 passed + 内核测试两种跑法（11/11 + 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端（命中 10 条 / `RuleMethod:20` / ORM 泄漏 0 / 契约校验通过）+ 零依赖保持 + 残留扫描 0 + AST 未使用 import 0 + BOM 保持。**如实边界**：① L14（第二套规则串解析器）**本轮未动**（只搬位置未改逻辑，属 Step 4）；② 实跑发现 2 个 dev 脚本自身缺陷（`diag_fuzzy_fix_simulation.py` 自 E7-b2 起就把 `source_ref` 字符串当对象用；`diag_fuzzy_field_registry_regression.py` 变量 `registry` 未定义）⇒ 已登记为 L15 / L16，**非 E11 引入**，本轮不越界修 |
| 2026-10-26 | **E12** | **来源层类职责对称化**（详见 §2.19）。起因：用户对 E11 终态提问「`rules.py` 这个查询服务中有查询 keywords 吗？keywords 和 methods 都是算法的一部分」。诊断：**文件级对称了，类级没有** —— 关键字侧的「查库」被塞进了「转换器」`RuleKeywordAdapter`（= E7 开的同一个病「取数与业务逻辑焊死」在关键字侧的对应症状），且 `library/__init__.py` L30-32 早已写明「输出是 `RuleProfile` / `KeywordProfile`（内核输入契约）」而实现吐的是裸 dict ⇒ **文档兑现了、实现没兑现**；而**端口层其实是对的**（`RuleRepository` 本就同时暴露 `get_rules` + `get_keywords_by_names`）⇒ 歪的是实现层的类边界与命名。**决策**（用户确认）：类级对称化（新增 `KeywordQueryService` 承担查库、`RuleKeywordAdapter` 退化为纯转换器、`RuleQueryService.get_keywords_by_names` 保留门面转发）+ 命名**先只改 docstring**（改名登记 L17）+ **端口与编排层零改动**。改动 = `library/keywords.py`（新增服务 + 摘掉查库 + docstring）/ `library/rules.py`（门面转发 + import + 类 docstring）/ `ports.py`（docstring + **键名 `'source'` 修正为 `'meta_source'`**）/ `library/__init__.py`（对称结构表）/ `diag_fuzzy_rule_journey.py`（改走生产门面 + 摘无用 import）/ `naming.py`（清 E5 遗留的未使用 import）。新增 3 个验收脚本：`_verify_kw_parity.py`（关键字路径新旧对拍）/ `_verify_zero_dep.py`（零依赖不变量）/ `_audit_unused_imports.py`（AST 未使用 import 审计，修正 `noqa` 口径）。验收：**黄金快照 49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E11.json`）+ 关键字路径新旧对拍 PASS（真实 DB，含键序/类型全等）+ pytest 22 passed + 内核测试两种跑法（11/11 + 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0 + 命名契约对拍 PASS + 零依赖保持 + AST 全包扫描（清 E5 遗留 2 个，剩 3 个 HEAD 既有遗留登记 L18）。**如实边界**：① L14/L15/L16 **本轮仍未动**；② L17 命名待改（按用户决定只改 docstring）；③ L18 的 3 个既有遗留未越界修 |
| 2026-10-26 | **E13** | **来源层文件级对齐 ·「查询是查询，管理是管理」**（详见 §2.20）。起因：用户对 E12 终态提问「同样的 `rules.py` 1-291 / `keywords.py` 1-142 这两文件也应该对齐，查询是查询，管理是管理」。诊断：**E12 只对称了类** —— 关键字侧已是「查询 + 管理」两条线，规则侧却仍是**一个 `RuleQueryService` 类 9 个方法**，其中**只有 2 个真正查库**，其余 7 个是纯业务判断（选库策略 / 四级特异级 / 档位过滤 / 结论分流 / 契约构造）⇒ **查库与管理焊死**，且**无法单独替换数据源**。**引用面调研**（决定 blast radius）：生产 **1 处**（`fuzzy_algorithm._get_repository()` 延迟导入）+ 测试 **3 处**（`verify_fuzzy_nested_context` 的 patch 目标）+ dev 脚本 **11 个文件**（全部只调门面方法）；`get_libraries` / `_product_to_library_codes` / `_match_defect_level` / `classify_conclusion_kind` / `select_libraries` / `get_methods` 实测**零外部调用方**（只在 `library/rules.py` 内部）。**决策**：**2v2 对称** —— 规则侧 `RuleQueryService`（查询，2 个方法，只碰 ORM）+ **`RuleRoutingService`（管理，9 个方法，不碰 ORM，同时是 `RuleRepository` 端口默认实现/门面）**；关键字侧沿用 E12 的 `KeywordQueryService` + `RuleKeywordAdapter`。**三处行为等价地雷已避开**（均写进 docstring）：① 选库**逐个**查库而非批量 `__in`（否则同 priority 库的相对顺序变 → 下游规则遍历顺序变 → 产出顺序可能变）；② 规则库以 **ORM 实例**传递而非 `library_code` 字符串（同 code 可能对应多条库记录，改字符串会改变 SQL 语义与命中条数）；③ 兜底库 `base` 单独一次查询并带 `library_type='fuzzy'`（其余不带），保持原三步语义。改动 = `library/rules.py`（291 → 357 行，`RuleQueryService` 收缩 + 新增 `RuleRoutingService` + docstring 对称表）/ `library/keywords.py`（docstring + 3 处类名）/ `library/__init__.py`（对称表改为「查询 / 管理」两行 + 门面说明，42 → 45 行）/ `library/files/rule_format.py` / `ports.py`（默认实现改 `RuleRoutingService`）/ `fuzzy_algorithm.py`（延迟导入 + 2 处 docstring）/ `sanity_check.py` / `input_specs.py` / `process/models/rules.py` / `tests/verify_fuzzy_nested_context.py`（**3 处 patch 目标**）+ **11 个 dev 脚本改名**。**新增只读 AST 护栏** `_dev_refs/_chk_library_layout.py`（管理侧**不得**出现 `.objects` + 查询侧**必须**出现 `.objects` + 交叉污染 + 旧目录消亡）⇒ 把「查询是查询、管理是管理」从 docstring 约定变成**可执行断言**；并**删除写盘型地雷脚本** `_tmp_split.py`（重跑会摧毁拆分成果）。⚠️ 批量改名**不能用编辑工具的「全部替换」**（实测在部分历史脚本上只命中第一处，编码已核实为 UTF-8 无 BOM）⇒ 改用 `_rename_to_routing.py`（`str.replace` 全量 + `newline=''` 保 CRLF + 补回多行 import 尾逗号），并以 `git grep` 残留扫描收尾（首轮 TARGETS 漏 2 个文件，第二轮补扫）。验收：**黄金快照 49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E12.json`）+ pytest 22 passed + 内核测试两种跑法（11/11 + 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0 + 关键字路径新旧对拍 PASS（ORM 泄漏 0）+ 零依赖保持（顶层名泄漏 NONE）+ **library/ 布局自检 PASS** + AST 全包扫描 13 个（**全为 HEAD 既有**，`library/` 下 0 个）。**如实边界**：① L14/L15/L16 **本轮仍未动**；② L17 **部分兑现**（`RuleQueryService` 语义已变为纯查询类、端口默认实现改为 `RuleRoutingService` ⇒ 名字与职责不再矛盾；但 `RuleRepository` 同时承载规则与关键字这件事**仍未改名**）；③ L18 的 13 个既有遗留未越界修 |
| 2026-10-26 | **E14** | **来源轴补刀 ·「碰 ORM 的 = 来源特有，不碰 ORM 的 = 来源无关」**（详见 §2.21）。起因：用户审 E13 终态时打开 `library/rules.py` 问「你之前的方案中不是会在 library 中新增一个文件管理 repository 吗？这是换房干了？」。**核查结论**：原方案（§2.12 L416 / §2.13.7.3 L634 / §2.13.9 L761，三轮都记着）确实规划过在 `library/` 下**按来源并列建文件** —— `RuleSource` 协议 + `DbRuleSource` / `FileRuleSource`，且规定「库只作**检索维度**，**选库的业务映射留在构建层（不污染数据源）**」⇒ **至今未做**；E13 切的是**「查询 / 管理」**轴，与来源轴**正交**（不是替代），且 E13 的 `RuleQueryService` 恰好就是 `DbRuleSource` 的「检索维度」那一半 ⇒ **不白做**；⚠️ **但有一处真冲突**：`RuleRoutingService` 住在**按内容域命名**的文件里、起来源无关的名字，却**返回 ORM 实例**、**直接调查询侧** ⇒ **DB 专属的类占了来源无关的位置**；同时原方案「选库的业务映射不污染数据源」的约束被 `_product_to_library_codes` 住在 `library/` 里**违反**。**代码明文证据**：`library/files/__init__.py` L5「与**数据库来源**的关系」、`library/files/rule_format.py` L3「**来源无关**部分」/ L15「**不塞进 `library.rules`**」（后者在 E14 前**与事实不符** —— `library/rules.py` 里住着 3 个同样不碰 ORM 的纯判断方法）。**决策**（用户拍板选项①「只补这一刀」）：新建 `library/policy.py`（`RulePolicy`，**零 ORM**，只 import `fuzzy_core.profiles` / `fuzzy_core.parsing` / `fuzzy.ports`）接管 6 个纯判断方法 ⇒ `RuleRoutingService` 由 9 方法瘦身为 **6 方法**（`split_by_conclusion_kind` / `to_rule_array` / `get_priority_array` 保留**门面转发**以满足 `RuleRepository` 端口协议）；**不动目录结构、不落 `RuleSource` 协议、不改名**。改动 = `library/policy.py`（新建 179 行）/ `library/rules.py`（**3 个方法体搬到 `policy.py`，现 280 行**）/ `library/keywords.py` / `library/__init__.py`（**两张结构表，现 60 行**）/ `ports.py` / `input_specs.py` L311 / `_chk_library_layout.py`（新增 `source_neutral` role + `_imports_orm()`）/ `_verify_zero_dep.py`（`_BANNED` 增 `library.policy`）/ 2 个 dev 脚本。**护栏升级**：把「来源无关」变成**可执行断言** —— 比 E13 的「管理侧不得出现 `.objects`」更强：**整个文件连 `process.models` 的 import 都不许有** ⇒ 真的能脱离数据库独立 import（实测 `django=False` / `process.models=False`）。验收：**黄金快照 49 样本整棵 JSON 逐条 diff = 0**（vs `_golden_E12.json`）+ pytest 22 passed + 内核测试两种跑法（11/11 + 6/6）+ sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0 + 关键字路径新旧对拍 PASS + 零依赖保持（新增 `library.policy` 禁止项）+ library/ 布局自检 PASS + AST 全包扫描 13 个（**`policy.py` 贡献 0**）。**如实边界**：① **`RuleSource` 协议抽象与 `library/` 来源轴目录重排本轮仍未做**（用户选择「只补一刀」）⇒ `library/files/` 仍是空壳；② L14/L15/L16 未动；③ L17 仍未关闭（只在 docstring 里标注「刻意设计」） |
| 2026-10-26 | **E15** | **端口搬入 `library/` + 改名瘦身**（详见 §2.22）。起因：用户连续四问 ——「repository 的定位其实是算法用的 keyword 和 rule」「rule 可能会涉及到 library 和 method，我认为这样是有层次的」「或者将 rule 的编排放在 repository 中也可以，rule 只负责规则部分的」「ports.py 1-106 这个不适合放在外层，放在 ...\fuzzy\library 比较合适」。**核查结论**：E14 的 `policy.py` 定位**站不住**（它只是「规则串语义判定」这一个函数簇 ⇒ 是**内容域轴**而非来源轴，与用户心里「rule / keyword / repository 三层」不匹配），而 `RuleRoutingService` 那个「来源无关」的名字实指「**数据库来源特有的编排**」⇒ 名实不符。**判据**：依赖倒置的**实质检验**是「高层不被低层实现拖住」，不是「端口文件必须在调用方目录」⇒ **E10 的「端口属消费方」结论不变、位置变**（`library/ports.py` 零 ORM）。**改动** = `fuzzy_core/profiles.py` 新增 `split_by_conclusion_kind`（+34 行，纯字段分组）+ **新建 `library/ports.py`**（103 行，`AlgorithmResourceRepository` Protocol **2 方法** + `RuleQueryContext`）+ **`fuzzy/ports.py` 消亡**（`RuleRepository` → `AlgorithmResourceRepository`，5 方法 → 2 方法）+ `library/policy.py` 删 3 个已入内核的方法（179 → 149 行）+ `library/rules.py` 删 3 个门面转发（281 → 259 行）+ `fuzzy_algorithm.py` 4 处加工调用改调内核 + `fuzzy/__init__.py` 分层图 + `library/__init__.py` 结构表 + `_verify_zero_dep.py` L41 + 5 个 dev 脚本与 1 个测试的加工调用。**验收**：黄金快照 49 样本整棵 JSON 逐条 diff = 0（vs `_golden_E14.json`）+ pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0 + 关键字路径新旧对拍 PASS + 零依赖保持 + library/ 布局自检 PASS + AST 全包扫描 13 个（**全为 HEAD 既有**）。**如实边界**：`RuleSource` 协议抽象仍未做；本轮只解决「位置与命名」，未解决「编排随来源走」 |
| 2026-10-26 | **E16** | **`library/` 内部重组 · `policy.py` 消亡、`repository.py` 落地**（详见 §2.23）。起因：承接 E15，用户明确「**编排放 repository，rule 只负责规则部分**」⇒ 终态五文件：**契约** `ports.py` / **rule 资源** `rules.py` / **keyword 资源** `keywords.py` / **资源集合** `repository.py` / **文件来源** `files/`。**改动** = **新建 `library/repository.py`**（181 行，`ResourceRepository` 3 方法：选库 / 收集组装 / 组合 keyword）+ **重写 `library/rules.py`**（259 → 218 行，`RuleQueryService` 2 方法 + `RuleService` 3 方法零 ORM）+ **删除 `library/policy.py`**（149 行，语义并入 `RuleService`）+ `library/keywords.py` / `library/files/*` docstring 同步 + `fuzzy_algorithm.py` 延迟导入改指 + **重写 `library/__init__.py`**（现 37 行）+ **重写 `_chk_library_layout.py`**（新增 `contract` / `resource_set` 两个 role + `_imports_sibling_impl()` + `policy.py` 消亡断言）+ `_verify_zero_dep.py` 的 `_BANNED` 改禁 `library.repository` + `_chk_enc.py` 主线改为扫**已废弃类名**残留 + `_rename_to_routing.py` **硬禁用** + 13 个 dev 脚本/测试改名。**顺手修好 3 处**（`verify_fuzzy_nested_context.py` 3 处 patch 目标失效 / `diag_fuzzy_level_word_crash.py` patch 目标 + classmethod 还原错 / `diag_fuzzy_field_registry_regression.py` 的 `registry` NameError ⇒ **L16 关闭**）。**验收**：黄金快照 49 样本整棵 JSON 逐条 diff = 0（vs `_golden_E15.json`）+ pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0（numeric 10 / advisory 0 / 契约校验通过）+ 关键字路径新旧对拍 PASS（ORM 泄漏 0）+ 零依赖保持 + library/ 布局自检 PASS + AST 全包扫描 13 个（`library/` 下 0 个）+ U+FFFD 扫描 92 文件 0 + 4 个 diag 脚本全部 exit=0。**如实边界**：**编排本身随来源走**（`ResourceRepository` 转手 ORM ⇒ DB 来源特有；文件来源落地需自己的编排，或引入 DTO）⇒ 登记 L20 |
| 2026-10-26 | **E17** | **契约层文件改名 · `library/ports.py` → `library/contracts.py`**（详见 §2.24）。起因：用户问「`library/ports.py` 这个文件命名我觉得不恰当，适合改成什么名称？」。**核查结论**：`port` 是 **DDD 六边形架构**的术语词，全仓（含隔壁 `molding-expert`）**只有它一个** `ports.py`；而本仓库描述「对外承诺什么」的既有词是**「契约」**（`field_contract.py`「入参契约通用机制」/ `input_specs.py`「调优入参契约」/ `fuzzy_core/profiles.py`「内核输入契约层」）⇒ **与仓库词汇统一**。**选定 `contracts.py`**（`protocols.py` 语义更精确但与 `ports` 同义；`specs.py` 被否决 —— 本项目 `*_specs` 专指**对外接口契约**，方向相反）。**改动** = 文件重命名 + **13 处 import 路径**（3 业务 + 1 测试 + 9 dev 脚本）+ **2 个护栏脚本**（`_chk_library_layout.py` 的 `EXPECT` 键名 / `_verify_zero_dep.py` 的 `_LEAKED_TOPLEVEL`）+ **3 处结构表**（`fuzzy/__init__.py` / `library/__init__.py`）+ **16 处 docstring 措辞**（「端口」→「契约」）+ `_chk_enc.py` 旧名扫描清单**新增 `library.ports`**。**踩坑**（如实记录）：① 一次性脚本按「有专属 edits / 只有 import 路径」二选一分支 ⇒ `fuzzy_algorithm.py` 与 `library/repository.py` 的 import 路径**被漏掉**，靠事后残留扫描补齐；② 断言拦下真实重复（`的取用端口 ——` 出现 2 次，脚本按 1 次断言 ⇒ 报错退出未写盘 ⇒ 合并为一条）。**历史事实保留**：`contracts.py` docstring 里的「由 `fuzzy/ports.py` 搬入」与**已硬禁用**的 `_rename_to_routing.py` 里的 `library/ports.py` **一律不改**（记的是当时事实）。**验收**：黄金快照 49 样本整棵 JSON 逐条 diff = 0（vs `_golden_E16.json`）+ pytest 22 passed + sanity 全绿 + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 真实 DB 端到端 exit=0 + 关键字路径新旧对拍 PASS + 零依赖保持 + library/ 布局自检 PASS + AST 全包扫描 13 个（`library/` 下 0 个）+ 6 个 diag 脚本全部 exit=0 |
| 2026-10-26 | **E18** | **`library/` 注释精简**（详见 §2.25）。起因：用户要求「`library` —— 检查一下这个功能模块，将无用的注释全部精简，不需要那么多设计用语」。**先立判定标准再动手**：删分层术语（第 ② 层 / 契约→资源→资源集合）、轮次考古（E2/E7/E15/E17、0005 迁移）、决策辩论（为什么用 Protocol 不用 ABC）、重复 3 次的对照表、护栏脚本已在监控的不变量复述；留每文件「是干什么的」一句话、字段/返回值格式（真契约）、看代码猜不出来的坑、行内短注释。改动 = `library/` 7 文件 **945 → 727 行（净减 218）**。**⭐ 代码零改动的硬校验**：剥离全部 docstring 后逐文件 `ast.dump(..., include_attributes=False)` 比对 ⇒ **7 个全 IDENTICAL** ⇒ 严格证明「只动注释、代码一字未改」。踩坑：① 行号区间记录偏移 2 处 ⇒ **首轮断言拦下、未写盘**（两遍式生效）⇒ 核实真实行号后修正；② EDITS 的 key 已含 `library/` 前缀又与目录常量拼接 ⇒ `FileNotFoundError` ⇒ 改 key。复查补刀 5 处（`rules.py` 两处 `# ====` 分隔条与其余 4 文件的 `# --- 标题 ---` 不一致；`repository.py` 两处措辞去掉「来源无关」「历史实现」；`rule_format.py` 一处措辞精简）。验收：黄金快照 49 样本整棵 JSON 逐条 diff = 0（vs `_golden_E17.json`）+ pytest 22 passed + 零依赖保持 + library/ 布局自检 PASS + 编码扫描 exit=0 + U+FFFD 0 |
| 2026-10-26 | **E19** | **`sanity_check.py` 迁入 pytest 后删除 · 消除 `return bool` 假通过**（详见 §2.26）。起因：用户问「`sanity_check.py` 1-603 这个文件干什么用的？」→「可以移除掉吗？因为其实我们在调整代码结构，这个后续肯定也是要改的」。**删除前先做覆盖缺口分析**（逐条比对 pytest 收集清单 22 个用例）⇒ 6 个 case **完全无等价物**（B3/B4/B7/C1/C2/C3）+ CASE 1/2/3/4 无等价物 + B1/B2/B5 仅弱覆盖（只测 `resolve_bucket` 函数，不验网络实际连桶）+ `test_numtsk_inference_priority` **无反转验证 ⇒ 可能空转**。**⚠️ 它有一个真缺陷**：pytest 只在返回值非 None 时发警告，**返回 False 仍算 passed** ⇒ 断言失败被静默吞掉（实测 **17 个** `PytestReturnNotNoneWarning`）+ `test_fuzzy_rule_net` 把异常吞成 `[SKIP]` 并 `return True`。**迁移**（用户拍板「迁移成 pytest 后删除」+「一起修」）：CASE 1/2/4 + B1~B7 + C1~C3 → `fuzzy_core/tests/test_inference_gates.py`（13 个真 assert）；CASE 3 → `tests/test_fuzzy_aggregation.py`（6 个，**零 Django 依赖** —— 实测 import 后 `django`/`process.models` 未进 `sys.modules`）。**顺带修掉的假通过**：`test_nets.py` / `test_macros.py` 的 `_assert_eq` / `_assert_close` / `_assert_raises` 改 `raise AssertionError`、删 `ok` / `return ok` / `ok &= `、Mamdani 的 `[SKIP]` 改为直接抛、priority 断言**补反转验证** ⇒ **pytest 警告 17 → 0**。**⭐ 端到端证明**：临时探针 `tests/test_tmp_fail_probe.py` 故意让断言失败 ⇒ pytest **1 failed**（改前静默 passed）⇒ 探针用完即删。**删除**：`git rm process/algorithms/fuzzy/sanity_check.py`（603 行，git 追踪）；残留扫描**代码级 import/call = 0**，文字提及仅 `diag_fuzzy_bucket_shift_impact.py` 5 处 ⇒ 已改指新位置。验收：黄金快照 49 样本整棵 JSON 逐条 diff = 0（vs `_golden_E18.json`）+ **pytest 41 passed**（22 + 13 + 6）+ 真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + provided_smoke 6/6 + `verify_fuzzy_nested_context` PASSED + 零依赖保持 + library/ 布局自检 PASS + AST 全包扫描 13 个（**全为 HEAD 既有**）+ diag 脚本 31/31 正常 exit=0 |
| 2026-10-26 | **E20** | **契约归属对齐 · 转换器归位到来源适配层**（详见 §2.27）。起因：用户对照 `fuzzy_core/profiles.py` 提问 ——「`profiles.py` 1-306 这才是标准结构，`keywords.py` 40-62 你转换器不是应该转换到 `KeywordProfile` 吗？`rules.py` 86-171 同理 rule 不是应该也是转换成 `RuleProfile`？」**核查结论**：① 关键字侧转换器**本就**有 `to_keyword_profiles` 出口，真问题是 `to_fuzzy_dict` 这个**裸 dict 中转层**（外部零调用、绕路 `KeywordProfile(**to_fuzzy_dict(kw))`、**丢失 `meta_source`**）；② `rules.py` 86-171 的 `RuleService` 是**规则串语义判定器**（不产出 Profile），真问题在 `library/repository.py` L110-119 —— **编排层越位构造契约**、且规则侧**没有**与 `RuleKeywordAdapter` 对称的转换器；③ 更本质的：**契约未贯穿到内核**（内核仍吃裸 dict ⇒ 契约层是中途站不是终点，见 L21）。**决策**（用户拍板「归属对齐」+「`RuleAdapter` 放 `rules.py`」）：本轮**只做归属，不动内核签名**。改动 = `library/keywords.py`（三个旧出口消亡 → 直接构造 `KeywordProfile` + 补 `meta_source` 透传 + docstring 修正，109 → 96 行）/ **新建 `library/rules.py::RuleAdapter`**（`RuleMethod` → `RuleProfile`，与 `RuleKeywordAdapter` 成对，171 → 209 行）/ `library/repository.py`（编排层不再构造契约，144 → 139 行）。**⭐ 行为等价直接证明**：从备份目录加载**改前**模块，与改后逐字段对拍 **12 案例 0 差异**（唯一有意差异 = dict 输入 `meta_source` 透传）。**连带修好 2 个 dev 脚本**：`_verify_kw_parity.py`（旧基线**冻结进脚本**，与生产代码的历史出口解耦 ⇒ 现 PASS）+ `diag_fuzzy_fix_simulation.py`（改用新接口，并**顺带关闭 E16 遗留 L15** —— `rules` 元组显式携带 priority，6 处解包点对齐 ⇒ exit=1 → exit=0）。验收：黄金快照 49 样本整棵 JSON 逐条 diff = 0（vs `_golden_E19.json`）+ pytest **41 passed**（30 + 11）+ 真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE）+ library/ 布局自检 PASS + compileall exit=0 + diag 脚本 **32/34 exit=0**（余 2 个为「诊断发现问题」的既有行为）。**如实边界**：**内核仍吃裸 dict**（L13 / L21 未关闭），贯穿到内核留待下一轮 |
| 2026-10-26 | **E21** | **跨包命名对齐 · `input_specs.py` → `specs.py`**（详见 §2.28）。起因：用户问「`input_specs.py` 这个文件定义了算法入参，但是我觉得 input_specs 这种命名还是太奇怪了，有什么更合适的？」。**诊断三条**：① **跨包不一致** —— `expert/specs.py` 与 `fuzzy/input_specs.py` 是同一层（对外接口契约）、同类物（字段字典 + 必填等级）、同一套 `field_contract` 机制，docstring 首句几乎一字不差，却两个名字；② **限定词冗余** —— E7-d 给 `specs.py` 加 `input` 前缀是为消歧（当时层 3 还有 `FuzzyKeywordSpec` / `FuzzyRuleSpec` 两类 spec），而层 3 早已改名 `elements.py`（类名 `FuzzyFeature` / `FuzzyRule` / `NumTskRule`）⇒ **fuzzy 包内 spec 词根只剩层 0 一个**，消歧前提消失；③ **`input` 撞义** —— 本包内「input」有两义：层 0 的「对外接口入参」vs 内核 `fuzzy_core/profiles.py` 的「内核输入契约」，后者才真配叫输入契约。**选定 `specs.py`**（用户拍板；备选 `field_specs.py` / `input_contract.py` / `fields.py` 均被否 —— 前者跨包仍不一致，次者同包内两个 `contract` 不同义，末者名不副实因文件还含校验器与词表）。**改动** = 文件重命名（内容一字未改）+ **8 处 import/注释**（`fuzzy/__init__.py` ×3 / `services/parameter_optimize.py` ×2 / `tests/test_optimize_smoke.py` / `tests/verify_demo_machine_fields.py` / `schemas/optimization.py` 注释 / `fuzzy_core/profiles.py` 注释）+ **2 处 dev 脚本**（`_verify_zero_dep.py` 顶层名泄漏清单 / `_verify_e2e_db.py` docstring）+ 执行文档同步。**导出符号零变化**（`__all__` 10 个）⇒ 外部零影响。验收：黄金快照 49 样本整棵 JSON 逐条 diff = 0（vs `_golden_E20.json`）+ pytest **41 passed**（30 + 11）+ 真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE，含新增 `specs` 检查项）+ library/ 布局自检 PASS + compileall exit=0 + 残留扫描（代码级 0 处）。**如实边界**：**结构未对齐** —— `expert` 是 `specs.py` + `data_validator.py` 分文件，`fuzzy` 仍把字典/校验器/词表三者合一（登记 L22，留待下一轮）；`_dev_refs/_rename_to_routing.py` 里的 `input_specs.py` 是**历史改名工具的当时路径**，一律保留不改 |

| 2026-10-26 | **E22** | **双文件改名 · `naming.py` → `field_names.py`、`fuzzy_algorithm.py` → `engine.py`**（详见 §2.29）。起因：用户两条消息 ——①「`naming.py` 这个文件我建议叫 fields 可能更合适一点」②「`fuzzy_algorithm.py` 这个叫 fuzzy_algorithm 不太合适，看看有没有更合适的名称」。**诊断 1**：`naming` 偏泛（该文件只管字段名双向映射）✔ 用户直觉正确；但建议的 `fields.py` 与同包 `specs.py`（E21 刚改名的**字段字典**）**包内撞名** ⇒ 选定 `field_names.py`（保留 `field` 词根 + `names` 限定「名」，与 `specs` 的字段**规格**互补）。**诊断 2**：`fuzzy_algorithm.py` 内是类 `FuzzyEngine` ⇒ **名不副实**；§0「入口改名」一行**早在 E4 执行时就已拍板 `engine.py`**，但一直没执行 ⇒ 本轮落地。**⚠️ 如实记录代价**：4 个算法包入口命名本就是 3+1 分裂（`fuzzy_algorithm` / `llm_algorithm` / `empirical_algorithm` / `expert.algorithm_engine`），改 fuzzy 后它成为**唯一不用 `*_algorithm.py` 的包** —— 判断 llm 那个「文件说 algorithm、类说 Engine」本身不自洽、fuzzy 改后**文件↔类严格对应**故净收益为正，但**全仓统一与否另行拍板**（登记 L4 / L23）。**改动** = 3 个文件重命名（`field_names.py` 353 行 BOM=False / `engine.py` 588 行 BOM=True / `_verify_naming_forward_parity.py` → `_verify_field_names_forward_parity.py`）+ `naming` **72 处** + `fuzzy_algorithm` **44 处**引用同步（30 个文件；字节级操作，**BOM / 行尾 / 编码零变化**）+ `fuzzy/__init__.py` 命名约定补两条。**⭐ 最强等价证明**：用备份还原「改前」**完整 backend 副本**，**同一生成器脚本**分别跑改前 / 改后 ⇒ 整棵 JSON **逐条 diff = 0**（两份均 221409 字节），且与 `_golden_E21.json` 的 `details` 逐条相等（49 样本）。**预存失败已隔离**：全量 pytest 的 77 个 expert 失败经**基线对照实验**证明改前同样 77 failed（栈全在 `expert/data_validator.py`）⇒ 与本轮无关。验收：pytest **41 passed**（30 + 11）+ 真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 字段名对拍主口径 84 字段逐键差异 0（副口径 36 处差异**全在边界输入段**、真实入参与往返闭合均 0 差异，详见 §2.29） + 关键字对拍 PASS + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE）+ library/ 布局自检 PASS + compileall exit=0 + 残留扫描代码级 0 处。**如实边界**：`llm` / `empirical` / `rule_miner` 三个包的入口文件名**未动**（本轮只授权改 fuzzy）；`fuzzy/specs.py` 仍把「字典 + 校验器 + 词表」三样合一（L22 未关闭） |

| 2026-10-26 | **E23** | **推荐结果层改名 · `aggregation.py` → `recommendations.py`**（详见 §2.30）。起因：用户消息 ——「`aggregation.py` 这个文件命名也有点问题，这个应该是推理完成后算法格式化输出结果，叫 aggregation 有点问题」。**模块实际职责**（读全文核实）：`aggregate()`（同参数多规则调整量归并：数值层裸累加 / 提示层跨层覆盖 / 文本建议分流，**带业务策略**）+ `to_recommendations()`（→ `AlgorithmRecommendation`，算 `recommended_value` / `confidence` / `direction`，**格式化输出**）+ 两个中间态 dataclass。**诊断**：现名 `aggregation` 只覆盖「归并」半边，**完全没体现「产出对外推荐契约」这半** —— 而 `engine.py` 正是把它当出口用 ⇒ 读者只知它「把同参数合并」，不知它就是产出推荐结果的那层；用户「格式化输出」的描述命中了 `to_recommendations()`，但未覆盖带策略的归并半边。**选定 `recommendations.py`**（用户拍板）：命名锚点用「**这层产出什么**」而非「它做了什么动作」—— 出口就是 `AlgorithmRecommendation[]`，与 `base.AlgorithmRecommendation` / `to_recommendations()` / service 层 `all_recommendations` 四者词根统一；复数风格与 `specs.py` / `contracts.py` / `profiles.py` 一致；候选 `output.py`（泛、`output` 在 Python 生态偏输出流）/ `formatter.py`（丢掉归并语义）/ `presenter.py`（无 DDD 先例）/ `advice.py`（❌ 与模块内 `advice` 子概念撞名）均未采用。**改动** = 2 个文件重命名（`recommendations.py` 224 行 BOM=False / `test_fuzzy_recommendations.py` 151 行 BOM=False）+ `\baggregation\b` **9 处**引用同步（5 个文件；**不命中** `aggregate()` / `AggregatedAdjustment` / `aggregated`）+ 3 处手工润色；**公开符号零变化** ⇒ 外部零影响。**⭐ 双重等价证明**：① 基线对照实验（改前完整副本 + 同脚本对跑）逐条 diff = **0**（两份均 221409 字节，且与 `_golden_E22.json` 的 details 逐条相等）；② **逐行 diff**（改后 vs 改前备份）⇒ `recommendations.py` **仅 docstring 首句 1 行不同**（224 → 224 行），6 个受影响文件共 22 行差异且逐条可解释 ⇒ **零逻辑改动**。验收：pytest **41 passed**（30 + 11）+ 真实 DB 端到端 exit=0（numeric 10 / advisory 0）+ 字段名对拍主口径 84 字段逐键差异 0 + 离线验证 8 PASS/0 FAIL + 零依赖保持（顶层名泄漏 NONE）+ library/ 布局自检 PASS + compileall exit=0 + 残留扫描代码级 0 处。**如实边界**：⚠️ 仓库现存在**两个「recommendation」词根模块** —— `fuzzy/recommendations.py`（算法层产出）与 `process/models/recommendation.py`（ORM 模型）；E6 曾为消解同名冲突把算法层 `Recommendation` 改名 `AlgorithmRecommendation`，本次是**模块名**层面、不同目录不冲突（登记 **L24**，低优先级不动）；`fuzzy/specs.py` 仍把「字典 + 校验器 + 词表」三样合一（L22 未关闭）；`llm` / `empirical` / `rule_miner` 三个包的入口文件名仍未动（L4 / L23 未关闭） |

| 2026-10-26 | **E24** | **内核论域实例与隶属度类型层清理**（详见 §2.31）。起因：用户消息 ——「`features.py` 1-92 这个我那件我觉得需要改造一下，你觉得呢？」。**这是 E9 拆出 `models/features.py` 后第一次回头审内核自身的类**（此前只搬移、未审）。诊断出四类问题：① `functional.py` L246-357 的**迁移粘贴事故** —— 5 组隶属度函数同名实现前后段覆盖，后写覆盖先写 ⇒ 前半段从未执行过；且重复段是**另一套实现**（纯数组版，丢了 `a<=b<=c` 断言）② `features.py` 4 个实例属性**只写不读**（生产代码零读取点）+ 死方法 `get_all_value()`（全仓零调用）+ `f_name` / `f_type` 两个**从未被读取的参数**（假契约）③ `macros.MEMBERSHIP_TYPES` **定义了零使用**，声明 `['gauss','tri','trap']` 与实现对不上（`tri` 是零调用的死分支、`trap` 从未实现）④ 桶中心**内联**在 `features.py`，与 `LEVEL_WORDS_BY_LVL` 的对应关系只写在注释里 ⇒ 7/9 档**零断言覆盖**。**分 4 批做、每批独立验收**（用户拍板「按 1→2→3 全做，每批验收」）：**E24-1** 删重复段（356 → 245 行；`triangular_mf` / `trapezoidal_mf` 的 scalar / list 从 `TypeError` 修复为正常值）→ **E24-2** `features.py` 瘦身（91 → 90 行；`nets.py` 3 处构造同步）→ **E24-5** 删 tri 分支 + `MEMBERSHIP_TYPES` 收紧为元组 `('gauss',)` 并由 `features.py` 消费（90 → 82 行）→ **E24-6** 桶中心抽 `macros.bucket_centers()` 纯函数 + 补 3/5/7/9 档直接断言（`macros.py` 236 → 275 行；`features.py` 82 → 78 行；pytest 30 → **32**）。**⭐ 等价证明**：全部 4 批都用**「改前完整 backend 副本 + 同一快照生成器对跑」**⇒ 整棵 JSON 逐条 diff = **0**；`features.py` 那批另做**三方对拍**（改前 / 改后 / 上轮留存基线 JSON，两两 diff = 0）+ **符号面 4 条断言**（签名收缩 / 死方法移除 / 只写不读属性 4 → 0 / 每个保留属性都有读取方）；E24-5 另做**行为面对拍**，差异**恰 2 项**且都是「tri 可用 → 明确拒绝」（唯一有意行为变化，已逐条列明）；全仓 AST 扫 `FuzzyFeature` 构造点 = 4 个、全是 gauss。**踩坑（如实记录）**：① Grep 结果有 **25 条上限**，两次因此漏掉调用点（`test_nets.py` 的位置参数 `FuzzyFeature('inj_pres_1', ...)` ⇒ pytest 报 `TypeError: got multiple values for argument 'f_membership_type'`）⇒ 改用**限定目录重搜 + AST 探针脚本**兜底 ② 验收口径缺口：之前只跑 `fuzzy_core/tests`，漏了 `backend/tests/` ⇒ 此后每批验收都跑两处 ③ E24-6 的 **7 档期望值写错**（我写 `q(1/3)`，实际桶 1 = `q(1/6)` = 200/6）⇒ 被新断言**当场拦下**（pytest 1 failed）⇒ 证明断言真在起作用，改对后 32 passed。**如实边界**：① `functional.py` 仍**无 `__all__`** ⇒ `from .functional import *` 仍会泄漏 `np` / `Union` / `centroid` 等到 `fuzzy_core` 顶层（登记 L5 后半，**未处理**）② `tri_mf` / `trap_mf` / `bell_mf` / `singleton_mf` / `gaussian_mf` 现在**全仓零外部调用点**，但**本轮刻意不删**（`trap_mf` 内部依赖 `tri_mf`；它们是 `functional.py` 的公开 API）⇒ 登记 L25 ③ 内核 net 仍吃裸 dict（L13 / L21 未关闭） |

| 2026-10-26 | **E25** | **隶属度函数层重组 · 统一签名 + 9 形状族**（详见 §2.32）。起因：用户四条消息 ——「首先我们讨论这部分是干什么的」→「文件命名是否正确？……我觉得应该叫 functions，你觉得呢？」→「**可以留在这里**，另外，对于实际应用中，一般有哪些隶属度函数？这才是关键问题，目前**不能因为我们只用了 gauss_mf 而不考虑别的**」→「解模糊是否应该放在这里？如果不放在这里，那么 functional 应该改名成 **memberships**」+ 拍板「**1. 走统一签名 2. 可以正名**」。**诊断**：① `functional.py` 名不副实（装的是隶属度函数）② **解模糊不该同处**（推理阶段不同 / 输入范式不同 / 扩展节奏不同，且 0/1 阶 T-S 根本不需要）③ 用户提的「按推理类型分节」是**错的分类轴**（推理代数 vs 仓库既有的结论形态轴；隶属度是横跨三类的公共模糊化层）④ 族不完备（只按当前调用点算完备性是错的 ⇒ 按**领域词汇覆盖**补齐）。**改动**：`functional.py` → **`memberships.py`**（9 形状 + `MembershipSpec` + `MEMBERSHIP_SPECS` 分派表 + `__all__`）+ **`defuzz.py`**（`centroid` + `defuzz` + `__all__`）；**统一签名 `mf(x, center, width, shape=None)`**（width = 总跨度）；**正名**（老 `bell_mf` 实为代数型 ⇒ 改 `algebraic_bell_mf`，exp 型另起 `bell_mf`）；`macros.MEMBERSHIP_TYPES` 改**由分派表派生** + 新增 `DEFAULT_MEMBERSHIP_TYPE`（`nets.py` 3 处硬编码改常量）；`features.py` 改分派（`membership_shape` 取自分派表 ⇒ 形状参数单一真源）+ 退化/倒挂论域 warning。**⭐ 数值零变化**：高斯 **p=2 逐位相等**（口径锚定老 fuzzykit 的 `exp(-(x-μ)²/(2σ²))`，**不**用教材的 `exp(-|z|^p)` —— 两者差一个 2 因子）；`σ = 论域宽/(2*(lvl-1))` = 相邻桶间距/2 ⇒ `width = 2σ` 精确还原 ⇒ `FuzzyFeature` 端到端 4 种论域（正序/负区间/倒挂/退化）逐点差异 **0**。**踩坑（如实记录）**：① **模块与函数同名遮蔽**（`from .defuzz import *` 把函数绑到包顶层、覆盖同名子模块 ⇒ 对拍脚本 `AttributeError`）② **高斯的 2 因子陷阱**（照抄教材口径会静默改变 μ 值）③ **标量 vs 数组的除零语义不同**（Python float 除零抛 `ZeroDivisionError`，numpy 标量除零给 `inf`/`nan` ⇒ 新实现把标量转 Python float 会让退化论域**从「静默 nan」变成「内核崩溃」**，实测退化论域差异 153 处 ⇒ 标量统一转 `np.float64`）④ **上游论域可能倒挂/退化**（`engine.py` 推测论域 `max_val = 当前值*2` ⇒ 当前值为负则区间倒挂 ⇒ 改前 σ 带符号硬抗，改后 `width` 为负会被拦 ⇒ 在 `features.py` 层把跨度取绝对值，对高斯逐位等价）。**修掉 3 个真 bug**：老 `bell_mf` 缺 `|·|` 算出 **>1** 的隶属度 / 老 `singleton_mf` 对 list 输入结果全 0 / `assert` 当校验（`python -O` 下失效）⇒ 改 `ValueError`。验收：**五档对拍逐点零差异**（严格档 21 组 + 参数化重述档 17 组 + 有意行为变化档 5 项 + 手算参照系 12 项 + 端到端 4 论域 × 2 档 × 51 点）+ pytest **43 passed**（32 + 11）+ 零依赖保持 + library/ 布局自检 PASS + compileall exit=0。**如实边界**：① 非高斯形状**未接线到生产**（L25）② 推测论域的倒挂/退化**未在上游修**（L26）③ 形状选择策略缺失（L27）④ 内核 net 仍吃裸 dict（L13 / L21 未关闭） |


