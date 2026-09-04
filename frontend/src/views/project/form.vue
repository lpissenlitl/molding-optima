<!--
  ProjectForm - 项目表单页（新建 + 编辑共用）

  路由：
    - /project/new           新建模式
    - /project/:id/edit      编辑模式（自动加载详情）

  设计要点：
    - 单文件处理两种模式（避免 create / edit 两份重复代码）
    - 通过 useRoute().params.id 判断模式（id 存在 → 编辑，否则新建）
    - 表单字段、验证规则、提交逻辑只写一次

  架构：flat items 数组 + 自动分行
    - 每个 card 是一个独立区域（Card 1：项目信息，Card 2：合同与备注）
    - card.items 是 flat 数组（业务方只关心字段顺序 + 列宽）
    - 自动分行算法 groupIntoRows()：按 span 总和=24 自动换行
      · span=8  → 1/3 行宽（默认 3 列布局）
      · span=16 → 2/3 行宽（跨 2 列）
      · span=24 → 占满整行
    - 添加新字段 = 在 items 里加一项，零模板改动
-->
<template>
  <div class="project-form">
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
      <h2>{{ is_edit ? '编辑项目' : '新建项目' }}</h2>
    </div>

    <el-form
      v-if="loaded"
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      label-position="right"
      v-loading="loading"
      class="form"
    >
      <el-card
        v-for="(card, cIdx) in formCards"
        :key="`card_${cIdx}`"
        shadow="never"
        class="form-section"
      >
        <template #header>
          <span class="section-title">{{ card.title }}</span>
        </template>

        <!--
          自动分行的 rows（由 computed cardRows 计算）
          每个 row 是一个 el-row，内部 items 是 el-col
        -->
        <el-row
          v-for="(row, rIdx) in cardRows[cIdx].rows"
          :key="`row_${cIdx}_${rIdx}`"
          :gutter="24"
        >
          <el-col
            v-for="(item, iIdx) in row"
            :key="`field_${cIdx}_${rIdx}_${iIdx}`"
            :span="item.span"
          >
            <!-- divider：分组标题（molding-expert 风格） -->
            <el-divider
              v-if="item.type === 'divider'"
              content-position="left"
              class="form-divider"
            >
              {{ item.label }}
            </el-divider>

            <!--
              常规字段：必须有 prop
              用 v-else-if="item.prop" 让 TypeScript 在块内 narrow prop 为 string
              （divider 不需要 prop，其他类型都要求 prop）
            -->
            <el-form-item
              v-else-if="item.prop"
              :label="item.label"
              :prop="item.prop"
            >
              <el-input
                v-if="item.type === 'input' || item.type === 'number'"
                v-model="form[item.prop]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
              />
              <el-select
                v-else-if="item.type === 'select'"
                v-model="form[item.prop]"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
                clearable
              >
                <el-option
                  v-for="opt in item.options"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
              <el-date-picker
                v-else-if="item.type === 'date'"
                v-model="form[item.prop]"
                type="date"
                value-format="YYYY-MM-DD"
                :placeholder="getPlaceholder(item, '选择日期')"
                :disabled="getDisabled(item)"
              />
              <el-input
                v-else-if="item.type === 'textarea'"
                v-model="form[item.prop]"
                type="textarea"
                :rows="item.rows || 4"
                :placeholder="getPlaceholder(item)"
                :disabled="getDisabled(item)"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>

      <!-- 操作按钮：sticky bottom，滚动时始终可见 -->
      <div class="form-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ is_edit ? '保存' : '创建' }}
        </el-button>
      </div>
    </el-form>

    <!-- 编辑模式的加载占位 -->
    <div v-else v-loading="true" class="loading-placeholder"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { projectMethod } from '@/api'
import { groupIntoRows } from '@/utils/form-layout'
import {
  projectStatusOptions,
  projectSourceOptions,
  applicationIndustryOptions,
  manufacturingMethodOptions,
  importanceLevelOptions,
} from '@/constants/project-const'

// ============================================================================
// 路由（核心：通过 useRoute 区分新建/编辑模式）
// ============================================================================

