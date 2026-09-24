<!--
  MachineSection - 注塑机区域子组件

  职责：
    1. 注塑机主选（autocomplete）
    2. 注塑机派生字段（基本信息）
    3. 射台主选
    4. 射台信息（当前射台的字段）

  通信：通过 inject(ConditionKey) 获取共享的 reactive condition，直接 mutate

  唯一性：注塑机 model 不唯一，显示 `${model} 「${device_no}」`
-->
<template>
  <div class="area-section">
    <div class="selection-area">
      <el-row :gutter="24">
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="选择注塑机" prop="injection_machine_id">
            <el-autocomplete
              v-model="machineQuery"
              :fetch-suggestions="fetchMachineSuggestions"
              :debounce="300"
              placeholder="输入或选择注塑机"
              clearable
              size="small"
              :disabled="disabled"
              @select="onMachineSelect"
              @clear="onMachineClear"
            >
              <template #prefix>
                <AppIcon icon="mdi:server-outline" />
              </template>
            </el-autocomplete>
          </el-form-item>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="射台序号" prop="injection_index">
            <el-select
              v-if="hasMultipleUnits"
              v-model="injectionIndexStr"
              :disabled="disabled"
              placeholder="选择第几射台"
              size="small"
              style="width: 100%;"
            >
              <el-option
                v-for="i in unitCount"
                :key="i"
                :label="`第 ${i} 射台`"
                :value="String(i)"
              />
            </el-select>
            <el-input
              v-else
              v-model="injectionIndexStr"
              v-number="0"
              placeholder="1（单射台默认）"
              size="small"
              :disabled="true"
            >
              <template #suffix>射台</template>
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
            <DerivedField label="品牌" :value="condition.machine_info?.brand" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="设备编号" :value="condition.machine_info?.device_no" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="射台数量" :value="unitCount" unit="个" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="锁模力"
              :value="condition.machine_info?.max_clamping_force"
              unit="kN"
            />
          </el-col>
        </el-row>
      </div>

      <div class="subsection-block">
        <div class="subsection-block__header">
          <span class="subsection-block__title">
            <AppIcon icon="mdi:water-pump" />
            射台信息
            <template v-if="hasMultipleUnits">
              <span class="subsection-block__shot">（第 {{ injectionIndexDisplay }} 射台）</span>
            </template>
          </span>
        </div>
        <el-row :gutter="24" class="subsection-block__content">
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField label="射台编码" :value="injectionUnitDerived?.unit_code" />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="最大注射行程"
              :value="injectionUnitDerived?.max_injection_stroke"
              unit="mm"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="最大注射重量"
              :value="injectionUnitDerived?.max_injection_weight"
              unit="g"
            />
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <DerivedField
              label="螺杆直径"
              :value="injectionUnitDerived?.screw_diameter"
              unit="mm"
            />
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, inject } from 'vue'
import { injectionMachineList, injectionMachineDetail } from '@/api'
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

// 共享 condition
const condition = inject(ConditionKey)!

// 派生计算
const {
  unitCount,
  hasMultipleUnits,
  injectionUnitDerived,
  injectionIndexDisplay,
} = useConditionDerived(condition)

// 注塑机显示文本格式化（唯一性：model 不唯一，需要 model + device_no）
/**
 * 注塑机显示文本：注塑机型号 「设备编号」
 * 与 fetchMachineSuggestions 中 items 的 value 字段保持一致
 * 这样 watch 同步、编辑模式初始化、下拉选择回填都用同一格式
 */
function formatMachineLabel(m: { model?: string; device_no?: string } | null | undefined): string {
  if (!m) return ''
  return m.device_no ? `${m.model} 「${m.device_no}」` : (m.model ?? '')
}

// 注塑机下拉状态
const machineQuery = ref<string>(formatMachineLabel(condition.machine_info))

// 射台字符串中间值（UI 1 索引 ↔ 后端 0 索引）
const injectionIndexStr = ref<string>(
  condition.injection_index != null ? String(condition.injection_index + 1) : '',
)

watch(injectionIndexStr, (val) => {
  const num = Number(val)
  condition.injection_index =
    val === '' || isNaN(num) ? null : Math.max(0, num - 1)
})

// 注塑机远程拉取 + 选择回调（自包含）
async function fetchMachineSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await injectionMachineList({
      page_no: 1,
      page_size: 30,
      model: queryString || undefined,
    })
    if (res?.status === 0) {
      const items = (res.data?.items ?? []).map((it: any) => ({
        // 组合文本格式：注塑机型号 「设备编号」
        // 同型号多台机器可区分；选中后输入框和提交值都用此格式
        value: it.device_no ? `${it.model} 「${it.device_no}」` : it.model,
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

async function onMachineSelect(item: any) {
  const m = item?.item ?? null
  if (!m) return
  condition.injection_machine_id = m.id
  // 列表 API 不返回反向关联
  // 必须调详情 API 获取完整的 injection_units
  try {
    const detail: any = await injectionMachineDetail(m.id)
    if (detail?.status === 0 && detail.data) {
      condition.machine_info = detail.data
    } else {
      // 详情失败,退回到列表项(基本信息可显示,射台信息不会显示)
      condition.machine_info = m
    }
  } catch {
    condition.machine_info = m
  }
  // 选择注塑机后,默认选第 1 射台(若用户尚未选过)
  if (condition.injection_index == null) {
    condition.injection_index = 0
    injectionIndexStr.value = '1'
  }
}

function onMachineClear() {
  condition.injection_machine_id = null
  condition.machine_info = null
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
