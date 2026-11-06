<!-- RuleMethodForm.vue - 模糊规则方法编辑表单（new / edit / detail 三模式共用） -->
<template>
  <div :class="['rule-method-form', embedded ? 'rule-method-form--embedded' : '']">
    <!-- 顶部 page-header（标题） -->
    <div v-if="showPageHeader" class="page-header">
      <h2 class="page-title">
        {{ mode === 'new' ? '新建规则方法' : mode === 'edit' ? '编辑规则方法' : '规则方法详情' }}
      </h2>
    </div>

    <div v-if="!loaded" v-loading="true" class="loading-placeholder" />

    <template v-else>
      <div class="form-body">
        <!-- ============ 左编辑区（50%）============ -->
        <div class="edit-area">
          <!-- 元数据卡 -->
          <el-card class="custom-form__section" shadow="never">
            <template #header>
              <span class="custom-form__title">元数据</span>
            </template>
            <el-form :model="form" label-width="100px" class="custom-form">
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="材料缩写">
                    <el-select
                      v-model="form.polymer_abbreviation"
                      filterable
                      clearable
                      :disabled="isReadonly"
                      placeholder="留空 = 不限"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="p in polymers"
                        :key="p.id"
                        :label="p.abbreviation"
                        :value="p.abbreviation"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="产品类别">
                    <el-input
                      v-model="form.product_category"
                      :disabled="isReadonly"
                      placeholder="如 汽车配件（留空=不限）"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="优先级">
                    <el-input-number v-model="form.priority" :min="0" :max="100" :disabled="isReadonly" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="置信度">
                    <el-input-number
                      v-model="form.confidence"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      :precision="2"
                      :disabled="isReadonly"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="启用">
                    <el-switch v-model="form.is_active" :disabled="isReadonly" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </el-card>

          <!-- 前置条件（CONDITION）卡 -->
          <el-card class="custom-form__section" shadow="never">
            <template #header>
              <span class="custom-form__title">前置条件（CONDITION）</span>
            </template>
            <div class="condition-block-list">
              <template v-for="(cond, i) in form.preconditions" :key="i">
                <div :class="['condition-row', `condition-row-${i}`]">
                  <!-- 行首连接词：IF（第一行）/ AND（后续行），标识模糊规则结构 -->
                  <span class="row-prefix" :class="{ 'row-prefix--start': i === 0 }">
                    {{ i === 0 ? 'IF' : 'AND' }}
                  </span>

                  <!-- 关键字 dropdown：prefix 图标区分缺陷 / 参数 / 缺陷位置 -->
                  <el-select
                    v-model="cond.keyword"
                    filterable
                    :disabled="isReadonly"
                    :placeholder="i === 0 ? '选择主要缺陷' : '选择关键字'"
                    style="width: 200px;"
                    @change="onConditionKeywordChange(cond)"
                  >
                    <template #prefix>
                      <AppIcon icon="mdi:tag-outline" style="color: #909399;" />
                    </template>
                    <template v-if="i === 0">
                      <el-option-group label="缺陷">
                        <el-option
                          v-for="k in defectKeywords"
                          :key="k.keyword_name"
                          :label="k.keyword_alias"
                          :value="k.keyword_name"
                        />
                      </el-option-group>
                    </template>
                    <template v-else>
                      <el-option-group label="参数">
                        <el-option
                          v-for="k in parameterKeywords"
                          :key="k.keyword_name"
                          :label="k.keyword_alias"
                          :value="k.keyword_name"
                        />
                      </el-option-group>
                      <el-option-group label="缺陷">
                        <el-option
                          v-for="k in defectKeywords"
                          :key="k.keyword_name"
                          :label="k.keyword_alias"
                          :value="k.keyword_name"
                        />
                      </el-option-group>
                      <el-option-group label="缺陷位置">
                        <el-option
                          v-for="k in defectPositionKeywords"
                          :key="k.keyword_name"
                          :label="k.keyword_alias"
                          :value="k.keyword_name"
                        />
                      </el-option-group>
                    </template>
                  </el-select>

                  <!-- 模糊等级 dropdown -->
                  <el-select
                    v-model="cond.level"
                    :disabled="isReadonly || !cond.keyword"
                    placeholder="等级"
                    style="width: 120px;"
                  >
                    <template #prefix>
                      <AppIcon icon="mdi:signal" style="color: #909399;" />
                    </template>
                    <el-option
                      v-for="lvl in levelOptionsFor(cond)"
                      :key="lvl"
                      :label="levelLabelFor(cond, lvl)"
                      :value="lvl"
                    />
                  </el-select>

                  <!-- 删除按钮：第 1 个不让删（主要缺陷不可删）+ 至少保留 1 个 -->
                  <el-button
                    v-if="!isReadonly && i > 0 && form.preconditions.length > 1"
                    text
                    type="danger"
                    size="small"
                    class="row-action-btn"
                    @click="removeCondition(i)"
                  >
                    <AppIcon icon="mdi:trash-can-outline" style="margin-right: 2px;" />
                    删除
                  </el-button>
                </div>
              </template>
            </div>

            <!-- 添加条件：文字链风格，对齐 GatingSystemForm 规范 -->
            <div class="add-button-wrapper">
              <el-button
                v-if="!isReadonly"
                text
                type="primary"
                size="small"
                @click="addCondition"
              >
                <AppIcon icon="mdi:plus" style="margin-right: 4px;" />
                添加条件
              </el-button>
            </div>
          </el-card>

          <!-- 结论动作（SOLUTION）卡 -->
          <el-card class="custom-form__section" shadow="never">
            <template #header>
              <span class="custom-form__title">结论动作（SOLUTION）</span>
            </template>
            <div class="action-block-list">
              <template v-for="(act, i) in form.actions" :key="i">
                <div :class="['action-row', `action-row-${i}`]">
                  <!-- 行首连接词：THEN（第一行）/ AND（后续行），标识模糊规则结论结构 -->
                  <span class="row-prefix" :class="{ 'row-prefix--start': i === 0 }">
                    {{ i === 0 ? 'THEN' : 'AND' }}
                  </span>

                  <el-select
                    v-model="act.keyword"
                    filterable
                    :disabled="isReadonly"
                    placeholder="选择参数"
                    style="width: 200px;"
                  >
                    <template #prefix>
                      <AppIcon icon="mdi:tune-vertical" style="color: #909399;" />
                    </template>
                    <el-option
                      v-for="k in parameterKeywords"
                      :key="k.keyword_name"
                      :label="k.keyword_alias"
                      :value="k.keyword_name"
                    />
                  </el-select>

                  <el-select
                    v-model="act.action"
                    :disabled="isReadonly"
                    placeholder="动作"
                    style="width: 120px;"
                  >
                    <template #prefix>
                      <AppIcon icon="mdi:arrow-right-bold" style="color: #909399;" />
                    </template>
                    <el-option
                      v-for="a in ACTIONS"
                      :key="a.value"
                      :label="a.label"
                      :value="a.value"
                    />
                  </el-select>

                  <el-input
                    v-model="act.value"
                    :disabled="isReadonly"
                    placeholder="值"
                    style="width: 120px;"
                  >
                    <template #prefix>
                      <AppIcon icon="mdi:format-text" style="color: #909399;" />
                    </template>
                  </el-input>

                  <!-- 删除按钮：第 1 个不让删（主动作不可删）+ 至少保留 1 个 -->
                  <el-button
                    v-if="!isReadonly && i > 0 && form.actions.length > 1"
                    text
                    type="danger"
                    size="small"
                    class="row-action-btn"
                    @click="removeAction(i)"
                  >
                    <AppIcon icon="mdi:trash-can-outline" style="margin-right: 2px;" />
                    删除
                  </el-button>
                </div>
              </template>
            </div>

            <!-- 添加动作：文字链风格 -->
            <div class="add-button-wrapper">
              <el-button
                v-if="!isReadonly"
                text
                type="primary"
                size="small"
                @click="addAction"
              >
                <AppIcon icon="mdi:plus" style="margin-right: 4px;" />
                添加动作
              </el-button>
            </div>
          </el-card>

          <!-- 文本预览卡（左侧底部） -->
          <el-card class="custom-form__section" shadow="never">
            <template #header>
              <span class="custom-form__title">文本预览（自动生成）</span>
            </template>
            <el-form label-width="100px" class="custom-form">
              <el-form-item label="规则描述">
                <el-input
                  v-model="form.rule_description"
                  type="textarea"
                  :rows="2"
                  readonly
                  placeholder="IF 条件 AND 条件 THEN 动作 AND 动作（自动生成）"
                />
              </el-form-item>
              <el-form-item label="规则解释">
                <el-input
                  v-model="form.rule_explanation"
                  type="textarea"
                  :rows="3"
                  readonly
                  placeholder="如果...那么...（自动生成）"
                />
              </el-form-item>
            </el-form>
          </el-card>
        </div>

        <!-- ============ 右流程图预览（50%，sticky）============ -->
        <div class="graph-area">
          <RuleMethodGraph
            :conditions="form.preconditions"
            :actions="form.actions"
            :keywords="allKeywords"
            @node-click="onGraphNodeClick"
          />
        </div>
      </div>

      <!-- 底部操作（全局 .form-actions） -->
      <!-- 两类模式：独立路由（显示 page-header + form-actions）／drawer 嵌入（仅 form-actions） -->
      <div v-if="showFormActions" class="form-actions">
        <!-- detail 模式：只显示返回 -->
        <template v-if="mode === 'detail'">
          <el-button @click="goBack">
            <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
            返回规则库
          </el-button>
        </template>

        <!-- new/edit 模式（drawer / 独立路由共用）：完整操作 -->
        <template v-else>
          <el-button @click="onCancel">
            <AppIcon icon="mdi:close" style="margin-right: 4px; font-size: 14px;" />
            取消
          </el-button>
          <el-button v-if="mode === 'new'" type="warning" @click="resetForm">
            <AppIcon icon="mdi:refresh" style="margin-right: 4px; font-size: 14px;" />
            重置
          </el-button>
          <el-button type="primary" :loading="save_loading" @click="onSubmit">
            <AppIcon icon="mdi:content-save-outline" style="margin-right: 4px; font-size: 14px;" />
            {{ mode === 'new' ? '保存' : '更新' }}
          </el-button>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/** 模糊规则方法编辑表单：new / edit / detail 三模式由 route 切换；结构化字段（preconditions + actions）自动生成 rule_description / rule_explanation（不允许直接编辑规则文本）；字典一次性加载后按 category 分组；流程图随字段实时刷新 */
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import RuleMethodGraph from '../components/RuleMethodGraph.vue'
import {
  getRuleMethod,
  createRuleMethod,
  updateRuleMethod,
  listRuleKeywords,
} from '@/api/rule'
import { polymerMethod } from '@/api'
import type { RuleKeyword, RuleMethodCreatePayload } from '@/types/rule'

