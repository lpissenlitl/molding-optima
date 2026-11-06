<!-- FormFieldRenderer - 通用表单字段渲染器：抽离 input / number / integer / select / radio 的渲染逻辑，避免在 GatingSystemForm / GatingCavityPanel 等多处重复 v-else-if 链；由 :item（字段定义）+ :model（响应式数据对象）驱动，v-model 经 item.prop 索引到 model[prop] -->

<template>
  <el-form-item
    :label="item.label"
    :prop="item.prop"
    :label-width="labelWidth"
    :required="item.required"
    :rules="item.rules"
  >
    <!-- 文本输入 -->
    <el-input
      v-if="item.type === 'input'"
      v-model.trim="(model as any)[item.prop!]"
      :placeholder="getPlaceholder(item)"
      :disabled="getDisabled(item)"
    >
      <template #suffix v-if="item.unit">{{ item.unit }}</template>
    </el-input>

    <!-- 数值输入（含整数 / 小数） -->
    <el-input
      v-else-if="item.type === 'number' || item.type === 'integer'"
      v-model.trim="(model as any)[item.prop!]"
      v-number="getPrecision(item)"
      :placeholder="getPlaceholder(item)"
      :disabled="getDisabled(item)"
    >
      <template #suffix v-if="item.unit">{{ item.unit }}</template>
    </el-input>

    <!-- 多行文本输入 -->
    <el-input
      v-else-if="item.type === 'textarea'"
      v-model="(model as any)[item.prop!]"
      type="textarea"
      :rows="item.rows ?? 4"
      :placeholder="getPlaceholder(item)"
      :disabled="getDisabled(item)"
    />

    <!-- 下拉选择 -->
    <el-select
      v-else-if="item.type === 'select' || item.type === 'number-select'"
      v-model="(model as any)[item.prop!]"
      :placeholder="getPlaceholder(item)"
      :disabled="getDisabled(item)"
      clearable
      filterable
      :allow-create="item.allowCreate !== false"
    >
      <el-option
        v-for="(opt, oIdx) in item.options"
        :key="oIdx"
        :label="opt.label"
        :value="opt.value"
      />
    </el-select>

    <!-- 是/否单选 -->
    <el-radio-group
      v-else-if="item.type === 'radio'"
      v-model="(model as any)[item.prop!]"
      :disabled="getDisabled(item)"
    >
      <el-radio-button :label="true">是</el-radio-button>
      <el-radio-button :label="false">否</el-radio-button>
    </el-radio-group>
  </el-form-item>
</template>

<script setup lang="ts">
import { getPlaceholder, getDisabled, getPrecision } from '@/utils/form-helper'
import type { FormItem } from '@/utils/form-types'

defineProps<{
  item: FormItem
  model: Record<string, any>
  /** el-form-item label 宽度（如 '80px'、'100px'） */
  labelWidth?: string
}>()
</script>
