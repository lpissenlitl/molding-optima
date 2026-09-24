/**
 * 特殊 keyword 标识符
 *
 * 用于前端识别有"特殊业务含义"的 keyword（如无缺陷）。
 *
 * 设计原则：
 * - 避免在多处散落魔法字符串（如 'DEFECTFREE' / 'NONE'）
 * - 后端通过 init_rule_keyword 初始化命令录入这些 keyword
 * - 前端通过这里的常量识别并应用特殊 UI 行为
 *
 * 后端录入：backend/bootstrap/management/commands/init_rule_keyword.py
 */

/**
 * "无缺陷"keyword 标识符
 *
 * 业务场景：产品本轮试模没有缺陷，但工艺仍可优化（减少周期时间、提产能、降能耗）。
 *
 * 前端识别约定：选中此 keyword 时，UI 需隐藏 level/position 字段；
 * 但 defect 对象仍保留完整结构（level=null, position=''）。
 * 此状态是有效的缺陷反馈输入，会触发算法优化（产能方向），与"跳过录入"语义不同。
 *
 * 命名选择：DEFECTFREE 而非 NONE（None 容易产生"无关键字"的歧义）。
 */
export const DEFECTFREE_KEYWORD_NAME = 'DEFECTFREE' as const