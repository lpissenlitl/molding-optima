# 模糊推理 —— 业务案例数据集（离线可复现）

## 为什么有这个东西

分析模糊推理的推荐逻辑时，每次都要连生产库把「真实上下文 + 规则 + 论域元数据」
捞出来跑一遍，才能看清一条建议是怎么从几百条规则里算出来的。
这套东西很容易写完就丢，下次再问同样的问题又要重来一遍。

本目录把**一个真实业务案例**固化成自持的 JSON 数据 + 一个离线 runner：
不连数据库就能重跑同一次推理，逐位复现线上的输出。

## 目录

```
examples/
├── README.md                    ← 本文件
├── export_case.py               ← 数据导出工具（开发期，**需要连库**）
├── run_demo.py                  ← 离线 runner（**不连库**）
└── cases/
    └── fuzzy_shortshot_low.json ← 案例数据（自持）
```

## 怎么跑

```bash
cd backend

# 跑全部案例（默认就带比对；退出码非 0 = 与期望输出有偏差）
..\.venv\Scripts\python.exe process\algorithms\fuzzy\examples\run_demo.py

# 只跑指定案例
..\.venv\Scripts\python.exe process\algorithms\fuzzy\examples\run_demo.py fuzzy_shortshot_low

# 列出全部案例
..\.venv\Scripts\python.exe process\algorithms\fuzzy\examples\run_demo.py --list

# 按当前输出重刷期望值（改了规则 / 论域元数据后用；会就地改写案例 JSON）
..\.venv\Scripts\python.exe process\algorithms\fuzzy\examples\run_demo.py --refresh-expected
```

输出形如：

```
参数     业务名                          当前值           推荐值       置信度  方向
--------------------------------------------------------------------------
PV0    hold_spd_1                   24.0 26.028486139161025   0.475092  increase
IT     inj_t                         4.0 4.507121534790256   0.475092  increase
IV0    inj_spd_1                    30.0 32.18242552380636   0.074187  increase
PP0    hold_pres_1                  44.0 46.300524812590155   0.045033  increase
MBP0   met_back_pres_1               5.0 6.16369649146612   0.041337  increase

[PASS] fuzzy_shortshot_low —— 与期望输出完全一致
（自证）全程 0 次 SQL 执行 —— 确认未访问数据库
```

### 「不连库」是可证的，不是说说

`run_demo.py` 在启动后把 `CursorWrapper.execute` 换成会抛异常的版本 ——
链路上只要出现一次 SQL 就立刻炸（而不是悄悄连上去）。
每次运行末尾会打印 `全程 0 次 SQL 执行`。

### 比对口径

- 按 `param_name` 配对，**不依赖输出顺序**（顺序是呈现细节，值与置信度才是行为契约）
- 浮点用 `repr` **逐位**比，不用容差 —— 避免 `==` 的容差掩盖真实漂移
- 比对字段：`current_value` / `recommended_value` / `confidence` / `direction` / `source`

## 案例数据格式

```jsonc
{
  "case_id": "fuzzy_shortshot_low",
  "title": "...",
  "description": "...",
  "source": {                       // 数据出处（便于回溯与重新导出）
    "tuning_record_id": 44,
    "baseline_process_parameter_id": 149,
    "captured_at": "2026-10-28T11:36:17.976334",
    "note": "由 export_case.py 从生产库导出"
  },
  "context": {                      // ★ 输入（业务字段名，与 HTTP 接口同构）
    "feedback":      {"defect": [{"keyword_name": "SHORTSHOT", "level": "low", "position": "DLSHORTSHOT1"}]},
    "process_parameter": {"inj_spd_1": 30.0, "inj_t": 4.0, ...},   // 业务字段名
    "polymer_info":  {"abbreviation": "PP", ...},
    "mold_info":     {"product_category": "酒瓶", ...},
    "machine_info":  {"max_set_injection_speed": 80.0, ...}        // 论域裁剪依据
  },
  "rules": [                        // ★ 规则池（RuleProfile 字段）
    {"rule_description": "IF SHORTSHOT_low AND IV0_low THEN IV0_add_2",
     "priority": 1.0, "conclusion_kind": "numeric", "specificity": 4,
     "source_ref": "RuleMethod:123"}
  ],
  "keywords": [                     // ★ 论域元数据（RuleKeyword 原始形态）
    {"keyword_name": "IV0", "fuzzy_level": 5,
     "range_min": 0.0, "range_max": 120.0, "step": 30.0, "description": "..."}
  ],
  "expected": {                     // ★ 期望输出（回归基线）
    "recommendations": [
      {"param_name": "IV0", "business_param_name": "inj_spd_1",
       "current_value": 30.0, "recommended_value": 32.053805467920334,
       "confidence": 0.23324155162492485,
       "direction": "increase", "source": "fuzzy.numeric"}
    ]
  }
}
```

### 三个刻意为之的设计

1. **存数据源原始形态，不存中间态**
   `rules` 存 `RuleProfile` 字段、`keywords` 存 `RuleKeyword` 原始元数据，
   **不存**「裁剪后的论域」—— 论域上界按设备实测值裁剪这一步发生在**引擎里**，
   离线复现时走同一条路径，否则就是「拿裁剪结果喂回去」，与线上不同源。

2. **复用生产适配器，口径零重复**
   `keywords` → `KeywordProfile` 走生产的 `RuleKeywordAdapter`（含 `step` 为空时
   `span/3` 的推导逻辑）；业务名 → 算法名走生产的 `field_names.to_algo_params`。
   案例目录里**没有**第二份口径。

