<!--
  ProcessCondition - 工艺条件卡（可折叠）+ 3 个 Section 协调器

  职责：卡片框架 / 折叠 / 折叠态 summary / 校验钩子
  通过 provide(ConditionKey, condition) 让子组件共享 reactive condition
-->
<template>
  <el-card
    class="process-condition-card"
    :class="{ 'is-collapsed': !expanded, 'is-readonly': isReadOnly }"
    shadow="never"
  >
    <!-- 卡片 header：可点击切换 -->
    <template #header>
      <div
        class="process-condition-card__header"
        :class="{ 'is-clickable': !isReadOnly }"
        @click="toggle"
      >
        <div class="process-condition-card__header-left">
          <AppIcon
            :icon="expanded ? 'mdi:chevron-down' : 'mdi:chevron-right'"
            class="process-condition-card__toggle-icon"
          />
          <span class="custom-form__title">工艺条件</span>
        </div>

        <!-- 折叠态简要信息 -->
        <div v-show="!expanded" class="process-condition-card__summary">
          <span class="summary-item">
            <AppIcon icon="mdi:identifier" class="summary-item__icon" />
            <span class="summary-item__value">
              {{ condition.condition_no || '/' }}
            </span>
          </span>
          <el-tag
            v-if="condition.status"
            size="small"
            :type="STATUS_TAG_TYPE[condition.status]"
          >
            {{ STATUS_MAP[condition.status] }}
          </el-tag>
          <template v-if="hasMold">
            <el-divider direction="vertical" />
            <span class="summary-item">
              <AppIcon icon="mdi:cube-outline" class="summary-item__icon" />
              <span class="summary-item__label">模具</span>
              <span class="summary-item__value">
                {{ condition.mold_info?.mold_no }}
                <span class="summary-item__sep">/</span>
                射{{ shotIndexDisplay }}
              </span>
            </span>
          </template>
          <template v-if="hasMachine">
            <el-divider direction="vertical" />
            <span class="summary-item">
              <AppIcon icon="mdi:server-outline" class="summary-item__icon" />
              <span class="summary-item__label">机器</span>
              <span class="summary-item__value">
                {{ condition.machine_info?.brand }}
                {{ condition.machine_info?.model }}
                <span class="summary-item__sep">/</span>
                射台{{ injectionIndexDisplay }}
              </span>
            </span>
          </template>
          <template v-if="hasPolymer">
            <el-divider direction="vertical" />
            <span class="summary-item">
              <AppIcon icon="mdi:flask-outline" class="summary-item__icon" />
              <span class="summary-item__label">材料</span>
              <span class="summary-item__value">
                {{ condition.polymer_info?.abbreviation }}
              </span>
            </span>
          </template>
        </div>

        <!-- 右侧展开/收起按钮（仅非只读时显示） -->
        <div v-if="!isReadOnly" class="process-condition-card__header-right">
          <el-button text size="small" @click.stop="toggle">
            {{ expanded ? '收起' : '展开编辑' }}
          </el-button>
        </div>
      </div>
    </template>

    <!-- 卡片 body：可折叠 -->
    <transition name="process-condition-collapse">
      <div v-show="expanded" class="process-condition-card__body">
        <el-form
          ref="formRef"
          :model="condition"
          :rules="rules"
          class="custom-form"
          label-width="100px"
        >
          <el-card class="custom-form__section custom-form__section--inner" shadow="never">
            <template #header>
              <span class="custom-form__title">
                <AppIcon icon="mdi:cube-outline" class="custom-form__title-icon" />
                模具
              </span>
            </template>
            <MoldSection :disabled="isReadOnly" />
          </el-card>

          <el-card class="custom-form__section custom-form__section--inner" shadow="never">
            <template #header>
              <span class="custom-form__title">
                <AppIcon icon="mdi:server-outline" class="custom-form__title-icon" />
                注塑机
              </span>
            </template>
            <MachineSection :disabled="isReadOnly" />
          </el-card>

          <el-card class="custom-form__section custom-form__section--inner" shadow="never">
            <template #header>
              <span class="custom-form__title">
                <AppIcon icon="mdi:flask-outline" class="custom-form__title-icon" />
                材料
              </span>
            </template>
            <PolymerSection :disabled="isReadOnly" />
          </el-card>
        </el-form>
      </div>
    </transition>
  </el-card>
