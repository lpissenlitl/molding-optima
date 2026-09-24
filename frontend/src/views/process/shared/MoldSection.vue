<!--
  MoldSection - 模具区域子组件

  职责：
    1. 模具主选（autocomplete）
    2. 模具派生字段（基本信息）
    3. 工艺射次主选
    4. 浇注系统（含制品循环 + 浇口循环）

  通信：通过 inject(ConditionKey) 获取共享的 reactive condition，直接 mutate

  索引：后端 shot_index 是 0 索引，UI 显示用 1 索引（shotIndexStr 转换）
-->
<template>
  <div class="area-section">
    <div class="selection-area">
      <el-row :gutter="24">
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="选择模具" prop="mold_id">
            <el-autocomplete
              v-model="moldQuery"
              :fetch-suggestions="fetchMoldSuggestions"
              :debounce="300"
              placeholder="输入或选择模具"
              clearable
              size="small"
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

        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="注射次序" prop="shot_index">
            <el-select
              v-if="hasMultipleShots"
              v-model="shotIndexStr"
              :disabled="disabled"
              placeholder="选择第几射"
              size="small"
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
              size="small"
              :disabled="true"
            >
              <template #suffix>射</template>
            </el-input>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 派生信息区：自动带出的只读数据 -->
    <div class="derived-area">
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

      <div class="subsection-block">
        <div class="subsection-block__header">
          <span class="subsection-block__title">
            <AppIcon icon="mdi:pipe" />
            浇注系统
            <template v-if="hasMultipleShots">
              <span class="subsection-block__shot">（第 {{ shotIndexDisplay }} 射）</span>
            </template>
          </span>
        </div>

      <!-- 浇注系统级字段（gating_system 共享的，不属于任何 cavity） -->
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

      <!-- cavity 平铺：一次注射成型对应浇注下所有腔体同时成型，不提供"切第几件"的主选 -->
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

        <!-- 浇口列表（每个 cavity 下 1:N 个浇口） -->
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
  </div>
</template>

<script setup lang="ts">
import { ref, watch, inject, computed } from 'vue'
import { moldList, moldDetail } from '@/api'
import DerivedField from './DerivedField.vue'
import { useConditionDerived } from './composables/useConditionDerived.js'
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

// 共享 condition（由父组件 ProcessCondition.vue 通过 provide 提供）
const condition = inject(ConditionKey)!

// 型腔布局 tooltip（领域知识，仅模具使用）
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

// 派生计算（从 composable 复用）
const {
  shotCount,
  hasMultipleShots,
  gatingDerived,
  cavities,
  shotIndexDisplay,
} = useConditionDerived(condition)

// 模具下拉状态
const moldQuery = ref<string>(condition.mold_info?.mold_no ?? '')

// 工艺射次字符串中间值（UI 1 索引 ↔ 后端 0 索引）
const shotIndexStr = ref<string>(
  condition.shot_index != null ? String(condition.shot_index + 1) : '',
)

watch(shotIndexStr, (val) => {
  const num = Number(val)
  condition.shot_index =
    val === '' || isNaN(num) ? null : Math.max(0, num - 1)
})

// 模具远程拉取 + 选择回调（自包含，不依赖父组件）
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
  // 选择模具后,默认选第 1 射(若用户尚未选过)
  if (condition.shot_index == null) {
    condition.shot_index = 0
    shotIndexStr.value = '1'
  }
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

<style lang="scss" scoped>
// 全局 .subsection-block* 定义在 src/styles/utilities/subsection-block.scss
// 本组件私有：.selection-area（选择区容器）
// 派生区内部所有 subsection-block 统一使用全局 card 风格（同源区块样式一致）

.selection-area {
  margin-bottom: 0;
}
</style>
