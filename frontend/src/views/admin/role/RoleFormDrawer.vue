<!--
  RoleFormDrawer - 角色表单抽屉（一体化组件：el-drawer + el-form + 提交逻辑）
  - 使用方：v-model:visible 控制显示，:id 传编辑 id，@success 接收提交成功事件
  - 基础字段：name、code、description、is_active
  - 权限分配：el-tree 多选
  - 创建时：必填 name + code
  - 编辑时：code 只读
-->
<template>
  <el-drawer
    :model-value="visible"
    :title="isCreate ? '新增角色' : '编辑角色'"
    direction="rtl"
    size="640px"
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
        <el-form-item label="角色名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="例如：注塑工艺工程师"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="角色编码" prop="code">
          <el-input
            v-model="form.code"
            placeholder="小写字母+下划线，例如：process_engineer"
            :disabled="!isCreate"
            maxlength="100"
          />
          <div v-if="!isCreate" class="field-tip">
            编码用于程序识别，保存后不可修改
          </div>
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="可选，描述角色用途"
            maxlength="255"
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

        <el-form-item label="权限分配">
          <div class="permission-tree-wrapper">
            <div class="tree-toolbar">
              <el-input v-model="tree_keyword"
                placeholder="搜索权限名称或编码"
                clearable
                size="default"
                style="width: 200px;"
              >
                <template #prefix><AppIcon icon="mdi:magnify" /></template>
              </el-input>
              <div class="tree-actions">
                <el-button size="small" link @click="expandAll(true)">展开全部</el-button>
                <el-button size="small" link @click="expandAll(false)">折叠全部</el-button>
                <el-button size="small" link @click="checkAll(true)">全选</el-button>
                <el-button size="small" link @click="checkAll(false)">清空</el-button>
              </div>
            </div>
            <div v-loading="tree_loading" class="tree-container">
              <el-tree
                ref="treeRef"
                :data="permissionTree"
                :props="treeProps"
                node-key="code"
                show-checkbox
                :check-strictly="false"
                :filter-node-method="filterNode"
                :default-expand-all="false"
                empty-text="暂无权限数据"
                @check="onTreeCheck"
              >
                <template #default="{ node, data }">
                  <span class="tree-node">
                    <span class="tree-node-label">{{ node.label }}</span>
                    <el-tag
                      v-if="data.type === 'button'"
                      size="small"
                      type="info"
                      effect="plain"
                      class="node-type-tag"
                    >
                      操作
                    </el-tag>
                    <!-- 仅开发环境显示：code 是技术标识，业务用户不需要看 -->
                    <span v-if="isDev" class="tree-node-code">{{ data.code }}</span>
                  </span>
                </template>
              </el-tree>
            </div>
            <div class="permission-summary">
              已选择 <strong>{{ checked_count }}</strong> 项权限
            </div>
          </div>
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
import { ref, reactive, watch, nextTick, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { roleMethod, getPermissionTree } from '@/api'

// ============================================================================
// Props / Emits
// ============================================================================

interface Props {
  visible: boolean
  id?: number | null
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  id: null,
})

const emit = defineEmits<{
  'update:visible': [val: boolean]
  success: []
}>()

const isCreate = computed(() => !props.id)

function onVisibleChange(val: boolean) {
  emit('update:visible', val)
}

// ============================================================================
// 表单数据
// ============================================================================

const formRef = ref<FormInstance>()
const treeRef = ref<any>()
const loading = ref(false)
const submitting = ref(false)
const tree_loading = ref(false)

