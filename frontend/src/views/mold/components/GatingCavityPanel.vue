<!--
  GatingCavityPanel - 单个 Cavity 的折叠面板（被 GatingSystemForm 引用）

  路由：无（子组件）

  设计要点：
  - 单文件封装 1 个 Cavity + 1:N Gates 的渲染
  - 数据通过 props.cavity 直接双向绑定（修改 reactive 对象属性即可同步到 mold_info）
  - 字段数组由 GatingSystemForm 传入（cavityItems / gateBaseItems / 矩形 / 圆形 / 环形）
  - Gate 折叠状态用本地 ref（不放数据对象上，避免被序列化到后端）
  - v-else-if 链渲染（与 GatingSystemForm 保持一致风格）
  - 删除 Cavity 通过 emit('remove') 通知父级（父级要同步 activeCavityMap）

  结构：
    el-collapse-item (Cavity #N)
      ├─ 标题：产品 #N + 浇口数 tag
      ├─ Cavity 字段（el-row + el-col）
      ├─ el-collapse (Gate 内层)
      │   └─ el-collapse-item (Gate #N)
      │       ├─ Gate 基础字段
      │       └─ Gate 尺寸字段（按 gate_shape 条件显示）
      └─ 添加 Gate 按钮
-->
<template>
  <!--
    cavity 块：边框 + 浅背景色，与其他 cavity 块视觉分隔
    - 标题行：产品 #N + 删除按钮（条件显示）
    - 单 cavity 时只有一个块，视觉简洁
    - 多 cavity 时多个块平铺，方便横向对比
  -->
  <div class="cavity-block">
    <div class="cavity-block__header">
      <span class="cavity-block__title">
        <AppIcon icon="mdi:cube-outline" />
        #{{ Number(cavityIndex) + 1 }}
        <!--
          产品名称：有值时正常显示，未填写时显示灰色"未命名"占位
          - 多 cavity 场景下最关键的区分信息（家族模具的多个产品）
          - 单 cavity 场景下也展示，让用户看到自己填了啥
        -->
        <span
          :class="[
            'cavity-block__name',
            { 'is-placeholder': !cavity.product_name }
          ]"
        >
          {{ cavity.product_name || '未命名' }}
        </span>
        <span class="cavity-block__meta">
          · {{ cavity.cavity_count_per_shot ?? '?' }} 腔
        </span>
      </span>
      <!-- 删除按钮：仅 showRemove=true 时显示（父组件控制） -->
      <el-popconfirm
        v-if="showRemove"
        title="确定删除此产品及其所有浇口？"
        @confirm="emit('remove')"
      >
        <template #reference>
          <el-button text type="danger" size="small">
            <AppIcon icon="mdi:trash-can-outline" style="margin-right: 4px;" />
            删除产品
          </el-button>
        </template>
      </el-popconfirm>
    </div>

    <!-- Cavity 字段 -->
    <el-row :gutter="24">
      <el-col
        v-for="(item, iIdx) in cavityItems"
        :key="`cav_field_${iIdx}`"
        :span="item.span || 6"
      >
        <FormFieldRenderer :item="item" :model="cavity" label-width="120px" />
      </el-col>
    </el-row>

    <!-- ============ Gate 列表（平铺）============ -->
    <div class="gate-list">
      <div
        v-for="(gate, gIdx) in cavity.gates"
        :key="`gate_${gIdx}`"
        class="gate-block"
      >
        <!-- Gate 标题行：编号 + 形状图标 + 形状文字 + 右上角删除
         * 几何图标按形状区分（替代 el-tag，降低视觉权重）
         * 未选形状时图标和文字都用 is-placeholder 灰斜体
         -->
        <div class="gate-block__header">
          <span class="gate-block__title">
            <AppIcon
              :icon="shapeIcon(gate.gate_shape)"
              :class="{ 'is-placeholder': !gate.gate_shape }"
            />
            浇口 #{{ Number(gIdx) + 1 }}
            <span
              :class="['gate-block__shape', { 'is-placeholder': !gate.gate_shape }]"
            >
              {{ gate.gate_shape || '未选择形状' }}
            </span>
          </span>
          <!-- 删除按钮：gate > 1 才显示（最少保留一个浇口） -->
          <el-popconfirm
            v-if="showGateRemove"
            title="确定删除此浇口？"
            @confirm="removeGate(Number(gIdx))"
          >
            <template #reference>
              <el-button text type="danger" size="small">
                <AppIcon icon="mdi:trash-can-outline" style="margin-right: 4px;" />
                删除浇口
              </el-button>
            </template>
          </el-popconfirm>
        </div>

        <!-- Gate 基础字段（4 个字段：浇口类型/形状/数量/位置）============ -->
        <el-row :gutter="24">
          <el-col
            v-for="(item, iIdx) in gateBaseItems"
            :key="`gate_base_${gIdx}_${iIdx}`"
            :span="item.span || 6"
          >
            <FormFieldRenderer :item="item" :model="gate" label-width="110px" />
          </el-col>
        </el-row>

        <!-- Gate 尺寸字段（按 gate_shape 条件显示）============ -->
        <template v-if="gate.gate_shape === '矩形'">
          <div class="gate-block__subsection">
            <el-row :gutter="24">
              <el-col
                v-for="(item, iIdx) in gateRectItems"
                :key="`gate_rect_${gIdx}_${iIdx}`"
                :span="item.span || 6"
              >
                <FormFieldRenderer :item="item" :model="gate" label-width="110px" />
              </el-col>
            </el-row>
          </div>
        </template>

        <template v-else-if="gate.gate_shape === '梯形'">
          <div class="gate-block__subsection">
            <el-row :gutter="24">
              <el-col
                v-for="(item, iIdx) in gateTrapezoidItems"
                :key="`gate_trapezoid_${gIdx}_${iIdx}`"
                :span="item.span || 6"
              >
                <FormFieldRenderer :item="item" :model="gate" label-width="110px" />
              </el-col>
            </el-row>
          </div>
        </template>

        <template v-else-if="gate.gate_shape === '圆形'">
          <div class="gate-block__subsection">
            <el-row :gutter="24">
              <el-col
                v-for="(item, iIdx) in gateCircleItems"
                :key="`gate_circle_${gIdx}_${iIdx}`"
                :span="item.span || 6"
              >
                <FormFieldRenderer :item="item" :model="gate" label-width="110px" />
              </el-col>
            </el-row>
          </div>
        </template>

        <template v-else-if="gate.gate_shape === '环形'">
          <div class="gate-block__subsection">
            <el-row :gutter="24">
              <el-col
                v-for="(item, iIdx) in gateAnnulusItems"
                :key="`gate_annulus_${gIdx}_${iIdx}`"
                :span="item.span || 6"
              >
                <FormFieldRenderer :item="item" :model="gate" label-width="110px" />
              </el-col>
            </el-row>
          </div>
        </template>
      </div>
    </div>

    <!-- 添加 Gate -->
    <div class="add-button-wrapper">
      <el-button text type="primary" size="small" @click="addGate">
        <AppIcon icon="mdi:plus" style="margin-right: 4px;" />
        添加浇口
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * props 数据双向绑定说明：
 * - props.cavity 是 gatingSystem.cavities[cIdx] 的引用（reactive 对象）
 * - gates 是 cavity.gates 数组，通过 push / splice 增删
 * - 子组件不创建本地 ref 镜像，保持单向数据流
 */
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormItem } from '@/utils/form-types'
import { gateForm } from '@/constants/mold-const'
import FormFieldRenderer from './FormFieldRenderer.vue'

