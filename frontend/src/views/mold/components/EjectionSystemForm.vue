<!-- EjectionSystemForm - 顶出系统子表单（被 MoldForm 引用）：单层无嵌套，由 MoldForm 包裹在 el-card 内，props.ejectionSystem 直接双向绑定，flat items + groupIntoRows 自动分行（6 字段 → 2 行），类型覆盖 input / number / select + radio（plan 准备就绪，当前无字段触发） -->

<template>
  <el-form
    :model="ejectionSystem"
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
          :model="ejectionSystem"
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
  ejectionTypeOptions,
  resetMethodOptions,
} from '@/constants/mold-const'
import FormFieldRenderer from './FormFieldRenderer.vue'

/** props 数据双向绑定：props.ejectionSystem 即 MoldForm.mold_info.ejection_system 的 reactive 引用，直接改属性即同步到 mold_info（v-model="ejectionSystem[prop]"），子组件不创建本地 ref 保持单向数据流 */

const props = defineProps<{
  ejectionSystem: Record<string, any>
}>()

/** 验证规则（与 GatingSystemForm / CoolingSystemForm 一致的架构：可被 MoldForm 统一验证） */
const rules = {}

const formRef = ref<FormInstance>()

/** 字段定义（flat items，6 个字段，4 列 → 自动分行 2 行）：原版有 3 个字段被注释（has_pre_ejection / pre_ejection_stroke / estimated_ejection_force），radio 类型已加入 v-else-if 链，未来启用时解开注释即可，并保持与 mold-const.ts 中 ejectionSystemForm 默认值字段对齐 */

const formItems: FormItem[] = [
  // --- 顶出配置 ---
  { label: '顶出类型', prop: 'ejection_type', type: 'select', options: ejectionTypeOptions },
  { label: '复位方式', prop: 'reset_method', type: 'select', options: resetMethodOptions },
  { label: '顶棍孔直径', prop: 'ejector_rod_hole_diameter', type: 'number', unit: 'mm' },
  { label: '顶棍孔X向间距', prop: 'ejector_rod_hole_spacing_x', type: 'number', unit: 'mm' },
  { label: '顶棍孔Y向间距', prop: 'ejector_rod_hole_spacing_y', type: 'number', unit: 'mm' },
  { label: '顶出行程', prop: 'ejection_stroke', type: 'number', unit: 'mm' },

  // --- 以下字段暂未启用（与原版保持一致，注释保留以备后续扩展）---
]

// 自动分行（4 列布局：6 字段 ÷ 4 列 = 2 行）
const rows = computed(() => groupIntoRows(formItems, { columns: 4 }))

// 暴露给父组件 MoldForm 统一验证
defineExpose({ formRef })
</script>

<style scoped lang="scss">
/* 子组件无特有样式，复用 custom-form 全局样式 */
</style>
