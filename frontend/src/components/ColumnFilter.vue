<template>
  <div class="column-header">
    <span>{{ label }}</span>
    <div class="filter-area">
      <el-popover
        v-model="visible"
        placement="bottom-end"
        trigger="click"
        :width="260"
        popper-class="column-filter-popover"
      >
        <div class="filter-content">
          <!-- 标题和清空按钮 -->
          <div class="filter-header">
            <span>{{ title || `筛选${label}` }}</span>
            <el-button type="text"
              size="small"
              @click="handleClear"
              :disabled="includeList.length === 0 && excludeList.length === 0"
            >
              清空
            </el-button>
          </div>

          <!-- 搜索框（选项过多时显示） -->
          <el-input
            v-if="showSearch && all_values.length > 6"
            v-model="search_keyword"
            placeholder="搜索..."
            prefix-icon="el-icon-search"
            size="small"
            clearable
            class="filter-search"
          />

          <!-- 全选/反选 -->
          <div v-if="all_values.length > 2" class="filter-actions">
            <el-button type="text" size="small" @click="handleSelectAll">
              全选
            </el-button>
            <el-button type="text" size="small" @click="handleInvert">
              反选
            </el-button>
          </div>

          <!-- 复选框列表：勾选 = 包含 -->
          <el-checkbox-group
            v-model="checked_values"
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

          <!-- 空状态提示（避免数据为空时中间一大块空白） -->
          <div v-if="filteredValues.length === 0" class="filter-empty">
            <i class="el-icon-warning-outline"></i>
            <span>暂无可筛选项</span>
          </div>

          <!-- 底部按钮 -->
          <div class="filter-footer">
            <el-button size="small" @click="handleCancel">
              取消
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="handleConfirm"
            >
              确定
            </el-button>
          </div>
        </div>

        <!-- 筛选图标：Excel 风格（漏斗 + 下拉三角） -->
        <!-- 注意：触发器用 #reference slot 写法，避免 el-popover 的 ElOnlyChild 检查报多根节点警告 -->
        <template #reference>
          <div
            class="filter-trigger"
            :class="{ active: hasActive }"
            :style="iconStyle"
            role="button"
            aria-label="筛选"
          >
            <svg
              viewBox="0 0 16 16"
              width="16"
              height="16"
              :class="iconClass"
              aria-hidden="true"
            >
              <!-- 漏斗主体 -->
              <path
                d="M1 3.5 L5.5 8 v5 l4 -2 V8 L14 3.5 Z"
                fill="currentColor"
              />
              <!-- 下拉小三角 -->
              <path
                d="M11 11.5 L13.5 13 L11 14.5"
                stroke="currentColor"
                stroke-width="1.2"
                fill="none"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
        </template>
      </el-popover>
    </div>
  </div>
</template>

<script>
/**
 * ColumnFilter 列筛选组件
 *
 * 设计要点：
 *   - BaseTable 通过 enableColumnFilter 接入，对 filterable: true 的列自动渲染
 *   - 支持 include（正向筛选）模式；exclude 字段保留向后兼容但当前 UI 未启用排除项
 *   - SVG 漏斗图标 + active 高亮（借鉴 molding-expert-web ColumnFilter 设计）
 *   - 通过 value_map 保留原始类型，避免 bool/number 被字符串化导致后端匹配失败
 *   - 向后兼容旧 props `values`（视为 include）、`exclude: true`（视为所有 values 为排除）
 *
 * 三态选择扩展点（molding-expert-web 完整版）：
 *   - 当前 UI 只有 '' (不参与) ↔ 'in' (包含) 两态
 *   - 内部状态结构已支持三态 ('in' / 'ex' / '')，后续可加 UI 入口
 */
