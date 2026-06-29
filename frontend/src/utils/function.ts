/*
 * @breif: 校验接口返回值
 * @params: data
 * @return: bool
 */
export function isValidData(data: any) {
  if (data == null || data == undefined) {
    return false
  } else if (JSON.stringify(data) == "{}") {
    return false
  } else if (JSON.stringify(data) == "[]") {
    return false
  }
  return true
}

export function numberToString(value: any) {
  if (value)
    return String(value)
  else
    return null
}

// 拷贝对象的值
export function updateObjectProperties(target: any, source: any) {
  Object.keys(source).forEach(key => {
    if (Object.keys(target).includes(key)) {
      target[key] = source[key]
    }
  })
}

// 同步数组
export function syncArray(target: any, source: any, initialItem: any) {
  const cur_val = source.length
  const bef_val = target.length

  if (bef_val < cur_val) {
    for (let i = bef_val; i < cur_val; ++i) {
      target.push(structuredClone(initialItem))
    }
  } else {
    target.length = cur_val
  }
}


// 创建随机字符串
export function generateRandomString(prefix: string = "", length: number) {
  let result = prefix
  const timestamp = Date.now().toString(36) // 将时间戳转换为36进制字符串
  const characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
  result += timestamp
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length))
  }
  return result
}
