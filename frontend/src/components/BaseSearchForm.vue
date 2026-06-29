<!-- eslint-disable vue/no-mutating-props -->
<template>
  <div class="search-container">
    <el-form
      class="search-form"
      :inline="true"
      :model="query"
      size="mini"
      label-width="auto"
    >
      <!-- 筛选项（根据 level 和展开状态控制显示） -->
      <template v-for="(item, index) in visibleItems">
        <!-- 自定义插槽：直接渲染，避免嵌套 el-form-item 导致间距异常 -->
        <div v-if="item.slot_name" :key="'slot-' + index" class="slot-item-wrapper">
          <slot
            :name="item.slot_name"
            :item="item"
            :query="query"
          />
        </div>

        <el-form-item
          v-else
          :key="index"
          :label="item.label"
          :prop="item.prop"
        >
          <!-- 自动完成输入框 -->
          <el-autocomplete
            v-if="item.type === 'autocomplete'"
            v-model.trim="query[item.prop]" 
            placeholder="请输入内容"
            clearable
            @clear="handleClear(item.prop)"
            :debounce="0"
            :fetch-suggestions="getSuggestions(item.query)"
            class="input-md"
          />
          
          <!-- 下拉选择框 -->
          <el-select
            v-else-if="item.type === 'select'"
            v-model="query[item.prop]"
            placeholder="请选择"
            clearable
            @clear="handleClear(item.prop)"
            class="input-md"
          >
            <el-option 
              v-for="option in item.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          
          <!-- 普通输入框 -->
          <el-input
            v-else-if="item.type === 'input'"
            v-model.trim="query[item.prop]"
            placeholder="请输入内容"
            clearable
            @clear="handleClear(item.prop)"
            class="input-md"
          />
          
          <!-- 日期选择器 -->
          <el-date-picker
            v-else-if="item.type === 'date'"
            v-model="query[item.prop]"
            type="date"
            placeholder="选择日期"
            value-format="yyyy-MM-dd"
            clearable
            @clear="handleClear(item.prop)"
            class="input-md"
          />
        </el-form-item>
      </template>
      
      <!-- 操作按钮 -->
      <el-form-item class="search-actions">
        <el-button 
          type="primary" 
          icon="el-icon-search" 
          @click="handleSearch"
        >
          搜索
        </el-button>
        <el-button 
          icon="el-icon-refresh" 
          @click="handleReset"
        >
          重置
        </el-button>
        
        <!-- 展开/收起按钮（仅在有高级项时显示） -->
        <el-button 
          v-if="hasAdvancedItems"
          type="text" 
          :icon="is_expanded ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"
          @click="toggleExpand"
        >
          {{ is_expanded ? '收起' : '展开' }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script>
export default {
  name: "BaseSearchForm",
  props: {
    /**
     * 查询对象（双向绑定）
     */
    query: {
      type: Object,
      required: true
    },
    
    /**
     * 筛选项配置数组
     * 每项结构：
     * {
     *   label: string,           // 字段标签
     *   prop: string,            // 字段名（对应 query 对象的键）
     *   type: string,            // 类型：autocomplete/select/input/date/slot
     *   level?: string,          // 级别：basic/advanced（可选，默认 basic）
     *   options?: Array,         // select 类型的选项数组
     *   query?: Object,          // autocomplete 类型的查询配置
     *   slot_name?: string        // slot 类型的插槽名称
     * }
     */
    items: {
      type: Array,
      default: () => []
    },
    
    /**
     * 是否支持展开/收起功能
     */
    expandable: {
      type: Boolean,
      default: false
    }
  },
  
  data() {
    return {
      is_expanded: false,
      default_query: {}  // 挂载时快照初始值，重置时恢复
    }
  },
  
  computed: {
    /**
     * 是否有高级筛选项
     */
    hasAdvancedItems() {
      if (!this.expandable) return false
      return this.items.some(item => item.level === "advanced")
    },
      
    /**
     * 可见的筛选项（基础项 + 展开时的高级项）
     */
    visibleItems() {
      if (!this.expandable) {
        return this.items
      }
        
      return this.items.filter(item => {
        return item.level !== "advanced" || this.is_expanded
      })
    }
  },

  created() {
    // 快照父组件传入的初始 query 值作为重置基准
    this.default_query = JSON.parse(JSON.stringify(this.query))
  },
  
  methods: {
    /**
     * 处理清空操作
     * 使用 $set 确保响应式更新
     */
    handleClear(prop) {
      this.$set(this.query, prop, null)
    },
    
    /**
     * 切换展开/收起状态
     */
    toggleExpand() {
      this.is_expanded = !this.is_expanded
      // 触发展开状态变化事件（可选）
      this.$emit("expand-change", this.is_expanded)
    },
    
    /**
     * 获取自动补全建议函数
     * 支持级联筛选：配置 filter_ref 时，每次触发时从 query 动态读取关联字段的当前值
     * 
     * 配置示例：
     * { table: "machine", column: "manufacturer",
     *   filter_ref: "query",
     *   filter_columns: { data_source: "mac_data_source" }
     * }
     * 等价于后端查询: filter_columns = { data_source: this.query.mac_data_source }
     */
    getSuggestions(item_query) {
      // 无级联配置：直接复用全局方法（性能最优）
      if (!item_query.filter_ref) {
        return this.$querySuggestions(item_query)
      }

      // 有级联配置：每次触发时动态解析关联字段的当前值
      return (input, cb) => {
        const params = { ...item_query }
        const source = this[item_query.filter_ref]  // 如 this.query
        params.filter_columns = Object.fromEntries(
          Object.entries(item_query.filter_columns).map(
            ([key, ref_prop]) => [key, source[ref_prop] ?? null]
          )
        )
        delete params.filter_ref  // 不传给后端
        this.$querySuggestions(params)(input, cb)
      }
    },

    /**
     * 处理搜索
     */
    handleSearch() {
      this.$emit("search", this.query)
    },
    
    /**
     * 处理重置
     * 恢复到初始默认值（而非全部置空），分页回到第一页
     */
    handleReset() {
      Object.keys(this.query).forEach(key => {
        this.$set(this.query, key, this.default_query[key] !== undefined ? this.default_query[key] : null)
      })
      
      // 触发重置事件
      this.$emit("reset", this.query)
    }
  }
}
</script>

<style lang="scss" scoped>
// 样式已在全局 index.scss 中定义
// 此处无需额外样式
</style>
