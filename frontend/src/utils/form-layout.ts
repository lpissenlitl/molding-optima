/**
 * 表单布局工具函数
 *
 * 设计目标：
 * - 让业务方定义 flat items 数组（只关心字段顺序 + 列宽）
 * - 工具函数自动按 span 总和分行，无需业务方手动分组
 *
 * 适用场景：
 * - 基于 Element Plus el-col span 系统的响应式表单布局
 * - 一行 24 栅格：通过 columns 参数切换 2/3/4 列布局（默认 4 列）
 *
 * @example 基础用法（默认 4 列布局）
 * ```ts
 * import { groupIntoRows } from '@/utils/form-layout'
 *
 * const items = [
 *   { type: 'input' },             // 默认 span=6（4 列布局）
 *   { type: 'input', span: 16 },   // 跨 2 列
 *   { type: 'select' },            // span=6
 *   { type: 'textarea', span: 24 }, // 占满整行
 * ]
 *
 * const rows = groupIntoRows(items)
 * // [
 * //   [items[0], items[1], items[2]],  // 6 + 16 = 22 → 一行
 * //   [items[3]],                       // 24 → 占满一行
 * // ]
 * ```
 *
 * @example 指定列数
 * ```ts
 * // 2 列布局（每项默认 span=12）
 * groupIntoRows(items, { columns: 2 })
 *
 * // 3 列布局（每项默认 span=8）
 * groupIntoRows(items, { columns: 3 })
 * ```
 */

/**
 * 行分组算法的最小接口
 * - 业务方只需保证 item 有 `type` 和 `span` 字段（可选）
 * - 通过泛型约束，业务方可以传入任何包含这两个字段的类型
 */
export interface RowGroupItem {
  type?: string
  span?: number
}

/**
 * groupIntoRows 配置选项
 */
export interface GroupIntoRowsOptions {
  /**
   * 一行几列布局（默认 4）
   * - columns=2 → 每项默认 span=12（2 列布局）
   * - columns=3 → 每项默认 span=8（3 列布局）
   * - columns=4 → 每项默认 span=6（4 列布局，默认）
   *
   * 算法：defaultSpan = floor(totalSpan / columns)
   * 提示：业务方仍可在 item 上单独指定 span 覆盖默认值（如跨列）
   */
  columns?: number

  /**
   * 一行的总栅格数（默认 24，对应 Element Plus el-col span 系统）
   * 通常无需修改，除非你用的是 12 栅格或其他栅格制
   */
  totalSpan?: number
}

/**
 * 自动分行算法：将 flat items 按 span 总和自动分组
 *
 * 规则：
 *   1. 默认每个 item span = totalSpan / columns（向下取整）
 *   2. divider 类型 span 自动设为 totalSpan（强制单独占一行）
 *   3. 累计 span 超 totalSpan → 自动换行
 *   4. span >= totalSpan（占满项）→ 单独占一行
 *
 * 默认 columns=4（每项 span=6），适合短字段密集的场景；
 * 长字段表单可在调用时显式传 { columns: 2 } 或 { columns: 3 }。
 *
 * @param items - flat 字段数组（业务方只关心顺序 + 列宽）
 * @param options - 配置选项（columns / totalSpan）
 * @returns 分行后的二维数组（每行是一个 el-row）
 */
export function groupIntoRows<T extends RowGroupItem>(
  items: T[],
  options: GroupIntoRowsOptions = {}
): T[][] {
  const totalSpan = options.totalSpan ?? 24
  const columns = options.columns ?? 4
  // 每列默认 span（如 columns=4, totalSpan=24 → span=6）
  const defaultSpan = Math.floor(totalSpan / columns)

  const rows: T[][] = []
  let currentRow: T[] = []
  let currentSpan = 0

  /**
   * 将当前累积的行刷入 rows，并重置状态
   *
   * 关键：这里给每项 item 强制设置 span 字段（自动 fallback）
   * 这样业务方模板里直接 :span="item.span" 即可，不用再处理 fallback
   * 不修改原 item，而是返回带 span 的新对象
   */
  const flush = () => {
    if (currentRow.length > 0) {
      const processedRow = currentRow.map((item) => ({
        ...item,
        span: item.span ?? (item.type === 'divider' ? totalSpan : defaultSpan),
      }))
      rows.push(processedRow)
      currentRow = []
      currentSpan = 0
    }
  }

  for (const item of items) {
    // divider 类型 span 自动 = totalSpan（强制单独占一行）
    const span = item.span ?? (item.type === 'divider' ? totalSpan : defaultSpan)

    // divider / 占满项 → 单独占一行
    if (item.type === 'divider' || span >= totalSpan) {
      flush()
      rows.push([item])
      continue
    }

    // 当前行放不下 → 换行
    if (currentSpan + span > totalSpan) {
      flush()
    }

    currentRow.push(item)
    currentSpan += span
  }

  // 处理最后一行
  flush()
  return rows
}