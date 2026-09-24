<!--
  OptimizationCreate - 工艺优化（工作台）
  - 工艺优化 = 基于工艺条件 + 缺陷反馈，迭代优化工艺参数
  - 工艺条件复用 shared/ProcessCondition
  - 工作台：入口单一，无返回按钮
-->
<template>
  <div class="optimization-create">
    <div v-if="!loaded" v-loading="true" class="loading-placeholder" />

    <template v-else>
      <!-- 工艺条件卡（复用） -->
      <ProcessCondition
        ref="conditionRef"
        :process-condition="form.condition"
        mode="edit"
        :default-expanded="!hasConditionData"
        :disabled="hasInitialProcess"
      />

      <!-- 工艺优化工作台 -->
      <el-card class="box-card optimization-card" style="margin-top: 16px">
        <template #header>
          <span class="custom-form__title">
            <AppIcon icon="mdi:tune-vertical" class="custom-form__title-icon" />
            工艺优化
          </span>
        </template>

        <div class="optimization-workspace">
          <!-- 左侧：调机过程时间线 -->
          <aside class="optimization-workspace__timeline">
            <RoundTimeline
              v-model:active-id="form.active_round_id"
              :rounds="form.rounds"
            />
          </aside>

          <!-- 右侧：当前轮次详情 -->
          <main class="optimization-workspace__detail">
            <template v-if="activeRound">
              <!-- 工艺参数展示 -->
              <div class="round-detail-block round-detail-block--embedded">
                <div class="round-detail-block__title">
                  <AppIcon icon="mdi:cog-outline" />
                  <span>工艺参数</span>
                  <el-switch
                    v-model="isProcessReadonly"
                    class="round-detail-block__action"
                    inline-prompt
                    active-text="只读"
                    inactive-text="编辑"
                    size="small"
                  />
                </div>
                <SettingProcess
                  :setting-process="activeRound.parameter"
                  :readonly="isProcessReadonly"
                />
              </div>

              <!--
                详情区顺序：工艺参数 → 上一轮建议 → 工艺实测 → 缺陷反馈
                - 参数（事实）/ 上一轮建议（回顾）/ 工艺实测（验证）/ 缺陷反馈（结果）
                - 缺陷反馈永远在最后；中间可插入模温机 / 热流道等反馈类
              -->
              <div class="round-detail-block">
                <div class="round-detail-block__title">
                  <AppIcon icon="mdi:lightbulb-on-outline" />
                  上一轮调整建议
                </div>
                <PreviousSuggestion :suggestion="previousSuggestion" />
              </div>

              <!--
                工艺实测：默认折叠（理论上大部分场景用不上，避免误导必填）
                - 展开后 chevron 旋转 + body 高度过渡
                - 折叠状态跨轮次粘性保留
              -->
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

              <!-- 缺陷反馈（永远位于最下方，作为本轮试模的最终结果） -->
              <div class="round-detail-block">
                <div class="round-detail-block__title">
                  <AppIcon icon="mdi:alert-circle-outline" />
                  缺陷反馈
                </div>
                <DefectFeedback
                  v-model="activeRound.feedback.defect"
                  :defect-keywords="defectKeywords"
                  :position-keywords="positionKeywords"
                  :keywords-loaded="keywordsLoaded"
                />
              </div>
            </template>
            <!-- 默认轮次不需 empty，但若 activeRound 缺失则兜底 -->
            <el-empty
              v-else
              description="点击 [获取初始工艺] 开始调机"
              :image-size="80"
            />
          </main>
        </div>
      </el-card>
    </template>

    <!-- 底部操作 -->
    <div v-if="loaded" class="form-actions">
      <!--
        配色原则（2026-09-23）：
        - 获取初始工艺：success 绿 — 创建成功（开新工艺）
        - 获取优化工艺：warning 黄 — 迭代优化（每次都是新决策）
        - 重置 / 折叠：plain — 中性辅助操作
        - 保存：primary 蓝 — 主操作（提交唯一入口）

        状态联动（业务流互斥）：
        - 获取初始工艺：有初始工艺后需重置才能重调
        - 获取优化工艺：必须先有工艺（任意轮次 parameter_id 存在）
      -->
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
        type="warning"
        :loading="optimize_loading"
        :disabled="!hasAnyProcess"
        @click="getOptimizedProcess"
      >
        <AppIcon icon="mdi:tune" style="margin-right: 4px;" />
        获取优化工艺
      </el-button>
      <el-button @click="toggleCondition">
        <AppIcon
          :icon="conditionExpanded ? 'mdi:chevron-up' : 'mdi:chevron-down'"
          style="margin-right: 4px;"
        />
        {{ conditionExpanded ? '折叠条件' : '展开条件' }}
      </el-button>
      <el-button @click="resetForm">重置</el-button>
      <el-button type="primary" :loading="save_loading" @click="onSubmit">
        保存
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { settingProcessForm } from '@/constants/process-const'
import { listRuleKeywords } from '@/api/rule'
import { processInitializationFromMasterdata, processOptimizationInfer } from '@/api/index'
import type { RuleKeyword } from '@/types/rule'
import type { Suggestion } from '@/types/optimization'
import {
  setSessionStorage,
  getSessionStorage,
  removeSessionStorage,
  createSessionStorageKey,
} from '@/utils/storage-session'
import ProcessCondition from '@/views/process/shared/ProcessCondition.vue'
import SettingProcess from '@/views/process/shared/SettingProcess.vue'
import RoundTimeline from '../components/RoundTimeline.vue'
import DefectFeedback from '../components/DefectFeedback.vue'
import ProcessActualFeedback from '../components/ProcessActualFeedback.vue'
import PreviousSuggestion from '../components/PreviousSuggestion.vue'

