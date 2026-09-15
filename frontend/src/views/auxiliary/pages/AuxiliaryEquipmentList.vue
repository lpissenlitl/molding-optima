<!--
  AuxiliaryEquipmentList - 辅助装置列表页

  架构（参考 InjectionMachineList / PolymerList）：
  - 搜索：AuxiliarySearchForm（封装 BaseSearchForm，配置驱动）
  - 列表：BaseTable 组件（接管 el-table + el-pagination + 密度切换 + TableSetting）
  - 列定义：8 列（名称/类型/规格/总数量/可用数量/备注/更新日期/创建日期）
  - 顶部 toolbar：添加辅机、导出列表、配置表格
  - 行操作列：编辑、删除（紧凑 text 按钮风格）
-->
<template>
  <div class="auxiliary-equipment-list">
    <!-- 搜索表单 -->
    <AuxiliarySearchForm
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
      view-name="aux_list_col_config"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="updateAuxiliary"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <template #toolbar>
        <el-button type="success" @click="toAddAuxiliary">
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          添加辅助装置
        </el-button>
        <el-button
          type="success"
          :disabled="selected_rows.length === 0"
          @click="exportListToExcel"
        >
          <AppIcon icon="mdi:download" style="margin-right: 4px; font-size: 14px;" />
          导出列表
        </el-button>
        <el-button type="primary" plain @click="show_table_setting = true">
          <AppIcon icon="mdi:settings-outline" style="margin-right: 4px; font-size: 14px;" />
          配置表格
        </el-button>
      </template>

      <!-- 设备名称列：可点击进入编辑 -->
      <template #cell-equipment_name="{ row }">
        <el-link type="primary" @click="updateAuxiliary(row)">{{ row.equipment_name }}</el-link>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="updateAuxiliary(row)">
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button type="text" class="text-danger" @click="deleteAuxiliary(row)">
                <AppIcon icon="mdi:delete-outline" style="margin-right: 4px; font-size: 14px;" />
                删除
              </el-button>
            </span>
          </template>
        </el-table-column>
      </template>
    </BaseTable>

    <!-- 表格列设置抽屉 -->
    <TableSetting
      :table-data="table_columns"
      v-model:show="show_table_setting"
      @close="refreshView"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import TableSetting from '@/components/TableSetting.vue'
import AuxiliarySearchForm from '../components/AuxiliarySearchForm.vue'
import { auxiliaryMethod, exportListData } from '@/api'
import { getReportDownloadUrl } from '@/utils/assert'
import { hasPermission } from '@/utils/permission'

// ============================================================================
// 列表数据
// ============================================================================

interface ListData {
  total: number
  items: any[]
}

const router = useRouter()

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const selected_rows = ref<any[]>([])
const table_size = ref<'small' | 'default' | 'large'>('default')
const show_table_setting = ref(false)

// 查询参数（与 AuxiliarySearchForm 一致）
const query = reactive({
  equipment_name: null as string | null,
  equipment_type: null as string | null,
  page_no: 1,
  page_size: 100,
})

// ============================================================================
// 列定义（8 列）
// ============================================================================

const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '设备名称', prop: 'equipment_name', minWidth: 160, align: 'left', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '设备类型', prop: 'equipment_type', minWidth: 110, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '规格参数', prop: 'specification', minWidth: 200, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '总数量', prop: 'total_count', minWidth: 100, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '可用数量', prop: 'available_count', minWidth: 100, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '备注', prop: 'remarks', minWidth: 240, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, label: '更新日期', prop: 'updated_at', minWidth: 170, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '创建日期', prop: 'created_at', minWidth: 170, align: 'center', header_align: 'center', sortable: false, tooltip: false },
])

// ============================================================================
// API
// ============================================================================

async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await auxiliaryMethod.get(query)
    if (res.status === 0) {
      list_data.value = res.data
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[AuxiliaryEquipmentList] fetchList failed:', err)
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
  query.page_no = 1
  fetchList()
}

function refreshView() {
  // TableSetting 关闭后，列定义已通过 .sync 更新，重新拉一次数据（可选）
  fetchList()
}

// ============================================================================
// 操作
// ============================================================================

function toAddAuxiliary() {
  if (!hasPermission('add_auxiliary')) {
    return ElMessage.warning('无添加辅助装置权限')
  }
  router.push('/equipment/auxiliary/new')
}

function updateAuxiliary(row: any) {
  if (!hasPermission('review_auxiliary')) {
    return ElMessage.warning('无该辅助装置详细信息的查看权限')
  }
  router.push(`/equipment/auxiliary/${row.id}/edit`)
}

async function exportListToExcel() {
  if (selected_rows.value.length === 0) {
    return ElMessage.warning('无选中项。')
  }
  const ids = selected_rows.value.map((it) => it.id)
  try {
    const res: any = await exportListData({ resource: 'auxiliary_list', ids })
    if (res.status === 0 && res.data?.url) {
      window.location.href = getReportDownloadUrl(res.data.url)
    }
  } catch (err) {
    console.error('[AuxiliaryEquipmentList] exportListToExcel failed:', err)
  }
}

async function deleteAuxiliary(row: any) {
  if (!hasPermission('delete_auxiliary')) {
    return ElMessage.warning('无删除辅助装置权限')
  }
  try {
    await ElMessageBox.confirm(
      `确认删除以下辅机信息？\r\n ${row.equipment_name}`,
      '删除辅机',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return ElMessage.info('已取消删除')
  }
  try {
    const res: any = await auxiliaryMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功!')
      fetchList()
    }
  } catch (err) {
    console.error('[AuxiliaryEquipmentList] deleteAuxiliary failed:', err)
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
.auxiliary-equipment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
