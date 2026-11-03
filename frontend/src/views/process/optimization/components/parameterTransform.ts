/**
 * parameter 翻译器：嵌套 settingProcessForm ↔ flat ProcessParameterFlat
 *
 * 背景（2026-10-15 调优接口改造）：
 * - 后端 HTTP 入参契约统一为 flat（ProcessParameterSchema，88 字段镜像 ORM）
 * - 前端 UI 仍是嵌套（settingProcessForm，5 段含 table_data 数组）
 * - 「嵌套 ↔ flat」的翻译由前端 API 层负责，不能让 HTTP 契约承载嵌套结构
 *
 * 两个方向：
 * - parameterToFlat(nested)        —— 提交调优前用（嵌套 → flat）
 * - parameterFromFlat(flat)        —— 解析调优响应后用（flat → 嵌套）
 *
 * 后端契约（D1 决策，2026-10-22）：
 *   initialize（``result.process``）与 optimize（``new_parameter``）**都返回 flat**，
 *   前端是唯一的形态翻译方。两个接口的响应字段名不同但形态一致，
 *   因此本模块是全站唯一的 flat ↔ nested 翻译实现。
 *
 * 字段映射（与后端 backend/process/schemas/parameter.py 的 ProcessParameterSchema 一一对应）：
 * - injection           → inj_stg, inj_spd_1..6, inj_pres_1..6, inj_pos_1..6,
 *                         inj_t, inj_dly_t, cool_t
 * - vp_switch           → vps_mode, vps_pos, vps_t, vps_pres, vps_spd
 * - holding             → hold_stg, hold_pres_1..5, hold_spd_1..5, hold_t_1..5
 * - metering            → met_stg, met_pres_1..4, met_rot_spd_1..4,
 *                         met_back_pres_1..4, met_pos_1..4,
 *                         pre_met_decomp_{mode,pres,spd,t,dist},
 *                         pst_met_decomp_{mode,pres,spd,t,dist},
 *                         met_lim_t, met_end_pos
 * - barrel_temperature  → brl_temp_stg, noz_temp, brl_temp_1..9
  *     （行业惯例：stage 1 = 喷嘴温度 = noz_temp；
  *      stage 2..10 = 料筒 1..9 段 = brl_temp_1..9；与后端 ORM 拆分一致）
 *
 * 设计原则：
 * - 字段名严格按后端 ORM 字段名（不引入新别名）
 * - 嵌套缺失的段 → 对应 flat 字段不输出（保持稀疏，由后端 Pydantic 校验
 *   "至少一个非 None 工艺字段" 拦住「忘翻译」异常）
 * - table_data[i].sections[k] 是数组位置 → flat 后缀号（inj_pres_<k+1>）
 * - 不做"自动推断缺哪段"——只翻译前端实际有值的字段
 *
 * 业务元数据（process_condition_id / param_code / param_source / parent_seq_idx /
 * seq_idx）由后端 service 层维护，前端翻译不涉及。
 */

// ⚠️ 必须是**值导入**而非 `import type`：parameterFromFlat 在运行时以
//    settingProcessForm 作为模板底（label / unit / max_stage 等 UI 元数据）。
//    `import type` 会被编译期擦除 ⇒ 运行时 ReferenceError。
import { settingProcessForm } from '@/constants/process-const'

/**
 * 调优入参的 flat 形态（与 ProcessParameterSchema 字段一一对应，全 Optional）
 *
 * 前端调用方使用：提交调优前 parameterToFlat(nested) → ProcessParameterFlat，
 * 再通过 processOptimizationInfer({ ..., parameter: flatPayload }) 发送。
 *
 * 字段全 Optional：与后端 Pydantic BaseSchema 一致；前端翻译出的字段若全是 None
 * 会触发后端 _parameter_must_have_override 校验拒绝，避免「忘翻译」静默提交。
 */
export interface ProcessParameterFlat {
  // --- 注射参数 ---
  inj_stg?: number | null
  inj_spd_1?: number | null
  inj_spd_2?: number | null
  inj_spd_3?: number | null
  inj_spd_4?: number | null
  inj_spd_5?: number | null
  inj_spd_6?: number | null
  inj_pres_1?: number | null
  inj_pres_2?: number | null
  inj_pres_3?: number | null
  inj_pres_4?: number | null
  inj_pres_5?: number | null
  inj_pres_6?: number | null
  inj_pos_1?: number | null
  inj_pos_2?: number | null
  inj_pos_3?: number | null
  inj_pos_4?: number | null
  inj_pos_5?: number | null
  inj_pos_6?: number | null
  inj_t?: number | null
  inj_dly_t?: number | null

