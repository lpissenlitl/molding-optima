<!--
  MachineSection - 注塑机区域子组件

  职责（从 ProcessCondition 拆分）：
    1. 注塑机主选（autocomplete 远程拉取）
    2. 注塑机派生字段（基本信息 subsection）
    3. 射台主选
    4. 射台信息 subsection（当前射台的字段）

  通信：
    - 通过 inject(ConditionKey) 获取共享的 reactive condition
    - 直接 mutate condition.xxx，无需 emit
    - useConditionDerived(condition) 自包含派生计算

  唯一性显示（关键）：
    - 注塑机 model 不唯一（同型号可能有多台设备）
    - 下拉显示 `${model} 「${device_no}」`，由 formatMachineLabel 统一格式化
    - watch props 同步、编辑模式初始化、下拉选择回填都用同一格式
-->
<template>
  <div class="area-section">
    <span class="custom-form__title">注塑机</span>

    <!-- 主选:注塑机（与基本信息 subsection 紧邻，语义上"选注塑机 → 查看基本信息"）
         label-width=auto，避免该行只有一个字段时 label-width=120px 带来的大量空白 -->
    <el-row :gutter="24">
      <el-col :xs="24" :sm="12" :md="12">
        <el-form-item label="注塑机" prop="injection_machine_id" label-width="auto">
          <el-autocomplete
            v-model="machineQuery"
            :fetch-suggestions="fetchMachineSuggestions"
            :debounce="300"
            placeholder="输入或选择注塑机"
            clearable
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
    </el-row>

    <!-- ============ 基本信息 subsection（注塑机主选后的派生字段）============
         名称用"基本信息"而不是"注塑机信息"：与模具部分统一,
         同一命名也适用于模具/注塑机/材料（都可用"基本信息"包装主选后的派生字段）
         默认显示：未选机器时所有字段为 "—" 占位（DerivedField 内部处理） -->
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
        <!-- 关键工艺属性：射台数量 -->
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

    <!-- 主选:射台（与射台信息 subsection 紧邻，语义上"选第几射台 → 查看该射台信息"）
         label-width=auto，避免该行只有一个字段时 label-width=120px 带来的大量空白 -->
    <el-row :gutter="24" style="margin-top: 16px;">
      <el-col :xs="24" :sm="12" :md="12">
        <el-form-item label="射台" prop="injection_index" label-width="auto">
          <el-select
            v-if="hasMultipleUnits"
            v-model="injectionIndexStr"
            :disabled="disabled"
            placeholder="选择第几射台"
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
            :disabled="true"
          >
            <template #suffix>射台</template>
          </el-input>
        </el-form-item>
      </el-col>
    </el-row>

    <!-- ============ 射台信息 subsection（当前射台的射台字段）============
         默认显示：未选机器时所有字段为 "—" 占位（DerivedField 内部处理） -->
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
</template>

<script setup lang="ts">
/**
 * MachineSection - 注塑机区域
 *
 * 设计动机：
 * - 注塑机逻辑相对独立（主选 + 基本信息 + 射台主选 + 射台信息）
 * - 唯一性显示（model + device_no）的格式化函数独立维护
 * - 后续可加 "能耗"、"控制方式" 等其他工艺属性
 */
import { ref, watch, inject } from 'vue'
import { injectionMachineList } from '@/api'
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
// 共享 condition
// ============================================================================

const condition = inject(ConditionKey)!

// ============================================================================
// 派生计算
// ============================================================================

const {
  unitCount,
  hasMultipleUnits,
  injectionUnitDerived,
  injectionIndexDisplay,
} = useConditionDerived(condition)

// ============================================================================
// 注塑机显示文本格式化（唯一性：model 不唯一，需要 model + device_no）
// ============================================================================

/**
 * 注塑机显示文本：注塑机型号 「设备编号」
 * 与 fetchMachineSuggestions 中 items 的 value 字段保持一致
 * 这样 watch 同步、编辑模式初始化、下拉选择回填都用同一格式
 */
function formatMachineLabel(m: { model?: string; device_no?: string } | null | undefined): string {
  if (!m) return ''
  return m.device_no ? `${m.model} 「${m.device_no}」` : (m.model ?? '')
}

// ============================================================================
// 注塑机下拉状态
// ============================================================================

const machineQuery = ref<string>(formatMachineLabel(condition.machine_info))

// ============================================================================
// 射台字符串中间值（UI 1 索引 ↔ 后端 0 索引）
// ============================================================================

const injectionIndexStr = ref<string>(
  condition.injection_index != null ? String(condition.injection_index + 1) : '',
)

watch(injectionIndexStr, (val) => {
  const num = Number(val)
  condition.injection_index =
    val === '' || isNaN(num) ? null : Math.max(0, num - 1)
})

// ============================================================================
// 注塑机远程拉取 + 选择回调（自包含）
// ============================================================================

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

function onMachineSelect(item: any) {
  const m = item?.item ?? null
  if (!m) return
  condition.injection_machine_id = m.id
  condition.machine_info = m
}

function onMachineClear() {
  condition.injection_machine_id = null
  condition.machine_info = null
}
</script>
