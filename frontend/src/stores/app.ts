import { defineStore } from 'pinia'
import axios from 'axios'

/**
 * App Store — 应用全局配置
 *
 * - 系统级静态信息（品牌、版本、版权）由本 store 统一管理
 * - 系统状态 normal/degraded/down 由 /api/health/ 心跳更新
 */

export type SystemStatus = 'normal' | 'degraded' | 'down'

export const useAppStore = defineStore('app', {
  state: () => ({
    name: 'Molding Optima',
    shortName: 'Molding Optima',
    groupName: 'MoldingX Group',
    version: __APP_VERSION__,
    copyrightYear: 2026,
    copyrightHolder: 'Molding Optima',
    status: 'normal' as SystemStatus,
    pageSizeArray: [30, 100, 200] as number[],
  }),

  getters: {
    footerBrand: (state) => `v${state.version} · ${state.groupName}`,
    copyrightText: (state) => `© ${state.copyrightYear} ${state.copyrightHolder}`,
    statusLabel(state): string {
      const map: Record<SystemStatus, string> = {
        normal: '系统正常',
        degraded: '系统降级',
        down: '系统停服',
      }
      return map[state.status]
    },
    pageSizeOptions: (state): number[] => state.pageSizeArray,
  },

  actions: {
    setStatus(status: SystemStatus) {
      this.status = status
    },
    /*
     * 调用 /api/health/ 探测后端可用性
     * - 直接用裸 axios，不走 @/utils/request：
     *   1. request 拦截器在错误时会弹 ElMessage，health check 静默失败更合适
     *   2. health 接口无需 token，request 会注入 token 反而冗余
     * - 超时 5s（健康检查不应该长时间阻塞 UI）
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

  persist: {
    key: 'molding-optima:app',
    paths: ['status'],
  },
})