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
          <!-- prop 必须用 "machine_info.id"：顶层 injection_machine_id 是提交态平铺字段
               （buildPayload 从 machine_info.id 推导），前端编辑期恒为空，用它做校验目标会永远失败 -->
          <el-form-item label="选择注塑机" prop="machine_info.id">
            <el-autocomplete
              v-model="machineQuery"
              :fetch-suggestions="fetchMachineSuggestions"
              :debounce="300"
              placeholder="输入并选择注塑机"
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
            <!-- 自定义错误文案：区分"完全没选"与"只敲了字没从下拉里选" -->
            <template #error>
              <div class="el-form-item__error" role="alert">{{ machineErrorText }}</div>
            </template>
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
import { ref, watch, inject, computed } from 'vue'
import { machineMethod } from '@/api'
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

// 反向同步：父组件 resetForm 或外部条件被清空时，输入框显示值也清零
// （局部 ref 只在 setup 初始化一次，不 watch condition 就会停留在旧值）
watch(
  () => condition.machine_info,
  (val) => { machineQuery.value = formatMachineLabel(val) },
)

// autocomplete 允许自由输入：敲了字但没从下拉里选中时，condition.machine_info 仍为空
// ⇒ 校验目标 machine_info.id 缺失。此处标记该状态，用于区分错误文案
const machineUnmatched = computed(() => !!machineQuery.value && !condition.machine_info?.id)

// 错误文案：只敲了字 ≠ 已选择，必须让用户看出差别
const machineErrorText = computed(() =>
  machineUnmatched.value ? '请从下拉列表中选择注塑机' : '请选择注塑机',
)
watch(
  () => condition.injection_index,
  (val) => { injectionIndexStr.value = val != null ? String(val + 1) : '' },
)

watch(injectionIndexStr, (val) => {
  const num = Number(val)
  condition.injection_index =
    val === '' || isNaN(num) ? null : Math.max(0, num - 1)
})

// 注塑机远程拉取 + 选择回调（自包含）
async function fetchMachineSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await machineMethod.get({
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

// 注塑机详情请求序号：只允许最后一次发起的请求写回，
// 避免"快速连选两台机器"时旧响应后到、把 machine_info 覆盖成上一台
let machineDetailSeq = 0

async function onMachineSelect(item: any) {
  const m = item?.item ?? null
  if (!m) return
  const seq = ++machineDetailSeq
  // 切换注塑机后,射台序号统一重置为第 1 射台(避免前一台机器的射台选择残留)
  // 前置到 await 之前：injection_index 的必填校验与 machineQuery 变化在同一轮触发，
  // 放到详情返回之后会让"请选择射台"在用户已选机器后仍然报错
  condition.injection_index = 0
  injectionIndexStr.value = '1'
  // 同步前置写入列表项（已含 id）：
  // el-form-item 的 change 校验在 machineQuery 变化的同一轮微任务里执行，
  // 若等详情接口返回后才写 machine_info，校验读到的仍是 null ⇒ 必填红字永久残留
  condition.machine_info = m
  // 列表 API 不返回反向关联
  // 必须调详情 API 获取完整的 injection_units
  try {
    const detail: any = await machineMethod.getDetail(m.id)
    if (seq !== machineDetailSeq) return
    if (detail?.status === 0 && detail.data) {
      condition.machine_info = detail.data
    }
  } catch {
    // 详情失败:保留列表项(基本信息可显示,射台信息不会显示)
  }
}

function onMachineClear() {
  // 清空嵌套 machine_info（包含 id），校验自动失败
  condition.machine_info = null
  condition.injection_index = null
  injectionIndexStr.value = ''
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
