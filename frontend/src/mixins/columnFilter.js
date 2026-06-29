/**
 * 表格列筛选 Mixin
 * 
 * 提供通用的列筛选功能，支持：
 * - 动态提取列的唯一值
 * - 多值筛选
 * - 与分页协同工作
 * 
 * @example
 * // 在组件中使用
 * import ColumnFilterMixin from '@/mixins/columnFilter'
 * 
 * export default {
 *   mixins: [ColumnFilterMixin],
 *   data() {
 *     return {
 *       // 需要筛选的列配置
 *       filterable_columns: ['status', 'device_id', 'type']
 *     }
 *   },
 *   methods: {
 *     // 获取数据后调用
 *     fetchData() {
 *       // ... 获取数据
 *       this.alarm_list = response.data.items
 *       
 *       // 更新列筛选选项
 *       this.updateAllColumnFilters(this.alarm_list)
 *     }
 *   }
 * }
 */

export default {
  data() {
    return {
      // 列筛选配置（由子类定义 filterableColumns）
      column_filters: {},
      
      // 筛选弹窗可见性
      filter_popover_visible: {}
    }
  },
  
  methods: {
    /**
     * 初始化列筛选配置
     * @param {string[]} columns - 需要筛选的列名数组
     */
    initColumnFilters(columns) {
      if (!columns || !Array.isArray(columns)) {
        console.warn("filterable_columns must be an array")
        return
      }
      
      columns.forEach(prop => {
        this.$set(this.column_filters, prop, {
          prop,
          values: [],
          all_values: []
        })
        this.$set(this.filter_popover_visible, prop, false)
      })
    },
    
    /**
     * 从数据中提取某列的所有唯一值
     * @param {string} prop - 列字段名
     * @param {Array} data - 数据数组
     * @returns {Array} 唯一值数组
     */
    extractColumnUniqueValues(prop, data) {
      if (!data || !Array.isArray(data)) {
        return []
      }
      
      const values = new Set()
      data.forEach(row => {
        const value = row[prop]
        if (value !== null && value !== undefined && value !== "") {
          // 处理对象类型的值（如 { id: 1, name: 'test' }）
          if (typeof value === "object") {
            // 尝试提取常用字段
            const extractValue = value.id || value.code || value.name || value.label || JSON.stringify(value)
            values.add(extractValue)
          } else {
            values.add(value)
          }
        }
      })
      
      // 排序并返回
      return Array.from(values).sort((a, b) => {
        // 数字排序
        if (typeof a === "number" && typeof b === "number") {
          return a - b
        }
        // 字符串排序
        return String(a).localeCompare(String(b), "zh-CN")
      })
    },
    
    /**
     * 更新单个列的筛选选项
     * @param {string} prop - 列字段名
     * @param {Array} data - 数据数组
     */
    updateColumnFilterOptions(prop, data) {
      if (!this.column_filters[prop]) {
        this.$set(this.column_filters, prop, {
          prop,
          values: [],
          all_values: []
        })
      }
      
      this.column_filters[prop].all_values = this.extractColumnUniqueValues(prop, data)
    },
    
    /**
     * 更新所有列的筛选选项
     * @param {Array} data - 数据数组
     */
    updateAllColumnFilters(data) {
      if (!this.filterable_columns || !Array.isArray(this.filterable_columns)) {
        return
      }
      
      this.filterable_columns.forEach(prop => {
        this.updateColumnFilterOptions(prop, data)
      })
    },
    
    /**
     * 列筛选变化处理
     * @param {string} prop - 列字段名
     */
    handleColumnFilterChange(prop) {
      // 预留接口，子类可以重写实现实时预览
      // this.applyAllFilters()
    },
    
    /**
     * 应用列筛选
     * @param {string} prop - 列字段名
     */
    applyColumnFilter(prop) {
      this.filter_popover_visible[prop] = false
      this.resetPagination()
      this.fetchData()
    },
    
    /**
     * 清空列筛选
     * @param {string} prop - 列字段名
     */
    clearColumnFilter(prop) {
      if (this.column_filters[prop]) {
        this.column_filters[prop].values = []
      }
      this.filter_popover_visible[prop] = false
      this.resetPagination()
      this.fetchData()
    },
    
    /**
     * 清空所有列筛选
     */
    clearAllColumnFilters() {
      if (this.column_filters) {
        Object.keys(this.column_filters).forEach(prop => {
          this.column_filters[prop].values = []
        })
      }
      this.filter_popover_visible = {}
      this.initColumnFilters(this.filterable_columns)
    },
    
    /**
     * 重置分页
     */
    resetPagination() {
      if (this.pagination) {
        this.pagination.current_page = 1
      }
    },
    
    /**
     * 构建列筛选参数
     * @returns {Object} 筛选参数字典
     */
    buildColumnFilterParams() {
      const params = {}
      
      if (!this.column_filters) {
        return params
      }
      
      Object.keys(this.column_filters).forEach(prop => {
        const filter = this.column_filters[prop]
        if (filter && filter.values && filter.values.length > 0) {
          // 多值用逗号分隔
          params[prop] = filter.values.join(",")
        }
      })
      
      return params
    },
    
    /**
     * 合并筛选参数（顶部筛选 + 列筛选）
     * @param {Object} baseParams - 基础参数（顶部筛选）
     * @returns {Object} 合并后的参数
     */
    mergeFilterParams(baseParams) {
      const params = { ...baseParams }
      const columnFilterParams = this.buildColumnFilterParams()
      
      // 列筛选优先级更高，覆盖基础参数
      Object.keys(columnFilterParams).forEach(key => {
        if (columnFilterParams[key]) {
          params[key] = columnFilterParams[key]
        }
      })
      
      return params
    },
    
    /**
     * 判断列是否有激活的筛选
     * @param {string} prop - 列字段名
     * @returns {boolean}
     */
    isColumnFilterActive(prop) {
      return this.column_filters[prop]?.values?.length > 0
    },
    
    /**
     * 获取列的筛选图标类名
     * @param {string} prop - 列字段名
     * @returns {string}
     */
    getColumnFilterIconClass(prop) {
      return `el-icon-arrow-down filter-icon ${this.isColumnFilterActive(prop) ? "filter-active" : ""}`
    }
  },
  
  mounted() {
    // 自动初始化
    if (this.filterable_columns) {
      this.initColumnFilters(this.filterable_columns)
    }
  }
}