  // --- VP 切换 ---
  vps_mode?: number | null
  vps_pos?: number | null
  vps_t?: number | null
  vps_pres?: number | null
  vps_spd?: number | null

  // --- 保压参数 ---
  hold_stg?: number | null
  hold_pres_1?: number | null
  hold_pres_2?: number | null
  hold_pres_3?: number | null
  hold_pres_4?: number | null
  hold_pres_5?: number | null
  hold_spd_1?: number | null
  hold_spd_2?: number | null
  hold_spd_3?: number | null
  hold_spd_4?: number | null
  hold_spd_5?: number | null
  hold_t_1?: number | null
  hold_t_2?: number | null
  hold_t_3?: number | null
  hold_t_4?: number | null
  hold_t_5?: number | null

  // --- 冷却参数 ---
  cool_t?: number | null

  // --- 熔胶参数 ---
  met_stg?: number | null
  met_pres_1?: number | null
  met_pres_2?: number | null
  met_pres_3?: number | null
  met_pres_4?: number | null
  met_rot_spd_1?: number | null
  met_rot_spd_2?: number | null
  met_rot_spd_3?: number | null
  met_rot_spd_4?: number | null
  met_back_pres_1?: number | null
  met_back_pres_2?: number | null
  met_back_pres_3?: number | null
  met_back_pres_4?: number | null
  met_pos_1?: number | null
  met_pos_2?: number | null
  met_pos_3?: number | null
  met_pos_4?: number | null

  // --- 松退参数 ---
  pre_met_decomp_mode?: number | null
  pre_met_decomp_pres?: number | null
  pre_met_decomp_spd?: number | null
  pre_met_decomp_t?: number | null
  pre_met_decomp_dist?: number | null
  pst_met_decomp_mode?: number | null
  pst_met_decomp_pres?: number | null
  pst_met_decomp_spd?: number | null
  pst_met_decomp_t?: number | null
  pst_met_decomp_dist?: number | null
  met_lim_t?: number | null
  met_end_pos?: number | null

  // --- 料筒温度 ---
  brl_temp_stg?: number | null
  noz_temp?: number | null
  brl_temp_1?: number | null
  brl_temp_2?: number | null
  brl_temp_3?: number | null
  brl_temp_4?: number | null
  brl_temp_5?: number | null
  brl_temp_6?: number | null
  brl_temp_7?: number | null
  brl_temp_8?: number | null
  brl_temp_9?: number | null
}

/** 嵌套 settingProcessForm 的类型别名（避免本文件依赖具体常量） */
type SettingProcessForm = typeof settingProcessForm

/** 注入类段 字段名常量（保留以备未来按前缀动态展开）*/
const PRES = ['inj_pres', 'hold_pres', 'met_pres']
const SPD = ['inj_spd', 'hold_spd', 'met_rot_spd']
const POS = ['inj_pos', 'met_pos']
const TIME = ['hold_t']
// barrel_temperature 例外（stage 1 = noz_temp，stage 2..10 = brl_temp_1..9），
// 不走 expandSections，由调用点手工拆分见下方

/**
 * 提取 table_data 行（label 匹配）的 sections 数组到 flat 字段后缀映射
 *
 * 设计要点：
 * - 按 `label` 而不是按位置匹配（前端 SettingProcess 的 table_data 行顺序可能
 *   因为 i18n / 业务调整而变化，按 label 是稳定契约）
 * - 段数 ≤ flat 后端 ORM 字段数时，超出段数被静默丢弃（与后端 extra="ignore" 同源）
 */
function pickRow(table_data: { label: string; sections: any[] }[] | undefined, label: string): any[] | undefined {
  if (!table_data) return undefined
  const row = table_data.find(r => r.label === label)
  return row?.sections
}

/** 把 sections[k] 展开成 flat field _value_v2（k 是 0-based；_k+1 是 1-based） */
function expandSections(prefix: string, sections: any[] | undefined, max: number, target: Record<string, any>): void {
  if (!sections) return
  for (let i = 0; i < Math.min(sections.length, max); i++) {
    const v = sections[i]
    if (v !== null && v !== undefined) {
      target[`${prefix}_${i + 1}`] = v
    }
  }
}

