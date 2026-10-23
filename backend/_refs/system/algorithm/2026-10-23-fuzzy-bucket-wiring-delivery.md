># fuzzy 档位取桶 · 第一刀 A 交付说明（接线前 vs 接线后）

> **日期**：2026-10-23
> **范围**：只做「接线 `resolve_bucket` + 同一次删 `HS_MAPPING_DICT`」，不扩展到论域治理 / 元数据标定
> **对应清单**：`backend/_refs/system/algorithm/2026-10-23-fuzzy-implementation-checklist.md`
> **对应规格**：`backend/_refs/system/algorithm/2026-10-23-fuzzy-implementation-design.md`
> **提交**：`4f50bfd`（产品代码）、`6b8c756`（连带修复）、`92db574`（红灯基准）

---

## 0. 一句话结论

档位→桶的映射从**全局静态 3 档表**改成**按字段自己的档位词表**定位。

实测（49 个真实样本，走真实引擎跑两遍）：**推荐的参数集合和条数没变，但每一个参数的推荐强度与优先级都变了**（49/49 样本的推荐值与置信度变化，48/49 样本的排序变化）。

也就是说：**不是"推荐多了/少了"，而是"原来把把握给错了参数"**。

---

## 1. 改了什么

### 1.1 病灶

`backend/process/algorithms/fuzzy/fuzzy_core/models/nets.py` 三处用**全局静态 3 档表**取桶索引：

```python
p_col_idx = self.pre_dict[name]['index'] + HS_MAPPING_DICT[level]
```

`HS_MAPPING_DICT['high'] == 2`，这是**全局 3 档口径**。而现网 **310/311 个字段是 5 档**，`high` 在 5 档词表 `('very_low','low','medium','high','very_high')` 里是**下标 3**。

⇒ 静态桶 2 = 5 档的 **medium**（论域 50% 分位）⇒ **拿"中档"当"高档"判**。

| 档位词 | 旧（静态表） | 新（按字段词表） | 旧口径实际含义 |
|---|---|---|---|
| `low` | 0 | 1 | 判成了 very_low（论域下界） |
| `medium` | 1 | 2 | 判成了 low（25% 分位） |
| `high` | 2 | 3 | **判成了 medium（50% 分位）** |

### 1.2 改动

| 文件 | 改动 |
|---|---|
| `fuzzy_core/models/nets.py` | 三处取桶（IF 前件 / THEN 结论 / NumTsk 前件）改用 `resolve_bucket(lvl, word)`，并按**该字段自己的 `lvl`** 取档位词表 |
| `fuzzy_core/models/nets.py` | 新增 `_resolve_bucket_safe`：解析失败**显式告警 + 跳过该门控**，绝不静默取错桶 |
| `fuzzy_core/macros.py` | **整表删除** `HS_MAPPING_DICT`（保留 `ACTION_MAP` / `LEVEL_NUMBER_TO_BUCKET`，它们是另外两件事） |
| `fuzzy_core/tests/test_nets.py` | 断言改为 `resolve_bucket` 语义 |
| `sanity_check.py` | 新增 **B1~B7** 七个真断言（接线前红灯，接线后全绿） |

**保留的编号轨**：`level1`…`level9` 这类编号词与级数解耦，仍然用 `LEVEL_NUMBER_TO_BUCKET`，永远正确。

---

## 2. 实测影响（真实引擎跑两遍，不是公式推算）

### 2.1 方法

> 脚本：`backend/_dev_refs/diag_fuzzy_bucket_before_after.py`（只读，不写库、不改产品代码）
> 产出：`_dev_refs/_before_after.json`、`_dev_refs/_before_after_out.txt`

与之前的 `diag_fuzzy_bucket_shift_impact.py`（**复刻激活度公式推算**）不同，本脚本：

1. 走真实 service 路径构造 `AlgorithmContext`（命名翻译 / 规则查询 / 缺陷筛选）；
2. monkeypatch `nets.resolve_bucket` 为旧口径 → 跑 `_call_algorithms` = **接线前**；
3. 恢复真实 `resolve_bucket` → 再跑一次 = **接线后**；
4. 逐样本对比 `Recommendation` 列表。

> 样本：49 条 `ProcessParameter`（真实实验数据）；缺陷固定为 `ABERRATION/high`（该组合命中 12 条规则）。

### 2.2 聚合结果（49 样本）

