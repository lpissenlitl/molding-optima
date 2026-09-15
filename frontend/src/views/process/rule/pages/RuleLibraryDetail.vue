<!--
  RuleLibraryDetail.vue - 规则库详情页

  布局：
  - 顶部：返回按钮 + 库元信息卡片
  - Tabs：规则方法（Tab 1）| 专家规则（Tab 2）

  路由：/process/rules/:libraryId
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
        <el-descriptions-item label="描述" :span="3">
          {{ library.description || '—' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Tabs -->
    <el-tabs v-model="activeTab" class="rule-tabs">
      <!-- Tab 1: 规则方法（仅模糊规则库显示）-->
      <el-tab-pane
        v-if="library?.library_type === 'fuzzy'"
        :label="`规则方法 (${library?.method_count ?? 0})`"
        name="methods"
      >
        <div class="tab-toolbar">
          <el-form :inline="true" class="search-bar">
            <el-form-item label="缺陷标识">
              <el-input
                v-model="methodQuery.defect_code"
                placeholder="搜索 defect_code"
                clearable
                style="width: 180px"
                @keyup.enter="loadMethods"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-select
                v-model="methodQuery.is_active"
                clearable
                placeholder="全部"
                style="width: 100px"
              >
                <el-option label="启用" :value="true" />
                <el-option label="禁用" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadMethods">搜索</el-button>
              <el-button @click="resetMethodQuery">重置</el-button>
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="showCreateMethodDialog">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>
            新建规则方法
          </el-button>
        </div>

        <el-table
          v-loading="methodLoading"
          :data="methods"
          border
          stripe
        >
          <el-table-column label="规则描述" prop="rule_description" min-width="240" show-overflow-tooltip />
          <el-table-column label="缺陷名称" prop="defect_label" width="120" show-overflow-tooltip />
          <el-table-column label="缺陷标识" prop="defect_code" width="120">
            <template #default="{ row }">
              <span class="mono">{{ row.defect_code || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="材料" prop="polymer_abbreviation" width="100" show-overflow-tooltip />
          <el-table-column label="优先级" prop="priority" width="80" align="center" />
          <el-table-column label="置信度" prop="confidence" width="80" align="center">
            <template #default="{ row }">
              {{ Number(row.confidence).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="来源" prop="source" width="100">
            <template #default="{ row }">
              <el-tag>{{ sourceLabel(row.source) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" prop="is_active" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="showEditMethodDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="deleteMethod(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="methodTotal > methodQuery.page_size"
          class="pagination"
          layout="total, prev, pager, next"
          :current-page="methodQuery.page_no"
          :page-size="methodQuery.page_size"
          :total="methodTotal"
          @current-change="onMethodPageChange"
        />
      </el-tab-pane>

      <!-- Tab 2: 专家规则（仅专家规则库显示）-->
      <el-tab-pane
        v-if="library?.library_type === 'expert'"
        :label="`专家规则 (${library?.expert_rule_count ?? 0})`"
        name="expert-rules"
      >
        <div class="tab-toolbar">
          <el-form :inline="true" class="search-bar">
            <el-form-item label="规则编码">
              <el-input
                v-model="expertQuery.rule_code"
                placeholder="搜索 rule_code"
                clearable
                style="width: 180px"
                @keyup.enter="loadExpertRules"
              />
            </el-form-item>
            <el-form-item label="状态">
              <el-select
                v-model="expertQuery.is_active"
                clearable
                placeholder="全部"
                style="width: 100px"
              >
                <el-option label="启用" :value="true" />
                <el-option label="禁用" :value="false" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadExpertRules">搜索</el-button>
              <el-button @click="resetExpertQuery">重置</el-button>
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="showCreateExpertRuleDialog">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>
            新建专家规则
          </el-button>
        </div>

        <el-table
          v-loading="expertLoading"
          :data="expertRules"
          border
          stripe
        >
          <el-table-column label="规则编码" prop="rule_code" width="160">
            <template #default="{ row }">
              <span class="mono">{{ row.rule_code }}</span>
            </template>
          </el-table-column>
          <el-table-column label="规则名称" prop="rule_name" min-width="200" show-overflow-tooltip />
          <el-table-column label="匹配条件" width="120" align="center">
            <template #default="{ row }">
              <el-tag v-if="!row.conditions || row.conditions.length === 0" type="info">默认</el-tag>
              <el-tag v-else>{{ row.conditions.length }} 项</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="系数" prop="coefficients" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="mono cell-coeffs">
                {{ row.coefficients ? JSON.stringify(row.coefficients) : '{}' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="优先级" prop="priority" width="80" align="center" />
          <el-table-column label="状态" prop="is_active" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="danger" @click="deleteExpertRule(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="expertTotal > expertQuery.page_size"
          class="pagination"
          layout="total, prev, pager, next"
          :current-page="expertQuery.page_no"
          :page-size="expertQuery.page_size"
          :total="expertTotal"
          @current-change="onExpertPageChange"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 编辑规则库弹窗 -->
    <el-dialog v-model="editLibraryVisible" title="编辑规则库" width="540px">
      <el-form :model="libraryForm" label-width="100px">
        <el-form-item label="库编码">
          <span class="mono">{{ libraryForm.library_code }}</span>
          <span style="margin-left: 8px; color: #909399; font-size: 12px">编码不可修改</span>
        </el-form-item>
        <el-form-item label="库名称" required>
          <el-input v-model="libraryForm.library_name" placeholder="规则库名称" />
        </el-form-item>
        <el-form-item label="归属">
          <el-tag v-if="libraryForm.owner_type === 'system'" type="info">系统级（不可修改）</el-tag>
          <el-select v-else v-model="libraryForm.owner_type" style="width: 100%">
            <el-option label="租户级" value="tenant" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="libraryForm.priority" :min="0" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input-number v-model="libraryForm.version" :min="1" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="libraryForm.is_active" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="libraryForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editLibraryVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLibrarySubmitting" @click="submitEditLibrary">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 规则方法编辑弹窗（新建/编辑共用） -->
    <el-dialog
      v-model="methodDialogVisible"
      :title="methodDialogMode === 'create' ? '新建规则方法' : '编辑规则方法'"
      width="640px"
    >
      <el-form :model="methodForm" label-width="100px">
        <el-form-item label="规则描述" required>
          <el-input v-model="methodForm.rule_description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="规则解释">
          <el-input v-model="methodForm.rule_explanation" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="材料缩写">
          <el-input v-model="methodForm.polymer_abbreviation" placeholder="如 ABS（留空 = 不限）" />
        </el-form-item>
        <el-form-item label="产品类别">
          <el-input v-model="methodForm.product_category" placeholder="如 汽车配件（留空 = 不限）" />
        </el-form-item>
        <el-form-item label="缺陷名称">
          <el-input v-model="methodForm.defect_label" placeholder="如 飞边" />
        </el-form-item>
        <el-form-item label="缺陷标识">
          <el-input v-model="methodForm.defect_code" placeholder="如 flash" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="methodForm.priority" :min="0" :max="10" />
        </el-form-item>
        <el-form-item label="置信度">
          <el-input-number v-model="methodForm.confidence" :min="0" :max="1" :step="0.05" :precision="2" />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="methodForm.source" style="width: 100%">
            <el-option label="专家经验" value="expert" />
            <el-option label="规则挖掘" value="rule_miner" />
            <el-option label="大模型生成" value="llm" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="methodForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="methodDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="methodSubmitting" @click="submitMethod">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 专家规则编辑弹窗（仅新建，无编辑） -->
    <el-dialog v-model="expertDialogVisible" title="新建专家规则" width="640px">
      <el-form :model="expertForm" label-width="100px">
        <el-form-item label="规则编码" required>
          <el-input v-model="expertForm.rule_code" placeholder="英文编码，如 default_injection" />
        </el-form-item>
        <el-form-item label="规则名称" required>
          <el-input v-model="expertForm.rule_name" placeholder="中文名称" />
        </el-form-item>
        <el-form-item label="匹配条件">
          <div class="hint">JSON 数组（每项含 field/operator/value），留空 = 默认规则</div>
          <el-input
            v-model="expertForm.conditionsText"
            type="textarea"
            :rows="4"
            placeholder='[{"field":"polymer.abbreviation","operator":"exact","value":"ABS"}]'
          />
        </el-form-item>
        <el-form-item label="覆盖系数">
          <div class="hint">JSON 对象，与内置默认值深度合并</div>
          <el-input
            v-model="expertForm.coefficientsText"
            type="textarea"
            :rows="4"
            placeholder='{"holding":{"hold_pres_inj_ratio_max":0.85}}'
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="expertForm.priority" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="expertForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="expertDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="expertSubmitting" @click="submitExpertRule">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, Delete, Plus } from '@element-plus/icons-vue'
import {
  getRuleLibrary,
  updateRuleLibrary,
  deleteRuleLibrary as apiDeleteRuleLibrary,
  listRuleMethods,
  createRuleMethod,
  updateRuleMethod,
  deleteRuleMethod as apiDeleteRuleMethod,
  listExpertRules,
  createExpertRule,
  deleteExpertRule as apiDeleteExpertRule,
} from '@/api/rule'
import type {
  RuleLibrary,
  RuleMethod,
  ExpertRule,
  RuleLibraryCreatePayload,
  RuleMethodCreatePayload,
  RuleSource,
} from '@/types/rule'
import { useUserStore } from '@/stores/user'

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
const libraryForm = reactive({
  library_code: '',
  library_name: '',
  owner_type: 'tenant' as 'system' | 'tenant',
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
  libraryForm.priority = library.value.priority
  libraryForm.version = library.value.version
  libraryForm.is_active = library.value.is_active
  libraryForm.description = library.value.description || ''
  editLibraryVisible.value = true
}

async function submitEditLibrary() {
  if (!libraryForm.library_name) {
    ElMessage.warning('请填写库名称')
    return
  }
  editLibrarySubmitting.value = true
  try {
    const payload: Partial<RuleLibraryCreatePayload> = {
      library_name: libraryForm.library_name,
      priority: libraryForm.priority,
      version: libraryForm.version,
      is_active: libraryForm.is_active,
      description: libraryForm.description,
    }
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
// Tabs
// ============================================================================

// 初始 tab：模糊库默认 methods，专家规则库默认 expert-rules
const activeTab = ref<'methods' | 'expert-rules'>(
  library.value?.library_type === 'fuzzy' ? 'methods' : 'expert-rules',
)

// ----- Tab 1: 规则方法 -----

const methods = ref<RuleMethod[]>([])
const methodTotal = ref(0)
const methodLoading = ref(false)
const methodQuery = reactive({
  defect_code: '',
  is_active: undefined as boolean | undefined,
  page_no: 1,
  page_size: 10,
})

async function loadMethods() {
  methodLoading.value = true
  try {
    const res: any = await listRuleMethods(libraryId.value, {
      page_no: methodQuery.page_no,
      page_size: methodQuery.page_size,
      defect_code: methodQuery.defect_code || undefined,
      is_active: methodQuery.is_active,
    })
    // 后端响应统一为 { status, msg, data: { total, items, ... } }
    methods.value = res.data?.items || res.items || []
    methodTotal.value = res.data?.total ?? res.total ?? 0
  } catch {
    methods.value = []
    methodTotal.value = 0
  } finally {
    methodLoading.value = false
  }
}

function resetMethodQuery() {
  methodQuery.defect_code = ''
  methodQuery.is_active = undefined
  methodQuery.page_no = 1
  loadMethods()
}

function onMethodPageChange(p: number) {
  methodQuery.page_no = p
  loadMethods()
}

const SOURCE_LABELS: Record<RuleSource, string> = {
  expert: '专家经验',
  rule_miner: '规则挖掘',
  llm: '大模型生成',
}
function sourceLabel(s: string) {
  return SOURCE_LABELS[s as RuleSource] || s
}

// 方法弹窗（新建/编辑共用）
const methodDialogVisible = ref(false)
const methodDialogMode = ref<'create' | 'edit'>('create')
const methodSubmitting = ref(false)
const methodForm = reactive({
  id: 0,
  rule_description: '',
  rule_explanation: '',
  polymer_abbreviation: '',
  product_category: '',
  defect_label: '',
  defect_code: '',
  priority: 1,
  confidence: 1.0,
  source: 'expert' as RuleSource,
  is_active: true,
})

function showCreateMethodDialog() {
  methodDialogMode.value = 'create'
  methodForm.id = 0
  methodForm.rule_description = ''
  methodForm.rule_explanation = ''
  methodForm.polymer_abbreviation = ''
  methodForm.product_category = ''
  methodForm.defect_label = ''
  methodForm.defect_code = ''
  methodForm.priority = 1
  methodForm.confidence = 1.0
  methodForm.source = 'expert'
  methodForm.is_active = true
  methodDialogVisible.value = true
}

function showEditMethodDialog(row: RuleMethod) {
  methodDialogMode.value = 'edit'
  methodForm.id = row.id
  methodForm.rule_description = row.rule_description
  methodForm.rule_explanation = row.rule_explanation || ''
  methodForm.polymer_abbreviation = row.polymer_abbreviation || ''
  methodForm.product_category = row.product_category || ''
  methodForm.defect_label = row.defect_label || ''
  methodForm.defect_code = row.defect_code || ''
  methodForm.priority = row.priority
  methodForm.confidence = row.confidence
  methodForm.source = row.source
  methodForm.is_active = row.is_active
  methodDialogVisible.value = true
}

async function submitMethod() {
  if (!methodForm.rule_description) {
    ElMessage.warning('请填写规则描述')
    return
  }
  methodSubmitting.value = true
  try {
    if (methodDialogMode.value === 'create') {
      const payload: RuleMethodCreatePayload = {
        rule_library_id: libraryId.value,
        rule_description: methodForm.rule_description,
        rule_explanation: methodForm.rule_explanation || undefined,
        polymer_abbreviation: methodForm.polymer_abbreviation || undefined,
        product_category: methodForm.product_category || undefined,
        defect_label: methodForm.defect_label || undefined,
        defect_code: methodForm.defect_code || undefined,
        priority: methodForm.priority,
        confidence: methodForm.confidence,
        source: methodForm.source,
        is_active: methodForm.is_active,
      }
      await createRuleMethod(payload)
      ElMessage.success('规则方法创建成功')
    } else {
      await updateRuleMethod(methodForm.id, {
        rule_description: methodForm.rule_description,
        rule_explanation: methodForm.rule_explanation || undefined,
        polymer_abbreviation: methodForm.polymer_abbreviation || undefined,
        product_category: methodForm.product_category || undefined,
        defect_label: methodForm.defect_label || undefined,
        defect_code: methodForm.defect_code || undefined,
        priority: methodForm.priority,
        confidence: methodForm.confidence,
        source: methodForm.source,
        is_active: methodForm.is_active,
      })
      ElMessage.success('规则方法更新成功')
    }
    methodDialogVisible.value = false
    loadMethods()
    // 数量也要刷新
    loadLibrary()
  } catch {
    /* 拦截器已提示 */
  } finally {
    methodSubmitting.value = false
  }
}

async function deleteMethod(row: RuleMethod) {
  try {
    await ElMessageBox.confirm(
      `确认删除规则方法？\n${row.rule_description}`,
      '删除规则方法',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await apiDeleteRuleMethod(row.id)
    ElMessage.success('删除成功')
    loadMethods()
    loadLibrary()
  } catch {
    /* 拦截器已提示 */
  }
}

// ----- Tab 2: 专家规则 -----

const expertRules = ref<ExpertRule[]>([])
const expertTotal = ref(0)
const expertLoading = ref(false)
const expertQuery = reactive({
  rule_code: '',
  is_active: undefined as boolean | undefined,
  page_no: 1,
  page_size: 10,
})

async function loadExpertRules() {
  expertLoading.value = true
  try {
    const res: any = await listExpertRules(libraryId.value, {
      page_no: expertQuery.page_no,
      page_size: expertQuery.page_size,
      rule_code: expertQuery.rule_code || undefined,
      is_active: expertQuery.is_active,
    })
    // 后端响应统一为 { status, msg, data: { total, items, ... } }
    expertRules.value = res.data?.items || res.items || []
    expertTotal.value = res.data?.total ?? res.total ?? 0
  } catch {
    expertRules.value = []
    expertTotal.value = 0
  } finally {
    expertLoading.value = false
  }
}

function resetExpertQuery() {
  expertQuery.rule_code = ''
  expertQuery.is_active = undefined
  expertQuery.page_no = 1
  loadExpertRules()
}

function onExpertPageChange(p: number) {
  expertQuery.page_no = p
  loadExpertRules()
}

// 专家规则弹窗（仅新建，无编辑）
const expertDialogVisible = ref(false)
const expertSubmitting = ref(false)
const expertForm = reactive({
  rule_code: '',
  rule_name: '',
  conditionsText: '',
  coefficientsText: '',
  priority: 100,
  is_active: true,
})

function showCreateExpertRuleDialog() {
  expertForm.rule_code = ''
  expertForm.rule_name = ''
  expertForm.conditionsText = ''
  expertForm.coefficientsText = ''
  expertForm.priority = 100
  expertForm.is_active = true
  expertDialogVisible.value = true
}

async function submitExpertRule() {
  if (!expertForm.rule_code || !expertForm.rule_name) {
    ElMessage.warning('请填写规则编码和规则名称')
    return
  }
  // 校验 JSON
  let conditions: any[] = []
  let coefficients: Record<string, any> = {}
  if (expertForm.conditionsText.trim()) {
    try {
      const parsed = JSON.parse(expertForm.conditionsText)
      if (!Array.isArray(parsed)) {
        ElMessage.warning('匹配条件必须是 JSON 数组')
        return
      }
      conditions = parsed
    } catch {
      ElMessage.warning('匹配条件 JSON 格式错误')
      return
    }
  }
  if (expertForm.coefficientsText.trim()) {
    try {
      const parsed = JSON.parse(expertForm.coefficientsText)
      if (typeof parsed !== 'object' || Array.isArray(parsed)) {
        ElMessage.warning('覆盖系数必须是 JSON 对象')
        return
      }
      coefficients = parsed
    } catch {
      ElMessage.warning('覆盖系数 JSON 格式错误')
      return
    }
  }
  expertSubmitting.value = true
  try {
    await createExpertRule({
      rule_library_id: libraryId.value,
      rule_code: expertForm.rule_code,
      rule_name: expertForm.rule_name,
      conditions,
      coefficients,
      priority: expertForm.priority,
      is_active: expertForm.is_active,
    })
    ElMessage.success('专家规则创建成功')
    expertDialogVisible.value = false
    loadExpertRules()
    loadLibrary()
  } catch {
    /* 拦截器已提示 */
  } finally {
    expertSubmitting.value = false
  }
}

async function deleteExpertRule(row: ExpertRule) {
  try {
    await ElMessageBox.confirm(
      `确认删除专家规则？\n${row.rule_code}（${row.rule_name}）`,
      '删除专家规则',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await apiDeleteExpertRule(row.id)
    ElMessage.success('删除成功')
    loadExpertRules()
    loadLibrary()
  } catch {
    /* 拦截器已提示 */
  }
}

// ============================================================================
// Tab 切换时按需加载
// ============================================================================

watch(activeTab, (val) => {
  if (val === 'methods' && methods.value.length === 0 && !methodLoading.value) {
    loadMethods()
  } else if (
    val === 'expert-rules' &&
    library.value?.library_type === 'expert' &&
    expertRules.value.length === 0 &&
    !expertLoading.value
  ) {
    // 专家规则 Tab 仅专家规则库加载（Tab 已用 v-if 隐藏，二次防护）
    loadExpertRules()
  }
})

// ============================================================================
// 初始化
// ============================================================================

onMounted(async () => {
  await loadLibrary()
  // 默认加载第一个 Tab
  loadMethods()
})
</script>

<style scoped>
.rule-library-detail {
  padding: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  gap: 16px;
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
}

.rule-tabs {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}

.tab-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 16px;
}

.search-bar {
  flex: 1;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.mono {
  font-family: 'Courier New', Consolas, monospace;
  color: #303133;
}

.cell-coeffs {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
  display: inline-block;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
</style>
