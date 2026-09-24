import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import pkg from './package.json'

export default defineConfig({
  // 构建时常量注入：版本号与 package.json 始终同步
  // 代码中使用 __APP_VERSION__ 即被静态替换为字符串字面量
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
  },
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        // 使用 Sass Modern API（消除 legacy 废弃警告）
        api: 'modern-compiler',
        // 全局注入 mixins（每个 <style lang="scss"> 块可用）
        additionalData: `@use "@/styles/mixins" as *;`,
      },
    },
  },
  server: {
    port: 9527,
    host: '0.0.0.0',
    open: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/storage': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
  },
})