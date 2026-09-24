import { defineStore } from 'pinia'
import axios from 'axios'

/**
 * App Store — 应用全局配置
 *
 * 设计原则：
 * - 系统级静态信息（品牌、版本、版权、组织）由本 store 统一管理
 * - 业务组件不直接写死"Admin"、"Molding Optima"、"v0.2.0"等
 * - 系统状态（normal/degraded/down）由后端 /api/health/ 心跳更新
 *
 * 持久化：app 基本信息无需持久化（来自代码版本），状态可持久化
 */

export type SystemStatus = 'normal' | 'degraded' | 'down'

export const useAppStore = defineStore('app', {
  state: () => ({
    // 品牌
    name: 'Molding Optima',
    shortName: 'Molding Optima',
    groupName: 'MoldingX Group',

    // 版本（编译时从 package.json 注入，详情见 vite-env.d.ts）
    version: __APP_VERSION__,

    // 版权
    copyrightYear: 2026,
    copyrightHolder: 'Molding Optima',

    // 系统状态（normal = 正常 / degraded = 降级 / down = 停服）
    status: 'normal' as SystemStatus,

    // 分页大小选项（替代旧 Vuex store/modules/app.ts 的 pageSizeArray）
    pageSizeArray: [30, 100, 200] as number[],
  }),

  getters: {
    /** 左侧品牌区底部署名（如：v0.2.0 · MoldingX Group）*/
    footerBrand: (state) => `v${state.version} · ${state.groupName}`,

    /** 底部版权完整文本（如：© 2026 Molding Optima）*/
    copyrightText: (state) =>
      `© ${state.copyrightYear} ${state.copyrightHolder}`,

    /** 系统状态对应的中文标签 */
    statusLabel(state): string {
      const map: Record<SystemStatus, string> = {
        normal: '系统正常',
        degraded: '系统降级',
        down: '系统停服',
      }
      return map[state.status]
    },

    /** 列表页 page-sizes 选项（供 $pageSizeArray 全局方法透出）*/
    pageSizeOptions: (state): number[] => state.pageSizeArray,
  },

  actions: {
    /** 手动设置状态（保留给外部触发，如切换降级模式） */
    setStatus(status: SystemStatus) {
      this.status = status
    },

    /**
     * 调用 /api/health/ 探测后端可用性，更新 status
     *
     * 注意点：
     * - 直接用裸 axios，不走 @/utils/request：
     *   1. request 拦截器在错误时会弹 ElMessage，health check 静默失败更合适
     *   2. health 接口无需 token，request 会注入 token 反而冗余
     * - 调用方：login/index.vue onMounted
     * - 超时：5s（健康检查不应该长时间阻塞 UI）
     */
    async checkHealth() {
      try {
        await axios.get('/api/health/', { timeout: 5000 })
        this.status = 'normal'
      } catch {
        this.status = 'down'
      }
    },
  },

  // 持久化：仅 status（name/version 不需要持久化）
  persist: {
    key: 'molding-optima:app',
    paths: ['status'],
  },
})