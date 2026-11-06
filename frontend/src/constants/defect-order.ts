/**
 * 缺陷类型业务展示顺序（前端展示规则）
 * - 常见缺陷排前面（现场经验排序），顺序变更只改本文件、不改 DB
 * - 匹配用 keyword_alias（中文显示名）而非 keyword_name（英文 code），需完全一致才命中
 * - 后端 listRuleKeywords 只按 id/created_at 排序、不保证业务顺序；后端返回中未在本表的 keyword 视为「不常见」排到末尾
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
 * 排序规则：双方都命中 COMMON_DEFECT_ORDER → 按该顺序排；只有一方命中 → 命中方排前；都不命中 → 保持原顺序
 * 注意：不修改原数组，返回新数组（computed 中更安全）；匹配 key 是 keyword_alias（为空时降级为 keyword_name），完全等价比较不做模糊匹配
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