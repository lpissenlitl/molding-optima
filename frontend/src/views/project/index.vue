<!--
  项目管理 - 列表页
  - 搜索表单：复用 BaseSearchForm（与 mold 模块的 MoldSearchForm 风格统一）
  - 列表（编号、状态、来源、名称、关联模具、客户、行业、量产地、项目经理、创建日期）
  - 操作列：编辑、删除、新增关联模具
  - 新建项目（跳转 /project/new）
-->
<template>
  <div class="project-list">
    <!-- 搜索表单（配置驱动，复用 BaseSearchForm） -->
    <ProjectSearchForm
      :query-detail="query"
      :control-width="200"
      @search="onSearch"
      @reset="onReset"
    />

    <!-- 表格 -->
    <BaseTable
      :data="list_data.items"
      :total="list_data.total"
      :query="query"
      :columns.sync="table_columns"
      :loading="list_loading"
      :table-size.sync="table_size"
      :height-offset="260"
      view-name="project_list"
      :external-unique-values="externalUniqueValues"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="goEdit"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <!-- 顶部工具栏 -->
      <template #toolbar>
        <el-button type="primary" @click="goCreate">
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          新建项目
        </el-button>
        <el-button
          type="danger"
          :disabled="selected_rows.length === 0"
          @click="batchDelete"
        >
          <AppIcon icon="mdi:delete-outline" style="margin-right: 4px; font-size: 14px;" />
          批量删除
          <span v-if="selected_rows.length > 0" style="margin-left: 4px;">
            ({{ selected_rows.length }})
          </span>
        </el-button>
      </template>

      <!-- 项目编号列：可点击跳转编辑 -->
      <template #cell-project_code="{ row }">
        <el-link type="primary" @click="goEdit(row)">{{ row.project_code }}</el-link>
      </template>

      <!-- 状态列 -->
      <template #cell-status="{ row }">
        <el-tag v-if="row.status" :type="statusTagType(row.status)" size="small">
          {{ statusLabel(row.status) }}
        </el-tag>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 来源列 -->
      <template #cell-source="{ row }">
        <el-tag v-if="row.source" :type="sourceTagType(row.source)" size="small">
          {{ sourceLabel(row.source) }}
        </el-tag>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 关联模具列 -->
      <template #cell-mold_no="{ row }">
        <el-link v-if="row.mold_no" type="primary" @click="goMoldCreate(row)">
          {{ row.mold_no }}
        </el-link>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="goMoldCreate(row)">
                <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
                新增模具
              </el-button>
              <el-button type="text" @click="goEdit(row)">
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button type="text" class="text-danger" @click="deleteProject(row)">
                <AppIcon icon="mdi:delete-outline" style="margin-right: 4px; font-size: 14px;" />
                删除
              </el-button>
            </span>
          </template>
        </el-table-column>
      </template>
    </BaseTable>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import ProjectSearchForm from './components/ProjectSearchForm.vue'
import { projectMethod } from '@/api'
import {
  projectStatusOptions,
  projectSourceOptions,
} from '@/constants/project-const'

// ============================================================================
// 列表数据
// ============================================================================

interface ListData {
  total: number
  items: any[]
}

const router = useRouter()

const query = reactive({
  page_no: 1,
  page_size: 20,
  project_code: undefined as string | undefined,
  project_name: undefined as string | undefined,
  status: undefined as string | undefined,
  source: undefined as string | undefined,
  initiator: undefined as string | undefined,
  project_manager: undefined as string | undefined,
})

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const table_size = ref<'small' | 'default' | 'large'>('default')
const selected_rows = ref<any[]>([])

// 列定义
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '项目编号', prop: 'project_code', minWidth: 180, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: true, label: '项目状态', prop: 'status', minWidth: 110, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '项目来源', prop: 'source', minWidth: 110, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '项目名称', prop: 'project_name', minWidth: 200, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '关联模具', prop: 'mold_no', minWidth: 140, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '客户名称', prop: 'initiator', minWidth: 160, align: 'left', header_align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '应用行业', prop: 'application_industry', minWidth: 110, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '量产地', prop: 'manufacturing_location', minWidth: 130, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '项目经理', prop: 'project_manager', minWidth: 110, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '创建日期', prop: 'created_at', minWidth: 170, align: 'center', sortable: true, tooltip: true, filterable: false },
])

const externalUniqueValues = ref<Record<string, any[]>>({})

// ============================================================================
// 标签映射
// ============================================================================

function statusTagType(value: string): 'success' | 'info' | 'warning' | 'danger' {
  const map: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
    active: 'success',
    ongoing: 'success',
    completed: 'success',
    draft: 'info',
    suspended: 'warning',
  }
  return map[value] ?? 'info'
}

function statusLabel(value: string): string {
  return projectStatusOptions.find((o) => o.value === value)?.label ?? value ?? '—'
}

function sourceTagType(value: string): 'success' | 'info' | 'warning' | 'danger' {
  const map: Record<string, 'success' | 'info' | 'warning' | 'danger'> = {
    sync: 'warning',
    manual: 'info',
    import: 'success',
  }
  return map[value] ?? 'info'
}

function sourceLabel(value: string): string {
  return projectSourceOptions.find((o) => o.value === value)?.label ?? value ?? '—'
}

// ============================================================================
// API
// ============================================================================

async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await projectMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      project_code: query.project_code || undefined,
      project_name: query.project_name || undefined,
      status: query.status,
      source: query.source,
      initiator: query.initiator || undefined,
      project_manager: query.project_manager || undefined,
    } as any)
    if (res.status === 0) {
      list_data.value = res.data
      syncExternalUniqueValues()
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[ProjectList] fetchList failed:', err)
  } finally {
    list_loading.value = false
  }
}

function onSearch() {
  // BaseSearchForm @search 事件：搜索时回到第一页
  query.page_no = 1
  fetchList()
}

function onReset() {
  // BaseSearchForm 已经把 query 字段重置为 initial 值
  // 这里只需把 page_no 重置为 1 并刷新列表
  query.page_no = 1
  fetchList()
}

function syncExternalUniqueValues() {
  const items = list_data.value.items || []
  const collect = (prop: string) => {
    const set = new Set<any>()
    items.forEach((row: any) => {
      const v = row[prop]
      if (v !== null && v !== undefined) set.add(v)
    })
    return Array.from(set)
  }
  externalUniqueValues.value = {
    status: collect('status'),
    source: collect('source'),
    application_industry: collect('application_industry'),
  }
}

// ============================================================================
// 操作
// ============================================================================

function goCreate() {
  router.push('/project/new')
}

function goEdit(row: any) {
  router.push(`/project/${row.id}/edit`)
}

async function deleteProject(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除项目 "${row.project_code}" 吗？此操作不可恢复！`,
      '删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }
  try {
    const res: any = await projectMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[ProjectList] deleteProject failed:', err)
  }
}

async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${ids.length} 个项目吗？此操作不可恢复！`,
      '批量删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }
  try {
    const res: any = await projectMethod.multipleDelete({ ids })
    if (res.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 个项目`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[ProjectList] batchDelete failed:', err)
  }
}

function goMoldCreate(row: any) {
  // 跳转到模具创建页，带上 project_id 上下文
  router.push({ path: '/mold/create', query: { project_id: row.id } })
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.project-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 操作列按钮紧凑显示 */
.row-action-buttons {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;

  .el-button + .el-button {
    margin-left: 0;
  }
}

.text-danger {
  color: #f56c6c;
}
</style>
