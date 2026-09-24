<!--
  ExpertRuleSection.vue - 专家规则 section（ExpertRule 列表 + CRUD）

  作为 RuleLibraryDetail 的子组件使用：
  - 接收 libraryId prop
  - 自包含：搜索、列表、分页、新建/编辑抽屉（含 JSON 实时校验）
  - 通过 emit('changed') 通知父组件刷新 expert_rule_count

  注意：专家规则属于平台级内部规则，仅 superadmin 可见。
  后端 ExpertRuleListByLibraryView / ExpertRuleDetailView 已加 require_superuser 装饰器做二次防护。
-->
<template>
  <div ref="sectionRef" class="section-container">
    <!-- 搜索区 -->
    <div class="search-container">
    <el-form :inline="true" class="search-form">
      <el-form-item label="规则编码">
        <el-input
          v-model="expertQuery.rule_code"
          placeholder="搜索 rule_code"
          clearable
          style="width: 180px"
          @keyup.enter="loadExpertRules"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select
          v-model="expertQuery.is_active"
          clearable
          placeholder="全部"
          style="width: 100px"
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item class="search-actions">
        <el-button type="primary" @click="loadExpertRules">
          <AppIcon icon="mdi:magnify" :size="14" style="margin-right: 4px;" />
          搜索
        </el-button>
        <el-button @click="resetExpertQuery">
          <AppIcon icon="mdi:refresh" :size="14" style="margin-right: 4px;" />
          重置
        </el-button>
        <el-button type="success" @click="showCreateExpertRuleDialog">
          <AppIcon icon="mdi:plus" :size="14" style="margin-right: 4px;" />
          新建专家规则
        </el-button>
      </el-form-item>
    </el-form>
    </div>

    <!-- 表格 -->
    <div class="table-wrapper">
    <el-table
      v-loading="expertLoading"
      :data="expertRules"
      :height="tableHeight"
      border
      stripe
    >
    <!-- 序号列：每页从 1 开始 -->
    <el-table-column type="index" label="#" width="60" align="center" />
    <el-table-column label="规则编码" prop="rule_code" width="240">
      <template #default="{ row }">
        <span class="mono">{{ row.rule_code }}</span>
      </template>
    </el-table-column>
    <el-table-column label="规则名称" prop="rule_name" min-width="300" show-overflow-tooltip />
    <el-table-column label="匹配条件" width="180" align="center">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.conditions && row.conditions.length > 0"
          :content="conditionsSummary(row.conditions)"
          placement="top"
          :show-after="200"
        >
          <el-tag>{{ row.conditions.length }} 项</el-tag>
        </el-tooltip>
        <el-tag v-else type="info">默认</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="系数" width="100" align="center">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.coefficients && Object.keys(row.coefficients).length > 0"
          :content="JSON.stringify(row.coefficients, null, 2)"
          placement="top"
          :show-after="200"
          raw-content
        >
          <el-tag>{{ Object.keys(row.coefficients).length }} 项</el-tag>
        </el-tooltip>
        <el-tag v-else type="info">默认</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="优先级" prop="priority" width="80" align="center" />
    <el-table-column label="状态" prop="is_active" width="80" align="center">
      <template #default="{ row }">
        <el-tag :type="row.is_active ? 'success' : 'info'">
          {{ row.is_active ? '启用' : '禁用' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="160" fixed="right" align="center">
      <template #default="{ row }">
        <el-button link type="primary" @click="showEditExpertRuleDialog(row)">编辑</el-button>
        <el-button link type="danger" @click="deleteExpertRule(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
    </div>

    <!-- 分页 -->
    <el-pagination
      class="pagination"
      background
      layout="total, sizes, prev, pager, next, jumper"
      :current-page="expertQuery.page_no"
      :page-size="expertQuery.page_size"
      :page-sizes="[10, 20, 50, 100]"
      :total="expertTotal"
      @current-change="onExpertPageChange"
      @size-change="onExpertSizeChange"
    />
  </div>

  <!-- 专家规则抽屉（新建/编辑共用）-->
  <el-drawer
    v-model="expertDialogVisible"
    :title="expertDialogMode === 'create' ? '新建专家规则' : '编辑专家规则'"
    direction="rtl"
    size="640px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <el-form :model="expertForm" label-width="100px">
      <el-form-item label="规则编码" required>
        <el-input v-model="expertForm.rule_code" placeholder="英文编码，如 default_injection" />
      </el-form-item>
      <el-form-item label="规则名称" required>
        <el-input v-model="expertForm.rule_name" placeholder="中文名称" />
      </el-form-item>
      <el-form-item label="匹配条件">
        <div class="hint">JSON 数组（每项含 field/operator/value），留空 = 默认规则</div>
        <el-input
          v-model="expertForm.conditionsText"
          type="textarea"
          class="json-input"
          :autosize="{ minRows: 6, maxRows: 16 }"
          placeholder='[{"field":"polymer.abbreviation","operator":"exact","value":"ABS"}]'
          @blur="formatJson('conditionsText')"
        />
        <div
          v-if="jsonStatus.conditions"
          class="field-tip json-status"
          :class="jsonStatus.conditions.startsWith('✓') ? 'is-ok' : 'is-error'"
        >
          {{ jsonStatus.conditions }}
        </div>
      </el-form-item>
      <el-form-item label="覆盖系数">
        <div class="hint">JSON 对象，与内置默认值深度合并</div>
        <el-input
          v-model="expertForm.coefficientsText"
          type="textarea"
          class="json-input"
          :autosize="{ minRows: 6, maxRows: 16 }"
          placeholder='{"holding":{"hold_pres_inj_ratio_max":0.85}}'
          @blur="formatJson('coefficientsText')"
        />
        <div
          v-if="jsonStatus.coefficients"
          class="field-tip json-status"
          :class="jsonStatus.coefficients.startsWith('✓') ? 'is-ok' : 'is-error'"
        >
          {{ jsonStatus.coefficients }}
        </div>
      </el-form-item>
      <el-form-item label="优先级">
        <el-input-number v-model="expertForm.priority" :min="0" />
      </el-form-item>
      <el-form-item label="启用">
        <el-switch v-model="expertForm.is_active" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="expertDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="expertSubmitting" @click="submitExpertRule">
        保存
      </el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// AppIcon 是 ComponentsPlugin 全局注册的组件，无需 import
import {
  listExpertRules,
  createExpertRule,
  updateExpertRule as apiUpdateExpertRule,
  deleteExpertRule as apiDeleteExpertRule,
} from '@/api/rule'
import type { ExpertRule } from '@/types/rule'

// ============================================================================
// Props / Emits
// ============================================================================

const props = defineProps<{
  libraryId: number
  /** 是否超管理员。后端已有 require_superuser 二次防护，此处预留未来前端控制位 */
  isSuperuser?: boolean
}>()

const emit = defineEmits<{
  /** CRUD 后通知父组件刷新 expert_rule_count */
  changed: []
}>()

// ============================================================================
// 列表状态
// ============================================================================

const expertRules = ref<ExpertRule[]>([])
const expertTotal = ref(0)
const expertLoading = ref(false)
const expertQuery = reactive({
  rule_code: '',
  is_active: undefined as boolean | undefined,
  page_no: 1,
  page_size: 10,
})

async function loadExpertRules() {
  expertLoading.value = true
  try {
    const res: any = await listExpertRules(props.libraryId, {
      page_no: expertQuery.page_no,
      page_size: expertQuery.page_size,
      rule_code: expertQuery.rule_code || undefined,
      is_active: expertQuery.is_active,
    })
    expertRules.value = res.data?.items || res.items || []
    expertTotal.value = res.data?.total ?? res.total ?? 0
  } catch {
    expertRules.value = []
    expertTotal.value = 0
  } finally {
    expertLoading.value = false
  }
}

function resetExpertQuery() {
  expertQuery.rule_code = ''
  expertQuery.is_active = undefined
  expertQuery.page_no = 1
  loadExpertRules()
}

function onExpertPageChange(p: number) {
  expertQuery.page_no = p
  loadExpertRules()
}

/** 切换每页大小：回到第 1 页后重新加载，避免跨页错位 */
function onExpertSizeChange(s: number) {
  expertQuery.page_size = s
  expertQuery.page_no = 1
  loadExpertRules()
}

/**
 * 匹配条件摘要：取前 2 条条件拼成可读字符串，作为 tooltip 内容
 * 例: "polymer.abbreviation exact \"ABS\"\nmolder.brand exact \"海天\""
 */
function conditionsSummary(conditions: ExpertRule['conditions']): string {
  if (!conditions || conditions.length === 0) return '默认规则（无条件）'
  const formatValue = (v: unknown) =>
    typeof v === 'string' ? v : JSON.stringify(v)
  const preview = conditions.slice(0, 2).map(c =>
    `${c.field} ${c.operator} ${formatValue(c.value)}`,
  )
  if (conditions.length > 2) {
    return preview.join('\n') + `\n... 还有 ${conditions.length - 2} 条`
  }
  return preview.join('\n')
}

// ============================================================================
// 抽屉（新建/编辑共用）+ JSON 实时校验
// ============================================================================

const expertDialogVisible = ref(false)
const expertDialogMode = ref<'create' | 'edit'>('create')
const expertEditId = ref<number>(0)
const expertSubmitting = ref(false)
const expertForm = reactive({
  rule_code: '',
  rule_name: '',
  conditionsText: '',
  coefficientsText: '',
  priority: 100,
  is_active: true,
})

// JSON 校验状态（与上述 fieldsText 字段一一对应）
const jsonStatus = reactive<{ conditions: string; coefficients: string }>({
  conditions: '',
  coefficients: '',
})

/**
 * 自动格式化 JSON + 实时校验提示
 * - 输入框失焦时调用：成功则 JSON.stringify(parsed, null, 2)，失败则仅提示错误不动数据
 */
function formatJson(field: 'conditionsText' | 'coefficientsText') {
  const text = expertForm[field].trim()
  const key = field === 'conditionsText' ? 'conditions' : 'coefficients'
  if (!text) {
    jsonStatus[key] = ''
    return
  }
  try {
    const parsed = JSON.parse(text)
    expertForm[field] = JSON.stringify(parsed, null, 2)
    jsonStatus[key] = '✓ 格式正确'
  } catch (e: any) {
    jsonStatus[key] = `✗ ${e.message}`
  }
}

function showCreateExpertRuleDialog() {
  expertDialogMode.value = 'create'
  expertEditId.value = 0
  expertForm.rule_code = ''
  expertForm.rule_name = ''
  expertForm.conditionsText = ''
  expertForm.coefficientsText = ''
  expertForm.priority = 100
  expertForm.is_active = true
  jsonStatus.conditions = ''
  jsonStatus.coefficients = ''
  expertDialogVisible.value = true
}

function showEditExpertRuleDialog(row: ExpertRule) {
  expertDialogMode.value = 'edit'
  expertEditId.value = row.id
  expertForm.rule_code = row.rule_code
  expertForm.rule_name = row.rule_name
  expertForm.conditionsText = row.conditions ? JSON.stringify(row.conditions, null, 2) : '[]'
  expertForm.coefficientsText = row.coefficients ? JSON.stringify(row.coefficients, null, 2) : '{}'
  expertForm.priority = row.priority
  expertForm.is_active = row.is_active
  jsonStatus.conditions = '✓ 格式正确'
  jsonStatus.coefficients = '✓ 格式正确'
  expertDialogVisible.value = true
}

async function submitExpertRule() {
  if (!expertForm.rule_code || !expertForm.rule_name) {
    ElMessage.warning('请填写规则编码和规则名称')
    return
  }
  // 校验 JSON
  let conditions: any[] = []
  let coefficients: Record<string, any> = {}
  if (expertForm.conditionsText.trim()) {
    try {
      const parsed = JSON.parse(expertForm.conditionsText)
      if (!Array.isArray(parsed)) {
        ElMessage.warning('匹配条件必须是 JSON 数组')
        return
      }
      conditions = parsed
    } catch {
      ElMessage.warning('匹配条件 JSON 格式错误')
      return
    }
  }
  if (expertForm.coefficientsText.trim()) {
    try {
      const parsed = JSON.parse(expertForm.coefficientsText)
      if (typeof parsed !== 'object' || Array.isArray(parsed)) {
        ElMessage.warning('覆盖系数必须是 JSON 对象')
        return
      }
      coefficients = parsed
    } catch {
      ElMessage.warning('覆盖系数 JSON 格式错误')
      return
    }
  }
  expertSubmitting.value = true
  try {
    if (expertDialogMode.value === 'create') {
      await createExpertRule({
        rule_library_id: props.libraryId,
        rule_code: expertForm.rule_code,
        rule_name: expertForm.rule_name,
        conditions,
        coefficients,
        priority: expertForm.priority,
        is_active: expertForm.is_active,
      })
      ElMessage.success('专家规则创建成功')
    } else {
      await apiUpdateExpertRule(expertEditId.value, {
        rule_code: expertForm.rule_code,
        rule_name: expertForm.rule_name,
        conditions,
        coefficients,
        priority: expertForm.priority,
        is_active: expertForm.is_active,
      })
      ElMessage.success('专家规则更新成功')
    }
    expertDialogVisible.value = false
    loadExpertRules()
    // 通知父组件刷新 expert_rule_count
    emit('changed')
  } catch {
    /* 拦截器已提示 */
  } finally {
    expertSubmitting.value = false
  }
}

async function deleteExpertRule(row: ExpertRule) {
  try {
    await ElMessageBox.confirm(
      `确认删除专家规则？\n${row.rule_code}（${row.rule_name}）`,
      '删除专家规则',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await apiDeleteExpertRule(row.id)
    ElMessage.success('删除成功')
    loadExpertRules()
    emit('changed')
  } catch {
    /* 拦截器已提示 */
  }
}

// ============================================================================
// 初始化：进入页面立即加载一次 + 动态计算表格高度
// ============================================================================

/**
 * 表格高度 = .table-wrapper 的真实 clientHeight（flex 容器已分配的空间）
 * - 不依赖 window.innerHeight 估算（避免顶部导航/库信息卡高度变动造成偏移）
 * - 首次 onMounted 后 flex 已完成布局，clientHeight 已是准确值
 * - resize 时 flex 重分配 → 高度同步更新
 */
const sectionRef = ref<HTMLElement | null>(null)
const tableHeight = ref<number>(400)

function calcTableHeight() {
  if (!sectionRef.value) return
  const wrapper = sectionRef.value.querySelector('.table-wrapper') as HTMLElement | null
  if (wrapper) {
    // 下界 300 保证小视窗下表格可用，下界不是上限，不会被压扁
    tableHeight.value = Math.max(300, wrapper.clientHeight)
  }
}

onMounted(async () => {
  // nextTick 保证 flex 布局完成，clientHeight 是最终值
  await nextTick()
  calcTableHeight()
  window.addEventListener('resize', calcTableHeight)
  if (props.libraryId) {
    loadExpertRules()
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', calcTableHeight)
})
</script>

<style scoped>
/*
 * Flex 布局：
 * - .section-container 是外层 flex 容器（垂直排列）
 * - .search-container / .pagination flex-shrink: 0 → 不被压衡
 * - .table-wrapper flex: 1 + min-height: 0 → 吃掉所有剩余空间
 *   min-height: 0 关键：flex 子项默认 min-height: auto，会被内容撑开
 *   设为 0 后子项可以收缩，让 .table-wrapper 高度 = flex 分配的空间
 */
.section-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.search-container {
  flex-shrink: 0;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
}

.pagination {
  display: flex;
  justify-content: flex-start;
  margin-top: 16px;
  flex-shrink: 0;
}

.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}

.cell-coeffs {
  font-family: 'Courier New', Consolas, monospace;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
  display: inline-block;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

/* JSON 输入框：等宽字体 + 合适字号，便于阅读 */
.json-input :deep(.el-textarea__inner) {
  font-family: 'JetBrains Mono', 'Courier New', Consolas, monospace;
  font-size: 13px;
  line-height: 1.6;
  tab-size: 2;
}

/* JSON 校验状态：复用 .field-tip 样式，额外加颜色区分 */
.json-status {
  margin-top: 4px;
  font-family: 'JetBrains Mono', Consolas, monospace;
}
.json-status.is-ok {
  color: var(--el-color-success, #67c23a);
}
.json-status.is-error {
  color: var(--el-color-danger, #f56c6c);
}
</style>