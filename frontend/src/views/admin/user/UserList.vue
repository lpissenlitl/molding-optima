<!--
  用户管理 - 列表页
  - 搜索（用户名、姓名、状态）
  - 列表（账号、姓名、邮箱、电话、状态、租户管理员、超级管理员、最后登录）
  - 操作列：编辑、重置密码、启用/禁用、删除
  - 批量删除
  - 新建用户（弹窗）
-->
<template>
  <div class="user-list">
    <!-- 搜索栏 -->
    <div class="search-container">
      <el-form
        class="search-form"
        :inline="true"
        :model="query"
        size="default"
        @submit.prevent="fetchList"
      >
        <el-form-item label="账号">
          <el-input
            v-model="query.username"
            placeholder="输入账号"
            clearable
            style="width: 160px;"
            @keyup.enter="fetchList"
          />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input
            v-model="query.engineer_name"
            placeholder="输入姓名"
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
            <el-option label="正常" :value="true" />
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
      view-name="user_list"
      :external-unique-values="externalUniqueValues"
      @size-change="(v: number) => { query.page_size = v; query.page_no = 1; fetchList() }"
      @current-change="(v: number) => { query.page_no = v; fetchList() }"
      @row-dblclick="editUser"
      @selection-change="(rows: any[]) => selected_rows = rows"
    >
      <!-- 顶部工具栏 -->
      <template #toolbar>
        <el-button
          type="success"
          @click="addUser"
        >
          <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 14px;" />
          新增用户
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

      <!-- 账号列：可点击跳转编辑 -->
      <template #cell-username="{ row }">
        <el-link type="primary" @click="editUser(row)">{{ row.username }}</el-link>
      </template>

      <!-- 状态列：直接切换（点击即生效，失败自动回滚） -->
      <template #cell-is_active="{ row }">
        <el-switch
          :model-value="row.is_active"
          :loading="row._toggle_loading"
          @change="(val: boolean) => toggleActive(row, val)"
        />
      </template>

      <!-- 租户管理员列 -->
      <template #cell-is_tenant_admin="{ row }">
        <el-tag v-if="row.is_tenant_admin" type="success" size="small">是</el-tag>
        <span v-else style="color: #c0c4cc;">否</span>
      </template>

      <!-- 超级管理员列 -->
      <template #cell-is_superuser="{ row }">
        <el-tag v-if="row.is_superuser" type="success" size="small">是</el-tag>
        <span v-else style="color: #c0c4cc;">否</span>
      </template>

      <!-- 最后登录时间 -->
      <template #cell-last_login_at="{ row }">
        <span>{{ formatDate(row.last_login_at) || '—' }}</span>
      </template>

      <!-- 行操作列 -->
      <template #append-columns>
        <el-table-column label="操作" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <span class="row-action-buttons">
              <el-button type="text" @click="editUser(row)"><AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />编辑</el-button>
              <el-button type="text" @click="resetPwd(row)"><AppIcon icon="mdi:key-variant" style="margin-right: 4px; font-size: 14px;" />重置密码</el-button>
              <el-button type="text"
                class="text-danger"
                @click="deleteUser(row)"
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
    <UserFormDrawer
      v-model:visible="drawer_visible"
      :id="editing_id"
      @success="onDialogSuccess"
    />

    <!-- 重置密码弹窗 -->
    <el-dialog
      v-model="reset_pwd_visible"
      title="重置密码"
      width="420px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form :model="reset_pwd_form" label-width="80px">
        <el-form-item label="账号">
          <span>{{ reset_pwd_form.username }}</span>
        </el-form-item>
        <el-form-item label="新密码" required>
          <el-input
            v-model="reset_pwd_form.password"
            type="password"
            show-password
            placeholder="至少 8 位，包含字母和数字"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reset_pwd_visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="reset_pwd_loading"
          @click="confirmResetPwd"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable, { type BaseTableColumn } from '@/components/BaseTable.vue'
import UserFormDrawer from './UserFormDrawer.vue'
import {
  userMethod,
  enableUser,
  disableUser,
  resetPassword,
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
  username: '',
  engineer_name: '',
  is_active: undefined as boolean | undefined,
})

const list_data = ref<ListData>({ total: 0, items: [] })
const list_loading = ref(false)
const table_size = ref<'small' | 'default' | 'large'>('default')
const selected_rows = ref<any[]>([])