const props = defineProps<{
  cavity: Record<string, any>
  cavityItems: FormItem[]
  gateBaseItems: FormItem[]
  gateRectItems: FormItem[]
  gateCircleItems: FormItem[]
  gateAnnulusItems: FormItem[]
  gateTrapezoidItems: FormItem[]
  /**
   * 是否显示"删除产品"按钮
   * - true：多 cavity 时（父组件传入 gatingSystem.cavities.length > 1）
   * - false：单 cavity 时（默认）
   * - 注：用户明确要求"删除按钮条件出现"，不做自动判断以外的逻辑
   */
  showRemove?: boolean
  /**
   * Cavity 索引（用于标题显示"产品 #N"）
   * - 父组件传入 Number(cIdx)
   * - 不传时显示 #1（单 cavity 场景下视觉一致）
   */
  cavityIndex?: number
}>()

const emit = defineEmits<{
  remove: []
}>()

/**
 * Cavity 索引（用于标题显示"产品 #N"）
 * - 可选 prop，不传时退化为显示 #1（单 cavity 场景下无所谓）
 * - 父组件传入 Number(cIdx)
 */
const cavityIndex = computed(() => props.cavityIndex ?? 0)

/**
 * 是否显示"删除浇口"按钮
 * - gate > 1：true（多浇口时显示删除）
 * - gate == 1：false（必须保留至少一个浇口，gate 是 cavity 的强制依赖）
 * - 子组件内部计算（与 cavity 删除不同：cavity 删除要 emit 通知父级，gate 删除内部 splice）
 */
const showGateRemove = computed(() => props.cavity.gates.length > 1)

/**
 * 添加浇口（gate 是 cavity 的强制依赖，可无限添加）
 */
function addGate() {
  props.cavity.gates.push(structuredClone(gateForm))
  ElMessage.success('已添加浇口')
}

/**
 * 删除浇口
 * - 守卫：gate <= 1 时拒绝删除（最少保留一个浇口）
 * - 守卫由 showGateRemove computed 在 UI 层面控制（按钮不出现）
 * - 这里再加一道保险，防止 v-if 误判
 */
function removeGate(gIdx: number) {
  if (props.cavity.gates.length <= 1) {
    ElMessage.warning('至少保留一个浇口')
    return
  }
  props.cavity.gates.splice(gIdx, 1)
  ElMessage.success('已删除浇口')
}