/**
 * 嵌套 settingProcessForm → flat ProcessParameterFlat
 *
 * 用法：
 *   const flat = parameterToFlat(activeRound.parameter)
 *   await processOptimizationInfer({
 *     condition_id: ..., parent_seq_idx: ..., parameter: flat, feedback: ...
 *   })
 *
 * 行为约定：
 * - 只翻译前端实际有值的字段（null / undefined 字段不进 flat dict）
 * - 段数超出后端 ORM 字段数的部分静默丢弃
 * - 不修改入参对象（返回新对象）
 *
 * 边界情况：
 * - null / undefined 入参 → 返回空对象 {}
 *   （调用方需要根据"用户是否真的改了参数"决定要不要把 parameter 字段设为 {} / null）
 * - 前端还没初始化（activeRound.parameter 是 settingProcessForm 默认值）→ 返回 {}
 *   此时调用方应把 parameter 字段设为 null（让后端从 ORM 反查 baseline）
 */
export function parameterToFlat(nested: SettingProcessForm | null | undefined): ProcessParameterFlat {
  if (!nested) return {}

  const flat: ProcessParameterFlat = {}

  // ---- 注射参数 ----
  if (nested.injection) {
    const inj = nested.injection
    if (inj.stage != null) flat.inj_stg = inj.stage
    if (inj.injection_time != null) flat.inj_t = inj.injection_time
    if (inj.delay_time != null) flat.inj_dly_t = inj.delay_time
    if (inj.cooling_time != null) flat.cool_t = inj.cooling_time
    expandSections('inj_pres', pickRow(inj.table_data, '压力'), 6, flat)
    expandSections('inj_spd', pickRow(inj.table_data, '速度'), 6, flat)
    expandSections('inj_pos', pickRow(inj.table_data, '位置'), 6, flat)
  }

  // ---- VP 切换 ----
  if (nested.vp_switch) {
    const vp = nested.vp_switch
    if (vp.mode != null) flat.vps_mode = vp.mode
    if (vp.position != null) flat.vps_pos = vp.position
    if (vp.time != null) flat.vps_t = vp.time
    if (vp.pressure != null) flat.vps_pres = vp.pressure
    if (vp.velocity != null) flat.vps_spd = vp.velocity
  }

  // ---- 保压参数 ----
  if (nested.holding) {
    const hold = nested.holding
    if (hold.stage != null) flat.hold_stg = hold.stage
    expandSections('hold_pres', pickRow(hold.table_data, '压力'), 5, flat)
    expandSections('hold_spd', pickRow(hold.table_data, '速度'), 5, flat)
    expandSections('hold_t', pickRow(hold.table_data, '时间'), 5, flat)
  }

  // ---- 熔胶参数 ----
  if (nested.metering) {
    const met = nested.metering
    if (met.stage != null) flat.met_stg = met.stage
    if (met.pre_decompress_mode != null) flat.pre_met_decomp_mode = met.pre_decompress_mode
    if (met.post_decompress_mode != null) flat.pst_met_decomp_mode = met.post_decompress_mode
    if (met.delay_time != null) flat.met_lim_t = met.delay_time
    if (met.ending_position != null) flat.met_end_pos = met.ending_position
    expandSections('met_pres', pickRow(met.table_data, '压力'), 4, flat)
    expandSections('met_rot_spd', pickRow(met.table_data, '螺杆转速'), 4, flat)
    expandSections('met_back_pres', pickRow(met.table_data, '背压'), 4, flat)
    expandSections('met_pos', pickRow(met.table_data, '位置'), 4, flat)

    // 松退（decompress_table_data 是固定两行：储前 / 储后）
    const dec = met.decompress_table_data
    if (dec && dec[0]) {
      const pre = dec[0]
      if (pre.pressure != null) flat.pre_met_decomp_pres = pre.pressure
      if (pre.velocity != null) flat.pre_met_decomp_spd = pre.velocity
      if (pre.time != null) flat.pre_met_decomp_t = pre.time
      if (pre.distance != null) flat.pre_met_decomp_dist = pre.distance
    }
    if (dec && dec[1]) {
      const pst = dec[1]
      if (pst.pressure != null) flat.pst_met_decomp_pres = pst.pressure
      if (pst.velocity != null) flat.pst_met_decomp_spd = pst.velocity
      if (pst.time != null) flat.pst_met_decomp_t = pst.time
      if (pst.distance != null) flat.pst_met_decomp_dist = pst.distance
    }
  }

  // ---- 料筒温度 ----
  // stage 1 = 喷嘴温度（noz_temp），stage 2..10 = 料筒 1..9 段（brl_temp_1..9）
  // 是注塑机 HMI 温度组表的行业惯例：喷嘴在入模端，其温度独立控制；
  // 料筒温度表中 stage 1 不含喷嘴，后端 ORM 同样拆分为 noz_temp + brl_temp_1..9
  if (nested.barrel_temperature) {
    const brl = nested.barrel_temperature
    if (brl.stage != null) flat.brl_temp_stg = brl.stage
    const sections = pickRow(brl.table_data, '温度')
    if (sections) {
      // sections[0] = 喷嘴温度（stage 1）
      if (sections[0] !== null && sections[0] !== undefined) {
        flat.noz_temp = sections[0]
      }
      // sections[1..9] = 料筒 1..9 段（stage 2..10）
      // 限长 9 是因为后端 ORM 实际只到 brl_temp_9；sections[10] 超出部分静默丢弃
      // 模板字符串键在 TS 严格模式下不能直接索引 ProcessParameterFlat
      // （后者是字面量联合），用 as any 路由一次（局部块，未被外部引用）
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const flatAny = flat as any
      for (let i = 1; i <= 9 && i < sections.length; i++) {
        const v = sections[i]
        if (v !== null && v !== undefined) {
          flatAny[`brl_temp_${i}`] = v
        }
      }
    }
  }

  return flat
}