const route = useRoute()
const router = useRouter()

/** 是否编辑模式（路由参数中含 id） */
const is_edit = computed(() => !!route.params.id)

/** 编辑模式下的项目 id */
const project_id = computed(() => {
  const id = route.params.id
  return id ? Number(id) : null
})

// ============================================================================
// 表单配置（flat items 数组 + 自动分行）
//
// 字段含义：
//   label     显示文本（divider 类型必填，其他类型必填）
//   prop      字段名（必填，绑定 form[prop]；divider 不需要）
//   type      input/select/date/textarea/number/divider（必填）
//   span      el-col 列宽（默认 8 = 3 列布局中的 1 列；divider 不适用）
//             可选值：8（1 列）/16（2 列）/24（满列）
//   options   select 选项数组（type=select 时必填）
//   placeholder 占位文本（可选；支持字符串）
//   disabled  禁用（布尔或函数；用于"项目编号在编辑模式禁用"等场景）
//   rules     Element Plus 验证规则数组（可选；动态汇总到顶层 rules）
//   rows      textarea 行数（type=textarea 时可选，默认 4）
//   default   字段默认值（可选；用于 form 初始化）
// ============================================================================

interface FormItem {
  label?: string
  prop?: string
  type: 'input' | 'select' | 'date' | 'textarea' | 'number' | 'divider'
  span?: number
  options?: Array<{ value: string | number; label: string }>
  placeholder?: string
  disabled?: boolean | ((item: FormItem) => boolean)
  rules?: any[]
  rows?: number
  default?: any
}

interface FormCard {
  title: string
  items: FormItem[]
}

const formCards: FormCard[] = [
  {
    title: '项目信息',
    items: [
      { label: '项目编号', prop: 'project_code', type: 'input', placeholder: '留空则自动生成', disabled: () => is_edit.value },
      { label: '项目名称', prop: 'project_name', type: 'input', span: 16, rules: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] },
      { label: '项目状态', prop: 'status', type: 'select', options: projectStatusOptions },
      { label: '项目来源', prop: 'source', type: 'select', options: projectSourceOptions },
      { label: '客户名称', prop: 'initiator', type: 'input' },
      { label: '应用行业', prop: 'application_industry', type: 'select', options: applicationIndustryOptions },
      { label: '量产地', prop: 'manufacturing_location', type: 'input' },
      { label: '制作方式', prop: 'manufacturing_method', type: 'select', options: manufacturingMethodOptions },
      { label: '重要程度', prop: 'importance_level', type: 'select', options: importanceLevelOptions },
      { label: '项目经理', prop: 'project_manager', type: 'input', span: 16 },
    ],
  },
  {
    title: '合同与备注',
    items: [
      { label: '合同日期', prop: 'contract_date', type: 'date' },
      { label: '合同 T1', prop: 'contract_t1_date', type: 'date' },
      { label: '合同出厂', prop: 'contract_factory_delivery_date', type: 'date' },
      { label: '备注', prop: 'remarks', type: 'textarea', span: 24, rows: 4 },
    ],
  },
]

// ============================================================================
// 自动分行算法（已抽到 @/utils/form-layout，import 后直接使用）
// ============================================================================

/** 卡片 → 行（自动分行后的结构） */
const cardRows = computed(() =>
  formCards.map((card) => ({
    title: card.title,
    rows: groupIntoRows(card.items, { columns: 4 }),
  }))
)

// ============================================================================
// 表单状态
// ============================================================================

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const loaded = ref(false)  // 编辑模式：详情是否加载完成（避免表单闪现）

/** 表单默认值（从 formCards 的 default 字段汇总） */
function getDefaultForm(): Record<string, any> {
  const result: Record<string, any> = {}
  for (const card of formCards) {
    for (const item of card.items) {
      if (item.prop) {
        result[item.prop] = item.default ?? null
      }
    }
  }
  // 业务默认值（覆盖 item.default 缺失的字段）
  result.source = 'manual'
  return result
}

const form = ref(getDefaultForm())