// ============================================================================
// sessionStorage 持久化（避免切页面后丢失未提交的工艺数据）
// ============================================================================

/**
 * sessionStorage key（带软件版本号）
 * - 保存：form / conditionExpanded / observationExpanded
 * - 不保存：loaded / *_loading / defectKeywords / previousSuggestion（mock） / conditionSyncTimer
 */
const STORAGE_KEY = createSessionStorageKey('optimization-create-draft')

/** debounce 延迟（ms）；输入框每键都触发 reactive，节流到 300ms 足够实时 */
const PERSIST_DEBOUNCE_MS = 300

/** 防抖定时器句柄（form / conditionExpanded / observationExpanded 共用） */
let persistTimer: ReturnType<typeof setTimeout> | null = null
function schedulePersist() {
  if (persistTimer) clearTimeout(persistTimer)
  persistTimer = setTimeout(() => {
    persistTimer = null
    persistDraft()
  }, PERSIST_DEBOUNCE_MS)
}

/**
 * 序列化并保存当前状态
 * - 走 JSON 序列化不走 structuredClone：Vue 3 的 reactive Proxy 在 Chrome 的
 *   structuredClone 路径上会抛 DataCloneError（form 嵌套了 mold_info / machine_info
 *   等 API 响应对象）。JSON 路径兼容性最好（足够处理表单数据）
 * - setSessionStorage 内部已 try-catch，失败静默
 */
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

/**
 * 从 sessionStorage 恢复草稿
 * - 恢复失败 / schema 异常 → 返回 false，调用方走默认初始化
 * - schema 校验：rounds 非空数组 + condition 为 plain object，防止 storage 中的
 *   过期 / 损坏数据引起崩溃
 */
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

// ============================================================================
// 状态
// ============================================================================

/**
 * 创建一个调机轮次
 * - id/created_at 用时间戳避免重复
 * - parameter 深克隆 settingProcessForm，表数据 / max_stage 字段齐全
 * - feedback 初值：defect=空数组，tuning_result/observations=null；预留 mold_temp / hot_runner
 * - parameter_id：初始为 null，被【获取初始工艺】填充（后端 ProcessParameter.id）
 * - seq_idx：初始为 null，被【获取初始工艺】填充（业务编号，condition 内全局递增）
 *   下一次 infer 需传作 parent_seq_idx
 *   注：不在 parameter 内部存储，保持 settingProcessForm 纯度
 */