</template>

<script setup lang="ts">
/**
 * ProcessCondition - 工艺条件卡协调壳
 *
 * 职责：提供 reactive condition、协调 3 个 Section、卡片折叠/校验
 * 父组件调用方式：await pcRef.value?.checkFormDataValid()
 */
import { ref, reactive, watch, computed, provide } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import MoldSection from './MoldSection.vue'
import MachineSection from './MachineSection.vue'
import PolymerSection from './PolymerSection.vue'
import { useConditionDerived } from './composables/useConditionDerived.js'
import { ConditionKey } from './types.js'
import type { Condition } from './types.js'

// 状态枚举映射（与后端 STATUS_CHOICES 保持一致，禁止臆造）
const STATUS_MAP: Record<string, string> = {
  active: '使用中',
  archived: '已归档',
}

const STATUS_TAG_TYPE: Record<string, 'success' | 'info' | 'warning'> = {
  active: 'success',
  archived: 'info',
}

// Props
const props = withDefaults(
  defineProps<{
    processCondition: Condition
    /** 模式：new/edit/transplant 可编辑，view 强制折叠（只读） */
    mode?: 'new' | 'edit' | 'view' | 'transplant'
    /** 默认展开状态（仅在非 view 模式生效） */
    defaultExpanded?: boolean
    /** 禁用所有输入（与 mode='view' 区别：保留折叠切换能力） */
    disabled?: boolean
  }>(),
  {
    mode: 'edit',
    defaultExpanded: true,
    disabled: false,
  },
)

const formRef = ref<FormInstance>()

// 只读模式：mode='view' 或 disabled=true 时强制折叠
const isReadOnly = computed(() => props.mode === 'view' || props.disabled)

const expanded = ref<boolean>(
  isReadOnly.value ? false : props.defaultExpanded,
)

function toggle() {
  if (isReadOnly.value) return
  expanded.value = !expanded.value
}

// 响应式 condition：provide 给所有 Section 使用（子组件可直接 mutate）
const condition = reactive<Condition>(props.processCondition ?? {})
provide(ConditionKey, condition)

// 派生计算（用于折叠态 summary）
const {
  hasMold,
  hasMachine,
  hasPolymer,
  shotIndexDisplay,
  injectionIndexDisplay,
} = useConditionDerived(condition)

const rules: FormRules = {
  mold_id: [{ required: true, message: '请选择模具', trigger: 'change' }],
  shot_index: [{ required: true, message: '请选择工艺射次', trigger: 'change' }],
  injection_machine_id: [{ required: true, message: '请选择注塑机', trigger: 'change' }],
  injection_index: [{ required: true, message: '请选择射台', trigger: 'change' }],
  polymer_id: [{ required: true, message: '请选择塑料', trigger: 'change' }],
}

defineExpose({
  /**
   * 校验表单。返回 true 表示通过。
   * 折叠态下强制展开，让用户看到/修改未通过校验的字段。
   */
  async checkFormDataValid(): Promise<boolean> {
    if (!formRef.value) return false
    if (!expanded.value) {
      expanded.value = true
    }
    try {
      await formRef.value.validate()
    } catch {
      ElMessage.error('工艺条件填写不完整，请检查')
      return false
    }
    return true
  },
  /** 切换展开/折叠 */
  toggle,
  /** 强制展开（非只读时） */
  expand: () => {
    if (!isReadOnly.value) expanded.value = true
  },
  /** 强制折叠 */
  collapse: () => {
    expanded.value = false
  },
  /** 当前是否展开（父组件同步按钮状态用） */
  isExpanded: () => expanded.value,
})

