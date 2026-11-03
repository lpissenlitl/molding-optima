# expert `gate_shape` 取值域统一 —— 独立批次记录（待排期）

> **日期**：2026-10-27
> **归属**：模糊推理重构收尾 · expert 基线定性（对应 `2026-10-27-fuzzy-post-refactor-review.md` §11.3 ③ / §11.6）
> **状态**：**批次记录，本轮不动代码**（用户已明确：本项单独排一批）
> **一句话结论**：spec 用的是**侧浇口体系**的形状词（`圆形`/`矩形`），而库里实际存的是**热流道/点浇口体系**的形状词（`圆点`）；
> 两套体系并存且 ORM 无 `choices` 约束 ⇒ 一旦出现「侧浇口 + 圆点」，尺寸字段**永不判必填**（漏检），
> 极端情况下保压时间会**静默退回下限 2.0s**。当前库无「侧浇口」⇒ 暂不触发。

---

## 1. 现象与事实

| # | 环节 | 事实 | 位置 |
|---|---|---|---|
| 1 | ORM | `gate_shape = models.CharField(null=True, max_length=20, verbose_name="浇口形状")` —— **可空、自由文本、无 `choices`** | `masterdata/models/mold.py:203` |
| 2 | ORM | `gate_type = models.CharField(null=True, max_length=100, verbose_name="浇口类型")` —— 同样**自由文本、无 `choices`** | `masterdata/models/mold.py:204` |
| 3 | spec | `gate_shape`：`'condition': '条件必填'`，`condition_when: {'gate_type': '侧浇口'}` | `expert/specs.py::MOLD_INFO_SPEC` |
| 4 | spec | `gate_radius`：`condition_when: {'gate_type': '侧浇口', 'gate_shape': '圆形'}` | 同上 |
| 5 | spec | `gate_length` / `gate_width`：`condition_when: {'gate_type': '侧浇口', 'gate_shape': '矩形'}` | 同上 |
| 6 | 库现状（实测） | `Gate` 4 条，`gate_shape` **全为 `圆点`**；`gate_type` 为 `针阀式热浇口` / `点浇口` / `热针点浇口` ⇒ **当前无「侧浇口」** | 查库 |
| 7 | 数据写入方 | `init_demo.py` 写热流道 / 点浇口数据时固定 `gate_shape="圆点"` + `diameter`（注释：「Gate 关键尺寸采用圆点形状(diameter)」） | `bootstrap/management/commands/init_demo.py:397 / 425 / 450 / 478 / 522 / 562 / 578 / 615` |

---

## 2. 两套形状词汇体系并存（问题本质）

| 体系 | 形状词 | 尺寸字段 | 出现在哪 |
|---|---|---|---|
| **A. 侧浇口体系** | `圆形` / `矩形` | `gate_radius`（圆）/ `gate_length` + `gate_width`（矩形） | **spec 的 `condition_when` 硬编码** |
| **B. 热流道 · 点浇口体系** | `圆点` | `diameter`（单个直径） | **库里的实际数据** + `init_demo.py` |

⇒ 这**不是单纯的取值写错**，而是**两套几何模型并存**：
体系 B 用「一个直径」描述点浇口，体系 A 用「半径 / 长×宽」描述侧浇口。
`gate_shape` 一个字段承载了两套语义，spec 只按体系 A 判定。

### 2.1 一个容易被忽略的事实：计算字段与形状无关

快照层 `gate_radius` 是**计算字段**（`spec.attr_name=None`）：

```python
# parameter_initialize.py:274-282
if mold_info.get('gate_radius') is None:
    gate = data_sources.get('Gate') or {}
    if gate.get('diameter') is not None:
        mold_info['gate_radius'] = gate['diameter'] / 2
    elif gate.get('outer_diameter') is not None:
        mold_info['gate_radius'] = gate['outer_diameter'] / 2
```

⇒ 只要 `Gate.diameter` / `outer_diameter` 有值，**即便 `gate_shape='圆点'`**，`gate_radius` 也会被算出来。
⇒ 所以「侧浇口 + 圆点」在**多数情况下不会立刻崩**，而是走到下面的**静默退化**。

---

## 3. 风险推演（按严重度排序）

| 级别 | 场景 | 后果 |
|---|---|---|
| **P1 · 漏检** | `gate_type='侧浇口'` 且 `gate_shape='圆点'` | `gate_radius` / `gate_length` / `gate_width` **永不判必填** ⇒ 几何缺失无人拦截 |
| **P0 · 静默数值错** | P1 之上，且 `Gate` 表**同时**没有 `diameter` / `outer_diameter` | `_calc_hold_time` 的侧浇口分支拿不到面积 ⇒ `return time_min`（**2.0s**）⇒ 保压时间严重偏小，**不报错、不留痕** |
| **P2 · 静默数值错（反向）** | `gate_shape='矩形'` 但只填了 `diameter` | `gate_length`/`gate_width` 判必填 ⇒ 400（**显式失败**，可接受） |
| **P3 · 口径漂移** | 自由文本 ⇒ 用户可填任意值（`圆形` / `圆型` / `circle`） | `condition_when` 静默不成立 ⇒ 同 P1 漏检 |

