<!--
  公司管理 - 列表页
  - 搜索（公司名称、所属行业、状态）
  - 列表（公司名称、编码、行业、层级、状态、创建时间）
  - 操作列：编辑、启用/禁用、删除、接管、释放
  - 批量删除
  - 新建/编辑公司（弹窗，含公司管理员子表单）
-->
<template>
  <div class="company-list">
    <!-- 搜索栏 -->
    <div class="search-container">
      <el-form
        class="search-form"
        :inline="true"
        :model="query"
        size="default"
        @submit.prevent="fetchList"
      >
        <el-form-item label="公司名称">
          <el-input
            v-model="query.name"
            placeholder="输入公司名称"
            clearable
            style="width: 180px;"
            @keyup.enter="fetchList"
          />
        </el-form-item>
        <el-form-item label="所属行业">
          <el-input
            v-model="query.industry"
            placeholder="输入行业"
            clearable
            style="width: 160px;"
            @keyup.enter="fetchList"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="query.is_active"
            placeholder="全部"
            clearable
            style="width: 120px;"
          >
            <el-option label="启用" :value="true" />
            <el-option label="已禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item class="search-actions">
          <el-button type="primary" @click="fetchList">
            <AppIcon icon="mdi:magnify" style="margin-right: 4px; font-size: 14px;" />
            搜索
          </el-button>
          <el-button @click="resetQuery">
            <AppIcon icon="mdi:refresh" style="margin-right: 4px; font-size: 14px;" />
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 表格 -->
    <BaseTable
      :data="list_data.items"
      :total="list_data.total"
      :query="query"
      :columns.sync="table_columns"
      :loading="list_loading"
      :table-size.sync="table_size"
      :height-offset="240"
      view-name="company_list"
      :external-unique-values="externalUniqueValues"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="editCompany"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <!-- 顶部工具栏 -->
      <template #toolbar>
        <el-button
          type="primary"
          @click="addCompany"
        >
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          新增公司
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

      <!-- 公司名称：可点击编辑 -->
      <template #cell-name="{ row }">
        <el-link type="primary" @click="editCompany(row)">{{ row.name }}</el-link>
      </template>

      <!-- 编码列：等宽字体 -->
      <template #cell-code="{ row }">
        <span class="code-text">{{ row.code || '—' }}</span>
      </template>

      <!-- 行业列 -->
      <template #cell-industry="{ row }">
        <span>{{ row.industry || '—' }}</span>
      </template>

      <!-- 层级列：custom-tag（统一胶囊 + 圆点） -->
      <template #cell-tier_level="{ row }">
        <span v-if="row.tier_level >= 3" class="custom-tag tag-warning">
          L{{ row.tier_level }}
        </span>
        <span v-else-if="row.tier_level === 2" class="custom-tag tag-success">
          L{{ row.tier_level }}
        </span>
        <span v-else class="custom-tag tag-info">
          L{{ row.tier_level }}
        </span>
      </template>

      <!-- 描述列 -->
      <template #cell-description="{ row }">
        <span>{{ row.description || '—' }}</span>
      </template>

      <!-- 状态列：直接切换（点击即生效，失败自动回滚） -->
      <template #cell-is_active="{ row }">
        <el-switch
          :model-value="row.is_active"
          :loading="row._toggle_loading"
          @change="(val: boolean) => toggleActive(row, val)"
        />
      </template>

      <!-- 接管列：互斥按钮（同一时刻只能接管一个企业） -->
      <template #cell-is_assumed="{ row }">
        <el-button
          v-if="userStore.company_id === row.id"
          link
          type="warning"
          :loading="row._assume_loading"
          @click="toggleAssume(row, false)"
        >
          <AppIcon icon="mdi:logout" style="margin-right: 4px; font-size: 14px;" />
          退出
        </el-button>
        <el-button
          v-else
          link
          type="primary"
          :loading="row._assume_loading"
          @click="toggleAssume(row, true)"
        >
          <AppIcon icon="mdi:login" style="margin-right: 4px; font-size: 14px;" />
          接管
        </el-button>
      </template>

      <!-- 创建时间 -->
      <template #cell-created_at="{ row }">
        <span>{{ formatDate(row.created_at) || '—' }}</span>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button
                type="text"
                @click="editCompany(row)"
              >
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
                编辑
              </el-button>
              <el-button
                type="text"
                class="text-danger"
                @click="deleteCompany(row)"
              >
                <AppIcon icon="mdi:delete-outline" style="margin-right: 4px; font-size: 14px;" />
                删除
              </el-button>
            </span>
          </template>
        </el-table-column>
      </template>
    </BaseTable>

    <!-- 新建/编辑抽屉 -->
    <CompanyFormDrawer
      v-model:visible="drawer_visible"
      :id="editing_id"
      @success="onDialogSuccess"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import CompanyFormDrawer from './CompanyFormDrawer.vue'
import {
  companyMethod,
  enableCompany,
  disableCompany,
  assumeCompany as assumeCompanyApi,
  releaseCompany as releaseCompanyApi,
} from '@/api'
import { useUserStore } from '@/stores/user'

// ============================================================================
// 列表数据
// ============================================================================

interface ListData {
  total: number
  items: any[]
}