// 监听 prop 变化，同步内部 condition
watch(
  () => props.processCondition,
  (val) => {
    Object.assign(condition, val ?? {})
  },
  { deep: true, immediate: true },
)
</script>

<style lang="scss" scoped>
/*
 * 本组件私有样式：折叠 / 简要信息 / 过渡动画
 * 依赖全局 utility（不在此处定义）：
 * - .custom-form / .custom-form__section / .custom-form__title
 *   → src/styles/utilities/custom-form.scss
 * - .subsection-block / --nested / --deep-nested
 *   → src/styles/utilities/subsection-block.scss
 */
.process-condition-card {
  // 重置 el-card body 默认 padding，让折叠过渡能同步压缩到 0
  :deep(.el-card__body) {
    padding: 0;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: 32px;
    padding: 4px 0;

    &.is-clickable {
      cursor: pointer;
      user-select: none;

      &:hover .process-condition-card__toggle-icon {
        color: var(--el-color-primary);
      }
    }
  }

  &__header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  &__toggle-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    color: #606266;
    vertical-align: middle;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), color 0.2s ease;
  }

  &__summary {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    flex: 1;
    min-width: 0;
    margin-left: 8px;
    font-size: 13px;
    color: #303133;
  }

  &__header-right {
    flex-shrink: 0;
    margin-left: auto;
  }

  // body 容器接管 el-card__body 的 padding，折叠时能过渡到 0
  &__body {
    padding: var(--el-card-padding, 20px);
    overflow: hidden;
  }

  /*
   * 内 card（模具 / 注塑机 / 材料）样式调整
   * - 缩小 body padding 避免与外 card padding 叠加
   * - header 加浅色背景 + 底部分隔线，与 body 区分
   */
  :deep(.custom-form__section--inner) {
    margin-bottom: 16px;

    .el-card__header {
      padding: 10px 20px;
      background-color: var(--color-bg-overlay, #f5f7fa);
      border-bottom: 1px solid var(--color-border-extra-light);
    }

    .el-card__body {
      padding: 16px 20px;
    }

    &:last-child {
      margin-bottom: 0;
    }

    // 去掉内 card 标题左边的主题色条（参考 SettingProcess.vue）
    .custom-form__title {
      padding-left: 0;
      border-left: none;
    }
  }
}

/*
 * 折叠态简要信息项
 * - __value 用 max-width + ellipsis 防止某项过长挤出其他项
 * - min-width: 0 关键：flex 子项默认 min-width: auto 会阻止 ellipsis 生效
 */
.summary-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  line-height: 1;
  min-width: 0;
  max-width: 100%;

  &__icon {
    // AppIcon 渲染为 <svg>，用 width/height 控制大小（font-size 对 svg 无效）
    width: 14px;
    height: 14px;
    flex-shrink: 0;
    color: #909399;
    vertical-align: middle;
  }

  &__label {
    color: #909399;
    flex-shrink: 0;
  }

  &__value {
    color: #303133;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__sep {
    color: #c0c4cc;
    margin: 0 2px;
    flex-shrink: 0;
  }
}

/*
 * 折叠过渡动画
 * - 同时过渡 max-height / opacity / padding-top / padding-bottom
 * - 只过渡 max-height 会“留边”（el-card body padding 不会被压缩）
 */
.process-condition-collapse-enter-active,
.process-condition-collapse-leave-active {
  transition:
    max-height 0.3s ease-in-out,
    opacity 0.25s ease-in-out,
    padding-top 0.3s ease-in-out,
    padding-bottom 0.3s ease-in-out;
  overflow: hidden;
}

.process-condition-collapse-enter-from,
.process-condition-collapse-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.process-condition-collapse-enter-to,
.process-condition-collapse-leave-from {
  max-height: 2000px; /* 足够大的高度容纳表单 */
  opacity: 1;
  /* padding 保持原值（继承自 .process-condition-card__body） */
}
</style>
