<!-- ProcessActualFeedback - 工艺实测表单 -->
<template>
  <div class="process-actual-feedback">
    <el-form
      :model="local_map"
      label-width="100px"
      size="small"
      class="process-actual-feedback__form"
    >
      <div class="process-actual-feedback__grid">
        <el-form-item
          v-for="item in OBSERVATION_ITEMS"
          :key="item.key"
          :label="item.label"
          class="process-actual-feedback__cell"
        >
          <el-input
            v-model="local_map[item.key]"
            v-number
            :placeholder="`请输入${item.label}`"
            class="process-actual-feedback__input"
          >
            <template #suffix>{{ resolved_units[item.key] }}</template>
          </el-input>
        </el-form-item>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { CycleObservation } from '@/types/optimization'
import { OBSERVATION_ITEMS, STANDARD_UNITS } from '@/constants/observation-order'

/** 机器单位信息子集（完整结构见 constants/machine-const.ts，缺字段回退 STANDARD_UNITS） */
type UnitType = keyof typeof STANDARD_UNITS
type MachineUnitMap = Partial<Record<UnitType, string>>

const props = defineProps<{
  /** v-model 绑定的观察列表 */
  modelValue?: CycleObservation[] | null
  /** 机器单位信息（用于覆盖默认单位）*/
  machine_unit?: MachineUnitMap | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: CycleObservation[]): void
}>()

/** 预计算各观察项单位（机器单位优先，undefined/null/空串视为未提供并回退标准单位） */
const resolved_units = computed<Record<string, string>>(() => {
  const map = props.machine_unit ?? {}
  const result: Record<string, string> = {}
  for (const item of OBSERVATION_ITEMS) {
    const type = item.unit_type as UnitType
    const v = map[type]
    result[item.key] = (v !== undefined && v !== null && v !== '')
      ? v
      : STANDARD_UNITS[type]
  }
  return result
})

/** 内部 map 形态 { param_key: value }（渲染直接 v-model，emit 时转回 CycleObservation[]） */
const local_map = reactive<Record<string, number | null>>(
  Object.fromEntries(OBSERVATION_ITEMS.map(i => [i.key, null])),
)

/** 比较两个 CycleObservation[] 是否等价（避免 v-model 循环） */
function isSameList(
  a: CycleObservation[],
  b: CycleObservation[] | null | undefined,
): boolean {
  if (!b || b.length !== a.length) return false
  const bm = new Map(b.map(o => [o.param_key, o.value]))
  for (const o of a) {
    if (bm.get(o.param_key) !== o.value) return false
  }
  return true
}

/** 从 CycleObservation[] 重建 local_map */
function syncFromExternal(list: CycleObservation[] | null | undefined) {
  for (const k of Object.keys(local_map)) local_map[k] = null
  if (!Array.isArray(list)) return
  for (const o of list) {
    if (o && o.param_key in local_map) {
      local_map[o.param_key] = o.value ?? null
    }
  }
}

/** 外部 v-model → 内部 map（首次 + 切轮次时同步）*/
watch(
  () => props.modelValue,
  (list) => syncFromExternal(list),
  { immediate: true },
)

/** 内部 map 变化 → emit CycleObservation[]（跳过等价的，避免循环）*/
watch(
  () => local_map,
  () => {
    const out: CycleObservation[] = []
    for (const item of OBSERVATION_ITEMS) {
      const v = local_map[item.key]
      if (v !== null && v !== undefined && !Number.isNaN(v)) {
        out.push({ param_key: item.key, value: v })
      }
    }
    if (isSameList(out, props.modelValue)) return
    emit('update:modelValue', out)
  },
  { deep: true },
)
</script>

<style lang="scss" scoped>
/*
 * 2-3 列网格布局：让 4 项观察项填满右栏宽度，避免右侧留白过大
 * - auto-fill 自适应列数（宽屏 3 列、窄屏 1-2 列）
 * - el-form-item 本身是 flex（label + content），能在 grid 单元格内正常工作
 */
.process-actual-feedback {
  &__grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 4px 24px;
  }

  /* el-form-item 默认 mb-22px，在 grid 里偏大，调紧凑一些 */
  &__cell {
    margin-bottom: 8px;
  }

  /* 输入框：占满剩余宽度 */
  &__input {
    width: 100%;
    max-width: 180px;
  }
}
</style>