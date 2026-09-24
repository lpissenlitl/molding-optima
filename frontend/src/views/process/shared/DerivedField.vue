<!--
  DerivedField - 派生字段展示组件（只读 description list 风格）

  用途：
    - 替换 "form-item + disabled el-input" 的派生字段"伪只读"模式
    - 接受数字、字符串、布尔等任意 value
    - 自动处理 null/undefined → "—" 占位
    - 数字 + unit 自动拼接（如 "100 g"、"50 mm"）
    - 可选 tooltip 包装领域知识

  用法（4 列）：
    <el-row :gutter="24">
      <el-col :xs="24" :sm="12" :md="6">
        <DerivedField label="平均壁厚" :value="product.ave_wall_thickness" unit="mm" />
      </el-col>
    </el-row>

  样式契约：
    - 不参与 el-form 校验（纯展示）
    - 字体大小与 form-item label 对齐（13px），value 略深
    - 与 .custom-form 配合使用，依赖全局表单规范
-->
<template>
  <div class="derived-field">
    <span class="derived-field__label">{{ label }}</span>
    <el-tooltip
      v-if="tooltip"
      effect="dark"
      placement="top"
      :content="tooltip"
    >
      <span class="derived-field__value">{{ displayValue }}</span>
    </el-tooltip>
    <span v-else class="derived-field__value">{{ displayValue }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * DerivedField Props
 * - label: 字段名（必填）
 * - value: 任意类型值。null/undefined 显示占位符
 * - unit: 单位后缀，仅在 value 是有限数字时拼接
 * - tooltip: hover tooltip（领域知识说明）
 * - placeholder: 空值占位，默认 "—"
 * - numberFormat: 数字精度（如 2 表示保留 2 位小数）。0 表示取整
 */
interface Props {
  label: string
  value?: any
  unit?: string
  tooltip?: string
  placeholder?: string
  numberFormat?: number
}

const props = withDefaults(defineProps<Props>(), {
  value: undefined,
  unit: '',
  tooltip: '',
  placeholder: '—',
  numberFormat: undefined,
})

/**
 * 渲染值计算
 * - null/undefined → placeholder
 * - 有限数字 + unit → "value unit"（可指定精度）
 * - 字符串 → 原样输出
 * - 布尔 → "是" / "否"
 * - 其他 → String(value)
 */
const displayValue = computed<string>(() => {
  const v = props.value

  if (v === null || v === undefined || v === '') {
    return props.placeholder
  }

  // 数字（含可配置精度）
  if (typeof v === 'number' && Number.isFinite(v)) {
    const formatted =
      props.numberFormat !== undefined
        ? v.toFixed(props.numberFormat)
        : String(v)
    return props.unit ? `${formatted} ${props.unit}` : formatted
  }

  // 布尔（UI 层常用 "是"/"否"）
  if (typeof v === 'boolean') {
    return v ? '是' : '否'
  }

  return String(v)
})
</script>

<style lang="scss" scoped>
/*
 * DerivedField 样式
 * - 横向 flex：label（左灰） + value（右深）
 * - label 与 form-item label 等宽视觉对齐
 * - value 略大、略重，强调派生信息的可读性
 * - min-height 保证与 el-form-item 视觉高度一致
 */
.derived-field {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  line-height: 1.4;

  &__label {
    flex-shrink: 0;
    color: var(--el-text-color-regular, #606266);
    font-size: 13px;
  }

  &__value {
    flex: 1;
    min-width: 0;
    color: var(--el-text-color-primary, #303133);
    font-size: 14px;
    font-weight: 500;
    word-break: break-all;
    // 单行省略（与 form 控件视觉一致）
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>