function makeRound(type: 'initial' | 'optimized' | 'manual' = 'initial') {
  const now = Date.now()
  return {
    id: now,
    type,
    created_at: new Date(now).toISOString(),
    parameter_id: null as number | null,
    seq_idx: null as number | null,
    parameter: structuredClone(settingProcessForm) as any,
    feedback: {
      defect: [] as any,
      tuning_result: null as any,
      observations: [] as any,
      // mold_temp / hot_runner：未来接入模温机 / 热流道反馈
    },
  }
}

const form = reactive({
  condition: {} as Record<string, any>,
  rounds: [makeRound('initial')] as Array<ReturnType<typeof makeRound>>,
  active_round_id: null as number | null,
})

/** 页面初始化后默认选中首个轮次 */
form.active_round_id = form.rounds[0]?.id ?? null

const activeRound = computed(() =>
  form.rounds.find((r) => r.id === form.active_round_id) ?? null,
)

/** 工艺条件是否已有数据：有数据默认折叠（用户重心已上优化），无数据默认展开（需填条件） */
const hasConditionData = computed(() => {
  const c: any = form.condition ?? {}
  return Boolean(c.mold_id || c.injection_machine_id || c.polymer_id || c.condition_no)
})

/**
 * 工艺按钮启用状态（业务流互斥，2026-09-23 加）：
 * - hasInitialProcess：已创建初始工艺（condition_id 存在）。此时 [获取初始工艺]
 *   应 disabled，需走 [重置] 才能重调（避免覆盖已生成的 condition/parameter）
 * - hasAnyProcess：已有任意轮次落库（任意 round.parameter_id 存在）。此时
 *   [获取优化工艺] 可用 —— infer 需 parent_seq_idx，而 parent_seq_idx 必须
 *   有上一轮已落库的 parameter 才能反查
 */
