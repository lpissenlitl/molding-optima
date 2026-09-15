<!--
  InjectionMachineList - 注塑机列表页

  架构（2026-09-09 重写）：
    - 搜索：InjectionSearchForm（保留 Options API 风格，封装 BaseSearchForm）
    - 列表：BaseTable 组件（接管 el-table + el-pagination + change-table-size + TableSetting）
    - 列定义：16 列，注射单元嵌套字段用 cell 插槽渲染（formatLabel 无法访问 row）
    - 顶部 toolbar：添加机器、导出列表
    - 行操作列：编辑、删除
-->
<template>
  <div class="injection-machine-list">
    <!-- 搜索表单 -->
    <InjectionSearchForm
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
      :enable-column-filter="false"
      view-name="mac_list_col_config"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="updateMachine"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <template #toolbar>
        <el-button type="success" @click="toAddMachine">
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          添加机器
        </el-button>
        <el-button type="success" plain @click="exportListToExcel">
          <AppIcon icon="mdi:download" style="margin-right: 4px; font-size: 14px;" />
          导出列表
        </el-button>
      </template>

      <!-- 设备型号列：可点击跳转编辑 -->
      <template #cell-model="{ row }">
        <el-link type="primary" @click="updateMachine(row)">{{ row.model }}</el-link>
      </template>

      <!-- 注射单元字段：嵌套数组 → "/" 拼接 -->
      <template #cell-injection_units_max_injection_weight="{ row }">
        {{ formatOneToMany(row.injection_units, 'max_injection_weight') }}
      </template>
      <template #cell-injection_units_max_injection_speed="{ row }">
        {{ formatOneToMany(row.injection_units, 'max_injection_speed') }}
      </template>
      <template #cell-injection_units_max_injection_stroke="{ row }">
        {{ formatOneToMany(row.injection_units, 'max_injection_stroke') }}
      </template>
      <template #cell-injection_units_max_injection_pressure="{ row }">
        {{ formatOneToMany(row.injection_units, 'max_injection_pressure') }}
      </template>
      <template #cell-injection_units_max_holding_pressure="{ row }">
        {{ formatOneToMany(row.injection_units, 'max_holding_pressure') }}
      </template>
      <template #cell-injection_units_max_screw_rotation_speed="{ row }">
        {{ formatOneToMany(row.injection_units, 'max_screw_rotation_speed') }}
      </template>
      <template #cell-injection_units_plasticizing_capacity="{ row }">
        {{ formatOneToMany(row.injection_units, 'plasticizing_capacity') }}
      </template>
      <template #cell-injection_units_screw_diameter="{ row }">
        {{ formatOneToMany(row.injection_units, 'screw_diameter') }}
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="updateMachine(row)">
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button type="text" class="text-danger" @click="deleteMachine(row)">
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
import InjectionSearchForm from '../components/InjectionSearchForm.vue'
import { machineMethod, exportListData } from '@/api'
import { getReportDownloadUrl } from '@/utils/assert'
import { hasPermission } from '@/utils/permission'

// ============================================================================
// 列表数据
// ============================================================================

interface ListData {
  total: number
  items: any[]
}

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const selected_rows = ref<any[]>([])
const table_size = ref<'small' | 'default' | 'large'>('default')

// 查询参数（与 InjectionSearchForm 一致）
const query = reactive({
  brand: null as string | null,
  model: null as string | null,
  device_no: null as string | null,
  location: null as string | null,
  machine_type: null as string | null,
  drive_system: null as string | null,

  page_no: 1,
  page_size: 100,
})

// ============================================================================
// 列定义（16 列）
// ============================================================================

const table_columns = ref<BaseTableColumn[]>([
  // 基础字段
  { visible: true, label: '品牌', prop: 'brand', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '设备型号', prop: 'model', minWidth: 150, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, label: '设备编号', prop: 'device_no', minWidth: 150, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '设备位置', prop: 'location', minWidth: 200, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '设备类型', prop: 'machine_type', minWidth: 110, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '驱动系统', prop: 'drive_system', minWidth: 100, align: 'center', header_align: 'center', sortable: false, tooltip: false },

  // 注射单元嵌套字段（prop 是单一字段名 + 模板插槽渲染）
  { visible: true, label: '最大注射重量(g)', prop: 'injection_units_max_injection_weight', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '最大注射速度(mm/s)', prop: 'injection_units_max_injection_speed', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '最大注射行程(mm)', prop: 'injection_units_max_injection_stroke', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, label: '最大注射压力(MPa)', prop: 'injection_units_max_injection_pressure', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, label: '最大保压压力(MPa)', prop: 'injection_units_max_holding_pressure', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, label: '最大螺杆转速(rpm)', prop: 'injection_units_max_screw_rotation_speed', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '塑化能力(g/h)', prop: 'injection_units_plasticizing_capacity', minWidth: 100, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '螺杆直径(mm)', prop: 'injection_units_screw_diameter', minWidth: 100, align: 'center', header_align: 'center', sortable: false, tooltip: false },

  // 元数据
  { visible: true, label: '投产日期', prop: 'commissioning_date', minWidth: 110, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  { visible: true, label: '更新日期', prop: 'updated_at', minWidth: 170, align: 'center', header_align: 'center', sortable: false, tooltip: false },
])

// ============================================================================
// 工具函数
// ============================================================================

/**
 * 一对多字段格式化：数组 → "/"-拼接字符串
 * 兼容 undefined / 空数组 / 字段缺失
 */
function formatOneToMany(items: any[] | undefined, field: string, sep = '/'): string {
  if (!Array.isArray(items)) return ''
  return items.map((it) => it?.[field]).filter(Boolean).join(sep)
}

// ============================================================================
// 路由 & API
// ============================================================================

const router = useRouter()

async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await machineMethod.get(query)
    if (res.status === 0) {
      list_data.value = res.data
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[InjectionMachineList] fetchList failed:', err)
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

// ============================================================================
// 操作
// ============================================================================

function toAddMachine() {
  if (!hasPermission('add_machine')) {
    return ElMessage.warning('无添加机器权限')
  }
  router.push('/equipment/injection/new')
}

function updateMachine(row: any) {
  if (!hasPermission('review_machine')) {
    return ElMessage.warning('无该机器详细信息的查看权限')
  }
  router.push(`/equipment/injection/${row.id}/edit`)
}

async function exportListToExcel() {
  if (selected_rows.value.length === 0) {
    return ElMessage.warning('无选中项。')
  }
  const ids = selected_rows.value.map((it) => it.id)
  try {
    const res: any = await exportListData({ resource: 'injection_list', ids })
    if (res.status === 0 && res.data?.url) {
      window.location.href = getReportDownloadUrl(res.data.url)
    }
  } catch (err) {
    console.error('[InjectionMachineList] exportListToExcel failed:', err)
  }
}

async function deleteMachine(row: any) {
  if (!hasPermission('delete_machine')) {
    return ElMessage.warning('无删除机器权限')
  }
  try {
    await ElMessageBox.confirm(
      `确认删除以下机器？\r\n ${row.model}`,
      '删除机器',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return ElMessage.info('已取消删除')
  }
  try {
    const res: any = await machineMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功!')
      fetchList()
    }
  } catch (err) {
    console.error('[InjectionMachineList] deleteMachine failed:', err)
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
.injection-machine-list {
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
