<!--
  OptimizationList - 优化记录列表

  路由：/process/optimization-records
  数据源：后端 /api/processes/parameter/（同 ProcessParameterList，复用通用工艺条件表）
  业务说明：
    列出每条 ProcessCondition 对应的工艺优化全链路状态：调机轮次数、模具/机台/材料等
    与"工艺参数列表"的区别：聚焦在"调机迭代"视角，凸显调机轮次 + 调机历史入口

  设计要点：
    - 复用 BaseTable / ProcessSearchForm：避免重复开发搜索 + 列表 + 列偏好持久化
    - 调机轮次列（parameters_count）：后端 annotation 注入（2026-09-23 加）
    - 行操作：
      - 查看调机历史（dialog，调用 /api/processes/optimization/<id>/history/）
      - 启动新优化（跳转 OptimizationCreate，但 OptimizationCreate 是空白表单场景，
        见 v1 暂不预填 condition，用户需手动填条件生成新优化）
-->
<template>
  <div class="optimization-list">
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
          :type="row.status === 'active' ? 'success' : 'info'"
          size="small"
        >
          {{ statusLabel(row.status) }}
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
        <el-table-column label="操作" width="220" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
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
            :type="idx === history_items.length - 1 ? 'primary' : 'success'"
            :timestamp="formatDate(item.created_at)"
            placement="top"
          >
            <el-card class="history-item">
              <div class="history-item__header">
                <span class="history-item__seq">
                  <AppIcon icon="mdi:counter" style="margin-right: 4px;" />
                  seq_idx = {{ item.sequence_index ?? item.seq_idx ?? '-' }}
                </span>
                <el-tag size="small" type="info">
                  parameter_id = {{ item.id ?? '-' }}
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
/**
 * 优化记录列表数据流：
 * - 列表查询走 processParameterMethod.get（BaseRequest 实例），URL = /api/processes/parameter/
 * - 列表字段顺序/列显隐/密度/pageSize 通过 view-name="optimization_list" 持久化
 * - 调机历史：调用 /api/processes/optimization/<id>/history/（后端已有 get_optimization_history）
 *
 * 后端响应结构（main_service.get_process_parameter_list）：
 *   {
 *     id, condition_no, status, origin_type,
 *     mold_no, mold_name, mold_type, cavity_layout, product_category,
 *     machine_brand, machine_model, machine_device_code,
 *     polymer_abbreviation, polymer_grade,
 *     shot_index, injection_index,
 *     parameters_count,  // 2026-09-23 加：调机轮次数
 *     created_at, updated_at
 *   }
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import ProcessSearchForm from '@/views/process/parameter/components/ProcessSearchForm.vue'
import { processParameterMethod, processParameterBatchDelete } from '@/api'

// ============================================================================
// 类型
// ============================================================================

interface ListData {
  total: number
  items: any[]
}

interface HistoryItem {
  id?: number
  sequence_index?: number
  seq_idx?: number
  created_at?: string
  inj_pres_1?: number | null
  hold_t_1?: number | null
  cool_t?: number | null
  brl_temp_1?: number | null
  [k: string]: any
}

// ============================================================================
// 路由
// ============================================================================

const router = useRouter()

// ============================================================================
// 列表状态
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
// 列定义（调机视角，凸显 parameters_count）
// ============================================================================

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
// 列表数据加载
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
    console.error('[OptimizationList] fetchList failed:', err)
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
// 调机历史 dialog
// ============================================================================

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
    const res: any = await request({
      url: `/api/processes/optimization/${row.id}/history/`,
      method: 'get',
    })
    if (res?.status === 0) {
      const data = res.data
      // 后端历史接口可能返回 list 或 {items: [...]}；都兼容
      history_items.value = Array.isArray(data) ? data : (data?.items ?? [])
    } else {
      ElMessage.error(res?.msg || '加载调机历史失败')
    }
  } catch (err) {
    console.error('[OptimizationList] openHistory failed:', err)
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

// ============================================================================
// 操作
// ============================================================================

function goCreate() {
  router.push('/process/optimization')
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
    const res: any = await processParameterBatchDelete([row.id])
    if (res?.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res?.msg || '删除失败')
    }
  } catch (err) {
    console.error('[OptimizationList] deleteOne failed:', err)
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
    const res: any = await processParameterBatchDelete(ids)
    if (res?.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 条记录`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res?.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[OptimizationList] batchDelete failed:', err)
  }
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.optimization-list {
  padding: 16px;
}

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
}

:deep(.row-action-buttons) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.text-danger {
  color: var(--el-color-danger);
}
</style>