> `_calc_hold_time`（`algorithm_engine.py:2597-2606`）：
> ```python
> elif gate_type == "侧浇口":
>     gate_radius = prod.get('gate_radius'); gate_length = ...; gate_width = ...
>     if gate_radius:      gate_area = HSO_PI * (gate_radius ** 2)
>     elif gate_length and gate_width: gate_area = gate_length * gate_width
>     else:                return time_min        # ← 静默退化点
> ```

**当前风险等级：低** —— 库里 4 条 `Gate` 全是 `圆点`，且 `gate_type` **无「侧浇口」** ⇒ 条件必填分支根本没进。

---

## 4. 候选口径（**需业务拍板**）

| 方案 | 内容 | 优点 | 缺点 | 适用 |
|---|---|---|---|---|
| **甲** | spec 判定值改为**兼容两套**：`gate_shape ∈ {'圆形', '圆点'}` 都要求 `gate_radius` | 改动最小（1 处 `condition_when`）⇒ 立刻消除 P1 漏检 | 体系 B 的 `圆点` 没有「矩形」概念 ⇒ 矩形分支仍悬空；P3 自由文本仍在 | **推荐作为止血** |
| **乙** | ORM 加 `choices` + 数据清洗，把取值域收敛到**唯一一套** | 从数据层根治，P3 一并消除 | 需 migration + 存量清洗 + 前端联动；且**必须先定「哪一套是正解」** | 长期正解（与 ② 的方案 A 合并做） |
| **丙** | 拆字段：`gate_shape`（形状：圆形/矩形/圆点）+ 独立的尺寸字段组 | 语义最清晰，两套体系各自表达 | 改动面最大（ORM + spec + 快照层 + 算法层 + 前端） | 长期，可与乙并行推进 |
| **丁** | 不动 | 零成本 | P0/P1/P3 全部保留 | 仅在「短期不会有侧浇口」时可接受 |

**推荐路径**：**先甲止血（1 处 `condition_when`，消除漏检），再走乙收敛取值域**（与 ② 的 ORM `choices` 批次合并）。

---

## 5. 批次范围与步骤（**待排期，本轮不执行**）

| 步 | 动作 | 落点 | 前置 |
|---|---|---|---|
| 0 | **业务拍板**：侧浇口体系用哪套词？`圆点` 是否要并入 `圆形`？矩形如何表达？ | — | 必需 |
| 1 | 止血（方案甲）：`gate_radius` / `gate_length` / `gate_width` 的 `condition_when` 兼容两套词 | `expert/specs.py::MOLD_INFO_SPEC` | 步 0 |
| 2 | ORM 收敛：`Gate.gate_shape` / `gate_type` 加 `choices` + 决定是否去 `null=True` | `masterdata/models/mold.py` | 步 0 |
| 3 | 生成 Django migration | — | 步 2 |
| 4 | 存量数据清洗（当前 4 条 `圆点`：确认去留） | 一次性脚本，**用完即删** | 步 2 |
| 5 | spec 与算法层同步（若取值词变更，`_calc_hold_time` 的分支判定需一并核对） | `expert/specs.py` / `expert/algorithm_engine.py` | 步 1 |
| 6 | 测试夹具同步（本轮 B 已把 10 个文件的 `gate_shape` 置为 `'圆形'`，届时需按新词调整） | `expert/tests/*.py` | 步 5 |
| 7 | 查库复验 + 回归（expert 13 failed 不增；fuzzy 41 passed 不变） | — | 步 6 |

---

## 6. 验收判据

| 项 | 判据 |
|---|---|
| 契约层 | `gate_type='侧浇口'` 时，无论 `gate_shape` 取体系 A 还是体系 B 的词，**至少有一个尺寸字段被判必填** |
| 算法层 | 侧浇口分支拿不到任何尺寸时，**不得静默返回 `time_min`**（要么显式报错，要么走有记录的兜底） |
| 数据层 | `Gate.gate_shape` / `gate_type` 的取值集合被 `choices` 约束，且**存量全部合法** |
| 回归 | `pytest process/algorithms/expert/tests -q`（当前 13 failed / 64 passed）**不得新增失败**；`pytest process/algorithms/fuzzy tests -q` 保持 **41 passed** |

---

## 7. 与本轮已完成工作的关系

本轮 B 批次给 10 个测试夹具补的 `gate_shape` 统一取值 **`'圆形'`**（与 `gate_type='侧浇口'` 自洽），
是**按 spec 现有判定**补齐的，**不代表数据层已统一到该词**。
⇒ 本批次的步 6 需要回头核对这些夹具取值是否与新词表一致。