/**
 * flat ProcessParameterFlat → 嵌套 settingProcessForm
 *
 * 用法：
 *   const nested = parameterFromFlat(inferData.new_parameter)
 *   newRound.parameter = nested
 *
 * 行为约定：
 * - 以 settingProcessForm 为模板底（保留 label / unit / max_stage 等 UI 元数据）
 * - 缺失字段 → null（**不补业务默认值**，避免伪造数据）
 * - barrel_temperature 段位：sections[0]=喷嘴（noz_temp）、sections[1..9]=料筒 1..9
 *   （brl_temp_1..9）—— 与 parameterToFlat 严格互逆
 *   ⚠️ 后端 nested 的 brl_temp_steps[0] 是「料筒 1 段」，两边语义不同，
 *      flat 用 noz_temp + brl_temp_1..9 两个独立字段消除了该歧义
 * - 只读白名单字段，多余字段（如 parameter_id / seq_idx / process_condition_id）忽略
 */
export function parameterFromFlat(flat: ProcessParameterFlat | null | undefined): SettingProcessForm {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const f: any = flat || {}
  const num = (v: any): number | null => (v === null || v === undefined ? null : v)

  /** 取 prefix_1..prefix_max 段位，缺位补 null */
  const sectionsOf = (prefix: string, max: number): Array<number | null> => {
    const out: Array<number | null> = []
    for (let i = 1; i <= max; i++) out.push(num(f[`${prefix}_${i}`]))
    return out
  }

  return {
    injection: {
      ...settingProcessForm.injection,
      stage: num(f.inj_stg) ?? settingProcessForm.injection.stage,
      table_data: [
        { label: '压力', unit: 'MPa', sections: sectionsOf('inj_pres', 6) },
        { label: '速度', unit: 'mm/s', sections: sectionsOf('inj_spd', 6) },
        { label: '位置', unit: 'mm', sections: sectionsOf('inj_pos', 6) },
      ],
      injection_time: num(f.inj_t),
      delay_time: num(f.inj_dly_t),
      cooling_time: num(f.cool_t),
    },
    vp_switch: {
      ...settingProcessForm.vp_switch,
      mode: num(f.vps_mode) ?? settingProcessForm.vp_switch.mode,
      position: num(f.vps_pos),
      time: num(f.vps_t),
      pressure: num(f.vps_pres),
      velocity: num(f.vps_spd),
    },
    holding: {
      ...settingProcessForm.holding,
      stage: num(f.hold_stg) ?? settingProcessForm.holding.stage,
      table_data: [
        { label: '压力', unit: 'MPa', sections: sectionsOf('hold_pres', 5) },
        { label: '速度', unit: 'mm/s', sections: sectionsOf('hold_spd', 5) },
        { label: '时间', unit: 's', sections: sectionsOf('hold_t', 5) },
      ],
    },
    metering: {
      ...settingProcessForm.metering,
      stage: num(f.met_stg) ?? settingProcessForm.metering.stage,
      table_data: [
        { label: '压力', unit: 'MPa', sections: sectionsOf('met_pres', 4) },
        { label: '螺杆转速', unit: 'rpm', sections: sectionsOf('met_rot_spd', 4) },
        { label: '背压', unit: 'MPa', sections: sectionsOf('met_back_pres', 4) },
        { label: '位置', unit: 'mm', sections: sectionsOf('met_pos', 4) },
      ],
      pre_decompress_mode: num(f.pre_met_decomp_mode) ?? settingProcessForm.metering.pre_decompress_mode,
      post_decompress_mode: num(f.pst_met_decomp_mode) ?? settingProcessForm.metering.post_decompress_mode,
      decompress_table_data: [
        {
          label: '储前',
          pressure: num(f.pre_met_decomp_pres),
          velocity: num(f.pre_met_decomp_spd),
          time: num(f.pre_met_decomp_t),
          distance: num(f.pre_met_decomp_dist),
        },
        {
          label: '储后',
          pressure: num(f.pst_met_decomp_pres),
          velocity: num(f.pst_met_decomp_spd),
          time: num(f.pst_met_decomp_t),
          distance: num(f.pst_met_decomp_dist),
        },
      ],
      delay_time: num(f.met_lim_t),
      ending_position: num(f.met_end_pos),
    },
    barrel_temperature: {
      ...settingProcessForm.barrel_temperature,
      stage: num(f.brl_temp_stg) ?? settingProcessForm.barrel_temperature.stage,
      table_data: [
        {
          label: '温度',
          unit: '℃',
          sections: [num(f.noz_temp), ...sectionsOf('brl_temp', 9)],
        },
      ],
    },
  }
}

