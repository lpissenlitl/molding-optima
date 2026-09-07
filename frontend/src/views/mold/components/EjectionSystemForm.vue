<!--
  EjectionSystemForm - 顶出系统子表单（被 MoldForm 引用）

  路由：无（子组件）

  设计要点：
  - 单层无嵌套（与 CoolingSystemForm 风格一致）
  - 由 MoldForm 包裹在 el-card 内使用，故不含 page-header / form-actions / loaded
  - 数据通过 props.ejectionSystem 直接双向绑定（修改 reactive 对象属性即可同步到 mold_info）
  - 数据：flat items 数组 + groupIntoRows 自动分行（6 字段 → 2 行）
  - 类型覆盖：input / number / select + radio（plan 准备就绪，当前无字段触发）
-->
<template>
  <el-form
    :model="ejectionSystem"
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

        <!-- 常规字段 -->
        <el-form-item
          v-else
          :label="item.label"
          :prop="item.prop"
        >
          <!-- input：纯文本 -->
          <el-input
            v-if="item.type === 'input'"
            v-model.trim="ejectionSystem[item.prop!]"
            :placeholder="getPlaceholder(item)"
            :disabled="getDisabled(item)"
          >
            <template #suffix v-if="item.unit">{{ item.unit }}</template>
          </el-input>

          <!-- number / integer：v-number 限制小数位 -->
          <el-input
            v-else-if="item.type === 'number' || item.type === 'integer'"
            v-model.trim="ejectionSystem[item.prop!]"
            v-number="getPrecision(item)"
            :placeholder="getPlaceholder(item)"
            :disabled="getDisabled(item)"
          >
            <template #suffix v-if="item.unit">{{ item.unit }}</template>
          </el-input>

          <!-- select：单选下拉 -->
          <el-select
            v-else-if="item.type === 'select'"
            v-model="ejectionSystem[item.prop!]"
            :placeholder="getPlaceholder(item)"
            :disabled="getDisabled(item)"
            clearable
            filterable
            allow-create
          >
            <el-option
              v-for="(opt, oIdx) in item.options"
              :key="oIdx"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>

          <!-- radio：布尔单选（是/否按钮组）-->
          <el-radio-group
            v-else-if="item.type === 'radio'"
            v-model="ejectionSystem[item.prop!]"
            :disabled="getDisabled(item)"
          >
            <el-radio-button :label="true">是</el-radio-button>
            <el-radio-button :label="false">否</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-col>
    </el-row>
  </el-form>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { groupIntoRows } from '@/utils/form-layout'
import {
  getPlaceholder,
  getDisabled,
  getPrecision,
} from '@/utils/form-helper'
import type { FormItem } from '@/utils/form-types'
import {
  ejectionTypeOptions,
  resetMethodOptions,
} from '@/constants/mold-const'

/**
 * props 数据双向绑定说明：
 * - props.ejectionSystem 是 MoldForm.mold_info.ejection_system 的引用（reactive 对象）
 * - 直接修改属性会同步到 mold_info（v-model="ejectionSystem[prop]" 生效）
 * - 这是当前 MoldForm 现状，子组件不创建本地 ref，保持单向数据流
 */
const props = defineProps<{
  ejectionSystem: Record<string, any>
}>()

/**
 * 字段定义（flat items，6 个字段，4 列布局 → 自动分行 2 行）
 *
 * 注：原版有 3 个字段被注释（has_pre_ejection / pre_ejection_stroke / estimated_ejection_force）
 * - radio 类型已加到 v-else-if 链，未来启用时只需解开注释
 * - 保持与 mold-const.ts 中 ejectionSystemForm 默认值字段对齐
 */
const formItems: FormItem[] = [
  // --- 顶出配置 ---
  { label: '顶出类型', prop: 'ejection_type', type: 'select', options: ejectionTypeOptions },
  { label: '复位方式', prop: 'reset_method', type: 'select', options: resetMethodOptions },
  { label: '顶棍孔直径', prop: 'ejector_rod_hole_diameter', type: 'number', unit: 'mm' },
  { label: '顶棍孔X向间距', prop: 'ejector_rod_hole_spacing_x', type: 'number', unit: 'mm' },
  { label: '顶棍孔Y向间距', prop: 'ejector_rod_hole_spacing_y', type: 'number', unit: 'mm' },
  { label: '顶出行程', prop: 'ejection_stroke', type: 'number', unit: 'mm' },

  // --- 以下字段暂未启用（与原版保持一致，注释保留以备后续扩展）---
  // { label: '是否有预顶出', prop: 'has_pre_ejection', type: 'radio' },
  // { label: '预顶出行程', prop: 'pre_ejection_stroke', type: 'integer', unit: 'mm' },
  // { label: '推荐顶出力', prop: 'estimated_ejection_force', type: 'integer', unit: 'kN' },
]

// 自动分行（4 列布局：6 字段 ÷ 4 列 = 2 行）
const rows = computed(() => groupIntoRows(formItems, { columns: 4 }))
</script>

<style scoped lang="scss">
/* 子组件无特有样式，复用 custom-form 全局样式 */
</style>
