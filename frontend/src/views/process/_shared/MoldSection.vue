<!--
  MoldSection - 模具区域子组件

  职责（从 ProcessCondition 拆分）：
    1. 模具主选（autocomplete 远程拉取 mold 列表）
    2. 模具派生字段（基本信息 subsection）
    3. 工艺射次主选
    4. 浇注系统 subsection（含制品循环 + 浇口循环，4 级嵌套）

  通信：
    - 通过 inject(ConditionKey) 获取共享的 reactive condition
    - 直接 mutate condition.xxx，无需 emit
    - useConditionDerived(condition) 自包含派生计算

  索引约定（与 useConditionDerived 一致）：
    - 后端 shot_index 是 0 索引（0 表示第 1 射）
    - UI 显示用 1 索引，由 shotIndexStr 字符串中间值做转换
-->
<template>
  <div class="area-section">
    <span class="custom-form__title">模具</span>

    <!-- 主选：模具编号 -->
    <el-row :gutter="24">
      <el-col :xs="24" :sm="12" :md="12">
        <el-form-item label="模具编号" prop="mold_id" label-width="auto">
          <el-autocomplete
            v-model="moldQuery"
            :fetch-suggestions="fetchMoldSuggestions"
            :debounce="300"
            placeholder="输入或选择模具"
            clearable
            :disabled="disabled"
            @select="onMoldSelect"
            @clear="onMoldClear"
          >
            <template #prefix>
              <AppIcon icon="mdi:cube-outline" />
            </template>
          </el-autocomplete>
        </el-form-item>
      </el-col>
    </el-row>

    <!-- ============ 基本信息 subsection(模具主选后跟随的模具派生字段)
         名称用"基本信息"而不是"模具信息"：
         · 同一命名也适用于注塑机/材料(都可用"基本信息"包装主选后的派生字段)
         · 不限于模具,语义上中立、便于复用 -->
    <div class="subsection-block">
      <div class="subsection-block__header">
        <span class="subsection-block__title">
          <AppIcon icon="mdi:information-outline" />
          基本信息
        </span>
      </div>
      <el-row :gutter="24" class="subsection-block__content">
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="模具名称" :value="condition.mold_info?.mold_name" />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="产品大类" :value="condition.mold_info?.product_category" />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="注射次数" :value="shotCount" unit="射" />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField
            label="型腔布局"
            :value="condition.mold_info?.cavity_layout"
            :tooltip="CAVITY_LAYOUT_TOOLTIP"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 主选:工艺射次(与浇注系统 subsection 紧邻,语义上"选第几射 → 查看该射浇注系统")
         label-width=auto,避免该行只有一个字段时 label-width=120px 带来的大量空白 -->
    <el-row :gutter="24" style="margin-top: 16px;">
      <el-col :xs="24" :sm="12" :md="12">
        <el-form-item label="工艺射次" prop="shot_index" label-width="auto">
          <el-select
            v-if="hasMultipleShots"
            v-model="shotIndexStr"
            :disabled="disabled"
            placeholder="选择第几射"
            style="width: 100%;"
          >
            <el-option
              v-for="i in shotCount"
              :key="i"
              :label="`第 ${i} 射`"
              :value="String(i)"
            />
          </el-select>
          <el-input
            v-else
            v-model="shotIndexStr"
            v-number="0"
            placeholder="1（单射默认）"
            :disabled="true"
          >
            <template #suffix>射</template>
          </el-input>
        </el-form-item>
      </el-col>
    </el-row>

    <!-- ============ 浇注系统 subsection(当前射的浇注系统 + 浇注级派生 + 制品平铺 + 浇口平铺) ============ -->
    <!-- 依存：选中模具 + 当前射存在 gating_system 才显示(随射次切换) -->
    <div v-if="gatingDerived" class="subsection-block">
      <div class="subsection-block__header">
        <span class="subsection-block__title">
          <AppIcon icon="mdi:pipe" />
          浇注系统
          <template v-if="hasMultipleShots">
            <span class="subsection-block__shot">（第 {{ shotIndexDisplay }} 射）</span>
          </template>
        </span>
      </div>

      <!-- 浇注系统级字段（不属于任何 cavity,是整个 gating_system 共享的） -->
      <el-row :gutter="24" class="subsection-block__content">
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField label="流道类别" :value="gatingDerived?.runner_type" />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <DerivedField
            label="制品总重量"
            :value="gatingDerived?.total_product_weight"
            unit="g"
          />
        </el-col>
        <template v-if="gatingDerived?.runner_type === '冷流道' || gatingDerived?.runner_type === '热转冷'">
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="流道重量"
              :value="gatingDerived?.runner_weight"
              unit="g"
            />
          </el-col>
        </template>
        <template v-if="gatingDerived?.runner_type === '热流道' || gatingDerived?.runner_type === '热转冷'">
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="热喷嘴数量"
              :value="gatingDerived?.hot_runner_nozzle_count"
              unit="个"
            />
          </el-col>
          <el-col v-if="gatingDerived?.hot_runner_supplier" :xs="24" :sm="12" :md="6">
            <DerivedField
              label="热流道供应商"
              :value="gatingDerived.hot_runner_supplier"
            />
          </el-col>
        </template>
      </el-row>

      <!-- 派生信息：浇注系统下的所有制品(cavity)平铺展示。
          一次注射成型对应浇注下所有腔体同时成型，
          所以不提供"切第几件"的主选、每个 cavity 都作为一个完整子区块展开 -->
      <div
        v-for="(cavity, cIdx) in cavities"
        v-show="cavities.length"
        :key="`cavity_${cIdx}`"
        class="subsection-block subsection-block--nested"
      >
        <div class="subsection-block__header">
          <span class="subsection-block__title">
            <AppIcon icon="mdi:package-variant-closed" />
            制品 #{{ cIdx + 1 }}
            <template v-if="cavity.product_name">
              <span class="subsection-block__shot">（{{ cavity.product_name }}）</span>
            </template>
          </span>
        </div>
        <el-row :gutter="24" class="subsection-block__content">
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="制品编号" :value="cavity.product_code" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="制品名称" :value="cavity.product_name" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="单腔重量"
              :value="cavity.estimated_weight_per_cavity"
              unit="g"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="型腔数" :value="cavity.cavity_count_per_shot" unit="个" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="平均壁厚"
              :value="cavity.ave_wall_thickness"
              unit="mm"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="最大壁厚"
              :value="cavity.max_wall_thickness"
              unit="mm"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="最大流长"
              :value="cavity.max_flow_length"
              unit="mm"
            />
          </el-col>
        </el-row>

        <!-- 浇口列表（每个 cavity 下 1:N 个浇口,平铺展示） -->
        <div
          v-for="(gate, gIdx) in cavity.gates"
          v-show="cavity.gates && cavity.gates.length"
          :key="`gate_${cIdx}_${gIdx}`"
          class="subsection-block subsection-block--deep-nested"
        >
          <div class="subsection-block__header">
            <span class="subsection-block__title">
              <AppIcon icon="mdi:flash-triangle-outline" />
              浇口 #{{ gIdx + 1 }}
              <template v-if="gate.gate_shape">
                <span class="subsection-block__shot">（{{ gate.gate_shape }}）</span>
              </template>
            </span>
          </div>
          <el-row :gutter="24" class="subsection-block__content">
            <el-col :xs="24" :sm="12" :md="6">
              <DerivedField label="浇口类别" :value="gate.gate_type" />
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <DerivedField label="浇口数量" :value="gate.gate_count" unit="个" />
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <DerivedField label="浇口形状" :value="gate.gate_shape" />
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
              <DerivedField label="浇口位置" :value="gate.location_description" />
            </el-col>
            <!-- 条件渲染：圆 / 矩 -->
            <template v-if="gate.gate_shape === '圆形'">
              <el-col :xs="24" :sm="12" :md="6">
                <DerivedField label="浇口直径" :value="gate.diameter" unit="mm" />
              </el-col>
            </template>
            <template v-else-if="gate.gate_shape === '矩形'">
              <el-col :xs="24" :sm="12" :md="6">
                <DerivedField label="浇口长" :value="gate.length" unit="mm" />
              </el-col>
              <el-col :xs="24" :sm="12" :md="6">
                <DerivedField label="浇口宽" :value="gate.width" unit="mm" />
              </el-col>
            </template>
          </el-row>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * MoldSection - 模具区域
 *
 * 设计动机：
 * - 模具是工艺条件中最复杂的部分（含浇注系统 → 制品 → 浇口 4 级嵌套）
 * - 单独成文件便于后续添加模具温度/冷却水路等其他子区块
 * - 模具的"列表 + 详情"两步拉取流程只在模具区域内部需要
 */
