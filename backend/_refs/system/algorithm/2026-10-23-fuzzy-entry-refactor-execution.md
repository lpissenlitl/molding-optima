# 模糊推理入口重构 · 执行记录

> **日期**：2026-10-23
> **来源**：用户第 16~18 轮对 `backend/process/algorithms/fuzzy/fuzzy_algorithm.py`（686 行）结构的质疑
> **状态**：**E1 + E2 + E3 已完成** —— 命名对照表见 §3；故障边界落地见 §2.5；中间态与聚合层见 §2.7；验收见 §5
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
| **本轮产出** | **§3 命名对照表**（E1-b）＋ **§2.7 中间态与聚合层**（E3） |
| **轮次划分** | E1 命名契约 → E2 故障边界+去 DB 依赖 → E3 中间态类型化+拆聚合 → E4 抽字段上下文+瘦身+改名 |
| **入口改名** | `fuzzy_algorithm.py` → **`engine.py`**（候选已提出，E4 执行时最终确认；类名 `FuzzyEngine` 不动） |
| **不做** | 不动 `llm` / `empirical` / `expert` 三个算法包；不动算法语义（激活度公式、聚合公式、阈值） |
| **不做** | 不新写测试框架/测试文件；只复用现成 `sanity_check.py` / `fuzzy_core/tests` / `backend/tests` / 黄金快照脚本 |

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
`FuzzyEngine._merge_layer_results` 里，与「Recommendation 契约转换」混在一起：

```python
{'source': 'numeric', 'param': 'IV0', 'delta': 1.2, 'activation': 0.9, 'rule': '...'}
```

**改后**：

```
RuleAdjustment（逐条） ── aggregate() ──► AggregatedAdjustment（参数级） ── to_recommendations() ──► Recommendation[]
```

| 层 | 位置 | 职责 | 依赖 |
|---|---|---|---|
| 中间态类型 | `aggregation.py` | `RuleAdjustment` / `AggregatedAdjustment` 两个 dataclass | 无 |
| 聚合 | `aggregation.py` | `aggregate()`：同参数累加 + 跨层覆盖 + 分离文本建议 | 无 |
| 契约转换 | `aggregation.py` | `to_recommendations()`：算 delta / confidence / direction | `base.Recommendation` |
| 编排 | `fuzzy_algorithm.py` | 只负责“调一下” | `aggregation` |

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
旧复刻版只测到 merged dict，没测到 Recommendation）。

### 2.3 引用点全景（改名成本评估，2026-10-23 实测）

| 引用点 | 形式 | 性质 |
|---|---|---|
| `process/algorithms/__init__.py` L29 | `from .fuzzy import fuzzy_algorithm` | 仅触发 `register` |
| `process/algorithms/fuzzy/__init__.py` L12 | `from .fuzzy_algorithm import FuzzyEngine` | 包级导出 |
| `process/services/parameter_optimize.py` L36 / L68 | `from process.algorithms.fuzzy import FuzzyEngine` | ✅ 走包级导出 |
| `process/services/parameter_optimize.py` L245 | `FuzzyEngine.to_business_name(...)` | 类方法引用 |
| `process/services/parameter_optimize.py` L534-536 | `FuzzyEngine.FIELD_NAME_ALIAS` 等 3 张表 | 类属性引用 |
| `process/services/condition.py` | 仅注释中出现 `FuzzyEngine` 字样 | 无 import |
| `_dev_refs/diag_fuzzy_bucket_shift_impact.py` L56 | `from ...fuzzy.fuzzy_algorithm import FuzzyEngine` | 开发脚本 |
| `_dev_refs/diag_fuzzy_rule_journey.py` L467 | 同上 | 开发脚本 |
| `_dev_refs/diag_fuzzy_level_word_crash.py` L42 | 同上 | 开发脚本 |
| 注释引用 × 6 | `nets.py` L6/L17、`specs.py` L21/L370、`sanity_check.py` L134 | 文档字符串 |

**关键事实**：**生产代码中零处 import 模块路径 `...fuzzy.fuzzy_algorithm`**，全部走包级导出。
⇒ 改名的全部成本 = **1 处生产 import + 3 处 dev_refs + 6 处注释 = 10 处**，其中生产路径只有 1 行。
⇒ **包级导出 `from process.algorithms.fuzzy import FuzzyEngine` 保持不变 ⇒ 外部调用方零影响。**

### 2.4 命名问题现状 —— 10 类

见 §3.3 台账（N1~N12）。

---

## 3. 命名对照表（E1-b 交付物）★

### 3.1 三套命名空间（必须先分清，这是最易出错的地方）

