<!--
  MoldForm - 模具表单页（新建 + 编辑共用）

  路由（与 project 保持 RESTful 风格）：
    - /mold/new              新建模式（?project_id=X 可预填项目上下文）
    - /mold/:id/edit         编辑模式（自动加载详情）

  设计要点：
    - 单文件处理 add / edit 两种模式（通过 useRoute 区分）
    - 5 个 section 顶层用 el-card 平铺（不折叠，避免信息被忽略）
    - 浇注系统 1:N（el-tabs 包裹），冷却/顶出 1:1（直接调用子组件）
    - 子组件双向绑定 props 传入的 reactive 对象
-->
<template>
  <div class="mold-form">
    <!-- 顶部：返回列表 -->
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
    </div>

    <!-- 编辑模式的加载占位 -->
    <div v-if="!loaded" v-loading="true" class="loading-placeholder"></div>

    <!-- 5 个 section（el-card 平铺，始终可见，层次清晰） -->
    <div v-else class="mold-cards">
      <!-- ============ 1. 基本信息 ============ -->
      <!--
        架构：flat items 数组 + groupIntoRows 自动分行 + FormFieldRenderer 复用渲染
        - cavity_layout 是特殊字段（带 tooltip），单独渲染
        - 其余字段统一走 FormFieldRenderer（去重 ~50 行 v-else-if 链）
      -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">基本信息</span>
        </template>
        <el-form
          ref="formRef"
          :model="mold_info"
          :rules="rules"
          class="custom-form"
          label-width="120px"
        >
          <el-row
            v-for="(row, rIdx) in basicRows"
            :key="`basic_row_${rIdx}`"
            :gutter="24"
          >
            <el-col
              v-for="(item, iIdx) in row"
              :key="`basic_${rIdx}_${iIdx}`"
              :span="item.span"
            >
              <!-- 特殊字段：cavity_layout 带领域知识 tooltip -->
              <el-form-item
                v-if="item.prop === 'cavity_layout'"
                :label="item.label"
                :prop="item.prop"
              >
                <el-tooltip effect="dark" placement="top">
                  <template #content>
                    1: 单色模具, 单腔, 共1个制品<br>
                    1+1: 单色模具, 两腔, 共2个制品, 制品参数不同<br>
                    1*2: 单色模具, 两腔, 共2个制品, 制品参数相同<br>
                    1&1: 双色模具, 1射单腔, 成型1个制品, 2射单腔, 成型1个制品<br>
                    1&1+1: 双色模具, 1射单腔, 成型1个制品, 2射双腔, 成型2个制品, 制品参数不同
                  </template>
                  <el-input
                    v-model.trim="mold_info.cavity_layout"
                    placeholder="输入或点击查看格式说明"
                  />
                </el-tooltip>
              </el-form-item>

              <!-- 常规字段：FormFieldRenderer 统一渲染 -->
              <FormFieldRenderer
                v-else
                :item="item"
                :model="mold_info"
              />
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- ============ 2. 浇注系统 ============ -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">浇注系统</span>
        </template>
        <el-alert
          title="每次注射可独立配置流道类型、产品参数与浇口"
          type="info"
          show-icon
          :closable="false"
          style="margin-bottom: 16px;"
        />
        <el-tabs v-model="activeGating" class="gating-tabs">
          <el-tab-pane
            v-for="(gating, idx) in mold_info.gating_systems"
            :key="`gating_${idx}`"
            :name="String(idx)"
          >
            <!--
             * tab label 平级信息：
             * - “第 N 射”（标识）+ 状态色（热/冷/混合/未选）
             * - 纯文字+颜色，不加背景/边框/字号差（避免与主标签“争权重”）
             -->
            <template #label>
              <span class="gating-tab-label">
                <span class="gating-tab-label__index">第 {{ Number(idx) + 1 }} 射</span>
                <span
                  class="gating-tab-label__badge"
                  :class="`gating-tab-label__badge--${getRunnerTypeClass(gating.runner_type)}`"
                >
                  {{ getRunnerTypeLabel(gating.runner_type) }}
                </span>
              </span>
            </template>
            <GatingSystemForm ref="gatingFormRefs" :gating-system="gating" />
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- ============ 3. 冷却系统 ============ -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">冷却系统</span>
        </template>
        <CoolingSystemForm ref="coolingFormRef" :cooling-system="cooling_system" />
      </el-card>

      <!-- ============ 4. 顶出系统 ============ -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">顶出系统</span>
        </template>
        <EjectionSystemForm ref="ejectionFormRef" :ejection-system="ejection_system" />
      </el-card>

      <!-- ============ 5. 其他参数 ============ -->
      <!--
        架构：flat items 数组 + groupIntoRows 自动分行 + FormFieldRenderer 复用渲染
        - 所有字段均为常规字段（无特殊装饰），统一走 FormFieldRenderer
        - 末尾 辅助装置 为领域知识 tooltip + 多选，独立渲染
      -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">其他参数</span>
        </template>
        <el-form
          :model="mold_info"
          class="custom-form"
          label-width="120px"
        >
          <el-row
            v-for="(row, rIdx) in structureRows"
            :key="`struct_row_${rIdx}`"
            :gutter="24"
          >
            <el-col
              v-for="(item, iIdx) in row"
              :key="`struct_${rIdx}_${iIdx}`"
              :span="item.span"
            >
              <FormFieldRenderer :item="item" :model="mold_info" />
            </el-col>
          </el-row>

          <!-- 辅助装置（多选）：领域知识用 tooltip，按需 hover 查看 -->
          <el-divider content-position="left" class="custom-form__divider">
            辅助装置
          </el-divider>
          <el-tooltip
            content="辅助装置是安装在模具上的功能性附加设备，例如：液压抽芯油缸、气动阀、热流道温控箱、模内传感器等。"
            placement="top"
          >
            <el-select
              v-model="checked_assist_equipments"
              multiple
              filterable
              :allow-create="true"
              default-first-option
              placeholder="请选择或输入辅助装置（如液压抽芯、热流道温控箱）"
              style="width: 100%;"
            >
              <el-option
                v-for="item in assistEquipmentOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-tooltip>
        </el-form>
      </el-card>
    </div>

    <!-- 操作按钮（fixed bottom，全局样式） -->
    <div v-if="loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        :disabled="!hasPermission('update_mold')"
        @click="handleSave"
      >
        {{ is_edit ? '保存' : '创建' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { moldMethod } from '@/api'
import {
  moldInfoForm,
  gatingSystemForm,
  moldTypeOptions,
  moldCategoryOptions,
  moldStructureOptions,
  shotCountOptions,
  partRemovalActionOptions,
  liftingTypeOptions,
  liftingEyeBoltOptions,
  locatingRingOuterDiaOptions,
  movingLocatingRingOuterDiaOptions,
  assistEquipmentOptions,
} from '@/constants/mold-const'
import {
  productMajorOptions,
  mediumOptionsMap,
  minorOptionsMap,
} from '@/utils/product-category'
import GatingSystemForm from '../components/GatingSystemForm.vue'
import CoolingSystemForm from '../components/CoolingSystemForm.vue'
import EjectionSystemForm from '../components/EjectionSystemForm.vue'
import FormFieldRenderer from '../components/FormFieldRenderer.vue'
import type { FormItem } from '@/utils/form-types'
import { groupIntoRows } from '@/utils/form-layout'
import { hasPermission } from '@/utils/permission'

// ============================================================================
// 路由（核心：通过 useRoute 区分新建/编辑模式，与 project 保持一致）
// ============================================================================

const route = useRoute()
const router = useRouter()

/** 是否编辑模式（路由参数中含 id） */
const is_edit = computed(() => !!route.params.id)

/** 编辑模式下的模具 id */
const mold_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

/** 新建模式下从项目跳转带入的 project_id（用于预填上下文） */
const project_id_from_route = computed(() => {
  const pid = route.query.project_id
  return pid ? Number(pid) : null
})

// ============================================================================
// 响应式状态
// ============================================================================

const mold_info = ref<any>(structuredClone(moldInfoForm))
const formRef = ref<FormInstance>()
/**
 * 所有浇注系统子表单的引用数组（2026-09-08 引入）
 * - 每个 GatingSystemForm 暴露自己的 formRef
 * - 保存时遍历调用所有 formRef.validate()，实现跨表单统一验证
 */
const gatingFormRefs = ref<any[]>([])
/**
 * 冷却系统子表单引用（1:1）
 */
const coolingFormRef = ref<any>(null)
/**
 * 顶出系统子表单引用（1:1）
 */
const ejectionFormRef = ref<any>(null)
const loading = ref(false)
const submitting = ref(false)
const loaded = ref(false)

/** 冷却系统（1:1 子组件 props） */
const cooling_system = computed(() => mold_info.value.cooling_system)

/** 顶出系统（1:1 子组件 props） */
const ejection_system = computed(() => mold_info.value.ejection_system)

/**
 * 流道类型 → badge 文字颜色 class
 * 热流道→hot（红）/ 冷流道→cold（蓝）/ 热转冷→mixed（橙）/ 未选→empty（灰）
 */
function getRunnerTypeClass(runnerType: string): 'hot' | 'cold' | 'mixed' | 'empty' {
  if (runnerType === '热流道') return 'hot'
  if (runnerType === '冷流道') return 'cold'
  if (runnerType === '热转冷') return 'mixed'
  return 'empty'
}

/**
 * 流道类型 → badge 文字映射
 * - 未选时显示“未选”，不显示空 label
 */
function getRunnerTypeLabel(runnerType: string): string {
  if (runnerType === '热流道') return '热流道'
  if (runnerType === '冷流道') return '冷流道'
  if (runnerType === '热转冷') return '热转冷'
  return '未选'
}

/** 浇注系统 tabs（默认第一个） */
const activeGating = ref('0')

/** 辅助装置（双向绑定到 mold_info.mechanism） */
const checked_assist_equipments = computed({
  get(): string[] {
    if (mold_info.value.mechanism) {
      return mold_info.value.mechanism.split('|').filter(Boolean)
    }
    return []
  },
  set(value: string[]) {
    mold_info.value.mechanism = value.length > 0 ? value.join('|') : null
  },
})

// ============================================================================
// 字段定义
// ============================================================================

// 硬编码分类 select：显式 allowCreate: false，禁止用户创建无意义的自定义值
const basicItems: FormItem[] = [
  { label: '模具编号', prop: 'mold_no', type: 'input' },
  { label: '模具名称', prop: 'mold_name', type: 'input' },
  { label: '模具类型', prop: 'mold_type', type: 'select', options: moldTypeOptions, allowCreate: false },
  { label: '模具类别', prop: 'category', type: 'select', options: moldCategoryOptions, allowCreate: false },
  { label: '模具结构', prop: 'structure', type: 'select', options: moldStructureOptions, allowCreate: false },
  { label: '注射次数', prop: 'shot_count', type: 'select', options: shotCountOptions, allowCreate: false },
  { label: '模腔布局', prop: 'cavity_layout', type: 'input' },
  { label: '目标成型周期', prop: 'target_cycle_time', type: 'number', unit: 's', precision: 2 },
  { label: '客户机吨位', prop: 'recommended_tonnage', type: 'number', unit: 'Ton', precision: 0 },
  // "总注射重量" 故意不展示：多射下不同材料相加无意义，重量已在 GatingSystem 按射维护
  // 如需恢复：取消下一行注释
  // { label: '总注射重量', prop: 'total_injection_weight', type: 'number', unit: 'g', precision: 2 },
  { label: '产品大类', prop: 'product_category', type: 'select', options: productMajorOptions, allowCreate: false },
  { label: '产品中类', prop: 'product_subcategory', type: 'select', options: [], allowCreate: false },  // 联动 mediumOptionsMap[product_category]
  { label: '产品小类', prop: 'product_model', type: 'select', options: [], allowCreate: false },  // 联动 minorOptionsMap[product_subcategory]
  { label: '产品描述', prop: 'product_description', type: 'textarea', span: 24, rows: 3 },
]

// 硬编码分类 select 显式 allowCreate: false；规格值字段（定位圈外径等）保留 true
const structureItems: FormItem[] = [
  { label: '模具长度', prop: 'mold_length', type: 'number', unit: 'mm', precision: 2 },
  { label: '模具宽度', prop: 'mold_width', type: 'number', unit: 'mm', precision: 2 },
  { label: '模具厚度', prop: 'mold_thickness', type: 'number', unit: 'mm', precision: 2 },
  { label: '模具重量', prop: 'mold_weight', type: 'number', unit: 'kg', precision: 2 },
  { label: '吊装类型', prop: 'handling_type', type: 'select', options: liftingTypeOptions, allowCreate: false },
  { label: '吊环规格', prop: 'handling_thread_size', type: 'select', options: liftingEyeBoltOptions, allowCreate: false },
  { label: '吊装点数量', prop: 'handling_point_count', type: 'integer', unit: '个', precision: 0 },
  { label: '定模定位圈外径', prop: 'locating_ring_outer_dia', type: 'number-select', options: locatingRingOuterDiaOptions, unit: 'mm' },
  { label: '定模定位圈内径', prop: 'locating_ring_inner_dia', type: 'number', unit: 'mm', precision: 2 },
  { label: '定模定位圈高度', prop: 'locating_ring_height', type: 'number', unit: 'mm', precision: 2 },
  { label: '动模定位圈外径', prop: 'mov_half_locating_ring_outer_dia', type: 'number-select', options: movingLocatingRingOuterDiaOptions, unit: 'mm' },
  { label: '动模定位圈内径', prop: 'mov_half_locating_ring_inner_dia', type: 'number', unit: 'mm', precision: 2 },
  { label: '动模定位圈高度', prop: 'mov_half_locating_ring_height', type: 'number', unit: 'mm', precision: 2 },
  { label: '取件方式', prop: 'part_removal_action', type: 'select', options: partRemovalActionOptions, allowCreate: false },
  { label: '开模行程', prop: 'recommended_opening_stroke', type: 'number', unit: 'mm', precision: 2 },
  { label: '流道分离距离', prop: 'runner_separation_distance', type: 'number', unit: 'mm', precision: 2 },
  { label: '最小锁模力', prop: 'min_clamping_force', type: 'number', unit: 'Ton', precision: 0 },
]

// 自动分行（4 列布局，divider 自动占满一行）
const basicRows = computed(() => groupIntoRows(basicItems, { columns: 4 }))
const structureRows = computed(() => groupIntoRows(structureItems, { columns: 4 }))

// ============================================================================
// 验证规则
// ============================================================================

const rules: FormRules = {
  mold_no: [
    { required: true, message: '模具编号不能为空', trigger: 'blur' },
  ],
}

// ============================================================================
// 联动：shot_count → gating_systems 数组
// ============================================================================

watch(
  () => mold_info.value.shot_count,
  (newCount) => {
    if (!newCount || newCount < 1) return
    const gs_count = mold_info.value.gating_systems.length
    if (newCount < gs_count) {
      mold_info.value.gating_systems.splice(newCount, gs_count - newCount)
    } else if (newCount > gs_count) {
      for (let i = gs_count; i < newCount; i++) {
        mold_info.value.gating_systems.push(structuredClone(gatingSystemForm))
      }
    }
  }
)

// ============================================================================
// 联动：product_category / product_subcategory → subcategory / model options
// ============================================================================

watch(
  () => mold_info.value.product_category,
  (val) => {
    // 重置 subcategory
    mold_info.value.product_subcategory = null
    mold_info.value.product_model = null
    const subCat = basicItems.find((i) => i.prop === 'product_subcategory')
    if (subCat) subCat.options = (mediumOptionsMap as Record<string, any>)[val] || []
  }
)

watch(
  () => mold_info.value.product_subcategory,
  (val) => {
    // 重置 model
    mold_info.value.product_model = null
    const model = basicItems.find((i) => i.prop === 'product_model')
    if (model) model.options = (minorOptionsMap as Record<string, any>)[val] || []
  }
)

// ============================================================================
// 操作
// ============================================================================

function goBack() {
  router.push('/mold/list')
}

async function handleSave() {
  // 1. 顶层表单验证（mold_no 等）
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请检查必填项')
    return
  }

  // 2. 所有 GatingSystemForm 子表单验证（流道类别等）
  for (const gatingForm of gatingFormRefs.value) {
    try {
      await gatingForm?.formRef?.validate()
    } catch {
      ElMessage.warning('请检查必填项')
      return
    }
  }

  // 3. 冷却系统 / 顶出系统子表单验证（预留扩展点，rules 当前为空）
  try {
    await coolingFormRef.value?.formRef?.validate()
  } catch {
    ElMessage.warning('请检查必填项')
    return
  }
  try {
    await ejectionFormRef.value?.formRef?.validate()
  } catch {
    ElMessage.warning('请检查必填项')
    return
  }

  submitting.value = true
  try {
    // 清理 null 值（保留 0、空字符串以外的有效值）
    const payload: any = {}
    for (const [key, val] of Object.entries(mold_info.value)) {
      if (val !== null && val !== '') {
        payload[key] = val
      }
    }

    let res: any
    if (mold_id.value !== null) {
      res = await moldMethod.edit(payload, mold_id.value)
    } else {
      res = await moldMethod.add(payload)
    }

    if (res.status === 0) {
      ElMessage.success(mold_id.value ? '模具信息编辑成功！' : '模具信息新增成功！')
      goBack()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (err: any) {
    console.error('[MoldForm] save failed:', err)
    ElMessage.error(err?.message || '提交异常')
  } finally {
    submitting.value = false
  }
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(async () => {
  // 从项目跳转创建 → 预填 project_id
  if (!is_edit.value && project_id_from_route.value !== null) {
    mold_info.value.project_id = project_id_from_route.value
  }

  if (is_edit.value && mold_id.value !== null) {
    await loadDetail(mold_id.value)
  } else {
    loaded.value = true
  }
})

async function loadDetail(id: number) {
  loading.value = true
  try {
    const res: any = await moldMethod.getDetail(id)
    if (res.status === 0) {
      Object.assign(mold_info.value, res.data)
      loaded.value = true
    } else {
      ElMessage.error(res.msg || '未读取到相关模具信息')
      router.push('/mold/list')
    }
  } catch (err: any) {
    console.error('[MoldForm] loadDetail failed:', err)
    ElMessage.error(err?.message || '加载模具详情异常')
    router.push('/mold/list')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
/*
 * mold-form 容器
 * - padding-bottom: 96px 预留底部 form-actions 空间（避免内容被遮挡）
 * - 全宽展示（工业软件充分利用屏幕宽度）
 */
.mold-form {
  padding: 16px 16px 96px;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 16px;
}

.loading-placeholder {
  height: 400px;
}

/*
 * 5 个 el-card 平铺布局
 * - display: flex + flex-direction: column：垂直堆叠
 * - gap: 16px：card 之间的间距（代替 margin-bottom，避免边界问题）
 */
.mold-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/*
 * 浇注系统 tabs 强化：
 * - tab bar 浅灰底+圆角，让“tab 通道”立体
 * - badge 纯文字+颜色，与主标签“第 N 射”同号同重（14px / 500），靠颜色区分状态
 * - 4 个状态用 BEM modifier：--hot / --cold / --mixed / --empty
 */
.gating-tabs {
  :deep(.el-tabs__nav-wrap) {
    background: var(--color-bg-page);
    border-radius: 6px;
    padding: 0 8px;
    margin-bottom: 4px;
  }
}

.gating-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 100%;

  &__index {
    font-weight: 500;
  }

  &__badge {
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 0;
    white-space: nowrap;

    &--hot {
      color: #f56c6c;
    }

    &--cold {
      color: #409eff;
    }

    &--mixed {
      color: #e6a23c;
    }

    &--empty {
      color: #c0c4cc;
    }
  }
}
</style>
