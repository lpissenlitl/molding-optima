/** 特殊 keyword 标识符：用于前端识别有「特殊业务含义」的 keyword（如无缺陷），避免魔法字符串散落多处；后端由 init_rule_keyword 命令录入 */


/**
 * "无缺陷"keyword 标识符
 * - 业务场景：产品本轮试模没有缺陷，但工艺仍可优化（减少周期时间、提产能、降能耗）
 * - 前端识别约定：选中此 keyword 时 UI 需隐藏 level/position 字段，但 defect 对象仍保留完整结构（level=null, position=''）
 * - 此状态是有效的缺陷反馈输入，会触发算法优化（产能方向），与"跳过录入"语义不同
 * - 命名选择：DEFECTFREE 而非 NONE（None 容易产生"无关键字"的歧义）
 */
export const DEFECTFREE_KEYWORD_NAME = 'DEFECTFREE' as const