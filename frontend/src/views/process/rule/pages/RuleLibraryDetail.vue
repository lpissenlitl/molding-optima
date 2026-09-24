<!--
  RuleLibraryDetail.vue - 规则库详情页（瘦身后的调度组件）

  布局：
  - 顶部：返回按钮 + 库元信息卡片
  - 内容区：根据 library_type 渲染对应 section（RuleMethod / ExpertRule）
  - 编辑规则库弹窗

  路由：/process/rules/:libraryId

  职责拆分：
  - 本组件只负责：库元信息 + 调度子组件
  - 模糊规则 section → RuleMethodSection.vue
  - 专家规则 section → ExpertRuleSection.vue
-->
<template>
  <div class="rule-library-detail" v-loading="libraryLoading">
    <!-- 顶部导航 -->
    <div class="page-header">
      <el-button text @click="goBack">
        <el-icon style="margin-right: 4px"><ArrowLeft /></el-icon>
        返回列表
      </el-button>
      <div class="page-title">
        <h2>{{ library?.library_name || '规则库详情' }}</h2>
        <el-tag v-if="library" :type="library.owner_type === 'system' ? 'info' : 'success'">
          {{ library.owner_type === 'system' ? '系统级' : '租户级' }}
        </el-tag>
        <el-tag v-if="library" :type="library.is_active ? 'success' : 'info'">
          {{ library.is_active ? '已启用' : '已禁用' }}
        </el-tag>
      </div>
      <div class="page-actions">
        <el-button :disabled="!library" @click="showEditLibraryDialog">
          <el-icon style="margin-right: 4px"><Edit /></el-icon>
          编辑
        </el-button>
        <el-button type="danger" :disabled="!library || library.owner_type === 'system'" @click="deleteLibrary">
          <el-icon style="margin-right: 4px"><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 库元信息卡片 -->
    <el-card v-if="library" class="library-info-card">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="库编码">
          <span class="mono">{{ library.library_code }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="库编号">
          {{ library.library_no || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="版本">v{{ library.version }}</el-descriptions-item>
        <el-descriptions-item label="优先级">{{ library.priority }}</el-descriptions-item>
        <el-descriptions-item label="归属">{{ library.owner_type === 'system' ? '系统级' : '租户级' }}</el-descriptions-item>
        <el-descriptions-item label="库类型">
          {{ library.library_type === 'fuzzy' ? '模糊规则库' : '专家规则库' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">{{ library.is_active ? '启用' : '禁用' }}</el-descriptions-item>
        <el-descriptions-item label="规则数量">
          {{ library.library_type === 'fuzzy'
              ? `${library.method_count ?? 0} 条规则方法`
              : `${library.expert_rule_count ?? 0} 条专家规则` }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="3">
          {{ library.description || '—' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 内容区：根据库类型渲染对应的 section
         用 v-if 直接分支渲染，避开 el-tabs 切换的复杂性。
         （每个 library_type 仅对应一个 section，无需 Tab 切换） -->
    <div v-if="library" class="rule-content">
      <RuleMethodSection
        v-if="library.library_type === 'fuzzy'"
        :library-id="libraryId"
        @changed="loadLibrary"
      />
      <ExpertRuleSection
        v-else-if="library.library_type === 'expert'"
        :library-id="libraryId"
        :is-superuser="isSuperuser"
        @changed="loadLibrary"
      />
    </div>

    <!-- 编辑规则库抽屉（子组件封装：RuleLibraryFormDrawer） -->
    <RuleLibraryFormDrawer
      v-model:visible="editLibraryVisible"
      mode="edit"
      :form="libraryForm"
      :submitting="editLibrarySubmitting"
      @submit="submitEditLibrary"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete } from '@element-plus/icons-vue'
import { getRuleLibrary, updateRuleLibrary, deleteRuleLibrary as apiDeleteRuleLibrary } from '@/api/rule'
import type { RuleLibrary, RuleLibraryCreatePayload } from '@/types/rule'
import { useUserStore } from '@/stores/user'
import RuleMethodSection from '../components/RuleMethodSection.vue'
import ExpertRuleSection from '../components/ExpertRuleSection.vue'
import RuleLibraryFormDrawer, { type RuleLibraryFormData } from '../components/RuleLibraryFormDrawer.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// ============================================================================
// 角色判断
// ============================================================================
//
// 专家规则（ExpertRule）属于平台级内部规则（工艺参数初始化系数），
// 不向租户展示，只有超级管理员才能查看/编辑。
// 后端 ExpertRuleListByLibraryView / ExpertRuleDetailView 已加 require_superuser 装饰器做二次防护。
const isSuperuser = computed(() => userStore.is_superuser)

// ============================================================================
// 路由参数
// ============================================================================

const libraryId = computed(() => Number(route.params.libraryId))

// ============================================================================
// 规则库元信息
// ============================================================================

const library = ref<RuleLibrary | null>(null)
const libraryLoading = ref(false)

async function loadLibrary() {
  if (!libraryId.value) return
  libraryLoading.value = true
  try {
    const res: any = await getRuleLibrary(libraryId.value)
    // 后端响应统一为 { status, msg, data: ... }
    library.value = res.data || res
  } catch {
    library.value = null
  } finally {
    libraryLoading.value = false
  }
}

// 编辑规则库
const editLibraryVisible = ref(false)
const editLibrarySubmitting = ref(false)
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

function showEditLibraryDialog() {
  if (!library.value) return
  libraryForm.library_code = library.value.library_code
  libraryForm.library_name = library.value.library_name
  libraryForm.owner_type = library.value.owner_type
  libraryForm.library_type = library.value.library_type
  libraryForm.priority = library.value.priority
  libraryForm.version = library.value.version
  libraryForm.is_active = library.value.is_active
  libraryForm.description = library.value.description || ''
  editLibraryVisible.value = true
}

async function submitEditLibrary() {
  editLibrarySubmitting.value = true
  try {
    const payload: Partial<RuleLibraryCreatePayload> = {
      library_name: libraryForm.library_name,
      priority: libraryForm.priority,
      version: libraryForm.version,
      is_active: libraryForm.is_active,
      description: libraryForm.description,
    }
    // 非系统级可改归属；系统级归属锁定，不传 owner_type
    if (libraryForm.owner_type !== 'system') {
      payload.owner_type = libraryForm.owner_type
    }
    await updateRuleLibrary(libraryId.value, payload)
    ElMessage.success('保存成功')
    editLibraryVisible.value = false
    loadLibrary()
  } catch {
    /* 拦截器已提示 */
  } finally {
    editLibrarySubmitting.value = false
  }
}

async function deleteLibrary() {
  if (!library.value) return
  try {
    await ElMessageBox.confirm(
      `确认删除规则库「${library.value.library_name}」？\n该操作将级联软删除库下所有规则方法和专家规则。`,
      '删除规则库',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await apiDeleteRuleLibrary(libraryId.value)
    ElMessage.success('删除成功')
    goBack()
  } catch {
    /* 拦截器已提示 */
  }
}

function goBack() {
  router.push('/process/rules')
}

// ============================================================================
// 初始化
// ============================================================================

onMounted(() => {
  loadLibrary()
})
</script>

<style scoped>
.rule-library-detail {
  padding: 16px;
  display: flex;
  flex-direction: column;
  /*
   * 关键：高度 100% 让 flex 子项能撑开。
   * 祖先链 .layout__content { flex: 1; min-height: 0; overflow: auto; }
   * 是计算高度的源头。
   */
  height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
  flex-shrink: 0;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.page-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.page-actions {
  display: flex;
  gap: 8px;
}

.library-info-card {
  margin-bottom: 16px;
  flex-shrink: 0;
}

/*
 * 内容区容器：与原 .rule-tabs 视觉风格保持一致（白底 + padding + 圆角）
 * 搜索表单样式 .search-container / .search-form / .search-actions
 * 来自 src/styles/utilities/custom-form.scss（全局）
 */
.rule-content {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
  /*
   * flex: 1 + min-height: 0 吃掉所有剩余空间
   * 子组件（RuleMethodSection / ExpertRuleSection）会基于此高度
   * 内部进一步 flex 分配（搜索 / 表格 / 分页）
   */
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}
</style>