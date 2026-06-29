/**
 * 创建一个长度为 length 的数组，每个元素是 value 的独立副本。
 * - 基本类型：直接复用
 * - 数组：浅拷贝（[...value]）
 * - 普通对象：浅拷贝（{...value}）
 * - null / undefined / 非对象：直接使用
 */
export function initArray<T>(length: number, value: T): T[] {
  if (length <= 0) return []

  // 提前判断一次 value 类型，避免在循环中重复判断
  let factory: () => T

  if (value === null || typeof value !== "object") {
    // 基本类型或 null：直接复用
    factory = () => value
  } else if (Array.isArray(value)) {
    // 数组：返回新数组（浅拷贝）
    factory = () => [...value] as T
  } else if (value instanceof Date) {
    // 可选：特殊对象处理（如 Date）
    factory = () => new Date(value) as unknown as T
  } else if (value instanceof RegExp) {
    factory = () => new RegExp(value.source, value.flags) as unknown as T
  } else {
    // 普通对象：返回新对象（浅拷贝）
    factory = () => ({ ...value })
  }

  return Array.from({ length }, factory)
}

// 拷贝array的内容，不要改变source array的长度
export function deepCopyArray(source: any, target: any) {
  for (let i = 0;i < target.length;++i) {
    const item = target[i]
    if (Array.isArray(item)) {
      deepCopyArray(source[i], item)
    } else {
      source[i] = item
    }
  }
}

// 拷贝object，不要修改object中array的长度
export function deepCopyObject(source: any, target: any) {
  for (const item in target) {
    if (Array.isArray(target[item])) {
      deepCopyArray(source[item], target[item])
    } else {
      if (source.hasOwnProperty(item)) {
        source[item] = target[item]
      }
    }
  }
}


export function arrayToMap(array: any[]) {
  return Object.fromEntries(array.map(item => [item.value, item.label]))
}