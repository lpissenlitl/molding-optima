<!--
  GatingSystemForm - 浇注系统子表单（被 MoldForm 引用）

  路由：无（子组件）

  设计要点：
  - 单层封装 1 个 GatingSystem + 1:N Cavities + 1:N Gates
  - 由 MoldForm 包裹在 el-card 内使用，故不含 page-header / form-actions / loaded
  - 数据通过 props.gatingSystem 直接双向绑定（修改 reactive 对象属性即可同步到 mold_info）
  - 字段数组按层级 + 条件分组（basic / 热流道 / 冷流道 / cavity / gate / 矩形 / 圆形 / 环形）
  - 折叠状态用本地 ref（不放数据对象上，避免被序列化到后端）
  - v-else-if 链渲染（plan §5.2 决策：5-7 个分支直接展开，不抽 BaseFormItem）

  折叠结构：
    el-collapse (Cavity 外层)
      └─ el-collapse-item (Cavity #1)
          ├─ Cavity 字段（el-row + el-col）
          └─ el-collapse (Gate 内层)
              └─ el-collapse-item (Gate #1)
                  ├─ Gate 基础字段
                  └─ Gate 尺寸字段（按 gate_shape 条件显示）
-->
<template>
  <el-form
    ref="formRef"
    :model="gatingSystem"
    :rules="rules"
    class="custom-form"
    label-width="120px"
  >
    <!--
     * 原 top el-alert（runnerTypeHint）已删除
     * 原因：流道类型提示已转移到 MoldForm 的 el-tab-pane label
     *      （作为 tag 显示在 tab 上），不在这里重复
     * 补充：选了"流道类别"后，下方 conditional 展开对应字段本身就是反馈
     -->

    <!-- ============ 基础字段 ============ -->
    <el-row :gutter="24">
      <el-col
        v-for="(item, iIdx) in basicItems"
        :key="`basic_${iIdx}`"
        :span="item.span || 6"
      >
        <FormFieldRenderer :item="item" :model="gatingSystem" />
      </el-col>
    </el-row>

    <!-- ============ 热流道字段（runner_type = 热流道 / 热转冷）============ -->
    <template v-if="showHotRunner">
      <el-divider content-position="left" class="custom-form__divider">
        热流道结构
      </el-divider>
      <el-row :gutter="24">
        <el-col
          v-for="(item, iIdx) in hotRunnerItems"
          :key="`hot_${iIdx}`"
          :span="item.span || 6"
        >
          <FormFieldRenderer :item="item" :model="gatingSystem" />
        </el-col>
      </el-row>
    </template>

    <!-- ============ 冷流道字段（runner_type = 冷流道 / 热转冷）============ -->
    <template v-if="showColdRunner">
      <el-divider content-position="left" class="custom-form__divider">
        冷流道结构
      </el-divider>
      <el-row :gutter="24">
        <el-col
          v-for="(item, iIdx) in coldRunnerItems"
          :key="`cold_${iIdx}`"
          :span="item.span || 6"
        >
          <FormFieldRenderer :item="item" :model="gatingSystem" />
        </el-col>
      </el-row>
    </template>

    <!-- ============ Cavity 列表（平铺）============
     * 设计：所有 cavity 块平铺展示，方便家族模具时横向对比参数
     * 单 cavity 场景下与折叠视觉效果一致（只有一个块）
     * 多 cavity 时每个块独立可删、可填
     -->
    <el-divider content-position="left" class="custom-form__divider">
      产品 
    </el-divider>
    <div class="cavity-list">
      <GatingCavityPanel
        v-for="(cavity, cIdx) in gatingSystem.cavities"
        :key="`cav_${cIdx}`"
        :cavity="cavity"
        :cavity-items="cavityItems"
        :gate-base-items="gateBaseItems"
        :gate-rect-items="gateRectItems"
        :gate-circle-items="gateCircleItems"
        :gate-trapezoid-items="gateTrapezoidItems"
        :gate-annulus-items="gateAnnulusItems"
        :show-remove="gatingSystem.cavities.length > 1"
        :cavity-index="Number(cIdx)"
        @remove="removeCavity(Number(cIdx))"
      />
    </div>

    <!-- 添加 Cavity：始终可见，文字按钮低权重 -->
    <div class="add-button-wrapper">
      <el-button text type="primary" size="small" @click="addCavity">
        <AppIcon icon="mdi:plus" style="margin-right: 4px;" />
        添加产品
      </el-button>
    </div>
  </el-form>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  getPlaceholder,
  getDisabled,
  getPrecision,
} from '@/utils/form-helper'
import type { FormItem } from '@/utils/form-types'
import {
  cavityForm,
  runnerTypeOptions,
  hotNozzleTypeOptions,
  sequencingControlMethodOptions,
  sprueBushingOuterDiaOptions,
  sprueBushingBoreDiaOptions,
  sprueBushingRadiusOptions,
  gateTypeOptions,
  gateShapeOptions,
} from '@/constants/mold-const'
import GatingCavityPanel from './GatingCavityPanel.vue'
import FormFieldRenderer from './FormFieldRenderer.vue'

/**
 * props 数据双向绑定说明：
 * - props.gatingSystem 是 MoldForm.mold_info.gating_systems[i] 的引用（reactive 对象）
 * - cavities / gates 是数组，通过数组方法（push / splice）增删
 * - 子组件不创建本地 ref 镜像，保持单向数据流
 */
const props = defineProps<{
  gatingSystem: Record<string, any>
}>()

/**
 * 表单验证规则（2026-09-08 引入 rules 架构）
 * - 详细规则优先使用 Element Plus rules 语法
 * - FormItem.required=true 仅控制是否显示红色星号
 * - 提交时调 formRef.value.validate() 触发验证
 * - 后续逐步补充其他必填字段（流道类别先定为必填）
 */
const rules: FormRules = {
  runner_type: [
    { required: true, message: '请选择流道类别', trigger: 'change' },
  ],
}

/**
 * 暴露 formRef 给父组件 MoldForm（让顶层保存按钮能调所有子表单的 validate）
 * - 当前只有 GatingSystemForm 实现，其他子组件（CoolingSystemForm / EjectionSystemForm）后续跟进
 */
const formRef = ref<FormInstance>()
defineExpose({ formRef })

// ============================================================================
// 字段定义（按层级 + 条件显示分组）
// ============================================================================

const basicItems: FormItem[] = [
  { label: '流道类别', prop: 'runner_type', type: 'select', options: runnerTypeOptions, required: true },
  { label: '制品总重量', prop: 'total_product_weight', type: 'number', unit: 'g', precision: 2 },
]

const hotRunnerItems: FormItem[] = [
  { label: '热流道类型', prop: 'hot_runner_system_type', type: 'select', options: hotNozzleTypeOptions },
  { label: '供应商', prop: 'hot_runner_supplier', type: 'input' },
  // 针阀驱动方式：仅热流道类型 = 针阀式时可填
  { label: '针阀驱动方式', prop: 'valve_actuation_type', type: 'input', disabled: () => props.gatingSystem.hot_runner_system_type !== '针阀式' },
  { label: '分流板温控区数', prop: 'hot_runner_manifold_zones', type: 'integer', unit: '组', precision: 0 },
  { label: '热喷嘴数量', prop: 'hot_runner_nozzle_count', type: 'integer', unit: '个', precision: 0 },
  { label: '是否序流控制', prop: 'has_sequencing_control', type: 'radio' },
  // 时序控制方式：仅当 has_sequencing_control = true 时可填
  { label: '时序控制方式', prop: 'sequencing_control_method', type: 'select', options: sequencingControlMethodOptions, disabled: () => props.gatingSystem.has_sequencing_control !== true },
]

const coldRunnerItems: FormItem[] = [
  { label: '流道重量', prop: 'runner_weight', type: 'number', unit: 'g', precision: 2 },
  { label: '流道长度', prop: 'runner_length', type: 'number', unit: 'mm', precision: 2 },
  { label: '浇口套外径 D1', prop: 'sprue_bushing_outer_dia', type: 'select', options: sprueBushingOuterDiaOptions, unit: 'mm' },
  { label: '浇口套孔径 D2', prop: 'sprue_bushing_bore_dia', type: 'select', options: sprueBushingBoreDiaOptions, unit: 'mm' },
  { label: '球面半径 R', prop: 'sprue_bushing_radius', type: 'select', options: sprueBushingRadiusOptions, unit: 'mm' },
]

const cavityItems: FormItem[] = [
  { label: '成型腔数', prop: 'cavity_count_per_shot', type: 'integer', unit: '腔', precision: 0 },
  { label: '制品名称', prop: 'product_name', type: 'input' },
  { label: '制品编号', prop: 'product_code', type: 'input' },
  { label: '单腔重量', prop: 'estimated_weight_per_cavity', type: 'number', unit: 'g', precision: 2 },
  { label: '最大壁厚', prop: 'max_wall_thickness', type: 'number', unit: 'mm', precision: 2 },
  { label: '最小壁厚', prop: 'min_wall_thickness', type: 'number', unit: 'mm', precision: 2 },
  { label: '平均壁厚', prop: 'ave_wall_thickness', type: 'number', unit: 'mm', precision: 2 },
  { label: '最大流长', prop: 'max_flow_length', type: 'number', unit: 'mm', precision: 2 },
  /*
   * 单腔投影面积（projected_area_per_cavity）
   * - 状态：UI 暂时隐藏（2026-09-07），保留数据结构以备恢复
   * - 原因：当前算法不需要用户填写此字段（算法从腔体几何参数推算）
   * - 恢复方法：取消下面这行注释即可（数据结构无需改动）
   */
  // { label: '单腔投影面积', prop: 'projected_area_per_cavity', type: 'number', unit: 'mm²', precision: 2 },
]

const gateBaseItems: FormItem[] = [
  { label: '浇口类型', prop: 'gate_type', type: 'select', options: gateTypeOptions },
  { label: '浇口形状', prop: 'gate_shape', type: 'select', options: gateShapeOptions },
  { label: '浇口数量', prop: 'gate_count', type: 'integer', unit: '个', precision: 0 },
  { label: '位置描述', prop: 'location_description', type: 'input' },
]

const gateRectItems: FormItem[] = [
  { label: '长', prop: 'length', type: 'number', unit: 'mm', precision: 2 },
  { label: '宽', prop: 'width', type: 'number', unit: 'mm', precision: 2 },
]

const gateCircleItems: FormItem[] = [
  { label: '直径', prop: 'diameter', type: 'number', unit: 'mm', precision: 2 },
]

const gateTrapezoidItems: FormItem[] = [
  { label: '上底长', prop: 'top_length', type: 'number', unit: 'mm', precision: 2 },
  { label: '下底长', prop: 'bottom_length', type: 'number', unit: 'mm', precision: 2 },
  { label: '高', prop: 'height', type: 'number', unit: 'mm', precision: 2 },
]

const gateAnnulusItems: FormItem[] = [
  { label: '外径', prop: 'outer_diameter', type: 'number', unit: 'mm', precision: 2 },
  { label: '内径', prop: 'inner_diameter', type: 'number', unit: 'mm', precision: 2 },
  { label: '间距', prop: 'gap', type: 'number', unit: 'mm', precision: 2 },
]

// ============================================================================
// 条件显示
// ============================================================================
//
// 原 runnerTypeHint 已删除（2026-09-07）：
// - 原因：流道类型提示不再用 el-alert 展示，改为在 MoldForm 的 tab label 上以 tag 形式呈现
// - 如果未来需要在某处重新显示提示语，可从这里恢复逻辑
//

const showHotRunner = computed(() =>
  props.gatingSystem.runner_type === '热流道' ||
  props.gatingSystem.runner_type === '热转冷'
)

const showColdRunner = computed(() =>
  props.gatingSystem.runner_type === '冷流道' ||
  props.gatingSystem.runner_type === '热转冷'
)

// ============================================================================
// 折叠状态管理（本地 ref，不放数据对象上避免序列化）
// ============================================================================

/**
 * Cavity 折叠状态：默认全部展开（便于查看）
 * - value: 展开的 cavity 索引数组
 */
// 折叠状态全部移到 GatingCavityPanel 内部（每个 panel 管自己的 gate 列表）
// Cavity 改为平铺，不再需要外层折叠

// ============================================================================
// 添加 / 删除
// ============================================================================

function addCavity() {
  props.gatingSystem.cavities.push(structuredClone(cavityForm))
  ElMessage.success('已添加产品')
}

function removeCavity(cIdx: number) {
  if (props.gatingSystem.cavities.length <= 1) {
    ElMessage.warning('至少需要保留 1 个产品')
    return
  }
  props.gatingSystem.cavities.splice(cIdx, 1)
  ElMessage.success('已删除产品')
  // 注：Gate 折叠状态在 GatingCavityPanel 内部，删除 cavity 时 panel 随之销毁
}

</script>

<style scoped lang="scss">
/*
 * 折叠相关样式
 * - collapse-title：左侧图标 + 标题 + 右侧 tag
 * - collapse-actions：右上角操作按钮（删除）
 * - collapse-body：折叠体内边距
 * - add-button-wrapper：底部添加按钮居中
 */
/*
 * cavity 平铺列表：每个 cavity 一个块，块间留空
 * - border + 浅背景色分隔（视觉上像"卡片"，但不嵌套 el-card）
 * - 单 cavity 场景下视觉简洁，多 cavity 场景下可横向对比
 */
.cavity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-button-wrapper {
  display: flex;
  justify-content: flex-start;
  margin: 8px 0 0;
  padding: 0;
}
</style>
