/**
 * 规则模块公共常量
 *
 * 与后端 process/models/rules.py + RuleKeyword.fuzzy_level 联动。
 * 历史源：RuleMethodForm.vue 的局部常量（2026-09-20 抽离）。
 *
 * 用途：
 * - LEVEL_WORDS：根据 fuzzy_level 给出可选的 level 词（low/medium/high/...）
 * - DEFECT/PARAMETER_LEVEL_LABELS：level 词的中文标签（按 keyword.category 选一套）
 *
 * 命名约束：
 * - 不在这里定义 DEFECTFREE 这种"特殊 keyword 标识符"——见 constants/special-keywords.ts
 */

import type { FuzzyLevel } from '@/types/rule'

// ============================================================================
// level 词字典（fuzzy_level → 渐进式命名）
// ============================================================================
//
// 业界标准渐进式命名：每加一档在两端扩展（very_ / extremely_）。
// medium 永远在中心位置（对称）。
//
// 与后端规则 service 对齐：
// - 新规则用 medium（与后端 rule_matcher.py 一致）
// - 历史 1752 条数据用 mid（暂保留兼容，后续可一次性迁移）

export const LEVEL_WORDS: Record<FuzzyLevel, string[]> = {
  3: ['low', 'medium', 'high'],
  5: ['very_low', 'low', 'medium', 'high', 'very_high'],
  7: [
    'extremely_low',
    'very_low',
    'low',
    'medium',
    'high',
    'very_high',
    'extremely_high',
  ],
}

/**
 * action 调整量的预设「模糊量词」列表（LEVEL_WORDS 全集去重）。
 *
 * ⚠️ **当前未在表单中使用**。保留仅为备查/未来扩展。
 *
 * 背景：2026-09 讨论中曾考虑做成 el-select + allow-create + 预填这些词，
 * 但用户反馈「前端不该限制，后端自动判断 mamdani/tsk」，所以退回到 el-input。
 *
 * 如果未来需重新启用 el-select 模式，可直接复用：
 * ```vue
 * <el-select v-model="act.value" filterable allow-create
 *            default-first-option>
 *   <el-option v-for="w in FUZZY_AMOUNT_WORDS" :key="w" :label="w" :value="w" />
 * </el-select>
 * ```
 */
export const FUZZY_AMOUNT_WORDS: string[] = Array.from(
  new Set(Object.values(LEVEL_WORDS).flat()),
)

// ============================================================================
// level 词 → 中文标签（按 keyword.category 分两套）
// ============================================================================
//
// 背景：项目 1752 条历史规则的 rule_explanation 中，同一个 `low` 词在不同
// keyword 下中文不一样：
// - defect + low → 轻微  （例：SHORTSHOT_low  →  短射轻微）
// - parameter + low → 偏小  （例：MEL_low  →  计量终止位置偏小）
// 所以前端 dropdown 与 rule_explanation 都需按 keyword.category 选择对应标签。
//
// 档位与中文的对应（渐进式）：
// - 3 档：轻微 / 中等 / 严重（缺陷） ｜ 偏小 / 中等 / 偏大（参数）
// - 5 档：极轻微 / ... / 极严重  ｜ 极小 / ... / 极大
// - 7 档：极其轻微 / ... / 极其严重  ｜ 极其小 / ... / 极其大

export const DEFECT_LEVEL_LABELS: Record<string, string> = {
  low: '轻微',
  medium: '中等',
  high: '严重',
  very_low: '极轻微',
  very_high: '极严重',
  extremely_low: '极其轻微',
  extremely_high: '极其严重',
}

export const PARAMETER_LEVEL_LABELS: Record<string, string> = {
  low: '偏小',
  medium: '中等',
  high: '偏大',
  very_low: '极小',
  very_high: '极大',
  extremely_low: '极其小',
  extremely_high: '极其大',
}