/** 验证规则（从 formCards 的 rules 字段动态汇总） */
const rules = computed<FormRules>(() => {
  const result: FormRules = {}
  for (const card of formCards) {
    for (const item of card.items) {
      if (item.prop && item.rules && item.rules.length > 0) {
        result[item.prop] = item.rules
      }
    }
  }
  return result
})

// ============================================================================
// 模板辅助函数
// ============================================================================

/** 解析 placeholder：默认根据 type 自动生成 */
function getPlaceholder(item: FormItem, fallback?: string): string {
  if (item.placeholder) return item.placeholder
  if (fallback) return fallback
  if (item.type === 'select') return `请选择${item.label}`
  if (item.type === 'date') return '选择日期'
  return `请输入${item.label}`
}

/** 解析 disabled：支持布尔或函数 */
function getDisabled(item: FormItem): boolean {
  if (typeof item.disabled === 'function') {
    return item.disabled(item)
  }
  return !!item.disabled
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(async () => {
  if (is_edit.value && project_id.value !== null) {
    await loadDetail()
  } else {
    // 新建模式：直接显示空表单
    loaded.value = true
  }
})

async function loadDetail() {
  if (project_id.value === null) return
  loading.value = true
  try {
    const res: any = await projectMethod.getDetail(project_id.value)
    if (res.status === 0) {
      Object.assign(form.value, res.data)
      loaded.value = true
    } else {
      ElMessage.error(res.msg || '加载项目详情失败')
      router.push('/project/list')
    }
  } catch (err: any) {
    console.error('[ProjectForm] loadDetail failed:', err)
    ElMessage.error(err?.message || '加载项目详情异常')
    router.push('/project/list')
  } finally {
    loading.value = false
  }
}

// ============================================================================
// 操作
// ============================================================================

function goBack() {
  router.push('/project/list')
}

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    // 清理 null 值（后端 schema 全部 Optional）
    const payload: any = {}
    for (const [key, val] of Object.entries(form.value)) {
      if (val !== null && val !== '') {
        payload[key] = val
      }
    }

    const res: any = is_edit.value
      ? await projectMethod.edit(payload, project_id.value!)
      : await projectMethod.add(payload)

    if (res.status === 0) {
      ElMessage.success(is_edit.value ? '保存成功' : '创建成功')
      router.push('/project/list')
    } else {
      ElMessage.error(res.msg || (is_edit.value ? '保存失败' : '创建失败'))
    }
  } catch (err: any) {
    console.error('[ProjectForm] submit failed:', err)
    ElMessage.error(err?.message || '提交异常')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.project-form {
  padding: 16px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;

  h2 {
    margin: 12px 0 0 0;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
  }
}

/*
 * 表单卡片通用样式
 * - form-section：每个 card 之间的间距
 * - 控件宽度统一：input / select / date-picker 占满 col 宽度
 */
.form {
  .form-section {
    margin-bottom: 16px;

    :deep(.el-card__header) {
      padding: 12px 20px;
    }
  }

  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }

  .el-form-item {
    margin-bottom: 18px;
  }

  // 控件占满 col 宽度（统一控制，移除 inline style）
  :deep(.el-select),
  :deep(.el-date-editor.el-input),
  :deep(.el-date-editor.el-input__inner),
  :deep(.el-input) {
    width: 100%;
  }

}

/*
 * 分组标题（divider 类型，左对齐 + 加粗）
 * - 用于 card 内再分组（如"基本信息"、"客户信息"等）
 */
.form-divider {
  margin: 4px 0 12px 0;

  :deep(.el-divider__text) {
    font-weight: 600;
    color: var(--el-text-color-primary);
    font-size: 13px;
  }
}

/*
 * 操作按钮（sticky bottom）
 * - position: sticky：滚动时固定在视窗底部
 * - 阴影 + 边框：与卡片视觉分隔
 * - 取消 / 提交按钮在右侧（flex-end）
 */
.form-actions {
  position: sticky;
  bottom: 16px;
  z-index: 10;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding: 12px 20px;
  background: var(--color-bg-base, #ffffff);
  border: 1px solid var(--color-border-extra-light, #ebeef5);
  border-radius: 4px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
}

.loading-placeholder {
  height: 400px;
}
</style>