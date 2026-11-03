# 智能调机页 · 工艺参数变更高亮的参照基准语义调整

- 日期：2026-10-28
- 影响文件：`frontend/src/views/process/optimization/pages/OptimizationCreate.vue`
- 关联组件：`frontend/src/views/process/shared/SettingProcess.vue`（**未改动**，组件本身无问题）
- 性质：语义变更 + 实现替换（不改高亮样式、不改比较算法）

---

## 1. 问题现象

用户报告两件事：

1. 点「获取优化工艺」拿到新参数后，**工艺参数表没有突出显示变更部分**；
2. 切换调机轮次时，每一轮应当「基于上一轮的参数变更」突出显示，但实际不是。

---

## 2. 根因：参照基准取错了对象

### 2.1 旧实现

`OptimizationCreate.vue` 维护一个 `originalParameter` ref，语义是「**进入该 round 那一刻的 parameter 快照**」：

```js
watch(activeRound, (newRound) => {
  if (isRestoring) return
  if (newRound?.parameter) {
    originalParameter.value = JSON.parse(JSON.stringify(newRound.parameter))
  } else {
    originalParameter.value = null
  }
}, { immediate: true })
```

### 2.2 为什么优化轮永远不高亮

两条填充路径的时序不同：

| 路径 | 代码 | watch 是否触发 | 结果 |
|---|---|---|---|
| 首轮「获取初始工艺」 | `applyInferResultToForm` **原地改** `activeRound.value.parameter` | ❌ 不触发（computed 返回的引用没变） | `originalParameter` 保持空模板 ⇒ 从空到有值 ⇒ **全表高亮** |
| 优化轮「获取优化工艺」 | `getOptimizedProcess` **先填后切**：`newRound.parameter = …` → `push` → 改 `active_round_id` | ✅ 触发，且触发时 `newRound.parameter` **已是新值** | `originalParameter` = 新参数 ⇒ **参照物 = 显示值 ⇒ 零差异 ⇒ 不高亮** |

即：**只有「原地填充」的首轮会高亮，「新建轮次」的优化轮永远不会高亮** —— 与观察到的现象完全一致。

### 2.3 更本质的问题

即便改成「新建轮次时先填后切」的顺序，只要参照物是「进入该 round 时的快照」，它就**永远等于该轮自己的最终值** ⇒ 差异恒为 0。

> **参照物必须来自轮次之外**，也就是上一轮。

---

## 3. 语义决策（用户 2026-10-28 拍板）

| # | 决策点 | 结论 |
|---|---|---|
| 1 | 参照基准 | **参照上一轮的工艺参数**（第 N 轮 ⇒ 第 N-1 轮） |
| 2 | 首轮（初始工艺）没有上一轮 | **不高亮**（返回 null） |
| 3 | 是否区分「算法建议改动」与「人工改动」 | **不区分**，统一参照上一轮，只要与上一轮不同就高亮 |

### 与后端语义的一致性

后端 `parameter_optimize.py::_apply_recommendations_to_baseline` 的口径就是
**`new_parameter = baseline（上一轮） + 推荐值`**。前端「参照上一轮」与之同构，
所以高亮出来的差异 **就是** 本轮算法实际改动的那几个字段。

---

## 4. 实现：改为派生（computed），不再 watch 维护

```js
const originalParameter = computed(() => {
  const idx = form.rounds.findIndex((r) => r.id === form.active_round_id)
  if (idx <= 0) return null
  const prev = form.rounds[idx - 1]
  if (!prev?.parameter) return null
  // 深拷贝：参照物必须是快照，不能与上一轮对象共享引用
  return JSON.parse(JSON.stringify(prev.parameter))
})
```

### 为什么从 ref+watch 换成 computed

