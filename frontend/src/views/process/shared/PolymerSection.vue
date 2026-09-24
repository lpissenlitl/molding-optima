<!--
  PolymerSection - 材料区域子组件

  职责：
    1. 材料主选（简称 + 牌号，双 autocomplete）
    2. 材料派生字段（基本信息）
    3. 推荐工艺（成型温度 + 注塑速率/背压/剪切/滞留）

  通信：通过 inject(ConditionKey) 获取共享的 reactive condition，直接 mutate

  联动：牌号 fetch 自动按当前简称过滤；两个 autocomplete 可独立检索
-->
<template>
  <div class="area-section">
    <!-- 选择区：双 autocomplete（独立检索 + 联动过滤） -->
    <div class="selection-area">
      <el-row :gutter="24">
        <!-- 简称 autocomplete -->
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="选择塑料">
            <el-autocomplete
              v-model="polymerAbbreviation"
              :fetch-suggestions="fetchAbbreviationSuggestions"
              :debounce="300"
              placeholder="输入简称检索（如 PP）"
              clearable
              size="small"
              :disabled="disabled"
              @select="onAbbreviationSelect"
              @clear="onPolymerClear"
            >
              <template #prefix>
                <AppIcon icon="mdi:flask-outline" />
              </template>
            </el-autocomplete>
          </el-form-item>
        </el-col>

        <!-- 牌号 autocomplete（fetch 按当前简称过滤） -->
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="塑料牌号" prop="polymer_id">
            <el-autocomplete
              v-model="selectedGrade"
              :fetch-suggestions="fetchGradeSuggestions"
              :debounce="300"
              placeholder="输入牌号检索"
              clearable
              size="small"
              :disabled="disabled"
              @select="onGradeSelect"
              @clear="onGradeClear"
            >
              <template #prefix>
                <AppIcon icon="mdi:tag-outline" />
              </template>
            </el-autocomplete>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 派生信息区：自动带出的只读数据 -->
    <div class="derived-area">
      <!-- 基本信息 subsection -->
      <div class="subsection-block">
        <div class="subsection-block__header">
          <span class="subsection-block__title">
            <AppIcon icon="mdi:information-outline" />
            基本信息
          </span>
        </div>
        <el-row :gutter="24" class="subsection-block__content">
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="塑料简称" :value="condition.polymer_info?.abbreviation" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="塑料牌号" :value="condition.polymer_info?.grade" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="类别" :value="condition.polymer_info?.category" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="生产厂家" :value="condition.polymer_info?.manufacturer" />
          </el-col>
        </el-row>
      </div>

      <!-- 推荐工艺 subsection -->
      <div class="subsection-block">
        <div class="subsection-block__header">
          <span class="subsection-block__title">
            <AppIcon icon="mdi:tune-variant" />
            推荐工艺
          </span>
        </div>

        <!-- 第一行：成型温度 -->
        <el-row :gutter="24" class="subsection-block__content">
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="推荐熔体温度"
              :value="condition.polymer_info?.recommended_melt_temp"
              unit="℃"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="推荐模具温度"
              :value="condition.polymer_info?.recommended_mold_temp"
              unit="℃"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="顶出温度"
              :value="condition.polymer_info?.ejection_temp"
              unit="℃"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="降解温度"
              :value="condition.polymer_info?.degradation_temp"
              unit="℃"
            />
          </el-col>
        </el-row>

        <!-- 第二行：注塑速率/背压/剪切/滞留 -->
        <el-row :gutter="24" class="subsection-block__content" style="margin-top: 12px;">
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="推荐注塑速率"
              :value="condition.polymer_info?.recommend_injection_rate"
              unit="cm³/s"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="推荐背压"
              :value="condition.polymer_info?.recommend_back_pressure"
              unit="MPa"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="推荐剪切线速度"
              :value="condition.polymer_info?.recommended_shear_line_speed"
              unit="mm/s"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="料筒滞留时间"
              :value="condition.polymer_info?.barrel_residence_time"
              unit="min"
            />
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, inject } from 'vue'
import { polymerList, polymerDetail } from '@/api'
import DerivedField from './DerivedField.vue'
import { ConditionKey } from './types.js'
import type { Condition } from './types.js'

