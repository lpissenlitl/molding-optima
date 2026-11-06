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

    <!-- 调机历史 dialog -->
    <el-dialog
      v-model="history_dialog_visible"
      :title="`调机历史 — ${history_dialog_title}`"
      width="900px"
      :close-on-click-modal="false"
    >
      <div v-loading="history_loading">
        <el-empty
          v-if="!history_loading && history_items.length === 0"
          description="该工艺条件下暂无调机记录"
        />
        <el-timeline v-else>
          <el-timeline-item
            v-for="(item, idx) in history_items"
            :key="item.id ?? idx"
            :type="idx === 0 ? 'primary' : 'success'"
            :timestamp="formatDate(item.created_at)"
            placement="top"
          >
            <el-card class="history-item">
              <div class="history-item__header">
                <span class="history-item__seq">
                  <AppIcon icon="mdi:counter" style="margin-right: 4px;" />
                  seq_idx = {{ item.seq_idx ?? '-' }}
                </span>
                <div class="history-item__tags">
                  <el-tag size="small" :type="idx === 0 ? 'primary' : 'info'">
                    {{ sourceLabel(item.param_source) }}
                  </el-tag>
                  <el-tag size="small" type="info">
                    parameter_id = {{ item.id ?? '-' }}
                  </el-tag>
                  <el-tag size="small" :type="resultTagType(item.tuning?.tuning_result)">
                    {{ resultLabel(item.tuning?.tuning_result) }}
                  </el-tag>
                </div>
              </div>
              <div v-if="item.tuning?.defect_feedbacks?.length" class="history-item__defects">
                <span class="history-item__defects-label">缺陷</span>
                <el-tag
                  v-for="(d, di) in item.tuning.defect_feedbacks"
                  :key="di"
                  size="small"
                  type="danger"
                  effect="plain"
                >
                  {{ d?.keyword_name ?? '未知缺陷' }}{{ d?.level ? ` / ${d.level}` : '' }}
                </el-tag>
              </div>
              <div class="history-item__body">
                <el-descriptions :column="2" size="small" border>
                  <el-descriptions-item label="注射压力 (段 1)">
                    {{ item.inj_pres_1 ?? '-' }} MPa
                  </el-descriptions-item>
                  <el-descriptions-item label="保压时间 (段 1)">
                    {{ item.hold_t_1 ?? '-' }} s
                  </el-descriptions-item>
                  <el-descriptions-item label="冷却时间">
                    {{ item.cool_t ?? '-' }} s
                  </el-descriptions-item>
                  <el-descriptions-item label="料筒温度 (段 1)">
                    {{ item.brl_temp_1 ?? '-' }} ℃
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import ProcessSearchForm from '@/views/process/library/components/ProcessSearchForm.vue'
import { processRecordMethod, processRecordHistory } from '@/api'
import { conditionStatusLabel, conditionStatusTagType } from '@/views/process/shared/condition-status'

// 类型
interface ListData {
  total: number
  items: any[]
}

interface HistoryItem {
  id?: number
  seq_idx?: number
  created_at?: string
  param_source?: string
  inj_pres_1?: number | null
  hold_t_1?: number | null
  cool_t?: number | null
  brl_temp_1?: number | null
  /** 该轮自身的试模反馈（与该轮参数配对） */
  tuning?: {
    tuning_result?: 'effective' | 'unchanged' | 'ineffective' | 'qualified' | 'unqualified' | null
    result?: string | null
    defect_feedbacks?: any[]
    result_detail?: string | null
  }
  [k: string]: any
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

// 参数来源（与后端 ProcessParameter.PARAMETER_SOURCE_CHOICES 对齐）
const PARAM_SOURCE_MAP: Record<string, string> = {
  unknown: '未标记',
  manual: '手工录入',
  import: '外部导入',
  algorithm_init: '算法初始化',
  system_inferred: '系统推理',
  manual_adjusted: '人工调整',
  equipment_sync: '设备同步',
  template_copy: '模板复制',
  ai_recommended: 'AI 推荐',
}

function originLabel(o: string) {
  return ORIGIN_MAP[o] ?? o
}

function sourceLabel(s?: string | null) {
  if (!s) return '未标记'
  return PARAM_SOURCE_MAP[s] ?? s
}

/** 效果评价 → 文案（null = 未评价） */
const RESULT_LABEL: Record<string, string> = {
  effective: '改善',
  unchanged: '无变化',
  ineffective: '变差',
  qualified: '合格',
  unqualified: '不合格',
}

/** 效果评价 → 标签色 */
const RESULT_TAG_TYPE: Record<string, 'success' | 'warning' | 'danger'> = {
  effective: 'success',
  unchanged: 'warning',
  ineffective: 'danger',
  qualified: 'success',
  unqualified: 'danger',
}

function resultLabel(v?: string | null) {
  return v ? (RESULT_LABEL[v] ?? v) : '未评价'
}

function resultTagType(v?: string | null): 'success' | 'warning' | 'danger' | 'info' {
  return v ? (RESULT_TAG_TYPE[v] ?? 'info') : 'info'
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

// 调机历史 dialog
const history_dialog_visible = ref(false)
const history_loading = ref(false)
const history_items = ref<HistoryItem[]>([])
const history_dialog_title = ref('')

async function openHistory(row: any) {
  if (!row?.id) {
    ElMessage.warning('记录缺少 ID，无法查看调机历史')
    return
  }
  history_dialog_title.value = row.condition_no || `#${row.id}`
  history_dialog_visible.value = true
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

function formatDate(s: string | undefined | null): string {
  if (!s) return '-'
  // ISO datetime → 本地化时间
  try {
    const d = new Date(s)
    if (isNaN(d.getTime())) return s
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} `
      + `${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return s
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

<style scoped lang="scss">
.history-item {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  &__seq {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  &__tags {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  &__defects {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
  }

  &__defects-label {
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}
</style>