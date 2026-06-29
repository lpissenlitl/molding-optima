
export const isValidUsername = (str: string) => str.replace(/^\s+|\s+$/g,"").length >= 0

export const isExternal = (path: string) => /^(https?:|mailto:|tel:)/.test(path)

export function isEmptyObject(e: object) {
  let t
  for (t in e)
    return !1
  return !0
}

export function hasString(data: any) {
  if (data) {
    if (typeof(data) === "object") {
      if (Array.isArray(data)) {
        //是数组
        for (let i = 0; i < data.length; ++ i) {
          if (hasString(data[i])) {
            return true
          }
        }
      } else {
        //是字典
        for (const item in data) {
          if (hasString(data[item])) {
            return true
          }
        }
      }
    } else {
      if (typeof(data) === "string") {
        return true
      }
    }
  }
  return false
}

export function hasNull(data:any) {
  if (data || data === 0) {
    if (typeof(data) === "object") {
      if (Array.isArray(data)) {
        //是数组
        for (let i = 0; i < data.length; ++ i) {
          if (hasNull(data[i])) {
            data[i] = typeof(data[i]) == "string" ? "" : 0
            return true
          }
        }
      } else {
        //是字典
        for (const item in data) {
          if (hasNull(data[item])) {
            data[item] = typeof(data[item]) == "string" ? "" : 0
            return true
          }
        }
      }
    }
    //是非空单值
    return false
  }
  return true
}

export function passMoldTestValidation(data: any) {
  if (data) {
    for (let i = 0; i < data.table_data.length; ++ i) {
      const table_data_item = data.table_data[i]
      if (hasNull(table_data_item)) {
        return i + 1
      }
    }
    return 0
  }
}


export function permissionReservation(user:any, row: any) {
  //如果是组织管理员,则可以编辑所有
  if (user.roles) {
    for (let i = 0 ;i < user.roles.length;i++) {
      if (user.roles[i].name === "组织管理员") {
        return true        
      }
    }
  }
  // 如果是制作组长,能编辑删除所在部门的约机
  if (user.permissions.indexOf("reservation_leader") != -1) {
    // console.log(user.department === row.production_department)
    if (user.department === row.production_department) {
      return true
    } else {
      return false
    }
  }
  // 如果是制作工程师,只能编辑和删除自己的约机
  else {
    if (user.engineer === row.production_engineer) {
      return true
    } else {
      return false
    }
  }
}


export function permissionTestingModify(user:any, row: any) {
  return true
}


export function formatNumber(value:any, fixed = 2) {
  console.log(value)
  if (value == "") {
    return null
  } else if (value == "0") {
    return "0"
  }
  // let outputs = value.match(/^([1-9][0-9]*)|([0-9].[0-9]{0, 2})/)
  // let outputs = value.match(/^0.[0-9]{0,2}/)
  // let outputs = value.match(/^[1-9][0-9]*.[0-9]{0,2}/)
  let outputs = null
  if (fixed === 0) {
    outputs = value.match(/^[1-9][0-9]*/)
  } else {
    // let regExp = new RegExp('(^[1-9][0-9]*.[0-9]{0,' + fixed + '}$)|(0[.][0-9]{0,' + fixed + '})|([1-9][0-9]*)')
    // let regExp = new RegExp('^([1-9][0-9]*.[0-9]{0,' + fixed + '})|(0.[0-9]{0,' + fixed + '})|([1-9][0-9]*)')
    // let regExp = new RegExp('^(0[.][0-9]{0,' + fixed + '})')
    // let regExp = new RegExp('^([1-9][0-9]*.[0-9]{0,' + fixed + '})|([1-9][0-9]*)')
    // outputs = value.match(/^([1-9][0-9]*.[0-9]{0,2})|(0.[0-9]{0,2})|([1-9][0-9]*)/)
    const regExp = new RegExp("^([1-9][0-9]*.[0-9]{0," + fixed + "})|(0[.][0-9]{0," + fixed + "})|([1-9][0-9]*)")
    outputs = value.match(regExp)
  }

  if (outputs) {
    return outputs[0]
  } else {
    return null
  }
}

export function checkProcessFormat(value: any, fixed = 2, max_set = 0) {
  // console.log(value)
  if (value == "") {
    return null
  } else {
    if (fixed === 0) {
      return Number(value).toFixed(fixed)
    } else {
      const point = String(value).indexOf(".")
      if ( point > 0 && (String(value).length - 1) > (point + fixed)) {
        return Number(value).toFixed(fixed)
      }
      return Math.abs(value)
    }
  } 
}
/**
 * 判断后端返回的数据是否为有效数据
 * - 有效：非 null、非 undefined、非空对象 {}
 * - 无效：null, undefined, {}, [], 以及其他无实际内容的结构
 *
 * @param {*} data - 从 API 返回的数据（通常是对象）
 * @returns {boolean} true 表示数据有效，false 表示无效（如空对象）
 */
export function isValidData(data: any) {
  // 排除 null 和 undefined
  if (data == null) {
    return false
  }

  // 如果是对象类型（且不是数组）
  if (typeof data === "object" && !Array.isArray(data)) {
    // 检查是否有自有可枚举属性
    return Object.keys(data).length > 0
  }

  // 其他类型（如字符串、数字、布尔值、数组等）视为有效
  // 如果你希望数组也必须非空，可取消下面注释：
  // if (Array.isArray(data)) {
  //   return data.length > 0;
  // }

  return true
}