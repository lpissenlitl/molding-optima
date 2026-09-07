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
          <el-row :gutter="24">
            <el-col
              v-for="(item, iIdx) in basicItems"
              :key="`basic_${iIdx}`"
              :span="item.span || 6"
            >
              <el-form-item :label="item.label" :prop="item.prop">
                <!-- cavity_layout 带 tooltip -->
                <el-tooltip
                  v-if="item.prop === 'cavity_layout'"
                  effect="dark"
                  placement="top"
                >
                  <template #content>
                    1: 单色模具, 单腔, 共1个制品<br>
                    1+1: 单色模具, 两腔, 共2个制品, 制品参数不同<br>
                    1*2: 单色模具, 两腔, 共2个制品, 制品参数相同<br>
                    1&1: 双色模具, 1射单腔, 成型1个制品, 2射单腔, 成型1个制品<br>
                    1&1+1: 双色模具, 1射单腔, 成型1个制品, 2射双腔, 成型2个制品, 制品参数不同
                  </template>
                  <el-input
                    v-model.trim="mold_info[item.prop!]"
                    :placeholder="getPlaceholder(item)"
                    :disabled="getDisabled(item)"
                  >
                    <template #suffix v-if="item.unit">{{ item.unit }}</template>
                  </el-input>
                </el-tooltip>

                <el-input
                  v-else-if="item.type === 'input'"
                  v-model.trim="mold_info[item.prop!]"
                  :placeholder="getPlaceholder(item)"
                  :disabled="getDisabled(item)"
                >
                  <template #suffix v-if="item.unit">{{ item.unit }}</template>
                </el-input>

                <el-input
                  v-else-if="item.type === 'number' || item.type === 'integer'"
                  v-model.trim="mold_info[item.prop!]"
                  v-number="getPrecision(item)"
                  :placeholder="getPlaceholder(item)"
                  :disabled="getDisabled(item)"
                >
                  <template #suffix v-if="item.unit">{{ item.unit }}</template>
                </el-input>

                <el-input
                  v-else-if="item.type === 'textarea'"
                  v-model="mold_info[item.prop!]"
                  type="textarea"
                  :rows="item.rows || 3"
                  :placeholder="getPlaceholder(item)"
                  :disabled="getDisabled(item)"
                />

                <el-select
                  v-else-if="item.type === 'select' || item.type === 'number-select'"
                  v-model="mold_info[item.prop!]"
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

                <el-radio-group
                  v-else-if="item.type === 'radio'"
                  v-model="mold_info[item.prop!]"
                  :disabled="getDisabled(item)"
                >
                  <el-radio-button :label="true">是</el-radio-button>
                  <el-radio-button :label="false">否</el-radio-button>
                </el-radio-group>
              </el-form-item>
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
          title="浇注系统支持多次注射（由基本信息中的注射次数控制）。每次注射可独立配置流道类型、产品参数与浇口。"
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
            <GatingSystemForm :gating-system="gating" />
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- ============ 3. 冷却系统 ============ -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">冷却系统</span>
        </template>
        <CoolingSystemForm :cooling-system="cooling_system" />
      </el-card>

      <!-- ============ 4. 顶出系统 ============ -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">顶出系统</span>
        </template>
        <EjectionSystemForm :ejection-system="ejection_system" />
      </el-card>

      <!-- ============ 5. 其他参数 ============ -->
      <el-card class="custom-form__section" shadow="never">
        <template #header>
          <span class="custom-form__title">其他参数</span>
        </template>
        <el-form
          :model="mold_info"
          class="custom-form"
          label-width="120px"
        >
          <el-row :gutter="24">
            <el-col
              v-for="(item, iIdx) in structureItems"
              :key="`struct_${iIdx}`"
              :span="item.span || 6"
            >
              <el-form-item :label="item.label" :prop="item.prop">
                <el-input
                  v-if="item.type === 'input'"
                  v-model.trim="mold_info[item.prop!]"
                  :placeholder="getPlaceholder(item)"
                  :disabled="getDisabled(item)"
                >
                  <template #suffix v-if="item.unit">{{ item.unit }}</template>
                </el-input>

                <el-input
                  v-else-if="item.type === 'number' || item.type === 'integer'"
                  v-model.trim="mold_info[item.prop!]"
                  v-number="getPrecision(item)"
                  :placeholder="getPlaceholder(item)"
                  :disabled="getDisabled(item)"
                >
                  <template #suffix v-if="item.unit">{{ item.unit }}</template>
                </el-input>

                <el-input
                  v-else-if="item.type === 'textarea'"
                  v-model="mold_info[item.prop!]"
                  type="textarea"
                  :rows="item.rows || 3"
                  :placeholder="getPlaceholder(item)"
                  :disabled="getDisabled(item)"
                />

                <el-select
                  v-else-if="item.type === 'select' || item.type === 'number-select'"
                  v-model="mold_info[item.prop!]"
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

                <el-radio-group
                  v-else-if="item.type === 'radio'"
                  v-model="mold_info[item.prop!]"
                  :disabled="getDisabled(item)"
                >
                  <el-radio-button :label="true">是</el-radio-button>
                  <el-radio-button :label="false">否</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 辅助装置（多选） -->
          <el-divider content-position="left" class="custom-form__divider">
            辅助装置
          </el-divider>
          <el-alert
            title="辅助装置指安装在模具上的功能性附加设备，例如：液压抽芯油缸、气动阀、热流道温控箱、模内传感器等。可从下拉中选择，或直接输入自定义名称。"
            type="info"
            show-icon
            :closable="false"
            style="margin-bottom: 12px;"
          />
          <el-select
            v-model="checked_assist_equipments"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请选择或输入辅助装置"
            style="width: 100%;"
          >
            <el-option
              v-for="item in assistEquipmentOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
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
import {
  getPlaceholder,
  getDisabled,
  getPrecision,
} from '@/utils/form-helper'
import type { FormItem } from '@/utils/form-types'
import { hasPermission } from '@/utils/permission'

