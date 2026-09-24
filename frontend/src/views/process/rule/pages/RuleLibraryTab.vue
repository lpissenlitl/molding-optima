<!--
  RuleLibraryTab.vue - 规则库 tab 内容
  - 父组件 RuleLibraryList 通过 v-show 控制显示（保持组件存活）
  - 接收 activeTab + isSuperuser props
  - 自己 watch activeTab 决定是否加载数据
  - 不写 scoped style：复用全局 custom-form.scss 样式（.search-container / .search-form / .search-actions）
-->
<template>
  <div class="tab-panel">
    <!-- 搜索卡片 -->
    <div class="search-container">
      <el-form :inline="true" class="search-form">
        <el-form-item label="库名称">
          <el-input
            v-model="libraryQuery.library_name"
            placeholder="搜索库名称"
            clearable
            style="width: 180px"
            @keyup.enter="loadLibraries"
          />
        </el-form-item>
        <el-form-item label="归属">
          <el-select v-model="libraryQuery.owner_type" clearable placeholder="全部" style="width: 120px">
            <el-option label="系统级" value="system" />
            <el-option label="租户级" value="tenant" />
          </el-select>
        </el-form-item>
        <el-form-item label="库类型">
          <el-select v-model="libraryQuery.library_type" clearable placeholder="全部" style="width: 140px">
            <el-option label="专家规则库" value="expert" />
            <el-option label="模糊规则库" value="fuzzy" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="libraryQuery.is_active" clearable placeholder="全部" style="width: 100px">
            <el-option :label="'启用'" :value="true" />
            <el-option :label="'禁用'" :value="false" />
          </el-select>
        </el-form-item>
        <!-- 三个动作按钮合并到同一个 form-item：搜索 + 重置 + 新建 -->
        <el-form-item class="search-actions">
          <el-button type="primary" @click="loadLibraries">
            <AppIcon icon="mdi:magnify" :size="14" style="margin-right: 4px;" />
            搜索
          </el-button>
          <el-button @click="resetLibraryQuery">
            <AppIcon icon="mdi:refresh" :size="14" style="margin-right: 4px;" />
            重置
          </el-button>
          <el-button type="success" @click="showCreateLibraryDialog">
            <AppIcon icon="mdi:plus" :size="14" style="margin-right: 4px;" />
            新建规则库
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 卡片网格 -->
    <div v-loading="libraryLoading" class="card-grid">
      <template v-if="libraries.length > 0">
        <RuleLibraryCard
          v-for="lib in libraries"
          :key="lib.id"
          :library="lib"
          :is-superuser="isSuperuser"
          :is-readonly="isLibraryReadonly(lib)"
          @click="goLibraryDetail"
          @edit="showEditLibraryDialog"
          @delete="handleDeleteLibrary"
        />
      </template>
      <el-empty v-else-if="!libraryLoading" description="暂无规则库，点击右上角新建" />
    </div>

    <!-- 分页 -->
    <el-pagination
      v-if="libraryTotal > 0"
      class="pagination"
      layout="total, prev, pager, next"
      :current-page="libraryQuery.page_no"
      :page-size="libraryQuery.page_size"
      :total="libraryTotal"
      @current-change="onLibraryPageChange"
    />

    <!-- 新建/编辑规则库抽屉（子组件封装：RuleLibraryFormDrawer） -->
    <RuleLibraryFormDrawer
      v-model:visible="createLibraryVisible"
      :mode="libraryDialogMode"
      :form="libraryForm"
      :submitting="createLibrarySubmitting"
      @submit="submitCreateLibrary"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import RuleLibraryCard from '../components/RuleLibraryCard.vue'
import RuleLibraryFormDrawer, { type RuleLibraryFormData } from '../components/RuleLibraryFormDrawer.vue'
import { listRuleLibraries, createRuleLibrary, updateRuleLibrary, deleteRuleLibrary } from '@/api/rule'
import type {
  RuleLibrary,
  RuleLibraryCreatePayload,
} from '@/types/rule'

const props = defineProps<{
  /** 当前激活的 tab key（来自父组件）*/
  activeTab: 'libraries' | 'keywords'
  /** 是否超级管理员（控制专家规则是否展示）*/
  isSuperuser: boolean
}>()

// ============================================================================
// 状态
// ============================================================================
const libraries = ref<RuleLibrary[]>([])
const libraryTotal = ref(0)
const libraryLoading = ref(false)
const libraryQuery = reactive({
  library_name: '',
  owner_type: '' as '' | 'system' | 'tenant',
  library_type: '' as '' | 'expert' | 'fuzzy',
  is_active: undefined as boolean | undefined,
  page_no: 1,
  page_size: 12,
})

