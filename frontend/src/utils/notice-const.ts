// 通知状态 OPTIONS
export const notice_status_options =  [
  { label: "待发送", value: "PENDING" },
  { label: "发送成功", value: "SUCCESS" },
  { label: "发送失败", value: "FAILED" },
  { label: "发送超时", value: "TIMEOUT" },
  { label: "已处理", value: "PROCESSED" },
  { label: "已删除", value: "DELETED" },
]

// 通知状态 MAP
export const notice_status_map = Object.fromEntries(notice_status_options.map(item => [item.value, item.label]))