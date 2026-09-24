<!--
  RuleKeywordTab.vue - 关键词 tab 内容
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
        <el-form-item label="关键词">
          <el-input
            v-model="keywordQuery.name"
            placeholder="搜索关键词名/别名"
            clearable
            style="width: 180px"
            @keyup.enter="loadKeywords"
          />
        </el-form-item>
        <el-form-item label="数据类型">
          <el-select v-model="keywordQuery.keyword_type" clearable placeholder="全部" style="width: 140px">
            <el-option label="压力" value="pressure" />
            <el-option label="速度" value="speed" />
            <el-option label="时间" value="time" />
            <el-option label="温度" value="temperature" />
            <el-option label="位置" value="position" />
            <el-option label="力" value="force" />
            <el-option label="长度" value="length" />
            <el-option label="重量" value="weight" />
          </el-select>
        </el-form-item>
        <!-- 三个动作按钮合并到同一个 form-item：搜索 + 重置 + 新建 -->
        <el-form-item class="search-actions">
          <el-button type="primary" @click="loadKeywords">
            <AppIcon icon="mdi:magnify" :size="14" style="margin-right: 4px;" />
            搜索
          </el-button>
          <el-button @click="resetKeywordQuery">
            <AppIcon icon="mdi:refresh" :size="14" style="margin-right: 4px;" />
            重置
          </el-button>
          <el-button type="success" @click="showCreateKeywordDialog">
            <AppIcon icon="mdi:plus" :size="14" style="margin-right: 4px;" />
            新建关键词
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 关键词表格：包一层 wrapper 让 el-table 撑满剩余空间 -->
    <div class="table-wrapper">
      <el-table
        v-loading="keywordLoading"
        :data="keywords"
        border
        stripe
        height="100%"
      >
        <!-- 序号列 -->
        <el-table-column type="index" label="#" width="60" align="center" fixed="left" />
        <el-table-column label="关键词名" prop="keyword_name" min-width="160">
          <template #default="{ row }">
            <span class="mono">{{ row.keyword_name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="别名" prop="keyword_alias" min-width="140" />
        <el-table-column label="数据类型" prop="keyword_type" width="100">
          <template #default="{ row }">
            <el-tag effect="plain">{{ keywordTypeLabel(row.keyword_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="单位" prop="unit" width="80" align="center" />
        <el-table-column label="默认范围" width="160">
          <template #default="{ row }">
            <span class="mono">{{ row.range_min }} ~ {{ row.range_max }}</span>
          </template>
        </el-table-column>
        <el-table-column label="模糊级别" prop="fuzzy_level" width="100" align="center">
          <template #default="{ row }">{{ row.fuzzy_level }} 级</template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="text" @click="showEditKeywordDialog(row)">
              <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 14px;" />
              编辑
            </el-button>
            <el-button type="text" class="text-danger" @click="handleDeleteKeyword(row)">
              <AppIcon icon="mdi:delete-outline" style="margin-right: 4px; font-size: 14px;" />
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页器：始终显示（无数据时也保留「共 0 条」占位，确认加载完成）-->
    <el-pagination
      class="pagination"
      layout="total, prev, pager, next"
      :current-page="keywordQuery.page_no"
      :page-size="keywordQuery.page_size"
      :total="keywordTotal"
      @current-change="onKeywordPageChange"
    />

    <!-- 关键词弹窗（新建/编辑共用）-->
    <!-- 关键词抽屉（新建/编辑共用） - 工业软件用右侧抽屉，方便查看上下文表格 -->
    <el-drawer
      v-model="keywordDrawerVisible"
      :title="keywordDialogMode === 'create' ? '新建关键词' : '编辑关键词'"
      direction="rtl"
      size="540px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form :model="keywordForm" label-width="100px">
        <el-form-item label="关键词名" required>
          <el-input v-model="keywordForm.keyword_name" placeholder="英文大写缩写，如 IP1 / BT1" />
        </el-form-item>
        <el-form-item label="别名" required>
          <el-input v-model="keywordForm.keyword_alias" placeholder="中文名，如 一级注射压力" />
        </el-form-item>
        <el-form-item label="字段分类" required>
          <el-select v-model="keywordForm.category" placeholder="选择字段分类" style="width: 100%">
            <el-option label="工艺参数" value="parameter" />
            <el-option label="缺陷类别" value="defect" />
            <el-option label="缺陷位置" value="defect_position" />
          </el-select>
        </el-form-item>
        <el-form-item label="字段属性" required>
          <el-select v-model="keywordForm.parameter_kind" placeholder="选择字段属性" style="width: 100%">
            <el-option label="设定值" value="setpoint" />
            <el-option label="实际值" value="actual" />
            <el-option label="其它" value="enum" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据类型" required>
          <el-select v-model="keywordForm.keyword_type" placeholder="选择数据类型" style="width: 100%">
            <el-option label="压力" value="pressure" />
            <el-option label="速度" value="speed" />
            <el-option label="时间" value="time" />
            <el-option label="温度" value="temperature" />
            <el-option label="位置" value="position" />
            <el-option label="力" value="force" />
            <el-option label="长度" value="length" />
            <el-option label="重量" value="weight" />
          </el-select>
        </el-form-item>
        <el-form-item label="单位" required>
          <el-select
            v-model="keywordForm.unit"
            placeholder="选择或输入单位（允许自定义）"
            allow-create
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="opt in currentUnitOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="默认最小值" required>
          <el-input v-model="keywordForm.range_min" v-number="2" placeholder="如 0.00" />
        </el-form-item>
        <el-form-item label="默认最大值" required>
          <el-input v-model="keywordForm.range_max" v-number="2" placeholder="如 200.00" />
        </el-form-item>
        <el-form-item label="模糊级别" required>
          <el-select v-model="keywordForm.fuzzy_level" placeholder="选择模糊级别" style="width: 100%">
            <el-option label="3 级（粗粒度）" :value="3" />
            <el-option label="5 级（推荐）" :value="5" />
            <el-option label="7 级（细粒度）" :value="7" />
            <el-option label="9 级（极细）" :value="9" />
          </el-select>
        </el-form-item>
        <el-form-item label="模糊步长">
          <el-input v-model="keywordForm.step" v-number="2" placeholder="如 10（留空则按 range 自动计算）" />
          <div class="field-tip">推理输出会取整到该值的整数倍。参考公式：步长 ≈（最大值 - 最小值）/ 模糊级别</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="keywordDrawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="keywordDialogSubmitting" @click="submitKeyword">
          保存
        </el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listRuleKeywords,
  createRuleKeyword,
  updateRuleKeyword,
  deleteRuleKeyword as apiDeleteRuleKeyword,
} from '@/api/rule'
import type {
  RuleKeyword,
  KeywordType,
  RuleKeywordCreatePayload,
  Category,
  ParameterKind,
  FuzzyLevel,
} from '@/types/rule'
import {
  pressureUnitOptions,
  speedUnitOptions,
  temperatureUnitOptions,
  positionUnitOptions,
  timeUnitOptions,
  clampingForceUnitOptions,
  screwRotationUnitOptions,
  weightUnitOptions,
} from '@/constants/machine-const'

const props = defineProps<{
  /** 当前激活的 tab key（来自父组件）*/
  activeTab: 'libraries' | 'keywords'
  /** 是否超级管理员（保留字段，便于未来按角色控制关键词）*/
  isSuperuser: boolean
}>()

// ============================================================================
// 状态
// ============================================================================
const keywords = ref<RuleKeyword[]>([])
const keywordTotal = ref(0)
const keywordLoading = ref(false)
const keywordQuery = reactive({
  name: '',
  keyword_type: '' as '' | KeywordType,
  page_no: 1,
  page_size: 20,
})

const KEYWORD_TYPE_LABELS: Record<KeywordType, string> = {
  pressure: '压力',
  speed: '速度',
  time: '时间',
  temperature: '温度',
  position: '位置',
  force: '力',
  length: '长度',
  weight: '重量',
}
function keywordTypeLabel(t: string) {
  return KEYWORD_TYPE_LABELS[t as KeywordType] || t
}

// ============================================================================
// 单位选项（按 keyword_type 动态展示常用单位，allow-create 支持自定义）
// ============================================================================
const UNIT_OPTIONS_BY_TYPE: Record<KeywordType, { value: string; label: string }[]> = {
  pressure: pressureUnitOptions,
  speed: speedUnitOptions,
  temperature: temperatureUnitOptions,
  position: positionUnitOptions,
  time: timeUnitOptions,
  force: clampingForceUnitOptions,
  length: positionUnitOptions,  // 长度复用位置单位
  weight: weightUnitOptions,
}
// 聚合所有常用单位（未选 keyword_type 时使用，避免选项为空）
const ALL_UNIT_OPTIONS: { value: string; label: string }[] = [
  ...pressureUnitOptions,
  ...speedUnitOptions,
  ...temperatureUnitOptions,
  ...positionUnitOptions,
  ...timeUnitOptions,
  ...clampingForceUnitOptions,
  ...weightUnitOptions,
  ...screwRotationUnitOptions,
]
const currentUnitOptions = computed(() => {
  if (!keywordForm.keyword_type) {
    // 未选 keyword_type：展示所有常用单位，避免选项为空
    return ALL_UNIT_OPTIONS
  }
  return UNIT_OPTIONS_BY_TYPE[keywordForm.keyword_type as KeywordType] || []
})

// ============================================================================
// 数据加载
// ============================================================================
async function loadKeywords() {
  keywordLoading.value = true
  try {
    const res: any = await listRuleKeywords({
      page_no: keywordQuery.page_no,
      page_size: keywordQuery.page_size,
      name: keywordQuery.name || undefined,
      keyword_type: keywordQuery.keyword_type || undefined,
    })
    keywords.value = res.data?.items || res.items || []
    keywordTotal.value = res.data?.total ?? res.total ?? 0
  } catch (e) {
    keywords.value = []
    keywordTotal.value = 0
  } finally {
    keywordLoading.value = false
  }
}

function resetKeywordQuery() {
  keywordQuery.name = ''
  keywordQuery.keyword_type = ''
  keywordQuery.page_no = 1
  loadKeywords()
}

function onKeywordPageChange(p: number) {
  keywordQuery.page_no = p
  loadKeywords()
}

// ============================================================================
// 关键词抽屉
// ============================================================================
const keywordDrawerVisible = ref(false)
const keywordDialogMode = ref<'create' | 'edit'>('create')
const keywordDialogSubmitting = ref(false)
const keywordEditId = ref<number>(0)
const keywordForm = reactive({
  keyword_name: '',
  keyword_alias: '',
  category: 'parameter' as Category,
  parameter_kind: 'setpoint' as ParameterKind,
  keyword_type: '' as '' | KeywordType,
  unit: '',
  range_min: 0,
  range_max: 0,
  fuzzy_level: 5 as FuzzyLevel,
  step: null as number | null,
})

function showCreateKeywordDialog() {
  keywordDialogMode.value = 'create'
  keywordEditId.value = 0
  keywordForm.keyword_name = ''
  keywordForm.keyword_alias = ''
  keywordForm.category = 'parameter'
  keywordForm.parameter_kind = 'setpoint'
  keywordForm.keyword_type = ''
  keywordForm.unit = ''
  keywordForm.range_min = 0
  keywordForm.range_max = 0
  keywordForm.fuzzy_level = 5
  keywordForm.step = null
  keywordDrawerVisible.value = true
}

function showEditKeywordDialog(row: RuleKeyword) {
  keywordDialogMode.value = 'edit'
  keywordEditId.value = row.id
  keywordForm.keyword_name = row.keyword_name
  keywordForm.keyword_alias = row.keyword_alias
  keywordForm.category = (row.category || 'parameter') as Category
  keywordForm.parameter_kind = (row.parameter_kind || 'setpoint') as ParameterKind
  keywordForm.keyword_type = row.keyword_type
  keywordForm.unit = row.unit
  keywordForm.range_min = row.range_min
  keywordForm.range_max = row.range_max
  keywordForm.fuzzy_level = row.fuzzy_level
  keywordForm.step = row.step ?? null
  keywordDrawerVisible.value = true
}

async function submitKeyword() {
  if (!keywordForm.keyword_name || !keywordForm.keyword_alias ||
      !keywordForm.category || !keywordForm.parameter_kind ||
      !keywordForm.keyword_type || !keywordForm.unit) {
    ElMessage.warning('请完整填写关键词信息')
    return
  }
  keywordDialogSubmitting.value = true
  try {
    const payload: RuleKeywordCreatePayload = {
      keyword_name: keywordForm.keyword_name,
      keyword_alias: keywordForm.keyword_alias,
      category: keywordForm.category,
      parameter_kind: keywordForm.parameter_kind,
      keyword_type: keywordForm.keyword_type as KeywordType,
      unit: keywordForm.unit,
      range_min: keywordForm.range_min,
      range_max: keywordForm.range_max,
      fuzzy_level: keywordForm.fuzzy_level,
      step: keywordForm.step ?? undefined,
    }
    if (keywordDialogMode.value === 'create') {
      await createRuleKeyword(payload)
      ElMessage.success('关键词创建成功')
    } else {
      await updateRuleKeyword(keywordEditId.value, payload as Partial<RuleKeywordCreatePayload>)
      ElMessage.success('关键词更新成功')
    }
    keywordDrawerVisible.value = false
    loadKeywords()
  } catch (e) {
    // 拦截器已统一提示
  } finally {
    keywordDialogSubmitting.value = false
  }
}

async function handleDeleteKeyword(row: RuleKeyword) {
  try {
    await ElMessageBox.confirm(
      `确认删除关键词？\n${row.keyword_name}（${row.keyword_alias}）`,
      '删除关键词',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await apiDeleteRuleKeyword(row.id)
    ElMessage.success('删除成功')
    loadKeywords()
  } catch {
    // 拦截器已统一提示
  }
}

// ============================================================================
// 生命周期：按需加载
// ============================================================================
onMounted(() => {
  if (props.activeTab === 'keywords') {
    loadKeywords()
  }
})

watch(() => props.activeTab, (val, oldVal) => {
  if (val === 'keywords' && oldVal !== 'keywords' && keywords.value.length === 0) {
    loadKeywords()
  }
})
</script>

<!--
  本组件 scoped style（仅 .text-danger）：
  - 复用父组件 RuleLibraryList.vue 提供的共享样式类
  - .text-danger 用于删除按钮颜色（与其他列表页保持一致）
  - 后续可考虑提升到全局 custom-form.scss 复用
-->
<style lang="scss" scoped>
.text-danger {
  color: #f56c6c;
}

/* 表单字段提示文字（紧贴在 el-input 下方）*/
.field-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
  line-height: 1.4;
  margin-top: 4px;
}
</style>