3. **数据源可替换**
   `run_demo.py` 里的 `CaseRepository` 实现 `AlgorithmResourceRepository` 协议 ——
   引擎本来就支持注入数据源，离线只是换了个实现（`tests/_verify_e2_offline.py`
   里已有同款先例）。

## 怎么更新 / 新增案例

### A. 只改了规则 / 论域元数据（**不换输入**）—— 刷期望值

```bash
# 按当前输出就地重刷 expected（只动 expected，context / rules / keywords 不变）
..\.venv\Scripts\python.exe process\algorithms\fuzzy\examples\run_demo.py --refresh-expected

# 刷完必须回来确认一次
..\.venv\Scripts\python.exe process\algorithms\fuzzy\examples\run_demo.py --check
```

⚠️ **刷之前先看 `git diff`**（或先备份）：`--refresh-expected` 会**无条件覆盖**期望值，
所以它只能用来「把已知变更同步进基线」，**不能用来「让 FAIL 变绿」**。

⚠️ 案例 JSON 里的 `keywords` 是**导出时的元数据快照** —— 改了库里的
`RuleKeyword`（例如论域上下界）后，**案例不会自动跟着变**，必须手工同步，
否则会出现「代码是对的、案例却报 FAIL」的假退化（2026-10-29 就踩过一次：
`MBP0.range_min` 没同步 §33 的 10→0）。

### B. 换输入 / 换案例 —— 重新导出

```bash
# 重新导出（会覆盖同名案例；期望输出按当前算法重算）
..\.venv\Scripts\python.exe process\algorithms\fuzzy\examples\export_case.py
```

`export_case.py` 取库里**最近一条** `TuningRecord`，按生产路径取规则与元数据，
再真跑一次引擎把输出固化成 `expected`。

新增案例：复制一份 JSON → 改 `case_id` / `context` / `rules` / `keywords` →
`expected` 用 `export_case.py` 的同款逻辑重算（**不要手写期望值**）。

⚠️ `export_case.py` 是**开发期工具**，它 import 了 service 层
（`process.services.parameter_optimize`）来还原「机台/材料/模具/工艺参数」的
真实抽取口径。算法包的运行时代码不依赖 service 层（依赖方向：service → algorithm），
本脚本只是站在 service 那一侧取数。

## 已知边界（案例固化了这些现状，不是 bug 修复记录）

- **选库口径已改为「未指定 ⇒ 全量模糊库」**（2026-10-29 改造）：旧的
  「产品类别 → 库编码」映射表指向 `packaging` / `auto_parts` / `medical` 等 code，
  库里不存在 ⇒ 候选必然落空，只加载 `base` 通用库，
  9 个补充库共 1058 条规则（占 64%）从不参与推理。
  现在未指定库时加载**全部模糊库**，「哪条规则适用于本产品」由规则自身的
  材料 / 产品标注判定（`matches_context` + `resolve_specificity`）。
  ⇒ 本案例上下文（PP / 汽车内饰件）下，9 个补充库中真正改变数值的只有
  `R20240326160428` 的 1 条（`IF SHORTSHOT_low THEN BT1_add_1` ⇒ 料筒温度一段 +1）；
  其余或因产品类别冲突被排除，或前件激活度为 0（如 `MEL_high` / `SHORTSHOT_high`）。
- **案例里的 `rules` 是导出时刻的快照**：离线跑（`run_demo.py`）用的是快照，
  在线跑用的是当前库 ⇒ 两者可能不一致（需要时用 `export_case.py` 重新导出）。
- **案例里的 `keywords` 同样是快照**（2026-10-29 手工同步过一次：`MBP0.range_min`
  10 → 0，与库的论域修复对齐）⇒ 改了库里的论域元数据要**手工同步**到案例，
  否则会出现「代码没退化、案例却报 FAIL」。
- **输出不携带规则依据**：`rule_refs` 恒为空数组，`reason` 只有「模糊推理」。
  案例里能看到 `rules[].source_ref` 指向 `RuleMethod:<id>`，
  但**引擎产出里没有它** ⇒ 工艺员看不到「依据哪几条规则」。
- **缺陷程度只影响激活度，不影响选规则**：`level=low` 时 `SHORTSHOT_medium`
  的规则照样进池（组内占比约 0.12）—— 这是「越严重越激进」的表达方式。

## 与其它验证资产的关系

| 资产 | 用途 | 位置 |
|---|---|---|
| **本目录** | 业务视角：真实案例输入 + 期望输出 | `process/algorithms/fuzzy/examples/` |
| 纯内核 pytest | 算法数值路径的单元测试（无需 DB） | `process/algorithms/fuzzy/fuzzy_core/tests/` |
| 回归对拍脚本 | 改前/改后副本的等价性证明 + 黄金快照 | `tests/fuzzy_kernel/_snapshot_core.py`、`tests/fuzzy_kernel/_golden_M1.json` |
| 离线边界验证 | 脏规则隔离、DB 故障降级 | `tests/_verify_e2_offline.py` |
| 规则库全量快照 | 规则/关键词的完整导出（非案例切片） | `_data/*.json` |

⚠️ 本目录的 runner **没有**接进 pytest（默认不新增测试用例）。
它是**手动跑**的回归基线：改了算法后跑一次 `run_demo.py --check`，
退出码非 0 就说明行为漂了。