| 指标 | 结果 |
|---|---|
| 异常样本 | 0 |
| **推荐条数变化** | **0 / 49（0%）** —— 前后都是 11 条 |
| **推荐参数集合变化** | **0 / 49（0%）** —— 前后参数完全相同 |
| **推荐排序变化** | **48 / 49（97%）** |
| **同一参数推荐值 / 置信度变化** | **49 / 49（100%）** |
| 接线前有、接线后全没了 | 0 |
| 接线前没有、接线后有 | 0 |

**读法**：接线**没有改变"推荐哪些参数"**，改变的是**"推多少"和"先推谁"**。

### 2.3 典型样本（`parameter_id=1`，缺陷 `ABERRATION/high`）

| 参数 | 接线前 推荐值 / 置信度 | 接线后 推荐值 / 置信度 | 变化解读 |
|---|---|---|---|
| **IV0** | 30.000 / 0.120 | **32.698 / 0.355** | 旧口径几乎不敢动；新口径**最有把握**（排到首位） |
| **IP0** | 84.012 / 0.003 | **85.071 / 0.282** | 旧口径几乎不认；新口径**第二有把握**（88 倍） |
| MBP0 | 5.664 / **0.254** | 4.713 / **0.003** | 旧口径**最有把握**（排首位）；新口径降 77 倍 |
| MSR0 | 59.060 / **0.247** | 59.996 / **0.001** | 同上，降 227 倍 |
| CT | 4.9959 / 0.0011 | 5.0000 / 7.6e-08 | 新口径下 CT 基本不动了 |
| BT | 250.0 / 1.7e-282 | 250.0 / 3.4e-252 | 见 §5 遗留问题 |
| CUSION | 0.0 / 0.0 | 0.0 / 0.0 | 见 §5 遗留问题 |

⇒ **优先级被整体翻转**：旧口径把最高置信度给到 MBP0/MSR0，新口径给到 IV0/IP0。

### 2.4 参数级（49 样本全量）

推荐值/置信度发生变化的参数恰好 4 个，覆盖全部 49 个样本：

| 参数 | 变化样本数 | 方向 |
|---|---|---|
| MBP0 | 49 | 置信度 ↓（0.25 量级 → 0.003 量级） |
| MSR0 | 49 | 置信度 ↓（0.25 量级 → 0.001 量级） |
| IP0 | 49 | 置信度 ↑（0.003 → 0.28） |
| CT | 49 | 置信度 ↓（0.0011 → 7.6e-08） |

### 2.5 与推算结果的差异（重要）

清单 §3.2 用公式推算的结论是「命中规则数 1018 → 715，top-10 换掉 6.4 条，top-1 变 92%」。

**真实引擎跑出来不一样**：推荐条数、参数集合都没变，只有推荐值/置信度/排序变了。

原因（已定位）：

- 引擎用 `net.predict(..., top_k=len(numeric_rules))` ⇒ **不截断**，所有规则都进结果；
- 第四层（结论层，`nets.py` L764-793）**不看激活度**地给每条规则产出结论值；
- `_merge_layer_results` 把同一参数的多条规则的 delta **累加**。

⇒ 激活度（桶）只影响 **delta 的权重** 和 **排序**，不影响"哪些参数出现"。

⚠️ 推算口径的"命中规则数"（activation > 阈值）**没有对应到任何下游行为** —— 因为 `MIN_ACTIVATION_THRESHOLD` 在 TSK 主路径**零引用**。这是遗留问题 D（见 §5）。

---

## 3. 回归基准（B1~B7）

`sanity_check.py` 新增 7 个**能证伪**的断言。接线前红灯、接线后绿灯：

| # | case | 断言 | 接线前 | 接线后 |
|---|---|---|---|---|
| B1 | 5 档 `high` 落位 | x=150 ⇒ 激活度 == 1.0 | ❌ 0.135335 | ✅ **1.000000** |
| B2 | 5 档 `low` 落位 | x=50 ⇒ 激活度 == 1.0 | ❌ 0.135335 | ✅ **1.000000** |
| B3 | `low`/`high` 不重叠 | x=75 ⇒ low 胜出 | ❌ high 胜出 | ✅ **low 胜出（完全反转）** |
| B4 | priority 真断言 | 反转 priority ⇒ 输出顺序必须反转 | ❌ 空转 | ✅ |
| B5 | 3 档向后兼容 | `lvl=3` ⇒ low/medium/high → 0/1/2 | ✅ | ✅ **零影响** |
| B6 | 多段档位词不再崩 | `very_low` 能解析 | ❌ **KeyError** | ✅ |
| B7 | 无元数据门控显式失效 | 缺元数据 ⇒ 激活度 == 0 | ✅ | ✅ |