// Props
const props = withDefaults(
  defineProps<{
    /** 禁用所有输入（mode='view' 时父组件传 true） */
    disabled?: boolean
  }>(),
  {
    disabled: false,
  },
)

// 共享 condition
const condition = inject(ConditionKey)!

// 简称 + 牌号选择状态
const polymerAbbreviation = ref<string>(condition.polymer_info?.abbreviation ?? '')
const selectedGrade = ref<string>(condition.polymer_info?.grade ?? '')

// 简称 autocomplete:输入简称关键词,按 abbreviation 模糊检索
async function fetchAbbreviationSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await polymerList({
      page_no: 1,
      page_size: 30,
      abbreviation: queryString || undefined,
    })
    if (res?.status === 0) {
      // 用 abbreviation 去重
      const seen = new Map<string, any>()
      for (const it of res.data?.items ?? []) {
        if (it.abbreviation && !seen.has(it.abbreviation)) {
          seen.set(it.abbreviation, {
            value: it.abbreviation,
            item: it,
          })
        }
      }
      cb(Array.from(seen.values()))
    } else {
      cb([])
    }
  } catch {
    cb([])
  }
}

// 牌号 autocomplete:输入 grade 关键词
// 若已选简称则联动过滤(基于 polymerAbbreviation.value)
async function fetchGradeSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await polymerList({
      page_no: 1,
      page_size: 30,
      grade: queryString || undefined,
      abbreviation: polymerAbbreviation.value || undefined,  // 联动
    })
    if (res?.status === 0) {
      const items = (res.data?.items ?? []).map((it: any) => ({
        value: it.grade,
        item: it,
      }))
      cb(items)
    } else {
      cb([])
    }
  } catch {
    cb([])
  }
}

// 简称选择(不清空 polymer_info - 用户可能已选过牌号)
// 若已有的 polymer_info 与新简称不一致,需重选牌号
function onAbbreviationSelect(item: any) {
  const p = item?.item ?? null
  if (!p) return
  if (condition.polymer_info && condition.polymer_info.abbreviation !== p.abbreviation) {
    selectedGrade.value = ''
    condition.polymer_id = null
    condition.polymer_info = null
  }
}

// 牌号选择 → 调详情 API + set condition
// 若当前简称空,自动同步为该 polymer 的 abbreviation
async function onGradeSelect(item: any) {
  const p = item?.item ?? null
  if (!p) return
  condition.polymer_id = p.id
  // 同步简称:如果当前简称空或不一致,同步为该 polymer 的 abbreviation
  if (p.abbreviation && polymerAbbreviation.value !== p.abbreviation) {
    polymerAbbreviation.value = p.abbreviation
  }
  // 列表 API 不含 Moldflow 参数
  // 必须调详情 API 获取完整数据
  try {
    const detail: any = await polymerDetail(p.id)
    if (detail?.status === 0 && detail.data) {
      condition.polymer_info = detail.data
    } else {
      // 详情失败,退回到列表项(基本信息可显示,推荐工艺字段可能不全)
      condition.polymer_info = p
    }
  } catch {
    condition.polymer_info = p
  }
}

// 简称清空:全部重置
function onPolymerClear() {
  polymerAbbreviation.value = ''
  selectedGrade.value = ''
  condition.polymer_id = null
  condition.polymer_info = null
}

// 牌号清空:仅清空牌号相关,保留简称
function onGradeClear() {
  selectedGrade.value = ''
  condition.polymer_id = null
  condition.polymer_info = null
}
</script>

<style lang="scss" scoped>
// 全局 .subsection-block* 定义在 src/styles/utilities/subsection-block.scss
// 本组件私有：.selection-area（选择区容器）
// 派生区内部所有 subsection-block 统一使用全局 card 风格（同源区块样式一致）

.selection-area {
  margin-bottom: 0;
}
</style>
