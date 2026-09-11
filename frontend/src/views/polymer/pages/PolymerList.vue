<!--
  PolymerList - 聚合物列表页

  设计要点：
    - 与 ProjectList / MoldList 保持统一规范
    - Composition API + <script setup>
    - BaseTable 组件封装（分页/选择/大小/列配置统一管理）
    - 顶部 toolbar 插槽（新建 + 批量操作 + 导出 + 配置表格）
    - 行操作：编辑 + 复制 + 删除（el-button type="text" 紧凑风格）
-->
<template>
  <div class="polymer-list">
    <!-- 搜索表单（配置驱动，复用 PolymerSearchForm） -->
    <PolymerSearchForm
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
      :height-offset="260"
      view-name="polymer_list"
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
          新建材料
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

      <!-- 塑料简称列：可点击跳转编辑 -->
      <template #cell-abbreviation="{ row }">
        <el-link type="primary" @click="goEdit(row)">{{ row.abbreviation }}</el-link>
      </template>

      <!-- 塑料牌号列：可点击跳转编辑 -->
      <template #cell-grade="{ row }">
        <el-link type="primary" @click="goEdit(row)">{{ row.grade }}</el-link>
      </template>

      <!-- 干燥温度范围 -->
      <template #cell-drying_temp="{ row }">
        <span v-if="row.drying_temp_min != null && row.drying_temp_max != null">
          {{ row.drying_temp_min }} - {{ row.drying_temp_max }} ℃
        </span>
        <span v-else-if="row.drying_temp_min != null">{{ row.drying_temp_min }} ℃</span>
        <span v-else-if="row.drying_temp_max != null">{{ row.drying_temp_max }} ℃</span>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 干燥时间范围 -->
      <template #cell-drying_time="{ row }">
        <span v-if="row.drying_time_min != null && row.drying_time_max != null">
          {{ row.drying_time_min }} - {{ row.drying_time_max }} h
        </span>
        <span v-else-if="row.drying_time_min != null">{{ row.drying_time_min }} h</span>
        <span v-else-if="row.drying_time_max != null">{{ row.drying_time_max }} h</span>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="goCopy(row)">
                <AppIcon icon="mdi:content-copy" style="margin-right: 4px; font-size: 14px;" />
                复制
              </el-button>
              <el-button type="text" @click="goEdit(row)">
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button type="text" class="text-danger" @click="deletePolymer(row)">
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
import PolymerSearchForm from '../components/PolymerSearchForm.vue'
import { polymerMethod, exportListData } from '@/api'
import { getReportDownloadUrl } from '@/utils/assert'

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
  manufacturer: undefined as string | undefined,
  abbreviation: undefined as string | undefined,
  grade: undefined as string | undefined,
  category: undefined as string | undefined,
  data_source: undefined as string | undefined,
  level_code: undefined as string | undefined,
  vendor_code: undefined as string | undefined,
})

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const table_size = ref<'small' | 'default' | 'large'>('default')
const selected_rows = ref<any[]>([])
const show_table_setting = ref(false)

// 列定义
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '塑料厂商', prop: 'manufacturer', minWidth: 120, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '塑料简称', prop: 'abbreviation', minWidth: 120, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '塑料牌号', prop: 'grade', minWidth: 180, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '塑料类别', prop: 'category', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '数据来源', prop: 'data_source', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '等级代码', prop: 'level_code', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '供应商代码', prop: 'vendor_code', minWidth: 120, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '推荐成型温度(℃)', prop: 'recommended_melt_temp', minWidth: 130, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '塑料降解温度(℃)', prop: 'degradation_temp', minWidth: 130, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '推荐模具温度(℃)', prop: 'recommended_mold_temp', minWidth: 130, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '推荐顶出温度(℃)', prop: 'ejection_temp', minWidth: 120, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '推荐剪切线速度(mm/s)', prop: 'recommended_shear_line_speed', minWidth: 160, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '推荐注射速率(cm³/s)', prop: 'recommend_injection_rate', minWidth: 140, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '推荐背压(MPa)', prop: 'recommend_back_pressure', minWidth: 120, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '干燥方式', prop: 'drying_method', minWidth: 100, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '干燥温度(℃)', prop: 'drying_temp', minWidth: 120, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '干燥时间(h)', prop: 'drying_time', minWidth: 120, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '更新日期', prop: 'updated_at', minWidth: 170, align: 'center', sortable: false, tooltip: false, filterable: false },
])

const externalUniqueValues = ref<Record<string, any[]>>({})

// ============================================================================
// API
// ============================================================================

async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await polymerMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      manufacturer: query.manufacturer || undefined,
      abbreviation: query.abbreviation || undefined,
      grade: query.grade || undefined,
      category: query.category,
      data_source: query.data_source,
      level_code: query.level_code || undefined,
      vendor_code: query.vendor_code || undefined,
    } as any)
    if (res.status === 0) {
      list_data.value = res.data
      syncExternalUniqueValues()
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[PolymerList] fetchList failed:', err)
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
    category: collect('category'),
    data_source: collect('data_source'),
    drying_method: collect('drying_method'),
  }
}

// ============================================================================
// 操作
// ============================================================================

function goCreate() {
  router.push('/material/polymer/new')
}

function goEdit(row: any) {
  router.push(`/material/polymer/${row.id}/edit`)
}

function goCopy(row: any) {
  router.push(`/material/polymer/${row.id}/copy`)
}

async function deletePolymer(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认删除以下材料信息？\n${row.grade}`,
      '删除材料',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    const res: any = await polymerMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[PolymerList] deletePolymer failed:', err)
  }
}

async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${ids.length} 条材料信息？此操作不可恢复！`,
      '批量删除确认',
      { type: 'warning' }
    )
  } catch {
    return
  }
  try {
    const res: any = await polymerMethod.multipleDelete({ ids })
    if (res.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 条材料`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[PolymerList] batchDelete failed:', err)
  }
}

async function exportListToExcel() {
  if (selected_rows.value.length === 0) {
    ElMessage.warning('请先选择要导出的材料')
    return
  }
  const ids = selected_rows.value.map((item) => item.id)
  try {
    const res: any = await exportListData({ resource: 'polymer_list', ids })
    if (res.status === 0 && res.data.url) {
      window.location.href = getReportDownloadUrl(res.data.url)
      ElMessage.success('导出成功')
    } else {
      ElMessage.error(res.msg || '导出失败')
    }
  } catch (err) {
    console.error('[PolymerList] exportListToExcel failed:', err)
  }
}

function refreshView() {
  show_table_setting.value = false
  fetchList()
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.polymer-list {
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