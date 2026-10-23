# 旧版 fuzzykit 与当前版模糊引擎对比（2026-10-22）

> 目的：还原旧版「原本想干什么」，据此判断当前版哪些是继承的缺陷、哪些是新造的缺陷、
> 哪些是重写时不该丢的能力。
>
> 旧版位置：`F:\items\inovance-cooperation\HsMoldingService\mdprocess\utils\fuzzykit`
> 当前版位置：`backend/process/algorithms/fuzzy/`
>
> 关联文档：
> - `2026-10-22-fuzzy-algorithm-internals.md`（当前版算法包内部整理，A/B/C 三类问题）
> - `2026-10-22-fuzzy-feature-full-chain-guide.md`（全链路背景，非当前焦点）

---

## 1. 结论速览

用户判断「旧版就是规则匹配器，通过矩阵运算，不可靠」——**这个判断对旧版成立，对当前版不成立**。

准确的说法是：

- 旧版**本来就是**规则匹配器，而且它对此很诚实：输出「候选规则列表 + 激活度」，让人来选。
  规则知识本来就不精确，给候选比给唯一答案更诚实。
- 当前版把外壳换成了「自动决策器」（每参数一个建议值），但**内核原封不动仍是匹配器的矩阵门控**，
  而新加的第五层聚合（直接相加）是**语义未定义的**。
- 于是变成：**匹配器的内核 + 自动决策的外壳 + 没定义的聚合语义** = 不可靠。

所以问题不在「矩阵运算」，而在**把匹配结果直接当成决策**这一步没有依据。

另外确认用户提供的证据（`process_optimize_service.py:545-547`）：

```python
# model = nets.TskRuleNet(tsk_array, keyword_array)
model = nets.NumTskRuleNet(tsk_array, keyword_array, rule_priority)
particular_list = nets.ParticularRules(adjust_array)
```

旧版线上走的是 **NumTskRuleNet（零阶 TSK）**，Mamdani（`FuzzyRuleNet`）虽实现完整但基本未启用。

---

## 2. 旧版 fuzzykit 结构

```
fuzzykit/
├── macros.py                       87 行   常量：HS_MAPPING_DICT 等
├── range_transfer.py               95 行   论域动态修正（钩子）
├── new_test.py                    232 行
├── fuzzy_core/
│   ├── models/nets.py            1281 行   四个网络类（核心）
│   ├── functional/
│   │   ├── membership.py           95 行   gauss/tri/trap 隶属度函数
│   │   ├── defuzzy.py             379 行   反模糊化（centroid 等）
│   │   └── arraypad.py           1217 行   数组补齐（供规则归纳用）
│   ├── induction/                 约 2400 行  规则归纳（ripper/irep/catnap）—— 挖掘，非推理
│   ├── dataset/
│   │   ├── Rule.dat               273 行   原始规则库
│   │   └── process_ranges.csv     177 行   论域配置（RuleKeyword 的原型）
│   └── utils/translate.py          66 行
```

### 2.1 四个网络类

| 类 | 行号 | 状态 |
|---|---|---|
| `FuzzyFeature` | L12 | 隶属度特征（当前版原样继承） |
| `FuzzyRule` | L74 | Mamdani 规则解析 |
| `FuzzyRuleNet` | L132 | **Mamdani 网络**（基本未启用） |
| `TskRule` | L430 | 一阶代数式 TSK 规则解析 |
| `TskRuleNet` | L521 | 一阶 TSK 网络（当前版删成 `NotImplementedError` 占位） |
| `ParticularRules` | L817 | adjust 特殊规则解析（当前版 import 但从未实例化） |
| `NumTskRule` | L869 | 数值 TSK 规则解析 |
| `NumTskRuleNet` | L959 | **零阶 TSK 网络（线上实际使用）** |

---

## 3. 旧版真实调用链

`mdprocess/services/process_optimize_service.py::tsk_algorithm()`（L515-696）：

```
1. 解析缺陷信息
   -> target_defect / target_position / target_level

2. rule_service.load_rule_from_database(subrule_no)
   -> rule_array     规则描述字符串列表
   -> keyword_array  [{keyword, lvl, min_val, max_val, step}]
   -> rule_priority  优先级列表
   -> rule_library   子规则库编号

3. read_machine_setting_para(machine_info, keyword_array)      <-- 论域上界修正
   设备真实上限直接改写 keyword_array[i]['max_val']

4. 规则分流
   含 'adjust' -> adjust_array -> ParticularRules
   其余        -> tsk_array    -> NumTskRuleNet(tsk_array, keyword_array, rule_priority)

5. 注入离散模式参数（0 / 0.95 / 1 形式的数值）
   injectstage1 / injectstageN / holdingstageN / meteringstageN / DMAM0..2

6. 注入缺陷参数
   current_value_dict[target_defect] = 0
   current_value_dict['DL' + 缺陷名 + 段号] = 0.99

7. model.predict(current_value_dict, top_k=10)

8. 过滤低激活度规则
   首轮  rule[1] > 0.01
   迭代轮 rule[1] > 0.05

9. 输出 candidate_rules 列表（规则描述 + 激活度 + 结论键值），交给前端/工艺员
```

**关键：旧版的输出是候选规则列表，不是最终建议值。服务端不做聚合。**

---

## 4. 旧版零阶 TSK 推理逐层拆解（`nets.py` L1171-1266）

### 第一层 隶属度层

```python
membership_degrees = np.zeros(num_degrees) + 0.0000001
for k in x:
    if k not in self.pre_set: continue
    idx, f_k = self.pre_dict[k]['index'], self.pre_dict[k]['memberships']
    for i in range(f_k.f_level):
        membership_degrees[idx + i] = f_k.get_value_by_level(x[k], i)
```

### 第二层 规则层（门控 + 连乘）

```python
rule_matrix = self.connected_matrix * membership_degrees
for i in range(self.rule_nums):
    conditions = rule_matrix[i, rule_matrix[i] != 0]
    if conditions.size != 0:
        rule_activations[i] = np.prod(conditions)      # 连乘
```

### 第三层 归一化层

```python
activations_sum = np.sum(rule_activations)             # 全库求和
new_activations[i] = rule_activations[i] / activations_sum
activations_with_priority = new_activations * priority_array
```

### 第四层 结论层

```python
cur_params = np.ones(shape=(self.connected_matrix.shape[0], ))
for i in range(self.rule_nums):
    k = self.rule_solution[i]
    if k not in x: continue
    if self.rule_classify[i] == 1:                     # 百分比规则
        cur_params[i] = x[k]
sol_matrix = self.solution_matrix.T * cur_params
```

### 第五层 输出层 —— **整段被注释掉**

```python
# # 第五层（输出层），将结论层加权求和
# sol_param = {}
# for k in self.sol_set:
#     idx = self.sol_dict[k]['index']
#     a = sol_matrix[idx, :]
#     sol_param[k] = np.dot(sol_matrix[:, idx], new_activations)
```

作者写了加权平均（`np.dot(sol_matrix[:, idx], new_activations)`），但注释掉了。
**旧版最终输出**是 `zip(rule_list, activations_with_priority, calculate_list)` 排序后的规则候选列表。

> 这行注释很关键：它是 TSK 的标准做法——零阶 TSK 的结论本身就是确定值，
> 激活度只用来排序，不参与数值计算（参与数值计算的是一阶 TSK 的线性结论）。
> 作者没搞清这一点，所以注释掉了。

---

## 5. 新旧逐层对照：四层内核完全一致

