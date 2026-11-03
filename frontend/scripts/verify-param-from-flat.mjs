/**
 * verify-param-from-flat.mjs
 *
 * 用**真实前端代码**验证「后端 flat → 前端 nested」翻译后表格非空。
 *
 * 背景（2026-10-28 修复）：
 *   optimize 响应的 new_parameter 是 flat，后端给了完整参数，
 *   但前端只取了 parameter_id / seq_idx，新轮次的 parameter 停留在
 *   makeRound 的空模板（settingProcessForm 全 null）⇒ 参数表静默空白。
 *   本脚本用 parameterTransform.parameterFromFlat（前端唯一翻译器）
 *   翻译真实后端数据，断言表格关键格子非空。
 *
 * 用法：
 *   node scripts/verify-param-from-flat.mjs [flat.json 路径]
 *   默认读 ../backend/tests/_flat_out.json
 *   （由 backend/tests/verify_fuzzy_algo_db.py 产出）
 *
 * ⚠️ 用 esbuild 在内存里把 TS 翻译器打成 ESM 后以 data URL 载入，
 *    **零临时文件**，跑完不留痕。
 */

import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { build } from 'esbuild'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')

const flatPath = process.argv[2] || resolve(root, '../backend/tests/_flat_out.json')

function fail(msg) {
  console.error(`FAIL  ${msg}`)
  process.exit(1)
}

// ---- 载入前端翻译器（真实代码）----
const bundled = await build({
  entryPoints: [resolve(root, 'src/views/process/optimization/components/parameterTransform.ts')],
  bundle: true,
  format: 'esm',
  write: false,
  platform: 'node',
  alias: { '@': resolve(root, 'src') },
})
const mod = await import(
  'data:text/javascript;base64,' +
    Buffer.from(bundled.outputFiles[0].text).toString('base64')
)
const { parameterFromFlat, hasFlatParameterContent } = mod

if (typeof parameterFromFlat !== 'function') fail('parameterFromFlat 未导出')

// ---- 载入后端产出的真实 flat ----
let flat
try {
  flat = JSON.parse(readFileSync(flatPath, 'utf-8'))
} catch (err) {
  fail(`读不到 ${flatPath}（先跑 backend/tests/verify_fuzzy_algo_db.py 产出）: ${err.message}`)
}

console.log(`flat 来源: ${flatPath}`)

// ---- 断言 1：flat 含工艺内容 ----
if (!hasFlatParameterContent(flat)) fail('flat 不含工艺内容（hasFlatParameterContent=false）')
console.log('OK  flat 含工艺内容')

// ---- 断言 2：翻译后的表格关键格子非空 ----
const nested = parameterFromFlat(flat)
const row = (seg, label) => nested[seg].table_data.find((r) => r.label === label)

const injSpeed = row('injection', '速度')
if (!injSpeed) fail('注射「速度」行缺失')
if (injSpeed.sections[0] === null || injSpeed.sections[0] === undefined) {
  fail('注射速度一段为空 ⇒ 前端参数表仍是空白')
}
console.log(`OK  注射速度: ${JSON.stringify(injSpeed.sections)}`)

const injPres = row('injection', '压力')
if (!injPres) fail('注射「压力」行缺失')
console.log(`OK  注射压力: ${JSON.stringify(injPres.sections)}`)

// ---- 断言 3：料筒温度段位不错位（sections[0]=喷嘴，sections[1..9]=料筒1..9）----
const temp = row('barrel_temperature', '温度')
if (!temp) fail('料筒温度行缺失')
if (temp.sections.length !== 10) fail(`料筒温度应有 10 段（喷嘴+料筒1..9），实为 ${temp.sections.length}`)
if (temp.sections[0] !== flat.noz_temp) {
  fail(`温度段位错位：sections[0]=${temp.sections[0]}，应为喷嘴 noz_temp=${flat.noz_temp}`)
}
if (temp.sections[1] !== flat.brl_temp_1) {
  fail(`温度段位错位：sections[1]=${temp.sections[1]}，应为料筒1 brl_temp_1=${flat.brl_temp_1}`)
}
console.log(`OK  料筒温度 10 段且喷嘴/料筒未错位: ${JSON.stringify(temp.sections)}`)

// ---- 断言 4：往返一致（flat → nested → flat 的工艺字段值不变）----
const { parameterToFlat } = mod
const roundTrip = parameterToFlat(nested)
const mismatched = []
for (const [k, v] of Object.entries(roundTrip)) {
  if (flat[k] !== undefined && flat[k] !== null && flat[k] !== v) {
    mismatched.push(`${k}: ${flat[k]} → ${v}`)
  }
}
if (mismatched.length) fail(`往返不一致: ${mismatched.join(', ')}`)
console.log(`OK  往返一致（${Object.keys(roundTrip).length} 个非 null 工艺字段）`)

console.log('\n=== verify-param-from-flat PASSED ===')
