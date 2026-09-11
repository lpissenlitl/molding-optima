<!--
  角色管理 - 列表页
  - 搜索（角色名称、状态）
  - 列表（名称、编码、描述、状态）
  - 操作列：编辑、启用/禁用、删除
  - 批量删除
  - 新建/编辑角色（弹窗，含权限树选择）
-->
<template>
  <div class="role-list">
    <!-- 搜索栏 -->
    <div class="search-container">
      <el-form
        class="search-form"
        :inline="true"
        :model="query"
        size="default"
        @submit.prevent="fetchList"
      >
        <el-form-item label="角色名称">
          <el-input
            v-model="query.name"
            placeholder="输入角色名称"
            clearable
            style="width: 180px;"
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
      view-name="role_list"
      :external-unique-values="externalUniqueValues"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="editRole"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <!-- 顶部工具栏 -->
      <template #toolbar>
        <el-button
          type="primary"
          @click="addRole"
        >
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          新增角色
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

      <!-- 名称列：可点击编辑 -->
      <template #cell-name="{ row }">
        <el-link type="primary" @click="editRole(row)">{{ row.name }}</el-link>
      </template>

      <!-- 编码列：等宽字体 -->
      <template #cell-code="{ row }">
        <span class="code-text">{{ row.code || '—' }}</span>
      </template>

      <!-- 描述列：超出省略 -->
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

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="editRole(row)"><AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />编辑</el-button>
              <el-button type="text"
                class="text-danger"
                @click="deleteRole(row)"
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
    <RoleFormDrawer
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
import RoleFormDrawer from './RoleFormDrawer.vue'
import {
  roleMethod,
  enableRole,
  disableRole,
} from '@/api'

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
  is_active: undefined as boolean | undefined,
})

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const table_size = ref<'small' | 'default' | 'large'>('default')
const selected_rows = ref<any[]>([])

// 列定义（后端 to_dict 不返回 permission_count，需要时调用详情接口获取）
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '角色名称', prop: 'name', minWidth: 140, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '角色编码', prop: 'code', minWidth: 140, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '描述', prop: 'description', minWidth: 240, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '启用', prop: 'is_active', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
])

/** 外部数据库唯一值（用于列筛选项） */
const externalUniqueValues = ref<Record<string, any[]>>({})

// ============================================================================
// API 调用
// ============================================================================

/**
 * 获取角色列表
 */
async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await roleMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      name: query.name || undefined,
      is_active: query.is_active,
    } as any)
    if (res.status === 0) {
      list_data.value = res.data
      // 同步唯一值用于列筛选
      syncExternalUniqueValues()
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    // request 拦截器已统一处理错误
    console.error('[RoleList] fetchList failed:', err)
  } finally {
    list_loading.value = false
  }
}

/**
 * 重置搜索条件
 */
function resetQuery() {
  query.name = ''
  query.is_active = undefined
  query.page_no = 1
  fetchList()
}

/**
 * 从列表数据同步唯一值（用于列筛选弹窗）
 */
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
  }
}

// ============================================================================
// 角色操作（弹窗 / 启用 / 禁用 / 删除）
// ============================================================================

const drawer_visible = ref(false)
const is_create = ref(true)
const editing_id = ref<number | null>(null)

/** 新建角色 */
function addRole() {
  is_create.value = true
  editing_id.value = null
  drawer_visible.value = true
}

/** 编辑角色 */
function editRole(row: any) {
  is_create.value = false
  editing_id.value = row.id
  drawer_visible.value = true
}

/** 表单提交成功回调 */
function onDialogSuccess() {
  drawer_visible.value = false
  fetchList()
}

/** 切换启用/禁用（乐观更新，失败回滚） */
async function toggleActive(row: any, enable: boolean) {
  const prev = row.is_active
  row.is_active = enable
  row._toggle_loading = true

  const action = enable ? '启用' : '禁用'
  const api = enable ? enableRole : disableRole
  try {
    const res: any = await api(row.id)
    if (res.status === 0) {
      ElMessage.success(`${action}成功`)
    } else {
      row.is_active = prev
      ElMessage.error(res.msg || `${action}失败`)
    }
  } catch (err) {
    row.is_active = prev
    console.error(`[RoleList] toggleActive ${action} failed:`, err)
    ElMessage.error(`${action}失败`)
  } finally {
    row._toggle_loading = false
  }
}

/** 删除单个角色 */
async function deleteRole(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除角色 "${row.name}" 吗？此操作不可恢复！`,
      '删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }

  try {
    const res: any = await roleMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[RoleList] deleteRole failed:', err)
  }
}

/** 批量删除 */
async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${ids.length} 个角色吗？此操作不可恢复！`,
      '批量删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }

  try {
    const res: any = await roleMethod.multipleDelete({ ids })
    if (res.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 个角色`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[RoleList] batchDelete failed:', err)
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
.role-list {
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

/* 自定义 tag */
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

/* 文字色 */
.text-warning {
  color: #e6a23c;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

/* 等宽字体显示编码 */
.code-text {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: #606266;
}
</style>