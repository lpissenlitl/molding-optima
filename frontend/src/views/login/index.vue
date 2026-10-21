<template>
  <div class="login-page">
    <!-- ============== 左侧：品牌展示 ============== -->
    <div class="brand-side">
      <!-- 装饰：网格背景 -->
      <div class="grid-bg"></div>

      <div class="brand-content">
        <!-- Logo -->
        <div class="logo-wrap">
          <div class="logo-ring ring-1"></div>
          <div class="logo-ring ring-2"></div>
          <div class="logo-core">
            <AppIcon icon="mdi:cube-outline" />
          </div>
        </div>

        <!-- 标题 -->
        <h1 class="brand-title">{{ appStore.name }}</h1>
        <div class="brand-divider"></div>
        <h2 class="brand-subtitle">智能工艺系统</h2>
      </div>

      <!-- 底部版本信息 -->
      <div class="brand-footer">{{ appStore.footerBrand }}</div>
    </div>

    <!-- ============== 右侧：登录表单 ============== -->
    <div class="form-side">
      <div class="form-card">
        <!-- 移动端品牌标识：单栏布局时替代左侧品牌区，避免页面过于单调 -->
        <div class="mobile-brand">
          <span class="mobile-brand__logo">
            <AppIcon icon="mdi:cube-outline" />
          </span>
          <span class="mobile-brand__text">
            <span class="mobile-brand__name">{{ appStore.name }}</span>
            <span class="mobile-brand__subtitle">智能工艺系统</span>
          </span>
        </div>

        <div class="form-header">
          <h3 class="form-title">欢迎登录</h3>
          <p class="form-subtitle">Welcome to {{ appStore.name }}</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          class="login-form"
          @submit.prevent="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="账号"
              :prefix-icon="renderIcon('mdi:account-outline')"
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              show-password
              :prefix-icon="renderIcon('mdi:lock-outline')"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="form.remember">记住我</el-checkbox>
            <el-link type="primary" :underline="false" class="forgot-link">
              忘记密码？
            </el-link>
          </div>

          <el-button
            type="primary"
            size="large"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>

        <div class="form-footer">
          <span>{{ appStore.copyrightText }}</span>
          <span class="status" :class="`status--${appStore.status}`">
            <span
              :class="['status-dot', `status-dot--${appStore.status}`]"
            ></span>
            {{ appStore.statusLabel }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import { type FormInstance } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

// 进入登录页时立即探测后端可用性，用于状态指示器展示
// 用户在未登录前就能看到"系统正常/停服"，避免启服务失败时盲目登录
onMounted(() => {
  appStore.checkHealth()
})

const form = reactive({
  username: '',
  password: '',
  remember: false,
})

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const renderIcon = (name: string) => h(Icon, { icon: name })

const handleLogin = async () => {
  if (!formRef.value) return
  // 表单校验
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await userStore.login({
      username: form.username,
      password: form.password,
      ua: navigator.userAgent,
    })
    // 登录成功：跳 redirect 参数或默认 /dashboard
    const redirect = route.query.redirect as string | undefined
    router.push(redirect || '/dashboard')
    // 注意：成功路径不重置 loading，让页面跳转避免闪烁
  } catch {
    // 错误提示已由 request 拦截器统一弹窗，仅重置 loading
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  min-height: 100vh;
  /* dvh 适配移动端浏览器地址栏占位，避免 100vh 超出可视区域 */
  min-height: 100dvh;
  width: 100%;
  max-width: 100%;
  display: flex;
  background: #f5f7fa;
  color: #1f2937;
  position: relative;
  /* 横向裁剪但不做滚动容器：clip 不会把 overflow-y 的 visible 降级为 auto，
     纵向仍由 body 整页滚动（不会出现内层滚动条），横向不产生滚动条 */
  overflow-x: clip;
}

/* ============== 左侧品牌区（参考主题色 var(--theme-primary)） ============== */
.brand-side {
  /* 1 1 0：可伸缩且不被内容最小宽度锁死，min-width: 0 允许收缩到内容下限以下 */
  flex: 1 1 0;
  min-width: 0;
  position: relative;
  @include flex-column-center;
  background: var(--theme-primary);
  color: #fff;
  overflow: hidden;
}

/* 网格背景 */
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
}

.brand-content {
  position: relative;
  z-index: 1;
  padding: 40px;
  max-width: 480px;
  text-align: center;
}

/* Logo 圆环 */
.logo-wrap {
  position: relative;
  width: 88px;
  height: 88px;
  margin: 0 auto 32px;
  @include flex-center;
}

.logo-ring {
  position: absolute;
  border: 1.5px solid;
  border-radius: 50%;
}
.ring-1 {
  width: 100%;
  height: 100%;
  border-color: rgba(255, 255, 255, 0.2);
  border-top-color: rgba(255, 255, 255, 0.7);
  animation: rotate 10s linear infinite;
}
.ring-2 {
  width: 72%;
  height: 72%;
  border-color: rgba(255, 255, 255, 0.15);
  border-bottom-color: rgba(255, 255, 255, 0.5);
  animation: rotate 8s linear infinite reverse;
}

@keyframes rotate {
  to { transform: rotate(360deg); }
}

