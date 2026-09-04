<template>
  <div class="not-found-page">
    <!-- 装饰背景 -->
    <div class="decoration">
      <div class="grid-bg"></div>
      <div class="glow glow-1"></div>
      <div class="glow glow-2"></div>
    </div>

    <div class="content">
      <!-- Logo + 大数字 -->
      <div class="code-wrap">
        <div class="logo-ring">
          <AppIcon icon="mdi:alert-circle-outline" />
        </div>
        <div class="code">
          <span class="digit" v-for="(d, i) in digits" :key="i" :style="{ animationDelay: `${i * 0.15}s` }">
            {{ d }}
          </span>
        </div>
      </div>

      <!-- 标题与说明 -->
      <h1 class="title">页面不存在</h1>
      <p class="subtitle">Page Not Found</p>
      <p class="desc">
        您访问的页面可能已被移除、修改或暂时无法访问
      </p>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button type="primary" size="large" class="btn-primary" @click="goBack">
          <AppIcon icon="mdi:arrow-left" />
          <span>返回上一页</span>
        </el-button>
        <el-button size="large" class="btn-secondary" @click="goHome">
          <AppIcon icon="mdi:home-outline" />
          <span>返回登录</span>
        </el-button>
      </div>

      <!-- 装饰横线 -->
      <div class="divider">
        <span></span>
        <em>·  Molding Optima  ·</em>
        <span></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const digits = ['4', '0', '4']

const goBack = () => {
  // 如果有上一页则返回，否则跳登录
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/login')
  }
}

const goHome = () => {
  router.push('/login')
}
</script>

<style scoped lang="scss">
.not-found-page {
  @include fullscreen;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--theme-primary);
  color: #fff;
  position: relative;
  overflow: hidden;
  font-family:
    -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', sans-serif;
}

/* ============== 装饰背景 ============== */
.decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 1;
}

.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
}
.glow-1 {
  width: 480px;
  height: 480px;
  background: #3b82f6;
  top: -10%;
  left: -10%;
  animation: float 12s ease-in-out infinite;
}
.glow-2 {
  width: 400px;
  height: 400px;
  background: #6366f1;
  bottom: -10%;
  right: -10%;
  animation: float 14s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(60px, 40px); }
}

/* ============== 主内容 ============== */
.content {
  position: relative;
  z-index: 2;
  text-align: center;
  padding: 40px;
  max-width: 560px;
}

/* Logo 圆环 + 图标 */
.code-wrap {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-ring {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.8);
  font-size: 56px;
  animation: ringRotate 12s linear infinite;
}

@keyframes ringRotate {
  to { transform: rotate(360deg); }
}

.logo-ring::before,
.logo-ring::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1.5px solid transparent;
}
.logo-ring::before {
  border-top-color: rgba(255, 255, 255, 0.7);
  animation: ringRotate 8s linear infinite;
}
.logo-ring::after {
  border-bottom-color: rgba(255, 255, 255, 0.4);
  animation: ringRotate 10s linear infinite reverse;
  inset: 12px;
}

/* 404 大数字（带逐位动画） */
.code {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
}

.digit {
  font-size: 96px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(180deg, #ffffff 0%, rgba(255, 255, 255, 0.7) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
  animation: digitIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) backwards;
}

@keyframes digitIn {
  0% {
    opacity: 0;
    transform: translateY(40px) scale(0.6);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 文字 */
.title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px;
  letter-spacing: 2px;
}

.subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  margin: 0 0 24px;
  letter-spacing: 3px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0 0 40px;
  line-height: 1.7;
}

/* 按钮 */
.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 48px;
}

.actions :deep(.el-button) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 140px;
  height: 42px;
  border-radius: 6px;
  font-size: 14px;
}

.btn-primary {
  background: #ffffff;
  color: var(--theme-primary);
  border-color: #ffffff;
  font-weight: 500;
  transition: all 0.25s ease;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(255, 255, 255, 0.25);
  background: #ffffff;
  color: var(--theme-primary);
  border-color: #ffffff;
}

.btn-secondary {
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  border-color: rgba(255, 255, 255, 0.4);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.6);
  color: #ffffff;
}

/* 底部分割线 */
.divider {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  letter-spacing: 2px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
}

.divider span {
  width: 48px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
}

.divider em {
  font-style: normal;
}

/* 响应式（使用 mixin） */
@include breakpoint-down(xs) {
  .digit {
    font-size: 72px;
  }
  .title {
    font-size: 24px;
  }
  .actions :deep(.el-button) {
    min-width: 100%;
  }
}
</style>