// 常量
// 前置条件 level 词字典：业界渐进式命名（very_/extremely_ 两端扩展，medium 居中对称）；新规则用 medium，历史 1752 条用 mid 兼容

import {
  LEVEL_WORDS,
  DEFECT_LEVEL_LABELS,
  PARAMETER_LEVEL_LABELS,
} from '@/constants/rule-const'

/** 根据当前条件的 keyword 选填合适的 LEVEL_LABELS（parameter → PARAMETER_LEVEL_LABELS，defect / defect_position → DEFECT_LEVEL_LABELS）。 */
function levelLabelsFor(cond: ConditionItem): Record<string, string> {
  const kw = allKeywords.value.find(k => k.keyword_name === cond.keyword)
  return kw?.category === 'parameter' ? PARAMETER_LEVEL_LABELS : DEFECT_LEVEL_LABELS
}

function levelLabelFor(cond: ConditionItem, lvl: string): string {
  return levelLabelsFor(cond)[lvl] || lvl
}

const ACTIONS = [
  { label: '增加', value: 'add' },
  { label: '减小', value: 'reduce' },
  { label: '弹窗', value: 'adjust' },
  { label: '设定', value: 'set' },
]

const ACTION_LABELS: Record<string, string> = {
  add: '增加', reduce: '减小', adjust: '弹窗', set: '设定',
}