| 层 | 旧版 nets.py | 当前版 nets.py | 是否一致 |
|---|---|---|---|
| 隶属度层 | L1184-1192 | L671-686 | **逐行相同** |
| 规则层 `np.prod` | L1195-1202 | L688-700 | **逐行相同** |
| 归一化 `sum` 全库 | L1205-1209 | L702-712 | **逐行相同** |
| 结论层 `sol_matrix.T * cur_params` | L1213-1223 | L714-726 | **逐行相同** |
| 第五层聚合 | **注释掉** | **自创「直接相加」** | **分叉点** |

⇒ 当前版的四层推理就是旧版的四层推理，一字不差地搬过来。
⇒ **所有 A 类问题（P1~P4）都是旧版原样继承的，不是新写的。**
⇒ **唯一的分叉是第五层聚合，这是当前版自创且语义未定的部分。**

---

## 6. 旧版有、当前版丢了的能力（6 项）

### 6.1 缺陷参与连续计算

旧版把缺陷当**普通参数**注入 `current_value_dict`，给它具体数值（0 或 0.99），
让它走完整的「模糊化 -> 门控 -> 连乘」流程。

`process_ranges.csv` 里缺陷的论域是 `SHORTSHOT,3,0,1,-1,-1,-1`，即 **[0,1] 的 3 档论域**。

当前版：`nets.py` 中 `if not self.pre_dict.get(name): continue` 把缺陷前件**静默剔除**，
缺陷改为在路由层（`RuleQueryService._match_defect_level`）用字符串精确匹配做筛选。

**修复成本极低（已实证）**：`RuleKeyword` 里**本来就有 18 个缺陷名**
（`SHORTSHOT` / `FLASH` / `ABERRATION` / ... / `DEFECTFREE`），`fuzzy_level=5`，
论域齐全。之所以没进 `pre_dict`，只是因为 `collect_param_names()` 主动排除了缺陷名。
一旦把缺陷名收进 `keyword_array`，`nets.py` 的门控代码**一行都不用改**就能工作：

```
-- C) CURRENT mapping + defect keywords present in pre_dict --
   1. act=0.355867  IF SHORTSHOT_low THEN BT1_add_1
   2. act=0.258412  IF SHORTSHOT_low AND IV0_high THEN IV0_reduce_2
   4. act=0.034972  IF SHORTSHOT_medium AND IV0_high THEN IV0_reduce_3.0
```

（对比 A 组同样输入下只有 0.001361——差异见 12.3）

**效果对比**：
- 旧版：缺陷严重度是连续的，隶属度参与强度计算（缺陷越重，相关规则激活度越高）
- 当前版：缺陷严重度是 0/1 开关，只决定「这条规则要不要进来」

### 6.2 缺陷位置参与门控

旧版 `DL` + 缺陷名 + 段号 是真实的前件维度（注入 0.99）。
当前版 `RuleQueryContext.defect_position` 注释明说「本期不参与规则筛选」。

**但当前规则库确实在用它**（已实证，纠正了本文初稿的「出现次数为 0」说法）：

```
rules carrying a DL* position precondition: 20
```

这 20 条规则全部是 `OVERSIZE` / `UNDERSIZE` 的位置细分：

```
IF OVERSIZE_low AND DLOVERSIZE1_high AND PP0_low AND PT0_high THEN PT0_reduce_0.3
IF OVERSIZE_low AND DLOVERSIZE2_high AND PP1_high THEN PP1_reduce_3
IF OVERSIZE_low AND DLOVERSIZE1_high AND PP0_high THEN PP0_reduce_3
IF OVERSIZE_low AND DLOVERSIZE2_high AND PP1_low AND PT1_high THEN PT1_reduce_0.3
IF UNDERSIZE_medium AND DLUNDERSIZE1_high AND PP0_low THEN PP0_add_6.5
IF UNDERSIZE_medium AND DLUNDERSIZE2_high AND PP1_low THEN PP1_add_8
...
```

`RuleKeyword` 里也有对应的 `DLOVERSIZE1/2`、`DLUNDERSIZE1/2` 等条目。

**后果（真实缺陷，不是潜伏）**：`collect_param_names()` 用 `is_position_name()` 排除
所有 `DL` 开头的参数 ⇒ 这些前件被静默剔除 ⇒ 规则退化成
`IF OVERSIZE_low AND PP0_low AND PT0_high THEN PT0_reduce_0.3`，
**位置 1 与位置 2 的规则同时激活、互相冲突**。

### 6.3 离散模式参数参与计算

旧版注入：注射段数、保压段数、计量段数、DMAM 模式（0/0.95/1 形式的 one-hot 数值）。
当前版：无。

### 6.4 论域上界按设备真实值修正

旧版 `read_machine_setting_para`（`process_optimize_service.py` L255-303）**真的生效**：

| 参数 | 设备字段 |
|---|---|
| IP0~IP5 | `max_set_injection_pressure` |
| IV0~IV5 | `max_set_injection_speed` |
| IL0~IL5 | `max_injection_stroke` |
| PP0~PP4 | `max_set_holding_pressure` |
| PV0~PV4 | `max_set_holding_speed` |
| MP0~MP3 | `max_set_metering_pressure` |
| MBP0~MBP3 | `max_set_metering_back_pressure` |
| MSR0~MSR3 | `max_set_screw_rotation_speed` |
| ML0~ML3 / VPTL / MEL | `max_injection_stroke` |

当前版：`specs.py` 钉了契约（标注「必填」，注释明说是「论域上界」），
`schemas/optimization.py` 有对应字段，但**算法包内没有任何地方把这些值写进 keyword 的 max_val**。
`specs.py` L372-377 留了明确 TODO：

```
# TODO（论域改造时一并处理，本次只钉契约）：
# 2. fuzzy_algorithm.py 的 keyword 兜底分支（min_val=0, max_val=当前值×2）改为
#    读本维度的 max_set_* / max_*_temp，让论域真正等于设备与材料的物理边界。
# 3. utils/translate.py 已有未被使用的 ranges_provider 钩子，是第 2 点的现成接缝。
```

⇒ **这是当前版相对旧版的能力回退**，且正好命中「我们很常用设备真实值和传入参修正」这条既定要求。

### 6.5 激活度阈值过滤

旧版在调用方过滤（首轮 >0.01，迭代轮 >0.05）。
当前版 TSK 路径不用 `MIN_ACTIVATION_THRESHOLD`（该常量只在死代码 Mamdani 路径用），
改用「丢弃零变化项」代替，语义完全不同。

### 6.6 档位语义字典分离

旧版 `rule_service.change_rule_to_explanation` 用了**四个独立字典**：

| 字典 | 用途 | 示例 |
|---|---|---|
| `KeyWord` | 参数中文名 + 缺陷档位中文名 | 偏低/适中/偏高 |
| `Paramkeyword` | **参数**档位中文名 | 偏低/适中/偏高 |
| `LocationKeyWord` | **缺陷位置**中文名 | — |
| `optimizeKeyWord` | 调整幅度中文名 | — |

⇒ 旧版作者在「翻译成人话」这层，**明确区分了「参数档位」和「缺陷严重度」**。
但引擎层没有区分——因为两边都是 3 档、索引恰好都是 0/1/2，「碰巧能用」。

**参数从 3 档升到 5 档后，这个巧合失效，而代码没有分离语义 —— 这就是 P1/P6 的病根。**

---

## 7. 当前版自创、语义未定的部分（1 项）

### 第五层聚合：直接相加

当前版 `fuzzy_algorithm.py::_merge_layer_results`：