| 维度 | 旧（ref + watch） | 新（computed 派生） |
|---|---|---|
| 参照物来源 | 进入 round 时的快照 | 上一轮 round 的 parameter |
| 与显示值错位 | 必然错位（优化轮恒等） | 不可能（参照物来自轮次之外） |
| 切轮次同步 | 靠 watch 触发，依赖 `isRestoring` 标志 | 自动重算，无需标志 |
| 刷新草稿 | 需把 `originalParameter` 一起持久化再恢复 | **无需持久化**（rounds 恢复即自动重算） |
| 人工改参数后 | 参照物需特殊维护 | 参照物不受影响（本轮改的是当前轮，上一轮是只读参照） |

### 连带清理

- 删除 `watch(activeRound, …)`
- 删除 `isRestoring` 标志
- `persistDraft()` 不再保存 `originalParameter`；`restoreDraft()` 不再恢复它
  （旧缓存里残留的 `originalParameter` 字段被忽略，无害）
- `nextTick` 随之从 vue import 中移除（确认全文再无其他使用）

### 组件侧无需改动

`SettingProcess.vue` 的高亮实现（`isFieldChanged(path)`）本身是正确的：

- 路径取值兼容多位数索引（`decompress_table_data[10].pressure`）
- 空值归一化：`null / undefined / ''` 互为「空」（「有值 → 空」也算变更）
- 数值容差 `0.0001`；`0` 不视为空

`originalProcess` prop 收到 `null` 时，`isFieldChanged` 首行 `if (!this.original_process) return false`
⇒ **首轮自动不高亮**，无需额外开关。

---

## 5. 行为对照表

| 场景 | 参照物 | 预期表现 |
|---|---|---|
| 第 0 轮（初始工艺） | null | 不高亮 |
| 第 1 轮（优化工艺） | 第 0 轮 parameter | 高亮本轮相对初始工艺的差异 |
| 第 2 轮 | 第 1 轮 parameter | 高亮本轮相对上一轮的差异 |
| 第 0 轮人工改参数后点「获取优化工艺」 | 第 0 轮**改后**的值 | 只高亮**算法真正改动**的字段（人工改动已在基线里，不重复标） |
| 在第 N 轮人工改参数 | 上一轮 | 该改动也会标出（统一口径，不区分来源） |
| 刷新页面恢复草稿 | 由 rounds 派生 | 与刷新前一致 |

---

## 6. 验证状态

| 项 | 状态 |
|---|---|
| `npm run type-check`（vue-tsc --noEmit） | ✅ EXITCODE=0 |
| 页面端到端实测（浏览器走完初始工艺 → 优化工艺 → 切轮次） | ⏳ **未执行**（需人工在页面上确认） |

### 人工验证清单

1. 打开智能调机页 → 「获取初始工艺」→ 切到第 1 轮：**参数表无橙色高亮**
2. 填缺陷反馈 → 「获取优化工艺」→ 自动切到第 2 轮：**被改动的单元格为橙色**
   （`.field-changed` 背景 `#fff7e6` / 文字 `#fa8c16`）
3. 切回第 1 轮：无高亮；切回第 2 轮：高亮恢复
4. 再跑一次「获取优化工艺」生成第 3 轮：高亮应只反映第 2 轮 → 第 3 轮的差异

---

## 7. 顺带发现（**本次未改**，待决策）

`previousSuggestion`（「上一轮调整建议」块）是**全局 ref**，不随 `active_round_id` 切换：

- `getOptimizedProcess` 里把它设为刚 infer 出来的建议（`source_round_id` = 上一轮 id）
- 切到别的轮次时它不变 ⇒ 显示的始终是「最后一次 infer 的建议」，
  而不是「当前轮次对应的上一轮建议」

与本次的参照基准语义是同一类问题（都与轮次脱钩），但属独立功能点，
是否一并调整由业务决定。

---

## 8. 关联文档

- 后端契约侧：`backend/_refs/system/algorithm/2026-10-22-optimize-contract-and-fuzzy-engine-review.md` §13
  （D1 flat 契约统一 —— 本次高亮能生效的前提：`new_parameter` 已是 flat 且已回填前端）
- 前端接口集成：`frontend/_refs/module/process/process-get-optimized-frontend-integration-2026-09-23.md`
