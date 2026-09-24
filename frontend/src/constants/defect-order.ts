/**
 * 缺陷类型业务展示顺序（前端展示规则）
 *
 * ## 业务约定（注射成型领域知识）
 *
 * - 常见缺陷排前面（用户最常遇到的优先展示，方便快速选择）
 * - 不常见缺陷排后面
 *
 * ## 顺序来源
 *
 * 与 `HsMoldingWeb/src/utils/process_const.ts` 中的 `defects_const` 对齐：
 * - 现场经验排序
 * - 顺序变更时**只改本文件**，不需要改 DB
 *
 * ## 与后端的关系
 *
 * - 后端 `listRuleKeywords` 只按系统字段（id / created_at）排序，**不保证业务排序**
 * - 后端响应包含的缺陷 keyword（category='defect'）会按本表前移
 * - 后端响应中未在本表出现的 keyword 保持原顺序排在末尾
 * - DB keyword 的 `keyword_alias` 与本表字符串完全一致时才命中（区分空格 / 大小写）
 *
 * ## 匹配 key
 *
 * - 匹配使用 `keyword_alias`（中文显示名），不是 `keyword_name`（英文 code）
 * - 原因：旧版本数据用中文别名，业务侧习惯也是看中文
 *
 * ## 注意
 *
 * - **不在本表中的 keyword 视为"不常见"**，排到末尾
 * - 如果某天"阴阳面"被频繁投诉，把它从 17 上移到合适位置即可，**无需改后端**
 * - 如果新缺陷变常见，加进本表合适位置即可
 */
export const COMMON_DEFECT_ORDER: string[] = [
  '短射',     // SHORTSHOT
  '缩水',     // SHRINKAGE
  '飞边',     // FLASH
  '气纹',     // GASVEINS
  '熔接痕',   // WELDLINE
  '料花',     // MATERIALFLOWER
  '困气',     // AIRTRAP
  '色差',     // ABERRATION
  '烧焦',     // BURN
  '水波纹',   // WATERRIPPLE
  '脱模不良', // HARDDEMOLDING
  '顶白',     // TOPWHITE
  '变形',     // WARPING
  '尺寸偏大', // OVERSIZE
  '尺寸偏小', // UNDERSIZE
  '浇口印',   // GATEMARK
  '阴阳面',   // SHADING
]

/**
 * 对 RuleKeyword[] 按常见缺陷顺序排序
 *
 * 排序规则：
 * 1. 双方都命中 COMMON_DEFECT_ORDER → 按该顺序排
 * 2. 只有 a 命中 → a 排前
 * 3. 只有 b 命中 → b 排前
 * 4. 都不命中 → 保持原顺序（依赖 Array.sort 的稳定性）
 *
 * 注意：
 * - 不修改原数组，返回新数组（computed 中更安全）
 * - 匹配 key 是 keyword_alias（中文），如果 alias 为空则降级为 keyword_name
 * - 完全等价比较，不做模糊匹配（保持规则简单可预测）
 */
export function sortDefectsByCommon<
  T extends { keyword_name: string; keyword_alias?: string | null },
>(defects: T[]): T[] {
  const orderMap = new Map<string, number>()
  COMMON_DEFECT_ORDER.forEach((name, idx) => orderMap.set(name, idx))

  // 用 indexed 包装以保证原顺序稳定性（都不在表中时按原顺序）
  const indexed = defects.map((d, originalIdx) => ({ d, originalIdx }))
  indexed.sort((a, b) => {
    const aKey = a.d.keyword_alias || a.d.keyword_name
    const bKey = b.d.keyword_alias || b.d.keyword_name
    const aOrder = orderMap.get(aKey)
    const bOrder = orderMap.get(bKey)
    if (aOrder !== undefined && bOrder !== undefined) return aOrder - bOrder
    if (aOrder !== undefined) return -1
    if (bOrder !== undefined) return 1
    // 都不在表中：保持原顺序（stable）
    return a.originalIdx - b.originalIdx
  })
  return indexed.map(({ d }) => d)
}