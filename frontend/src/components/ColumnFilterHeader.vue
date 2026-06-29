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
          <span>筛选{{ label }}</span>
          <button 
            class="custom-btn-text"
            @click="handleClear"
            :disabled="internalValues.length === 0"
          >
            清空
          </button>
        </div>
        
        <!-- 搜索框（选项过多时显示） -->
        <el-input
          v-if="all_values.length > 10"
          v-model="searchKeyword"
          placeholder="搜索..."
          prefix-icon="el-icon-search"
          size="mini"
          clearable
          class="filter-search"
        />
        
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
            {{ displayValue(value) }}
          </el-checkbox>
        </el-checkbox-group>
        
        <!-- 底部按钮 -->
        <div class="filter-footer">
          <button class="custom-btn" @click="handleCancel">
            取消
          </button>
          <button class="custom-btn primary" @click="handleConfirm">
            确定
          </button>
        </div>
      </div>
      
      <!-- 筛选图标（Iconify） -->
      <AppIcon 
        slot="reference"
        icon="mdi:filter-variant"
        class="filter-icon"
        :class="{ 'filter-active': values.length > 0 }"
        width="16"
        height="16"
      />
    </el-popover>
  </div>
</template>

<script>
export default {
  name: "ColumnFilterHeader",
  
  props: {
    // 列标签
    label: {
      type: String,
      required: true
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
    
    // 格式化值的函数
    formatValue: {
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
        const displayValue = this.displayValue(value)
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
     * 格式化值
     */
    displayValue(val) {
      return this.formatValue ? this.formatValue(val) : val
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

/* 筛选图标 */
.filter-icon {
  margin-left: 4px;
  color: #909399;
  cursor: pointer;
  transition: all 0.2s;
  vertical-align: middle;
  display: inline-flex;
  align-items: center;
}

.filter-icon:hover {
  color: #409EFF;
}

.filter-icon.filter-active {
  color: #409EFF;
}

::v-deep .column-filter-popover {
  min-width: 200px;
  padding: 0;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.filter-content {
  padding: 12px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #EBEEF5;
}

.filter-header span {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

/* 自定义清空按钮 */
.filter-header .custom-btn-text {
  padding: 3px 8px;
  font-size: 12px;
  line-height: 1.5;
  border: none;
  background: transparent;
  color: #606266;
  cursor: pointer;
  border-radius: 3px;
  transition: all 0.2s;
}

.filter-header .custom-btn-text:hover:not(:disabled) {
  color: #409EFF;
  background-color: #ECF5FF;
}

.filter-header .custom-btn-text:disabled {
  color: #C0C4CC;
  cursor: not-allowed;
}

.filter-search {
  margin-bottom: 10px;
}

::v-deep .filter-search .el-input__inner {
  height: 30px;
  line-height: 30px;
  font-size: 12px;
}

.filter-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 300px;
  overflow-y: auto;
  padding: 2px 0;
}

::v-deep .el-checkbox {
  margin-right: 0;
  height: 26px;
  line-height: 26px;
}

::v-deep .el-checkbox__label {
  font-size: 13px;
  padding-left: 6px;
}

::v-deep .el-checkbox__input {
  line-height: 1;
}

/* 自定义底部按钮 */
.filter-footer {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #EBEEF5;
}

/* 自定义小按钮样式 */
.filter-footer .custom-btn {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 3px;
  border: 1px solid #DCDFE6;
  background-color: #fff;
  color: #606266;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  line-height: 1.5;
}

.filter-footer .custom-btn:hover {
  color: #409EFF;
  border-color: #C6E2FF;
  background-color: #ECF5FF;
}

.filter-footer .custom-btn.primary {
  background-color: #409EFF;
  border-color: #409EFF;
  color: #fff;
}

.filter-footer .custom-btn.primary:hover {
  background-color: #66B1FF;
  border-color: #66B1FF;
}

.filter-footer .custom-btn:active {
  transform: scale(0.98);
}
</style>