```python
merged[p]['delta'] += rec['delta']              # 同参数多条规则直接相加
merged[p]['activation_sum'] += rec['activation']
```

问题：
1. 旧版不做聚合（输出候选列表），当前版做了，但**没有依据**。
2. 归一化分母是**全库**（P2），所以「A 参数有 10 条规则、B 参数有 1 条」时 A 被摊薄 10 倍。
3. 再直接相加，等于把「相对份额」当成「绝对强度」用——两者混用（P3 + P4）。

**这是当前版唯一一处「不是从旧版继承」的核心逻辑，也是最不可靠的一处。**

---

## 8. 当前版修好的旧版 bug（2 项）

### 8.1 下标错位

旧版 `resolve_input_paras`（L1017-1026）排除 `worse` 规则时：

```python
for i, rule in enumerate(rule_array):
    if 'worse' in rule.get('rule_description'):
        self.rule_nums -= 1
        continue                                   # 跳过，但 rule_dict 用的是原始 i
    self.rule_dict[i] = NumTskRule(...)            # <-- key 会跳号
    self.rule_solution.append(...)                 # <-- append 不占 rule_dict 下标
```

⇒ `rule_dict` 的 key 跳号、`rule_solution` 连续、两者错位；
⇒ `connected_matrix` 行数是减后的 `rule_nums`，写 `rule_dict` 的原始 key 会**越界**；
⇒ 旧版靠 `if row_idx < len(self.connected_matrix)` 的防护（L1141/L1157）掩盖，
   实际后果是**被排除的规则会覆盖后面规则的内容**。

当前版改用 `idx = len(self.rule_dict)` 连续化，并用 `orig_idx` 同步对齐 priority，**已修复**。

### 8.2 档位词解析

旧版 `NumTskRule._rule_process`：

```python
words = phase.split('_')
r_preconditions[words[0]] = {'name': words[0], 'level': words[1], ...}
```

只认**第二段**是档位，只支持单段档位词（low/mid/high）。
当前版改成最长后缀匹配，方向对，但仍不完整（`IV0_very_low` 会被拆成 name=`IV0_very`）。

---

## 9. 规则库形态差异

| | 旧版 `Rule.dat` | 当前版 DB |
|---|---|---|
| 条数 | 273 | 1646 |
| 参数分级 | 3 档 | 5 档 |
| 缺陷分级 | 3 档（low/mid/high） | 3 档 |
| 结论形态 | **档位**（`MEL_add_low`） | **数值**（`add_2` / `reduce_30%`） |
| 结论参数个数 | 1 | 1（100%） |
| 位置维度 | `DL*` 参与 | 不参与 |
| 模式维度 | `injectstage*` / `holdingstage*` / `DMAM*` 参与 | 不参与 |

旧版规则样例：

```
IF SHORTSHOT_low AND MEL_mid THEN MEL_add_low
IF SHORTSHOT_low AND MEL_high AND injectstage1_high AND IV0_low THEN IV0_add_low
```

当前版等价形态：

```
IF SHORTSHOT_low AND IV0_low THEN IV0_add_2
```

⇒ **旧版是 Mamdani 语义（结论=目标档位），当前版是零阶 TSK 语义（结论=确定数值）。**
⇒ 旧版 Mamdani 那套（`FuzzyRuleNet` 的「档位+方向」结论矩阵 + centroid 反模糊化）
   是为旧规则形态设计的，当前规则形态下**根本不适用**，删掉是对的。

---

## 10. `RuleKeyword` 字段沿革

| 旧版 `process_ranges.csv` | 旧版 ORM `RuleKeyword` | 当前版 ORM `RuleKeyword` | 旧版 TSK 是否使用 |
|---|---|---|---|
| Name | `name` | `keyword_name` | 是 |
| level | `level` | `fuzzy_level` | 是 |
| all_range_min | `all_range_min` | `range_min` | 是 |
| all_range_max | `all_range_max` | `range_max` | 是 |
| action_range_min | （无） | `action_range_min` | **否** |
| action_range_max | （无） | `action_range_max` | **否** |
| action_max_val | `action_max_val` | `action_max_val` | **否**（只当 step 给 Mamdani 用） |

⇒ 「单次最大调整量约束」「调整区间上下限」这两个机制**从旧版到当前版都没有实现过**，
是原作者留下的未完成设计，不是当前版的回退。

旧版 `range_transfer.py` 里的 `tranfer_by_current(current_value_dict)` 也是 `pass` 空实现——
「按当前值修正论域」这个想法旧版就有钩子，但同样没做。

---

## 11. 对重写的直接影响

### 11.1 必须保留（当前版已有，不能丢）

- 四层推理骨架（隶属度 -> 门控连乘 -> 归一化 -> 结论）
- 零阶 TSK 数值结论语义（`add_2` / `reduce_30%`）
- 规则串词法解析（但要修最长后缀）
- per-parameter 论域与分级（当前版已领先旧版）

### 11.2 必须改掉（重写的真正目标）

| 项 | 现状 | 目标 |
|---|---|---|
| 第五层聚合 | 直接相加，语义未定 | 明确语义后再实现（见下） |
| 档位->桶定位 | 全局 3 档表 | per-parameter，用该参数自己的 fuzzy_level |
| 语义字典 | 缺陷档位与参数档位混成一张表 | 拆成两套 |
| 归一化分母 | 全库共享 | 至少按参数分组 |
| 缺陷参与 | 字符串路由（0/1） | 明确选型：连续参与 or 保留路由 |
| 缺陷位置 | 不参与 | 明确是否纳入 |
| 离散模式参数 | 不参与 | 明确是否纳入 |
| 论域上界 | 契约有、实现无 | 接上设备真实上限 |
| 激活度阈值 | 无 | 明确阈值与作用位置 |

### 11.3 三个待拍板问题（重新定位）

之前列出的三个问题仍然有效，但旧版给出了新线索：

**问题一：激活度是绝对强度还是相对份额？**
- 旧版：归一化后**只用来排序**，不参与数值 ⇒ 相对份额
- 旧版作者注释掉的 `np.dot` 那行 ⇒ 他想在数值里用权重
- 当前版：归一化后又拿去乘调整量再相加 ⇒ 混用
- **重写必须二选一**。若选「相对份额」，聚合就该用加权平均（`np.dot`）；
  若选「绝对强度」，归一化就该去掉。

**问题二：同参数多条规则怎么合并？**
- 旧版：**不合并**，输出候选列表让人选
- 当前版：直接相加
- **第三条路**：加权平均（TSK 标准做法），权重 = 归一化激活度

**问题三：档位->桶的桶序？**
- 已基本确定：per-parameter + 与前端 `LEVEL_WORDS` 对齐（`very_low` 为第 0 桶）
- 新增依据：旧版 `Paramkeyword` 与 `KeyWord` 分离，证明参数档位与缺陷档位本就是两套语义

### 11.4 旧版最值得学的一点

旧版输出候选规则列表，让工艺员选。这在「规则知识本身不可靠」的领域是**更诚实的接口设计**。

⇒ 重写时可以保留这个选项：除了最终建议值，同时输出「命中的规则 + 激活度 + 各自结论」，
让使用者能回溯依据。当前版的 `rule_refs` 恒空（可用性问题）恰好是这个缺口。

---

## 12. 实证结案：P1 的精确性质与量化影响

### 12.1 前提事实（已实证）

```
RuleKeyword rows: 311
  fuzzy_level=5   count=310     (只有 DEFECTFREE 是 3)
```

规则库前件里实际出现的等级词只有四种：

```
== level words in preconditions ==
  low            1516
  high           1437
  medium          493
  worse           154
```

