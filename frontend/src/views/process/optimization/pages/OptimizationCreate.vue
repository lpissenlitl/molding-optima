<!-- OptimizationCreate - 智能调机（工作台） -->
<template>
  <div class="optimization-create">
    <div v-if="!loaded" v-loading="true" class="loading-placeholder" />

    <template v-else>
      <ProcessCondition
        ref="conditionRef"
        :process-condition="form.condition"
        v-model:expanded="conditionExpanded"
        mode="edit"
        :default-expanded="!hasConditionData"
        :disabled="hasInitialProcess"
      />

      <el-card class="box-card optimization-card" style="margin-top: 16px">
        <template #header>
          <div class="optimization-card__header">
            <div class="optimization-card__header-left">
              <AppIcon icon="mdi:tune-vertical" class="optimization-card__header-icon" />
              <span class="custom-form__title">智能调机</span>
            </div>
          </div>
        </template>

        <div class="optimization-workspace">
          <aside class="optimization-workspace__timeline">
            <RoundTimeline
              v-model:active-id="form.active_round_id"
              :rounds="form.rounds"
            />
          </aside>

          <main class="optimization-workspace__detail">
            <template v-if="activeRound">
              <!-- 本轮操作：归档轮参数锁死，这里给出「以本轮为基线开新轮」的出口 -->
              <div class="round-action-bar">
                <div class="round-action-bar__info">
                  <span class="round-action-bar__title">
                    第 {{ activeRound.seq_idx ?? '-' }} 轮
                  </span>
                  <el-tag v-if="isRoundSealed" size="small" type="info">
                    <AppIcon icon="mdi:lock-outline" style="margin-right: 2px;" />
                    已归档
                  </el-tag>
                  <el-tag v-else size="small" type="warning">未评价</el-tag>
                </div>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  :loading="clone_loading"
                  :disabled="activeRound.parameter_id == null"
                  @click="cloneFromActiveRound"
                >
                  <AppIcon icon="mdi:content-copy" style="margin-right: 4px;" />
                  以此轮为基线开新轮
                </el-button>
              </div>

              <div class="round-detail-block round-detail-block--embedded">
                <div class="round-detail-block__title">
                  <AppIcon icon="mdi:cog-outline" />
                  <span>工艺参数</span>
                  <el-switch
                    :model-value="isParameterReadonly"
                    :disabled="isRoundSealed"
                    class="round-detail-block__action"
                    inline-prompt
                    active-text="只读"
                    inactive-text="编辑"
                    size="small"
                    @change="toggleReadonly"
                  />
                </div>
                <div v-if="isRoundSealed" class="round-sealed-hint">
                  <AppIcon icon="mdi:lock-outline" />
                  该轮参数已归档（是当时实际使用的工艺，属历史事实，不可修改）；评价仍可修改，
                  需要调整参数请「以此轮为基线开新轮」。
                </div>
                <TuningParameterPanel
                  :setting-process="activeRound.parameter"
                  :original-process="originalParameter"
                  :readonly="isParameterReadonly"
                />
              </div>

              <!-- 详情区顺序：参数 → 调整建议 → 工艺实测 → 缺陷反馈；缺陷永远在最后 -->
              <div class="round-detail-block">
                <div class="round-detail-block__title">
                  <AppIcon icon="mdi:lightbulb-on-outline" />
                  调整建议
                </div>
                <PreviousSuggestion :suggestion="activeRound.suggestion" />
              </div>

              <!-- 工艺实测：默认折叠（避免误导必填）+ 粘性状态（跨轮次保留） -->
              <div
                class="round-detail-block round-detail-block--collapsible"
                :class="{ 'is-collapsed': !observationExpanded }"
              >
                <el-tooltip
                  placement="top"
                  :show-after="200"
                  :hide-after="0"
                  popper-class="round-detail-block__tooltip"
                >
                  <template #content>
                    反馈实际工艺参数（重量/压力/时间等），辅助后端推理；参数可选填<br>
                    <small style="opacity: 0.7;">功能待完善，此处占位</small>
                  </template>
                  <div
                    class="round-detail-block__title round-detail-block__title--clickable"
                    role="button"
                    tabindex="0"
                    @click="observationExpanded = !observationExpanded"
                    @keydown.enter.prevent="observationExpanded = !observationExpanded"
                    @keydown.space.prevent="observationExpanded = !observationExpanded"
                  >
                    <AppIcon icon="mdi:gauge" />
                    <span>工艺实测</span>
                    <AppIcon
                      class="round-detail-block__chevron"
                      :icon="observationExpanded ? 'mdi:chevron-up' : 'mdi:chevron-down'"
                    />
                  </div>
                </el-tooltip>
                <Transition name="round-detail">
                  <div v-show="observationExpanded" class="round-detail-block__body">
                    <ProcessActualFeedback
                      v-model="activeRound.feedback.observations"
                      :machine-unit="machineUnit"
                    />
                  </div>
                </Transition>
              </div>

              <!-- 缺陷反馈：作为本轮试模的最终结果 -->
              <div class="round-detail-block">
                <div class="round-detail-block__title">
                  <AppIcon icon="mdi:alert-circle-outline" />
                  缺陷反馈
                </div>
                <DefectFeedback
                  v-model="activeRound.feedback.defect"
                  v-model:tuning-result="activeRound.feedback.tuning_result"
                  :has-comparison="activeRound.type !== 'initial'"
                  :defect-keywords="defectKeywords"
                  :position-keywords="positionKeywords"
                  :keywords-loaded="keywordsLoaded"
                />
              </div>
            </template>
            <el-empty
              v-else
              description="点击 [获取初始工艺] 开始调机"
              :image-size="80"
            />
          </main>
        </div>
      </el-card>
    </template>

    <div v-if="loaded" class="form-actions">
      <!-- 按钮配色语义：success=开新工艺 / warning=迭代优化 / plain=辅助 / primary=主操作 -->
      <el-button
        type="success"
        :loading="initial_loading"
        :disabled="hasInitialProcess"
        @click="getInitialProcess"
      >
        <AppIcon icon="mdi:auto-fix" style="margin-right: 4px;" />
        获取初始工艺
      </el-button>
      <el-button
        v-if="!isQualifiedResult"
        type="warning"
        :loading="optimize_loading"
        :disabled="!hasAnyProcess"
        @click="getOptimizedProcess"
      >
        <AppIcon icon="mdi:tune" style="margin-right: 4px;" />
        {{ isRoundSealed ? '基于本轮重新优化' : '获取优化工艺' }}
      </el-button>
      <el-button @click="toggleCondition">
        <AppIcon
          :icon="conditionExpanded ? 'mdi:chevron-up' : 'mdi:chevron-down'"
          style="margin-right: 4px;"
        />
        {{ conditionExpanded ? '折叠工艺条件' : '展开工艺条件' }}
      </el-button>
      <el-button @click="resetForm">
        <el-icon style="margin-right: 4px"><RefreshLeft /></el-icon>
        重置优化页面
      </el-button>
      <el-button
        type="primary"
        :loading="save_loading"
        :disabled="!hasActiveParameter"
        @click="onSubmit"
      >
        <el-icon style="margin-right: 4px"><Check /></el-icon>
        保存当前工艺
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RefreshLeft, Check } from '@element-plus/icons-vue'
import { settingProcessForm } from '@/constants/process-const'
import { DEFECTFREE_KEYWORD_NAME } from '@/constants/special-keywords'
import { listRuleKeywords } from '@/api/rule'
import {
  processInitializationFromMasterdata,
  processOptimizationInfer,
  processParameterCloneRound,
  tuningFeedback,
  processRecordHistory,
  processConditionDetail,
} from '@/api/index'
import type { TuningRoundItem } from '@/api/index'
import type { RuleKeyword } from '@/types/rule'
import type { Suggestion } from '@/types/optimization'
import {
  setSessionStorage,
  getSessionStorage,
  removeSessionStorage,
  createSessionStorageKey,
} from '@/utils/storage-session'
import ProcessCondition from '@/views/process/shared/ProcessCondition.vue'
import TuningParameterPanel from '../components/TuningParameterPanel.vue'
import RoundTimeline from '../components/RoundTimeline.vue'
import DefectFeedback from '../components/DefectFeedback.vue'
import ProcessActualFeedback from '../components/ProcessActualFeedback.vue'
import PreviousSuggestion from '../components/PreviousSuggestion.vue'
import { parameterToFlat, parameterFromFlat, hasFlatParameterContent, isEmptyFlatParameter } from '../components/parameterTransform'