// 列定义
const table_columns = ref<BaseTableColumn[]>([
  { visible: true, label: '账号', prop: 'username', minWidth: 120, align: 'center', sortable: true, tooltip: false, filterable: false },
  { visible: true, label: '姓名', prop: 'engineer_name', minWidth: 100, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '邮箱', prop: 'email', minWidth: 180, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '电话', prop: 'phone', minWidth: 120, align: 'center', sortable: false, tooltip: true, filterable: false },
  { visible: true, label: '启用', prop: 'is_active', minWidth: 90, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '租户管理员', prop: 'is_tenant_admin', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '超级管理员', prop: 'is_superuser', minWidth: 100, align: 'center', sortable: false, tooltip: false, filterable: false },
  { visible: true, label: '最后登录', prop: 'last_login_at', minWidth: 180, align: 'center', sortable: true, tooltip: true, filterable: false },
])

/** 外部数据库唯一值（用于列筛选项） */
const externalUniqueValues = ref<Record<string, any[]>>({})

// ============================================================================
// API 调用
// ============================================================================

/**
 * 获取用户列表
 */
async function fetchList() {
  list_loading.value = true
  try {
    const res: any = await userMethod.get({
      page_no: query.page_no,
      page_size: query.page_size,
      username: query.username || undefined,
      engineer_name: query.engineer_name || undefined,
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
    console.error('[UserList] fetchList failed:', err)
  } finally {
    list_loading.value = false
  }
}

/**
 * 重置搜索条件
 */
function resetQuery() {
  query.username = ''
  query.engineer_name = ''
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
    is_tenant_admin: collect('is_tenant_admin'),
    is_superuser: collect('is_superuser'),
  }
}

// ============================================================================
// 用户操作（弹窗 / 启用 / 禁用 / 删除）
// ============================================================================

const drawer_visible = ref(false)
const is_create = ref(true)
const editing_id = ref<number | null>(null)

/** 新建用户 */
function addUser() {
  is_create.value = true
  editing_id.value = null
  drawer_visible.value = true
}

/** 编辑用户 */
function editUser(row: any) {
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
  const api = enable ? enableUser : disableUser
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
    console.error(`[UserList] toggleActive ${action} failed:`, err)
    ElMessage.error(`${action}失败`)
  } finally {
    row._toggle_loading = false
  }
}

/** 删除单个用户 */
async function deleteUser(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除用户 "${row.username}" 吗？此操作不可恢复！`,
      '删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }

  try {
    const res: any = await userMethod.delete(row.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      fetchList()
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[UserList] deleteUser failed:', err)
  }
}

/** 批量删除 */
async function batchDelete() {
  const ids = selected_rows.value.map((r) => r.id)
  if (ids.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${ids.length} 个用户吗？此操作不可恢复！`,
      '批量删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }

  try {
    const res: any = await userMethod.multipleDelete({ ids })
    if (res.status === 0) {
      ElMessage.success(`成功删除 ${ids.length} 个用户`)
      selected_rows.value = []
      fetchList()
    } else {
      ElMessage.error(res.msg || '批量删除失败')
    }
  } catch (err) {
    console.error('[UserList] batchDelete failed:', err)
  }
}

// ============================================================================
// 重置密码
// ============================================================================

const reset_pwd_visible = ref(false)
const reset_pwd_loading = ref(false)
const reset_pwd_form = reactive({
  user_id: 0,
  username: '',
  password: '',
})

function resetPwd(row: any) {
  reset_pwd_form.user_id = row.id
  reset_pwd_form.username = row.username
  reset_pwd_form.password = ''
  reset_pwd_visible.value = true
}

async function confirmResetPwd() {
  if (!reset_pwd_form.password || reset_pwd_form.password.length < 8) {
    ElMessage.warning('密码至少 8 位')
    return
  }

  reset_pwd_loading.value = true
  try {
    const res: any = await resetPassword(reset_pwd_form.user_id, {
      password: reset_pwd_form.password,
    })
    if (res.status === 0) {
      ElMessage.success('密码重置成功')
      reset_pwd_visible.value = false
    } else {
      ElMessage.error(res.msg || '重置失败')
    }
  } catch (err) {
    console.error('[UserList] resetPwd failed:', err)
  } finally {
    reset_pwd_loading.value = false
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
.user-list {
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
</style>