| 命名空间 | 示例 | 谁产出 | 谁消费 | 转换点 |
|---|---|---|---|---|
| **业务字段名** | `inj_spd_1`、`brl_temp_3`、`noz_temp` | 前端 / DB | `parameter_optimize` 层 | `naming.py` 翻译 |
| **算法字段名** | `IV0`、`BT3`、`NT` | `naming.py` 翻译后 | **模糊推理内部全部** | `to_business_name()` 反向出口 |
| **规则库缺陷码** | `SHORTSHOT`、`FLASH` | 反馈 `keyword_name` | 规则查询 `defect_code` | 直接对应 |

**规则（写死，不可违反）**：

1. `context['process_parameter']` **进入 `recommend()` 后已经是算法命名空间**
   （由 `parameter_optimize._normalize_field_name_by_spec` 翻译完成）。
   ⇒ 算法内部一律使用算法名，**禁止**在算法层出现业务名。
2. `to_business_name()` 是**唯一的反向出口**，只允许编排层调用。
3. 业务名 ↔ 算法名的映射表**只有一份**（`FIELD_NAME_ALIAS` / `FIELD_INDEX_OFFSET` / `FAMILY_FIELD_ALIAS`），
   双向共用，禁止出现第二份硬编码映射。

> ⚠️ 现状风险点：`specs.py` L14 已明确写「工艺参数走的是**另一套**命名空间」，但这条规则**只写在注释里**，
> 代码里没有任何机制保证混用会被发现。E3 抽 `naming.py` 时要把这条规则变成可执行的约束。

### 3.2 术语总表

| 概念（中文） | 当前代码标识 | 目标标识 | 所在层 | 说明 |
|---|---|---|---|---|
| 模糊推理引擎 | `FuzzyEngine` | **不变** | 编排层 | 包级导出唯一符号 |
| 业务→算法字段名映射 | `FIELD_NAME_ALIAS` | → `naming.py` | 契约层 | 33 条 |
| 段号偏移（1-based→0-based） | `FIELD_INDEX_OFFSET` | → `naming.py` | 契约层 | 10 条 |
| 整段族映射 | `FAMILY_FIELD_ALIAS` | → `naming.py` | 契约层 | 1 条（`brl_temp`→`BT`） |
| 算法→业务字段名 | `to_business_name()` | → `naming.py` | 契约层 | 唯一反向出口 |
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

### 3.3 同名不同义 / 语义冲突台账

| # | 冲突描述 | 位置 | 处置 | 执行轮次 |
|---|---|---|---|---|
| **N1** | **`'source'` 一词两义**：元数据来源（`'guessed'`）vs 推理层（`'numeric'`）；两个 dict **会一起传进** `net.predict()` | `adapters` 产出 / `fuzzy_algorithm.py` L402 / L487 / L534 | 元数据侧 → `meta_source`；结果侧 → `layer` | **E3** ✅ 已修 |
| **N2** | **同一东西三个名字**：`rec['param']` / `Recommendation.param_name` / `to_dict()` 输出 key `'param'` | L599 / base.py dataclass | 中间态与 dataclass 统一 `param_name`；**`to_dict()` 保持 `'param'`**（对外契约，不动） | **E3** ✅ 已修 |
| **N3** | **等级两种叫法**：`lvl`（适配层 dict）/ `f_level`（`FuzzyFeature`）；且 `'level'` 又指档位词（`'low'`） | `keyword_dicts` / `nets.py` L110 | 统一 `level_count`；`level` 保留给档位词 | ⛔ **不做**（`'lvl'` 是内核输入契约 key，改名必动内核，见 §6 L9） |
| **N4** | **`'delta'` 中间态有、最终态无**（被折进 `recommended_value`） | L489 / L642 | 中间态保留 `delta`；`to_recommendations()` 显式写明 `recommended = current + delta * factor` | **E3** ✅ 已修 |
| **N5** | **`layer` 三义**：结论形态（推理）/ 结论形态（`_build_field_context` 参数）/ 规则库层级（`RuleQueryService` docstring） | `rule_query_service.py` L172 / L258 / L289 | 规则库层级一律改称「**特异级**」；结论形态保留 `layer` | **E1** ✅ 已修 |
| **N6** | **文档与实现矛盾**：docstring 与注释写「三级特异性匹配」，实现是 L1~L4 **四级** | `rule_query_service.py` L172 / L187 | 改为「四级」 | **E1** ✅ 已修 |
| **N7** | **`'rule'` 字段在 advisory 路径被硬编码为 `'advisory'`**（不是规则标识） | L565 | 改为 `rule_str`（真实串）或 `None` | **E3** ✅ 已修 |
| **N8** | **`extra` 接了从未使用** —— ⚠️ **原判断有误**：它不是「诊断通道」，而是**弹窗文本通道**（`nets.py` L721/L825 收集 `r_extra` 并回传），不能往里塞诊断信息 | L477 / L554 | 诊断信息另起通道：`self._diagnostics`（编排层自建） | **E2** ✅ 已修 |
| **N9** | **`RuleMethodAdapter` import 了从未使用**，名字却像主适配器（实际在用的是 `RuleKeywordAdapter`） | L21 | 删除 import | **E1** ✅ 已修 |
| **N10** | **`self._rule_net` 从未使用**，注释却描述「工厂级网络和兜底层网络」 | L192-194 | 删除属性；注释改写为「无状态」 | **E1** ✅ 已修 |
| **N11** | **注释引用了不存在的文件名** `fuzzy_engine.py`（实际是 `fuzzy_algorithm.py`） | `sanity_check.py` L134 | 随 E4 改名一并修正 | **E4**（待） |
| **N12** | **`load_rules()` 兼容占位**（`pass`），长得像正经 API | L678-681 | **待定**（见 §3.4） | **E4**（待） |
| **N13** | **文档引用路径不完整**：代码里写 `fuzzy-engine-reference.md`，实际在 `_refs/system/ai/` 下 | `fuzzy_algorithm.py` L6/L199、`rule_query_service.py` L6、`adapters.py` L26 | 补全目录前缀（文件存在，非失效链接） | **E4**（待） |
| **N14** | **`ParticularRules` import 了从未使用**（AST 审计：生产侧零引用） | `fuzzy_algorithm.py` L25 | 删除 import | **E1** ✅ 已修 |
| **N15** | **`'level'` 一词两义**：前件里的**档位词**（`'low'`）vs 结论里的**数值**（`2` / `'30%'`）—— `NumTskRule._rule_process` 把结论值存进了 `'level'` key | `nets.py` L505 vs L486 | 结论值改存 `'value'`（内核改动，需同步 `nets.py` 结论层与 `solution_matrix` 构造） | **E4**（待，属内核） |