/**
 * 工艺字段白名单（后端 ProcessParameterSchema 的 83 个工艺字段）
 *
 * 另有 5 个元数据字段（process_condition_id / param_code / param_source /
 * parent_seq_idx / seq_idx）不在此列——它们不参与工艺内容判定。
 */
const PROCESS_FLAT_FIELDS: string[] = [
  'inj_stg', 'inj_t', 'inj_dly_t', 'cool_t',
  ...['inj_spd', 'inj_pres', 'inj_pos'].flatMap(p => Array.from({ length: 6 }, (_, i) => `${p}_${i + 1}`)),
  'vps_mode', 'vps_pos', 'vps_t', 'vps_pres', 'vps_spd',
  'hold_stg',
  ...['hold_pres', 'hold_spd', 'hold_t'].flatMap(p => Array.from({ length: 5 }, (_, i) => `${p}_${i + 1}`)),
  'met_stg', 'met_lim_t', 'met_end_pos',
  ...['met_pres', 'met_rot_spd', 'met_back_pres', 'met_pos'].flatMap(p => Array.from({ length: 4 }, (_, i) => `${p}_${i + 1}`)),
  'pre_met_decomp_mode', 'pre_met_decomp_pres', 'pre_met_decomp_spd', 'pre_met_decomp_t', 'pre_met_decomp_dist',
  'pst_met_decomp_mode', 'pst_met_decomp_pres', 'pst_met_decomp_spd', 'pst_met_decomp_t', 'pst_met_decomp_dist',
  'brl_temp_stg', 'noz_temp',
  ...Array.from({ length: 9 }, (_, i) => `brl_temp_${i + 1}`),
]

/**
 * flat 里是否含实际工艺内容（排除 parameter_id / seq_idx 等元数据）
 *
 * 用途：响应有效性校验——结构完整但工艺内容全空时提前告警，
 * 避免「接口 200、参数表却静默空白」这类问题难以定位。
 */
export function hasFlatParameterContent(flat: ProcessParameterFlat | null | undefined): boolean {
  if (!flat) return false
  const f = flat as Record<string, unknown>
  return PROCESS_FLAT_FIELDS.some((k) => f[k] !== null && f[k] !== undefined)
}

/**
 * 判断 flat payload 是否为空（前端翻译后无任何非 None 字段）
 *
 * 调用方在 parameterToFlat 后应检查：
 * - isEmptyFlatParameter(flat) === true → 用户没改参数，HTTP 入参 parameter = null
 * - 否则 → HTTP 入参 parameter = flat（后端 Pydantic 会校验"至少一个工艺字段"）
 */
export function isEmptyFlatParameter(flat: ProcessParameterFlat): boolean {
  return Object.keys(flat).length === 0
}