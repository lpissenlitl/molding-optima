<!--
  CoolingSystemForm - 冷却系统子表单（被 MoldForm 引用）

  路由：无（子组件）

  设计要点：
  - 单层无嵌套（与 GatingSystemForm 不同）
  - 由 MoldForm 包裹在 el-card 内使用，故不含 page-header / form-actions / loaded
  - 数据通过 props.coolingSystem 直接双向绑定（修改 reactive 对象属性即可同步到 mold_info）
  - 数据：flat items 数组 + groupIntoRows 自动分行
  - 类型覆盖：input / integer / select / number-select + divider
-->
<template>
  <el-form
    :model="coolingSystem"
    :rules="rules"
    ref="formRef"
    class="custom-form"
    label-width="120px"
  >
    <el-row
      v-for="(row, rIdx) in rows"
      :key="`row_${rIdx}`"
      :gutter="24"
    >
      <el-col
        v-for="(item, iIdx) in row"
        :key="`field_${rIdx}_${iIdx}`"
        :span="item.span"
      >
        <!-- divider 分组标题 -->
        <el-divider
          v-if="item.type === 'divider'"
          content-position="left"
          class="custom-form__divider"
        >
          {{ item.label }}
        </el-divider>

        <!-- 常规字段：FormFieldRenderer 统一渲染 -->
        <FormFieldRenderer
          v-else
          :item="item"
          :model="coolingSystem"
        />
      </el-col>
    </el-row>
  </el-form>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { FormInstance } from 'element-plus'
import { groupIntoRows } from '@/utils/form-layout'
import type { FormItem } from '@/utils/form-types'
import {
  coolingTypeOptions,
  coolingChannelDiameterOptions,
  coolingFittingTypeOptions,
} from '@/constants/mold-const'
import FormFieldRenderer from './FormFieldRenderer.vue'

/**
 * props 数据双向绑定说明：
 * - props.coolingSystem 是 MoldForm.mold_info.cooling_system 的引用（reactive 对象）
 * - 直接修改属性会同步到 mold_info（v-model="coolingSystem[prop]" 生效）
 * - 这是当前 MoldForm 现状，子组件不创建本地 ref，保持单向数据流
 */
const props = defineProps<{
  coolingSystem: Record<string, any>
}>()

/**
 * 验证规则（与 GatingSystemForm 一致的架构：可被 MoldForm 统一验证）
 * - 当前未定义任何必填规则，后续按业务需求补充
 */
const rules = {}

const formRef = ref<FormInstance>()

/**
 * 字段定义（flat items，按 span=6 自动分行）
 * - divider 自动 span=24，单独占一行
 * - type=integer → v-number=0；type=select → 普通下拉；type=number-select → select + v-number
 */
const formItems: FormItem[] = [
  // --- 型腔（定模） ---
  { label: '前模（定模）', type: 'divider' },
  { label: '型腔冷却类型', prop: 'cooling_cavity_type', type: 'select', options: coolingTypeOptions },
  { label: '冷却回路数量', prop: 'cooling_cavity_circuit_count', type: 'integer', unit: '组' },
  { label: '冷却管道直径', prop: 'cooling_cavity_pipe_diameter', type: 'number-select', unit: 'mm', options: coolingChannelDiameterOptions },
  { label: '水路接口类型', prop: 'cooling_cavity_fitting_type', type: 'select', options: coolingFittingTypeOptions },
  { label: '水路接口数量', prop: 'cooling_cavity_fitting_count', type: 'integer', unit: '个' },

  // --- 型芯（动模） ---
  { label: '后模（动模）', type: 'divider' },
  { label: '型芯冷却类型', prop: 'cooling_core_type', type: 'select', options: coolingTypeOptions },
  { label: '冷却回路数量', prop: 'cooling_core_circuit_count', type: 'integer', unit: '组' },
  { label: '冷却管道直径', prop: 'cooling_core_pipe_diameter', type: 'number-select', unit: 'mm', options: coolingChannelDiameterOptions },
  { label: '水路接口类型', prop: 'cooling_core_fitting_type', type: 'select', options: coolingFittingTypeOptions },
  { label: '水路接口数量', prop: 'cooling_core_fitting_count', type: 'integer', unit: '个' },
]

// 自动分行（4 列布局，divider 自动占满一行）
const rows = computed(() => groupIntoRows(formItems, { columns: 4 }))

// 暴露给父组件 MoldForm 统一验证
defineExpose({ formRef })
</script>

<style scoped lang="scss">
/* 子组件无特有样式，复用 custom-form 全局样式 */
</style>