// Props / Emits

const props = withDefaults(
  defineProps<{
    /** 规则库 ID（从 drawer 嵌入时传递，否则从 route.params.libraryId 读）*/
    libraryId?: number
    /** 规则方法 ID（从 drawer 嵌入时传递，否则从 route.params.methodId 读；undefined 表示新建）*/
    methodId?: number
    /** 是否显示顶部 page-header（独立路由访问时为 true，drawer 嵌入时为 false）*/
    showPageHeader?: boolean
    /** 是否显示底部 form-actions（独立路由访问时为 true，drawer 嵌入时为 false）*/
    showFormActions?: boolean
    /** 是否嵌入在 drawer 内（控制容器 padding / 动画）*/
    embedded?: boolean
  }>(),
  {
    showPageHeader: true,
    showFormActions: true,
    embedded: false,
  },
)

const emit = defineEmits<{
  /** drawer 嵌入时点击取消 / 关闭 */
  (e: 'close'): void
  /** drawer 嵌入时保存成功 */
  (e: 'saved', methodId: number): void
}>()

// 路由 & 模式

const route = useRoute()
const router = useRouter()

/** 实际生效的 libraryId / methodId */
const effectiveLibraryId = computed(() => 
  props.libraryId ?? Number(route.params.libraryId)
)
const effectiveMethodId = computed(() => 
  props.methodId ?? Number(route.params.methodId)
)

