<template>
  <div class="column-header">
    <span>{{ label }}</span>
    <el-popover
      v-model="visible"
      placement="bottom-end"
      trigger="click"
      popper-class="column-filter-popover"
    >
      <div class="filter-content">
        <!-- 标题和清空按钮 -->
        <div class="filter-header">
          <span>{{ title || `筛选${label}` }}</span>
          <el-button 
            type="text" 
            size="mini" 
            @click="handleClear"
            :disabled="values.length === 0"
          >
            清空
          </el-button>
        </div>
        
        <!-- 搜索框（选项过多时显示） -->
        <el-input
          v-if="showSearch && all_values.length > 10"
          v-model="searchKeyword"
          placeholder="搜索..."
          prefix-icon="el-icon-search"
          size="mini"
          clearable
          class="filter-search"
        />
        
        <!-- 全选/反选 -->
        <div v-if="all_values.length > 3" class="filter-actions">
          <el-button type="text" size="mini" @click="handleSelectAll">
            全选
          </el-button>
          <el-button type="text" size="mini" @click="handleInvert">
            反选
          </el-button>
        </div>
        
        <!-- 复选框组 -->
        <el-checkbox-group 
          v-model="internalValues"
          @change="handleChange"
          class="filter-checkbox-group"
        >
          <el-checkbox 
            v-for="value in filteredValues" 
            :key="value" 
            :label="value"
          >
            {{ formatLabel ? formatLabel(value) : value }}
          </el-checkbox>
        </el-checkbox-group>
        
        <!-- 底部按钮 -->
        <div class="filter-footer">
          <el-button size="mini" @click="handleCancel">
            取消
          </el-button>
          <el-button 
            type="primary" 
            size="mini" 
            @click="handleConfirm"
          >
            确定
          </el-button>
        </div>
      </div>
      
      <!-- 筛选图标 -->
      <i 
        slot="reference"
        :class="iconClass || 'el-icon-arrow-down filter-icon'"
        :style="iconStyle"
      ></i>
    </el-popover>
  </div>
</template>

<script>
export default {
  name: "ColumnFilter",
  
  props: {
    // 列标签
    label: {
      type: String,
      required: true
    },
    
    // 自定义标题
    title: {
      type: String,
      default: ""
    },
    
    // 当前选中的值
    values: {
      type: Array,
      default: () => []
    },
    
    // 所有可选值
    all_values: {
      type: Array,
      default: () => []
    },
    
    // 是否显示搜索框
    showSearch: {
      type: Boolean,
      default: true
    },
    
    // 自定义图标类名
    iconClass: {
      type: String,
      default: ""
    },
    
    // 自定义图标样式
    iconStyle: {
      type: Object,
      default: null
    },
    
    // 格式化标签的函数
    formatLabel: {
      type: Function,
      default: null
    }
  },
  
  data() {
    return {
      visible: false,
      internalValues: [...this.values],
      searchKeyword: ""
    }
  },
  
  computed: {
    /**
     * 过滤后的值列表
     */
    filteredValues() {
      if (!this.searchKeyword) {
        return this.all_values
      }
      
      const keyword = this.searchKeyword.toLowerCase()
      return this.all_values.filter(value => {
        const displayValue = this.formatLabel ? this.formatLabel(value) : String(value)
        return displayValue.toLowerCase().includes(keyword)
      })
    }
  },
  
  watch: {
    values(newValues) {
      this.internalValues = [...newValues]
    }
  },
  
  methods: {
    /**
     * 复选框变化
     */
    handleChange() {
      this.$emit("change", this.internalValues)
    },
    
    /**
     * 确认筛选
     */
    handleConfirm() {
      this.visible = false
      this.$emit("confirm", [...this.internalValues])
    },
    
    /**
     * 取消操作
     */
    handleCancel() {
      this.visible = false
      this.internalValues = [...this.values]
      this.$emit("cancel")
    },
    
    /**
     * 清空筛选
     */
    handleClear() {
      this.internalValues = []
      this.visible = false
      this.$emit("clear")
    },
    
    /**
     * 全选
     */
    handleSelectAll() {
      this.internalValues = [...this.all_values]
      this.handleChange()
    },
    
    /**
     * 反选
     */
    handleInvert() {
      const selected = new Set(this.internalValues)
      this.internalValues = this.all_values.filter(v => !selected.has(v))
      this.handleChange()
    }
  }
}
</script>

<style scoped>
.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.filter-content {
  padding: 12px;
  min-width: 200px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #EBEEF5;
}

.filter-header span {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.filter-search {
  margin-bottom: 12px;
}

.filter-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 4px 0;
}

.filter-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

::v-deep .el-checkbox {
  margin-right: 0;
}

.filter-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #EBEEF5;
}
</style>