import { ref, watch, inject, computed } from 'vue'
import { moldList, moldDetail } from '@/api'
import DerivedField from './DerivedField.vue'
import { useConditionDerived } from './composables/useConditionDerived'
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
// 共享 condition（由父组件 ProcessCondition.vue 通过 provide 提供）
// ============================================================================

const condition = inject(ConditionKey)!

// ============================================================================
// 模具相关 tooltip（领域知识，仅模具使用）
// ============================================================================

/**
 * 型腔布局 tooltip
 * 1: 单色模具, 单腔, 共1个制品
 * 1+1: 单色模具, 两腔, 共2个制品, 制品参数不同
 * 1*2: 单色模具, 两腔, 共2个制品, 制品参数相同
 * 1&1: 双色模具, 1射单腔, 成型1个制品, 2射单腔, 成型1个制品
 * 1&1+1: 双色模具, 1射单腔, 成型1个制品, 2射双腔, 成型2个制品, 制品参数不同
 */
const CAVITY_LAYOUT_TOOLTIP = [
  '1: 单色模具, 单腔, 共1个制品',
  '1+1: 单色模具, 两腔, 共2个制品, 制品参数不同',
  '1*2: 单色模具, 两腔, 共2个制品, 制品参数相同',
  '1&1: 双色模具, 1射单腔, 成型1个制品, 2射单腔, 成型1个制品',
  '1&1+1: 双色模具, 1射单腔, 成型1个制品, 2射双腔, 成型2个制品, 制品参数不同',
].join('\n')

