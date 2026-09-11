<!--
  PolymerForm - 聚合物表单（new / edit / copy 三模式共用）

  路由：
    - /material/polymer/new         新建
    - /material/polymer/:id/edit    编辑
    - /material/polymer/:id/copy    复制（清空 id 和 grade）

  架构（2026-09-08）：
    - 9 个 section 拆为 3 个开关分组：basicCards（基本信息 / 推荐工艺，始终展示）+ 填充物组成（开关）+ simulationCards（PVT / 流变 / 机械 / 收缩，开关）
    - 仿真参数 + 填充物组成默认隐藏，避免对普通用户造成填写负担
    - 开关始终可见（独立 card），打开后对应 section 平铺
    - 4 列布局，divider 仅保留 3+ 字段领域分组
-->
<template>
  <div class="polymer-form">
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
    </div>

    <div v-if="!loaded" v-loading="true" class="loading-placeholder"></div>

    <el-form
      v-else
      ref="formRef"
      :model="polymer_info"
      :rules="rules"
      class="custom-form"
      label-width="120px"
    >
      <!-- 基本 cards（始终展示） -->
      <el-card
        v-for="(card, cIdx) in basicCards"
        :key="`basic_${cIdx}`"
        class="custom-form__section"
        shadow="never"
      >
        <template #header>
          <span class="custom-form__title">{{ card.title }}</span>
        </template>

        <el-row
          v-for="(row, rIdx) in basicCardRows[cIdx].rows"
          :key="`basic_${cIdx}_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`field_${cIdx}_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <el-divider
              v-if="item.type === 'divider'"
              content-position="left"
              class="custom-form__divider"
            >
              {{ item.label }}
            </el-divider>

            <el-form-item
              v-else-if="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'input'"
                v-model.trim="getCardModel(card.title)[item.prop!]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>

              <el-input
                v-else-if="item.type === 'number'"
                v-model.trim="getCardModel(card.title)[item.prop!]"
                v-number="getPrecision(item)"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>

              <el-select
                v-else-if="item.type === 'select'"
                v-model="getCardModel(card.title)[item.prop!]"
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

              <el-autocomplete
                v-else-if="item.type === 'autocomplete'"
                v-model="getCardModel(card.title)[item.prop!]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
                :debounce="0"
                :fetch-suggestions="querySuggestions(item.query)"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 填充物组成开关 card（始终展示） -->
      <el-card class="custom-form__section custom-form__section--toggle" shadow="never">
        <div class="filler-toggle">
          <div class="filler-toggle__info">
            <AppIcon icon="mdi:grain" class="filler-toggle__icon" />
            <div class="filler-toggle__text">
              <div class="filler-toggle__title">填充物组成（详细配置）</div>
              <div class="filler-toggle__desc">
                本材料是否需要详细列出所含填充物（如玻璃纤维、碳酸钙）及各自含量？仅靠厂商信息时可关闭。
              </div>
            </div>
          </div>
          <el-switch
            v-model="showFillerComposition"
            active-text="配置填充物"
            inactive-text="仅塑料信息"
            inline-prompt
            style="--el-switch-on-color: #67c23a;"
          />
        </div>
      </el-card>

      <!-- 填充物组成 section（开关打开时展示） -->
      <el-card
        v-show="showFillerComposition"
        class="custom-form__section"
        shadow="never"
      >
        <template #header>
          <div class="filler-section-header">
            <span class="custom-form__title">填充物组成</span>
            <div class="filler-section-header__actions">
              <span class="filler-total">
                总含量：<strong :class="{ 'filler-total--over': filler_total_percentage > 100 }">{{ filler_total_percentage.toFixed(2) }}%</strong>
              </span>
              <el-button type="primary" size="small" plain @click="addFillerRow">
                <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
                新增填充物
              </el-button>
            </div>
          </div>
        </template>

        <table class="filler-table">
          <thead>
            <tr>
              <th class="filler-col-name">填充物</th>
              <th class="filler-col-pct">含量 (%)</th>
              <th class="filler-col-note">备注</th>
              <th class="filler-col-action">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!polymer_info.polymer_filler_compositions || polymer_info.polymer_filler_compositions.length === 0">
              <td colspan="4" class="filler-empty">
                暂无填充物，点击右上角“新增填充物”添加
              </td>
            </tr>
            <tr v-for="(row, idx) in polymer_info.polymer_filler_compositions" :key="`filler_${idx}`">
              <td>
                <el-select
                  v-model="row.filler_id"
                  placeholder="选择填充物"
                  filterable
                  clearable
                  style="width: 100%;"
                >
                  <el-option
                    v-for="opt in filler_select_options"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
              </td>
              <td>
                <el-input
                  v-model.trim="row.percentage"
                  v-number="2"
                  placeholder="含量"
                  clearable
                >
                  <template #append>%</template>
                </el-input>
              </td>
              <td>
                <el-input
                  v-model.trim="row.note"
                  placeholder="可选备注"
                  clearable
                />
              </td>
              <td class="filler-col-action">
                <el-button type="text"
                  class="text-danger"
                  @click="removeFillerRow(idx)"
                >
                  <AppIcon icon="mdi:delete-outline" style="margin-right: 2px; font-size: 14px;" />
                  删除
                </el-button>
              </td>
            </tr>
          </tbody>
        </table>
      </el-card>

      <!-- 仿真参数开关 card（始终展示） -->
      <el-card class="custom-form__section custom-form__section--toggle" shadow="never">
        <div class="simulation-toggle">
          <div class="simulation-toggle__info">
            <AppIcon icon="mdi:flask-outline" class="simulation-toggle__icon" />
            <div class="simulation-toggle__text">
              <div class="simulation-toggle__title">仿真用材料参数（高级）</div>
              <div class="simulation-toggle__desc">
                本材料是否需要填写 PVT / 流变 / 机械 / 收缩 等仿真参数？
              </div>
            </div>
          </div>
          <el-switch
            v-model="showSimulationParams"
            active-text="包含仿真参数"
            inactive-text="仅工艺参数"
            inline-prompt
            style="--el-switch-on-color: #409eff;"
          />
        </div>
      </el-card>

      <!-- 仿真 cards（开关打开时平铺） -->
      <el-card
        v-for="(card, cIdx) in simulationCards"
        v-show="showSimulationParams"
        :key="`sim_${cIdx}`"
        class="custom-form__section"
        shadow="never"
      >
        <template #header>
          <span class="custom-form__title">{{ card.title }}</span>
        </template>

        <el-row
          v-for="(row, rIdx) in simulationCardRows[cIdx].rows"
          :key="`sim_${cIdx}_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`sim_${cIdx}_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <el-divider
              v-if="item.type === 'divider'"
              content-position="left"
              class="custom-form__divider"
            >
              {{ item.label }}
            </el-divider>

            <el-form-item
              v-else-if="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'input'"
                v-model.trim="getCardModel(card.title)[item.prop!]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>

              <el-input
                v-else-if="item.type === 'number'"
                v-model.trim="getCardModel(card.title)[item.prop!]"
                v-number="getPrecision(item)"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
              >
                <template #suffix v-if="item.unit">{{ item.unit }}</template>
              </el-input>

              <el-select
                v-else-if="item.type === 'select'"
                v-model="getCardModel(card.title)[item.prop!]"
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

              <el-autocomplete
                v-else-if="item.type === 'autocomplete'"
                v-model="getCardModel(card.title)[item.prop!]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
                :debounce="0"
                :fetch-suggestions="querySuggestions(item.query)"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-form>

    <div v-if="loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        :disabled="!hasPermission('update_polymer')"
        @click="handleSave"
      >
        {{ is_copy ? '保存为新条目' : (is_edit ? '保存' : '创建') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { polymerMethod, fillerMethod } from '@/api'
import {
  polymerInfoForm,
  polymerAbbreivationOptions,
  polymerCategoryOptions,
  polymerDataSourceOptions,
  dryingMethodOptions,
} from '@/constants/polymer-const'
import { groupIntoRows } from '@/utils/form-layout'
import {
  getPlaceholder,
  getDisabled,
  getPrecision,
  querySuggestions,
} from '@/utils/form-helper'
import { hasPermission } from '@/utils/permission'
import type { FormCard, FormItem } from '@/utils/form-types'

const route = useRoute()
const router = useRouter()

const is_edit = computed(() => !!route.params.id && route.name !== 'material-polymer-copy')
const is_copy = computed(() => route.name === 'material-polymer-copy')
const polymer_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

const polymer_info = ref<any>(structuredClone(polymerInfoForm))
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const loaded = ref(false)

/** 是否包含仿真用材料参数（默认 false，开关控制 4 个仿真 section 显隐）*/
const showSimulationParams = ref(false)

/** 是否详细配置填充物组成（默认 false，纯靠厂商信息；用户主动打开后详细配置）*/
const showFillerComposition = ref(false)

/** 可选择的填充物列表（开关打开时加载一次）*/
const available_fillers = ref<any[]>([])

/** 填充物总含量百分比（computed，顶部展示）*/
const filler_total_percentage = computed(() => {
  const list = polymer_info.value.polymer_filler_compositions || []
  return list.reduce((sum: number, item: any) => {
    const v = Number(item?.percentage)
    return sum + (Number.isFinite(v) ? v : 0)
  }, 0)
})

// ============================================================================
// 填充物库加载
// ============================================================================

async function loadAvailableFillers() {
  if (available_fillers.value.length > 0) return // 缓存避免重复加载
  try {
    const res: any = await fillerMethod.get({ page_no: 1, page_size: 1000 })
    if (res.status === 0) {
      available_fillers.value = res.data?.items || []
    } else {
      ElMessage.warning(res.msg || '加载填充物库失败')
    }
  } catch (err: any) {
    console.error('[PolymerForm] loadAvailableFillers failed:', err)
    ElMessage.error(err?.message || '加载填充物库异常')
  }
}

function addFillerRow() {
  if (!polymer_info.value.polymer_filler_compositions) {
    polymer_info.value.polymer_filler_compositions = []
  }
  polymer_info.value.polymer_filler_compositions.push({
    filler_id: null,
    percentage: null,
    note: null,
  })
}

function removeFillerRow(index: number | string) {
  polymer_info.value.polymer_filler_compositions.splice(Number(index), 1)
}

/** 依据 filler_id 查找填充物名称（用于表格只读展示）*/
function getFillerName(filler_id: number | null): string {
  if (filler_id == null) return ''
  const found = available_fillers.value.find((f) => f.id === filler_id)
  return found ? `${found.name}（${found.abbreviation || '-'}）` : `ID: ${filler_id}`
}

/** 填充物下拉 options（用于 el-select）*/
const filler_select_options = computed(() =>
  available_fillers.value.map((f) => ({
    label: `${f.name}（${f.abbreviation || '-'}）`,
    value: f.id,
  }))
)

// 开关打开时按需加载填充物库
watch(showFillerComposition, async (val) => {
  if (val) {
    await loadAvailableFillers()
  }
})

// ============================================================================
// 字段定义
// ============================================================================

const basicItems: FormItem[] = [
  { label: '塑料简称', prop: 'abbreviation', type: 'select', options: polymerAbbreivationOptions, allowCreate: false, required: true },
  { label: '牌号', prop: 'grade', type: 'input', placeholder: '厂商具体牌号，如：PA6-GF30', required: true },
  { label: '塑料类别', prop: 'category', type: 'select', options: polymerCategoryOptions, allowCreate: false },
  { label: '塑料厂商', prop: 'manufacturer', type: 'autocomplete', query: { table: 'polymer', column: 'manufacturer' }, placeholder: '如：BASF, SABIC, 金发科技' },
  { label: '系列', prop: 'series', type: 'input', placeholder: '可选，如：Ultradur®, Luran®' },
  { label: '数据来源', prop: 'data_source', type: 'select', options: polymerDataSourceOptions, allowCreate: true },
  { label: '内部编号', prop: 'internal_id', type: 'input', placeholder: '企业内部材料编码' },
  { label: '等级代码', prop: 'level_code', type: 'input', placeholder: '如：A级、工程级、回收料等' },
  { label: '供应商代码', prop: 'vendor_code', type: 'input', placeholder: '对应采购系统的供应商编码' },
]

// 推荐工艺参数：密度（材料本体）→ 温度 → 剪切 → 杂项 → 干燥
// divider 仅保留：其他工艺参数（7 字段杂项）+ 塑料干燥参数（5 字段独立领域）
const processItems: FormItem[] = [
  { label: '熔体密度', prop: 'melt_density', type: 'number', unit: 'g/cm³', precision: 4 },
  { label: '固体密度', prop: 'solid_density', type: 'number', unit: 'g/cm³', precision: 4 },
  { label: '最小熔体温度', prop: 'min_melt_temp', type: 'number', unit: '℃' },
  { label: '最大熔体温度', prop: 'max_melt_temp', type: 'number', unit: '℃' },
  { label: '推荐熔体温度', prop: 'recommended_melt_temp', type: 'number', unit: '℃' },
  { label: '最小模具温度', prop: 'min_mold_temp', type: 'number', unit: '℃' },
  { label: '最大模具温度', prop: 'max_mold_temp', type: 'number', unit: '℃' },
  { label: '推荐模具温度', prop: 'recommended_mold_temp', type: 'number', unit: '℃' },
  { label: '最小剪切线速度', prop: 'min_shear_line_speed', type: 'number', unit: 'mm/s' },
  { label: '最大剪切线速度', prop: 'max_shear_line_speed', type: 'number', unit: 'mm/s' },
  { label: '推荐剪切线速度', prop: 'recommended_shear_line_speed', type: 'number', unit: 'mm/s' },

  { label: '其他工艺参数', type: 'divider' },
  { label: '降解温度', prop: 'degradation_temp', type: 'number', unit: '℃' },
  { label: '顶出温度', prop: 'ejection_temp', type: 'number', unit: '℃' },
  { label: '料筒停留时间', prop: 'barrel_residence_time', type: 'number', unit: 'min' },
  { label: '最大剪切速率', prop: 'max_shear_rate', type: 'number', unit: '1/s' },
  { label: '最大剪切应力', prop: 'max_shear_stress', type: 'number', unit: 'MPa' },
  { label: '推荐注射速率', prop: 'recommend_injection_rate', type: 'number', unit: 'cm³/s' },
  { label: '推荐背压', prop: 'recommend_back_pressure', type: 'number', unit: 'MPa' },

  { label: '塑料干燥参数', type: 'divider' },
  { label: '干燥方式', prop: 'drying_method', type: 'select', options: dryingMethodOptions, allowCreate: false },
  { label: '干燥温度下限', prop: 'drying_temp_min', type: 'number', unit: '℃' },
  { label: '干燥温度上限', prop: 'drying_temp_max', type: 'number', unit: '℃' },
  { label: '干燥时间下限', prop: 'drying_time_min', type: 'number', unit: 'h' },
  { label: '干燥时间上限', prop: 'drying_time_max', type: 'number', unit: 'h' },
]

// PVT 仿真参数：按物理相分类（熔体相 m → 固体相 s → 通用 Tait）
// 13 字段一气呵成，不加 divider（用户重点是"看全 PVT 配方"）
const pvtItems: FormItem[] = [
  { label: 'Tait b1m', prop: 'tait_b1m', type: 'number', unit: 'm³/kg', precision: 8 },
  { label: 'Tait b2m', prop: 'tait_b2m', type: 'number', unit: 'm³/kg-K', precision: 8 },
  { label: 'Tait b3m', prop: 'tait_b3m', type: 'number', unit: 'Pa', precision: 8 },
  { label: 'Tait b4m', prop: 'tait_b4m', type: 'number', unit: '1/K', precision: 8 },
  { label: 'Tait b1s', prop: 'tait_b1s', type: 'number', unit: 'm³/kg', precision: 8 },
  { label: 'Tait b2s', prop: 'tait_b2s', type: 'number', unit: 'm³/kg·K', precision: 8 },
  { label: 'Tait b3s', prop: 'tait_b3s', type: 'number', unit: 'Pa', precision: 8 },
  { label: 'Tait b4s', prop: 'tait_b4s', type: 'number', unit: '1/K', precision: 8 },
  { label: 'Tait b5', prop: 'tait_b5', type: 'number', unit: 'K', precision: 8 },
  { label: 'Tait b6', prop: 'tait_b6', type: 'number', unit: 'K/Pa', precision: 8 },
  { label: 'Tait b7', prop: 'tait_b7', type: 'number', unit: 'm³/kg', precision: 8 },
  { label: 'Tait b8', prop: 'tait_b8', type: 'number', unit: '1/K', precision: 8 },
  { label: 'Tait b9', prop: 'tait_b9', type: 'number', unit: '1/Pa', precision: 8 },
]

// 流变仿真参数：仅保留 2 个领域分组（Cross-WLF 参数 + MFR 测试条件）
// 删除冗余：粘度模型（1 字段）/ 接合点损失法（2 字段，label 已有前缀）/ 其他流变参数（2 字段）
const rheologyItems: FormItem[] = [
  { label: '粘度模型', prop: 'model_type', type: 'select', options: [{ label: 'Cross-WLF', value: 'cross_wlf' }], allowCreate: false },

  { label: 'Cross-WLF 参数', type: 'divider' },
  { label: 'Cross-WLF n', prop: 'cross_wlf_n', type: 'number', precision: 8 },
  { label: 'Cross-WLF tau', prop: 'cross_wlf_tau', type: 'number', unit: 'Pa', precision: 8 },
  { label: 'Cross-WLF D1', prop: 'cross_wlf_d1', type: 'number', unit: 'Pa·s', precision: 8 },
  { label: 'Cross-WLF D2', prop: 'cross_wlf_d2', type: 'number', unit: 'K', precision: 8 },
  { label: 'Cross-WLF D3', prop: 'cross_wlf_d3', type: 'number', unit: 'K/Pa', precision: 8 },
  { label: 'Cross-WLF A1', prop: 'cross_wlf_a1', type: 'number', precision: 8 },
  { label: 'Cross-WLF A2', prop: 'cross_wlf_a2', type: 'number', unit: 'K', precision: 8 },

  { label: '接合点损失法c1', prop: 'c1', type: 'number', unit: 'Pa^(1-c2)', precision: 8 },
  { label: '接合点损失法c2', prop: 'c2', type: 'number', precision: 8 },

  { label: '转换温度', prop: 'transition_temp', type: 'number', unit: '℃', precision: 8 },
  { label: '粘度指数', prop: 'viscosity_index', type: 'number', precision: 8 },

  { label: 'MFR 测试条件', type: 'divider' },
  { label: 'MFR测试温度', prop: 'mfr_temp', type: 'number', unit: '℃', precision: 2 },
  { label: 'MFR载荷', prop: 'mfr_load', type: 'number', unit: 'kg', precision: 2 },
  { label: 'MFR值', prop: 'mfr_value', type: 'number', unit: 'g/10min', precision: 2 },
]

// 机械仿真参数：仅保留 弹性性能（5 字段主体），删除 热膨胀性能（2 字段冗余）
const mechanicalItems: FormItem[] = [
  { label: '弹性性能', type: 'divider' },
  { label: '弹性模量E1', prop: 'elastic_modulus_1', type: 'number', unit: 'MPa', precision: 4 },
  { label: '弹性模量E2', prop: 'elastic_modulus_2', type: 'number', unit: 'MPa', precision: 4 },
  { label: '泊松比v12', prop: 'poisson_v12', type: 'number', precision: 4 },
  { label: '泊松比v23', prop: 'poisson_v23', type: 'number', precision: 4 },
  { label: '剪切模量G12', prop: 'shear_modulus_g12', type: 'number', unit: 'MPa', precision: 4 },

  { label: '热膨胀系数α1', prop: 'thermal_expansion_1', type: 'number', unit: '1/℃', precision: 4 },
  { label: '热膨胀系数α2', prop: 'thermal_expansion_2', type: 'number', unit: '1/℃', precision: 4 },
]

// 收缩仿真参数：6 字段全部是"收缩"类，label 前缀已表明方向与范围，无需 divider
const shrinkageItems: FormItem[] = [
  { label: '平行收缩率', prop: 'ave_h_shrink', type: 'number', unit: '%', precision: 4 },
  { label: '垂直收缩率', prop: 'ave_v_shrink', type: 'number', unit: '%', precision: 4 },
  { label: '最小平行收缩率', prop: 'min_h_shrink', type: 'number', unit: '%', precision: 4 },
  { label: '最大平行收缩率', prop: 'max_h_shrink', type: 'number', unit: '%', precision: 4 },
  { label: '最小垂直收缩率', prop: 'min_v_shrink', type: 'number', unit: '%', precision: 4 },
  { label: '最大垂直收缩率', prop: 'max_v_shrink', type: 'number', unit: '%', precision: 4 },
]

// ============================================================================
// formCards（始终展示 2 个，开关打开后追加 4 个仿真 section）
// ============================================================================

const basicCards: FormCard[] = [
  { title: '基本信息', items: basicItems },
  { title: '推荐工艺参数', items: processItems },
]

const simulationCards: FormCard[] = [
  { title: 'PVT 仿真参数', items: pvtItems },
  { title: '流变仿真参数', items: rheologyItems },
  { title: '机械仿真参数', items: mechanicalItems },
  { title: '收缩仿真参数', items: shrinkageItems },
]

const basicCardRows = computed(() =>
  basicCards.map((card) => ({
    title: card.title,
    rows: groupIntoRows(card.items, { columns: 4 }),
  }))
)

const simulationCardRows = computed(() =>
  simulationCards.map((card) => ({
    title: card.title,
    rows: groupIntoRows(card.items, { columns: 4 }),
  }))
)

// 流变 / 机械 / 收缩 section 绑定嵌套 model，其他绑定 polymer_info 顶层
function getCardModel(title: string): any {
  switch (title) {
    case '流变仿真参数':
      return polymer_info.value.rheology
    case '机械仿真参数':
      return polymer_info.value.mechanical
    case '收缩仿真参数':
      return polymer_info.value.shrinkage
    default:
      return polymer_info.value
  }
}

const rules: FormRules = {
  abbreviation: [
    { required: true, message: '材料名称缩写为空!', trigger: 'change' },
  ],
  grade: [
    { required: true, message: '材料牌号为空!', trigger: 'blur' },
  ],
}

function goBack() {
  router.push('/material/polymer/list')
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    ElMessage.warning('请检查必填项')
    return
  }

  submitting.value = true
  try {
    // 清理 null / 空字符串（保留 0 等有效值）
    const payload: any = {}
    for (const [key, val] of Object.entries(polymer_info.value)) {
      if (val !== null && val !== '') {
        payload[key] = val
      }
    }

    let res: any
    if (polymer_id.value !== null && !is_copy.value) {
      res = await polymerMethod.edit(payload, polymer_id.value)
    } else {
      res = await polymerMethod.add(payload)
    }

    if (res.status === 0) {
      ElMessage.success(is_edit ? '材料信息编辑成功！' : '材料信息新增成功！')
      goBack()
    } else {
      ElMessage.error(res.msg || '保存失败')
    }
  } catch (err: any) {
    console.error('[PolymerForm] save failed:', err)
    ElMessage.error(err?.message || '提交异常')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  if (polymer_id.value !== null) {
    await loadDetail(polymer_id.value)
  } else {
    loaded.value = true
  }
})

async function loadDetail(id: number) {
  loading.value = true
  try {
    const res: any = await polymerMethod.getDetail(id)
    if (res.status === 0) {
      polymer_info.value = res.data
      if (is_copy.value) {
        polymer_info.value.id = null
        polymer_info.value.grade = null
      }
      // 若该 polymer 已有填充物组成数据，自动展开开关并加载填充物库
      if (Array.isArray(polymer_info.value.polymer_filler_compositions) && polymer_info.value.polymer_filler_compositions.length > 0) {
        showFillerComposition.value = true
      }
      loaded.value = true
    } else {
      ElMessage.error(res.msg || '未读取到相关材料信息')
      router.push('/material/polymer/list')
    }
  } catch (err: any) {
    console.error('[PolymerForm] loadDetail failed:', err)
    ElMessage.error(err?.message || '加载材料详情异常')
    router.push('/material/polymer/list')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.polymer-form {
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

/* 仿真参数开关 card：左侧 info 区 + 右侧 switch */
.custom-form__section--toggle {
  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.simulation-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.simulation-toggle__info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.simulation-toggle__icon {
  font-size: 24px;
  color: #409eff;
  margin-top: 2px;
}

.simulation-toggle__title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.simulation-toggle__desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

/* 填充物开关 card（与仿真开关同款） */
.filler-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.filler-toggle__info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.filler-toggle__icon {
  font-size: 24px;
  color: #67c23a;
  margin-top: 2px;
}

.filler-toggle__title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.filler-toggle__desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

/* 填充物 section header（右侧总含量 + 新增按钮） */
.filler-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
}

.filler-section-header__actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filler-total {
  font-size: 13px;
  color: #606266;

  strong {
    color: #67c23a;
    font-weight: 600;
    font-size: 14px;
    margin-left: 2px;
  }

  &--over strong {
    color: #e6a23c;
  }
}

/* 填充物表格 */
.filler-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;

  thead th {
    text-align: left;
    padding: 10px 12px;
    background-color: #fafafa;
    color: #606266;
    font-weight: 500;
    border-bottom: 1px solid #ebeef5;
    white-space: nowrap;
  }

  tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid #ebeef5;
    vertical-align: middle;
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  .filler-col-name { width: 32%; }
  .filler-col-pct  { width: 14%; }
  .filler-col-note { width: auto; }
  .filler-col-action {
    width: 90px;
    text-align: center;
    white-space: nowrap;
  }
}

.filler-empty {
  text-align: center !important;
  padding: 32px 12px !important;
  color: #909399;
  font-size: 13px;
}

.text-danger {
  color: #f56c6c;
}
</style>