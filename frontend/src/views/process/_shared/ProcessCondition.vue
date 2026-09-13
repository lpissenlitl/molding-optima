<!--
  ProcessCondition - 工艺条件卡（可折叠）· 协调壳

  重构说明（2026-09-13）：
    - 拆分为 MoldSection / MachineSection / PolymerSection 三个子组件
    - 主组件只保留：卡片框架、折叠逻辑、折叠态 summary、校验钩子
    - 通过 provide(ConditionKey, condition) 让子组件共享 reactive condition
    - 子组件直接 mutate condition.xxx（无需 emit / props 双向绑定）

  父组件调用方式：
    <ProcessCondition
      ref="pcRef"
      :process-condition="condition"
      mode="edit"
      :default-expanded="true"
    />
    await pcRef.value?.checkFormDataValid()

  ┌────────────────────────────────────────────────────────────────┐
  │ ▼ 工艺条件                              [收起 ▲]               │  ← 展开态 header
  │ ────────────────────────────────────────────────────────────  │
  │  MoldSection / MachineSection / PolymerSection 三个 area      │
  └────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────┐
  │ ▶ 工艺条件  📋 PC2025-001 [使用中]  模具:M001/射1  ...     [展开编辑 ▼] │  ← 折叠态 header
  └────────────────────────────────────────────────────────────────┘
-->
<template>
  <el-card
    class="process-condition-card"
    :class="{ 'is-collapsed': !expanded, 'is-readonly': isReadOnly }"
    shadow="never"
  >
    <!-- 卡片 header：可点击切换（仅在可折叠时） -->
    <template #header>
      <div
        class="process-condition-card__header"
        :class="{ 'is-clickable': !isReadOnly }"
        @click="toggle"
      >
        <!-- 左侧：折叠图标 + 标题 -->
        <div class="process-condition-card__header-left">
          <AppIcon
            :icon="expanded ? 'mdi:chevron-down' : 'mdi:chevron-right'"
            class="process-condition-card__toggle-icon"
          />
          <span class="custom-form__title">工艺条件</span>
        </div>

        <!-- 折叠态：显示简要信息 -->
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

        <!-- 右侧：展开/收起按钮（仅在可折叠时显示） -->
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
          label-width="120px"
        >
          <!-- 1. 模具 -->
          <MoldSection :disabled="isReadOnly" />

          <!-- 2. 注塑机 -->
          <MachineSection :disabled="isReadOnly" />

          <!-- 3. 材料 -->
          <PolymerSection :disabled="isReadOnly" />
        </el-form>
      </div>
    </transition>
  </el-card>
</template>

<script setup lang="ts">
/**
 * ProcessCondition - 工艺条件卡（协调壳）
 *
 * 职责：
 *   1. 创建并 provide 共享的 reactive condition
 *   2. 监听 props.processCondition 变化并同步内部 condition
 *   3. 卡片 header / 折叠 / summary 协调
 *   4. el-form 校验钩子（checkFormDataValid）
 *   5. 派生计算（用于折叠态 summary）
 *
 * 子组件（按区域拆分）：
 *   - MoldSection: 模具主选 + 基本信息 + 工艺射次 + 浇注系统（含制品/浇口循环）
 *   - MachineSection: 注塑机主选 + 基本信息 + 射台主选 + 射台信息
 *   - PolymerSection: 材料主选 + 基本信息 + 工艺参数
 *
 * 索引说明：
 *   - 后端 shot_index / injection_index 是 0 索引（0 表示第 1 射/射台）
 *   - UI 显示 1 索引（用户友好），由各子组件的字符串中间值 + watch 自动转换
 */
import { ref, reactive, watch, computed, provide } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import MoldSection from './MoldSection.vue'
import MachineSection from './MachineSection.vue'
import PolymerSection from './PolymerSection.vue'
import { useConditionDerived } from './composables/useConditionDerived'
import { ConditionKey } from './types'
import type { Condition } from './types'

// ============================================================================
// 状态枚举映射（与后端 STATUS_CHOICES 保持一致，禁止臆造）
// ============================================================================

const STATUS_MAP: Record<string, string> = {
  active: '使用中',
  archived: '已归档',
}

const STATUS_TAG_TYPE: Record<string, 'success' | 'info' | 'warning'> = {
  active: 'success',
  archived: 'info',
}

// ============================================================================
// Props
// ============================================================================

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

// ============================================================================
// 折叠状态
// ============================================================================

/** 只读模式：mode='view' 或 disabled=true 时强制折叠 */
const isReadOnly = computed(() => props.mode === 'view' || props.disabled)

