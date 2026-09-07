<!--
  组织架构 - 树形管理
  - 顶部：当前公司标识 + 节点过滤 + 刷新
  - 主体：el-tree，行内操作（编辑 / 添加子组织 / 删除）
  - 支持拖拽调整层级（含跨公司拒绝、根节点保护）
-->
<template>
  <div class="org-list">
    <!-- 顶部信息条 -->
    <div class="page-header">
      <div class="header-left">
        <span class="company-tag">
          <AppIcon icon="mdi:office-building" />
          当前公司：<strong>{{ userStore.company_name || '未选择' }}</strong>
        </span>
        <div class="filter-input">
          <el-input
            v-model="filter_text"
            placeholder="输入关键字过滤节点"
            clearable
          />
        </div>
      </div>
      <div class="header-right">
        <el-button @click="fetchList">
          <AppIcon icon="mdi:refresh" style="margin-right: 4px; font-size: 14px;" />
          刷新
        </el-button>
      </div>
    </div>

    <!-- 树形卡片 -->
    <el-card class="tree-card" shadow="never" v-loading="list_loading">
      <!-- 未选择公司 -->
      <el-empty
        v-if="!has_company"
        description="请先在【公司管理 → 切换身份】中选择一个公司后再管理组织架构"
        :image-size="100"
      />

      <!-- 已选择公司但无组织数据 -->
      <el-empty
        v-else-if="org_tree.length === 0"
        description="该公司暂无组织数据，请联系系统管理员初始化根组织"
        :image-size="80"
      />

      <!-- 组织树 -->
      <el-tree
        v-else
        ref="treeRef"
        node-key="id"
        :data="org_tree"
        :props="default_props"
        :filter-node-method="filterNode"
        :default-expanded-keys="default_expanded_keys"
        :expand-on-click-node="false"
        @node-drag-end="handleDragEnd"
        draggable
        :allow-drag="allowDrag"
        :allow-drop="allowDrop"
        class="org-tree"
      >
        <template #default="{ node, data }">
          <span class="custom-tree-node">
            <span class="node-info">
              <AppIcon
                v-if="data.org_type === 'group'"
                icon="mdi:office-building"
                class="org-icon"
              />
              <AppIcon
                v-else-if="data.org_type === 'department'"
                icon="mdi:account-group"
                class="org-icon"
              />
              <AppIcon
                v-else-if="data.org_type === 'workshop'"
                icon="mdi:factory"
                class="org-icon"
              />
              <AppIcon
                v-else-if="data.org_type === 'team'"
                icon="mdi:account-multiple"
                class="org-icon"
              />
              <AppIcon v-else icon="mdi:folder-outline" class="org-icon" />
              <span :class="{ 'node-disabled': data.is_active === false }">
                {{ data.name }}
              </span>
              <span v-if="data.level != null" class="org-level-tag">
                L{{ data.level }}
              </span>
              <el-tag
                v-if="data.is_active === false"
                type="info"
                size="small"
                effect="plain"
              >
                已禁用
              </el-tag>
            </span>
            <span class="node-actions" @click.stop>
              <el-button
                type="primary"
                link
                size="small"
                @click="onNodeEdit(node, data)"
              >
                <AppIcon icon="mdi:pencil-outline" style="margin-right: 4px; font-size: 12px;" />
                编辑
              </el-button>
              <el-button
                type="primary"
                link
                size="small"
                @click="onNodeAdd(node, data)"
              >
                <AppIcon icon="mdi:plus" style="margin-right: 4px; font-size: 12px;" />
                添加子组织
              </el-button>
              <el-button
                v-if="allowDelete(data)"
                type="danger"
                link
                size="small"
                @click="onNodeDelete(node, data)"
              >
                <AppIcon icon="mdi:delete-outline" style="margin-right: 4px; font-size: 12px;" />
                删除
              </el-button>
            </span>
          </span>
        </template>
      </el-tree>
    </el-card>

    <!-- 新建/编辑抽屉 -->
    <OrganizationFormDrawer
      v-model:visible="drawer_visible"
      :id="editing_id"
      :parent-id="parent_id"
      @success="onDialogSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import OrganizationFormDrawer from './OrganizationFormDrawer.vue'
import { organizationMethod } from '@/api'
import { useUserStore } from '@/stores/user'

// ============================================================================
// 当前用户上下文（公司）
// ============================================================================

const userStore = useUserStore()

