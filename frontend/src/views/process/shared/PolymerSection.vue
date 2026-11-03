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
          <el-form-item label="选择塑料" prop="polymer_abbreviation">
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
          <el-form-item label="塑料牌号" prop="polymer_info.id">
            <el-autocomplete
              v-model="selectedGrade"
              :fetch-suggestions="fetchGradeSuggestions"
              :debounce="300"
              placeholder="输入并选择牌号"
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
            <!-- 自定义错误文案：区分"完全没选"与"只敲了字没从下拉里选" -->
            <template #error>
              <div class="el-form-item__error" role="alert">{{ gradeErrorText }}</div>
            </template>
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
import { ref, watch, inject, computed } from 'vue'
import { polymerMethod } from '@/api'
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

// 反向同步：父组件 resetForm 或外部条件被清空时，输入框显示值也清零
// （局部 ref 只在 setup 初始化一次，不 watch condition 就会停留在旧值）
//
// ⚠️ internalPolymerClear：内部主动清空 polymer_info（如改简称导致牌号失效）时置位。
// condition.polymer_info 由有值变 null 会让本 watch 触发，若照常回填就把用户刚选的
// 新简称一起清掉了 ⇒ 这种清空要跳过回填（消费标志位后 return）。
let internalPolymerClear = false

watch(
  () => condition.polymer_info?.abbreviation,
  (val) => {
    if (internalPolymerClear) {
      internalPolymerClear = false
      return
    }
    polymerAbbreviation.value = val ?? ''
  },
)
watch(
  () => condition.polymer_info?.grade,
  (val) => { selectedGrade.value = val ?? '' },
)

// 简称/牌号变空 → 自动重置材料派生信息
// 覆盖两种清空路径:
//   1. 点 X 按钮(@clear 触发 el-autocomplete 把 v-model 设为 '')
//   2. 手动删空 input(@clear 不触发,只能靠 watch 兜底)
// 同时把输入框状态镜像到 condition.polymer_abbreviation：
// el-form-item 的校验目标必须落在 el-form 的 model 上，
// 局部 ref 无法直接作为校验目标 ⇒ 镜像后由 prop="polymer_abbreviation" 校验。
// immediate 保证初始值(编辑模式已有 polymer_info)也能镜像。
watch(
  polymerAbbreviation,
  (val) => {
    condition.polymer_abbreviation = val || null
    if (val === '') {
      selectedGrade.value = ''
      // 清空嵌套 polymer_info（包含 id），校验自动失败
      condition.polymer_info = null
    }
  },
  { immediate: true },
)
watch(selectedGrade, (val) => {
  if (val === '') {
    // 清空嵌套 polymer_info（包含 id），校验自动失败
    condition.polymer_info = null
  }
})

// autocomplete 允许自由输入：敲了字但没从下拉里选中时，condition.polymer_info 仍为空
// ⇒ 校验目标 polymer_info.id 缺失。此处标记该状态，用于区分错误文案
const gradeUnmatched = computed(() => !!selectedGrade.value && !condition.polymer_info?.id)

// 错误文案：只敲了字 ≠ 已选择，必须让用户看出差别
const gradeErrorText = computed(() =>
  gradeUnmatched.value ? '请从下拉列表中选择牌号' : '请选择塑料牌号',
)

// 简称 autocomplete:输入简称关键词,按 abbreviation 模糊检索
async function fetchAbbreviationSuggestions(queryString: string, cb: (results: any[]) => void) {
  try {
    const res: any = await polymerMethod.get({
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
    const res: any = await polymerMethod.get({
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
    // 清空嵌套 polymer_info（包含 id），校验自动失败
    // 置位跳过反向同步回填：否则 polymer_info 由有值变 null 会把刚选的新简称一起清掉
    internalPolymerClear = true
    condition.polymer_info = null
  }
}

// 牌号详情请求序号：只允许最后一次发起的请求写回，
// 避免“快速连选两个牌号”时旧响应后到、把 polymer_info 覆盖成上一个牌号
let gradeDetailSeq = 0

// 牌号选择 → 调详情 API + set condition
// 若当前简称空,自动同步为该 polymer 的 abbreviation
async function onGradeSelect(item: any) {
  const p = item?.item ?? null
  if (!p) return
  const seq = ++gradeDetailSeq
  // id 写入 condition.polymer_info.id（嵌套结构，校验 prop="polymer_info.id"）
  // 同步简称:如果当前简称空或不一致,同步为该 polymer 的 abbreviation
  if (p.abbreviation && polymerAbbreviation.value !== p.abbreviation) {
    polymerAbbreviation.value = p.abbreviation
  }
  // 同步前置写入列表项（已含 id）：
  // el-form-item 的 change 校验在 selectedGrade 变化的同一轮微任务里执行，
  // 若等详情接口返回后才写 polymer_info，校验读到的仍是 null ⇒ 必填红字永久残留
  condition.polymer_info = p
  // 列表 API 不含 Moldflow 参数
  // 必须调详情 API 获取完整数据
  try {
    const detail: any = await polymerMethod.getDetail(p.id)
    if (seq !== gradeDetailSeq) return
    if (detail?.status === 0 && detail.data) {
      condition.polymer_info = detail.data
    }
  } catch {
    // 详情失败:保留列表项(基本信息可显示,推荐工艺字段可能不全)
  }
}

// 简称清空:副作用由 watch(polymerAbbreviation) 接管
// 保留函数仅用于匹配模板的 @clear 绑定;点 X 时 el-autocomplete 已把 v-model 同步清空
function onPolymerClear() {
  // no-op
}

// 牌号清空:副作用由 watch(selectedGrade) 接管
// 保留函数仅用于匹配模板的 @clear 绑定;点 X 时 el-autocomplete 已把 v-model 同步清空
function onGradeClear() {
  // no-op
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
