<!-- MoldSection - 模具区域子组件 -->
<template>
  <div class="area-section">
    <div class="selection-area">
      <el-row :gutter="24">
        <el-col :xs="24" :sm="12" :md="6">
          <!-- prop 必须用 "mold_info.id"：顶层 mold_id 是提交态平铺字段（buildPayload 从 mold_info.id 推导），前端编辑期恒为空，用它做校验目标会永远失败 -->
          <el-form-item label="选择模具" prop="mold_info.id">
            <el-autocomplete
              v-model="moldQuery"
              :fetch-suggestions="fetchMoldSuggestions"
              :debounce="300"
              placeholder="输入并选择模具"
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
            <!-- 自定义错误文案：区分"完全没选"与"只敲了字没从下拉里选" -->
            <template #error>
              <div class="el-form-item__error" role="alert">{{ moldErrorText }}</div>
            </template>
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
import { moldMethod } from '@/api'
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
/** 型腔布局 tooltip */
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

// 反向同步：父组件 resetForm 或外部条件被清空时，输入框显示值也清零
// （局部 ref 只在 setup 初始化一次，不 watch condition 就会停留在旧值）
watch(
  () => condition.mold_info?.mold_no,
  (val) => { moldQuery.value = val ?? '' },
)

// autocomplete 允许自由输入：敲了字但没从下拉里选中时，condition.mold_info 仍为空
// ⇒ 校验目标 mold_info.id 缺失。此处标记该状态，用于区分错误文案
const moldUnmatched = computed(() => !!moldQuery.value && !condition.mold_info?.id)

// 错误文案：只敲了字 ≠ 已选择，必须让用户看出差别
const moldErrorText = computed(() =>
  moldUnmatched.value ? '请从下拉列表中选择模具' : '请选择模具',
)
watch(
  () => condition.shot_index,
  (val) => { shotIndexStr.value = val != null ? String(val + 1) : '' },
)

watch(shotIndexStr, (val) => {
  const num = Number(val)
  condition.shot_index =
    val === '' || isNaN(num) ? null : Math.max(0, num - 1)
})

// 模具远程拉取 + 选择回调（自包含，不依赖父组件）
async function fetchMoldSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await moldMethod.get({
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

// 模具详情请求序号：只允许最后一次发起的请求写回，
// 避免"快速连选两个模具"时旧响应后到、把 mold_info 覆盖成上一个模具
let moldDetailSeq = 0

async function onMoldSelect(item: any) {
  const mold = item?.item ?? null
  if (!mold) return
  const seq = ++moldDetailSeq
  // 切换模具后,射次统一重置为第 1 射(避免前一个模具的射次选择残留)
  // 放在 await 之前：shot_index 的必填校验与 moldQuery 变化在同一轮触发
  condition.shot_index = 0
  shotIndexStr.value = '1'
  // 同步前置写入列表项（已含 id）：
  condition.mold_info = mold
  // 列表 API(to_dict() 不带 include_rvs=True)不返回反向关联
  // 必须调详情 API 获取完整的 gating_systems / cavities / gates
  try {
    const detail: any = await moldMethod.getDetail(mold.id)
    if (seq !== moldDetailSeq) return
    if (detail?.status === 0 && detail.data) {
      condition.mold_info = detail.data
    }
  } catch {
    // 详情失败:保留列表项(基本信息可显示,浇注系统不会显示)
  }
}

function onMoldClear() {
  // 清空嵌套 mold_info（包含 id），校验自动失败
  condition.mold_info = null
  condition.shot_index = null
  shotIndexStr.value = ''
}
</script>

<style lang="scss" scoped>
// 全局 .subsection-block* 定义在 src/styles/utilities/subsection-block.scss

.selection-area {
  margin-bottom: 0;
}
</style>