// sessionStorage 持久化（避免切页面后丢失未提交的工艺数据）

/** sessionStorage key（带软件版本号）；保存 form / conditionExpanded / observationExpanded */
const STORAGE_KEY = createSessionStorageKey('optimization-create-draft')

/** debounce 延迟（ms）；输入框每键都触发 reactive，节流到 300ms 足够实时 */
const PERSIST_DEBOUNCE_MS = 300

/** 防抖定时器句柄（三个 watch 共用） */
let persistTimer: ReturnType<typeof setTimeout> | null = null
function schedulePersist() {
  if (persistTimer) clearTimeout(persistTimer)
  persistTimer = setTimeout(() => {
    persistTimer = null
    persistDraft()
  }, PERSIST_DEBOUNCE_MS)
}

/** 序列化并保存当前状态（走 JSON 而非 structuredClone：Vue 3 reactive Proxy 在后者会抛 DataCloneError） */
function persistDraft() {
  let plain: unknown
  try {
    plain = JSON.parse(JSON.stringify(form))
  } catch (err) {
    // 极端情况（循环引用 / BigInt）：跳过本次写入
    console.warn('[OptimizationCreate] persistDraft 序列化失败，已跳过:', err)
    return
  }
  setSessionStorage(STORAGE_KEY, {
    form: plain,
    // 变更高亮的参照基准由 rounds 派生（见 originalParameter）⇒ 无需持久化
    conditionExpanded: conditionExpanded.value,
    observationExpanded: observationExpanded.value,
  })
}

