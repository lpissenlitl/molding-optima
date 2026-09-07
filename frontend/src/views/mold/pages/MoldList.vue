<!--
  MoldList - 模具列表页

  设计要点：
  - 表格使用 BaseTable（统一列定义、密度切换、列筛选、用户偏好持久化）
  - 编辑/新建：路由跳转（与 ProjectList 风格一致）—— mold form 字段较多，独立页面空间更充足
  - 跨模块链接：moldflow / trial / reservation / resume（通过路由跳转）
  - 操作列：编辑（review_mold）、删除（delete_mold）
  - 表格偏好（列显隐、密度、pageSize）通过 view-name="mold_list" 自动持久化

  与 project/pages/ProjectList.vue 的差异：
  - 跨模块入口多出 moldflow / trial / resume
-->
<template>
  <div class="mold-list">
    <!-- 搜索表单 -->
    <MoldSearchForm
      :query-detail="query"
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
      :height-offset="220"
      view-name="mold_list"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="goEdit"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <!-- 顶部工具栏 -->
      <template #toolbar>
        <el-button
          type="primary"
          :disabled="!hasPermission('add_mold')"
          @click="goCreate"
        >
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          新建模具
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

      <!-- 模具编号列：可点击跳编辑 -->
      <template #cell-mold_no="{ row }">
        <el-link
          v-if="row.mold_no"
          type="primary"
          @click="goEdit(row)"
          :disabled="!hasPermission('review_mold')"
        >
          {{ row.mold_no }}
        </el-link>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 预约列：button 触发跨模块路由 -->
      <template #cell-reservation="{ row }">
        <el-button
          v-if="row.id"
          type="primary"
          size="small"
          round
          @click="goReservation(row)"
          :disabled="!hasPermission('add_reservation')"
        >
          预约
        </el-button>
      </template>

      <!-- 模流数据列 -->
      <template #cell-moldflow_data="{ row }">
        <el-link
          v-if="row.id"
          type="primary"
          @click="goMoldflow(row)"
          :disabled="!hasPermission('review_moldflow')"
        >
          查看
        </el-link>
      </template>

      <!-- 试模数据列 -->
      <template #cell-trial_data="{ row }">
        <el-link
          v-if="row.id"
          type="primary"
          @click="goTrialData(row)"
          :disabled="!hasPermission('trial_view')"
        >
          查看
        </el-link>
      </template>

      <!-- 试模履历列 -->
      <template #cell-trial_resume="{ row }">
        <el-link
          v-if="row.id"
          type="primary"
          @click="goTrialResume(row)"
          :disabled="!hasPermission('review_trial_resume')"
        >
          查看
        </el-link>
      </template>

      <!-- 问题履历列 -->
      <template #cell-issue_resume="{ row }">
        <el-link
          v-if="row.id"
          type="primary"
          @click="goIssueResume(row)"
          :disabled="!hasPermission('review_problem_resume')"
        >
          查看
        </el-link>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button
                type="text"
                @click="goEdit(row)"
                :disabled="!hasPermission('review_mold')"
              >
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button
                type="text"
                class="text-danger"
                @click="deleteMold(row)"
                :disabled="!hasPermission('delete_mold')"
              >
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
/**
 * MoldList 数据流：
 * - 编辑/新建：router.push('/mold/new') 或 router.push('/mold/:id/edit')
 *   MoldForm 自身处理详情加载、保存提交、保存后 router.push('/mold/list') 返回
 *   列表通过 activated / onMounted 自动重新拉取（若需要可监听 $route）
 * - 列表字段顺序 / 列显隐 / 密度 / pageSize 通过 view-name="mold_list" 自动持久化
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { hasPermission } from '@/utils/permission'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import MoldSearchForm from '../components/MoldSearchForm.vue'
import { moldMethod } from '@/api'

// ============================================================================
// 类型
// ============================================================================

interface ListData {
  total: number
  items: any[]
}

// ============================================================================
// 状态
// ============================================================================

const router = useRouter()

// 查询参数（与 MoldSearchForm 的 queryDetail 字段保持一致）
const query = reactive({
  page_no: 1,
  page_size: 20,
  mold_no: undefined as string | undefined,
  mold_name: undefined as string | undefined,
  category: undefined as string | undefined,
  structure: undefined as string | undefined,
  cavity_layout: undefined as string | undefined,
  manufacturing_method: undefined as string | undefined,
})

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const table_size = ref<'small' | 'default' | 'large'>('default')
const selected_rows = ref<any[]>([])

// 列定义
// - visible: true  → 默认显示
// - visible: false → 默认隐藏（高级列，用户可手动打开列筛选启用）
// - filterable: true → 启用 BaseTable 列筛选（漏斗）
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '模具编号', prop: 'mold_no', minWidth: 120, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: true, label: '模具名称', prop: 'mold_name', minWidth: 200, align: 'left', header_align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '模具类别', prop: 'category', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '制作方式', prop: 'manufacturing_method', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '试模约机', prop: 'reservation', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '模流数据', prop: 'moldflow_data', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '试模数据', prop: 'trial_data', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '试模履历', prop: 'trial_resume', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '问题履历', prop: 'issue_resume', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '模具结构', prop: 'structure', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '模腔布局', prop: 'cavity_layout', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '产品大类', prop: 'product_category', minWidth: 120, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '产品小类', prop: 'product_model', minWidth: 120, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '注塑周期[s]', prop: 'target_cycle_time', minWidth: 120, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: true, label: '推荐吨位[Ton]', prop: 'recommended_tonnage', minWidth: 150, align: 'center', sortable: true, tooltip: false, filterable: false },
  // 尺寸列（默认隐藏）
  { visible: false, label: '模具长度[mm]', prop: 'mold_length', minWidth: 120, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: false, label: '模具宽度[mm]', prop: 'mold_width', minWidth: 120, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: false, label: '模具厚度[mm]', prop: 'mold_thickness', minWidth: 120, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: false, label: '模具重量[kg]', prop: 'mold_weight', minWidth: 120, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: true, label: '创建日期', prop: 'created_at', minWidth: 170, align: 'center', sortable: true, tooltip: true, filterable: false },
])

// 抽屉控制已移除：编辑/新建走路由跳转（/mold/new 与 /mold/:id/edit）

// ============================================================================
// 数据加载
// ============================================================================

async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await moldMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      mold_no: query.mold_no || undefined,
      mold_name: query.mold_name || undefined,
      category: query.category,
      structure: query.structure,
      cavity_layout: query.cavity_layout || undefined,
      manufacturing_method: query.manufacturing_method || undefined,
    } as any)
    if (res.status === 0) {
      list_data.value = res.data
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[MoldList] fetchList failed:', err)
  } finally {
    list_loading.value = false
  }
}

function onSearch() {
  query.page_no = 1
  fetchList()
}

function onReset() {
  query.page_no = 1
  fetchList()
}

// ============================================================================
// 操作
// ============================================================================

function goCreate() {
  router.push('/mold/new')
}

function goEdit(row: any) {
  router.push(`/mold/${row.id}/edit`)
}

async function deleteMold(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认删除以下模具信息？\n${row.mold_no}`,
      '删除模具',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    const res: any = await moldMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[MoldList] deleteMold failed:', err)
  }
}

async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${ids.length} 个模具吗？此操作不可恢复！`,
      '批量删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }
  try {
    const res: any = await moldMethod.multipleDelete({ ids })
    if (res.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 个模具`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[MoldList] batchDelete failed:', err)
  }
}

// 跨模块链接（保留 mold 现状的所有跨模块入口）
function goReservation(row: any) {
  router.push({ path: '/schedule/reservation/create', query: { mold_id: row.id } })
}
function goMoldflow(row: any) {
  router.push({
    path: '/mold/moldflow/report',
    query: { mold_id: row.id, mold_no: row.mold_no, category: row.category },
  })
}
function goTrialData(row: any) {
  router.push({ path: '/mold-trial/workflow', query: { mold_id: row.id } })
}
function goTrialResume(row: any) {
  router.push({ path: '/mold/resume/trial', query: { mold_id: row.id } })
}
function goIssueResume(row: any) {
  router.push({ path: '/mold/resume/issue', query: { mold_id: row.id } })
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.mold-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 操作列按钮紧凑显示（与 project/index.vue 一致） */
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