// ============================================================================
// 数据加载
// ============================================================================
async function loadLibraries() {
  libraryLoading.value = true
  try {
    const res: any = await listRuleLibraries({
      page_no: libraryQuery.page_no,
      page_size: libraryQuery.page_size,
      library_name: libraryQuery.library_name || undefined,
      owner_type: libraryQuery.owner_type || undefined,
      library_type: libraryQuery.library_type || undefined,
      is_active: libraryQuery.is_active,
    })
    libraries.value = res.data?.items || res.items || []
    libraryTotal.value = res.data?.total ?? res.total ?? 0
  } catch (e) {
    libraries.value = []
    libraryTotal.value = 0
  } finally {
    libraryLoading.value = false
  }
}

function resetLibraryQuery() {
  libraryQuery.library_name = ''
  libraryQuery.owner_type = ''
  libraryQuery.library_type = ''
  libraryQuery.is_active = undefined
  libraryQuery.page_no = 1
  loadLibraries()
}

function onLibraryPageChange(p: number) {
  libraryQuery.page_no = p
  loadLibraries()
}

// ============================================================================
// 新建/编辑规则库抽屉
// ============================================================================
const createLibraryVisible = ref(false)
const createLibrarySubmitting = ref(false)
const libraryDialogMode = ref<'create' | 'edit'>('create')
const libraryEditId = ref<number>(0)
const libraryForm = reactive<RuleLibraryFormData>({
  library_code: '',
  library_name: '',
  owner_type: 'tenant',
  library_type: 'expert',
  priority: 100,
  version: 1,
  is_active: true,
  description: '',
})

function showCreateLibraryDialog() {
  libraryDialogMode.value = 'create'
  libraryEditId.value = 0
  libraryForm.library_code = ''
  libraryForm.library_name = ''
  libraryForm.owner_type = 'tenant'
  libraryForm.library_type = 'expert'
  libraryForm.priority = 100
  libraryForm.version = 1
  libraryForm.is_active = true
  libraryForm.description = ''
  createLibraryVisible.value = true
}

function showEditLibraryDialog(lib: RuleLibrary) {
  libraryDialogMode.value = 'edit'
  libraryEditId.value = lib.id
  libraryForm.library_code = lib.library_code
  libraryForm.library_name = lib.library_name
  libraryForm.owner_type = lib.owner_type
  libraryForm.library_type = lib.library_type
  libraryForm.priority = lib.priority
  libraryForm.version = lib.version
  libraryForm.is_active = lib.is_active
  libraryForm.description = lib.description || ''
  createLibraryVisible.value = true
}

async function submitCreateLibrary() {
  createLibrarySubmitting.value = true
  try {
    if (libraryDialogMode.value === 'create') {
      await createRuleLibrary({ ...libraryForm })
      ElMessage.success('规则库创建成功')
    } else {
      // 编辑模式：库编码 / 归属 / 库类型在子组件里被 disabled，不可改
      // 这里只提交子组件允许编辑的字段
      const payload: Partial<RuleLibraryCreatePayload> = {
        library_name: libraryForm.library_name,
        priority: libraryForm.priority,
        version: libraryForm.version,
        is_active: libraryForm.is_active,
        description: libraryForm.description,
      }
      await updateRuleLibrary(libraryEditId.value, payload)
      ElMessage.success('规则库更新成功')
    }
    createLibraryVisible.value = false
    loadLibraries()
  } catch (e) {
    // 拦截器已统一提示
  } finally {
    createLibrarySubmitting.value = false
  }
}

async function handleDeleteLibrary(lib: RuleLibrary) {
  try {
    await ElMessageBox.confirm(
      `确认删除规则库？\n${lib.library_name}（${lib.library_code}）\n\n该操作会级联软删除库下所有规则方法和专家规则。`,
      '删除规则库',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await deleteRuleLibrary(lib.id)
    ElMessage.success('规则库已删除')
  } catch (e) {
    // 拦截器已统一提示
  }
}

// 系统库对非超管只读：超管可编辑/删除所有库（含系统库），普通用户只能操作租户库
// 后端已强制限制，这里只是 UI 层的视觉信号
const isLibraryReadonly = (lib: RuleLibrary) =>
  lib.owner_type === 'system' && !props.isSuperuser

// ============================================================================
// 路由跳转
// ============================================================================
const router = useRouter()
function goLibraryDetail(lib: RuleLibrary) {
  router.push(`/process/rules/${lib.id}`)
}

// ============================================================================
// 生命周期：按需加载
// ============================================================================
// 父组件用 v-show，子组件始终挂载。仅在首次激活 / 切回激活时加载数据
onMounted(() => {
  if (props.activeTab === 'libraries') {
    loadLibraries()
  }
})

watch(() => props.activeTab, (val, oldVal) => {
  if (val === 'libraries' && oldVal !== 'libraries' && libraries.value.length === 0) {
    loadLibraries()
  }
})
</script>

<!--
  本组件不写 scoped style：表单字段提示样式（.field-tip）已在子组件 RuleLibraryFormDrawer 内定义。
-->
<style lang="scss">
</style>