/** 清理防抖 + 立即写入（重置前调用，避免被 debounce 延迟的写覆盖重置结果） */
function flushPersist() {
  if (persistTimer) {
    clearTimeout(persistTimer)
    persistTimer = null
  }
  persistDraft()
}

/** 从 sessionStorage 恢复草稿（失败或 schema 异常返回 false，由调用方走默认初始化） */
function restoreDraft(): boolean {
  const cached = getSessionStorage<{
    form: typeof form
    conditionExpanded: boolean
    observationExpanded: boolean
  }>(STORAGE_KEY)
  if (!cached) return false

  const c = cached.form
  if (!c || typeof c !== 'object') return false
  if (!Array.isArray(c.rounds) || c.rounds.length === 0) return false
  if (typeof c.condition !== 'object' || c.condition === null) return false

  // 覆盖默认值（不调 resetForm，那里会清 storage）
  Object.assign(form, c)
  form.active_round_id = c.active_round_id ?? c.rounds[0]?.id ?? null
  conditionExpanded.value = cached.conditionExpanded ?? true
  observationExpanded.value = cached.observationExpanded ?? false
  return true
}

// 状态

/** 创建一个调机轮次（parameter 深克隆 settingProcessForm；parameter_id / seq_idx 初值 null，由【获取初始工艺】填充） */
function makeRound(type: 'initial' | 'optimized' | 'manual' = 'initial') {
  const now = Date.now()
  return {
    id: now,
    type,
    created_at: new Date(now).toISOString(),
    parameter_id: null as number | null,
    seq_idx: null as number | null,
    /** 该轮是否已归档（已落库评价 ⇒ 参数锁死，只能只读查看） */
    sealed: false,
    parameter: structuredClone(settingProcessForm) as any,
    // 该轮自身的算法建议（Recommendation 锚在该轮参数上；历史轮次回显时从后端还原）
    suggestion: null as Suggestion | null,
    feedback: {
      defect: [] as any,
      tuning_result: null as any,
      observations: [] as any,
    },
  }
}

const form = reactive({
  condition: {} as Record<string, any>,
  rounds: [makeRound('initial')] as Array<ReturnType<typeof makeRound>>,
  active_round_id: null as number | null,
})

const activeRound = computed(() =>
  form.rounds.find((r) => r.id === form.active_round_id) ?? null,
)

/**
 * 当前轮是否「合格」：合格态产品没有缺陷 ⇒ 不进入缺陷驱动的优化流程，
 * 所以隐藏【获取优化工艺】。提交通道仍可用 ——【保存当前工艺】照常落库。
 */
const isQualifiedResult = computed(
  () => activeRound.value?.feedback?.tuning_result === 'qualified',
)

/** 当前活动轮次的高亮参照基准：第 N 轮参照第 N-1 轮的 parameter（第 0 轮不参照）；由 rounds 派生的 computed */
const originalParameter = computed(() => {
  const idx = form.rounds.findIndex((r) => r.id === form.active_round_id)
  if (idx <= 0) return null
  const prev = form.rounds[idx - 1]
  if (!prev?.parameter) return null
  // 深拷贝：参照物必须是快照，不能与上一轮对象共享引用
  return JSON.parse(JSON.stringify(prev.parameter))
})

/** 工艺条件是否已有数据：有数据默认折叠（用户重心已上优化），无数据默认展开（需填条件） */
const hasConditionData = computed(() => {
  const c: any = form.condition ?? {}
  return Boolean(c.mold_id || c.injection_machine_id || c.polymer_id || c.condition_no)
})

/** 工艺按钮启用状态：hasInitialProcess 禁用【获取初始工艺】，hasAnyProcess 启用【获取优化工艺】（infer 需 parent_seq_idx） */
const hasInitialProcess = computed(() => Boolean(form.condition?.id))
const hasAnyProcess = computed(() =>
  form.rounds.some((r) => r.parameter_id != null),
)

const hasActiveParameter = computed(() =>
  activeRound.value?.parameter_id != null,
)

/** 机器单位映射（供 ProcessActualFeedback 使用）；重量无机器信息，默认 g */
const machineUnit = computed(() => {
  const m: any = form.condition?.machine_info ?? {}
  return {
    pressure: m.pressure_unit,
    time: m.time_unit,
    length: m.position_unit,
  }
})

const conditionExpanded = ref(true)

/** 工艺实测块是否展开（粘性状态：跨调机轮次保持）；默认折叠避免误导必填 */
const observationExpanded = ref(false)

/** 工艺参数区是否只读（用户手动切换，跨调机轮次保留） */
const isProcessReadonly = ref(false)

const isRoundSealed = computed(() => activeRound.value?.sealed === true)

/** 实际只读态：归档轮强制只读，用户开关只能进一步收紧（不能解锁归档轮） */
const isParameterReadonly = computed(() => isProcessReadonly.value || isRoundSealed.value)

