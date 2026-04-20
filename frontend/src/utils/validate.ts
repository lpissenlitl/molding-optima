import any = jasmine.any;

export const isValidUsername = (str: string) => str.replace(/^\s+|\s+$/g,'').length >= 0;

export const isExternal = (path: string) => /^(https?:|mailto:|tel:)/.test(path);

export function isEmptyObject(e: object) {
  var t;
  for (t in e)
      return !1;
  return !0
}

export function hasString(data: any){
  if(data){
    if(typeof(data)==='object'){
      if(Array.isArray(data)){
        //是数组
        for(let i = 0; i < data.length; ++ i){
          if(hasString(data[i])){
            return true
          }
        }
      } else{
        //是字典
        for(let item in data){
          if(hasString(data[item])){
            return true
          }
        }
      }
    } else{
      if(typeof(data)==='string'){
        return true
      }
    }
  }
  return false
}

export function hasNull(data:any){
  if(data||data === 0){
    if(typeof(data)==='object'){
      if(Array.isArray(data)){
        //是数组
        for(let i = 0; i < data.length; ++ i){
          if(hasNull(data[i])){
            data[i] = typeof(data[i]) == 'string' ? "" : 0
            return true
          }
        }
      } else{
        //是字典
        for(let item in data){
          if(hasNull(data[item])){
            data[item] = typeof(data[item]) == 'string' ? "" : 0
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

export function checkNumberFormat(value:any, fixed=2) {
  if (value == "") {
    return null
  } else if (value == "0") {
    return "0"
  }
  let outputs = null
  if (fixed === 0) {
    outputs = value.match(/^[1-9][0-9]*/)
  } else {
    let regExp = new RegExp('^([1-9][0-9]*.[0-9]{0,' + fixed + '})|(0[.][0-9]{0,' + fixed + '})|([1-9][0-9]*)')
    outputs = value.match(regExp)
  }

  if (outputs) {
    return outputs[0]
  } else {
    return null
  }
}

export function checkProcessFormat(value:any, fixed=2, max_set=0) {
  if (value == "") {
    return null
  } else {
    if (fixed === 0) {
      return Number(value).toFixed(fixed)
    } else {
      let point = String(value).indexOf('.')
      if ( point > 0 && (String(value).length - 1) > (point + fixed)) {
        return Number(value).toFixed(fixed)
      }
      return Math.abs(value)
    }
  } 
}