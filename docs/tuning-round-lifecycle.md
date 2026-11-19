# 调机轮次的数据模型与因果链

> 记录「一轮调机」在库里由什么构成、这些东西什么时候写、彼此的因果关系。
> 口径来源：2026-11-19 与用户的逐轮核对（已拍板，见「决策记录」）。
> 涉及文件：`backend/process/services/parameter_optimize.py`（主）、
> `backend/process/services/tuning.py`、`backend/process/services/condition.py`、
> `backend/process/models/tuning_record.py`、`backend/process/models/recommendation.py`。

## 一句话模型

```
P_N  =  P_{N-1}(base)  +  R(算法推理)
         ↑                      ↓
      R 挂在 P_{N-1} 上      照 R 调 ⇒ P_N

P_N + feedback(P_N)  ⇒  判定 R  ⇒  R.is_adopted   （= P_{N-1} 的建议是否被采纳）
P_N 自己的 R_N       ⇒  由 P_{N+1} 的 feedback 判定 ⇒ P_N 的 adopted
```

⇒ **P_N 同时有两个身份**：它是「P_{N-1} 推理出来的**结果**」，也是「**下一轮**的 base」。
**base 指的是上一轮**（P_{N-1} 是 P_N 的 base）。

## 一轮 P_N 身上挂着什么

| 对象 | 内容 | 写入者 | 写入时机 |
|---|---|---|---|
| `ProcessParameter` P_N | 本轮参数（建它时**同批建 pending TuningRecord**，两者 1:1） | `_create_new_round` | 第 N-1 轮反馈时（与 R 同批） |
| `TuningRecord` | P_N 的试模反馈：缺陷 + 试模评价 | `_record_tuning_round` | 第 N 轮反馈时 |
| `Recommendation` | **针对 P_N 的建议** R_N（照它调 ⇒ P_{N+1}） | `_record_tuning_round`（与 TuningRecord 同锚点） | 第 N-1 轮反馈时（与 P_N 同批） |
| `Recommendation.is_adopted` | R_N 有没有被采纳 | `_settle_recommendation_adoption`（结算父轮那条） | **第 N+1 轮**反馈时 |

⇒ **一轮记录不是同一时刻齐的**：
- 第 N 轮反馈时：P_N + TuningRecord 齐了，但 P_N 的 `is_adopted` 还是默认 `True`（还没人验证）
- 第 N+1 轮反馈时：P_N 的 `is_adopted` 才有真值

⇒ 末轮没有下一轮 ⇒ 永远停在「待验证」⇒ **末轮不显示建议**（末轮产品合格了，本来就不需要建议）。

## Recommendation 的锚点：挂在「被建议的那个参数」上

`Recommendation.process_parameter` 指向**被建议的那个参数**，不是产出它的那一轮。

```
P1 ──算法给建议 R1（50→60）──> P2 ──算法给建议 R2──> P3
```
⇒ R1 针对 P1 ⇒ 挂 **P1**；R2 针对 P2 ⇒ 挂 **P2**。

**为什么这样挂**：语义自洽 ——「P_N 是否被采纳」= 查 P_N 自己的 Recommendation；
采纳状态由**下一轮 feedback** 决定（那时才知道照建议调出来的参数好不好用）⇒ 新建时只置默认 `True`。

**落库实现：一次提交分三段，每段一个锚点**

| 段 | 函数 | 锚点 | 做什么 |
|---|---|---|---|
| 1 | `_settle_recommendation_adoption` | **父轮** P_{N-1} | 结算那条建议的采纳状态：`tuning_result == 'ineffective'` 时查 `process_parameter_id=parent_param.parent_param_id`；`parent_param_id` 为空（第 1 轮无父）⇒ 无可结算 |
| 2 | `_record_tuning_round` | **本轮** P_N | 记录这一轮：参数同步（用户改过的字段）+ TuningRecord（用户反馈）+ Recommendation（算法推荐，`process_parameter=parent_param`） |
| 3 | `_create_new_round` | **下一轮** P_{N+1} | 建 ProcessParameter + 它的 pending TuningRecord（同批，1:1） |

⇒ 三段的动作互不重叠，各自落在**不同轮次**的参数上 ⇒ 拆成三个方法；
第 2 段的三个动作落在**同一个锚点**（P_N）⇒ 合在一个方法里。
- `build_recommendation_suggestion` ⇒ `applied_values=None`
  （落地值在「按建议调整后的那一轮」上，被建议轮的记录里没有；跨轮取会多一次查询
  ⇒ 历史轮次的 `applied_value` 不填，前端按「有则用」处理）