/** 只读/编辑开关（归档轮下开关禁用，此函数不会被触发） */
function toggleReadonly(value: boolean) {
  isProcessReadonly.value = value
}

const clone_loading = ref(false)

const loaded = ref(false)
const save_loading = ref(false)
const initial_loading = ref(false)
const optimize_loading = ref(false)
const conditionRef = ref<InstanceType<typeof ProcessCondition> | null>(null)

/** 缺陷类 keyword 列表（后端 listRuleKeywords 未支持 category 过滤，前端拉全量后 filter） */
const defectKeywords = ref<RuleKeyword[]>([])
const positionKeywords = ref<RuleKeyword[]>([])
const keywordsLoaded = ref(false)

async function loadDefectKeywords() {
  keywordsLoaded.value = false
  try {
    // 兼容 { data: { items } } 与 { items } 两种响应格式
    const res = await listRuleKeywords({ page_size: 500 }) as any
    const items: RuleKeyword[] = res?.data?.items ?? res?.items ?? []
    defectKeywords.value = items.filter(
      k => k.category === 'defect' && k.keyword_name !== DEFECTFREE_KEYWORD_NAME,
    )
    positionKeywords.value = items.filter(k => k.category === 'defect_position')
  } catch {
    // 拦截器已统一 toast，这里只恢复兜底状态
    defectKeywords.value = []
    positionKeywords.value = []
  } finally {
    keywordsLoaded.value = true
  }
}

function toggleCondition() {
  // 经 v-model:expanded 同步到子组件（不直接调子组件方法，避免两处状态源）
  conditionExpanded.value = !conditionExpanded.value
}

// 数据加载

const route = useRoute()

/** 解析 URL 上的 condition_id（「继续调机」入口：/process/optimization?condition_id=123） */
function resolveConditionId(): number | null {
  const raw = route.query.condition_id
  const id = Number(Array.isArray(raw) ? raw[0] : raw)
  return Number.isInteger(id) && id > 0 ? id : null
}

/** 轮次类型推断：第 1 轮=初始；人工调整=手动；其余=优化 */
function inferRoundType(item: TuningRoundItem, index: number): 'initial' | 'optimized' | 'manual' {
  if (index === 0) return 'initial'
  if (item.param_source === 'manual_adjusted') return 'manual'
  return 'optimized'
}

/**
 * 从后端重建轮次（「继续调机」入口）
 *
 * 配对语义：第 N 轮 = 参数(N) + 反馈(N)，后端每轮自带自己的 tuning，不跨轮搬运。
 * 与草稿的取舍：草稿含未提交改动但换设备即失，不同源时以 URL 指定的 condition 为准。
 */
async function restoreFromServer(conditionId: number): Promise<boolean> {
  // allSettled 而非 all：detail 只补嵌套结构，失败也仍要能按 history 重建轮次
  // （all 会在 detail 失败时整体 reject ⇒ 页面显示草稿里的其它 condition）
  const [detailRes, historyRes] = await Promise.allSettled([
    processConditionDetail(conditionId),
    processRecordHistory(conditionId),
  ])
  const detailData = detailRes.status === "fulfilled" ? (detailRes.value?.data ?? {}) : {}
  // detail 返回的是扁平 condition（嵌套信息在顶层），兼容 {condition:{...}} 包装形态
  const detail = detailData.condition ?? detailData
  const historyData = historyRes.status === "fulfilled" ? (historyRes.value?.data ?? {}) : {}
  const history: TuningRoundItem[] = historyData.history ?? []
  if (!history.length) return false

  // 扁平字段取 history.condition、嵌套结构取 detail；先清空旧键再合并，
  // 避免草稿残留字段混入（保持 form.condition 引用不变）
  for (const key of Object.keys(form.condition)) {
    delete (form.condition as Record<string, any>)[key]
  }
  // process_parameters 是 detail 带出的全量轮次，前端用不到 ⇒ 剔除以免草稿体积膨胀
  const detailRest = { ...detail }
  delete detailRest.process_parameters
  Object.assign(form.condition, historyData.condition ?? {}, detailRest)

  // 后端按 created_at 倒序返回 → 按 seq_idx 正序（第 1 轮在前）
  const ordered = [...history].sort((a, b) => (a.seq_idx ?? 0) - (b.seq_idx ?? 0))
  const rounds = ordered.map((item, index) => {
    const t = item.tuning
    return {
      id: item.id,
      type: inferRoundType(item, index),
      created_at: item.created_at ?? new Date().toISOString(),
      parameter_id: item.id,
      seq_idx: item.seq_idx ?? null,
      sealed: item.sealed ?? false,
      parameter: parameterFromFlat(item as any),
      suggestion: item.tuning?.suggestion
        ? {
            source_round_id: item.id,
            adopted: item.tuning.suggestion.adopted ?? null,
            groups: item.tuning.suggestion.groups ?? [],
          }
        : null,
      feedback: {
        defect: (t?.defect_feedbacks ?? []) as any,
        tuning_result: t?.tuning_result ?? null,
        // 实测观察后端不落库（tuning-feedback schema 明确不存），回显为空
        observations: [] as any,
      },
    }
  })

  form.rounds.splice(0, form.rounds.length, ...(rounds as any))
  form.active_round_id = rounds[rounds.length - 1].id
  return true
}