/** 是否已选定公司（company_id 为正整数才视为有效） */
const has_company = computed(() => !!userStore.company_id)

// ============================================================================
// 树数据
// ============================================================================

const default_props = {
  id: 'id',
  label: 'name',
  children: 'children',
}

/** 后端返回的扁平组织列表 */
const org_list = ref<any[]>([])

/** 前端构造的树形结构（喂给 el-tree） */
const org_tree = ref<any[]>([])

const list_loading = ref(false)

/** 默认展开所有节点 */
const default_expanded_keys = computed<number[]>(() =>
  org_list.value
    .filter((item) => item && item.id != null)
    .map((item) => item.id)
)

// ============================================================================
// 节点过滤
// ============================================================================

const filter_text = ref('')
const treeRef = ref<any>()

function filterNode(value: string, data: any) {
  if (!value) return true
  return (data.name || '').indexOf(value) !== -1
}

watch(filter_text, (val) => {
  treeRef.value?.filter(val)
})

// ============================================================================
// 公司上下文变更：自动重新拉数据
// ============================================================================
//
// 场景：用户在【公司管理】页面切换 / 释放租户后，回来此页面时
// onMounted 不会重新触发，需主动 reload 才能看到新公司的组织。
// ============================================================================

watch(
  () => userStore.company_id,
  () => {
    // 清空本地状态避免闪现上一家公司的数据
    org_list.value = []
    org_tree.value = []
    fetchList()
  }
)

// ============================================================================
// 数据加载与树构建
// ============================================================================

async function fetchList() {
  if (!has_company.value) {
    org_list.value = []
    org_tree.value = []
    return
  }

  list_loading.value = true
  try {
    const res: any = await organizationMethod.get({ page_size: 1000 } as any)
    if (res.status === 0) {
      org_list.value = res.data?.items || []
      constructViewModel()
    } else {
      ElMessage.error(res.msg || '查询失败')
    }
  } catch (err) {
    console.error('[OrgList] fetchList failed:', err)
  } finally {
    list_loading.value = false
  }
}

/** 递归构造子节点（按 sort_order 升序） */
function constructChildren(parent: any) {
  if (!parent.children) parent.children = []
  for (let i = 0; i < org_list.value.length; ++i) {
    const org = org_list.value[i]
    if (org.parent_id === parent.id) {
      const node = { ...org }
      node.parent = parent
      parent.children.push(node)
      constructChildren(node)
    }
  }
  parent.children.sort(
    (a: any, b: any) => (a.sort_order ?? 0) - (b.sort_order ?? 0)
  )
}

/** 从扁平列表构建树（一级节点：parent_id == null） */
function constructViewModel() {
  const tree: any[] = []
  for (let i = 0; i < org_list.value.length; ++i) {
    const org = org_list.value[i]
    if (org.parent_id == null) {
      const node = { ...org }
      tree.push(node)
      constructChildren(node)
    }
  }
  org_tree.value = tree
}

// ============================================================================
// 弹窗 / 操作
// ============================================================================

const drawer_visible = ref(false)
const editing_id = ref<number | null>(null)
const parent_id = ref<number | null>(null)

function onNodeEdit(_node: any, data: any) {
  editing_id.value = data.id
  parent_id.value = null
  drawer_visible.value = true
}

function onNodeAdd(_node: any, data: any) {
  editing_id.value = null
  parent_id.value = data.id
  drawer_visible.value = true
}

/** 表单提交成功回调 */
function onDialogSuccess() {
  drawer_visible.value = false
  fetchList()
}

async function onNodeDelete(node: any, data: any) {
  try {
    await ElMessageBox.confirm(
      `确定删除组织 "${data.name}" 吗？此操作不可恢复！`,
      '删除确认',
      { type: 'error' }
    )
  } catch {
    return
  }

  try {
    const res: any = await organizationMethod.delete(data.id)
    if (res.status === 0) {
      ElMessage.success('删除成功')
      // 乐观更新：从父节点的 children 中移除
      const parent = node.parent
      const siblings =
        parent && parent.data && Array.isArray(parent.data.children)
          ? parent.data.children
          : org_tree.value
      const idx = siblings.findIndex((c: any) => c.id === data.id)
      if (idx !== -1) siblings.splice(idx, 1)
    } else {
      ElMessage.error(res.msg || '删除失败')
    }
  } catch (err) {
    console.error('[OrgList] onNodeDelete failed:', err)
  }
}

// ============================================================================
// 拖拽规则
// ============================================================================

