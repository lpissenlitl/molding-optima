# 模糊推理算法包内部整理

> 日期：2026-10-22
> 范围：**仅 `backend/process/algorithms/fuzzy/` 包内部**。
> 上下游（HTTP / 编排 / 落库 / 前端）见另一份
> [2026-10-22-fuzzy-feature-full-chain-guide.md](2026-10-22-fuzzy-feature-full-chain-guide.md)，
> 本文不重复。
> 状态：**只做整理与定位，不含改动方案**。

---

## 1. 算法包的边界

**对外唯一接口**（继承 `process/algorithms/base.py::AlgorithmBase`）：

```python
class FuzzyEngine(AlgorithmBase):
    algorithm_name    = "模糊推理"
    algorithm_type    = "optimization"
    algorithm_subtype = "fuzzy"

    def recommend(self, context: dict) -> List[Recommendation]:  # ← 唯一入口
    def is_available(self, context: dict) -> bool:
    def run(self, context: dict) -> List[Recommendation]:         # 转发到 recommend
```

`Recommendation` 数据类（`base.py`）：

| 字段 | 类型 | 含义 |
|---|---|---|
| `param_name` | str | **算法命名空间**的参数名（`IV0`），不是业务名（`inj_spd_1`） |
| `current_value` | float | 当前值 |
| `recommended_value` | float | 建议值（提示类为 None） |
| `confidence` | float | 置信度 [0,1] |
| `reason` | str | 原因（算法内部文本，服务层会重写） |
| `source` | str | `fuzzy.numeric` / `fuzzy.advisory` / `fuzzy.check` |
| `direction` | Optional[str] | `increase` / `decrease` / `hold` / `check` |

**依赖方向**：算法包 → Django models（`RuleKeyword` / `RuleMethod` / `RuleLibrary`）。
即：**算法包不是纯函数库**，它直接查 DB、也依赖 Django settings。

---

## 2. 包结构

| 文件 | 行数 | 职责 | 状态 |
|---|---|---|---|
| `fuzzy_algorithm.py` | 624 | `FuzzyEngine`：字段命名契约 + `recommend` 编排 + 聚合 | 保留骨架 |
| `adapters.py` | 295 | ORM ↔ 算法数据结构转换 | 保留 |
| `specs.py` | 350 | 算法入参字段白名单 | 保留 |
| `sanity_check.py` | 206 | 自检脚本 | **重写** |
| `services/rule_query_service.py` | 321 | 规则路由（DB 查询 + 三级特异性 + 分流） | 保留 + 补日志 |
| `fuzzy_core/models/nets.py` | 864 | **推理网络（核心）** | **重写** |
| `fuzzy_core/functional.py` | 275 | 隶属度函数 | **重写（瘦身）** |
| `fuzzy_core/parsing.py` | 215 | 词法解析 | **小修** |
| `fuzzy_core/macros.py` | 120 | 常量表 | **重构** |
| `fuzzy_core/utils/translate.py` | 162 | 规则标准化 / 缺陷翻译 | **全删（无人调用）** |
| `fuzzy_core/tests/test_nets.py` | 207 | 单测（测旧实现） | **重写** |

---

## 3. `recommend` 内部调用序列

```
recommend(context)
│
├─ 1. _extract_defect_context(context)              → {defect_name, level, position}
│      从 feedback.defect[0] 取（只取第一条）
│
├─ 2. RuleQueryService.get_rules(RuleQueryContext)    → List[ResolvedRule]
│      选库 → 四级特异性匹配 → 缺陷档位过滤 → 去重
│
├─ 3. split_by_conclusion_kind(rules)                 → {'numeric': [...], 'advisory': [...]}
│      按**结论形态**分流，与规则库层级无关
│
├─ 4. _infer_numeric_layer(numeric_rules, x)
│      ├─ _collect_keyword_names(rules)               → 参数名集合（剔除缺陷名 / DL*）
│      ├─ _load_keyword_dicts(names, x)                → 论域元数据（RuleKeyword + 兜底）
│      ├─ NumTskRuleNet(rule_array, kws, prios)
│      │    ├─ resolve_input_paras()                  → 规则→NumTskRule；剔除 check 类；下标连续化
│      │    ├─ _construct_numtskruleNet()              → connected_matrix + solution_matrix
│      │    └─ tsk_inference(x)                       → 四层推理
│      └─ delta = 调整量 × activation                 ← 摊薄落点
│
├─ 5. _infer_advisory_layer(advisory_rules, x)
│      ├─ check 类（adjust/popup）→ 文本建议（delta=0）
│      └─ 档位结论 → FuzzyRuleNet（Mamdani）★ 死代码
│
└─ 6. _merge_layer_results(numeric, advisory, factor, current)
       同参数 delta 直接相加 → Recommendation[]
```

