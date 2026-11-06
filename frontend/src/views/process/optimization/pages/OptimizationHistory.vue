<!-- OptimizationHistory - 调机记录列表 -->
<template>
  <div class="page-stack">
    <!-- 搜索表单（复用工艺参数搜索） -->
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
      view-name="optimization_list"
      :show-selection="true"
      :show-index="true"
      :stripe="true"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="openHistory"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <template #toolbar>
        <el-button type="success" @click="goCreate">
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          启动新优化
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

      <!-- 工艺编号列：可点击查看调机历史 -->
      <template #cell-condition_no="{ row }">
        <el-link
          v-if="row.condition_no"
          type="primary"
          @click="openHistory(row)"
        >
          {{ row.condition_no }}
        </el-link>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 状态列：标签式渲染 -->
      <template #cell-status="{ row }">
        <el-tag
          v-if="row.status"
          :type="conditionStatusTagType(row.status)"
          size="small"
        >
          {{ conditionStatusLabel(row.status) }}
        </el-tag>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 起源列 -->
      <template #cell-origin_type="{ row }">
        <span v-if="row.origin_type">{{ originLabel(row.origin_type) }}</span>
        <span v-else style="color: #c0c4cc;">—</span>
      </template>

      <!-- 调机轮次列：核心信息，加色高亮 -->
      <template #cell-parameters_count="{ row }">
        <el-tag
          :type="row.parameters_count > 1 ? 'warning' : 'info'"
          size="small"
          effect="plain"
        >
          <AppIcon icon="mdi:repeat-variant" style="margin-right: 2px;" />
          {{ row.parameters_count ?? 0 }} 轮
        </el-tag>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="290" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="continueTuning(row)">
                <AppIcon icon="mdi:play-circle-outline" style="margin-right: 4px; font-size: 14px;" />
                继续调机
              </el-button>
              <el-button type="text" @click="openHistory(row)">
                <AppIcon icon="mdi:history" style="margin-right: 4px; font-size: 14px;" />
                调机历史
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

    <!-- 调机历史抽屉（左轮次列表 + 右全量只读详情） -->
    <TuningHistoryDrawer
      v-model:visible="history_drawer_visible"
      :title="`调机历史 — ${history_drawer_title}`"
      :loading="history_loading"
      :items="history_items"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import ProcessSearchForm from '@/views/process/library/components/ProcessSearchForm.vue'
import { processRecordMethod, processRecordHistory } from '@/api'
import type { TuningRoundItem } from '@/api'
import { conditionStatusLabel, conditionStatusTagType } from '@/views/process/shared/condition-status'
import TuningHistoryDrawer from '../components/TuningHistoryDrawer.vue'

// 类型
interface ListData {
  total: number
  items: any[]
}

// 路由
const router = useRouter()

// 列表状态
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

// 列定义（调机视角，凸显 parameters_count）
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '工艺编号', prop: 'condition_no', minWidth: 160, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '调机轮次', prop: 'parameters_count', minWidth: 100, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '状态', prop: 'status', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '起源', prop: 'origin_type', minWidth: 110, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '模具编号', prop: 'mold_no', minWidth: 140, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '模具名称', prop: 'mold_name', minWidth: 180, align: 'left', header_align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '设备型号', prop: 'machine_model', minWidth: 150, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '塑料简称', prop: 'polymer_abbreviation', minWidth: 110, align: 'center', sortable: true, tooltip: true, filterable: false },
  { visible: true, label: '创建时间', prop: 'created_at', minWidth: 170, align: 'center', sortable: true, tooltip: true, filterable: false },
])

// 标签转换
const ORIGIN_MAP: Record<string, string> = {
  manual_creation: '手工新建',
  template_based: '基于模板',
  ai_recommendation: 'AI 推荐',
  doe_experiment: 'DOE 实验',
  legacy_import: '历史导入',
  equipment_capture: '设备捕获',
  process_transplant: '工艺移植',
}

function originLabel(o: string) {
  return ORIGIN_MAP[o] ?? o
}

// 列表数据加载
async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await processRecordMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      view_type: 'optimization',
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
  } catch {
    // 拦截器已统一 toast
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

// 调机历史抽屉
const history_drawer_visible = ref(false)
const history_loading = ref(false)
const history_items = ref<TuningRoundItem[]>([])
const history_drawer_title = ref('')

async function openHistory(row: any) {
  if (!row?.id) {
    ElMessage.warning('记录缺少 ID，无法查看调机历史')
    return
  }
  history_drawer_title.value = row.condition_no || `#${row.id}`
  history_drawer_visible.value = true
  history_items.value = []
  history_loading.value = true
  try {
    const res: any = await processRecordHistory(row.id)
    if (res?.status === 0) {
      history_items.value = res.data?.history ?? []
    } else {
      ElMessage.error(res?.msg || '调机历史加载失败')
    }
  } catch {
    // 拦截器已统一 toast
  } finally {
    history_loading.value = false
  }
}

// 操作
function goCreate() {
  router.push('/process/optimization')
}

/** 继续调机：带 condition_id 进智能调机页，由该页从后端重建该 condition 的历史轮次 */
function continueTuning(row: any) {
  if (!row?.id) {
    ElMessage.warning('记录缺少 ID，无法继续调机')
    return
  }
  router.push({ path: '/process/optimization', query: { condition_id: row.id } })
}

async function deleteOne(row: any) {
  try {
    await ElMessageBox.confirm(
      `确认删除该优化记录？\n${row.condition_no ?? row.id}\n（将级联删除该条件下所有调机轮次）`,
      '删除优化记录',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    const res: any = await processRecordMethod.batchDelete({ ids: [row.id] })
    if (res?.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res?.msg || '删除失败')
    }
  } catch {
    // 拦截器已统一 toast
  }
}

async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${ids.length} 条优化记录吗？\n（每条将级联删除该条件下所有调机轮次）此操作不可恢复！`,
      '批量删除确认',
      { type: 'error' },
    )
  } catch {
    return
  }
  try {
    const res: any = await processRecordMethod.batchDelete({ ids })
    if (res?.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 条记录`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res?.msg || '批量删除失败')
    }
  } catch {
    // 拦截器已统一 toast
  }
}

// 生命周期
onMounted(() => {
  fetchList()
})
</script>