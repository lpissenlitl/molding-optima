# fuzzy 模块算法实现 · 实施清单

> **日期**：2026-10-23
> **来源**：`backend/_refs/system/algorithm/2026-10-23-fuzzy-implementation-design.md` 附录 F（实现 vs 规格对照审计）
> **状态**：**纯文档，未改任何生产代码**
> **本批范围（用户第 13 轮拍板）**：只做 **第一刀 A（接线 `resolve_bucket` + 同一次删 `HS_MAPPING_DICT`）**
> **执行方式（用户第 13 轮拍板）**：先出完整实施清单 → 用户挑选 → 再执行

---

## 0. 一页速览

| 项 | 内容 |
|---|---|
| **靶子** | `nets.py` L283 / L293 / L646 三处用全局静态 3 档表 `HS_MAPPING_DICT[level]` 取桶索引 |
| **正确实现** | `macros.resolve_bucket(lvl, word)` —— 按字段自己的档位词表定位桶（**已实现、有 6 组单测**） |
| **为什么不只是"小错"** | 现网 310/311 个字段是 **5 档**，`low/medium/high` 全部**错位一档** ⇒ **3435/3435（100%）前件引用受影响** |
| **实测影响（49 个实验样本）** | 命中规则数 **1018 → 715**（均值）；top-10 推荐**平均换掉 6.4 条**；**首位建议在 45/49（92%）样本上会变** |
| **本批要改的文件** | `nets.py`（3 处 + import）/ `macros.py`（删表）/ `tests/test_nets.py`（断言） |
| **本批要补的基准** | `sanity_check.py` 新增 **7 个真断言** case（B1~B7，现有 4 个 case 断言强度不足，见 §5） |
| **不做** | 门控三态/β_p、聚合层/冲突显式化、TSK 激活度阈值、`functional.py` 清理、`activation` 语义 —— 全部留在后续批次 |

---

## 1. 第一刀 A · 现状代码逐处拆解

### 1.1 生产主路径（`NumTskRuleNet`）—— 影响 100% 前件

`backend/process/algorithms/fuzzy/fuzzy_core/models/nets.py` **L633-652**：

```python
for row_idx, rule in self.rule_dict.items():
    for name, value in rule.r_preconditions.items():
        level = str(value.get('level', '')).lower()
        if not is_level_word(level):
            # 不可判级的前件，不作为门控：
            #   - 'worse'：人工判断词（"该参数不合理"），没有隶属度可言
            #   - 缺陷名：缺陷程度在规则匹配阶段（defect_code + level）
            #     已经保证，缺陷本身也没有数值论域
            continue
        if not self.pre_dict.get(name):
            # 无 RuleKeyword 元数据 → 建不了论域 → 不作为门控
            logger.debug('[NumTskRuleNet] pre_dict 中没有 %s，跳过该前件', name)
            continue
        p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[level]   # ★ L646 病灶
        if row_idx < len(self.connected_matrix):
            self.connected_matrix[row_idx][p_col_idx] = 1
```

**问题**：`HS_MAPPING_DICT['high'] == 2`，这是**全局 3 档口径**。而现网 310/311 个字段是 5 档，`high` 在 5 档词表 `('very_low','low','medium','high','very_high')` 里是**下标 3**。

⇒ 静态桶 2 = 5 档的 **medium**（论域 50% 分位）⇒ **拿"中档"当"高档"判**。

| 档位词 | 静态桶（现网） | 5 档正确桶 | 现网实际含义 |
|---|---|---|---|
| `low` | 0 | 1 | 判成了 very_low（论域下界） |
| `medium` | 1 | 2 | 判成了 low（25% 分位） |
| `high` | 2 | 3 | **判成了 medium（50% 分位）** |

### 1.2 提示层（`FuzzyRuleNet`）—— 两处

**L276-294**：

```python
for name, value in rule.r_preconditions.items():
    level = str(value.get('level', '')).lower()
    if not is_level_word(level):
        continue
    if name in self.pre_dict:
        p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[level]   # ★ L283 病灶
        self.connected_matrix[row_idx][p_col_idx] = 1

for name, value in rule.r_solutions.items():
    level = str(value.get('level', '')).lower()
    if not is_level_word(level):
        continue
    if name in self.sol_dict:
        s_col_idx = self.sol_dict[name]['index'] + HS_MAPPING_DICT[level]   # ★ L293 病灶
        self.solution_matrix[row_idx][s_col_idx] = 1 * value['action']
```

