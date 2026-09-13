<!--
  PolymerSection - 材料区域子组件

  职责（从 ProcessCondition 拆分）：
    1. 材料主选（autocomplete 远程拉取）
    2. 材料派生字段（基本信息 subsection）
    3. 工艺参数 subsection（成型温度 + 注塑速率/背压/剪切/滞留）

  通信：
    - 通过 inject(ConditionKey) 获取共享的 reactive condition
    - 直接 mutate condition.xxx，无需 emit

  唯一性显示（关键）：
    - 材料 abbreviation 不唯一（同缩写可能有多个 grade 牌号）
    - 下拉显示 `${abbreviation} 「${grade}」`，由 formatPolymerLabel 统一格式化
-->
<template>
  <div class="area-section">
    <span class="custom-form__title">材料</span>

    <!-- 主选：塑料（与基本信息 subsection 紧邻，语义上"选材料 → 查看基本信息"）
         label-width=auto，避免该行只有一个字段时 label-width=120px 带来的大量空白 -->
    <el-row :gutter="24">
      <el-col :xs="24" :sm="12" :md="12">
        <el-form-item label="塑料" prop="polymer_id" label-width="auto">
          <el-autocomplete
            v-model="polymerQuery"
            :fetch-suggestions="fetchPolymerSuggestions"
            :debounce="300"
            placeholder="输入或选择塑料"
            clearable
            :disabled="disabled"
            @select="onPolymerSelect"
            @clear="onPolymerClear"
          >
            <template #prefix>
              <AppIcon icon="mdi:flask-outline" />
            </template>
          </el-autocomplete>
        </el-form-item>
      </el-col>
    </el-row>

    <!-- ============ 基本信息 subsection（材料主选后的派生字段）============ -->
    <div class="subsection-block">
      <div class="subsection-block__header">
        <span class="subsection-block__title">
          <AppIcon icon="mdi:information-outline" />
          基本信息
        </span>
      </div>
      <el-row :gutter="24" class="subsection-block__content">
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="塑料牌号" :value="condition.polymer_info?.grade" />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="类别" :value="condition.polymer_info?.category" />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="生产厂家" :value="condition.polymer_info?.manufacturer" />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="系列" :value="condition.polymer_info?.series" />
        </el-col>
      </el-row>
    </div>

    <!-- ============ 工艺参数 subsection（成型温度 + 注塑速率/背压/剪切/滞留）============ -->
    <div class="subsection-block">
      <div class="subsection-block__header">
        <span class="subsection-block__title">
          <AppIcon icon="mdi:tune-variant" />
          工艺参数
        </span>
      </div>

      <!-- 第一行：成型温度（推荐温度区间 + 极限温度） -->
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
</template>

<script setup lang="ts">
/**
 * PolymerSection - 材料区域
 *
 * 设计动机：
 * - 材料逻辑最简单（主选 + 基本信息 + 工艺参数）
 * - 唯一性显示（abbreviation + grade）的格式化函数独立维护
 * - 后续可加 "干燥工艺"、"流变属性"、"PVT 属性" 等子区块
 */
import { ref, inject } from 'vue'
import { polymerList } from '@/api'
import DerivedField from './DerivedField.vue'
import { ConditionKey } from './types'
import type { Condition } from './types'

// ============================================================================
// Props
// ============================================================================

const props = withDefaults(
  defineProps<{
    /** 禁用所有输入（mode='view' 时父组件传 true） */
    disabled?: boolean
  }>(),
  {
    disabled: false,
  },
)

// ============================================================================
// 共享 condition
// ============================================================================

const condition = inject(ConditionKey)!

// ============================================================================
// 材料显示文本格式化（唯一性：abbreviation 不唯一，需要 abbreviation + grade）
// ============================================================================

/**
 * 材料显示文本：材料缩写 「牌号」
 * 与 fetchPolymerSuggestions 中 items 的 value 字段保持一致
 * 牌号 grade 是唯一键（同缩写如 PP 可能有多个牌号）
 */
function formatPolymerLabel(p: { abbreviation?: string; grade?: string } | null | undefined): string {
  if (!p) return ''
  return p.grade ? `${p.abbreviation} 「${p.grade}」` : (p.abbreviation ?? '')
}

// ============================================================================
// 材料下拉状态
// ============================================================================

const polymerQuery = ref<string>(formatPolymerLabel(condition.polymer_info))

// ============================================================================
// 材料远程拉取 + 选择回调（自包含）
// ============================================================================

async function fetchPolymerSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await polymerList({
      page_no: 1,
      page_size: 30,
      abbreviation: queryString || undefined,
    })
    if (res?.status === 0) {
      const items = (res.data?.items ?? []).map((it: any) => ({
        // 组合文本格式：材料缩写 「牌号」
        // 同缩写多种牌号（如多个 PP）可区分；选中后输入框和提交值都用此格式
        value: it.grade ? `${it.abbreviation} 「${it.grade}」` : it.abbreviation,
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

function onPolymerSelect(item: any) {
  const p = item?.item ?? null
  if (!p) return
  condition.polymer_id = p.id
  condition.polymer_info = p
}

function onPolymerClear() {
  condition.polymer_id = null
  condition.polymer_info = null
}
</script>
