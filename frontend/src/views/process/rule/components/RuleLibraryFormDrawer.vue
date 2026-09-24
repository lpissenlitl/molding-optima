<!--
  RuleLibraryFormDrawer.vue - 规则库新建/编辑抽屉（共用子组件）

  设计：
  - 受控组件：父组件拥有 form 数据 / submitting 状态 / 提交逻辑
  - 子组件只负责渲染抽屉 + 表单 UI + 表单校验（轻量）
  - 父组件传 form，watch mode 变化时初始化表单
  - 新建/编辑共用，编辑模式下"库编码 + 库类型"锁定

  使用方：
  - RuleLibraryTab.vue（列表页新建/编辑）
  - RuleLibraryDetail.vue（详情页编辑）

  字段：
  - 库编码（创建必填，编辑只读）
  - 库名称（必填）
  - 归属（创建可改，编辑只读）
  - 库类型（创建可改，编辑只读）
  - 优先级（默认 100）
  - 版本号（默认 1）
  - 描述（可选）
-->
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
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        保存
      </el-button>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { LibraryType } from '@/types/rule'

// ============================================================================
// 表单数据结构（与父组件共享）
// ============================================================================

export interface RuleLibraryFormData {
  library_code: string
  library_name: string
  owner_type: 'system' | 'tenant'
  library_type: LibraryType
  priority: number
  version: number
  is_active: boolean
  description: string
}

// ============================================================================
// Props / Emits
// ============================================================================

const props = defineProps<{
  /** 抽屉可见性（受控） */
  visible: boolean
  /** 模式：新建 / 编辑 */
  mode: 'create' | 'edit'
  /** 表单数据（父组件拥有） */
  form: RuleLibraryFormData
  /** 提交中状态（父组件控制 loading） */
  submitting?: boolean
}>()

const emit = defineEmits<{
  /** 抽屉可见性变化（关闭时） */
  'update:visible': [val: boolean]
  /** 校验通过后通知父组件提交 */
  submit: []
}>()

// ============================================================================
// 表单引用 + 校验规则
// ============================================================================

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
}

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
