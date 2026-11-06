<!-- RuleLibraryFormDrawer.vue - 规则库新建/编辑抽屉（共用子组件） -->
<template>
  <el-drawer
    :model-value="visible"
    :title="mode === 'edit' ? '编辑规则库' : '新建规则库'"
    direction="rtl"
    size="540px"
    :close-on-click-modal="false"
    destroy-on-close
    @update:model-value="emit('update:visible', $event)"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="formRules"
      label-width="100px"
      @submit.prevent
    >
      <el-form-item label="库编码" prop="library_code">
        <el-input
          v-model="form.library_code"
          placeholder="英文编码，如 general"
          :disabled="mode === 'edit'"
        />
        <div v-if="mode === 'edit'" class="field-tip">
          库编码为唯一标识，保存后不可修改
        </div>
      </el-form-item>

      <el-form-item label="库名称" prop="library_name">
        <el-input
          v-model="form.library_name"
          placeholder="中文名，如 通用规则库"
        />
      </el-form-item>

      <el-form-item label="归属" prop="owner_type">
        <el-radio-group v-model="form.owner_type" :disabled="mode === 'edit'">
          <el-radio value="tenant">租户级</el-radio>
          <el-radio value="system">系统级</el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 归属租户（仅平台超管代办建租户级库时出现） -->
      <el-form-item v-if="showTenantCompany" label="归属租户" prop="target_company_id">
        <el-select
          v-model="form.target_company_id"
          placeholder="选择该库归属的租户"
          filterable
          style="width: 100%"
        >
          <el-option
            v-for="c in companyOptions"
            :key="c.id"
            :label="`${c.name}（${c.code}）`"
            :value="c.id"
          />
        </el-select>
        <div class="field-tip">
          超管代办建库：租户级库必须挂到目标租户名下，否则该库对该租户不生效
        </div>
      </el-form-item>

      <el-form-item label="库类型" prop="library_type">
        <el-radio-group v-model="form.library_type" :disabled="mode === 'edit'">
          <el-radio value="expert">专家规则库</el-radio>
          <el-radio value="fuzzy">模糊规则库</el-radio>
        </el-radio-group>
        <div class="field-tip">
          决定库内允许的规则种类；编辑时不可修改（类型决定库下数据语义）
        </div>
      </el-form-item>

      <el-form-item label="优先级">
        <el-input-number
          v-model="form.priority"
          :min="0"
          :max="1000"
          placeholder="0-1000，数值越大越优先"
        />
      </el-form-item>

      <el-form-item label="版本号">
        <el-input-number v-model="form.version" :min="1" />
      </el-form-item>

      <el-form-item label="启用">
        <el-switch v-model="form.is_active" />
        <span style="margin-left: 8px; color: #909399; font-size: 12px">
          禁用后该库下所有规则不参与决策
        </span>
      </el-form-item>

      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="可选"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:visible', false)">
        <AppIcon icon="mdi:close" style="margin-right: 4px; font-size: 14px;" />
        取消
      </el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        保存
      </el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { companyMethod } from '@/api'
import type { LibraryType } from '@/types/rule'

// 表单数据结构（与父组件共享）

export interface RuleLibraryFormData {
  library_code: string
  library_name: string
  owner_type: 'system' | 'tenant'
  library_type: LibraryType
  priority: number
  version: number
  is_active: boolean
  description: string
  /** 归属租户（仅平台超管代办建租户级库时使用） */
  target_company_id: number | null
}

// Props / Emits

const props = defineProps<{
  /** 抽屉可见性（受控） */
  visible: boolean
  /** 模式：新建 / 编辑 */
  mode: 'create' | 'edit'
  /** 表单数据（父组件拥有） */
  form: RuleLibraryFormData
  /** 提交中状态（父组件控制 loading） */
  submitting?: boolean
  /** 是否超管理员：超管可为指定租户代办建库 */
  isSuperuser?: boolean
}>()

const emit = defineEmits<{
  /** 抽屉可见性变化（关闭时） */
  'update:visible': [val: boolean]
  /** 校验通过后通知父组件提交 */
  submit: []
}>()

// 表单引用 + 校验规则

const formRef = ref<FormInstance>()

const formRules: FormRules<RuleLibraryFormData> = {
  library_code: [
    { required: true, message: '请填写库编码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '以小写字母开头，仅含小写字母/数字/下划线', trigger: 'blur' },
  ],
  library_name: [
    { required: true, message: '请填写库名称', trigger: 'blur' },
  ],
  owner_type: [
    { required: true, message: '请选择归属', trigger: 'change' },
  ],
  library_type: [
    { required: true, message: '请选择库类型', trigger: 'change' },
  ],
  target_company_id: [
    {
      validator: (_rule, value, callback) => {
        if (showTenantCompany.value && !value) {
          callback(new Error('请选择归属租户'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

// --- 归属租户（超管代办）---

/** 仅「超管 + 新建 + 租户级」才需要指定归属租户 */
const showTenantCompany = computed(
  () => props.mode === 'create' && !!props.isSuperuser && props.form.owner_type === 'tenant',
)

interface CompanyOption {
  id: number
  name: string
  code: string
}

const companyOptions = ref<CompanyOption[]>([])

async function loadCompanies() {
  if (companyOptions.value.length) return
  try {
    const res: any = await companyMethod.get({ page_no: 1, page_size: 200 } as any)
    const items = res?.data?.items || res?.items || []
    companyOptions.value = items.map((c: any) => ({ id: c.id, name: c.name, code: c.code }))
  } catch {
    companyOptions.value = []
  }
}

// 抽屉打开时按需拉取租户列表（超管代办才需要）
watch(
  () => props.visible,
  (visible) => {
    if (visible && showTenantCompany.value) loadCompanies()
  },
)

async function handleSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  emit('submit')
}
</script>

<style lang="scss" scoped>
.field-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
  line-height: 1.4;
  margin-top: 4px;
}
</style>