// ============================================================================
// 派生计算（从 composable 复用）
// ============================================================================

const {
  shotCount,
  hasMultipleShots,
  gatingDerived,
  cavities,
  shotIndexDisplay,
} = useConditionDerived(condition)

// ============================================================================
// 模具下拉状态
// ============================================================================

const moldQuery = ref<string>(condition.mold_info?.mold_no ?? '')

// ============================================================================
// 工艺射次字符串中间值（UI 1 索引 ↔ 后端 0 索引）
// ============================================================================

const shotIndexStr = ref<string>(
  condition.shot_index != null ? String(condition.shot_index + 1) : '',
)

watch(shotIndexStr, (val) => {
  const num = Number(val)
  condition.shot_index =
    val === '' || isNaN(num) ? null : Math.max(0, num - 1)
})

// ============================================================================
// 模具远程拉取 + 选择回调（自包含，不依赖父组件）
// ============================================================================

async function fetchMoldSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await moldList({
      page_no: 1,
      page_size: 30,
      mold_no: queryString || undefined,
    })
    if (res?.status === 0) {
      const items = (res.data?.items ?? []).map((it: any) => ({
        value: it.mold_no,
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

async function onMoldSelect(item: any) {
  const mold = item?.item ?? null
  if (!mold) return
  condition.mold_id = mold.id
  // 列表 API(to_dict() 不带 include_rvs=True)不返回反向关联
  // 必须调详情 API 获取完整的 gating_systems / cavities / gates
  try {
    const detail: any = await moldDetail(mold.id)
    if (detail?.status === 0 && detail.data) {
      condition.mold_info = detail.data
    } else {
      // 详情失败,退回到列表项(基本信息可显示,浇注系统不会显示)
      condition.mold_info = mold
    }
  } catch {
    condition.mold_info = mold
  }
}

function onMoldClear() {
  condition.mold_id = null
  condition.mold_info = null
}
</script>