/** mode 派生（由路由或 props 决定） */
const mode = computed<'new' | 'edit' | 'detail'>(() => {
  if (route.name === 'process-rule-method-detail') return 'detail'
  // 有 methodId 表示编辑
  if (effectiveMethodId.value) return 'edit'
  return 'new'
})

const isReadonly = computed(() => mode.value === 'detail')

// 字典加载

const allKeywords = ref<RuleKeyword[]>([])
const parameterKeywords = computed(() => allKeywords.value.filter(k => k.category === 'parameter'))
const defectKeywords = computed(() => allKeywords.value.filter(k => k.category === 'defect'))
const defectPositionKeywords = computed(() => allKeywords.value.filter(k => k.category === 'defect_position'))

const polymers = ref<Array<{ id: number; abbreviation: string }>>([])

async function loadDictionaries() {
  // 关键词字典（一次性加载，按需过滤）
  const kwRes: any = await listRuleKeywords({ page_no: 1, page_size: 1000 })
  allKeywords.value = kwRes.data?.items || kwRes.items || []

  // 材料字典
  const polyRes: any = await polymerMethod.get({ page_no: 1, page_size: 1000 })
  polymers.value = polyRes.data?.items || polyRes.items || []
}

/** keyword_name → keyword_alias 的映射（用于规则解释） */
function aliasOf(keywordName: string): string {
  return allKeywords.value.find(k => k.keyword_name === keywordName)?.keyword_alias || keywordName
}

// 表单数据
/** 前置条件：keyword（首项限缺陷类别）+ level（按 keyword.fuzzy_level 取档位）；条件侧是纯模糊集词，不需要运算符，生成格式 IF keyword level AND ... */
interface ConditionItem {
  keyword: string
  level: string
}

interface ActionItem {
  keyword: string
  action: string
  /** action 调整量：el-input，接受任意文本（数值或模糊量词）。前端不做任何限制、不预设下拉——后端按 value 内容自动分发到 NumTskRuleNet（数值结论，主路径）或 FuzzyRuleNet（Mamdani 模糊量词）。 */
  value: string
}

const form = reactive<{
  rule_library_id: number
  polymer_abbreviation: string
  product_category: string
  priority: number
  confidence: number
  /** 来源：前端 UI 不展示不修改，但保留后端原值用于回写（新建默认 'expert'，编辑读入后端真实值，可能是 rule_miner / llm 产出） */
  source: 'expert' | 'rule_miner' | 'llm'
  is_active: boolean
  rule_description: string
  rule_explanation: string
  preconditions: ConditionItem[]
  actions: ActionItem[]
}>({
  rule_library_id: 0,
  polymer_abbreviation: '',
  product_category: '',
  priority: 1,
  confidence: 1.0,
  source: 'expert',
  is_active: true,
  rule_description: '',
  rule_explanation: '',
  preconditions: [{ keyword: '', level: '' }],
  actions: [{ keyword: '', action: 'add', value: '' }],
})