import GatingSystemForm from '../components/GatingSystemForm.vue'
import CoolingSystemForm from '../components/CoolingSystemForm.vue'
import EjectionSystemForm from '../components/EjectionSystemForm.vue'

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

const basicItems: FormItem[] = [
  { label: '模具编号', prop: 'mold_no', type: 'input' },
  { label: '模具名称', prop: 'mold_name', type: 'input' },
  { label: '模具类型', prop: 'mold_type', type: 'select', options: moldTypeOptions },
  { label: '模具类别', prop: 'category', type: 'select', options: moldCategoryOptions },
  { label: '模具结构', prop: 'structure', type: 'select', options: moldStructureOptions },
  { label: '注射次数', prop: 'shot_count', type: 'select', options: shotCountOptions },
  { label: '模腔布局', prop: 'cavity_layout', type: 'input' },
  { label: '目标成型周期', prop: 'target_cycle_time', type: 'number', unit: 's', precision: 2 },
  { label: '客户机吨位', prop: 'recommended_tonnage', type: 'number', unit: 'Ton', precision: 0 },
  // "总注射重量" 故意不展示：多射下不同材料相加无意义，重量已在 GatingSystem 按射维护
  // 如需恢复：取消下一行注释
  // { label: '总注射重量', prop: 'total_injection_weight', type: 'number', unit: 'g', precision: 2 },
  { label: '产品大类', prop: 'product_category', type: 'select', options: productMajorOptions },
  { label: '产品中类', prop: 'product_subcategory', type: 'select', options: [] },  // 联动 mediumOptionsMap[product_category]
  { label: '产品小类', prop: 'product_model', type: 'select', options: [] },  // 联动 minorOptionsMap[product_subcategory]
  { label: '产品描述', prop: 'product_description', type: 'textarea', span: 24, rows: 3 },
]

const structureItems: FormItem[] = [
  { label: '模具长度', prop: 'mold_length', type: 'number', unit: 'mm', precision: 2 },
  { label: '模具宽度', prop: 'mold_width', type: 'number', unit: 'mm', precision: 2 },
  { label: '模具厚度', prop: 'mold_thickness', type: 'number', unit: 'mm', precision: 2 },
  { label: '模具重量', prop: 'mold_weight', type: 'number', unit: 'kg', precision: 2 },
  { label: '吊装类型', prop: 'handling_type', type: 'select', options: liftingTypeOptions },
  { label: '吊环规格', prop: 'handling_thread_size', type: 'select', options: liftingEyeBoltOptions },
  { label: '吊装点数量', prop: 'handling_point_count', type: 'integer', unit: '个', precision: 0 },
  { label: '定模定位圈外径', prop: 'locating_ring_outer_dia', type: 'number-select', options: locatingRingOuterDiaOptions, unit: 'mm' },
  { label: '定模定位圈内径', prop: 'locating_ring_inner_dia', type: 'number', unit: 'mm', precision: 2 },
  { label: '定模定位圈高度', prop: 'locating_ring_height', type: 'number', unit: 'mm', precision: 2 },
  { label: '动模定位圈外径', prop: 'mov_half_locating_ring_outer_dia', type: 'number-select', options: movingLocatingRingOuterDiaOptions, unit: 'mm' },
  { label: '动模定位圈内径', prop: 'mov_half_locating_ring_inner_dia', type: 'number', unit: 'mm', precision: 2 },
  { label: '动模定位圈高度', prop: 'mov_half_locating_ring_height', type: 'number', unit: 'mm', precision: 2 },
  { label: '取件方式', prop: 'part_removal_action', type: 'select', options: partRemovalActionOptions },
  { label: '开模行程', prop: 'recommended_opening_stroke', type: 'number', unit: 'mm', precision: 2 },
  { label: '流道分离距离', prop: 'runner_separation_distance', type: 'number', unit: 'mm', precision: 2 },
  { label: '最小锁模力', prop: 'min_clamping_force', type: 'number', unit: 'Ton', precision: 0 },
]

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
  if (!formRef.value) return
  try {
    await formRef.value.validate()
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
 * - max-width: 1400px 大表单居中展示
 */
.mold-form {
  padding: 16px 16px 96px;
  max-width: 1400px;
  margin: 0 auto;
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