**⇒ 规则库用的是 3 档语义词（偏低/适中/偏高），而所有参数的论域是 5 桶。**

### 12.2 P1 的精确表述（修正之前「错位一档」的粗略说法）

`FuzzyFeature` 的 5 个桶的 means 是从论域下界到上界均匀铺开的：

| 桶 | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| 语义位置 | 最低 | 偏低 | 适中 | 偏高 | 最高 |
| `HS_MAPPING_DICT` 映射 | `low`->0 | `medium`->1 | `high`->2 | （无） | （无） |

**⇒ `low` 查到了「最低」桶，`medium` 查到了「偏低」桶，`high` 查到了「适中」桶。**
**⇒ 整体下移一档；桶 3、桶 4 永远不会被任何规则命中。**

关键障碍：`nets.py` 里查表时 **只有 level、没有 name**：

```python
p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[level]
```

**⇒ 代码层无法区分「缺陷严重度的 low」和「参数档位的 low」——这两者必须分开映射。**
这正是 P6（词表三处分叉）的根源。

### 12.3 量化影响（真实规则库 + 真实参数，monkeypatch 映射表对比）

输入：全部 183 个工艺参数取论域 40% 处（偏低工况），1646 条真实规则。

**A 组（当前映射 low->0 / medium->1 / high->2）**

```
 1. act=0.001361  IF SHORTSHOT_low AND IV0_high THEN IV0_reduce_2
 2. act=0.001361  IF SHORTSHOT_medium AND IV0_high THEN IV0_reduce_3.0
 3. act=0.001361  IF SHORTSHOT_high AND IV0_high THEN IV0_reduce_3.8
 4. act=0.001361  IF SHRINKAGE_low AND VPTL_high THEN VPTL_reduce_0.5
```

**B 组（修正映射 low->1 / medium->2 / high->3）**

```
 1. act=0.001559  IF SHORTSHOT_low AND MEL_low THEN MEL_add_2
 2. act=0.001559  IF SHORTSHOT_medium AND MEL_low THEN MEL_add_3.0
 3. act=0.001559  IF SHORTSHOT_high AND MEL_low THEN MEL_add_3.8
 4. act=0.001559  IF SHORTSHOT_low AND IV0_low THEN IV0_add_2
 5. act=0.001559  IF SHORTSHOT_low AND PV0_low THEN PV0_add_2
```

**⇒ 两组的 top 规则集没有任何一条相同（交集为空）。**

- A 组激活的是「参数偏高 -> 减小」类规则（与「偏低工况」输入矛盾）
- B 组激活的是「参数偏低 -> 增大」类规则（与输入一致）

**⇒ 当前映射下，规则的行为与规则作者的意图相反。不只是数值偏差，是激活了错误的规则集。**

### 12.4 激活度语义混乱的量化证据

同一个输入（偏低工况），仅因「缺陷是否参与」不同：

| 场景 | 激活度 |
|---|---|
| A 组（缺陷被剔除） | 0.001361 |
| C 组（缺陷参与 pre_dict） | 0.355867 |

**相差 261 倍**，而输入参数完全相同。

原因：归一化分母是**全库 1646 条规则**的激活度之和。
缺陷参与后，大部分无关规则被缺陷前件筛掉，分母变小 ⇒ 激活度变大。

**⇒ 激活度既不是绝对强度（它随无关规则数量剧烈变化），
也不是稳定的相对份额（它随缺陷路由变化）。**
这就是 P2/P3/P4 的共同病根，也是「三个待拍板问题」中第一个的实证依据。

---

## 13. `worse` 的新旧差异（已实证）

`worse` 在当前规则库出现 154 次，全部是「提示检查」类规则（结论为弹窗文本）：

```
IF FLASH_low AND CLAMP_worse THEN CLAMP_adjust_请检查锁模力是否不合理。
IF GASVEINS_low AND IPOS_worse THEN IPOS_adjust_请检查注射位置是否不合理。
```

**旧版**：`resolve_input_paras` 里 `if 'worse' in rule_description: rule_nums -= 1; continue`
⇒ **整条规则被排除**，旧版根本不提供这类提示。

**当前版**：`worse` 不在 `ALL_LEVEL_WORDS` ⇒ `is_level_word('worse')` 为 False
⇒ 前件被当作「不作门控」处理（`continue`），**规则保留并参与计算**。

**⇒ 行为差异：当前版比旧版多出了 154 条提示类建议。**
数值上无影响（结论是文本不是调整量），但提示建议的数量与旧版不同。
重写时需明确这 154 条是否应当输出。

另外，旧版的 `worse` 排除逻辑还带一个下标错位 bug（见 8.1），当前版已修。

---

## 14. 前件参数缺失清单（已实证）

```
precondition params missing from RuleKeyword: {'injectstage3': 2, 'HOLDEXIST': 3}
```

| 参数 | 出现次数 | 状态 |
|---|---|---|
| `injectstage3` | 2 | 旧版遗留的注射阶段维度，当前 RuleKeyword 里没有 |
| `HOLDEXIST` | 3 | 保压存在标志，当前 RuleKeyword 里没有 |

这 5 条规则的前件被静默剔除，退化成更宽松的规则。

---

## 15. 遗留待确认（已部分结案，详见第 12/13/14/16/18 节）

## 16. 考古结论：`levelN` 体系的真实用途（2026-10-22 补充）

### 16.1 事实

`level1..level9` 在旧版**用过，但只在结论侧**：

```
Rule.dat:169  IF WELDLINE_low AND DLWELDLINE7_high THEN SCT1_add_level1
Rule.dat:177  IF WELDLINE_mid AND DLWELDLINE7_high THEN SCT1_add_level5
Rule.dat:185  IF WELDLINE_high AND DLWELDLINE7_high THEN SCT1_add_level9
```

旧版 Mamdani 结论矩阵的构造：

```python
s_col_idx = self.sol_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
self.solution_matrix[row_idx][s_col_idx] = 1 * value['action']
```

⇒ `levelN` 定位的是「**输出变量要调到第几个模糊集**」，是 Mamdani **档位结论**的载体
（`add_level1` = “把 SCT1 调到第 1 档”），与“参数当前处于第 N 档”无关。

**前件侧从未使用 levelN**：旧版规则库 273 条的前件 100% 是自然语言词
（`WELDLINE_low` / `DLWELDLINE7_high` / `IV4_low` / `IV4_mid` / `NT_mid` /
`injectstage1_low` / `IDT1_mid` / `VALVEEXIST_high`）。

### 16.2 旧版作者的心智模型（`mdprocess/const.py`）

四套语义词典，每套都是「3 个自然语言词 + level1..9」：

```python
KeyWord         = {"low":"轻微",  "mid":"中等", "high":"严重"}          # 缺陷严重度
optimizeKeyWord = {"low":"少量",  "mid":"中等", "high":"大量"}          # 调整幅度
LocationKeyWord = {"low":"激活程度低","mid":"激活程度中等","high":"激活程度高"}
Paramkeyword    = {"low":"偏小",  "mid":"中等大小","high":"偏大"}        # 参数档位
```

### 16.2b `levelN` 的真实性质：**1-based 编号 → 0-based 列偏移**

它不是“档位映射”，而是索引转换。旧版 Mamdani 结论矩阵：

```python
# 输出变量分配列段：每个输出变量占 lvl 列（它有几个模糊集）
idx = 0
for k, v in self.sol_dict.items():
    k_dict['index'] = idx
    k_dict['memberships'] = FuzzyFeature(k, [0., k_dict['step']], f_level=k_dict['lvl'], ...)
    idx += k_dict['lvl']

# 规则结论 → 具体列号
s_col_idx = self.sol_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
self.solution_matrix[row_idx][s_col_idx] = 1 * value['action']
```