export default {
  name: "ColumnFilter",

  props: {
    // 列标签
    label: {
      type: String,
      required: true,
    },

    // 自定义标题
    title: {
      type: String,
      default: "",
    },

    // 当前包含筛选的值（向后兼容旧 props）
    values: {
      type: Array,
      default: () => [],
    },

    // 排除筛选的值（向后兼容旧 props）
    // - Array: 直接作为 exclude 列表
    // - true: 配合 values，把所有 values 视为排除（向后兼容旧 exclude=true 语义）
    exclude: {
      type: [Array, Boolean],
      default: false,
    },

    // 所有可选值
    all_values: {
      type: Array,
      default: () => [],
    },

    // 是否显示搜索框
    showSearch: {
      type: Boolean,
      default: true,
    },

    // 自定义图标类名
    iconClass: {
      type: String,
      default: "",
    },

    // 自定义图标样式
    iconStyle: {
      type: Object,
      default: null,
    },

    // 格式化标签的函数
    formatLabel: {
      type: Function,
      default: null,
    },
  },

  data() {
    return {
      visible: false,
      // 当前勾选项（与 el-checkbox-group 双向绑定，简单直观）
      checked_values: [],
      // 搜索关键字
      search_keyword: "",
    }
  },

  computed: {
    /**
     * 从 props.values 提取 include 列表
     * 兼容 exclude=true 时把所有 values 视为排除
     */
    includeList() {
      if (!Array.isArray(this.values)) return []
      if (this.exclude === true && this.values.length > 0) return []
      return [...this.values]
    },

    /**
     * 从 props.exclude 提取 exclude 列表
     * 兼容 exclude=true 时把 values 视为排除
     */
    excludeList() {
      if (Array.isArray(this.exclude)) return [...this.exclude]
      if (this.exclude === true && Array.isArray(this.values) && this.values.length > 0) {
        return [...this.values]
      }
      return []
    },

    /**
     * 是否有激活的筛选条件（用于图标高亮）
     */
    hasActive() {
      return this.includeList.length > 0 || this.excludeList.length > 0
    },

    /**
     * 搜索过滤后的值列表
     */
    filteredValues() {
      if (!this.search_keyword) return this.all_values
      const keyword = this.search_keyword.toLowerCase()
      return this.all_values.filter(value => {
        const displayValue = this.formatLabel
          ? this.formatLabel(value)
          : String(value)
        return displayValue.toLowerCase().includes(keyword)
      })
    },
  },

  watch: {
    visible(val) {
      if (val) {
        // 打开弹窗时从 props 同步当前勾选状态（避免与外部脱节）
        this.checked_values = [...this.includeList]
      }
    },
    values() {
      if (this.visible) {
        this.checked_values = [...this.includeList]
      }
    },
    exclude() {
      if (this.visible) {
        this.checked_values = [...this.includeList]
      }
    },
  },

  created() {
    // 初始化 checked_values 为当前 include
    this.checked_values = [...this.includeList]
  },

  methods: {
    /**
     * 复选框变化（仅同步内部状态，不立即 emit）
     */
    handleChange() {
      // 让用户点确定才 emit，cancel 会还原
    },

    /**
     * 确认筛选
     * payload 形态：{ include: [v1, v2], exclude: [] }
     */
    handleConfirm() {
      this.visible = false
      this.$emit("confirm", {
        include: [...this.checked_values],
        exclude: [...this.excludeList],
      })
    },

    /**
     * 取消操作（还原为 props 当前值）
     */
    handleCancel() {
      this.visible = false
      this.search_keyword = ""
      this.checked_values = [...this.includeList]
      this.$emit("cancel")
    },

    /**
     * 清空筛选
     */
    handleClear() {
      this.checked_values = []
      this.visible = false
      this.search_keyword = ""
      this.$emit("clear")
    },

    /**
     * 全选（仅作用于当前可见项，避免与搜索冲突）
     * 保留搜索之外的已选项 + 把当前可见项全部勾选
     */
    handleSelectAll() {
      const visible = new Set(this.filteredValues)
      const kept = this.checked_values.filter(v => !visible.has(v))
      this.checked_values = [...kept, ...this.filteredValues]
    },

    /**
     * 反选（仅作用于当前可见项）
     * 保留搜索之外的已选项 + 对可见项 toggle（已选取消、未选勾选）
     */
    handleInvert() {
      const visible = new Set(this.filteredValues)
      const kept = this.checked_values.filter(v => !visible.has(v))
      const newlyChecked = this.filteredValues.filter(v => !this.checked_values.includes(v))
      this.checked_values = [...kept, ...newlyChecked]
    },
  },
}
</script>

<style scoped>
.column-header {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}
.column-header > span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: inherit;
  padding-right: 28px;
}

/* filter 区绝对定位浮在右上角，label 占满剩余空间 */
.column-header .filter-area {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
}

/* Excel/飞书风格列筛选下拉：紧凑、紧凑、紧凑 */
.filter-content {
  padding: 8px;
  min-width: 220px;
  max-width: 280px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  padding: 0 2px 6px;
  border-bottom: 1px solid #EBEEF5;
}

.filter-header span {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.filter-search {
  margin-bottom: 6px;
}

.filter-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  padding: 0 2px;
}

.filter-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-height: 260px;
  overflow-y: auto;
  padding: 0 2px;
}

/* 复选框行高紧凑 + label 字体适中（覆盖 element-plus 默认） */
:deep(.el-checkbox) {
  margin-right: 0;
  margin-bottom: 0;
  height: 28px;
  display: flex;
  align-items: center;
}
:deep(.el-checkbox__label) {
  font-size: 13px;
  padding-left: 6px;
}

/* 空状态占位（避免大块空白） */
.filter-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 18px 8px;
  color: #909399;
  font-size: 12px;
}
.filter-empty i {
  color: #e6a23c;
  font-size: 13px;
}

/* Excel 风格筛选图标：默认浅灰、active 蓝色 */
.filter-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  cursor: pointer;
  color: #c0c4cc;
  border-radius: 3px;
  transition: color 0.2s, background-color 0.2s;
  vertical-align: middle;
  user-select: none;
}

.filter-trigger:hover {
  color: #409eff;
  background-color: #ecf5ff;
}

.filter-trigger.active {
  color: #409eff;
  background-color: #ecf5ff;
}

.filter-trigger svg {
  display: block;
  pointer-events: none;
}

.filter-footer {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #EBEEF5;
}
</style>