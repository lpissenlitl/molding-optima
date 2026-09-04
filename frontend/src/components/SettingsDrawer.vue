<!--
  SettingsDrawer：系统设置侧拉抽屉
  - 主题切换：light / dark / high-contrast
  - 字号切换：default / large
  - 侧边栏默认折叠：开 / 关
  - 所有设置通过 settings store 管理，主题/字号在 main.ts 同步到 <html>
-->
<template>
  <el-drawer
    v-model="visible"
    title="系统设置"
    direction="rtl"
    size="420px"
    :with-header="true"
  >
    <div class="settings-layout">
      <!-- ============== 内容区（可滚动）============== -->
      <div class="settings">
        <!-- 主题 -->
        <section class="settings__section">
          <h4 class="settings__title">主题</h4>
          <p class="settings__hint">切换界面外观，适配不同作业环境</p>

          <el-radio-group
            :model-value="settingsStore.theme"
            @change="(v: Theme) => settingsStore.setTheme(v)"
            class="settings__theme-group"
          >
            <el-radio-button
              v-for="opt in THEME_OPTIONS"
              :key="opt.value"
              :value="opt.value"
              class="settings__theme-option"
            >
              <div class="theme-card">
                <AppIcon :icon="themeIcon(opt.value)" class="theme-card__icon" />
                <div class="theme-card__name">{{ opt.label }}</div>
                <div class="theme-card__hint">{{ opt.hint }}</div>
              </div>
            </el-radio-button>
          </el-radio-group>
        </section>

        <!-- 字号 -->
        <section class="settings__section">
          <h4 class="settings__title">字号</h4>
          <p class="settings__hint">车间远距离操作建议使用大字号</p>

          <el-radio-group
            :model-value="settingsStore.fontSize"
            @change="(v: FontSize) => settingsStore.setFontSize(v)"
          >
            <el-radio-button
              v-for="opt in FONT_SIZE_OPTIONS"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </el-radio-button>
          </el-radio-group>
        </section>

        <!-- 侧边栏 -->
        <section class="settings__section">
          <h4 class="settings__title">侧边栏</h4>
          <p class="settings__hint">默认是否折叠（仅桌面端生效）</p>

          <div class="settings__row">
            <span>默认折叠</span>
            <el-switch
              :model-value="settingsStore.sidebarDefaultCollapsed"
              @change="(v: boolean | string | number) => settingsStore.setSidebarDefaultCollapsed(Boolean(v))"
            />
          </div>
        </section>
      </div>

      <!-- ============== 底部操作（固定）============== -->
      <footer class="settings__footer">
        <el-button @click="handleReset">恢复默认</el-button>
        <el-button type="primary" @click="visible = false">完成</el-button>
      </footer>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  useSettingsStore,
  THEME_OPTIONS,
  FONT_SIZE_OPTIONS,
  type Theme,
  type FontSize,
} from '@/stores/settings'

const settingsStore = useSettingsStore()

const visible = defineModel<boolean>({ default: false })

function themeIcon(theme: Theme): string {
  const map: Record<Theme, string> = {
    light: 'mdi:white-balance-sunny',
    dark: 'mdi:weather-night',
    'high-contrast': 'mdi:contrast-box',
  }
  return map[theme]
}

function handleReset() {
  settingsStore.reset()
}
</script>

<style scoped lang="scss">
// 整体布局：内容区（可滚动） + 底部（固定）
.settings-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

// 内容区：超出时滚动（留白依赖 el-drawer 默认 padding: 20px）
.settings {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 24px;

  &__section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__title {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  &__hint {
    margin: 0 0 8px;
    font-size: 12px;
    color: var(--color-text-secondary);
  }

  &__theme-group {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    width: 100%;

    // 覆盖 el-radio-button 默认样式（让它能展示卡片）
    :deep(.el-radio-button__inner) {
      width: 100%;
      padding: 0;
      border: 1px solid var(--color-border-base);
      border-radius: 6px;
      background: transparent;
      box-shadow: none;
    }

    :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
      background: var(--color-bg-overlay);
      border-color: var(--theme-primary);
      box-shadow: 0 0 0 2px rgba(37, 67, 115, 0.15);
    }
  }

  &__theme-option {
    width: 100%;

    // 隐藏 el-radio-button 默认 label 包裹
    :deep(.el-radio-button__inner) {
      display: block;
    }
  }

  &__row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: var(--color-bg-overlay);
    border-radius: 6px;
    color: var(--color-text-regular);
    font-size: 14px;
  }

  // 底部操作：固定在底部，不随内容滚动
  &__footer {
    flex-shrink: 0;
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    background: var(--color-bg-base);  // 与内容区分隔
    border-top: 1px solid var(--color-border-light);
  }
}

.theme-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;

  &__icon {
    font-size: 22px;
    color: var(--theme-primary);
  }

  &__name {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  &__hint {
    font-size: 11px;
    color: var(--color-text-secondary);
    text-align: center;
    line-height: 1.3;
  }
}
</style>