⇒ `level5`→4 的含义是「**SCT1 内部的第 5 个模糊集**」；
⇒ **必须 0-based，因为它要跟 `sol_dict[name]['index']` 相加**；
⇒ 上限 9 = 作者认为“目标档位”刻度到 9 够用。

**⇒ `levelN` 把“档位”定义成【论域内的第 N 个分位】（相对位置），
因此天然与字段级数解耦——只要 `N ≤ 该字段 lvl` 就正确。**

### 16.2c 旧版规则库按「维度」严格分工（实测）

| 位置 | 维度 | 词表 | 字段级数 | 正确性 |
|---|---|---|---|---|
| 前件 | 缺陷严重度（8 个） | `low/mid/high` | 3 | ✅ |
| 前件 | 缺陷位置（`DL*`，132 条规则在用） | `low/mid/high` | 3 | ✅ |
| 前件 | 工艺参数（165 个） | `low/mid/high` | **3** | ✅ |
| 结论 | 目标档位（`SCT0..SCT8`） | `level1..level9` | **9** | ✅ |

**旧版 CSV 的 `level` 列实测：165 个字段是 3，9 个字段是 9（`SCT0..SCT8`）。**
`SCT1_add_level1/5/9` 与 9 档的 `SCT1` **精确对应**——不是巧合，是配套设计。

**⇒ 旧版的隐含前提：「前件维度一律 3 档；结论目标档位可精确到 9 档。」
两套体系各管一段，恰好都正确。**

**⇒ “粗糙”的两处：**
1. `levelN` 挂在全局字典里，但它的物理含义其实依赖目标变量的 lvl；
   **旧版没有校验 `N ≤ 目标变量 lvl`**——若 3 档变量写 `add_level5`，
   `index+5` 会**写到下一个输出变量的模糊集列上**（静默串位）。
2. 前件侧的 per-field 多级**根本没实现**——因为前件全是 3 档，per-field 与全局等价。

### 16.3 旧版为什么一直“能跑”

```python
p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[value['level'].lower()]
```

`low→0, mid→1, high→2` —— 永远指前 3 个桶。
而旧版 `process_ranges.csv` 里**所有字段的 `level` 列都是 3** ⇒ 桶 0/1/2 恰好就是全部
⇒ `偏小/中等/偏大` 与桶 0/1/2 **一一对应** ⇒ **巧合正确**。

**⇒ 结论：旧版的 per-field 分级能力（CSV level 列 + levelN 词表 + per-field 桶宽）完整存在，
前件维度固定 3 档（巧合正确）、结论目标档位可到 9 档（用 levelN，正确）。
只有当某个**前件维度**被改成 5 档时，旧版也会同样错位——它只是没这么设过。**

### 16.4 对当前版的含义

当前版把 310 个字段全改成 5 档，规则库仍是自然语言词 ⇒ **旧版的“巧合”被打破，
全库 1646 条规则集体错位一档。**

**⇒ P1 不是当前版写错的新 bug，是旧版设计缺陷在“字段级数变多”时暴露出来的必然结果。**
这解释了为什么它在旧版一直没被发现。

### 16.5 三条修复路径及其历史依据

| 路径 | 依据 | 规则库改动 | 风险 |
|---|---|---|---|
| **A. 回到 3 档** | 旧版实际运行状态，`偏小/中等/偏大` 与桶 0/1/2 天然对齐 | **零** | 最低 |
| **B. 用 `levelN` 表达 per-field 级数** | **旧版已有但闲置的能力**，`levelN`→桶 N−1 天然与级数解耦 | 1646 条改写 | 中，语义最严谨 |
| **C. per-field 自然语言词表** | 新设计，5 档词表等差扩展 | **零** | 低，需新增 `level_words` 字段 |

**推荐：A 作为默认 + B 作为可选严格形式并存（双轨）**

```
查表规则：
  1. levelN 形式（IV0_level4）→ 桶 N−1，校验 N ≤ 字段 lvl      ← 严格、无歧义
  2. 自然语言词（IV0_high）  → 该字段自己词表里的下标            ← 老规则零改动
```

**核心：`fuzzy_level` 保留 per-field 能力（3/5/9 随意），只是让“词→桶”不再是全局硬编码。**

---

## 18. E2 步骤1 实施记录（2026-10-22）

对应 `2026-10-22-fuzzy-engine-paradigm-decision.md` 的 **E2 档位映射**，
按“小步推进、先加后接”拆分，本步只做**能力建设**，**不接线**（`nets.py` 未改）。

### 18.1 改动清单

| 文件 | 改动 |
|---|---|
| `fuzzy_core/macros.py` | 新增 `LEVEL_WORDS_BY_LVL`（3/5/7/9）+ `LEVEL_WORD_ALIASES` + `resolve_bucket()`；`ALL_LEVEL_WORDS` 改为**从词表派生**；`FUZZY_LEVELS` 指向新表；`HS_MAPPING_DICT` **保留不动**（旧行为仍在） |
| `fuzzy_core/parsing.py` | `split_phase` 情形 3 改为**多段后缀匹配**（E1 遗留补齐）；`normalize_level_word` 改读 `LEVEL_WORD_ALIASES` |
| `fuzzy_core/tests/test_macros.py` | 新建（5 组用例，5/5 通过） |
| `fuzzy_core/models/nets.py` | **未改** —— 推理行为零变化 |

### 18.2 词表定义（权威源：`macros.LEVEL_WORDS_BY_LVL`）

```
3 档: low, medium, high
5 档: very_low, low, medium, high, very_high
7 档: extremely_low, very_low, low, medium, high, very_high, extremely_high
9 档: extremely_low, very_low, low, slightly_low, medium,
      slightly_high, high, very_high, extremely_high
```

**两条硬约束（已写进单测）：**
1. `len(词表) == lvl` —— 桶数必须等于等级数
2. 每张词表**必须含 low / medium / high** —— 现有 1646 条规则用的就是这三个词

**核心词的物理位置：**

| lvl | low | medium | high |
|---|---|---|---|
| 3 | 0% | 50% | 100% |
| 5 | 25% | 50% | 75% |
| 7 | 33% | 50% | 67% |
| 9 | 25% | 50% | 75% |

⇒ 3 档的 low/high 压在论域两端（更极端），5/7/9 档在中间（更温和）。
这是“级数越多、档位越细”的必然结果，不是错误，但会影响跨级数字段的激活严格程度。

### 18.3 `resolve_bucket()` 双轨

```
轨道 1：levelN 形式  → 桶 N-1，仅要求 N <= lvl（与级数解耦）
轨道 2：自然语言词    → 该字段自己词表里的下标
```

越界 / 词不在表 / 等级数无词表，**一律抛 ValueError**（不静默夹取、不静默跳过）。

### 18.4 回归验证（`_dev_refs/diag_fuzzy_e2_step1_regression.py`）

用 `git show HEAD:` 载入旧版 `parsing.py` / `macros.py` 与工作区新版逐条对照：

```
[M1] ALL_LEVEL_WORDS：旧 17 → 新 19（新增 slightly_low/slightly_high，移除 0）
[M2] split_phase 对照（5246 个词法单元）：差异 0
[M3] is_level_word 对照：差异 0
[M4] collect_param_names：29 → 29，新增 0 / 移除 0
```

**⇒ 结论：本次改动对现有 1646 条规则库【零行为变化】。**