⚠️ **风险提示**：L293 是**结论侧**取桶。当前规则库中**模糊等级结论 0 条** ⇒ 该路径实际空跑 ⇒ 改动风险极低，但**接线时要用 `sol_dict[name]['lvl']`（输出变量的档位数），不是输入侧的**。

### 1.3 静态表本体

`backend/process/algorithms/fuzzy/fuzzy_core/macros.py` **L68-84**：

```python
# === 档位映射（已弃用：HS_ 前缀 + 全局静态表）===
# ...
# - 档位词那部分的正确做法是 `resolve_bucket(lvl, level_word)`
#   （按字段自己的词表定位）。本表暂留仅为过渡期兼容
#   （诊断脚本会 monkeypatch 本表做 A/B 对照），接线完成后整表删除。
# @deprecated
HS_MAPPING_DICT = {
    'low': 0, 'mid': 1, 'medium': 1, 'high': 2,
    **LEVEL_NUMBER_TO_BUCKET,
    **ACTION_MAP,
}
```

⇒ **注释自己写明了"接线完成后整表删除"，但从未接线**（第三例"写好不接线"）。

### 1.4 静态表的全部引用点

| 文件 | 位置 | 性质 | 本批处置 |
|---|---|---|---|
| `nets.py` | L37 import | 代码 | **删** |
| `nets.py` | L283 / L293 / L646 | 代码 | **换成 `resolve_bucket`** |
| `macros.py` | L68-84 | 表定义 | **删表 + 删注释** |
| `tests/test_nets.py` | L28 import、L194 断言 | 测试 | **改成 `resolve_bucket` 断言** |
| `parsing.py` | L101 | 注释 | 改措辞（可选） |
| `fuzzy_algorithm.py` | L507 | 注释 | 改措辞（可选） |
| `specs.py` | L307-317 | 注释 | 改措辞（可选） |
| `_dev_refs/diag_fuzzy_bucket_mapping.py` | L32-36 等 | 诊断脚本 | **改成脚本内自带旧表**（见 §4.3） |

> ⚠️ `macros.py` 的 `LEVEL_NUMBER_TO_BUCKET` 与 `ACTION_MAP` **不能删** —— 它们被 `resolve_bucket` 内部和 `nets.py` L180/L468 使用。

---

## 2. 第一刀 A · 期望代码

### 2.1 `nets.py` import 段（L33-41）

```python
from ..macros import (
    ACTION_MAP,
    ALL_LEVEL_WORDS,
    DEFECT_CONST,
    MIN_ACTIVATION_THRESHOLD,
    MAMDANI_SAMPLE_POINTS,
    EPSILON,
    resolve_bucket,        # ★ 新增；HS_MAPPING_DICT 移除
)
```

### 2.2 新增一个安全解析助手（建议放在 `nets.py` 模块级，`logger` 定义之后）

```python
def _resolve_bucket_safe(lvl: int, word: str, where: str):
    """按字段的档位数解析桶索引；解析不了就显式告警并返回 None。

    §8「禁止静默降级」：词表对不上时不能悄悄取错桶，必须留下可查的日志。
    """
    try:
        return resolve_bucket(lvl, word)
    except ValueError as e:
        logger.warning('[%s] 档位词 %r 无法映射到 lvl=%d 的桶：%s', where, word, lvl, e)
        return None
```

> **为什么不让它直接抛**：现网规则库 3435 条门控引用全部可解析（实测 `resolve_bucket 无法解析 = 0`），但 `resolve_bucket` 对 `lvl` 不在 {3,5,7,9} 的字段、对 `very_low` 落在 3 档词表等情形会抛 `ValueError` ⇒ 直接抛会让**整层推理崩**（`_infer_numeric_layer` L478 的 `except Exception` 会把整层结果清空）。⇒ 显式告警 + 跳过该门控，是 §8 表格里"标记该规则不可用 + 原因"的轻量实现。

### 2.3 三处取桶逐处改法