/** 根节点不可拖（保护基础结构） */
function allowDrag(node: any) {
  return node.data.parent_id !== null
}

/** 拖放规则：
 *  1. 顶级节点不接受拖入（避免破坏根结构）
 *  2. 跨公司禁止拖放
 */
function allowDrop(draggingNode: any, dropNode: any, _type: string) {
  if (dropNode.level <= 1) return false
  if (draggingNode.data.company_id !== dropNode.data.company_id) return false
  return true
}

// ============================================================================
// 拖拽结束：批量更新兄弟节点的 parent_id / sort_order / path
// ============================================================================

async function handleDragEnd(
  draggingNode: any,
  dropNode: any,
  dropType: string,
  _ev: any
) {
  // 不允许拖拽时直接返回
  if (dropType === 'none') return

  // 拖拽节点原父节点及其兄弟
  const before_parent = draggingNode.data.parent
  const before_nodes = before_parent?.children ?? []

  let after_parent: any = null
  let after_nodes: any[] = []

  if (dropType === 'inner') {
    // 拖入目标节点内部
    after_parent = dropNode.data
    after_nodes = dropNode.data.children ?? []
  } else if (dropType === 'before' || dropType === 'after') {
    // 拖到目标节点相邻
    after_parent = dropNode.data.parent
    after_nodes = dropNode.data.parent?.children ?? []
  }

  // 更新拖拽节点的父指针
  draggingNode.data.parent = after_parent

  // 重排原父节点下的兄弟节点
  for (let i = 0; i < before_nodes.length; ++i) {
    before_nodes[i].parent_id = before_parent.id
    before_nodes[i].sort_order = i
    before_nodes[i].path = `${before_parent.path}/${before_nodes[i].code}`
  }

  // 重排新父节点下的兄弟节点
  for (let i = 0; i < after_nodes.length; ++i) {
    after_nodes[i].parent_id = after_parent.id
    after_nodes[i].sort_order = i
    after_nodes[i].path = `${after_parent.path}/${after_nodes[i].code}`
  }

  const all_nodes = [...before_nodes, ...after_nodes]
  const org_list_payload = all_nodes.map((item: any) => ({
    id: item.id,
    parent_id: item.parent_id,
    sort_order: item.sort_order,
    path: item.path,
  }))

  try {
    const res: any = await organizationMethod.multipleUpdate({
      org_list: org_list_payload,
    })
    if (res.status === 0) {
      ElMessage.success('组织结构调整成功')
      // 重新拉数据保证 path 字段一致（后端可能补充了 path 字段）
      await fetchList()
    } else {
      ElMessage.error(res.msg || '调整失败')
      await fetchList() // 回滚本地状态
    }
  } catch (err) {
    console.error('[OrgList] handleDragEnd failed:', err)
    await fetchList()
  }
}

// ============================================================================
// 删除限制：非根节点 + 叶子节点才能删除
// ============================================================================

function allowDelete(data: any) {
  const is_root = !data.parent_id
  const is_leaf = !data.children || data.children.length === 0
  return !is_root && is_leaf
}

// ============================================================================
// 生命周期
// ============================================================================

onMounted(() => {
  fetchList()
})
</script>

<style scoped lang="scss">
.org-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    flex: 1;          // 占满 header 剩余空间（为 filter-input 腾出伸缩空间）
    min-width: 0;     // 防止 flex item 内容溢出导致布局错乱

    .filter-input {
      flex: 1;            // 包裹 div 承担 flex 响应（不受 inline-flex 影响）

      // 强制 el-input 及其内部撑满包裹 div
      :deep(.el-input) {
        width: 100%;
      }
    }
  }

  .header-right {
    display: flex;
    gap: 8px;
  }
}

.company-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;
  color: #409eff;
  font-size: 14px;

  strong {
    font-weight: 600;
  }
}

.tree-card {
  :deep(.el-card__body) {
    padding: 16px;
    min-height: 400px;
  }
}

.org-tree {
  width: 100%;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-right: 16px;
}

.node-info {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.node-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.org-icon {
  font-size: 16px;
  color: #909399;
}

.org-level-tag {
  display: inline-block;
  font-size: 11px;
  color: #909399;
  background-color: #f4f4f5;
  border-radius: 3px;
  padding: 1px 6px;
  margin-left: 4px;
  font-weight: 500;
}

.node-disabled {
  color: #c0c4cc;
  text-decoration: line-through;
}
</style>