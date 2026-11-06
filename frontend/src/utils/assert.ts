/** 文件/报表 URL 工具；token 已从 Vuex 迁到 Pinia useUserStore().token（与 request.ts 一致） */

import { useUserStore } from '@/stores/user'

export function getFullFileUrl(assertRelativeUrl: string) {
  if (!assertRelativeUrl) {
    return ''
  }

  if (import.meta.env.DEV) {
    return 'http://localhost/storage/' + assertRelativeUrl
  }

  return window.location.origin + '/storage/' + assertRelativeUrl
}

export function getFileDownloadUrl(uuid: string) {
  if (!uuid) {
    return ''
  }
  const token = useUserStore().token
  return `/api/files/${uuid}/download/?token=${encodeURIComponent(token)}`
}

export function getFilePreviewUrl(uuid: string) {
  if (!uuid) {
    return ''
  }
  const token = useUserStore().token
  return `/api/files/${uuid}/preview/?token=${encodeURIComponent(token)}`
}

export function getReportDownloadUrl(path: string) {
  if (!path) {
    return ''
  }
  const token = useUserStore().token
  return `/api/reports/download/${path}/?token=${encodeURIComponent(token)}`
}