**① `NumTskRuleNet._construct_numtskruleNet`（L642-648，生产主路径）**

```python
                if not self.pre_dict.get(name):
                    # 无 RuleKeyword 元数据 → 建不了论域 → 不作为门控
                    logger.debug('[NumTskRuleNet] pre_dict 中没有 %s，跳过该前件', name)
                    continue
                # ★ 按【该字段自己的档位数】取桶：同一个 'high' 在 3 档字段是桶 2，
                #   在 5 档字段是桶 3（论域 75% 分位）。用全局静态表会整体错位一档。
                bucket = _resolve_bucket_safe(
                    self.pre_dict[name]['lvl'], level, 'NumTskRuleNet.pre')
                if bucket is None:
                    continue
                p_col_idx = self.pre_dict[name]['index'] + bucket
```

**② `FuzzyRuleNet._construct_ruleNet` IF 前件（L282-284）**

```python
                if name in self.pre_dict:
                    bucket = _resolve_bucket_safe(
                        self.pre_dict[name]['lvl'], level, 'FuzzyRuleNet.pre')
                    if bucket is None:
                        continue
                    p_col_idx = self.pre_dict[name]['index'] + bucket
                    self.connected_matrix[row_idx][p_col_idx] = 1
```

**③ `FuzzyRuleNet._construct_ruleNet` THEN 结论（L292-294）**

```python
                if name in self.sol_dict:
                    # ⚠️ 结论侧用【输出变量自己的档位数】sol_dict[name]['lvl']
                    bucket = _resolve_bucket_safe(
                        self.sol_dict[name]['lvl'], level, 'FuzzyRuleNet.sol')
                    if bucket is None:
                        continue
                    s_col_idx = self.sol_dict[name]['index'] + bucket
                    self.solution_matrix[row_idx][s_col_idx] = 1 * value['action']
```

### 2.4 `macros.py` 删表（L68-84 整段删除）

删掉 `HS_MAPPING_DICT` 定义与其上方注释块，**保留** `LEVEL_NUMBER_TO_BUCKET`（L57-66）与 `ACTION_MAP`（L51-55）。

### 2.5 `tests/test_nets.py` 断言替换

```python
# 旧（L194）
ok &= _assert_eq(HS_MAPPING_DICT['low'], 0, "low=0")

# 新
from fuzzy_core.macros import resolve_bucket
ok &= _assert_eq(resolve_bucket(3, 'low'), 0, "3 档 low → 桶 0")
ok &= _assert_eq(resolve_bucket(5, 'low'), 1, "5 档 low → 桶 1")
ok &= _assert_eq(resolve_bucket(5, 'high'), 3, "5 档 high → 桶 3")
```

---

## 3. 第一刀 A · 实测影响面（务必让业务方知情）

> 脚本：`backend/_dev_refs/diag_fuzzy_bucket_shift_impact.py`（只读）
> 方法：复刻 `FuzzyFeature` 高斯参数 + `tsk_inference` 的激活度公式，对同一条规则分别用静态桶 / 正确桶算 μ；样本取 49 条 `ProcessParameter` 实验数据（经 `_normalize_field_name_by_spec` 归一，与引擎取数路径一致）

### 3.1 结构性变化

| 实测 | 数据 |
|---|---|
| 门控引用总数 | 3435 |
| 门控字段级数分布 | **{5: 3435}**（全部 5 档） |
| **门控桶会位移的规则数** | **1643 / 1643 = 100%** |
| `resolve_bucket` 无法解析的引用 | **0** |
| 前件缺 `RuleKeyword` 元数据 | 5 |

### 3.2 行为变化（49 个样本）

| 指标 | 接线前 | 接线后 | 变化 |
|---|---|---|---|
| 命中规则数（activation > 0.01001，均值） | **1018** / 样本 | **715** / 样本 | 每样本少 **290~421** 条（49 个样本中 48 个减少、1 个不变） |
| 激活度总和（均值） | 464.00 | 426.56 | 比值 **0.918**（最小 0.790 / 最大 1.021） |
| **top-10 推荐重叠度** | — | — | **均值 3.57/10（换掉 6.4 条）**，最差 3/10 |
| **top-1 首位建议变化** | — | — | **45/49 样本（92%）** |
| 规则级彻底失效 | — | — | **0 条**（1637 条前后都能命中，6 条前后都不命中） |

