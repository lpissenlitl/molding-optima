<!--
  RuleMethodSection.vue - 模糊规则 section（RuleMethod 列表 + CRUD）

  作为 RuleLibraryDetail 的子组件使用：
  - 接收 libraryId prop
  - 自包含：搜索、列表、分页、新建/编辑抽屉
  - 通过 emit('changed') 通知父组件刷新 method_count
-->
<template>
  <div ref="sectionRef" class="section-container">
    <!-- 搜索区 -->
    <div class="search-container">
    <el-form :inline="true" class="search-form">
      <el-form-item label="缺陷标识">
        <el-input
          v-model="methodQuery.defect_code"
          placeholder="搜索 defect_code"
          clearable
          style="width: 180px"
          @keyup.enter="loadMethods"
        />
      </el-form-item>
      <el-form-item label="状态">
        <el-select
          v-model="methodQuery.is_active"
          clearable
          placeholder="全部"
          style="width: 100px"
        >
          <el-option label="启用" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item class="search-actions">
        <el-button type="primary" @click="loadMethods">
          <AppIcon icon="mdi:magnify" :size="14" style="margin-right: 4px;" />
          搜索
        </el-button>
        <el-button @click="resetMethodQuery">
          <AppIcon icon="mdi:refresh" :size="14" style="margin-right: 4px;" />
          重置
        </el-button>
        <el-button type="success" @click="openCreateMethod">
          <AppIcon icon="mdi:plus" :size="14" style="margin-right: 4px;" />
          新建规则方法
        </el-button>
      </el-form-item>
    </el-form>
    </div>

    <!-- 表格 -->
    <div class="table-wrapper">
    <el-table
      v-loading="methodLoading"
      :data="methods"
      :height="tableHeight"
      border
      stripe
    >
    <!-- 序号列：每页从 1 开始 -->
    <el-table-column type="index" label="#" width="60" align="center" />
    <!-- 规则编号：业务标识 RM-{YYYYMM}-{NNNNN} -->
    <el-table-column label="规则编号" prop="rule_no" width="150" align="center">
      <template #default="{ row }">
        <span class="mono">{{ row.rule_no || '—' }}</span>
      </template>
    </el-table-column>
    <!-- 规则描述：tooltip 透出 rule_explanation -->
    <el-table-column label="规则描述" min-width="240">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.rule_explanation"
          :content="row.rule_explanation"
          placement="top"
          :show-after="200"
        >
          <span class="cell-text cell-text--truncate">{{ row.rule_description }}</span>
        </el-tooltip>
        <span v-else class="cell-text cell-text--truncate">{{ row.rule_description }}</span>
      </template>
    </el-table-column>
    <el-table-column label="缺陷标识" prop="defect_code" width="120">
      <template #default="{ row }">
        <span class="mono">{{ row.defect_code || '—' }}</span>
      </template>
    </el-table-column>
    <el-table-column label="缺陷名称" prop="defect_label" width="120" show-overflow-tooltip />
    <el-table-column label="材料" prop="polymer_abbreviation" width="100" show-overflow-tooltip />
    <!-- 产品类别 -->
    <el-table-column label="产品类别" prop="product_category" width="120" show-overflow-tooltip>
      <template #default="{ row }">
        {{ row.product_category || '不限' }}
      </template>
    </el-table-column>
    <!-- 状态：高频筛选维度，提到“优先级”之前，提升扫表焦点 -->
    <el-table-column label="状态" prop="is_active" width="80" align="center">
      <template #default="{ row }">
        <el-tag :type="row.is_active ? 'success' : 'info'">
          {{ row.is_active ? '启用' : '禁用' }}
        </el-tag>
      </template>
    </el-table-column>
    <el-table-column label="优先级" prop="priority" width="80" align="center" />
    <el-table-column label="置信度" prop="confidence" width="80" align="center">
      <template #default="{ row }">
        {{ Number(row.confidence).toFixed(2) }}
      </template>
    </el-table-column>
    <el-table-column label="来源" prop="source" width="100">
      <template #default="{ row }">
        <el-tag>{{ sourceLabel(row.source) }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="180" fixed="right" align="center">
      <template #default="{ row }">
        <el-button link type="primary" @click="openEditMethod(row)">编辑</el-button>
        <el-button link type="danger" @click="deleteMethod(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
    </div>

    <!-- 分页 -->
    <el-pagination
      class="pagination"
      background
      layout="total, sizes, prev, pager, next, jumper"
      :current-page="methodQuery.page_no"
      :page-size="methodQuery.page_size"
      :page-sizes="[10, 20, 50, 100]"
      :total="methodTotal"
      @current-change="onMethodPageChange"
      @size-change="onMethodSizeChange"
    />
  </div>

  <!--
    规则方法抽屉（新建/编辑共用）
    size=80% 以容纳结构化编辑 + 流程图预览
    drawer 标题由 RuleMethodSection 控制，表单内容由 RuleMethodForm 组件负责
  -->
  <el-drawer
    v-model="methodDialogVisible"
    :title="dialogMode === 'create' ? '新建规则方法' : '编辑规则方法'"
    direction="rtl"
    size="90%"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <RuleMethodForm
      v-if="methodDialogVisible"
      :library-id="props.libraryId"
      :method-id="editingMethodId"
      :show-page-header="false"
      :show-form-actions="true"
      :embedded="true"
      @close="onFormClose"
      @saved="onFormSaved"
    />
  </el-drawer>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
// AppIcon 是 ComponentsPlugin 全局注册的组件，无需 import
import RuleMethodForm from '@/views/process/rule/pages/RuleMethodForm.vue'
import {
  listRuleMethods,
  deleteRuleMethod as apiDeleteRuleMethod,
} from '@/api/rule'
import type { RuleMethod, RuleSource } from '@/types/rule'

// ============================================================================
// Props / Emits
// ============================================================================

const props = defineProps<{
  libraryId: number
}>()

const emit = defineEmits<{
  /** CRUD 后通知父组件刷新 method_count */
  changed: []
}>()

// ============================================================================
// 列表状态
// ============================================================================

const methods = ref<RuleMethod[]>([])
const methodTotal = ref(0)
const methodLoading = ref(false)
const methodQuery = reactive({
  defect_code: '',
  is_active: undefined as boolean | undefined,
  page_no: 1,
  page_size: 10,
})

async function loadMethods() {
  methodLoading.value = true
  try {
    const res: any = await listRuleMethods(props.libraryId, {
      page_no: methodQuery.page_no,
      page_size: methodQuery.page_size,
      defect_code: methodQuery.defect_code || undefined,
      is_active: methodQuery.is_active,
    })
    methods.value = res.data?.items || res.items || []
    methodTotal.value = res.data?.total ?? res.total ?? 0
  } catch {
    methods.value = []
    methodTotal.value = 0
  } finally {
    methodLoading.value = false
  }
}

function resetMethodQuery() {
  methodQuery.defect_code = ''
  methodQuery.is_active = undefined
  methodQuery.page_no = 1
  loadMethods()
}

function onMethodPageChange(p: number) {
  methodQuery.page_no = p
  loadMethods()
}

/** 切换每页大小：回到第 1 页后重新加载，避免跨页错位 */
function onMethodSizeChange(s: number) {
  methodQuery.page_size = s
  methodQuery.page_no = 1
  loadMethods()
}

// ============================================================================
// 来源标签
// ============================================================================

const SOURCE_LABELS: Record<RuleSource, string> = {
  expert: '专家经验',
  rule_miner: '规则挖掘',
  llm: '大模型生成',
}
function sourceLabel(s: string) {
  return SOURCE_LABELS[s as RuleSource] || s
}

// ============================================================================
// 抽屉（新建/编辑共用，80% 宽度，内嵌 RuleMethodForm 组件）
// ============================================================================

const methodDialogVisible = ref(false)
const editingMethodId = ref<number | undefined>(undefined)
const dialogMode = ref<'create' | 'edit'>('create')

function openCreateMethod() {
  dialogMode.value = 'create'
  editingMethodId.value = undefined
  methodDialogVisible.value = true
}

function openEditMethod(row: RuleMethod) {
  dialogMode.value = 'edit'
  editingMethodId.value = row.id
  methodDialogVisible.value = true
}

/** RuleMethodForm 发出 close 事件——关闭抽屉 */
function onFormClose() {
  methodDialogVisible.value = false
}

/** RuleMethodForm 发出 saved 事件——关闭抽屉 + 刷新列表 */
async function onFormSaved(_methodId: number) {
  methodDialogVisible.value = false
  await loadMethods()
  // 通知父组件刷新 method_count
  emit('changed')
}

async function deleteMethod(row: RuleMethod) {
  try {
    await ElMessageBox.confirm(
      `确认删除规则方法？\n${row.rule_description}`,
      '删除规则方法',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await apiDeleteRuleMethod(row.id)
    ElMessage.success('删除成功')
    loadMethods()
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
    tableHeight.value = Math.max(300, wrapper.clientHeight)
  }
}

onMounted(async () => {
  await nextTick()
  calcTableHeight()
  window.addEventListener('resize', calcTableHeight)
  if (props.libraryId) {
    loadMethods()
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

/* 表格单元格文本：单行截断，配合 el-tooltip 使用 */
.cell-text {
  display: inline-block;
  max-width: 100%;
  vertical-align: middle;
}

.cell-text--truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>