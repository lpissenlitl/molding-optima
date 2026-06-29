/**
 * 仅将 source 中存在于 target 的键值对赋值给 target（浅拷贝）
 * - 不会添加 source 中 target 没有的新字段
 * - 不会删除 target 中的任何字段
 * - 只作用于 target 自身可枚举属性（不处理原型链）
 *
 * @param {Object} target - 目标对象（会被修改）
 * @param {Object} source - 源对象
 * @returns {Object} 修改后的 target
 */
export function assignExistingKeys(target: any, source: any) {
  if (!target || typeof target !== "object" || !source || typeof source !== "object") {
    return target
  }

  // 遍历 target 自身的所有可枚举 key
  Object.keys(target).forEach(key => {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      target[key] = source[key]
    }
  })

  return target
}