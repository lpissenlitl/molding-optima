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
  display: flex;
  background: #f5f7fa;
  color: #1f2937;
  position: relative;
  overflow: hidden;
}

/* ============== 左侧品牌区（参考主题色 var(--theme-primary)） ============== */
.brand-side {
  flex: 1;
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
  flex: 0 0 460px;
  @include flex-center;
  background: #f5f7fa;
  padding: 40px;
}

.form-card {
  width: 100%;
  max-width: 360px;
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
@media (max-width: 900px) {
  .brand-side {
    display: none;
  }
  .form-side {
    flex: 1;
  }
}

@include breakpoint-down(xs) {
  .form-side {
    padding: 24px;
  }
}
</style>