### 3.4 待定项（需在对应轮次前拍板）

| # | 待定内容 | 候选 | 建议 | 拍板时机 |
|---|---|---|---|---|
| **P1** | **入口文件名** | `engine.py`（推荐）/ `fuzzy_engine.py` / 不改 | `engine.py` | E4 前 |
| **P2** | `load_rules()` 是否删除 | 删 / 保留 | **保留**（public API，外部可能有未知调用方；改为明确抛 `NotImplementedError` 而非 `pass`） | E4 前 |
| **P3** | `llm/llm_algorithm.py`、`empirical/empirical_algorithm.py` 同类冗余 | 一并改 / 只改 fuzzy | **只改 fuzzy**，另两个记入 §6 遗留 | 已定（本次不动） |
| **P4** | `to_business_name()` 的归属 | 留 `FuzzyEngine` 类方法 / 移到 `naming.py` | 移到 `naming.py`，`FuzzyEngine` 保留**兼容类属性别名**（`parameter_optimize.py` L245/L534 零改动） | E4 前 |

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
| **E4** | 抽字段上下文 + 瘦身 + 改名 | ① 抽 `field_context.py` ② 命名契约 → `naming.py`（P4 兼容别名）③ 入口改名 `engine.py`（P1）④ 删 `load_rules` 或改抛（P2）⑤ 修 N11 注释 | **无** | 同上 + 全量 import 点复查 |

**每轮的通用验收（不新写脚本，只跑现成）**：