const form = reactive({
  name: '',
  code: '',
  description: '',
  is_active: true,
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 1, max: 50, message: '角色名称长度 1-50', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
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
// 权限树
// ============================================================================

const treeProps = {
  label: 'name',
  children: 'children',
}

const permissionTree = ref<any[]>([])
const tree_keyword = ref('')
const checked_codes = ref<string[]>([])

// 仅开发环境显示技术标识（权限 code），生产环境隐藏
const isDev = import.meta.env.DEV
const checked_count = computed(() => checked_codes.value.length)

watch(tree_keyword, (val) => {
  treeRef.value?.filter(val)
})

function filterNode(value: string, data: any) {
  if (!value) return true
  const kw = value.toLowerCase()
  return (
    (data.name || '').toLowerCase().includes(kw) ||
    (data.code || '').toLowerCase().includes(kw)
  )
}

async function loadPermissionTree() {
  tree_loading.value = true
  try {
    const res: any = await getPermissionTree()
    if (res.status === 0) {
      permissionTree.value = res.data || []
    } else {
      ElMessage.error(res.msg || '权限树加载失败')
    }
  } catch (err) {
    console.error('[RoleFormDrawer] loadPermissionTree failed:', err)
  } finally {
    tree_loading.value = false
  }
}

function onTreeCheck() {
  const checked = treeRef.value?.getCheckedNodes(false, true) || []
  checked_codes.value = checked.map((n: any) => n.code)
}

function expandAll(expand: boolean) {
  const traverse = (nodes: any[]) => {
    nodes.forEach((node) => {
      const treeNode = treeRef.value?.getNode(node.code)
      if (treeNode) treeNode.expanded = expand
      if (node.children) traverse(node.children)
    })
  }
  traverse(permissionTree.value)
}

function checkAll(check: boolean) {
  if (check) {
    const collectLeafCodes = (nodes: any[], acc: string[] = []): string[] => {
      nodes.forEach((n) => {
        if (n.children && n.children.length > 0) {
          collectLeafCodes(n.children, acc)
        } else {
          acc.push(n.code)
        }
      })
      return acc
    }
    const leafCodes = collectLeafCodes(permissionTree.value)
    treeRef.value?.setCheckedKeys(leafCodes)
  } else {
    treeRef.value?.setCheckedKeys([])
  }
  onTreeCheck()
}

function setCheckedFromCodes(codes: string[]) {
  if (!codes || codes.length === 0) {
    treeRef.value?.setCheckedKeys([])
    return
  }
  treeRef.value?.setCheckedKeys(codes)
  onTreeCheck()
}

// ============================================================================
// 详情加载（编辑模式）
// ============================================================================

async function loadRoleDetail(roleId: number) {
  loading.value = true
  try {
    const res: any = await roleMethod.getDetail(roleId)
    if (res.status === 0) {
      const r = res.data
      Object.assign(form, {
        name: r.name || '',
        code: r.code || '',
        description: r.description || '',
        is_active: r.is_active !== false,
      })
      await nextTick()
      setCheckedFromCodes(r.permission_codes || [])
    } else {
      ElMessage.error(res.msg || '加载角色详情失败')
    }
  } catch (err) {
    console.error('[RoleFormDrawer] loadRoleDetail failed:', err)
  } finally {
    loading.value = false
  }
}

// ============================================================================
// 模式切换
// ============================================================================

watch(
  () => props.id,
  async (newId) => {
    await loadPermissionTree()
    await nextTick()

    if (newId) {
      await loadRoleDetail(newId)
    } else {
      // 创建模式：重置表单
      Object.assign(form, {
        name: '',
        code: '',
        description: '',
        is_active: true,
      })
      tree_keyword.value = ''
      formRef.value?.clearValidate()
      treeRef.value?.setCheckedKeys([])
      checked_codes.value = []
    }
  },
  { immediate: true }
)

// ============================================================================
// 提交
// ============================================================================

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
      description: form.description || null,
      is_active: form.is_active,
      permission_codes: checked_codes.value,
    }

    let res: any
    if (isCreate.value) {
      payload.code = form.code
      res = await roleMethod.add(payload)
    } else {
      res = await roleMethod.edit(payload, props.id!)
    }

    if (res.status === 0) {
      ElMessage.success(isCreate.value ? '创建成功' : '更新成功')
      emit('success')
      emit('update:visible', false)
    } else {
      ElMessage.error(res.msg || (isCreate.value ? '创建失败' : '更新失败'))
    }
  } catch (err) {
    console.error('[RoleFormDrawer] submit failed:', err)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
.drawer-body {
  padding: 0 24px;
}

.field-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 4px;
}

.permission-tree-wrapper {
  width: 100%;
}

.tree-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.tree-actions {
  display: flex;
  gap: 4px;
}

.tree-container {
  max-height: 460px;
  overflow-y: auto;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 8px;
  background-color: #fafafa;
}

.tree-node {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  font-size: 13px;
}

.tree-node-label {
  flex-shrink: 0;
}

.node-type-tag {
  flex-shrink: 0;
}

.tree-node-code {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 11px;
  color: #909399;
  margin-left: auto;
}

.permission-summary {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;

  strong {
    color: #409eff;
    margin: 0 4px;
  }
}

:deep(.el-tree-node__content) {
  height: 28px;
}

:deep(.el-tree-node__content:hover) {
  background-color: #f5f7fa;
}
</style>
