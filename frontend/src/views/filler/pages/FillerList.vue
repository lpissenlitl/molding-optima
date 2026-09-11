<!--
  FillerList - 填充物列表（CRUD）

  架构（2026-09-08 Phase 1）：
    - BaseTable + Composition API（与 PolymerList 同款风格）
    - 路由：/material/filler/list（在 material 父路由下，侧边栏自然聚合）
    - 列定义：BaseTableColumn[] 类型化（用 column.map 实现 value→label）
    - 行操作列：编辑 + 删除（text 按钮 + AppIcon）
    - 删除确认：ElMessageBox.confirm
-->
<template>
  <div class="filler-list">
    <FillerSearchForm
      :query-detail="query"
      @search="handleSearch"
      @reset="handleReset"
    />

    <BaseTable
      :columns="table_columns"
      :data="list_data.items || []"
      :total="list_data.total || 0"
      :query="query"
      :loading="list_loading"
      view-name="filler_list"
      @row-dblclick="editFiller"
      @selection-change="(rows) => (selected_rows = rows)"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; getListData() }"
      @current-change="(v: number) => { query.page_no = v; getListData() }"
    >
      <template #toolbar>
        <el-button type="primary" @click="toAddFiller">
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          新增填充物
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

      <template #append-columns>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="editFiller(row)">
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 2px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button type="text" class="text-danger" @click="deleteFiller(row)">
                <AppIcon icon="mdi:delete-outline" style="margin-right: 2px; font-size: 14px;" />
                删除
              </el-button>
            </span>
          </template>
        </el-table-column>
      </template>
    </BaseTable>

    <TableSetting
      :table-data="table_columns"
      v-model:show="show_table_setting"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import TableSetting from '@/components/TableSetting.vue'
import FillerSearchForm from '../components/FillerSearchForm.vue'
import { fillerMethod, exportListData } from '@/api'
import { getReportDownloadUrl } from '@/utils/assert'
import {
  fillerTypeOptions,
  fillerCategoryOptions,
  colorOptions,
  shapeOptions,
} from '@/constants/polymer-const'
import { loadTablePreference } from '@/utils/columns-setting'

const router = useRouter()

const query = reactive({
  name: null as string | null,
  abbreviation: null as string | null,
  category: null as string | null,
  shape: null as string | null,
  page_no: 1,
  page_size: 20,
})

const list_data = ref<{ items: any[]; total: number }>({ items: [], total: 0 })
const list_loading = ref(false)
const selected_rows = ref<any[]>([])
const show_table_setting = ref(false)

// 列定义：用 column.map 实现 value→label 自动映射（BaseTable formatCell 自动用 map）
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, prop: 'name', label: '名称', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: false },
  {
    visible: true, prop: 'abbreviation', label: '缩写', minWidth: 200,
    align: 'center', header_align: 'center', sortable: false, tooltip: true,
    map: Object.fromEntries(fillerTypeOptions.map((o) => [o.value, o.label])),
  },
  {
    visible: true, prop: 'category', label: '类别', minWidth: 140,
    align: 'center', header_align: 'center', sortable: false, tooltip: false,
    map: Object.fromEntries(fillerCategoryOptions.map((o) => [o.value, o.label])),
  },
  {
    visible: true, prop: 'shape', label: '形状', minWidth: 100,
    align: 'center', header_align: 'center', sortable: false, tooltip: true,
    map: Object.fromEntries(shapeOptions.map((o) => [o.value, o.label])),
  },
  { visible: true, prop: 'particle_size_d50', label: '中位粒径 D50(μm)', minWidth: 160, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, prop: 'aspect_ratio', label: '长径比', minWidth: 100, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, prop: 'moisture_content', label: '含水率(%)', minWidth: 100, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, prop: 'surface_treatment', label: '表面处理', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, prop: 'density', label: '密度(g/cm³)', minWidth: 120, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  { visible: true, prop: 'thermal_stability_temp', label: '热稳定温度(℃)', minWidth: 150, align: 'center', header_align: 'center', sortable: false, tooltip: true },
  {
    visible: true, prop: 'color', label: '颜色', minWidth: 100,
    align: 'center', header_align: 'center', sortable: false, tooltip: true,
    map: Object.fromEntries(colorOptions.map((o) => [o.value, o.label])),
  },
  { visible: true, prop: 'updated_at', label: '更新日期', minWidth: 170, align: 'center', header_align: 'center', sortable: true, tooltip: false },
])

onMounted(() => {
  loadViewSetting()
  getListData()
})

function loadViewSetting() {
  const pref = loadTablePreference('filler_list')
  if (pref?.columns?.length) {
    const storedMap = new Map(pref.columns.map((s: any) => [s.prop, s]))
    table_columns.value = table_columns.value.map((col) => {
      const stored = storedMap.get(col.prop) as any
      return stored ? { ...col, visible: stored.visible !== false } : col
    })
  }
}

async function getListData() {
  list_loading.value = true
  try {
    const res: any = await fillerMethod.get({ ...query })
    if (res.status === 0) {
      list_data.value = res.data || { items: [], total: 0 }
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[FillerList] fetchList failed:', err)
  } finally {
    list_loading.value = false
  }
}

function handleSearch() {
  query.page_no = 1
  getListData()
}

function handleReset() {
  query.name = null
  query.abbreviation = null
  query.category = null
  query.shape = null
  query.page_no = 1
  getListData()
}

function toAddFiller() {
  router.push('/material/filler/new')
}

function editFiller(row: any) {
  router.push(`/material/filler/${row.id}/edit`)
}

async function deleteFiller(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认删除以下填充物？\n${row.name || row.abbreviation || `ID: ${row.id}`}`,
      '删除填充物',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    const res: any = await fillerMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      getListData()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[FillerList] deleteFiller failed:', err)
  }
}

async function exportListToExcel() {
  if (selected_rows.value.length === 0) {
    ElMessage.warning('请先选择要导出的填充物')
    return
  }
  const ids = selected_rows.value.map((item) => item.id)
  try {
    const res: any = await exportListData({ resource: 'filler_list', ids })
    if (res.status === 0 && res.data?.url) {
      window.location.href = getReportDownloadUrl(res.data.url)
      ElMessage.success('导出成功')
    } else {
      ElMessage.error(res.msg || '导出失败')
    }
  } catch (err) {
    console.error('[FillerList] exportListToExcel failed:', err)
  }
}
</script>

<style scoped lang="scss">
.filler-list {
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