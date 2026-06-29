import { downloadReport } from "@/api"

/**
 * 从给定 URL 下载文件（自动从 URL 路径提取文件名）
 * @param url - 文件下载地址（如 "/api/reports/download/报告_A123.xlsx/"）
 * @param fallbackName - 可选：当无法从 URL 提取时的默认文件名
 */
export async function downloadFromUrl(url: string, fallbackName = "download.xlsx") {
  try {
    // 1. 从 URL 提取文件名
    let filename: string
    try {
      // 处理绝对或相对 URL
      const path = url.startsWith("http") 
        ? new URL(url).pathname 
        : url
      filename = path.split("/").filter(Boolean).pop() || fallbackName
    } catch (e) {
      filename = fallbackName
    }

    // 2. 发起下载请求
    const response = await downloadReport(url)
    console.log(response)
    const blob = response.data as Blob

    // 3. 触发浏览器下载
    const blobUrl = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = blobUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(blobUrl)
    document.body.removeChild(a)
  } catch (error) {
    console.error("Download failed:", error)
    throw error // 让调用者处理错误
  }
}