/** new 模式下重置为空白默认状态（edit 模式无"撤销修改"按钮，功能与"取消"重复） */
const initialFormState = () => ({
  rule_library_id: 0,
  polymer_abbreviation: '',
  product_category: '',
  priority: 1,
  confidence: 1.0,
  source: 'expert' as const,
  is_active: true,
  rule_description: '',
  rule_explanation: '',
  preconditions: [{ keyword: '', level: '' }],
  actions: [{ keyword: '', action: 'add', value: '' }],
})

function resetForm() {
  if (mode.value === 'new') {
    Object.assign(form, initialFormState(), { rule_library_id: effectiveLibraryId.value })
  }
}

const loaded = ref(false)
const save_loading = ref(false)

// 增删条件/动作

function addCondition() {
  form.preconditions.push({ keyword: '', level: '' })
}

function removeCondition(i: number) {
  form.preconditions.splice(i, 1)
  // 保证至少 1 行（避免空数组报错）
  if (form.preconditions.length === 0) addCondition()
}

/** level 下拉选项：按 keyword.fuzzy_level 返回 level 词列表（未选 keyword 返回 []，fuzzy_level 不在 3/5/7 范围时兜底为 3 档） */
function levelOptionsFor(cond: ConditionItem): string[] {
  if (!cond.keyword) return []
  const kw = allKeywords.value.find(k => k.keyword_name === cond.keyword)
  const lvl = kw?.fuzzy_level
  if (lvl === 3 || lvl === 5 || lvl === 7) {
    return LEVEL_WORDS[lvl]
  }
  // 兜底：3 档
  return LEVEL_WORDS[3]
}

/** keyword 切换时清空 level（因为 fuzzy_level 可能不同，旧 level 可能无效） */
function onConditionKeywordChange(cond: ConditionItem) {
  cond.level = ''
}

function addAction() {
  form.actions.push({ keyword: '', action: 'add', value: '' })
}

function removeAction(i: number) {
  form.actions.splice(i, 1)
  if (form.actions.length === 0) addAction()
}

// 联动 & 交互：缺陷名称 / 缺陷标识由后端从 preconditions 自动提取，前端不展示不联动

/** 流程图节点点击 → 滚动到对应编辑行 + 高亮闪烁 */
function onGraphNodeClick(payload: { type: 'condition' | 'action'; index: number }) {
  const selector = payload.type === 'condition'
    ? `.condition-row-${payload.index}`
    : `.action-row-${payload.index}`
  const el = document.querySelector(selector) as HTMLElement | null
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('highlight-flash')
    setTimeout(() => el.classList.remove('highlight-flash'), 2000)
  }
}

// 自动生成规则文本（核心逻辑）

function generateRuleText() {
  // 规则描述（机器语言）：IF keyword_level AND keyword_level THEN keyword_action_value AND ...（token 化契约见后端 _split_phase：条件侧 keyword_level 必须是单 token，勿写成 "SHORTSHOT low"；动作侧用 _ 分隔 name_action_value，如 MEL_add_10 / MEL_add_low）
  const condDesc = form.preconditions
    .filter(c => c.keyword && c.level)
    .map(c => `${c.keyword}_${c.level}`)
    .join(' AND ')

  const actDesc = form.actions
    .filter(a => a.keyword && a.value !== '' && a.value !== null)
    .map(a => `${a.keyword}_${a.action}_${a.value}`)
    .join(' AND ')

  form.rule_description = condDesc && actDesc
    ? `IF ${condDesc} THEN ${actDesc}`
    : ''

  // 规则解释（人类语言）：如果A为level，且B为level，那么A动作V，A动作V。（中文拼接紧凑不加空格，跟 JSON 数据中的中文风格保持一致）
  const condExp = form.preconditions
    .filter(c => c.keyword && c.level)
    .map(c => {
      const alias = aliasOf(c.keyword)
      const lvl = levelLabelFor(c, c.level)
      return `${alias}为${lvl}`
    })
    .join('且')

  const actExp = form.actions
    .filter(a => a.keyword && a.value !== '' && a.value !== null)
    .map(a => {
      const alias = aliasOf(a.keyword)
      const act = ACTION_LABELS[a.action] || a.action
      return `${alias}${act}${a.value}`
    })
    .join('，')

  form.rule_explanation = condExp && actExp
    ? `如果${condExp}，那么${actExp}。`
    : ''
}

