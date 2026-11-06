/** 仅将 source 中存在于 target 的键值对浅拷贝给 target：不新增字段、不删除字段、只作用于 target 自身可枚举属性（不处理原型链）；返回修改后的 target */

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