### 18.5 顺带修掉的 E1 遗留

`split_phase` 原来只匹配**单个 part**，导致 `IV0_very_low` 被拆成
`name='IV0_very'` + `level='low'`（档位错一档）。现改为最长后缀匹配。
现有规则库不用多段词 ⇒ 对存量零影响，只对未来的多段词规则生效。

### 18.7 步骤 1.5：`HS_` 前缀常量按语义分层

**背景**：`HS_` 是老 `HsMoldingService` 的缩写，随 fuzzykit 迁入时保留下来，现已弃用。
但 `HS_MAPPING_DICT` 实际上**混了三类语义**，不能一把删：

| 部分 | 内容 | 性质 | 与字段级数的关系 |
|---|---|---|---|
| 档位词 | `low/mid/medium/high` | 语义词 | **强耦合**——5 档上会错位一档 |
| 桶编号 | `level1..level9` | 1-based 编号 → 0-based 桶索引 | **解耦**——只需 N ≤ lvl |
| 动作 | `add/reduce/adjust` | 动作符号 | 无关 |

**⇒ 重要修正**：初稿把“档位词”与“桶编号”一起归为“待删部分”，这是错的。
**桶编号（`levelN`）是旧版原设计里唯一天然 per-field 正确的表达，应当永久保留。**

#### 分层结果（`macros.py`）

| 常量 | 语义 | 状态 |
|---|---|---|
| `ACTION_MAP` | 动作符号 | **新提取**，永久保留 |
| `LEVEL_NUMBER_TO_BUCKET` | `levelN` → 桶 N-1 | **新提取**，永久保留 |
| `LEVEL_WORDS_BY_LVL` | 字段级词表 | 步骤 1 新增，权威源 |
| `resolve_bucket(lvl, word, field_words=None)` | 档位词/编号 → 桶索引 | 步骤 1 新增，双轨入口 |
| `HS_MAPPING_DICT` | 由上面三块组装 | `@deprecated`，**仅过渡期保留**（诊断脚本会 monkeypatch 它做 A/B 对照），接线完成后整表删除 |
| `HS_DEFECT_DICT` | 旧版 7 项缺陷 id 表 | **已删**（全仓零消费方，且与现库 18 个缺陷不一致） |

#### 桶编号与词表的对应关系（已写成可执行断言）

`levelN` 的 N 就是该字段词表里的第 N 个词：

```
lvl=3:  level1 → 桶0 → 词表[0] = 'low'
lvl=5:  level3 → 桶2 → 词表[2] = 'medium'
lvl=9:  level9 → 桶8 → 词表[8] = 'extremely_high'
```

`test_macros.test_level_number_table_alignment()` 逐条验证：
编号表长度 == 最大等级数(9)、桶索引恒为 N−1、`levelN` ↔ 词表第 N 个词、
`level{lvl+1}` 越界报错、`level10` 超出编号表报错。

#### 验证

`test_macros` 6/6、`test_nets` 11/11、回归脚本零行为变化、`test_optimize_smoke` PASSED。

### 18.6 下一步（步骤 2：接线）

把 `nets.py:634` 的 `HS_MAPPING_DICT[level]` 换成 `resolve_bucket(...)`。

**关键前提已确认**：`pre_dict[name]['lvl']` **已经存在**（`nets.py` L602 / L604 / L615 都在用），
即每个字段的模糊等级数已经在手 ⇒ **步骤 2 不需要任何额外传参、也不需要 DB migration**，
改动就是 1 行查表 + 1 处 import。

**本步不需要 DB migration**（先按 `fuzzy_level` 从 `LEVEL_WORDS_BY_LVL` 推导，
`RuleKeyword.level_words` 字段留到确认有特殊需求时再加）。

### 18.8 实证：`levelN` 在当前算法中【零使用】

**问题**：`levelN` 编号形式在现行算法链路里到底有没有用？

**实测**（`_dev_refs/diag_fuzzy_level_number_usage.py`）：

```
--- Q1 有效规则 is_deleted=False（1646 条）---
  原始文本含 levelN 的规则数: 0 次
  解析后【前件】level 命中 levelN: 0 次
  解析后【结论】命中 levelN: 0 次

--- Q2 已删除规则 is_deleted=True（0 条）---
  原始文本含 levelN 的规则数: 0 次

--- Q3 前端 LEVEL_WORDS ---
  frontend/src/constants/rule-const.ts:28
  export const LEVEL_WORDS: Record<FuzzyLevel, string[]> = { ... }
  —— 词表里没有任何 levelN
```

**补充实证**（`_dev_refs/diag_fuzzy_sct_migration.py`）：旧版那 24 条
`SCT*_add_levelN` 规则**整批未迁入**。

```
当前有效规则总数: 1646
含 'SCT' 的规则: 0 条
  含 'add_level': 0 条
  含 'level1': 0 条
RuleKeyword 中含 'SCT' 的字段: 9 个 -> ['SCT0'..'SCT8']
```

⇒ `SCT0..SCT8` 这 9 个字段**元数据在、但一条规则都没在用**
⇒ 当前规则库是**重新编写的**，不是从旧版迁移的。

**结论**：

| 环节 | `levelN` 状态 |
|---|---|
| 词法层 `split_phase` | **能解析**（`IV0_level3` → name='IV0', level='level3'） |
| 映射表 `LEVEL_NUMBER_TO_BUCKET` | **在**（9 条目，N → N−1） |
| `resolve_bucket()` 编号轨道 | **在**，但未接线（步骤 2 未做） |
| 现行 `nets.py:634` 活路径 | **死分支**——规则库只有 low/medium/high 三个词 |
| 前端产出 | **不产出**——`LEVEL_WORDS` 按 `fuzzy_level` 给语义词，用户只能从列表里选 |

⇒ **`levelN` 在当前算法中是纯预留能力，无任何数据流经。**

**为什么仍保留**（三条理由）：

1. **它是旧版唯一天然 per-field 正确的表达**。编号 → 桶 N−1，只需 N ≤ lvl，
   与字段级数完全解耦；语义词做不到这一点。
2. **成本几乎为零**：一张 9 条目的字典，无运行时开销。
3. **它是“调到第 N 档”这类精确表达的现成接缝**。将来若引入
   “把 SCT1 调到第 5 档”这类结论语义，编号形式是唯一不会随级数变化而失配的写法。

**但必须诚实标注**：它当前**无数据流经**，不得让后来者误以为它在工作。

**更紧急的是**：真正在生产里跑着的是**语义词**那一轨——它 100% 有数据流经，
而它在 5 档字段上**错位一档**（P1，见第 12 节）。
`levelN` 零使用 vs 语义词全错位，这个对比恰好说明：
**步骤 2 必须接语义词那一轨，`levelN` 只是顺带保留。**

### 18.9 附带发现：9 档前后端不一致

`_dev_refs/diag_fuzzy_word_table_alignment.py`：

```
前端档位: [3, 5, 7]
后端档位: [3, 5, 7, 9]
  [OK]   3 档一致: ['low', 'medium', 'high']
  [OK]   5 档一致: ['very_low', 'low', 'medium', 'high', 'very_high']
  [OK]   7 档一致: ['extremely_low', 'very_low', 'low', 'medium', 'high', 'very_high', 'extremely_high']
  [DIFF] 9 档: 前端缺失
```

- 前端 `FuzzyLevel = 3 | 5 | 7`
- 后端 `RuleKeyword.fuzzy_level` choices = `[(3),(5),(7),(9)]`

