export function initArray(length: Number, value: any) {
  let ret =[]
  for(let i=0;i<length;++i) {
    if(typeof(value)==='object' && value !== null) {
      if(Array.isArray(value)) {
        ret.push(Object.assign([], value))
      } else {
        ret.push(Object.assign({}, value))
      }
    } else{
      ret.push(value)
    }
  }
  return ret
}

// 拷贝array的内容，不要改变source array的长度
export function deepCopyArray(source: any, target: any) {
  for(let i=0;i<target.length;++i) {
    let item = target[i]
    if(Array.isArray(item)) {
      deepCopyArray(source[i], item)
    } else {
      source[i] = item
    }
  }
}

// 拷贝object，不要修改object中array的长度
export function deepCopyObject(source: any, target: any) {
  for(let item in target){
    if(Array.isArray(target[item])) {
      deepCopyArray(source[item], target[item])
    } else {
      if(source.hasOwnProperty(item)){
        source[item] = target[item]
      }
    }
  }
}