```
# 1) 黄金快照（现成脚本，需先加一个只读比对模式）
..\.venv\Scripts\python.exe _dev_refs\diag_fuzzy_bucket_before_after.py --json _dev_refs\_golden_after.json
#    ⇒ 与 _golden_before.json 逐条 diff，after 段必须完全为空

# 2) 现成 sanity check
..\.venv\Scripts\python.exe process\algorithms\fuzzy\sanity_check.py

# 3) 现成 pytest
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
| E4 | | | | | |

---

## 6. 遗留问题台账

| # | 问题 | 来源 | 状态 |
|---|---|---|---|
| L1 | 聚合公式语义（`confidence` = 平均激活度）是否合理 | E1 讨论 | 待评估（属算法语义，本轮不动） |
| L2 | 激活度阈值 `MIN_ACTIVATION_THRESHOLD` 需按规则数标定 | 上一轮 D+B 遗留 | 待定（需业务标定） |
| L3 | 规则库重复项（同名规则多条命中）需去重口径 | 上一轮遗留 | 待定 |
| L4 | `llm/llm_algorithm.py` / `empirical/empirical_algorithm.py` 目录名冗余 | P3 | 待定（本次不动） |
| L5 | `functional.py` 两套实现同名覆盖（后半段覆盖前半段） | AST 审计 | 待定（属内核清理，不在入口范围） |
| L6 | `nets.py` L692/L717 矩阵越界只记日志 | §2.2 | 待定（属内核清理） |
| L7 | 文档引用路径不完整（`fuzzy-engine-reference.md` 未写目录） | N13 | 待定（E4 随改名一并修） |
| L8 | ~~`import process.algorithms.fuzzy.fuzzy_algorithm` 仍需 Django setup（父包 `process/algorithms/__init__.py` 会 import 全部引擎触发注册）⇒ 目前是「调用可离线」而非「导入可离线」~~ | §2.6 | ✅ **已关闭**（E3 实测：E2 去 ORM 依赖后，导入与调用均可离线） |
| L9 | 等级两种叫法（`lvl` / `f_level`）未统一为 `level_count` | N3 / §2.7 | 待定（`'lvl'` 是内核 `nets.py` 的输入契约 key，改名必动内核；与「内核不动」边界冲突） |

---

## 7. 变更记录

| 日期 | 轮次 | 变更 |
|---|---|---|
| 2026-10-23 | E1-b | 新建本文档；产出 §3 命名对照表（术语总表 22 项 + 冲突台账 N1~N14 + 待定项 P1~P4）；完成引用点全景调研（§2.3） |
| 2026-10-23 | E1 | 代码侧零风险修正：`rule_query_service.py` 8 处 docstring（「三级」→「四级」N6、规则库层级→组织维度 N5、过期术语「工厂级/兜底层」→`NumTskRuleNet`/`FuzzyRuleNet`）；`fuzzy_algorithm.py` 删死 import（`RuleMethodAdapter` N9 / `ParticularRules` N14）+ 删死属性 `self._rule_net`（N10）。验收：sanity 全绿 + pytest 17/5 + 黄金快照 49 样本 diffs=0。新增存档 `_dev_refs/_golden_E1.json` |
| 2026-10-23 | E2 | **故障边界 + 去 DB 依赖**（详见 §2.5 / §2.6）。新增 `ports.py`（`RuleRepository` 协议 + 数据类搬迁，零 ORM 依赖）；`rule_query_service.py` 改为从 ports 导入并新增 `get_keywords_by_names`；`fuzzy_algorithm.py` 支持 `FuzzyEngine(repository=...)` 注入（默认实现延迟导入）、`recommend()` 拆为兜底壳 + `_recommend()` 主流程、规则查询异常单独捕获（error 级）、新增 `_precheck_numeric_rules()` 条目级预检与 `self._diagnostics`。修正 N8 判断错误（`extra` 是弹窗文本通道）；新增 N15（`'level'` 一词两义）。验收：黄金快照 49 样本 diffs=0 + sanity 全绿 + pytest 17/5 + 离线验证 7 项 PASS。新增 `_dev_refs/_verify_e2_offline.py`（可复用的离线回归工具）与 `_dev_refs/_golden_E2.json` |
| 2026-10-23 | E3 | **中间态类型化 + 拆聚合**（详见 §2.7）。新增 `aggregation.py`（224 行）：`RuleAdjustment` / `AggregatedAdjustment` 两个 dataclass + `aggregate()` + `to_recommendations()`。`fuzzy_algorithm.py` 776 → 697 行：中间态裸 dict → dataclass（`'param'`→`param_name`、`'source'`→`layer` / `meta_source`），删除 `_merge_layer_results`（95 行，混聚合+契约两事），`_recommend()` 第 5 步改为调 `aggregate()` + `to_recommendations()`。落地 N1/N2/N4/N7；**N3 排除**（`'lvl'` 是内核输入契约 key，见 §6 L9）。修正 advisory 路径硬编码的 `'rule': 'advisory'` → `rule_str=None`。`sanity_check.py` CASE 3 从**复刻品**改为**直接测真函数**（复刻品已漂移：漏了「文本建议分离」规则），并补上文本建议用例与 `to_recommendations()` 公式/对外字符串断言；`backend/tests/test_fuzzy_field_report.py` 随 `'source'`→`'meta_source'` 同步。实测纠正 §2.6：导入已可离线（原写「仍需 Django setup」是 E2 时的推测，未实测）。验收：黄金快照 49 样本 diffs=0 + sanity 全绿 + pytest 17/5 + 离线验证 7 项 PASS。新增存档 `_dev_refs/_golden_E3.json` |