### 3.3 ⚠️ 一条必须讲清楚的机制

**缺陷门控在两种映射下都是"惰性"的，不参与区分。**

- `membership_degrees` 初值是 `EPSILON = 1e-7`，只有出现在 `x`（= `process_parameter`）里的参数才会被真值覆盖；
- 缺陷字段（`SHORTSHOT` / `BURN` / …）**不在 `process_parameter` 里**（缺陷严重度只作为 `RuleQueryContext.defect_level` 做**规则查询过滤**，不作为数值进推理）；
- ⇒ 缺陷门控的隶属度恒为 `1e-7`，对所有规则是**同一个常数因子** ⇒ 静态桶还是正确桶都一样。

⇒ **本次位移的全部影响都落在「工艺参数门控」上**（`IV0_low` / `MBP0_high` / `PT0_medium` …）。
⇒ 顺带确认：**缺陷严重度的实际筛选机制在规则查询层，不在模糊推理层** —— 这是对的，不需要改。

---

## 4. 第一刀 A · 执行清单（逐文件）

### 4.1 步骤 1：先补回归基准（**必须先做**）

见 §5。**理由**：改完之后"对不对"没有客观判据；现有 4 个 sanity case 的断言强度不足（§5.1）。

### 4.2 步骤 2：接线 + 删表（**一个 commit**）

> ⚠️ **前置动作（必做）**：`git status` 显示 fuzzy 模块已有**前几轮遗留的未提交改动**
> （`macros.py` / `nets.py` / `parsing.py` / `test_nets.py` / `fuzzy_algorithm.py` / `specs.py` 等，
> 合计约 338 行插入 —— 正是当初写下 `resolve_bucket` / `LEVEL_WORDS_BY_LVL` / `test_macros.py` 那批）。
> ⇒ **先把它们单独 commit 一次**，再动第一刀。
> ⇒ 理由：只有这样，第一刀的 diff 才是**干净且可独立 revert** 的；否则一次 revert 会连带回退掉已上线的 `resolve_bucket` 本身。

| # | 文件 | 改动 | 行数 |
|---|---|---|---|
| 1 | `fuzzy_core/models/nets.py` | L33-41 import：删 `HS_MAPPING_DICT`，加 `resolve_bucket` | ~2 |
| 2 | `fuzzy_core/models/nets.py` | 新增 `_resolve_bucket_safe` 助手（模块级） | ~12 |
| 3 | `fuzzy_core/models/nets.py` | L282-284 前件取桶 → `resolve_bucket` | ~4 |
| 4 | `fuzzy_core/models/nets.py` | L292-294 结论取桶 → `resolve_bucket` | ~4 |
| 5 | `fuzzy_core/models/nets.py` | L646 前件取桶 → `resolve_bucket`（生产主路径） | ~4 |
| 6 | `fuzzy_core/macros.py` | 删 L68-84（`HS_MAPPING_DICT` + 注释块） | -17 |
| 7 | `fuzzy_core/tests/test_nets.py` | L28 import + L194 断言 → `resolve_bucket` 断言 | ~5 |

> **一个 commit 的理由**：删表与接线必须同时生效，否则中间态会引入"表还在但没人用"的第二次死代码。
> **回退成本**：单 commit ⇒ `git revert` 一次即完全回退（无需手工改回 3 处 + 恢复 macros）。

### 4.3 步骤 3：清理诊断脚本依赖

`backend/_dev_refs/diag_fuzzy_bucket_mapping.py` 依赖 `macros.HS_MAPPING_DICT` 做 A/B 对照 ⇒ 接线后会 ImportError。

**改法**：把旧表**内联到脚本里**（作为"历史口径"的常量），不再从 macros 导入：

```python
# 历史口径（2026-10-23 接线前的全局静态 3 档表），仅供 A/B 对照
LEGACY_STATIC_MAP = {'low': 0, 'mid': 1, 'medium': 1, 'high': 2}
```

### 4.4 步骤 4：跑验收（见 §7）

---

## 5. 回归基准设计（步骤 1 的具体内容）