---

## 4. 三个核心数据结构

### 4.1 `NumTskRule`（一条规则的内存表示，`nets.py:400`）

```python
r_preconditions: {param_name: {name, level, p_type}}     # p_type: 'process' | 'defect'
r_solutions:     {param_name: {name, action, level, s_type}}
                  # action: add→1 / reduce→-1 / adjust→-2
                  # level:  原始字符串（'2' / '30%'）
r_extra:         {原短语: value}                          # popup 专用
```

> ⚠️ 用 **dict 赋值**存储 ⇒ 同名 key 后者覆盖前者。

### 4.2 `FuzzyFeature`（一个参数的隶属度铺桶，`nets.py:75`）

```python
sigmas = [(hi - lo) / (2 * (f_level - 1))] * f_level
means  = [lo, quantile(lo,hi,1/(lvl-1)), ..., hi]
membership_func = gauss_mf
```

**`f_level` 就是该参数自己的 `RuleKeyword.fuzzy_level`** ⇒ 推理层**已经是 per-parameter**。

### 4.3 两个矩阵（`nets.py:592`）

**门控矩阵 `connected_matrix`**（行=规则，列=(参数,桶)）：

```
列布局：  [IV0的5桶][IP0的5桶][PP0的5桶] ...
           └ idx=0 ┘  └ idx=5 ┘
规则 i 的第 j 个前件 → connected_matrix[i][idx(name) + HS_MAPPING_DICT[level]] = 1
```
唯一作用：**广播乘取出门控位置的隶属度**。

**结论矩阵 `solution_matrix`**（行=规则，列=结论参数）：

```
solution_matrix[i][sol_idx] = float(level) * action      # 绝对值
                             = float(level) * action / 100 # 百分比
```

---

## 5. 四层推理的精确语义

### 第一层：隶属度层（`nets.py:688`）

```python
membership_degrees = np.zeros(num_degrees) + EPSILON     # 初始 1e-7，不是 0
for k in x:
    if k not in self.pre_set: continue                    # 缺陷名在此被跳过
    for i in range(f_k.f_level):
        membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)
```

例：`IV0` 论域 [0,120]、`lvl=5` ⇒ `σ=15`，`means=[0,30,60,90,120]`

| x | very_low | low | mid | high | very_high |
|---|---|---|---|---|---|
| 30 | 0.1353 | **1.0000** | 0.1353 | 0.0003 | ~0 |
| 0  | **1.0000** | 0.1353 | ~0 | ~0 | ~0 |

### 第二层：规则层（`nets.py:700`）

```python
rule_matrix = self.connected_matrix * membership_degrees
conditions = rule_matrix[i, rule_matrix[i] != 0]
if conditions.size != 0:
    rule_activations[i] = np.prod(conditions)          # TSK 连乘
```

- **连乘** ⇒ 所有条件都要满足（μ=0.1 × μ=0.9 = 0.09）
- 条件集合由**门控位置**决定，不完全等于规则的 IF 列表
- **缺陷前件在此被静默剔除**（缺陷不在 `pre_dict` 里，`continue` 跳过）⇒ 缺陷条件不参与连乘

### 第三层：归一化 + priority（`nets.py:708`）

```python
activations_sum = np.sum(rule_activations)              # ← 全部规则的总和
new_activations[i] = rule_activations[i] / max(activations_sum, EPSILON)
activations_with_priority = new_activations * priority_array
```

> ⚠️ 分母跨参数共享 ⇒ 参数 A 的强度被参数 B 稀释。

### 第四层：结论层（`nets.py:715`）

```python
cur_params = np.ones(rule_nums)
if self.rule_classify[i] == 1:      # 百分比规则
    cur_params[i] = x[k]             # k = rule_solution[i] = 第一个结论参数
sol_matrix = self.solution_matrix.T * cur_params
```

`sol_matrix[j][i] = solution_matrix[i][j] * cur_params[i]` ⇒ **整行所有结论乘同一个当前值**。

---

## 6. 问题清单（实证结论）

