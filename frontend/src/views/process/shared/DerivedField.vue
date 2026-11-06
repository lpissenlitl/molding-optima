<!-- DerivedField - 派生字段展示组件（只读 description list 风格）：替换 "form-item + disabled el-input" 的伪只读模式 -->
<!-- null/undefined 自动转 "—" 占位，数字 + unit 自动拼接，可选 tooltip 承载领域知识；纯展示不参与 el-form 校验 -->
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

/** DerivedField Props */
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

/** 渲染值计算 */
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
/* DerivedField 样式 */
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