/** 实时同步：结构化字段变化 → 文本预览重生成 */
watch(
  () => [form.preconditions, form.actions],
  generateRuleText,
  { deep: true },
)

// 数据加载

async function loadForm() {
  loaded.value = false
  await loadDictionaries()

  try {
    if (mode.value === 'new') {
      // 新建：空 form + 规则库 ID 来自 props 或 route
      form.rule_library_id = effectiveLibraryId.value
    } else {
      // 编辑 / 详情：拉取后端数据
      const id = effectiveMethodId.value
      if (!id) {
        ElMessage.error('无效的规则方法 ID')
        goBack()
        return
      }
      const res: any = await getRuleMethod(id)
      if (res?.status === 0 && res.data) {
        const data = res.data
        Object.assign(form, {
          rule_library_id: data.rule_library_id,
          polymer_abbreviation: data.polymer_abbreviation || '',
          product_category: data.product_category || '',
          priority: data.priority ?? 1,
          confidence: data.confidence ?? 1.0,
          source: (data.source as 'expert' | 'rule_miner' | 'llm') || 'expert',
          is_active: data.is_active ?? true,
          rule_description: data.rule_description || '',
          rule_explanation: data.rule_explanation || '',
          // Phase 1：编辑现有规则时 preconditions/actions 留空（用户重新填）
          preconditions: [{ keyword: '', level: '' }],
          actions: [{ keyword: '', action: 'add', value: '' }],
        })
      } else {
        ElMessage.error(res?.msg || '加载失败')
        goBack()
        return
      }
    }
  } catch {
    // 拦截器已统一 toast + console
    goBack()
    return
  } finally {
    loaded.value = true
  }
}

// 校验 & 提交

function validate(): boolean {
  if (!form.rule_library_id) {
    ElMessage.error('规则库 ID 缺失')
    return false
  }
  if (form.preconditions.length === 0) {
    ElMessage.warning('请至少添加 1 个前置条件')
    return false
  }
  if (form.actions.length === 0) {
    ElMessage.warning('请至少添加 1 个结论动作')
    return false
  }
  for (const [i, c] of form.preconditions.entries()) {
    if (!c.keyword) {
      ElMessage.warning(`前置条件 ${i + 1}：关键字未填`)
      return false
    }
    if (!c.level) {
      ElMessage.warning(`前置条件 ${i + 1}：模糊等级未填`)
      return false
    }
  }
  for (const [i, a] of form.actions.entries()) {
    if (!a.keyword) {
      ElMessage.warning(`结论动作 ${i + 1}：关键字未填`)
      return false
    }
    if (a.value === '' || a.value === null) {
      ElMessage.warning(`结论动作 ${i + 1}：值未填`)
      return false
    }
  }
  return true
}

async function onSubmit() {
  if (!validate()) return

  // 强制生成一次（即使 watch 未触发也保证最新）
  generateRuleText()

  save_loading.value = true
  try {
    const payload: RuleMethodCreatePayload = {
      rule_library_id: form.rule_library_id,
      rule_description: form.rule_description,
      rule_explanation: form.rule_explanation || undefined,
      polymer_abbreviation: form.polymer_abbreviation || undefined,
      product_category: form.product_category || undefined,
      priority: form.priority,
      confidence: form.confidence,
      source: form.source,
      is_active: form.is_active,
    }

    if (mode.value === 'new') {
      const res: any = await createRuleMethod(payload)
      if (res?.status === 0) {
        ElMessage.success('规则方法创建成功')
        const newId = res.data?.id
        if (props.embedded) {
          // drawer 嵌入模式：通知父组件保存成功
          emit('saved', newId ?? 0)
        } else if (newId) {
          // 独立路由模式：切换到 edit 模式，URL 带上 methodId
          router.replace(`/process/rules/${form.rule_library_id}/methods/${newId}/edit`)
        } else {
          goBack()
        }
      } else {
        ElMessage.error(res?.msg || '保存失败')
      }
    } else if (mode.value === 'edit') {
      const id = effectiveMethodId.value
      const res: any = await updateRuleMethod(id, payload)
      if (res?.status === 0) {
        ElMessage.success('规则方法更新成功')
        if (props.embedded) {
          // drawer 嵌入模式：通知父组件保存成功
          emit('saved', id)
        } else {
          // 独立路由模式：重新拉取以刷新快照
          await loadForm()
        }
      } else {
        ElMessage.error(res?.msg || '更新失败')
      }
    }
  } catch {
    // 拦截器已统一 toast + console
  } finally {
    save_loading.value = false
  }
}