### 5.1 ⚠️ 先说现有基准为什么不够

`backend/process/algorithms/fuzzy/sanity_check.py` 的 `case_numeric_layer` **断言空转**（实测）：

```
connected_matrix（门控连接矩阵）: []          ← 全 0
priority=[10, 5] 的输出顺序:
    activation=0.000000  IF SHORTSHOT_high THEN inj_pres_1_add_10
    activation=0.000000  IF SHORTSHOT_high THEN inj_pres_2_add_5
priority=[5, 10]（把优先级反过来）的输出顺序:
    activation=0.000000  IF SHORTSHOT_high THEN inj_pres_1_add_10
    activation=0.000000  IF SHORTSHOT_high THEN inj_pres_2_add_5
⇒ 优先级反转后输出顺序是否变化: 否（⇒ 断言空转）
```

**原因**：`keyword_array` 里只有 `inj_pres_1` / `inj_pres_2`，**没有 `SHORTSHOT`** ⇒ 前件被 `nets.py` L642 跳过 ⇒ `connected_matrix` 全 0 ⇒ 激活度全 0 ⇒ `sorted(..., key=-activation)` 退化为**稳定排序 = 输入顺序** ⇒ 断言 `'add_10' in results[0][0]` 恒真。

⇒ **必须新建真断言**，否则改完无法证明对错。

### 5.2 新增 case 清单（`sanity_check.py`）

**统一场景**：字段 `inj_pres_1`，`lvl=5`，论域 `[0, 200]`
⇒ `FuzzyFeature` 高斯参数：`means = [0, 50, 100, 150, 200]`，`σ = (200-0)/(2×4) = 25`

| # | case | 断言 | 接线前 | 接线后 |
|---|---|---|---|---|
| **B1** | 5 档 `high` 落位 | `IF inj_pres_1_high THEN inj_pres_1_add_5`，x=150 ⇒ 激活度 == 1.0 | 0.135335 ❌ | **1.000000** ✅ |
| **B2** | 5 档 `low` 落位 | x=50 ⇒ 激活度 == 1.0（low 桶 1，mean=50） | 0.135335 ❌ | **1.000000** ✅ |
| **B3** | `low` / `high` 不重叠 | x=50 ⇒ `low` 规则激活 1.0、`high` 规则激活 ≈ 0.0003 | 0.135335 ❌ | **1.0 / 0.000335** ✅ |
| **B4** | **priority 真断言** | 同前件两条规则，priority 大的排前；**反转 priority 后顺序必须反转** | ❌（现网空转） | ✅ |
| **B5** | 3 档向后兼容 | `lvl=3` 时 `low→桶0 / medium→桶1 / high→桶2`，与旧版完全一致 | ✅ | ✅（零影响） |
| **B6** | 多段档位词不再崩 | `IF inj_pres_1_very_low THEN ...` 能解析（5 档 → 桶 0） | **KeyError** ❌ | 正常 ✅ |
| **B7** | 无元数据门控显式失效 | 前件参数不在 `keyword_array` ⇒ 该规则激活度 == 0（**不是**被当成无条件命中） | ✅ | ✅（不变） |

> 期望值验算脚本：`diag_fuzzy_bucket_shift_impact.py` §5（可直接复跑核对）。
> **B1/B2/B3 是"能证伪"的断言**：接线前必失败、接线后必通过 ⇒ 它们同时充当**回归基准**和**改对了的证明**。
> **B6 是接线带来的能力增强**（消除 `ALL_LEVEL_WORDS` 里 6 个多段词一旦被使用就崩的隐患）。

### 5.3 载体选择

| 位置 | 用途 | 说明 |
|---|---|---|
| `backend/process/algorithms/fuzzy/sanity_check.py` | **主战场**：加 B1~B7 七个 case | 无 Django 依赖、可 `python sanity_check.py` 直接跑 |
| `backend/process/algorithms/fuzzy/fuzzy_core/tests/test_macros.py` | `resolve_bucket` 自身单测（**已存在 6 组**，无需新增） | 已有 |
| `backend/process/algorithms/fuzzy/fuzzy_core/tests/test_nets.py` | 引擎级：把 L194 的静态表断言换成 `resolve_bucket` 断言 | 已有 |

