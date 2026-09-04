<!--
  OrganizationFormDrawer - 组织表单抽屉
  - 创建模式：从行内"添加子组织"上下文传入 parentId
  - 编辑模式：编辑现有组织，不修改父级（父级调整请使用拖拽）
  - 字段：name、code、org_type、manager_id、description、sort_order、is_active
-->
<template>
  <el-drawer
    :model-value="visible"
    :title="isCreate ? '新增子组织' : '编辑组织'"
    direction="rtl"
    size="600px"
    :close-on-click-modal="false"
    destroy-on-close
    @update:model-value="onVisibleChange"
  >
    <div class="drawer-body">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        label-position="right"
        v-loading="loading"
      >
        <el-form-item label="组织名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="例如：注塑车间"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="组织编码" prop="code">
          <el-input
            v-model="form.code"
            placeholder="可留空，系统将基于名称自动生成"
            maxlength="30"
          />
          <div class="field-tip">
            同一公司下编码必须唯一；留空时系统自动生成
          </div>
        </el-form-item>

        <el-form-item label="组织类型" prop="org_type">
          <el-select
            v-model="form.org_type"
            placeholder="选择组织类型"
            style="width: 100%;"
          >
            <el-option
              v-for="opt in org_type_options"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="组织负责人">
          <el-select
            v-model="form.manager_id"
            placeholder="选择用户（可搜索）"
            clearable
            filterable
            style="width: 100%;"
          >
            <el-option
              v-for="u in user_options"
              :key="u.id"
              :label="u.engineer_name ? `${u.username}（${u.engineer_name}）` : u.username"
              :value="u.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="排序">
          <el-input-number
            v-model="form.sort_order"
            :min="0"
            :max="999"
            controls-position="right"
            style="width: 140px;"
          />
          <span class="field-tip" style="margin-left: 12px;">
            数字越小排序越靠前
          </span>
        </el-form-item>

        <el-form-item label="组织描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="可选"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="是否启用">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="onVisibleChange(false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { organizationMethod, userMethod } from '@/api'

// ============================================================================
// Props / Emits
// ============================================================================

interface Props {
  visible: boolean
  /** 编辑时传 id，null/undefined 表示创建模式 */
  id?: number | null
  /** 创建模式下的初始父级（行内"添加子组织"时由列表页传入） */
  parentId?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  id: null,
  parentId: null,
})

const emit = defineEmits<{
  'update:visible': [val: boolean]
  success: []
}>()

/** 是否为创建模式：id 为空 = 创建 */
const isCreate = computed(() => !props.id)

function onVisibleChange(val: boolean) {
  emit('update:visible', val)
}

// ============================================================================
// 组织类型
// ============================================================================

const org_type_options = [
  { value: 'group', label: '集团' },
  { value: 'subsidiary', label: '子公司' },
  { value: 'division', label: '事业部' },
  { value: 'department', label: '部门' },
  { value: 'workshop', label: '车间' },
  { value: 'section', label: '工段' },
  { value: 'team', label: '班组' },
]

// ============================================================================
// 表单数据
// ============================================================================

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)

const form = reactive({
  name: '',
  code: '',
  manager_id: undefined as number | undefined,
  org_type: 'department',
  description: '',
  sort_order: 0,
  is_active: true,
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入组织名称', trigger: 'blur' },
    { min: 1, max: 255, message: '组织名称长度 1-255', trigger: 'blur' },
  ],
  org_type: [
    { required: true, message: '请选择组织类型', trigger: 'change' },
  ],
  code: [
    {
      validator: (_rule, value, callback) => {
        if (!value) return callback()
        const ok = /^[a-z][a-z0-9_]*$/.test(value)
        callback(ok ? undefined : new Error('编码格式：小写字母开头，仅含小写字母/数字/下划线'))
      },
      trigger: 'blur',
    },
  ],
}

// ============================================================================
// 选项数据：用户列表（负责人下拉）
// ============================================================================

const user_options = ref<any[]>([])

async function loadUsers() {
  try {
    const res: any = await userMethod.get({ page_size: 1000 } as any)
    if (res.status === 0) {
      user_options.value = res.data?.items || []
    }
  } catch (err) {
    console.error('[OrganizationFormDrawer] loadUsers failed:', err)
  }
}

// ============================================================================
// 详情加载（编辑模式）
// ============================================================================

async function loadOrgInfo(orgId: number) {
  loading.value = true
  try {
    const res: any = await organizationMethod.getDetail(orgId)
    if (res.status === 0) {
      const o = res.data
      Object.assign(form, {
        name: o.name || '',
        code: o.code || '',
        manager_id: o.manager_id || undefined,
        org_type: o.org_type || 'department',
        description: o.description || '',
        sort_order: o.sort_order ?? 0,
        is_active: o.is_active !== false,
      })
    } else {
      ElMessage.error(res.msg || '加载组织详情失败')
    }
  } catch (err) {
    console.error('[OrganizationFormDrawer] loadOrgInfo failed:', err)
  } finally {
    loading.value = false
  }
}

// ============================================================================
// 生命周期 + 模式切换
// ============================================================================

/** id 变化时重新初始化（外部切换 create/edit 模式） */
watch(
  () => props.id,
  async (newId) => {
    await loadUsers()

    if (newId) {
      await loadOrgInfo(newId)
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

function resetForm() {
  Object.assign(form, {
    name: '',
    code: '',
    manager_id: undefined,
    org_type: 'department',
    description: '',
    sort_order: 0,
    is_active: true,
  })
  formRef.value?.clearValidate()
}

// ============================================================================
/** 提交表单 */
async function submit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    const payload: any = {
      name: form.name,
      code: form.code || null,
      manager_id: form.manager_id || null,
      org_type: form.org_type,
      description: form.description || null,
      sort_order: form.sort_order,
      is_active: form.is_active,
    }

    // 仅创建时指定父级；编辑模式不修改父级（父级调整请用拖拽）
    if (isCreate.value) {
      payload.parent_id = props.parentId
    }

    let res: any
    if (isCreate.value) {
      res = await organizationMethod.add(payload)
    } else {
      res = await organizationMethod.edit(payload, props.id!)
    }

    if (res.status === 0) {
      ElMessage.success(isCreate.value ? '创建成功' : '更新成功')
      emit('success')
      emit('update:visible', false)
    } else {
      ElMessage.error(res.msg || (isCreate.value ? '创建失败' : '更新失败'))
    }
  } catch (err) {
    console.error('[OrganizationFormDrawer] submit failed:', err)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.field-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}
</style>