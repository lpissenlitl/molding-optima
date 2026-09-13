/**
 * useConditionDerived - 工艺条件派生计算 composable
 *
 * 职责（从 ProcessCondition 中提取）：
 *   1. 索引计算：shot_index / injection_index / product_index（0 索引）
 *   2. 数量判断：shot_count / unit_count / cavity_count + 多射/多腔标识
 *   3. 实体存在性：hasMold / hasMachine / hasPolymer
 *   4. 派生对象：按索引从数据源（mold_info / machine_info）切片
 *      - gatingDerived: 当前射次的浇注系统
 *      - currentCavity: 当前制品（shot + product 索引）
 *      - currentGate: 当前浇口（cavity.gates[0]）
 *      - injectionUnitDerived: 当前射台
 *   5. 显示用 1 索引
 *
 * 用法：
 *   const condition = reactive<Condition>(props.processCondition ?? {})
 *   const { gatingDerived, currentCavity, ... } = useConditionDerived(condition)
 *
 * 设计原则：
 *   - 接受 reactive 对象（不是 Ref），内部用 condition.xxx 直接访问
 *   - 所有派生都是 computed，调用方在模板中直接用即可
 *   - 不缓存中间状态（避免响应性陷阱），全部走 computed 链
 *   - 容错：缺失索引/缺失数据 返回 undefined，由调用方决定如何降级
 *
 * 索引约定（与 ProcessCondition 内部一致）：
 *   - 后端 shot_index / injection_index / product_index 是 0 索引
 *   - UI 显示用 1 索引（更友好），由 shotIndexDisplay 等 computed 转换
 */
import { computed, type ComputedRef } from 'vue'
import type {
  Condition,
  GatingSystemSummary,
  CavitySummary,
  GateSummary,
  InjectionUnitSummary,
} from '../types'

export interface ConditionDerived {
  // === 索引（0 索引，从 condition.* 直接取） ===
  shotIndex: ComputedRef<number>
  injectionIndex: ComputedRef<number>
  productIndex: ComputedRef<number>

  // === 计数与判断 ===
  shotCount: ComputedRef<number>
  unitCount: ComputedRef<number>
  cavityCount: ComputedRef<number>
  hasMultipleShots: ComputedRef<boolean>
  hasMultipleUnits: ComputedRef<boolean>
  hasMultipleProducts: ComputedRef<boolean>

  // === 实体存在性 ===
  hasMold: ComputedRef<boolean>
  hasMachine: ComputedRef<boolean>
  hasPolymer: ComputedRef<boolean>

  // === 派生对象（按索引切片） ===
  gatingDerived: ComputedRef<GatingSystemSummary | undefined>
  /** 当前射次浇注系统下的所有 cavity(一次注射成型,所有腔同时成型,平铺展示) */
  cavities: ComputedRef<CavitySummary[]>
  /** 单个 cavity 按索引切片(保留向后兼容,部分调用方仍按索引取) */
  currentCavity: ComputedRef<CavitySummary | undefined>
  currentGate: ComputedRef<GateSummary | undefined>
  injectionUnitDerived: ComputedRef<InjectionUnitSummary | undefined>

  // === 1 索引显示值 ===
  shotIndexDisplay: ComputedRef<number>
  injectionIndexDisplay: ComputedRef<number>
  productIndexDisplay: ComputedRef<number>
}

export function useConditionDerived(condition: Condition): ConditionDerived {
  // === 索引（0 索引，缺失则 0） ===
  const shotIndex = computed<number>(() => condition.shot_index ?? 0)
  const injectionIndex = computed<number>(() => condition.injection_index ?? 0)
  const productIndex = computed<number>(() => condition.product_index ?? 0)

  // === 计数（数据源缺失时默认 1） ===
  const shotCount = computed<number>(() => condition.mold_info?.shot_count ?? 1)
  const unitCount = computed<number>(() => condition.machine_info?.unit_count ?? 1)

  // === 浇注系统派生（按 shot_index 切片） ===
  const gatingDerived = computed<GatingSystemSummary | undefined>(() => {
    const systems = condition.mold_info?.gating_systems ?? []
    if (systems.length === 0) return undefined
    const idx = Math.min(shotIndex.value, systems.length - 1)
    return systems[idx]
  })

  // === 当前 cavity（按 shot + product_index 切片） ===
  const currentCavity = computed<CavitySummary | undefined>(() => {
    const cavities = gatingDerived.value?.cavities ?? []
    if (cavities.length === 0) return undefined
    const idx = Math.min(productIndex.value, cavities.length - 1)
    return cavities[idx]
  })

  // === cavity 列表 + 数量 + 多制品判断 ===
  const cavities = computed<CavitySummary[]>(() => gatingDerived.value?.cavities ?? [])
  const cavityCount = computed<number>(() => cavities.value.length)
  const hasMultipleProducts = computed<boolean>(() => cavities.value.length > 1)

  // === 当前浇口（cavity.gates[0]，取第一个浇口） ===
  // 工艺上 cavity 可对应多个 gate（不同形状），但工艺条件展示通常用主浇口
  // 如需扩展可加 gateIndex，类似 product_index
  const currentGate = computed<GateSummary | undefined>(() => {
    return currentCavity.value?.gates?.[0]
  })

  // === 射台派生（按 injection_index 切片） ===
  const injectionUnitDerived = computed<InjectionUnitSummary | undefined>(() => {
    const units = condition.machine_info?.injection_units ?? []
    if (units.length === 0) return undefined
    const idx = Math.min(injectionIndex.value, units.length - 1)
    return units[idx]
  })

  // === 多射/多射台判断（数据源缺失时按 1 处理，即单射/单台） ===
  const hasMultipleShots = computed<boolean>(() => shotCount.value > 1)
  const hasMultipleUnits = computed<boolean>(() => unitCount.value > 1)

  // === 实体存在性 ===
  const hasMold = computed<boolean>(() => !!condition.mold_info)
  const hasMachine = computed<boolean>(() => !!condition.machine_info)
  const hasPolymer = computed<boolean>(() => !!condition.polymer_info)

  // === 1 索引显示 ===
  const shotIndexDisplay = computed<number>(() => shotIndex.value + 1)
  const injectionIndexDisplay = computed<number>(() => injectionIndex.value + 1)
  const productIndexDisplay = computed<number>(() => productIndex.value + 1)

  return {
    // 索引
    shotIndex,
    injectionIndex,
    productIndex,
    // 计数
    shotCount,
    unitCount,
    cavityCount,
    hasMultipleShots,
    hasMultipleUnits,
    hasMultipleProducts,
    // 实体存在
    hasMold,
    hasMachine,
    hasPolymer,
    // 派生对象
    gatingDerived,
    cavities,
    currentCavity,
    currentGate,
    injectionUnitDerived,
    // 1 索引显示
    shotIndexDisplay,
    injectionIndexDisplay,
    productIndexDisplay,
  }
}