const hasInitialProcess = computed(() => Boolean(form.condition?.id))
const hasAnyProcess = computed(() =>
  form.rounds.some((r) => r.parameter_id != null),
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

/** 子组件内部 toggle 不会通知父组件，定时 poll 同步 */
let conditionSyncTimer: ReturnType<typeof setInterval> | null = null

const loaded = ref(false)
const save_loading = ref(false)
const initial_loading = ref(false)
const optimize_loading = ref(false)
const conditionRef = ref<InstanceType<typeof ProcessCondition> | null>(null)

// ============================================================================
// 缺陷 keyword 列表（DefectFeedback 需要）
// ============================================================================

/**
 * 缺陷类 keyword 列表
 * - 后端 listRuleKeywords 未实现 category 过滤，前端拉全部后 filter
 * - TODO（后端支持后可改为参数过滤）
 */
const defectKeywords = ref<RuleKeyword[]>([])
const positionKeywords = ref<RuleKeyword[]>([])
const keywordsLoaded = ref(false)

async function loadDefectKeywords() {
  keywordsLoaded.value = false
  try {
    // 兼容两种响应格式：{ status, msg, data: { total, items } } 或 res.items
    const res = await listRuleKeywords({ page_size: 500 }) as any
    const items: RuleKeyword[] = res?.data?.items ?? res?.items ?? []
    defectKeywords.value = items.filter(k => k.category === 'defect')
    positionKeywords.value = items.filter(k => k.category === 'defect_position')
  } catch (err: any) {
    ElMessage.error(err?.message || '缺陷 keyword 加载失败')
    defectKeywords.value = []
    positionKeywords.value = []
  } finally {
    keywordsLoaded.value = true
  }
}

// ============================================================================
// 上一轮调整建议（开发阶段 mock，后续接入算法响应）
// ============================================================================

/** 上一轮算法 / 工艺员调整建议；生产环境来源：上一轮 infer 接口的 suggestion 字段 */
const previousSuggestion = ref<Suggestion | null>({
  source_round_id: 0,
  adopted: null,  // 未确认
  groups: [
    {
      category: '工艺调整',
      icon: 'mdi:tune-variant',
      items: [
        {
          description: '降低注射一段压力 5 MPa',
          direction: 'decrease',
          rule_refs: ['M001', 'M005'],
        },
        {
          description: '延长保压时间 0.5 s',
          direction: 'increase',
          rule_refs: ['M003'],
        },
        {
          description: '检查产品壁厚均匀性',
          direction: 'check',
        },
      ],
    },
    {
      category: '模温调整',
      icon: 'mdi:thermometer',
      items: [
        {
          description: '提高动模温度 10 ℃',
          direction: 'increase',
        },
        {
          description: '定模温度保持不变',
          direction: 'hold',
        },
      ],
    },
  ],
})

function toggleCondition() {
  conditionRef.value?.toggle()
  syncConditionExpanded()
}

/** 同步子组件折叠状态（如点 header）→ 修正按钮文字 */
function syncConditionExpanded() {
  const cur = conditionRef.value?.isExpanded?.()
  if (typeof cur === 'boolean' && cur !== conditionExpanded.value) {
    conditionExpanded.value = cur
  }
}

// ============================================================================
// 数据加载
// ============================================================================

/**
 * 加载表单：优先从 sessionStorage 恢复草稿，失败走默认初始化
 * - 静默恢复，符合「切页面自动接着填」的预期
 * - 不在 setup 顶部调 restoreDraft：form 还未定义；改为 loaded=false 阶段调
 * - restore 成功后才挂 watch，否则 setup 顶部 reactive 后立即 watch 会触发
 *   「初始写」覆盖 restoreDraft 读到的旧数据
 */
async function loadForm() {
  loaded.value = false
  try {
    const restored = restoreDraft()
    if (!restored) {
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
  } catch (err: any) {
    ElMessage.error(err?.message || '加载失败')
    loaded.value = true
  }
}

// ============================================================================
// 操作
// ============================================================================

/**
 * 重置表单（用户主动清空数据）
 * - 二次确认避免误操作
 * - flushPersist 清掉任何 pending debounce 写，避免覆盖重置结果
 *
 * 重要：不能替换 form.condition / form.rounds 的整个引用——
 *   - ProcessCondition.vue 在 setup 时 reactive(props.processCondition) 包装了**第一次**的引用
 *   - 后续替换 form.condition 不会重包装，子组件 UI 会停留在旧数据
 *   - 改用 mutate（delete / splice）保留引用，触发 reactive set/deleteProperty
 */
async function resetForm() {
  try {
    await ElMessageBox.confirm(
      '确定要重置当前页面吗？所有未保存的工艺数据、轮次、缺陷反馈将被清除。',
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

  conditionExpanded.value = true
  observationExpanded.value = false

  ElMessage.success('页面已重置')
}

// ============================================================================
// 后端推理响应 → 前端表单（原子应用）
// ============================================================================
// 背景：
//   后端 /initialization/from-masterdata/ 返回扁平工艺字段（inj_pres_steps 等），
//   前端 settingProcessForm 是嵌套结构（injection / holding / metering / ...）。
//   这里负责两层映射 + 一步原子应用。
//
// 原子语义：
//   后端 Condition + Parameter 落库在同一事务（要么都成功，要么都回滚）。
//   前端 JS 单线程：响应进入应用函数后，同步顺序执行所有赋值，要么都写入，
//   要么一个都不写入（抛错时由调用方的 catch 统一回滚）。
//   设计上所有写入集中在一个函数，不允许在调用点散落赋值，避免出现「cond
//   已更新但 param 未更新」的中间状态。

/** 把后端 steps 数组补齐到 max 长度，缺的填 null（前端 UI 需要固定长度） */
function padSteps(steps: Array<number | null | undefined> | null | undefined, max: number): Array<number | null> {
  if (!Array.isArray(steps)) return new Array(max).fill(null)
  // 后端 steps 元素本身不会传 undefined，过滤保持类型严谨
  const padded: Array<number | null> = (steps as Array<number | null>).slice()
  while (padded.length < max) padded.push(null)
  return padded.slice(0, max)
}

/**
 * 把后端推理 result.process（扁平 ProcessParams.to_dict）映射到前端 settingProcessForm
 *
 * 后端字段参考：backend/process/engines/expert/param_types.py:ProcessParams
 * 前端结构参考：frontend/src/constants/process-const.ts:settingProcessForm
 */
function mapInferResultToParameter(result: any): typeof settingProcessForm {
  const p = result?.process ?? {}
  void result?.mold_temp
  // hot_runner 暂不映射（前端 SettingProcess 未提供阀口时间设置）
  return {
    injection: {
      ...settingProcessForm.injection,
      stage: p.inj_stg ?? 1,
      table_data: [
        { label: '压力', unit: 'MPa', sections: padSteps(p.inj_pres_steps, 6) },
        { label: '速度', unit: 'mm/s', sections: padSteps(p.inj_spd_steps, 6) },
        { label: '位置', unit: 'mm', sections: padSteps(p.inj_pos_steps, 6) },
      ],
      injection_time: p.inj_t ?? null,
      delay_time: p.inj_dly_t ?? null,
      cooling_time: p.cool_t ?? null,
    },
    vp_switch: {
      ...settingProcessForm.vp_switch,
      mode: p.vps_mode ?? 0,
      position: p.vps_pos ?? null,
      time: p.vps_t ?? null,
      pressure: p.vps_pres ?? null,
      velocity: p.vps_spd ?? null,
    },
    holding: {
      ...settingProcessForm.holding,
      stage: p.hold_stg ?? 1,
      table_data: [
        { label: '压力', unit: 'MPa', sections: padSteps(p.hold_pres_steps, 5) },
        { label: '速度', unit: 'mm/s', sections: padSteps(p.hold_spd_steps, 5) },
        { label: '时间', unit: 's', sections: padSteps(p.hold_time_steps, 5) },
      ],
    },
    metering: {
      ...settingProcessForm.metering,
      stage: p.met_stg ?? 1,
      table_data: [
        { label: '压力', unit: 'MPa', sections: padSteps(p.met_pres_steps, 4) },
        { label: '螺杆转速', unit: 'rpm', sections: padSteps(p.met_rot_spd_steps, 4) },
        { label: '背压', unit: 'MPa', sections: padSteps(p.met_back_pres_steps, 4) },
        { label: '位置', unit: 'mm', sections: padSteps(p.met_pos_steps, 4) },
      ],
      delay_time: p.met_lim_t ?? null,
      ending_position: p.met_end_pos ?? null,
    },
    barrel_temperature: {
      ...settingProcessForm.barrel_temperature,
      stage: p.brl_temp_stg ?? 5,
      table_data: [
        { label: '温度', unit: '℃', sections: padSteps(p.brl_temp_steps, 10) },
      ],
    },
  }
}

/**
 * 把后端推理响应原子地应用到前端表单
 *
 * 设计要点：
 *   - 全部字段在一个同步函数里赋值（JS 单线程，默认原子）
 *   - 缺字段跳过（如只拿到 condition_id 没拿到 parameter_id 不处理参数部分）
 *   - 不主动 throw（任何异常都让调用方 catch 统一处理）
 *   - 后端用 {status, msg, timestamp, data: ...} 包裹，axios 拦截器返回整个 body，
 *     所以这里从 result.data 取业务数据
 *
 * 依赖：调用方在赋值前确保 form / activeRound 已初始化。
 */
function applyInferResultToForm(result: any) {
  const data = result?.data
  if (!data) return

  // 1) 工艺条件（ProcessCondition）
  if (data.condition_id) form.condition.id = data.condition_id
  if (data.condition_no) form.condition.condition_no = data.condition_no

  // 2) 当前轮次工艺参数（ProcessParameter）
  if (!activeRound.value) return

  if (data.parameter_id != null) {
    activeRound.value.parameter_id = data.parameter_id
  }
  if (data.seq_idx != null) {
    activeRound.value.seq_idx = data.seq_idx
  }
  if (data.process) {
    activeRound.value.parameter = mapInferResultToParameter(data)
  }
}

/**
 * 获取初始工艺：调用后端 /initialization/from-masterdata/ 生成初始参数
 *
 * 业务约束：
 * - 模具 / 注塑机 / 材料 / shot_index / injection_index 5 项必填
 *   （由 ProcessCondition.checkFormDataValid 统一校验）
 * - 响应写入 form.condition.id（condition_id）和 activeRound.parameter_id（parameter_id）
 * - 响应写入 activeRound.parameter（工艺参数嵌套结构，详见 mapInferResultToParameter）
 *
 * 关联文档：
 * docs/process-get-initial-frontend-integration-2026-09-23.md
 * docs/process-frontend-param-mapping-atomic-2026-09-23.md
 */
async function getInitialProcess() {
  // Step 1: 5 项必填校验（ProcessCondition 组件复用校验逻辑）
  const isValid = await conditionRef.value?.checkFormDataValid()
  if (!isValid) return

  initial_loading.value = true
  try {
    // Step 2: 调用后端
    const result: any = await processInitializationFromMasterdata({
      mold_id: form.condition.mold_id,
      polymer_id: form.condition.polymer_id,
      injection_machine_id: form.condition.injection_machine_id,
      shot_index: form.condition.shot_index ?? 0,
      injection_index: form.condition.injection_index ?? 0,
    })

    // Step 3: 响应处理（集中到 applyInferResultToForm，保证原子性）
    applyInferResultToForm(result)

    // Step 4: 成功提示（toast 摘要）
    const ruleHint = Array.isArray(result?.data?.matched_rules) && result.data.matched_rules.length > 0
      ? `（命中 ${result.data.matched_rules.length} 条规则）`
      : ''
    ElMessage.success(
      `初始工艺已生成 condition_id=${result?.data?.condition_id ?? '-'}, `
      + `parameter_id=${result?.data?.parameter_id ?? '-'}, `
      + `seq_idx=${result?.data?.seq_idx ?? '-'}${ruleHint}`,
    )
  } catch (err: any) {
    // request.ts 拦截器已 ElMessage.warning 显示了后端响应 data.msg
    // （含 BizException 详情，如 "工艺参数输入字段不足 - 缺少字段: gate_type, ..."）
    // 这里仅保留袌底，不重复 toast（避免双重提示）
    console.error('[getInitialProcess] 调用后端失败:', err)
  } finally {
    initial_loading.value = false
  }
}

/**
 * 获取优化工艺：调后端 /optimization/infer/ 生成新轮次
 *
 * 业务约束：
 * - 必须先调 getInitialProcess（前置依赖：form.condition.id + activeRound.seq_idx）
 * - infer 后创建新轮次（不替换当前轮次），保持调机树语义
 * - previousSuggestion 由 infer 响应的 suggestion 字段填充
 *   （替换原 mock 数据，这是 docs 原则 6 / 8 的实现）
 *
 * 响应处理：
 * - new_parameter.parameter_id / seq_idx → 新轮次
 * - suggestion.groups → previousSuggestion.groups（供 UI 展示"上一轮调整建议"）
 *
 * 关联文档：docs/process-get-optimized-frontend-integration-2026-09-23.md
 */
async function getOptimizedProcess() {
  // Step 1: 前置校验
  if (!form.condition?.id) {
    ElMessage.warning('请先点击【获取初始工艺】生成工艺条件')
    return
  }
  if (!activeRound.value?.seq_idx) {
    ElMessage.warning('当前轮次缺少 seq_idx，请重置后重试')
    return
  }

  optimize_loading.value = true
  try {
    // Step 2: 调用后端
    const result: any = await processOptimizationInfer({
      condition_id: form.condition.id,
      parent_seq_idx: activeRound.value.seq_idx,
      feedback: activeRound.value.feedback,
    })

    // Step 3: 创建新轮次（optimized）+ 切换 active
    const newRound = makeRound('optimized')
    // 后端响应包装：{status, msg, timestamp, data: {...}}；业务数据在 .data 下
    const inferData = result?.data ?? result ?? {}
    if (inferData.new_parameter) {
      newRound.parameter_id = inferData.new_parameter.parameter_id ?? null
      newRound.seq_idx = inferData.new_parameter.seq_idx ?? null
    }
    form.rounds.push(newRound)
    form.active_round_id = newRound.id

    // Step 4: 更新 previousSuggestion（上一轮调整建议）
    if (inferData.suggestion && Array.isArray(inferData.suggestion.groups)) {
      previousSuggestion.value = {
        source_round_id: activeRound.value.id,  // 上一轮 round.id
        adopted: null,  // 未确认（待本轮填 effective/ineffective 后自动变更）
        groups: inferData.suggestion.groups,
      }
    }

    // Step 5: 成功提示（toast 摘要）
    const groupCount = Array.isArray(inferData.suggestion?.groups)
      ? inferData.suggestion.groups.length
      : 0
    ElMessage.success(
      `优化工艺已生成 seq_idx=${inferData.new_parameter?.seq_idx ?? '-'}, `
      + `parameter_id=${inferData.new_parameter?.parameter_id ?? '-'}, `
      + `建议 ${groupCount} 类`,
    )
  } catch (err: any) {
    // request.ts 拦截器已 ElMessage.warning 显示了后端响应 data.msg
    // （含 BizException 详情，含 infer 错误或字段缺失提示）
    // 这里仅保留袌底，不重复 toast（避免双重提示）
    console.error('[getOptimizedProcess] 调用后端失败:', err)
  } finally {
    optimize_loading.value = false
  }
}

/** 提交保存。TODO：调保存接口 */
async function onSubmit() {
  save_loading.value = true
  try {
    // TODO: 提交保存
    ElMessage.success('保存成功')
  } catch (err: any) {
    ElMessage.error(err?.message || '保存失败')
  } finally {
    save_loading.value = false
  }
}

onMounted(() => {
  loadForm()
  loadDefectKeywords()
  syncConditionExpanded()
  conditionSyncTimer = setInterval(syncConditionExpanded, 250)

  /*
   * 持久化 watch —— 挂载后才挂（不 immediate）
   * - 挂载前 form 已被 restoreDraft / loadForm 默认初始化填好，避免初始写覆盖读到的旧数据
   * - 为什么 3 个 watch 而不是 1 个数组 watch：
   *   - form 深嵌套（rounds[i].parameter 含 table_data），深 watch 开销大但不可避
   *   - conditionExpanded / observationExpanded 是普通 boolean ref，独立 watch 减少依赖追踪
   *   - 三个回调统一走 schedulePersist，共用同一个 debounce 定时器，不会多次写
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
  if (conditionSyncTimer) {
    clearInterval(conditionSyncTimer)
    conditionSyncTimer = null
  }
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

.loading-placeholder {
  height: 400px;
}

/*
 * 工艺优化工作台布局（左侧时间线 + 右侧详情）
 * - 280px 给左侧（约 1/4 ~ 1/3），1fr 给右侧
 * - 详情区超过 600px 时出现纵向滚动
 */
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

  /* body 容器：仅占位，无内边距，由子组件自行处理 */
  &__body {
    display: block;
  }

  /*
   * 嵌入态：当块内嵌 SettingProcess 时让其外层 wrapper 透明化
   * - 避免外层 border 与 wrapper 的 box-shadow/padding 叠加形成三层视觉重量
   * - 仅影响本页面嵌入场景；SettingProcess 默认态不变
   * - 3 个 process-card 仍保留 border（作为 SettingProcess 内部状态分隔）
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

/*
 * round-detail 过渡：opacity 与 max-height 同 duration 紧（避免「先淡后塌」）
 * - max-height 240px（接近 4 行表单项实际高度 200px），避免 600px 过大导致动画前 1/3「空转」
 */
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
