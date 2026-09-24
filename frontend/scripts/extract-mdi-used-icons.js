/**
 * 从 @iconify-json/mdi 的全量 icons.json 中，提取项目实际用到的 mdi 图标子集，
 * 生成 frontend/src/assets/icons/mdi-used.ts。
 *
 * 使用方式：
 *   node scripts/extract-mdi-used-icons.js
 *
 * 工作原理：
 *   1. 扫描 src/**\/*.vue 提取所有 mdi:xxx 引用
 *   2. 从 icons.json 中挑出对应图标的 body 数据
 *   3. 输出成 IconifyJSON 兼容格式的 .ts 文件
 *
 * 这样 Vite 构建时只会把这 ~60 个图标打包进去（~2 KB），
 * 而不是整个 mdi 图标集（7474 个图标，~3 MB）。
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// frontend/ 目录
const FRONTEND_DIR = path.resolve(__dirname, '..')
const SRC_DIR = path.join(FRONTEND_DIR, 'src')
const MDI_JSON = path.join(
  FRONTEND_DIR,
  'node_modules/@iconify-json/mdi/icons.json',
)
const OUTPUT_TS = path.join(SRC_DIR, 'assets/icons/mdi-used.ts')

// ---------- 1. 扫描 src 下所有源代码文件，提取 mdi:xxx 引用 ----------
const mdiRefPattern = /mdi:[a-z0-9-]+/g
// 扫描范围：所有源代码后缀。漏了 .ts 会丢路由/菜单配置里的图标，
// 运行时 iconify 会 fallback 到 CDN（api.iconify.design）报 ERR_CONNECTION_REFUSED。
const SOURCE_EXTS = new Set(['.vue', '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'])
const usedSet = new Set()

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === 'dist') continue
      walk(full)
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name).toLowerCase()
      if (SOURCE_EXTS.has(ext)) {
        const content = fs.readFileSync(full, 'utf-8')
        for (const match of content.matchAll(mdiRefPattern)) {
          usedSet.add(match[0])
        }
      }
    }
  }
}

walk(SRC_DIR)

const usedIcons = [...usedSet].sort()
console.log(`[mdi-extract] src 中扫描到 ${usedIcons.length} 个 mdi 图标引用`)

// ---------- 2. 读取全量 icons.json，挑出对应图标 ----------
const all = JSON.parse(fs.readFileSync(MDI_JSON, 'utf-8'))
const subsetIcons = {}
const missing = []

for (const fullName of usedIcons) {
  const simple = fullName.replace(/^mdi:/, '')
  const data = all.icons[simple]
  if (!data) {
    missing.push(fullName)
    continue
  }
  subsetIcons[simple] = {
    body: data.body,
    // left / top / width / height 通常用集合默认；个别有 rotation 的保留
    ...(data.left !== undefined ? { left: data.left } : {}),
    ...(data.top !== undefined ? { top: data.top } : {}),
    ...(data.width !== undefined ? { width: data.width } : {}),
    ...(data.height !== undefined ? { height: data.height } : {}),
    ...(data.rotate !== undefined ? { rotate: data.rotate } : {}),
  }
}

if (missing.length) {
  console.warn(
    `[mdi-extract] ⚠️ 以下 ${missing.length} 个图标在 mdi 集中不存在（可能拼写错误）：`,
  )
  for (const m of missing) console.warn(`    - ${m}`)
}

console.log(
  `[mdi-extract] 提取到 ${Object.keys(subsetIcons).length}/${usedIcons.length} 个图标数据`,
)

// ---------- 3. 生成 .ts 文件 ----------
fs.mkdirSync(path.dirname(OUTPUT_TS), { recursive: true })

const tsLines = [
  '// 此文件由 scripts/extract-mdi-used-icons.js 自动生成，请勿手动编辑。',
  '//',
  `// 项目实际用到的 ${Object.keys(subsetIcons).length} 个 mdi 图标（集合全量 ${all.icons ? Object.keys(all.icons).length : '?'} 个）。`,
  '// 仅打包这些图标，避免把整个 mdi 图标集（~3 MB）打进 bundle。',
  '',
  '/* eslint-disable */',
  '/* tslint:disable */',
  '',
  'export const mdiUsedIcons = ' +
    JSON.stringify(
      {
        prefix: 'mdi',
        icons: subsetIcons,
        width: all.width,
        height: all.height,
      },
      null,
      2,
    ) +
    '',
  '',
]

fs.writeFileSync(OUTPUT_TS, tsLines.join('\n'), 'utf-8')

const size = fs.statSync(OUTPUT_TS).size
console.log(
  `[mdi-extract] ✅ 已生成 ${path.relative(FRONTEND_DIR, OUTPUT_TS)} (${(size / 1024).toFixed(1)} KB)`,
)
