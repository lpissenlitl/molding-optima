<template>
  <div>
    <el-form
      ref="group"
      size="small"
    >
      <el-form-item 
        label="组织信息过滤"
      >
        <el-input
          placeholder="输入关键字进行过滤"
          v-model="filterText"
          size=""
        >
        </el-input>
      </el-form-item>
    </el-form>

    <el-card class="box-card" style="min-height:50rem">
      <div slot="header" class="clearfix" style="text-align:center">
        组织结构
      </div>

      <div class="custom-tree-container">
        <el-tree
          :data="group_tree"
          node-key="id"
          default-expand-all
          :filter-node-method="filterNode"
          ref="tree"
          :props="defaultProps"
          :expand-on-click-node="false"
          @node-drag-start="handleDragStart"
          @node-drag-enter="handleDragEnter"
          @node-drag-leave="handleDragLeave"
          @node-drag-over="handleDragOver"
          @node-drag-end="handleDragEnd"
          @node-drop="handleDrop"
          draggable
          :allow-drop="allowDrop"
          :allow-drag="allowDrag"
        >
          <span class="custom-tree-node" slot-scope="{ node, data }">
            <span>{{ node.label }}</span> 
            <span>
              <el-button
                type="text"
                size="mini"
                @click="() => edit(node, data)"
              >
                <span>编辑</span>
              </el-button>
              <el-button
                type="text"
                size="mini"
                @click="() => append(node, data)"
              >
                <span>添加</span>
              </el-button>
              <el-button
                type="text"
                size="mini"
                @click="() => remove(node, data)"
              >
                <span style="color:red">删除</span>
              </el-button>              
            </span>
          </span>
        </el-tree>
      </div>
    </el-card>
  </div>
</template>

<script>
import { groupMethod } from "@/api"
import { UserModule } from '@/store/modules/user'

export default {
  data() {
    return {
      defaultProps: {
        children: 'children',
        label: 'name',
        id:'id',
      },
      group_tree: [],
      nodes: [],
      filterText: '',
    }
  },
  created() {

  },
  mounted() {
    this.initView()
  },
  methods: {
    initView() { 
      this.nodes = []
      groupMethod.get({
        company_id: UserModule.company_id
      }).then(res => {
        if (res.status == 0) {
          if (res.data && res.data.total > 0) {
            this.nodes = res.data.items
            this.constructViewModel()
          } else {
            this.initCompanyGroup()
          }
        } 
      })
    },
    initCompanyGroup() {
      let root = {
        company_id: UserModule.company_id,
        name: UserModule.name,
        parent_id: null,
        sort_index: 0,
        created_at: null,
        updated_at: null,
        deleted: 0
      }

      groupMethod.add(root)
      .then(res => {
        if (res.status == 0) {
          this.nodes.push(JSON.parse(JSON.stringify(res.data)))
          this.constructViewModel()
        }
      })
    },
    constructViewModel() {
      // 构建一级节点
      for (let i = 0; i < this.nodes.length; ++i) {
        if (!this.nodes[i].parent_id) {
          let node = JSON.parse(JSON.stringify(this.nodes[i]))
          this.group_tree.push(node)
          this.appendChildren(node)
        }
      }
    },
    appendChildren(parent) {
      // 构建子节点
      if (!parent.children) {
        parent.children = []
      }

      for (let i = 0; i < this.nodes.length; ++i) {
        if (this.nodes[i].parent_id == parent.id) {
          let node = JSON.parse(JSON.stringify(this.nodes[i]))
          parent.children.push(node)
          this.appendChildren(node)
        } 
      }
    },
    edit(node, data) {
      this.$prompt('请输入修改后的名称', '修改名称', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      }).then((prompt) => {
        data.name = prompt.value
        groupMethod.edit({
          "name": data.name
        }, data.id).then(res => {

        })
      }).catch(() => {
        this.$message({ 
          type: "info", 
          message: "已取消"
        })
      })
    }, 
    append(node, data) {
 
      if (!data.children) {
        this.$set(data, 'children', []);
      }

      this.$prompt('请输入组织节点名称', '添加组织节点', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
      }).then((prompt) => {

        let newNode = {
          company_id: UserModule.company_id,
          id: null,
          name: prompt.value,
          parent_id: data.id,
          sort_index: data.children.length,
          created_at: null,
          updated_at: null,
          deleted: 0,
        }

        groupMethod.add(newNode)
        .then(res => {
          if (res.status === 0) {
            this.$refs.tree.append(res.data, node)
            this.$message({
              type: "success",
              message: "添加成功！"
            })
          }
        })
      })

    },
    remove(node, data) {
      const h = this.$createElement
      this.$confirm("删除", {
        title:"删除",
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        message: h('div', [
          h('p', '确认要删除吗？'),
          h('p', '请注意！删除不可恢复。'),
        ]),
        type: "warning",
      }).then(() => {

        let record = []
        this.recordDeletedNode(node.data, record)

        for (let i = 0; i < record.length; ++i) {
          groupMethod.delete(record[i])
          .then(res => {

          })
        }
        this.$refs.tree.remove(node)
      })
    },
    recordDeletedNode(parent, record) {
      record.push(parent.id)
      if (parent.children) {
        for (let i = 0; i < parent.children.length; ++i) {
          this.recordDeletedNode(parent.children[i], record)
        }
      }
    },
    filterNode(value, data) {
      if (!value) return true;
      return data.name.indexOf(value) !== -1;
    },
    handleDragStart(node, ev) {
    },
    handleDragEnter(draggingNode, dropNode, ev) {
    },
    handleDragLeave(draggingNode, dropNode, ev) {
    },
    handleDragOver(draggingNode, dropNode, ev) {
    },
    handleDragEnd(draggingNode, dropNode, dropType, ev) {

      if (dropType==="before" || dropType==="after") {
        // 平级
        groupMethod.edit({
          "parent_id": dropNode.data.parent_id
        }, draggingNode.data.id)
        .then(res => {
        })
      }

      if(dropType==="inner") {
        // 在当前dropNode的下面，是下一级
        groupMethod.edit({
          "parent_id": dropNode.data.id
        }, draggingNode.data.id)
        .then(res => {
        })
      }

      let parent_children = dropNode.parent.data.children
      if (parent_children) {
        for (let i = 0; i < parent_children.length; ++i) {
          groupMethod.edit({
            "sort_index": i
          }, parent_children[i].id)
          .then(res => {
          })
        }
      }
    },
    handleDrop(draggingNode, dropNode, dropType, ev) {
      return 
    },
    allowDrop(draggingNode, dropNode, type) {

      if (dropNode.level <= 1) {
        return false
      }

      return true
    },
    allowDrag(draggingNode) {
      // 不能拖拽的,设置在这里
      return draggingNode.data.parent_id;
    },
  },
  watch: {
    filterText(val) {
      this.$refs.tree.filter(val);
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
    font-size: 14px;
    padding-right: 8px;
  }
</style>