- 回显查询代码**不用改**（按 parameter 关联查 ⇒ 挂哪显示在哪；
  同一 parameter 挂多条时按 created_at 升序覆盖 ⇒ **只取最新一条**）

## is_adopted 的判定口径

**「不采纳」目前只等于「变差」。**

只在 `tuning_result == 'ineffective'` 时置 `False`；
`unchanged`（无变化）、`effective`（改善）、`qualified`（合格）**都保持 `True`**。

理由：`is_adopted` 本义是「**采纳**」（用户照建议改了并采用了），不是「有改善」——
改了没变差也算采纳。所以第 N-1 轮的建议被判「不采纳」的唯一条件是：**照它调出来的 P_N 变差了**。

映射表：`process/services/tuning.py` 的 `TUNING_RESULT_MAP`（唯一真相源）。

## ProcessParameter 的双重身份

1. **工艺参数调整的 base** —— 下一轮的建议都相对它计算；
2. **feedback 的载体** —— TuningRecord 与 ProcessParameter 关联，用户提交的缺陷反馈与
   试模评价落在「这个 parameter」对应的 tuning_record 上。

⇒ base parameter 的同步、feedback 的落库、算法推荐的挂载是**同一件事的三面**
（都落在当前活动轮这一个锚点上）⇒ 合并为单一方法 `_record_tuning_round`
（同一次事务内写 ProcessParameter 字段、它的 TuningRecord、它的 Recommendation）。

**parameter 同步口径**：基于库中原值（`changed_fields` 为空）⇒ 不动；
用户在界面改了字段 ⇒ 同步到库，保证 DB 与用户实际在用的参数一致
（只写真正变化的字段；`tuning-feedback` 不写 ProcessParameter）。

**⚠️ 合并坑（已踩）**：`_record_tuning_round` 里 parameter 段与 tuning_record 段
**互不阻断** —— 用户没改字段是最常见路径，若 parameter 段用 `return` 早退
⇒ 整轮 feedback（缺陷 + 评价 + 训练样本）全部丢失。

**tuning_record 落库口径**：缺陷与效果标签写到**本 parameter 自己**的 TuningRecord
（不写到父轮）：界面上的「第 N 轮」= 参数(N) + 反馈(N)，反馈属于该轮参数自身的试模结果。
记录不存在 ⇒ 补建（业务层保证 1:1，此处兜底）。

## 已知边界

**① 新旧数据混存**：老数据的 Recommendation 挂在产出轮（老口径），新数据挂在被建议轮
⇒ 同一棵树里某轮可能挂两条建议（回显按 parameter 关联后按 created_at 升序覆盖 ⇒ **只显示最新那条**，旧的被盖掉）。
如需统一要写迁移，不在本次范围。

**② 归档轮次不写回参数**：父轮已有评价时，它的参数是「当时实际用的工艺」这一历史事实，
写回会改写归档 ⇒ 跳过（只记 warning）。不影响子轮次（基线已按用户改值覆盖）。

**③ `is_adopted` 与 TuningRecord 不同时刻齐**：见上文「一轮记录不是同一时刻齐的」。

## 决策记录（已拍板）

| # | 决策 | 结论 |
|---|---|---|
| 1 | Recommendation 锚点 | **被建议轮**（用户口径：「我们并无法确定这一轮的 parameter 是否被采纳」⇒ 要能查自己身上那条） |
| 2 | 末轮无建议 | **接受**（用户口径：「末轮如果产品合格了，本身就是不需要建议了」） |
| 3 | `is_adopted` 的「不采纳」 | **只等于 ineffective**（unchanged 也算采纳） |
| 4 | 历史回显的 `applied_value` | **不填**（跨轮取值不值那个查询成本） |
| 5 | `_record_tuning_round` 的早退 | parameter 段**不得** early return（会丢整轮 feedback 与推荐） |
| 6 | 落库函数的划分粒度 | **按锚点分三段**（结算父轮 / 记录本轮 / 建下一轮），不按「操作对象相同」合并 |

## ⚠️ 一条已推翻的错误结论（勿再沿用）

**「现状的 `is_adopted` 差一轮」是错的**（2026-11-18 提出，2026-11-19 已推翻）。

两种锚点下 `is_adopted` 的**判定对象与判定时点完全等价**：
都是「第 N 轮反馈时，确定影响 P_N 的那条建议」。
差别只在**回显归属轮次**与 `applied_value` 的取值来源。

## 相关记忆

- 调机轮次的参数-反馈配对语义与落库位置约定
- 上一轮工艺效果评价（tuning_result）的粒度与落库口径
- 合格态不是流程闸门：service 层不预判合格，交由算法空跑