/** 是否展开（受 mode / defaultExpanded 控制） */
const expanded = ref<boolean>(
  isReadOnly.value ? false : props.defaultExpanded,
)

/** 切换展开/折叠（非只读时生效） */
function toggle() {
  if (isReadOnly.value) return
  expanded.value = !expanded.value
}

// ============================================================================
// 响应式状态（共享给所有 Section）
// ============================================================================

const condition = reactive<Condition>(props.processCondition ?? {})

/**
 * 通过 InjectionKey 提供共享的 reactive condition
 *
 * 设计动机：
 * - 子组件需要直接 mutate condition.xxx（如选择模具后写 mold_id）
 * - 用 InjectionKey 比 props/emit 更简洁：避免 prop drilling 和 emit 转发
 * - 用 InjectionKey 强类型：避免字符串 key 拼错、保证类型推断
 */
provide(ConditionKey, condition)

// ============================================================================
// 派生计算（用于折叠态 summary）
// ============================================================================

const {
  hasMold,
  hasMachine,
  hasPolymer,
  shotIndexDisplay,
  injectionIndexDisplay,
} = useConditionDerived(condition)

// ============================================================================
// 校验规则
// ============================================================================

const rules: FormRules = {
  mold_id: [{ required: true, message: '请选择模具', trigger: 'change' }],
  shot_index: [{ required: true, message: '请选择工艺射次', trigger: 'change' }],
  injection_machine_id: [{ required: true, message: '请选择注塑机', trigger: 'change' }],
  injection_index: [{ required: true, message: '请选择射台', trigger: 'change' }],
  polymer_id: [{ required: true, message: '请选择塑料', trigger: 'change' }],
}

// ============================================================================
// 父组件钩子
// ============================================================================

defineExpose({
  /**
   * 触发 el-form 校验。
   * 校验通过：返回 true，父组件继续保存
   * 校验失败：返回 false，父组件应提示用户
   */
  async checkFormDataValid(): Promise<boolean> {
    if (!formRef.value) return false
    // 折叠态时强制展开（让用户能看到/修改不通过校验的字段）
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
  /** 切换展开/折叠（供父组件主动控制） */
  toggle,
  /** 强制展开（供父组件主动控制） */
  expand: () => {
    if (!isReadOnly.value) expanded.value = true
  },
  /** 强制折叠（供父组件主动控制） */
  collapse: () => {
    expanded.value = false
  },
})

// ============================================================================
// 监听：prop 变化时同步内部 condition
// ============================================================================

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
 * 自定义类 .process-condition-card-*：本组件特有的折叠 / 简要信息样式
 *
 * 全局 utility（不定义，本组件直接使用）：
 * - .custom-form / .custom-form__section / .custom-form__title / .custom-form__divider
 *   → src/styles/utilities/custom-form.scss
 * - .subsection-block / .subsection-block--nested / --deep-nested / .subsection-block__*
 *   → src/styles/utilities/subsection-block.scss
 *
 * 本组件私有：
 * - .process-condition-card__*（折叠 header / summary）
 * - .summary-item*（折叠态简要信息项）
 * - .process-condition-collapse-enter/leave-*（折叠过渡）
 */
.process-condition-card {
  /*
  * 重置 el-card body 默认 padding（20px 上下）
  * - 原：el-card__body 自带 padding，导致折叠后 transition 元素高度为 0 但 padding 仍占空间，出现"留边"
  * - 现在：padding 完全由 .process-condition-card__body 控制，折叠时可同步过渡到 0
  */
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

  /*
  * body 容器：接管原本 el-card__body 的 padding
  * - 展开态：与 el-card 默认 20px padding 一致
  * - 折叠态：通过 transition 同步过渡到 0（见下方 transition 规则）
  * - max-height 控制：展开时足够大（2000px），折叠时为 0
  */
  &__body {
    padding: var(--el-card-padding, 20px);
    overflow: hidden;
  }
}

/*
* 折叠态简要信息项（本组件私有）
*
* 优化点：
* - __value / __label / __shot 用 max-width + ellipsis，防止某一项过长挤出其他项
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
    // AppIcon (Iconify Icon) 渲染为 <svg>，用 width/height 控制大小（font-size 对 svg 无效）
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
* - enter: 从 maxHeight:0 + opacity:0 + padding:0 展开到实际高度 + 透明 + 20px padding
* - leave: 反向折叠
* - ease-in-out 缓动函数让展开/折叠看起来更顺滑
*
* 关键：padding-top/bottom 与 max-height 同步过渡
* - 只过渡 max-height 会"留边"（el-card body padding 不会被压缩）
* - 现在 3 个属性同步过渡，折叠收得干净
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