/** 加载表单：优先从 sessionStorage 恢复草稿，失败走默认初始化（restore 成功后才挂 watch，避免初始写覆盖旧数据） */
async function loadForm() {
  loaded.value = false
  try {
    const conditionId = resolveConditionId()
    const restored = restoreDraft()
    if (conditionId != null && Number(form.condition.id) !== conditionId) {
      // URL 指定了另一个 condition（草稿属于别的会话）→ 以服务端为准重建轮次
      await restoreFromServer(conditionId)
    } else if (!restored) {
      Object.assign(form, {
        condition: {},
        rounds: [makeRound('initial')],
        active_round_id: null,
      })
      form.active_round_id = form.rounds[0]?.id ?? null
      conditionExpanded.value = true
      observationExpanded.value = false
    }
    loaded.value = true
  } catch {
    // 拦截器已统一 toast，这里只置 loaded 避免死锁
    loaded.value = true
  }
}

// 操作

/** 重置表单（原地清空而非替换引用：ProcessCondition.vue 只包装了首次引用，替换会让子组件停留在旧数据） */
async function resetForm() {
  try {
    await ElMessageBox.confirm(
      '确定要重置当前优化页面吗？所有未保存的工艺数据、轮次、缺陷反馈将被清除。',
      '重置确认',
      {
        type: 'warning',
        confirmButtonText: '重置',
        cancelButtonText: '取消',
        // 数据丢失风险高：禁用 ESC / 点遮罩关闭，强制明确操作
        closeOnClickModal: false,
        closeOnPressEscape: false,
      },
    )
  } catch {
    return  // 用户取消
  }

  flushPersist()
  removeSessionStorage(STORAGE_KEY)

  // 清空 form.condition 所有字段（保留对象引用，让子组件 reactive proxy 能跟上）
  if (form.condition) {
    for (const key of Object.keys(form.condition)) {
      delete (form.condition as Record<string, any>)[key]
    }
  }

  // 重置 rounds：splice 保留数组引用，computed activeRound 能感知
  form.rounds.splice(0, form.rounds.length, makeRound('initial'))
  form.active_round_id = form.rounds[0]?.id ?? null

  // 父组件 label 与子组件折叠态各设一次：conditionRef.expand() 直设子组件内部状态，
  // 不走 watch props 的 pre-flush 时序，避免「UI 仍折叠但 label 已变」的错位
  conditionExpanded.value = true
  conditionRef.value?.expand?.()
  observationExpanded.value = false

  ElMessage.success('优化页面已重置')
}

/*
 * 形态：后端 initialize / optimize 都返回 flat（inj_pres_1..6 / hold_t_1..5 ...），
 * 前端 settingProcessForm 是嵌套结构，翻译统一由 parameterFromFlat 负责。
 *
 * 原子语义：所有写入集中在本函数内顺序执行，要么都写入要么都不写入
 * （抛错由调用方 catch 回滚），避免出现「condition 已更新但 param 未更新」的中间态。
 */

/** 把后端推理响应原子地应用到前端表单（缺字段跳过，不主动 throw） */
function applyInferResultToForm(result: any) {
  const data = result?.data
  if (!data) return

  if (data.condition_id) form.condition.id = data.condition_id
  if (data.condition_no) form.condition.condition_no = data.condition_no

  if (!activeRound.value) return

  if (data.parameter_id != null) {
    activeRound.value.parameter_id = data.parameter_id
    // 同步更新 created_at：占位 round 的时间点不准，parameter_id 写入才是真正创建时刻
    activeRound.value.created_at = new Date().toISOString()
  }
  if (data.seq_idx != null) {
    activeRound.value.seq_idx = data.seq_idx
  }
  if (data.process) {
    activeRound.value.parameter = parameterFromFlat(data.process)
  }
}

/** 获取初始工艺：调用 /initialization/from-masterdata/ 生成初始参数（模具/注塑机/材料/shot_index/injection_index 5 项必填） */
async function getInitialProcess() {
  const isValid = await conditionRef.value?.checkFormDataValid()
  if (!isValid) return

  initial_loading.value = true
  try {
    const result: any = await processInitializationFromMasterdata({
      // 字段在 ProcessCondition 内以嵌套结构存储（mold_info/machine_info/polymer_info）
      mold_id: form.condition.mold_info?.id,
      polymer_id: form.condition.polymer_info?.id,
      injection_machine_id: form.condition.machine_info?.id,
      shot_index: form.condition.shot_index ?? 0,
      injection_index: form.condition.injection_index ?? 0,
    })

    // 集中应用响应，保证原子性
    applyInferResultToForm(result)

    ElMessage.success('已生成初始工艺参数')
  } catch {
    // 拦截器已统一 toast
  } finally {
    initial_loading.value = false
  }
}