⇒ **后端多支持 9 档，前端类型里没有。** 这是**改动前就存在**的不一致，
`LEVEL_WORDS_BY_LVL` 落地后被显性化。

当前无影响：`RuleKeyword.fuzzy_level` 实际分布 = 3 档 1 个（DEFECTFREE）、5 档 310 个、
**7 档 0 个、9 档 0 个** ⇒ 7/9 档均为纯预留。

**待拍板**：9 档词表命名。后端目前用 `ultra_low/ultra_high` 填充中间两档，
而前端命名规律是「两端扩展 `very_` / `extremely_`」（前端注释原文：
“每加一档在两端扩展（very_ / extremely_），medium 永远在中心位置”）。
`ultra_` 打破了同一词根的对称性 ⇒ 建议改为 `super_low`/`super_high`，
或直接**去掉后端 choices 的 9 档**、前后端统一收窄为 3|5|7。

---

### 18.10 步骤 1.6：注释术语修正 + 三引擎现状核实（2026-10-22）

#### 18.10.1 背景：一句注释造成了一次实际误判

`nets.py` 原头注释用「工厂级 / 兜底层」描述分层 —— 那是旧 `HsMoldingService` 的**业务分层**，
迁入本项目后已失效。当前项目按【**结论形态**】分层（见 `fuzzy_algorithm.py`）。

后果实证：读到「兜底层」即判定 Mamdani 是死代码，**实际它是活的**
（`fuzzy_algorithm.py:491` 确实构造并调用 `FuzzyRuleNet`）。⇒ 注释误导已造成实际误判，
必须修正。

#### 18.10.2 三引擎生产现状（`_dev_refs/diag_fuzzy_mamdani_liveness.py` 实测）

规则库 1646 条按**结论形态**分流：

| 结论形态 | 条数 | 走哪个引擎 |
|---|---|---|
| 数值/百分比（`add_3.8` / `reduce_30%`） | 1547 | `NumTskRuleNet`（零阶 T-S）**生产主路径** |
| adjust / popup（`X_adjust_提示语`） | 99 | `ParticularRules`（纯文本建议，不经 net） |
| 模糊等级（`X_add_low` 形态） | **0** | `FuzzyRuleNet`（Mamdani）—— **已接线但空跑** |

⇒ **Mamdani 引擎代码完整、路径已接线，但规则库无一条模糊等级结论。**
⇒ `TskRuleNet`（一阶）是明确的占位死类（L815-818 自述）。

#### 18.10.3 三引擎的成熟度与取舍

| 引擎 | 现状 | 差距 | 结论 |
|---|---|---|---|
| 零阶 T-S | 已在跑 | **P1/P2/P3 三处接线错** | **唯一当前刚需** |
| Mamdani | 代码完整、已接线、零输入 | 主要缺 P1 | 顺手修（零回归风险） |
| 一阶 T-S | 空壳占位 | **需改规则库结论数据形态 + 迁移 1646 条** | **明确排除** |

一阶 T-S 的排除理由：规则库结论是**绝对/百分比调整量**，不是线性模型；
一阶要求 `z = c₀ + Σcᵢxᵢ`，每条规则需携带一组系数 ⇒ 规则编辑器要改、全库要迁移。
**判据：只有当业务出现「调整量要随当前值变化」的需求时才引入。**

#### 18.10.4 P3 的精确修法：**补分母**，不是重写

当前权重链路已经是对的，缺的只是最后一步：

```python
# nets.py L713-714 —— 权重已算好
new_activations[i] = rule_activations[i] / activations_sum
activations_with_priority = new_activations * priority_array

# fuzzy_algorithm.py L427 —— 分子已加权
'delta': float(value) * float(activation)

# fuzzy_algorithm.py L548 —— 只差分母
merged[p]['delta'] += rec['delta']
```

| | 分子 | 分母 |
|---|---|---|
| 标准零阶 T-S | `Σ(w·c)` | `Σ(w)` **按输出参数分组** |
| 当前实现 | `Σ(w·c)` ✅ | **缺** ❌ |

⇒ **P3 = 补上「按结论参数分组的激活度之和」做分母。**

#### 18.10.5 本步改动（纯注释，零行为变化）

| 位置 | 改动 |
|---|---|
| `nets.py` 头注释 | 「工厂级/兜底层」→ 数值层/提示层；补术语对照块 + 三引擎实测分流数据 |
| `nets.py` L129 / L188 / L407 / L495 分节标题 | 同上口径 |
| `nets.py` `FuzzyRuleNet` docstring | 补「实际空跑」警示 |
| `nets.py` `NumTskRuleNet` docstring | 「零阶 TSK」→「零阶 T-S（数值层）」 |

**验证**：`test_nets` 11/11、`test_macros` 6/6、回归脚本「结果不同的单元: 0」、`test_optimize_smoke` PASSED。

#### 18.10.6 改名与拆文件：延后到重写收尾

`nets` 并非全错 —— Mamdani 确实有网络结构感，类名真正区分的是**两种推理范式**。
真正有害的是注释（已修）。

`nets.py` 当前塞了 4 类东西，**拆分比改名更有价值**：

```
FuzzyFeature            隶属度函数 → functional.py
FuzzyRule / NumTskRule  规则解析   → parsing.py
*RuleNet                推理引擎   → engines/
ParticularRules         提示规则   → engines/advisory.py
```

拆完后 `nets.py` 这个名字自然消失 ⇒ 改名是拆分的**副产品**，不是独立任务。
且项目已有保兼容先例（`split_phase as _split_phase`），可留旧名别名。

---

### 18.11 步骤 1.7：字段提取与定性（FieldRegistry）（2026-10-22）

#### 18.11.1 动机：把「静默跳过」变成「可见的定性」

改造前的过滤链有 5 层，每层滤掉的东西不同，但**没有任何一层会告诉你"我滤掉了什么"**：

| 层 | 位置 | 滤掉什么 | 是否有日志 |
|---|---|---|---|
| L1 词法层 | `collect_param_names` | 缺陷名 17 + 位置名 4 | 无 |
| L2 DB 层 | `get_keywords_by_names` | DB 里没有的字段 | 无 |
| L2' 兜底层 | `_load_keyword_dicts` | 用当前工艺参数值**猜**一个论域 | 无（且 `lvl` 硬编码 3） |
| L3 规则层 | `pre_set` | 规则里没出现过的字段 | 无 |
| L4 引擎层 | `nets.py` L630 | 没元数据的字段（**静默 continue**） | 仅 debug 级 |

⇒ 后果：字段缺元数据时，规则**少了一个门控条件**（激活度偏高），
但这件事只在 debug 日志里，线上等于隐形。

#### 18.11.2 过滤链的实测真相

`_dev_refs/diag_fuzzy_filter_chain.py`（全量 1646 条规则）：

```
L0  RuleKeyword 全量              311 个
L1a 规则里出现的字段              50 个（前件 46 / 结论 27）
L1b collect_param_names()          29 个   <- 剔除缺陷 17 + 位置 4 = 21
L2a collect 里 DB 查得到的          27 个
L2b collect 里 DB 查不到的           2 个   <- HOLDEXIST / injectstage3
L4a net.pre_set                    46 个
L4b net.pre_dict                   23 个   <- 真正参与模糊计算的只有 23 个
L5  静默跳过的前件                 23 个   <- 21 设计排除 + 2 意外缺失
```

**重要修正**：之前按全量 RuleKeyword(311) 统计得出的“48/46 个字段参与”口径不准。
**真正参与模糊计算的是 23 个前件字段**（缺陷名被正确排除，是设计而非错误）。

