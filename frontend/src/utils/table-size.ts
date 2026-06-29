
/* 自动计算 table 的高度 */
export function calculateTableHeight(
  min_height: number = 500, 
  offset: number = 220,
  divisor: number = 1
) {
  const resize_height = (window.innerHeight - offset) / divisor
  return Math.max(min_height, resize_height) + "px"
}