/**
 * 校验本轮缺陷反馈完整性
 *
 * 口径：只有「合格」允许不带缺陷（合格态无缺陷，也不进入缺陷驱动的优化流程）；
 * 其余档位必须带缺陷，否则算法没有优化对象（与后端 `_validate_feedback` 一致）。
 */
interface FeedbackValidation {
  ok: boolean
  error?: string
}
function validateFeedback(feedback: any): FeedbackValidation {
  const defects = feedback?.defect
  const list = Array.isArray(defects) ? defects : []
  if (!feedback?.tuning_result) {
    return { ok: false, error: '请选择本轮工艺效果评价' }
  }
  if (list.length === 0 && feedback.tuning_result !== 'qualified') {
    return { ok: false, error: '请填写缺陷反馈信息' }
  }
  for (let i = 0; i < list.length; i++) {
    const d = list[i]
    if (d?.keyword_name == null) {
      return { ok: false, error: `第 ${i + 1} 项缺陷未选择缺陷类型` }
    }
    const isDefectFree = d?.keyword_name === DEFECTFREE_KEYWORD_NAME
    if (!isDefectFree) {
      if (d?.level == null || d?.level === '') {
        return { ok: false, error: `第 ${i + 1} 项缺陷未选择缺陷程度` }
      }
      if (!d?.position || d.position === '') {
        return { ok: false, error: `第 ${i + 1} 项缺陷未填写缺陷位置` }
      }
    }
  }
  return { ok: true }
}

/**
 * 以当前轮为基线开新轮（clone）
 *
 * 归档轮参数不可改写，但可「回到某一轮重来」：后端以源轮参数为起点新建第 N+1 轮
 * （parent 指向源轮），源轮零改动，新轮未评价 ⇒ 参数可继续编辑。
 */
async function cloneFromActiveRound() {
  const round = activeRound.value
  if (!round?.parameter_id) {
    ElMessage.warning('当前轮次尚未落库，无法作为基线')
    return
  }
  clone_loading.value = true
  try {
    const res: any = await processParameterCloneRound(round.parameter_id)
    const data = res?.data ?? {}
    if (res?.status !== 0 || data?.id == null) {
      ElMessage.error(res?.msg || '开新轮失败，请稍后重试')
      return
    }
    const newRound = makeRound('manual')
    newRound.parameter_id = data.id
    newRound.seq_idx = data.seq_idx ?? null
    newRound.parameter = parameterFromFlat(data)
    form.rounds.push(newRound)
    form.active_round_id = newRound.id
    ElMessage.success(
      `已基于第 ${round.seq_idx ?? '-'} 轮创建新轮（第 ${data.seq_idx ?? '-'} 轮），参数可继续编辑`,
    )
  } catch {
    // 拦截器已统一 toast
  } finally {
    clone_loading.value = false
  }
}