> 红灯历史保留在 commit `92db574`（先补基准、后接线），可回溯证明"改对了"。

**B5 的含义**：**3 档字段完全不受影响**（静态表本身就是 3 档口径）⇒ 老配置的用户零感知。

---

## 4. 验收结果

| # | 清单 §7 判据 | 结果 |
|---|---|---|
| 1 | `pytest fuzzy_core/tests/` 全绿 | ✅ `test_nets.py` 11/11、`test_macros.py` 6/6 组；`backend/tests/` 5 passed |
| 2 | sanity 全绿且 B1/B2/B3/B6 接线前失败 | ✅（`92db574` 留有红灯历史） |
| 3 | `grep HS_MAPPING_DICT backend/process/` 零命中 | ✅ 产品代码零引用（仅注释中保留历史说明） |
| 4 | 影响面复核 | ✅（§2，`diag_fuzzy_bucket_before_after.py`） |
| 5 | 端到端 diff 材料 | ✅ **本文档**（真实引擎两遍对比） |
| 6 | 诊断脚本仍可运行 | ✅ 14 个脚本迁到只读旧表快照，3 个关键脚本实跑通过 |

---

## 5. 本刀**未**解决、且已确认为真实缺陷的问题

> 这些是「正确实现 fuzzy 算法」的下一批内容，**本刀范围外**。

| # | 问题 | 位置 | 证据 |
|---|---|---|---|
| **D** | **TSK 主路径没有激活度阈值**：`MIN_ACTIVATION_THRESHOLD` 在 `fuzzy_algorithm.py` **零引用**；激活度 ≈0 的规则照样产出推荐 | `nets.py` L764-793 / `fuzzy_algorithm.py` L477-493 | 本次实测 `BT conf=1.7e-282`、`CUSION conf=0.0` 仍出现在推荐列表里 |
| **B** | **`conditions` 取"乘积后非零"而非"连接到的列"**：某门控隶属度恰为 0 时被踢出 ⇒ 该门控被跳过 ⇒ **规则在门控不满足时反而激活** | `nets.py` L748-755 | 代码走查 |
| **K** | **`activation` 语义混乱**：引擎产出的是「归一化激活度 × priority」，却被当 `activation` 塞出；`confidence = Σ(归一化值)/条数` 而归一化值之和恒为 1 ⇒ confidence 恒 ≈ 1/条数 | `fuzzy_algorithm.py` L489-491 / L648 | 本次实测 confidence 出现 1.7e-282 这种量级 |
| **G** | **缺元数据字段走"推测论域"**（lvl=3、论域[0, 现值×2]），45 个字段受影响 | `fuzzy_algorithm.py` L444-451 | 引擎启动时的 warning |
| **C** | 同参数多规则 delta **裸累加**，相反方向不显式标冲突 | `fuzzy_algorithm.py` L610 | 代码走查（业务策略待定） |

---

## 6. 风险与回退

| 风险 | 等级 | 现状 |
|---|---|---|
| 推荐强度/优先级变化 | 🔴 高 | **已量化并交付**（§2）：条数与集合不变，变的是强度与排序；建议业务方按 §2.3 逐参数确认 |
| `resolve_bucket` 抛 `ValueError` 拖垮整层推理 | 🟡 中 | 已用 `_resolve_bucket_safe` 兜住（告警 + 跳过该门控，不抛） |
| 删表后有隐藏引用 | 🟢 低 | 已清零（§4 第 3 项）；14 个诊断脚本已迁到只读快照 |
| 3 档字段用户 | 🟢 低 | B5 证明零影响 |

**回退**：

```bash
git revert 4f50bfd        # 产品代码（只此一个 commit 即可完全回退第一刀）
git revert 6b8c756        # 连带修复（诊断脚本迁移，建议一起回退）
```

⚠️ 无需手工改回 3 处取桶 / 恢复 `macros.py` —— 第一刀是**单个 commit**。

---

## 7. 复现方式

```powershell
cd backend
..\.venv\Scripts\python.exe process\algorithms\fuzzy\sanity_check.py
..\.venv\Scripts\python.exe _dev_refs\diag_fuzzy_bucket_before_after.py --json _dev_refs\_before_after.json
..\.venv\Scripts\python.exe -m pytest process\algorithms\fuzzy\fuzzy_core\tests\ -q
```