### 6.1 当前就在错（100% 触发）

| # | 位置 | 问题 | 实证 |
|---|---|---|---|
| **P1** | `nets.py:633` `HS_MAPPING_DICT[level]` | 档位→桶用**全局静态表**（3 档语义）。5 档参数上 `low`→`+0`→指向 very_low 桶，**错位一档** | `IV0=30` 时 `IV0_low` 取到 μ=0.1353（应为 1.0）⇒ 调整量被摊薄到 13.5% |
| **P2** | `nets.py:709` 归一化分母 | 分母是**全部参数全部规则**的激活度和，跨参数稀释 | 参数 A 有 10 条规则、B 有 1 条时，A 被摊薄 10 倍 |
| **P3** | `fuzzy_algorithm.py:548` `merged[p]['delta'] +=` | 同参数多条规则**直接相加**，不是加权平均 | 与 P2 叠加后，同参数多条规则的总调整量 ≈ 规则调整量 × (A 的份额) |
| **P4** | `fuzzy_algorithm.py:427` `delta = value × activation` | 摊薄落点：满激活（μ=1）的规则也会被 P2 摊薄 | — |
| **P5** | `parsing.py:90` 从右往左取第一个档位词 | 多段档位词解析错误（`IV0_very_low` → name=`IV0_very`） | 库中 `very_low` 出现在前件中的频次需按最长后缀口径重算 |
| **P6** | `macros.py` 词表三处分叉 | 前端 per-parameter / 后端 `FUZZY_LEVELS` 全局 / 引擎 `HS_MAPPING_DICT` 3 档 | P1 的根因 |

### 6.2 潜伏（当前规则库不触发，规则库一变就错）

| # | 位置 | 问题 | 当前库状态 |
|---|---|---|---|
| **L1** | `nets.py:723` 第四层 | 一条规则含 ≥2 个结论时，**整行乘第一个结论参数的当前值** ⇒ 第二个百分比结论乘错对象 | 实证：`IV0_reduce_30% AND IP0_reduce_20%` → 得 `{IV0:-9, IP0:-6}`（IP0 应为 -20，乘的是 IV0 的 30）；混合 `IP0_add_5 AND IV0_reduce_30%` → 得 `{IV0:-30, IP0:500}`（应为 `{IV0:-9, IP0:5}`）。**但库里多结论规则 0 条** |
| **L2** | `nets.py:437` `r_preconditions[name] = {...}` | 同名前件 dict 覆盖 ⇒ 同参数不同档位时后者胜，**规则语义静默改变** | 实证：`IF IV0_low AND IV0_high` → 门控只剩 high 桶。**库里此形态 0 条**；57 条是同参数同档位重复（无害冗余） |
| **L3** | `fuzzy_algorithm.py:385` 兜底论域 | 缺 RuleKeyword 时自造 `lvl=3` 异构论域 | 实证：结论侧 27 个参数 **100% 有 RuleKeyword**，缺失 0 ⇒ 不触发 |
| **L4** | `nets.py:702` 无阈值过滤 | TSK 路径不应用 `MIN_ACTIVATION_THRESHOLD`（该常量只在 Mamdani 用） | 激活度 ~1e-32 的规则仍进入聚合 |
| **L5** | `fuzzy_algorithm.py:730` `rule_refs` | 永远返回空数组 ⇒ 建议不显示依据规则 | 100% 触发（可用性缺陷，非计算错误） |

### 6.3 死代码与结构性混乱