// 导航

/** 返回上一级：drawer 嵌入模式 emit('close')，独立路由模式 router.push 回规则库列表 */
function goBack() {
  if (props.embedded) {
    emit('close')
  } else {
    router.push(`/process/rules/${effectiveLibraryId.value}`)
  }
}

/** form-actions 取消按钮的点击处理（仅独立路由模式有底部操作区） */
function onCancel() {
  goBack()
}

// 生命周期

onMounted(() => {
  loadForm()
})
</script>

<style lang="scss" scoped>
/* 容器遵守全局表单规范（padding 16 16 96），复用全局 .form-actions / .page-header */
.rule-method-form {
  padding: 16px 16px 96px;
  box-sizing: border-box;
}

/* drawer 嵌入模式：去掉 max-width 限制与底部 96px padding（drawer 自身提供滚动） */
.rule-method-form--embedded {
  max-width: none;
  margin: 0;
  padding: 16px 24px 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

/* ============ 左编辑区 + 右流程图 ============ */
.form-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.edit-area,
.graph-area {
  /* 1:1 左右布局（大屏 ≥ 1100px）：flex: 1 1 0 平分宽度（不用 flex-basis: 50%，否则右侧起始 50% 再 grow 会占 ~75%）；min-width: 0 防溢出；<1100px 改上下布局 */
  flex: 1 1 0;
  min-width: 0;
}

.edit-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.graph-area {
  /* 流程图保持右侧粘性定位（sticky）；卡片内按宽度切换列比：≥480px 为 2:1，360-480px 为 1:1，<360px 上下 1:1 */
  position: sticky;
  top: 16px;
}

/* ============ 条件/动作行 ============ */
.condition-block-list,
.action-block-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.condition-row,
.action-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

/* 行首连接词（IF / AND / THEN）：等宽字体 + 加粗 + 固定宽度，突出模糊规则结构 */
.row-prefix {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 50px;
  height: 24px;
  padding: 0 8px;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 12px;
  font-weight: 700;
  color: #409eff;
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 3px;
  white-space: nowrap;
  letter-spacing: 0.5px;
  flex: 0 0 auto;
}

/* 起点词（IF / THEN）：主题色背景，标识规则结构关键点 */
.row-prefix--start {
  color: #fff;
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

/* 行内按钮统一紧致 */
.row-action-btn {
  padding: 4px 8px;
  margin-left: auto;
}

/* 添加按钮容器：文字链风格，对齐 GatingSystemForm 规范 */
.add-button-wrapper {
  display: flex;
  justify-content: flex-start;
  margin: 12px 0 0;
}

/* 高亮闪烁（流程图节点点击触发） */
:deep(.highlight-flash) {
  background-color: #ecf5ff;
  animation: flash 2s ease-out;
}

@keyframes flash {
  0% {
    background-color: rgba(64, 158, 255, 0.2);
  }
  100% {
    background-color: transparent;
  }
}

/* ============ 响应式：< 1100px 改为上下布局，流程图置底 ============ */
@media (max-width: 1100px) {
  .form-body {
    flex-direction: column;
  }
  .edit-area,
  .graph-area {
    flex: 1 1 auto;
    width: 100%;
  }
  .graph-area {
    position: static; /* 取消 sticky，纵向布局不需要粘性 */
    order: 1; /* 流程图移到编辑区下方 */
  }
}
</style>