.logo-core {
  width: 44px;
  height: 44px;
  @include flex-center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  font-size: 24px;
  color: var(--theme-primary);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.logo-core :deep(svg) {
  color: var(--theme-primary);
}

/* 标题 */
.brand-title {
  font-size: 42px;
  font-weight: 700;
  margin: 0 0 16px;
  letter-spacing: 1px;
}

.brand-divider {
  width: 48px;
  height: 2px;
  background: rgba(255, 255, 255, 0.6);
  margin: 0 auto 16px;
}

.brand-subtitle {
  font-size: 22px;
  font-weight: 500;
  margin: 0;
  letter-spacing: 4px;
  color: rgba(255, 255, 255, 0.95);
}

/* 底部版本 */
.brand-footer {
  position: absolute;
  bottom: 24px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 1px;
}

/* ============== 右侧表单区 ============== */
.form-side {
  /* 桌面端固定 460px 基础宽度；min-width: 0 允许在空间不足时被压缩 */
  flex: 0 0 460px;
  min-width: 0;
  @include flex-center;
  background: #f5f7fa;
  padding: 40px;
}

.form-card {
  width: 100%;
  /* 卡片最大宽度：移动端/平板下保持 360px 居中，不随容器拉宽 */
  max-width: 360px;
  min-width: 0;
}

/* 移动端品牌标识：仅单栏布局显示，替代被隐藏的左侧品牌区
   - 垂直堆叠居中：Logo → 产品名 → 副标题，视觉重心明确
   - 不与下方左对齐的表单标题争抢同一层级，单独作为顶部品牌头 */
.mobile-brand {
  display: none;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  margin-bottom: 32px;
}

.mobile-brand__logo {
  width: 60px;
  height: 60px;
  @include flex-center;
  border-radius: 16px;
  background: var(--theme-primary);
  color: #fff;
  font-size: 32px;
  box-shadow: var(--shadow-md);
}

.mobile-brand__logo :deep(svg) {
  color: #fff;
}

.mobile-brand__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  line-height: 1.25;
}

.mobile-brand__name {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
  letter-spacing: 0.5px;
}

.mobile-brand__subtitle {
  font-size: 13px;
  color: #6b7280;
  letter-spacing: 3px;
}

.form-header {
  margin-bottom: 32px;
}

.form-title {
  font-size: 26px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 6px;
}

.form-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
  letter-spacing: 0.5px;
}

/* 表单 */
.login-form {
  margin-bottom: 0;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 6px;
  padding: 2px 12px;
}

.login-form :deep(.el-input__inner) {
  height: 40px;
  font-size: 14px;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #9ca3af;
}

.login-form :deep(.el-input__prefix) {
  color: #9ca3af;
  font-size: 16px;
}

.form-options {
  @include flex-between;
  margin: -4px 0 20px;
}

.login-form :deep(.el-checkbox__label) {
  color: #6b7280;
  font-size: 13px;
}

.forgot-link {
  font-size: 13px;
}

.login-btn {
  width: 100%;
  height: 42px;
  font-size: 15px;
  letter-spacing: 4px;
  font-weight: 500;
}

.form-footer {
  @include flex-between;
  color: #9ca3af;
  font-size: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

/* 系统状态指示器：
   - 颜色随 status 变化（normal=绿/degraded=黄/down=红）
   - 气泡带呼吸动画，三种状态节奏不同：
     normal   2.0s 舒缓，传达稳定
     degraded 1.5s 偏快，传达轻微预警
     down     1.0s 急促，传达严重告警
*/
.status {
  display: inline-flex;
  align-items: center;
  gap: 6px;

  &--normal   { color: #10b981; }
  &--degraded { color: #f59e0b; }
  &--down     { color: #ef4444; }
}

@keyframes status-pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.45;
    transform: scale(1.4);
  }
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: status-pulse 2s ease-in-out infinite;

  &--normal   { background: #10b981; animation-duration: 2s;   }
  &--degraded { background: #f59e0b; animation-duration: 1.5s; }
  &--down     { background: #ef4444; animation-duration: 1s;   }
}

/* ============== 响应式 ============== */
/* 中小屏（<1024px）：单栏布局
   - 隐藏左侧品牌区，登录卡片水平居中（保持 360px 上限，不被拉宽）
   - margin: auto 实现垂直居中；内容高于视口时 auto 归零，
     保证顶部不被裁切、整页由 body 滚动（无内层滚动条）
   - 断点用 1024px（md），因为两栏布局的最小可用宽度约为
     品牌区 560px + 表单区 460px = 1020px
*/
@include breakpoint-down(md) {
  .login-page {
    flex-direction: column;
  }
  .brand-side {
    display: none;
  }
  .form-side {
    flex: 0 0 auto;
    width: 100%;
    max-width: 100%;
    margin: auto 0;
    padding: 24px;
  }
  .form-card {
    max-width: 360px;
  }
  .mobile-brand {
    display: flex;
  }
  /* 品牌区已展示系统名，隐藏重复的英文副标题 */
  .form-subtitle {
    display: none;
  }
}

/* 超小屏（<480px）：收紧留白，按钮字间距压缩避免文字换行 */
@include breakpoint-down(xs) {
  .form-side {
    padding: 16px;
  }
  .login-btn {
    letter-spacing: 2px;
  }
}
</style>