/** 获取优化工艺：调 /optimization/infer/ 生成新轮次（需先有初始工艺与完整缺陷反馈；infer 后新建轮次而非替换当前轮次） */
async function getOptimizedProcess() {
  // 前置校验：需先有初始工艺（condition.id）与 seq_idx（infer 依赖）
  if (!form.condition?.id) {
    ElMessage.warning('请先点击【获取初始工艺】生成工艺条件')
    return
  }
  if (!activeRound.value?.seq_idx) {
    ElMessage.warning('当前轮次缺少 seq_idx，请重置后重试')
    return
  }
  // 合格态不进入缺陷驱动的优化流程（正常路径下按钮已隐藏，这里防御）
  if (isQualifiedResult.value) {
    ElMessage.info('产品已合格，无需进行工艺优化')
    return
  }
  // 缺陷反馈完整性校验（避免后端静默接收空 feedback 导致不报期望）
  const validation = validateFeedback(activeRound.value?.feedback)
  if (!validation.ok) {
    ElMessage.warning(validation.error!)
    return
  }

  // 无缺陷时算法没有优化对象（后端会 fail-fast 报「推荐算法暂不可用」，对用户是误导）
  if (!(activeRound.value?.feedback?.defect?.length)) {
    ElMessage.warning('本轮未填写缺陷，暂无优化建议')
    return
  }

  optimize_loading.value = true
  try {
    // 工艺参数：嵌套 form → flat（算法契约源头就是 flat）
    // - 没改参数则不传（service 从 ORM 反查 parent_param）
    // - 改了就传 flat dict（后端校验「至少一个工艺字段」，空 dict 会在 HTTP 边界报错而非污染 baseline）
    const flatParameter = parameterToFlat(activeRound.value?.parameter)
    const parameterPayload = isEmptyFlatParameter(flatParameter) ? undefined : flatParameter

    const result: any = await processOptimizationInfer({
      condition_id: form.condition.id,
      parent_seq_idx: activeRound.value.seq_idx,
      parameter: parameterPayload,
      feedback: activeRound.value.feedback,
    })

    const inferData = result?.data ?? result ?? {}

    // 合格态短路响应（后端不跑 fuzzy、不建新轮次）——正常路径按钮已隐藏，这里防御别把空轮次塞进时间线
    if (inferData.skipped) {
      ElMessage.info(inferData.message || '本轮已记录，未进行工艺优化')
      return
    }

    // 响应有效性校验：new_parameter / suggestion.groups 缺失时不进下一轮（排查走服务端日志）
    const hasNewParameter = !!(
      inferData.new_parameter && inferData.new_parameter.parameter_id != null
    )
    const hasSuggestion = Array.isArray(inferData.suggestion?.groups)
      && inferData.suggestion.groups.length > 0

    if (!hasNewParameter || !hasSuggestion) {
      ElMessage.error('推荐算法暂不可用，请稍后重试或联系管理员')
      return
    }

    const newRound = makeRound('optimized')
    if (inferData.new_parameter) {
      newRound.parameter_id = inferData.new_parameter.parameter_id ?? null
      newRound.seq_idx = inferData.new_parameter.seq_idx ?? null
      // 关键：flat → nested 后填入新轮次，否则表格停留在空模板（settingProcessForm 全 null）静默空白
      newRound.parameter = parameterFromFlat(inferData.new_parameter)
      if (!hasFlatParameterContent(inferData.new_parameter)) {
        ElMessage.warning('优化响应未携带工艺参数字段，参数表可能为空，请检查服务端日志')
      }
    }
    form.rounds.push(newRound)
    form.active_round_id = newRound.id

    // 调整建议挂到 newRound（Recommendation 锚在其所属 parameter 上）⇒ 切回历史轮次不会串轮
    if (inferData.suggestion && Array.isArray(inferData.suggestion.groups)) {
      newRound.suggestion = {
        source_round_id: newRound.id,
        adopted: null,  // 未确认（待本轮填 effective/ineffective 后自动变更）
        groups: inferData.suggestion.groups,
      }
    }

    const groupCount = inferData.suggestion.groups.length
    const seqIdx = inferData.new_parameter?.seq_idx ?? '-'
    // 面向用户只说「第几轮」，不暴露数据库主键（parameter_id 是内部标识）
    ElMessage.success(
      `优化工艺已生成（第 ${seqIdx} 轮），建议 ${groupCount} 类`,
    )
  } catch {
    // 拦截器已统一 toast（已在 getOptimizedProcess 顶部校验响应有效性）
  } finally {
    optimize_loading.value = false
  }
}

/** 提交当前轮次试模结果（TuningRecord 落库；幂等覆盖，不创建新 ProcessParameter） */
async function onSubmit() {
  if (!activeRound.value) {
    ElMessage.warning('请先选择调机轮次')
    return
  }
  if (activeRound.value.parameter_id == null) {
    ElMessage.warning('当前轮次未绑定工艺参数，请先调【获取初始工艺】或【获取优化工艺】')
    return
  }

  save_loading.value = true
  try {
    const feedback = activeRound.value.feedback || {}
    // 工艺参数一并提交：后端在同一事务里写回参数 + 评价，语义 =「我用了这组参数，试模结果是 X」
    // （参数没改则不传，退化为只写评价）
    const flatParameter = parameterToFlat(activeRound.value.parameter)
    // 归档轮次参数锁死：只提交评价（后端也会忽略参数，这里先不传避免无谓往返）
    const parameterPayload = isRoundSealed.value
      ? undefined
      : (isEmptyFlatParameter(flatParameter) ? undefined : flatParameter)
    const res: any = await tuningFeedback(activeRound.value.parameter_id, {
      defect_feedbacks: feedback.defect ?? [],
      observations: feedback.observations ?? [],
      tuning_result: feedback.tuning_result ?? null,
      parameter: parameterPayload,
    })
    if (res?.status === 0) {
      const created = res.data?.created
      if (res.data?.parameter_locked) {
        ElMessage.warning('该轮参数已归档，仅保存了试模评价')
      } else {
        // 落库评价后该轮即归档（参数锁死），同步本地标记让参数区立即变只读
        activeRound.value.sealed = true
        ElMessage.success(created ? '已保存当前试模结果' : '已更新当前试模结果')
      }
    } else {
      // HTTP 200 但 status !== 0：业务失败（不走 catch，由调用方自己 toast）
      ElMessage.error(res?.msg || '保存失败，请稍后重试')
    }
  } catch {
    // 拦截器已统一 toast
  } finally {
    save_loading.value = false
  }
}

onMounted(() => {
  loadForm()
  loadDefectKeywords()

  /*
   * 持久化 watch：挂载后才挂（不 immediate），避免初始写覆盖读到的旧数据。
   * form 深嵌套必须深 watch，两个 boolean ref 独立 watch 以减少依赖追踪；
   * 三个回调统一走 schedulePersist，共用同一 debounce 定时器。
   */
  watch(
    () => form,
    () => schedulePersist(),
    { deep: true },
  )
  watch(conditionExpanded, () => schedulePersist())
  watch(observationExpanded, () => schedulePersist())
})