const query = reactive({
  page_no: 1,
  page_size: 20,
  name: '',
  industry: '',
  is_active: undefined as boolean | undefined,
})

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const table_size = ref<'small' | 'default' | 'large'>('default')
const selected_rows = ref<any[]>([])

// 列定义
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '公司名称', prop: 'name', minWidth: 160, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '公司编码', prop: 'code', minWidth: 130, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '所属行业', prop: 'industry', minWidth: 130, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '权限等级', prop: 'tier_level', minWidth: 80, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '描述', prop: 'description', minWidth: 220, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '启用', prop: 'is_active', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: true },
  { visible: true, label: '切换身份', prop: 'is_assumed', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '创建时间', prop: 'created_at', minWidth: 160, align: 'center', sortable: true, tooltip: true, filterable: false },
])

/** 外部数据库唯一值（用于列筛选项） */
const externalUniqueValues = ref<Record<string, any[]>>({})

// ============================================================================
// API 调用
// ============================================================================

async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await companyMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      name: query.name || undefined,
      industry: query.industry || undefined,
      is_active: query.is_active,
    } as any)
    if (res.status === 0) {
      list_data.value = res.data
      syncExternalUniqueValues()
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[CompanyList] fetchList failed:', err)
  } finally {
    list_loading.value = false
  }
}

function resetQuery() {
  query.name = ''
  query.industry = ''
  query.is_active = undefined
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
    is_active: collect('is_active'),
    tier_level: collect('tier_level'),
  }
}

// ============================================================================
// 弹窗 / 操作
// ============================================================================

const drawer_visible = ref(false)
const is_create = ref(true)
const editing_id = ref<number | null>(null)

function addCompany() {
  is_create.value = true
  editing_id.value = null
  drawer_visible.value = true
}

function editCompany(row: any) {
  is_create.value = false
  editing_id.value = row.id
  drawer_visible.value = true
}

/** 表单提交成功回调 */
function onDialogSuccess() {
  drawer_visible.value = false
  fetchList()
}

async function toggleActive(row: any, enable: boolean) {
  // 乐观更新：UI 先反映新状态（el-switch 已经通过 :model-value 反映）
  const prev = row.is_active
  row.is_active = enable
  row._toggle_loading = true

  const action = enable ? '启用' : '禁用'
  const api = enable ? enableCompany : disableCompany
  try {
    const res: any = await api(row.id)
    if (res.status === 0) {
      ElMessage.success(`${action}成功`)
    } else {
      row.is_active = prev // 回滚
      ElMessage.error(res.msg || `${action}失败`)
    }
  } catch (err) {
    row.is_active = prev // 回滚
    console.error(`[CompanyList] toggleActive ${action} failed:`, err)
    ElMessage.error(`${action}失败`)
  } finally {
    row._toggle_loading = false
  }
}

async function deleteCompany(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除公司 "${row.name}" 吗？此操作不可恢复！`,
      '删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }

  try {
    const res: any = await companyMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[CompanyList] deleteCompany failed:', err)
  }
}

async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${ids.length} 个公司吗？此操作不可恢复！`,
      '批量删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }

  try {
    const res: any = await companyMethod.multipleDelete({ ids })
    if (res.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 个公司`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[CompanyList] batchDelete failed:', err)
  }
}

// ============================================================================
// 接管 / 释放租户上下文（单一开关列控制，单选语义）
// ============================================================================

const userStore = useUserStore()

/**
 * 切换接管状态
 * - enable=true  → 接管该公司（user.company_id = row.id）
 * - enable=false → 释放当前接管（user.company_id = null）
 */
async function toggleAssume(row: any, enable: boolean) {
  row._assume_loading = true
  const api = enable ? assumeCompanyApi : releaseCompanyApi

  try {
    const res: any = await api(row.id)
    if (res.status === 0) {
      // 同步更新 userStore（让全应用感知当前租户上下文变化）
      userStore.company_id = enable ? row.id : null
      userStore.is_tenant_admin = enable
      userStore.company_name = enable ? row.name : ''

      // 从后端重新拉完整用户信息（同步 organization_id / permissions 等字段）
      try {
        await userStore.fetchInfo()
      } catch (err) {
        console.error('[CompanyList] fetchInfo after assume failed:', err)
      }

      ElMessage.success(
        enable
          ? `已接管公司 "${row.name}"`
          : '已释放租户上下文'
      )
      // 刷新列表，让其他行的 switch 状态同步
      fetchList()
    } else {
      ElMessage.error(res.msg || '操作失败')
    }
  } catch (err) {
    console.error('[CompanyList] toggleAssume failed:', err)
    ElMessage.error('操作失败')
  } finally {
    row._assume_loading = false
  }
}

// ============================================================================
// 工具
// ============================================================================

function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return iso || ''
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
.company-list {
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

.custom-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
}

.tag-success {
  color: #67c23a;
  background-color: #f0f9eb;
}

.tag-danger {
  color: #f56c6c;
  background-color: #fef0f0;
}

.text-warning {
  color: #e6a23c;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.text-primary {
  color: #409eff;
}

.text-secondary {
  color: #909399;
  font-size: 13px;
}

.code-text {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #606266;
}
</style>
