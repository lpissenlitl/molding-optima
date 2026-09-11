/**
 * 单位换算抽屉（命令式 API，类似 $message）
 *
 * 用法：
 * ```ts
 * import { openUnitConversionDrawer } from '@/utils/unit-conversion-drawer'
 *
 * // 任意页面（注射单元、锁模、模具等）
 * <el-button @click="openConverter">单位换算</el-button>
 *
 * function openConverter() {
 *   openUnitConversionDrawer({
 *     macTrademark: 'HTF300W',
 *     injectorInfo: injection_machine.injection_units[activeIdx],
 *     injectorLabel: `注射部件-#${activeIdx + 1}（${unit_code ?? '-'}）`,
 *   })
 * }
 * ```
 *
 * 设计要点：
 * - 通过 createApp + mount 动态挂载到 body，与主 App 解耦
 * - 单例：重复调用时若已存在则忽略，避免多层抽屉叠加
 * - 关闭动画完成后（350ms）卸载 DOM 与 app 实例，避免内存泄漏
 * - 新 mount 的 app 不继承主 App 的 ElementPlus / AppIcon 注册，
 *   故在本文件内单独 use/component，确保组件能正常渲染
 * - injectorLabel 用于顶部提示当前引用的是哪部分数据，让用户清晰知道上下文
 */
import { createApp, h, type App } from 'vue'
import ElementPlus from 'element-plus'
import { Icon } from '@iconify/vue'
import UnitConversionDrawer from '@/components/UnitConversionDrawer.vue'

const SINGLETON_ATTR = 'data-unit-conversion-drawer-singleton'
const UNMOUNT_DELAY = 350 // el-drawer 关闭动画默认 300ms，留 50ms 缓冲

export interface OpenUnitConversionDrawerOptions {
  /** 机器型号（drawer 内显示为默认值，可编辑） */
  macTrademark?: string | null
  /**
   * 注射单元信息（当前激活 tab 的注射单元对象）
   * - 取 screw_diameter 作为默认螺杆直径
   * - 用户在 drawer 内可手动覆盖
   */
  injectorInfo?: Record<string, any> | null
  /**
   * 当前射台的显示标签（仅用于顶部提示，不参与换算逻辑）
   * - 示例："注射部件-#1（射台编号 A）"
   * - 不传则不显示提示条
   */
  injectorLabel?: string
}

export function openUnitConversionDrawer(
  opts: OpenUnitConversionDrawerOptions = {},
): void {
  // 单例：避免重复打开
  if (document.querySelector(`[${SINGLETON_ATTR}]`)) return

  const container = document.createElement('div')
  container.setAttribute(SINGLETON_ATTR, '')
  document.body.appendChild(container)

  const app: App = createApp({
    setup() {
      return () =>
        h(UnitConversionDrawer, {
          macTrademark: opts.macTrademark ?? null,
          injectorInfo: opts.injectorInfo ?? null,
          injectorLabel: opts.injectorLabel,
          onClose: handleClose,
        })
    },
  })

  // 命令式挂载的 app 不继承主 App 注册的插件/组件
  app.use(ElementPlus)
  app.component('AppIcon', Icon)

  app.mount(container)

  function handleClose() {
    setTimeout(() => {
      app.unmount()
      container.remove()
    }, UNMOUNT_DELAY)
  }
}
