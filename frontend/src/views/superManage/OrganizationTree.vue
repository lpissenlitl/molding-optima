<template>
  <div>
    <el-card class="box-card" :style="{'min-height': cardHeight}">
      <div slot="manager" class="clearfix" style="text-align:center">
        组织结构
      </div>
      <el-input 
        size="small"
        placeholder="输入关键字进行过滤"
        v-model="filter_text"
        style="margin-bottom:1rem"
      >
      </el-input>
      <div class="custom-tree-container">
        <el-tree
          ref="tree"
          node-key="id"
          :data="org_tree"
          :props="default_props"
          :filter-node-method="filterNode"
          :default-expanded-keys="defaultExpandedKeys()"
          :expand-on-click-node="false"
          @node-drag-end="handleDragEnd"
          draggable
          :allow-drag="allowDrag"
          :allow-drop="allowDrop"
        >
          <span class="custom-tree-node" slot-scope="{ node, data }">
            <span>{{ node.label }}</span> 
            <span>
              <el-button
                type="text"
                size="mini"
                @click="() => onNodeEdit(node, data)"
              >
                <span>编辑</span>
              </el-button>
              <el-button
                type="text"
                size="mini"
                @click="() => onNodeAdd(node, data)"
              >
                <span>添加</span>
              </el-button>
              <el-button
                v-if="allowDelete(data)"
                type="text"
                size="mini"
                @click="() => onNodeDelete(node, data)"
              >
                <span style="color:red">删除</span>
              </el-button>              
            </span>
          </span>
        </el-tree>
      </div>
    </el-card>

    <el-dialog
      v-el-drag-dialog
      :visible.sync="show_dialog"
      :close-on-click-modal="false"
      width="600px"
    >
      <template slot="title">
        <div style="text-align: center; font-weight: bold;">
          {{ org_detail.id ? "编辑组织信息" : "新增组织信息" }}
        </div>
      </template>
      <el-form 
        ref="form_info" 
        :model="org_detail" 
        :rules="rules" 
        size="mini" 
        label-width="6rem" 
      >
        <el-form-item 
          label="组织名称" 
          prop="name"
        >
          <el-input 
            style="width: 100%"
            v-model.trim="org_detail.name"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="组织编码" 
          prop="code"
        >
          <el-input 
            style="width: 100%"
            v-model.trim="org_detail.code"
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="组织类型" 
          prop="org_type"
        >
          <el-select 
            style="width: 100%"
            v-model="org_detail.org_type"
          >
            <el-option label="集团" value="group"></el-option>
            <el-option label="子公司" value="subsidiary"></el-option>
            <el-option label="事业部" value="division"></el-option>
            <el-option label="部门" value="department"></el-option>
            <el-option label="车间" value="workshop"></el-option>
            <el-option label="工段" value="section"></el-option>
            <el-option label="班组" value="team"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item 
          label="负责人" 
          prop="manager"
        >
          <el-autocomplete
            style="width: 100%"
            v-model.trim="org_detail.manager_name" 
            :debounce="0"
            :fetch-suggestions="$querySuggestions({
              table: 'user',
              column: 'engineer_name',
              with_id: true , 
              sub_column: 'username'
            })"
            clearable
            placeholder="请输入内容"
            @select="(item)=>{
              org_detail.manager_name = item.value
              org_detail.manager_id = item.id
            }"
          > 
          </el-autocomplete>
        </el-form-item>
        <el-form-item 
          label="组织描述" 
          prop="description"
        >
          <el-input 
            type="textarea" 
            v-model="org_detail.description" 
            rows="4" 
          ></el-input>
        </el-form-item>
        <el-form-item 
          label="是否启用" 
          prop="is_active"
        >
          <el-tooltip content="如果不激活,则将禁用该组织下任何人员使用权限">
            <el-switch v-model="org_detail.is_active"></el-switch>
          </el-tooltip>
        </el-form-item>
      </el-form>

      <template slot="footer">
        <div style="text-align: center;">
          <el-button 
            type="danger" 
            size="small"
            @click="show_dialog = false" 
          >
            返 回
          </el-button>
          <el-button 
            type="primary" 
            size="small"
            @click="saveData" 
          >
            {{ org_detail.id ? "更  新": "保  存" }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { organizationMethod } from "@/api"
import { calculateTableHeight } from "@/utils/table-size"

const initOrgDetail = {
  id: null,
  parent_id: null,
  sort_order: null,
  name: null,
  code: null,
  manager_id: null,
  manager_name: null,
  description: null,
  org_type: null,
  is_active: true,
}

export default {
  name: "OrganizationTree",
  data() {
    return {
      filter_text: "",
      default_props: {
        id: "id",
        label: "name",
        children: "children",
      },
      org_list: [],
      org_tree: [],
      org_detail: structuredClone(initOrgDetail),
      rules: {
        name: [
          { required: true, message: "组织名称不能为空", trigger: "blur" }
        ],
        org_type: [
          { required: true, message: "组织类型不能为空", trigger: "blur" }
        ],
        code: [
          { required: true, message: "组织编码不能为空", trigger: "blur" }
        ]
      },
      show_dialog: false
    }
  },
  computed: { 
    cardHeight() { 
      return calculateTableHeight(500, 60)
    },
  },
  watch: {
    filter_text(val) {
      this.$refs.tree.filter(val)
    }
  },
  mounted() {
    this.initializeView()
  },
  methods: {
    async initializeView() { 
      this.org_list = []
      const res = await organizationMethod.get({})
      if (res.status == 0) {
        this.org_list = res.data.items
        this.constructViewModel()
      } 
    },
    filterNode(value, data) {
      if (!value) return true
      if (!data.name) return false
      return data.name.indexOf(value) !== -1
    },
    defaultExpandedKeys() {
      return this.org_list.filter(item => item && item.id != null).map(item => item.id)
    },
    allowDelete(data) { 
      const is_root = !data.parent_id
      const is_leaf = !data.children || data.children.length === 0
      return !is_root && is_leaf
    },
    allowDrag(node) {
      return node.data.parent_id !== null
    },
    allowDrop(draggingNode, dropNode, type) {
      if (dropNode.level <= 1) {
        return false
      } else if (draggingNode.data.company_id !== dropNode.data.company_id) {
        return false
      } else {
        return true
      }
    },
    async handleDragEnd(draggingNode, dropNode, dropType, ev) {
      // 不允许拖拽时，直接返回不处理
      if (dropType === "none") {
        return
      } 

      //原兄弟节点调整
      let before_parent = draggingNode.data.parent
      let before_nodes = before_parent.children

      let after_parent = null
      let after_nodes = []

      if (dropType === "inner") { 

        // 移动到目标节点内，目标节点
        after_parent = dropNode.data

        // 移动到目标节点内，所有兄弟节点
        after_nodes = dropNode.data.children
      } else if (dropType === "before" || dropType === "after") { 

        // 移动到目标节点相邻，父节点
        after_parent = dropNode.data.parent

        // 移动到目标节点相邻，所有兄弟节点
        after_nodes = dropNode.data.parent.children
      }

      // 更新拖拽节点的父节点信息
      draggingNode.data.parent = after_parent

      // 更新拖拽前所有兄弟节点的信息
      for (let i = 0; i < before_nodes.length; ++i) {
        before_nodes[i].parent_id = before_parent.id
        before_nodes[i].sort_order = i
        before_nodes[i].path = `${before_parent.path}/${before_nodes[i].code}`
      }

      // 更新拖拽后所有兄弟节点的信息
      for (let i = 0; i < after_nodes.length; ++i) {
        after_nodes[i].parent_id = after_parent.id
        after_nodes[i].sort_order = i
        after_nodes[i].path = `${after_parent.path}/${after_nodes[i].code}`
      }

      let all_nodes = [...before_nodes, ...after_nodes]
      let org_list = all_nodes.map(item => ({
        id: item.id,
        parent_id: item.parent_id,
        sort_order: item.sort_order,
        path: item.path
      }))

      // 调用接口批量更新
      const res = await organizationMethod.multipleUpdate({ org_list })
      if (res.status === 0) {
        this.$message({ type: "success", message: "已更新组织信息！" })
      }
    },
    constructChildren(parent) {
      // 构建子节点
      if (!parent.children) parent.children = []
      for (let i = 0; i < this.org_list.length; ++i) {
        let org_detail = this.org_list[i]
        if (org_detail.parent_id == parent.id) {
          let node = structuredClone(this.org_list[i])
          node.parent = parent
          parent.children.push(node)
          this.constructChildren(node)
        } 
      }

      parent.children.sort((a, b) => a.sort_order - b.sort_order )
    },
    constructViewModel() {
      // 构建一级节点
      let org_tree = []
      for (let i = 0; i < this.org_list.length; ++i) {
        let org_detail = this.org_list[i]
        if (org_detail.parent_id == null) {
          let node = structuredClone(this.org_list[i])
          org_tree.push(node)
          this.constructChildren(node)
        }
      }

      this.org_tree = org_tree
    },
    onNodeEdit(node, data) {
      this.org_detail = {
        node: node,
        ...data
      }
      this.show_dialog = true
    }, 
    onNodeAdd(node, data) {
      this.org_detail = structuredClone(initOrgDetail)
      this.org_detail.node = node
      this.org_detail.parent_id = data.id
      this.org_detail.sort_order = data.children.length

      this.show_dialog = true
    },
    async onNodeDelete(node, data) {
      try {
        await this.$confirm("删除组织", {
          title:"删除组织",
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          message: "确认要删除该组织吗？",
          type: "warning",
        })

        const res = await organizationMethod.delete(data.id)
        if (res.status === 0) {
          this.$message({ type: "success", message: "已删除该组织！" })
          const parent = node.parent
          const children = parent.data.children || parent.data
          const index = children.findIndex(v => v.id === data.id)
          children.splice(index, 1)
        }
      } catch (err) {
        this.$message({ type: "error", message: "取消操作！" })
        return
      }
    },
    async saveData() {
      try {
        await this.$refs.form_info.validate() // 成功时 resolve，失败时 reject
      } catch (err) {
        return this.$message({ type: "error", message: "请填写完整信息！" })
      }

      const { node, parent, children, ...payload } = this.org_detail
      if (this.org_detail.id) {
        const res = await organizationMethod.edit( 
          payload,
          this.org_detail.id
        )
        if (res.status === 0) {
          Object.assign(node.data, res.data)
          this.$message({ type: "success", message: "组织信息更新成功！" })
          this.initializeView()
        }
      } else {
        const res = await organizationMethod.add(payload)
        if (res.status === 0) {
          if (!node.children) {
            this.$set(node, "children", [])
          }
          node.children.push(res.data)
          this.$message({ type: "success", message: "组织信息添加成功！" })
          this.initializeView()
        }
      }

      this.show_dialog = false
    },
    resetView() {
      this.show_dialog = false
      this.initializeView()
    }
  },
}
</script>

<style lang="scss" scoped>
  .custom-tree-node {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 16px;
    padding-right: 8px;
  }
</style>