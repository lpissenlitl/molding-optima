/// <reference types="vite/client" />

/**
 * 由 vite.config.ts 的 define 注入。
 * 值为 package.json 的 version（构建时静态替换为 JSON 字符串字面量）。
 * 用于 localStorage key 拼接、版本展示等场景，保证与 package.json 始终同步。
 */
declare const __APP_VERSION__: string