#### 18.11.3 字段三态

把“哪些字段参与模糊计算”这件事**收敛到一处**（`fuzzy_algorithm._build_field_context`）：

| 状态 | 判定 | 参与推理 | 元数据 |
|---|---|---|---|
| `authority` | 关键词表里有权威元数据 | 是 | 权威（真 fuzzy_level + range） |
| `guessed` | 无权威元数据，但有当前工艺参数值 | **是** | 推测的（lvl=3、[0, 当前值*2]） |
| `unknown` | 既无权威元数据，也无当前值 | 否 | 无（进降级清单） |

`guessed` 与 `unknown` 的区别是关键：
- `guessed` **仍在参与推理**，只是论域是猜的 ⇒ 结论可用但可信度打折
- `unknown` **完全没参与** ⇒ 规则少一个门控条件 ⇒ 激活度偏高

> **设计修正（2026-10-23）**：最初设计了独立的 `fuzzy_core/field_registry.py`
> （四态 + dataclass + property + 降级清单 API，292 行）。评审时判定为**过度设计**并已废弃：
> ① 唯一调用方是 `fuzzy_algorithm.py` 内部，逻辑量只有 ~25 行，不成“库”；
> ② `excluded` 态**永远为空**（`collect_param_names` 已提前剔除缺陷名/位置名）；
> ③ `from_rules()` / `extract_field_names()` / `admissions` / `participates` 全是**死代码**；
> ④ `_guess_meta()` **重复实现了** `_load_keyword_dicts` 的兜底算法 —— 同一套逻辑两份实现，
>    将来改一边忘另一边就会出现“元数据是新的、定性是旧的”这类极难查的偏差。
> ⇒ 最终形态：**分类逻辑内联到 `fuzzy_algorithm._build_field_context`**，三态（去 `excluded`）。

#### 18.11.4 “以关键词为基”的精确含义

“关键词为基”指的是**元数据/校验层**以关键词为基准，**不是矩阵层**：

| 层 | 基 | 理由 |
|---|---|---|
| 元数据/校验层 | **关键词** | 它定义合法字段空间，规则才能被校验 |
| 矩阵/推理层 | **规则** | 只建用到的模糊集；按 311 个关键词建的话，90% 是全 0 列，成本 7 倍 |

> 「关键词没有对应规则就不会命中」这个论据，在**规则驱动**下自动成立；
> 在**关键词驱动**下需要**主动排除**。这正是“基”要分层的原因。

#### 18.11.5 本步改动

| 文件 | 改动 |
|---|---|
| `fuzzy_algorithm.py` | 新增 `_build_field_context()`（分类 + 日志 + 降级清单）；两处推理入口改走它；兜底项加 `source` 标记 |
| `tests/test_fuzzy_field_report.py` | **新建**：5 组用例（mock 掉 `_load_keyword_dicts`，不依赖规则库） |
| ~~`fuzzy_core/field_registry.py`~~ | **已废弃删除**（过度设计，见 18.11.3 的设计修正） |
| ~~`fuzzy_core/tests/test_field_registry.py`~~ | **已废弃删除**（随上一项） |

**`nets.py` 未动**（降级清单在引擎外收集，不需要引擎内部状态）。
**`_load_keyword_dicts` / `_collect_keyword_names` 保留**（两个诊断脚本在用），
且兜底算法**逐字未变**，保证零行为变化。

#### 18.11.6 验证

```
test_nets                 11/11 ✅
test_macros                6/6  ✅
test_fuzzy_field_report     5/5  ✅   （2026-10-23，替代原 test_field_registry）
回归脚本（词法对照）       结果不同的单元: 0 ✅
test_optimize_smoke     PASSED ✅
新回归脚本（真实数据）:
  场景 A（真实 qc，12 条规则）
    M1 论域内容一致 PASS   M2 顺序一致 PASS   M3 推理结果一致 PASS
  场景 B（全量 1547 条数值规则）
    M1 论域内容一致 PASS   M2 顺序一致 PASS   M3 推理结果一致 PASS（1547 条逐条一致）
```

#### 18.11.7 遗留：HOLDEXIST / injectstage3 永远 unknown（且是**结构性**的）

全量场景下 `guessed = 0`、`unknown = 2`（`HOLDEXIST` / `injectstage3`）。

**关键事实（2026-10-23 修正）**：`context` 里四类信息是**互不糅合**的：

```python
# process/services/parameter_optimize.py :: _compose_algorithm_context
{
    'machine_info': machine_info,            # 设备
    'polymer_info': polymer_info,            # 材料
    'mold_info': mold_info,                  # 模具
    'process_parameter': algorithm_params,   # ← 只有【工艺参数】（字段名已归一化）
    'feedback': feedback,
}
```

⇒ `process_parameter` **只有工艺参数**，设备/材料/模具信息在各自独立的 key 里。

而 `HOLDEXIST`（保压启用，布尔控制位）、`injectstage3`（引擎内部 one-hot 中间变量）：
- 不在 `process_parameter`（工艺参数域）⇒ 兜底 B 拿不到当前值
- 不在 `RuleKeyword`（无权威元数据）

⇒ **兜底结构上不可能生效** ⇒ 这 2 个字段永远 `unknown` ⇒ 那 5 条规则永远少一个门控条件

这**不是“数据没配”**，而是“**这两个字段根本不属于当前论域**”。

**根因已查明（2026-10-23，参见「工艺规则关键词 Model 字段设计」）**：这两个字段是
**故意不导入 `RuleKeyword` 的**，同类共 19 条：

| 字段 | 条数 | 不导入的原因 |
|---|---|---|
| `injectstage1-6` | 8 | fuzzy 引擎内部 one-hot 预处理中间变量 |
| `holdingstage1-5` | 5 | 同上 |
| `meteringstage1-4` | 4 | 同上 |
| `HOLDEXIST` | 1 | 业务控制位（保压启用，布尔量） |
| `VALVEEXIST` | 1 | 业务控制位（热流道启用，布尔量） |

⇒ 所以处置方向**不是“补元数据”**（之前的选项 A），而是**复查那 5 条引用它们的规则本身**：
  - `injectstage3` 是引擎内部中间变量 ⇒ 规则引用它没有业务含义
  - `HOLDEXIST` 是布尔量 ⇒ 没有连续论域，不适合走高斯模糊化

⇒ 旧版 `HsMoldingService` 里这些是**离散注入参数**（如 `injectstage1 = 0.95`），
根本不适合走高斯模糊化。归入 **S2 论域设计 + 规则库校正**（而非“数据没配齐”）：
需在 `RuleKeyword` 里显式标注维度类型（连续 / 枚举 / 离散档位），
并明确其取值来源（工艺参数 / 设备状态），让引擎按类型分流。

---

## 17. 遗留待确认（部分已在第 12/13/14/16/18 节结案）

1. ~~规则的 `low/medium/high` 在 5 档下到底对应哪一档？~~ **已结案（步骤 1）**：
   采用选项 a —— 保持 3 档语义，映射到 5 档的桶 1/2/3，
   `very_low`/`very_high` 作为两端延伸。**存量 1646 条规则零改动**。
   （选项 b 需改写全库规则，代价高且无必要。）
2. **缺陷严重度是否走连续参与（旧版语义）还是保留字符串路由（当前版）？**
   - 前置条件已具备：`RuleKeyword` 里 18 个缺陷名 + 论域齐全，修复零成本
3. **缺陷位置（`DL*`，20 条规则在用）是否纳入？** 数据已具备。
4. `worse` 的 154 条提示类规则是否应输出？