/**
 * Gate 形状 → Material Design Icon
 * - 用于 gate-block__title 图标，按形状视觉区分
 * - 默认 mdi:circle-medium（未选形状时占位）
 */
function shapeIcon(shape?: string): string {
  switch (shape) {
    case '矩形': return 'mdi:rectangle-outline'
    case '梯形': return 'mdi:triangle-outline'
    case '圆形': return 'mdi:circle-outline'
    case '环形': return 'mdi:ring'
    default: return 'mdi:circle-medium'
  }
}
</script>

<style scoped lang="scss">
/*
 * cavity 块样式：边框 + 浅背景色，与其他 cavity 块视觉分隔
 * - 与 GatingSystemForm 的 .cavity-list（gap:12px）配合，块间留空
 * - 多 cavity 场景下像一叠卡片，单 cavity 场景下视觉简洁
 */
.cavity-block {
  border: 1px solid var(--color-border-light, #e4e7ed);
  border-radius: 6px;
  padding: 16px;
  background-color: var(--color-bg-overlay, #f5f7fa);

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  &__title {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    color: var(--el-text-color-primary, #303133);
  }

  /*
   * 产品名称：主信息，字重中等
   * - 与编号（主）、腔数（次）形成层次
   * - 未填写时用 is-placeholder 类变灰，不影响布局
   */
  &__name {
    font-size: 14px;
    font-weight: 500;
    color: var(--el-text-color-primary, #303133);
    margin-left: 4px;

    &.is-placeholder {
      color: var(--el-text-color-placeholder, #c0c4cc);
      font-weight: 400;
      font-style: italic;
    }
  }

  /*
   * meta 信息（如"· 4 腔"）：次要颜色、正常字重
   * - 与编号形成层次：编号是主信息，腔数是补充信息
   * - 单腔场景（1 腔）仍显示，让用户知道这个字段存在
   */
  &__meta {
    font-size: 13px;
    font-weight: 400;
    color: var(--el-text-color-regular, #606266);
    margin-left: 2px;
  }

  /*
   * cavity 内的 divider text 背景覆盖（局部）
   * - Element Plus divider text 默认 var(--el-bg-color, #fff)
   * - cavity-block 背景是 var(--color-bg-overlay, #f5f7fa)，白底突兀
   * - 用 :deep() 局部覆盖（不影响 cavity 外的白底页面）
   * - 这里写 background-color: var(--color-bg-overlay) 而不是 inherit
   *   因为 inherit 在 Element Plus divider 上无效（text 直接父级 .el-divider 是 transparent）
   */
  :deep(.custom-form__divider .el-divider__text) {
    background-color: var(--color-bg-overlay, #faf5f6);
  }
}

/*
 * Gate 列表容器
 * - 与 cavity-list 一致风格：gap 分隔
 * - gate 块比 cavity 块小（内嵌在 cavity 内）
 */
.gate-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 12px 0;
}

/*
 * gate 块：边框 + 浅背景色
 * - 与 cavity-block 一致的设计语言（嵌套卡片）
 * - 视觉权重比 cavity 轻（border 颜色稍浅、padding 略小）
 * - 背景 #fff（cavity 背景是 #f5f7fa，gate 在 cavity 内层所以白底反差更分明）
 */
.gate-block {
  border: 1px solid var(--color-border-lighter, #ebeef5);
  border-radius: 4px;
  padding: 12px 16px;
  background-color: #fff;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  &__title {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 600;
    color: var(--el-text-color-primary, #303133);
  }

  /*
   * gate 元信息（"未选择形状"）：次要颜色、正常字重
   * - 与 cavity-block__meta 一致
   */
  &__meta {
    font-size: 13px;
    font-weight: 400;
    color: var(--el-text-color-regular, #606266);
    margin-left: 4px;

    &.is-placeholder {
      color: var(--el-text-color-placeholder, #c0c4cc);
      font-style: italic;
    }
  }

  /*
   * 形状文字标签（如"矩形""梯形""圆形""环形"）
   * - 替代 el-tag，视觉权重与 cavity 标题字色一致
   * - 与 __title 中的 AppIcon 配合：图标 + 文字双标识形状
   */
  &__shape {
    font-size: 13px;
    font-weight: 500;
    color: var(--el-text-color-primary, #303133);
    margin-left: 4px;

    &.is-placeholder {
      color: var(--el-text-color-placeholder, #c0c4cc);
      font-weight: 400;
      font-style: italic;
    }
  }

  /*
   * 尺寸字段容器（rect / trapezoid / circle / annulus）
   * - 与基础字段用 dashed border 隔开，视觉分组
   */
  &__subsection {
    padding-top: 16px;
    border-top: 1px dashed var(--color-border-lighter, #ebeef5);
  }
}

.add-button-wrapper {
  display: flex;
  justify-content: flex-start;
  margin: 4px 0 0;
  padding: 0;
}
</style>