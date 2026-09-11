<!--
  ProjectForm - 项目表单页（新建 + 编辑共用）

  路由：
    - /mold/project/new           新建模式
    - /mold/project/:id/edit      编辑模式（自动加载详情）

  设计要点：
    - 单文件处理两种模式（避免 create / edit 两份重复代码）
    - 通过 useRoute().params.id 判断模式（id 存在 → 编辑，否则新建）
    - 表单字段、验证规则、提交逻辑只写一次

  架构：flat items 数组 + 自动分行（默认 4 列布局）
    - 每个 card 是一个独立区域（Card 1：项目信息，Card 2：合同与备注）
    - card.items 是 flat 数组（业务方只关心字段顺序 + 列宽）
    - 自动分行算法 groupIntoRows()：按 span 总和=24 自动换行
      · 默认 columns=4 → 默认 span=6（4 列紧凑布局）
      · span=12 → 跨 2 列（适用于"项目名称"等长字段）
      · span=24 → 占满整行（适用于 textarea、备注、分组标题 divider）
    - 添加新字段 = 在 items 里加一项，零模板改动
-->
<template>
  <div class="project-form">
    <div class="page-header">
      <el-button text @click="goBack">
        <AppIcon icon="mdi:arrow-left" style="margin-right: 4px; font-size: 14px;" />
        返回列表
      </el-button>
    </div>

    <el-form
      v-if="loaded"
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      label-position="right"
      v-loading="loading"
      class="custom-form"
    >
      <el-card
        v-for="(card, cIdx) in formCards"
        :key="`card_${cIdx}`"
        shadow="never"
        class="custom-form__section"
      >
        <template #header>
          <span class="custom-form__title">{{ card.title }}</span>
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
              class="custom-form__divider"
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
    </el-form>

    <!-- 编辑模式的加载占位 -->
    <div v-else v-loading="true" class="loading-placeholder"></div>

    <!--
      操作按钮：移出 el-form，改为 project-form 的子元素
      三个原因（从结构到 UX 逐层递进）：

      1. DOM 结构原因（关注点分离）
         - el-form 只管表单内容，form-actions 只管底部操作
         - 未来样式调整（如改 sticky / drawer）互不影响

      2. CSS 加载顺序原因（避免 FOUC）
         - Vite dev 模式 CSS 异步注入，组件渲染先于样式生效
         - button 在 el-form 内部时，CSS 加载前按 DOM 流渲染在 card 下方
         - 移到 el-form 外部后，DOM 流位置接近 fixed 后的位置，跳跃距离缩短到不可见
         - 生产环境通过 <link> 阻塞渲染，理论上无 FOUC

      3. v-if="loaded"（UX 一致性，非必需）
         - 功能上 handleSubmit 有 if (!formRef.value) return 防御，不加也安全
         - 加上的价值：加载时不出现“取消/创建”按钮，避免误以为可操作
         - 与 el-form 的 v-if="loaded" 显隐同步，视觉一致
    -->
    <div v-if="loaded" class="form-actions">
      <el-button @click="goBack">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ is_edit ? '保存' : '创建' }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { projectMethod } from '@/api'
import { groupIntoRows } from '@/utils/form-layout'
import type { FormItem, FormCard } from '@/utils/form-types'
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

const formCards: FormCard[] = [
  {
    title: '项目信息',
    items: [
      { label: '项目编号', prop: 'project_code', type: 'input', placeholder: '留空则自动生成', disabled: () => is_edit.value },
      { label: '项目名称', prop: 'project_name', type: 'input', rules: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] },
      { label: '项目状态', prop: 'status', type: 'select', options: projectStatusOptions },
      { label: '项目来源', prop: 'source', type: 'select', options: projectSourceOptions },
      { label: '客户名称', prop: 'initiator', type: 'input' },
      { label: '应用行业', prop: 'application_industry', type: 'select', options: applicationIndustryOptions },
      { label: '量产地', prop: 'manufacturing_location', type: 'input' },
      { label: '制作方式', prop: 'manufacturing_method', type: 'select', options: manufacturingMethodOptions },
      { label: '重要程度', prop: 'importance_level', type: 'select', options: importanceLevelOptions },
      { label: '项目经理', prop: 'project_manager', type: 'input' },
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
      router.push('/mold/project/list')
    }
  } catch (err: any) {
    console.error('[ProjectForm] loadDetail failed:', err)
    ElMessage.error(err?.message || '加载项目详情异常')
    router.push('/mold/project/list')
  } finally {
    loading.value = false
  }
}

// ============================================================================
// 操作
// ============================================================================

function goBack() {
  router.push('/mold/project/list')
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
      router.push('/mold/project/list')
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
  /*
   * padding-bottom: 96px 预留底部空间：
   * - form-actions 是 fixed bottom，不占用布局空间
   * - 96px = 操作栏高度 (48px) + 顶部呼吸间隔 (32px) + 16px 保险
   * - 防止 form 末尾的字段（如备注 textarea）被 fixed 操作栏遮挡
   */
  padding: 16px 16px 96px;
  max-width: 1400px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  /*
   * 只保留"返回列表"按钮（退出路径）
   * 页面标识由 navbar 面包屑 + URL 路径承担，避免信息冗余
   * 与 polymer/PolymerForm / admin/RoleCreate 等保持一致
   */
  margin-bottom: 16px;
}

/*
 * 表单内部样式（.custom-form / .custom-form__section / .custom-form__divider 等）
 * 已抽取到全局：src/styles/utilities/custom-form.scss
 * form 模板使用 class="custom-form" 即可继承所有样式
 */

/*
 * 分组标题（divider 类型，左对齐 + 加粗）
 * - 用于 card 内再分组（如"基本信息"、"客户信息"等）
 * - 已抽取到全局：src/styles/utilities/custom-form.scss（.custom-form__divider）
 */

.loading-placeholder {
  height: 400px;
}
</style>