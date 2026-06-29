//获取本地存储中存储的单值
export function getLocalStorageValue(key: string) {
  return localStorage.getItem(key);
}

//获取本地存储中的对象
export function getLocalStorageObject(key: string) {
  return JSON.parse(<string>localStorage.getItem(key));
}

//保存单值到本地存储
export function saveLocalStorageValue(key:string, value:any) {
  localStorage.setItem(key, value);
}

//保存对象到本地存储
export function saveLocalStorageObject(key:string, object:object) {
  localStorage.setItem(key, JSON.stringify(object));
}

//删除本地存储中键值对
export function removeLocalStorage(key:string) {
  localStorage.removeItem(key);
}