| 项 | 位置 | 说明 |
|---|---|---|
| Mamdani 整层 | `nets.py:184` `FuzzyRuleNet` | 实测库中**档位结论 0 条** ⇒ 从未产出真实结论。连带 `functional.py` 的 `centroid` / `defuzz` 全死 |
| `tri_mf` / `trap_mf` / `bell_mf` / `singleton_mf` | `functional.py` | 两个 Net 都硬编码 `f_membership_type='gauss'` ⇒ 全死 |
| `FuzzyFeature` 的 `'tri'` 分支 | `nets.py:94` | 无任何调用方传过 `'tri'` ⇒ 全死 |
| 三个隶属度函数**各定义两次** | `functional.py` L156+L312 / L100+L256 / L139+L281 | 重复定义 |
| 误粘贴的模块 docstring | `functional.py` L245-253 | 在 `if __name__` 之后的裸字符串 |
| `TskRuleNet` | `nets.py:811` | `raise NotImplementedError` 占位类 |
| `ParticularRules` | `nets.py:769` | 被 `fuzzy_algorithm.py` import 但**从未实例化** |
| `translate.py` 全模块 | `fuzzy_core/utils/` | `defect_translate` / `rule_standard` 全库无调用（`ranges_provider` 钩子是唯一有价值的部分，但也没接上） |
| 死常量 | `macros.py` | `FUZZY_LEVELS` / `MEMBERSHIP_TYPES` / `DEFUZZ_METHODS` / `HS_DEFECT_DICT` / `ADJUST_ACTIONS` 均无消费方 |
| `ADJUST_ACTIONS` 拼写 | `macros.py:84` | 注释 "=== 动动作名" |
| `sanity_check.py` CASE 2 | `sanity_check.py:72` | 在测 Mamdani，用的是库里不存在的规则串 |
| `sanity_check.py` CASE 3 | `sanity_check.py:112` | **复制一份 `_merge_layer_results` 简化版**来测 —— 因为 import 链有 Django 依赖，测不了真函数 |
| `RuleMethodAdapter` 旧 JSON 路径 | `adapters.py:58` | 读已删除字段 `rule_content` / `defect_name` |
| `_classify_name` 靠 `DEFECT_CONST` | `macros.py:17` | 含 7 个老 fuzzykit 遗留词（`WARPAGE` / `BUBBLE` / ...） |

---

## 7. 规则库的实际形态（决定哪些 bug 会触发）

实测 1646 条（未删除）：

| 维度 | 分布 |
|---|---|
| 结论形态 | 绝对值 **1538** / 百分比 **9** / 提示文本 **99** / 档位结论 **0** |
| 数值结论个数 | 1 个：**1547 条**（100%） / ≥2 个：**0 条** |
| 前件形态 | 缺陷 1 个（必在首位）+ 工艺参数若干；同名重复 57 条（**全是同档位重复**，无害） |
| 参数 `fuzzy_level` | 5 档占 99.7% / 3 档 1 个 / 7 档 0 / 9 档 0 |
| 结论侧参数 RuleKeyword 覆盖 | 27/27 = **100%**（兜底论域分支不触发） |

**推论**：

1. **L1 / L2 / L3 当前都不会触发** —— 它们是「规则库一变就错」的潜伏 bug，重写时必须一并修正，否则等于埋雷。
2. **P1 ~ P4 是唯一现在就在错的四个** —— 且它们都在推理核心的同一处：**「档位→桶→激活度→聚合」这条链的语义是混的**。
3. 规则库形态**极其规整**（每条规则 1 个数值结论、缺陷必在首位），说明**算法不需要处理任意形态的规则** ⇒ 重写时可以收窄设计，不必追求通用模糊引擎。

---

## 8. 重写边界建议

| 处置 | 内容 |
|---|---|
| **删** | Mamdani 全层（`FuzzyRuleNet` / `centroid` / `defuzz` / `tri_mf` / `trap_mf` / `bell_mf` / `singleton_mf`）、`TskRuleNet`、`ParticularRules`、`translate.py`、`RuleMethodAdapter` 旧 JSON 路径、死常量 |
| **重写** | `nets.py` 的推理部分（门控 + 四层 + 结论层）、`functional.py` 瘦身为纯隶属度函数库 |
| **重写** | `parsing.py` 的档位词拆分（最长后缀匹配） |
| **重构** | `macros.py`（词表唯一权威源，per-parameter） |
| **修** | `fuzzy_algorithm.py` 的聚合（加权平均 vs 相加）、`rule_refs` 回填 |
| **保留** | `fuzzy_algorithm.py` 的 `recommend` 骨架、字段命名契约、`RuleQueryService`、`adapters.py`、`specs.py` |
| **新增** | 真正的单元测试（pytest，无需 DB）—— 因为算法包当前**不可测** |

---

## 9. 本轮实证脚本

| 脚本 | 产出 |
|---|---|
| `_dev_refs/diag_fuzzy_algo_audit.py` | A1~A6：混合结论、同参数多桶前件、同名前件覆盖、兜底论域、第四层动态实证 |
| `_dev_refs/diag_fuzzy_pct_audit.py` | B1~B4：百分比结论形态分布、多结论规则计数 |

运行方式：`cd backend; ../.venv/Scripts/python.exe _dev_refs/<脚本>.py`