---

## 6. 其余 11 项 · 展开（供后续挑选，本批**不做**）

| # | 项 | 现状代码 | 期望 | 影响面 | 改法要点 |
|---|---|---|---|---|---|
| **B** | 门控三态 + β_p 降权（§5.3） | `nets.py` L716-719：`rule_activations[i] = np.prod(conditions)` | 未命中 / 边界态（β_p 降权）/ 明确态 三态显式区分 | **依赖 C 先定**；ε 取值待标定（§10-C） | 需先定义"边界"的判据（相邻桶隶属度接近 ⇒ β_p = clamp(competition/ε, β_min, 1)） |
| **C** | 聚合层 + 冲突显式化（§5.4/§5.5） | `fuzzy_algorithm.py` L610：`merged[p]['delta'] += rec['delta']` | 同参数多规则给出相反方向 ⇒ 显式标记冲突，不裸累加 | **业务定**（§10-K：择优 vs 加权平均，用户已说"暂时不需要考虑，是业务逻辑问题"） | 先补 `conflict` 视图字段（不阻断主建议），再谈策略 |
| **D** | TSK 主路径缺激活度阈值（§8） | `MIN_ACTIVATION_THRESHOLD` 只在 Mamdani L367 用；TSK L715-726 无过滤 | TSK 路径同样过滤无效激活 | 成本低；**但会进一步减少命中数**，与 A 叠加需重测 | `tsk_inference` 里加一行 `rule_activations[rule_activations < THRESH] = 0` |
| **E** | 结论形态一等公民（§4.4） | `fuzzy_algorithm.py` L267 `split_by_conclusion_kind` | — | — | ✅ **已实现**，只需在 §4.4 标注完成 |
| **F** | 按级数的词表（§3.2） | `macros.LEVEL_WORDS_BY_LVL`（3/5/7/9） | — | — | ✅ **已实现**，接线后即生效 |
| **G** | 字段缺元数据显式告警（§8） | `fuzzy_algorithm.py` L444 warning + 分类清单 | — | — | ✅ **已实现** |
| **H** | 模糊化（§5.1） | `functional.gauss_mf`，`σ=(hi−lo)/(2(lvl−1))` | — | σ 宽容度待标定（§10-D） | ✅ **已实现**；σ 标定是数据活 |
| **I** | 数值/提示分流（§5.6） | `fuzzy_algorithm.py` L512-540 | — | — | ✅ **已实现** |
| **J** | `functional.py` 重复定义 | L246-250 残留字符串字面量 `"""→隶属度函数"""`；L252-357 重新定义 `triangular_mf` / `trapezoidal_mf` / `gaussian_mf` / `bell_mf` / `singleton_mf`，**覆盖**前面的别名 | 只保留一份 | 主路径只调 `gauss_mf`/`tri_mf`/`defuzz` ⇒ **行为不受影响**；但 `trapezoidal_mf` 在 `x == c` 时旧版 0 / 新版 1 ⇒ 同名两义 | 删 L246-357；把 L48/L99/L139 的别名实现补齐（`trapezoidal_mf` 保持指向 `trap_mf`） |
| **K** | `activation` 语义混乱 | 引擎 L726 产出 `归一化激活度 × priority`；`fuzzy_algorithm.py` L490 把它当 `activation` 塞出；L489 `delta = 结论值 × activation`（已含权重）；L648 `confidence = activation_sum / rule_count` | 拆成三个字段：`raw_activation`（原始激活度）/ `weight`（归一化×priority）/ `delta`（未乘权重的结论值） | 影响 `Recommendation.confidence` 的可信度；`confidence = Σ(归一化值)/条数` 语义不对（归一化值之和恒为 1 ⇒ confidence 恒 ≈ 1/条数） | 改输出契约 ⇒ 需同步前端；建议单独一批 |

### 6.1 推荐的后续批次顺序（供参考）

```
第 1 批（本次）  A：接线 resolve_bucket + 删静态表
第 2 批          D：TSK 激活度阈值（成本最低、与 §8 一致）
第 3 批          J：functional.py 清理（不影响行为，纯卫生）
第 4 批          K：activation / delta / confidence 语义拆开（要动前端契约）
第 5 批          C：聚合层 + 冲突显式化（等业务定 §10-K）
第 6 批          B：门控三态 + β_p（依赖 5）
```