onBeforeUnmount(() => {
  if (persistTimer) {
    clearTimeout(persistTimer)
    persistTimer = null
  }
})
</script>

<style lang="scss" scoped>
.optimization-create {
  padding: 16px 16px 96px;
}

/* header：与 ProcessCondition.vue 视觉对齐
   - 左侧 18x18 灰 icon + 主题色条 + 标题，与工艺条件的 chevron 占同一视觉锚点
   - icon 无点击行为，颜色调灰（#606266）避免喧宾夺主 */
.optimization-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 4px 0;

  &-left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  &-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    color: #606266;
    vertical-align: middle;
  }
}

/* 工作台布局：左侧时间线 280px（约 1/4~1/3），右侧详情 1fr */
.optimization-workspace {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  min-height: 400px;

  &__timeline {
    border: 1px solid var(--color-border-extra-light, #ebeef5);
    border-radius: 4px;
    background: #fff;
    height: 100%;
    min-height: 0;  // 避免 grid/flex 子项无法收缩
    overflow-y: auto;
  }

  &__detail {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.round-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid var(--color-border-extra-light, #ebeef5);
  border-radius: 4px;

  &__info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__title {
    font-weight: 600;
    font-size: 14px;
  }
}

/* 归档提示：浅底 + 锁图标，说明「为什么不能改」 */
.round-sealed-hint {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--color-bg-overlay, #f5f7fa);
  border-radius: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
}

/* 详情区每个区块：浅色背景条 + 图标，与左侧时间线 header 视觉呼应 */
.round-detail-block {
  background: #fff;
  border: 1px solid var(--color-border-extra-light, #ebeef5);
  border-radius: 4px;

  // 上下 12 / 16，与上下其他 block 节奏一致；避免表单/子组件紧贴标题
  padding: 12px 16px 16px;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px 6px;
    background: var(--color-bg-overlay, #f5f7fa);
    border-bottom: 1px solid var(--color-border-extra-light, #ebeef5);
    font-weight: 600;
    font-size: 14px;
    // 负 margin 抵消外层 padding，让背景条仍贴左右边缘
    margin: -12px -16px 12px;

    &--clickable {
      cursor: pointer;
      user-select: none;
      outline: none;
      transition: background-color 0.15s ease;

      &:hover {
        background: #ebeef5;
      }

      &:focus-visible {
        box-shadow: inset 0 0 0 2px var(--el-color-primary-light-5, #409eff);
      }
    }
  }

  /* chevron：推到最右侧 + 胶囊型「呼吸背景」提示可交互 */
  &__chevron {
    margin-left: auto;
    color: var(--el-text-color-secondary, #909399);
    padding: 2px 6px;
    border-radius: 10px;
    transition: transform 0.25s ease, background-color 0.25s ease;
  }

  /* 动作区（如「只读 / 编辑」switch）：推到最右侧，与 chevron 复用同一原则 */
  &__action {
    margin-left: auto;
  }

  // 折叠态 chevron 呼吸提示（透明度 0.04~0.18，可见但不眨眼；仅 is-collapsed 生效）
  &--collapsible.is-collapsed &__chevron {
    animation: chevron-breathe 2.4s ease-in-out infinite;
  }

  @keyframes chevron-breathe {
    0%, 100% { background-color: rgba(64, 158, 255, 0.08); }
    50%      { background-color: rgba(64, 158, 255, 0.36); }
  }

  /* body 仅占位，内边距由子组件自行处理 */
  &__body {
    display: block;
  }

  /*
   * 嵌入态：TuningParameterPanel 外层 wrapper 透明化
   * - 避免外层 border 与 wrapper 的 box-shadow/padding 叠加成三层视觉重量
   * - 仅作用于本页面嵌入场景，组件默认态不变；内部 3 个 process-card 仍保留 border
   */
  &--embedded :deep(.process-settings-wrapper) {
    background-color: transparent;
    box-shadow: none;
    border-radius: 0;
    padding: 0;
  }

  /* 折叠块：去掉底部内边距 + title 下 margin / 下边框（避免 body display:none 后的残留空白） */
  &--collapsible {
    transition: padding-bottom 0.25s ease;

    .round-detail-block__title {
      transition: margin-bottom 0.25s ease, border-bottom-color 0.25s ease;
    }

    &.is-collapsed {
      padding-bottom: 0;

      .round-detail-block__title {
        margin-bottom: 0;
        border-bottom-color: transparent;
      }
    }
  }
}

/* round-detail 过渡：opacity 与 max-height 同 duration（避免「先淡后塌」）
   max-height 取 240px（≈4 行表单项 200px），过大会让动画前段空转 */
.round-detail-enter-active,
.round-detail-leave-active {
  transition: opacity 0.25s ease, max-height 0.25s ease;
  overflow: hidden;
}
.round-detail-enter-from,
.round-detail-leave-to {
  opacity: 0;
  max-height: 0;
}
.round-detail-enter-to,
.round-detail-leave-from {
  opacity: 1;
  max-height: 240px;
}
</style>
