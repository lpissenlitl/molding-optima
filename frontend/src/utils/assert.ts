/**
 * 文件/报表 URL 工具
 *
 * 历史版本：
 * - `getToken` 来自 `./auth`（Vuex 时代，现已移除）
 * - 2026-09：auth 模块已删除，token 迁移到 Pinia useUserStore().token
 *   （与 request.ts 的 token 来源一致）
 */
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
