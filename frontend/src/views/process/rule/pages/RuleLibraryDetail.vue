<!-- RuleLibraryDetail.vue - 规则库详情页（瘦身后的调度组件） -->
<template>
  <div class="rule-library-detail" v-loading="libraryLoading">
    <!-- 顶部导航 -->
    <div class="page-header">
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

    <!-- 内容区：根据库类型渲染对应的 section（v-if 直接分支渲染，避开 el-tabs 切换；每个 library_type 仅对应一个 section） -->
    <div v-if="library" class="rule-content">
      <RuleMethodSection
        v-if="library.library_type === 'fuzzy'"
        :library-id="libraryId"
        :is-superuser="canPromote"
        @changed="loadLibrary"
      />
      <ExpertRuleSection
        v-else-if="library.library_type === 'expert' && isSuperuser"
        :library-id="libraryId"
        @changed="loadLibrary"
      />
      <el-alert
        v-else-if="library.library_type === 'expert'"
        class="expert-readonly-hint"
        type="info"
        :closable="false"
        show-icon
        title="专家规则由平台超管维护"
        description="专家规则是工艺参数初始化系数，属平台级资产：仅平台超管可查看与维护，租户私有专家库同样由超管代办维护。"
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

// 角色判断：专家规则属平台级内部规则，仅 superadmin 可见（后端已加 require_superuser 二次防护）
const isSuperuser = computed(() => userStore.is_superuser)

// 晋升入口（仅平台超管 + 租户级私库的模糊规则）
// ⚠️ **系统库里的规则本就是公共资产**，无需晋升；专家规则走另一条链路，也不支持
const canPromote = computed(() =>
  isSuperuser.value
  && library.value?.owner_type === 'tenant'
  && library.value?.library_type === 'fuzzy',
)

// 路由参数

const libraryId = computed(() => Number(route.params.libraryId))

// 规则库元信息

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
  target_company_id: null,
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

// 初始化

onMounted(() => {
  loadLibrary()
})
</script>

<style scoped>
.rule-library-detail {
  padding: 16px;
  display: flex;
  flex-direction: column;
  /* 关键：高度 100% 让 flex 子项能撑开（祖先链 .layout__content { flex: 1; min-height: 0; overflow: auto; } 是计算高度的源头） */
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

/* 内容区容器：与原 .rule-tabs 视觉风格保持一致（白底 + padding + 圆角） */
.rule-content {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
  /* flex: 1 + min-height: 0 吃掉所有剩余空间 */
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}

/* 专家规则只读提示：内容区垂直居中，避免顶部孤零零一条 alert */
.expert-readonly-hint {
  margin-top: 48px;
}
</style>