<!--
  ProcessParameterList - 工艺参数列表页

  路由：/process/parameter（菜单"工艺参数"）
  数据源：后端 ProcessCondition 表（一次试模的完整上下文：模具/机器/材料/工艺参数）。
  业务说明：
    ProcessCondition 是"试模上下文"的通用载体，不同业务视图（参数/优化/调机）
    都基于该载体展示不同视角。这里展示的是"工艺参数"视角。

  架构（2026-09-11 重写）：
    - 搜索：ProcessSearchForm（Vue 3 setup + BaseSearchForm）
    - 列表：BaseTable 组件（接管 el-table + el-pagination + 列筛选 + 偏好持久化）
    - 列定义：12 列，含状态/起源/模具/产品/机台/材料/创建时间等
    - 顶部 toolbar：新建工艺、批量删除、导出
    - 行操作：编辑 / 删除
    - 跨模块入口：调整记录（占位，后续接入）
-->
<template>
  <div class="process-condition-list">
    <!-- 搜索表单 -->
    <ProcessSearchForm
      :query-detail="query"
      @search="onSearch"
      @reset="onReset"
    />

    <!-- 列表 -->
    <BaseTable
      :data="list_data.items"
      :total="list_data.total"
      :query="query"
      :columns.sync="table_columns"
      :loading="list_loading"
      :table-size.sync="table_size"
      :height-offset="220"
      view-name="process_parameter_list"
      :show-selection="true"
      :show-index="true"
      :stripe="true"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="goEdit"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <template #toolbar>
        <el-button type="primary" @click="goCreate">
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          新建工艺
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

      <!-- 工艺条件编号列：可点击跳编辑 -->
      <template #cell-condition_no="{ row }">
        <el-link
          v-if="row.condition_no"
          type="primary"
          @click="goEdit(row)"
        >
          {{ row.condition_no }}
        </el-link>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 状态列：标签式渲染 -->
      <template #cell-status="{ row }">
        <el-tag
          v-if="row.status"
          :type="row.status === 'active' ? 'success' : 'info'"
          size="small"
        >
          {{ statusLabel(row.status) }}
        </el-tag>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 起源类型列：标签式渲染 -->
      <template #cell-origin_type="{ row }">
        <span v-if="row.origin_type">{{ originLabel(row.origin_type) }}</span>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="goEdit(row)">
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button type="text" class="text-danger" @click="deleteOne(row)">
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
 * 工艺条件列表数据流：
 * - 编辑/新建：路由跳转（/process/parameter/new、/process/parameter/:id/edit）
 * - 列表字段顺序/列显隐/密度/pageSize 通过 view-name="process_condition_list" 持久化
 * - 列表查询走 processParameterMethod（BaseRequest 实例），URL = /api/processes/parameter/
 *
 * 后端响应结构（main_service.get_process_parameter_list）：
 *   {
 *     id, condition_no, status, origin_type,
 *     mold_no, mold_name, mold_type, cavity_layout, product_category,
 *     machine_brand, machine_model, machine_device_code,
 *     polymer_abbreviation, polymer_grade,
 *     shot_index, injection_index,
 *     created_at, updated_at
 *   }
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import ProcessSearchForm from '../components/ProcessSearchForm.vue'
import { processParameterMethod, processParameterBatchDelete } from '@/api'

// ============================================================================
// 类型
// ============================================================================

interface ListData {
  total: number
  items: any[]
}

// ============================================================================
// 路由
// ============================================================================

const router = useRouter()

// ============================================================================
// 状态
// ============================================================================

const query = reactive({
  page_no: 1,
  page_size: 20,
  status: null as string | null,
  origin_type: null as string | null,
  mold_no: null as string | null,
  machine_model: null as string | null,
  polymer_abbreviation: null as string | null,
  start_date: null as string | null,
  end_date: null as string | null,
})

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const table_size = ref<'small' | 'default' | 'large'>('default')
const selected_rows = ref<any[]>([])

// ============================================================================
// 列定义
// ============================================================================

const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '工艺编号', prop: 'condition_no', minWidth: 160, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '状态', prop: 'status', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '起源', prop: 'origin_type', minWidth: 110, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '模具编号', prop: 'mold_no', minWidth: 140, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '模具名称', prop: 'mold_name', minWidth: 180, align: 'left', header_align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '产品大类', prop: 'product_category', minWidth: 120, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '设备品牌', prop: 'machine_brand', minWidth: 110, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '设备型号', prop: 'machine_model', minWidth: 150, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '设备编号', prop: 'machine_device_code', minWidth: 140, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '塑料简称', prop: 'polymer_abbreviation', minWidth: 110, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '塑料牌号', prop: 'polymer_grade', minWidth: 150, align: 'left', header_align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '创建时间', prop: 'created_at', minWidth: 170, align: 'center', sortable: true, tooltip: true, filterable: false },
])

// ============================================================================
// 标签转换
// ============================================================================

const STATUS_MAP: Record<string, string> = {
  active: '使用中',
  archived: '已归档',
}

const ORIGIN_MAP: Record<string, string> = {
  manual_creation: '手工新建',
  template_based: '基于模板',
  ai_recommendation: 'AI 推荐',
  doe_experiment: 'DOE 实验',
  legacy_import: '历史导入',
  equipment_capture: '设备捕获',
  process_transplant: '工艺移植',
}

function statusLabel(s: string) {
  return STATUS_MAP[s] ?? s
}

function originLabel(o: string) {
  return ORIGIN_MAP[o] ?? o
}

// ============================================================================
// 数据加载
// ============================================================================

async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await processParameterMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      status: query.status || undefined,
      origin_type: query.origin_type || undefined,
      mold_no: query.mold_no || undefined,
      machine_model: query.machine_model || undefined,
      polymer_abbreviation: query.polymer_abbreviation || undefined,
      start_date: query.start_date || undefined,
      end_date: query.end_date || undefined,
    } as any)
    if (res?.status === 0) {
      list_data.value = res.data ?? { total: 0, items: [] }
    } else {
      ElMessage.error(res?.msg || '查询失败')
    }
  } catch (err) {
    console.error('[ProcessParameterList] fetchList failed:', err)
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
  router.push('/process/parameter/new')
}

function goEdit(row: any) {
  router.push(`/process/parameter/${row.id}/edit`)
}

async function deleteOne(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认删除该工艺？\n${row.condition_no ?? row.id}`,
      '删除工艺',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    const res: any = await processParameterMethod.delete(row.id)
    if (res?.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res?.msg || '删除失败')
    }
  } catch (err) {
    console.error('[ProcessParameterList] deleteOne failed:', err)
  }
}

async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${ids.length} 条工艺吗？此操作不可恢复！`,
      '批量删除确认',
      { type: 'error' },
    )
  } catch {
    return
  }
  try {
    // 后端用 processParameterBatchDelete（POST /api/processes/parameter/batch_delete/）
    const res: any = await processParameterBatchDelete(ids)
    if (res?.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 条工艺`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res?.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[ProcessParameterList] batchDelete failed:', err)
  }
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.process-condition-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

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