---

## 7. 验收标准

| # | 项 | 判据 |
|---|---|---|
| 1 | 单测 | `pytest fuzzy_core/tests/` 全绿（含 `test_macros.py` 6 组 + `test_nets.py`） |
| 2 | sanity | `python sanity_check.py` 全绿；**B1/B2/B3/B6 在接线前失败、接线后通过**（这是"改对了"的证明） |
| 3 | 静态表清零 | `grep -rn "HS_MAPPING_DICT" backend/process/` **零命中** |
| 4 | 影响面复核 | 重跑 `diag_fuzzy_bucket_shift_impact.py`，与 §3.2 的预测吻合（命中数 1018→715、top-10 重叠 ≈3.6、top-1 变 ≈92%） |
| 5 | 端到端 | 跑一次完整 optimize 链路，把产出的 `Recommendation` 列表存档为**接线前基线**，与接线后 diff（这是业务方验收用的材料） |
| 6 | 诊断脚本 | `diag_fuzzy_bucket_mapping.py` 改为自带旧表后仍可运行 |

---

## 8. 风险与回退

| 风险 | 等级 | 缓解 |
|---|---|---|
| **推荐结果大面积变化**（前 10 条换 6.4 条、首位 92% 变） | 🔴 高 | 上线前必须出「接线前 vs 接线后」的推荐 diff 给业务方看；必要时先并行跑一段时间做对照 |
| `resolve_bucket` 抛 `ValueError` 导致整层推理失败 | 🟡 中 | 用 `_resolve_bucket_safe` 包装：告警 + 跳过该门控（§8），不抛 |
| 删表后有隐藏引用 | 🟢 低 | `grep` 验收（§7 第 3 项）；全仓引用点已在 §1.4 列全 |
| 现有 `sanity_check` 失效 | 🟢 低 | 改动不触及 `sanity_check` 逻辑；只是补新 case |

**回退**：本批为**单个 commit** ⇒ `git revert <sha>` 一次即可完全回退（无需手工改回 3 处 + 恢复 `macros.py`）。
⚠️ **前提**：先按 §4.2 把前几轮遗留的未提交改动**单独 commit**，否则 revert 会连带回退掉 `resolve_bucket` 本身。

---

## 9. 本轮新增的实测事实（供后续批次参考）

| # | 事实 | 来源 |
|---|---|---|
| 1 | `sanity_check.case_numeric_layer` 的优先级断言**空转**（前件被跳过 ⇒ 激活度全 0 ⇒ 排序=输入顺序） | `diag_fuzzy_bucket_shift_impact.py` §1 |
| 2 | **缺陷门控惰性**：缺陷字段不在 `process_parameter` 里 ⇒ 隶属度恒为 `EPSILON=1e-7` ⇒ 对所有规则是同一常数因子，不参与区分；缺陷严重度的实际筛选在**规则查询层**（`RuleQueryContext.defect_level`） | 同上 §3 + 代码走查 |
| 3 | 3435 条门控引用**全部**可被 `resolve_bucket` 解析（`无法解析 = 0`）⇒ 接线无解析失败风险 | 同上 §2 |
| 4 | 规则级**无彻底失效**：1637 条前后都能命中，6 条前后都不命中 | 同上 §3 |
| 5 | `ALL_LEVEL_WORDS` 里的 6 个多段词（`very_low`/`very_high`/`extremely_*`/`ultra_*`）在静态表里**没有** ⇒ 一旦被使用即 KeyError；接线后自动消除 | `diag_fuzzy_bucket_mapping.py` §3（已按 `is_level_word` 守卫修正误报） |

---

## 10. 待确认

| # | 问题 | 状态 |
|---|---|---|
| 1 | 是否按 §4 顺序执行（先补基准 → 再接线删表 → 再验收）？ | 待拍板 |
| 2 | 是否需要把「接线前 vs 接线后」的推荐 diff 做成一个可交付给业务方的材料？ | 待拍板 |
| 3 | 后续批次是否按 §6.1 顺序推进？ | 待拍板 |
