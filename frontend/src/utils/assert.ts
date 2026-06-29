import { getToken } from "./auth"


export function getFullFileUrl(assertRelativeUrl: string) {
  // console.log(process.env.NODE_ENV)
  if (!assertRelativeUrl) {
    return ""
  }

  if (process.env.NODE_ENV == "development") {
    return "http://localhost/storage/" + assertRelativeUrl
  }

  return window.location.origin + "/storage/" + assertRelativeUrl

}


export function getFileDownloadUrl(uuid: string) {
  if (!uuid) {
    return ""
  }
  const token = getToken()
  return `/api/files/${uuid}/download/?token=${encodeURIComponent(token)}`
}

export function getFilePreviewUrl(uuid: string) {
  if (!uuid) {
    return ""
  }
  const token = getToken()
  return `/api/files/${uuid}/preview/?token=${encodeURIComponent(token)}`
}

export function getReportDownloadUrl(path: string) { 
  if (!path) {
    return ""
  }
  const token = getToken()
  return `/api/reports/download/${path}/?token=${encodeURIComponent(token)}`
}