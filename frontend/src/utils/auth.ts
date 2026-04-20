import Cookies from 'js-cookie';

const TokenKey = 'hsmold_admin_token';
const IDKey = 'hsmold_admin_userid';
export const isNative = process.env.NODE_ENV === 'production' && process.env.IS_ELECTRON;

let myMap = new Map();


function setCookie(name: string, value:any) {
    if (isNative) {
      myMap.set(name, value)
    } else {
      Cookies.set(name, value)
    }
}

function removeCookie(name: string) {
  if (isNative) {
    myMap.delete(name)
  } else {
    Cookies.remove(name)
  }
}

function getCookie(name: string) {
  if (isNative) {
    return myMap.get(name)
  } else {
    return Cookies.get(name)
  }
}

export const getToken = () => getCookie(TokenKey);

export const setToken = (token: string) => setCookie(TokenKey, token);

export const removeToken = () => removeCookie(TokenKey);

export const getUserId = () => getCookie(IDKey);

export const setUserId = (id: any) => setCookie(IDKey, id);

export const removeUserId = () => removeCookie(IDKey);
