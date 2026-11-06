/** parameter 翻译器：嵌套 settingProcessForm ↔ flat ProcessParameterFlat（前端是唯一的形态翻译方） */

// ⚠️ 必须是**值导入**而非 `import type`：parameterFromFlat 在运行时以
//    settingProcessForm 作为模板底（label / unit / max_stage 等 UI 元数据）。
//    `import type` 会被编译期擦除 ⇒ 运行时 ReferenceError。
import { settingProcessForm } from '@/constants/process-const'

/** 调优入参的 flat 形态（与后端 ProcessParameterSchema 字段一一对应，全 Optional） */
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

/** 注入类段 字段名常量 */
const PRES = ['inj_pres', 'hold_pres', 'met_pres']
const SPD = ['inj_spd', 'hold_spd', 'met_rot_spd']
const POS = ['inj_pos', 'met_pos']
const TIME = ['hold_t']
// barrel_temperature 例外（stage 1 = noz_temp，stage 2..10 = brl_temp_1..9），
// 不走 expandSections，由调用点手工拆分见下方

/** 按 label（而非位置）匹配 table_data 行取 sections 展开为 flat 后缀字段；超出 ORM 字段数的段静默丢弃 */
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

/** 嵌套 settingProcessForm → flat：只翻译有值的字段，超出 ORM 字段数的段丢弃，不改入参；入参为 null/undefined 或未初始化时返回 {} */
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
  // 后端 ORM 同样拆分为 noz_temp + brl_temp_1..9，stage（档位序号）原样存进 brl_temp_stg
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

/** flat → 嵌套 settingProcessForm：以 settingProcessForm 为模板底，缺失字段填 null 不补默认值
 *  barrel_temperature sections[0]=喷嘴、[1..9]=料筒，与 parameterToFlat 互逆 */
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

/** 工艺字段白名单（后端 ProcessParameterSchema 的 83 个工艺字段，不含 5 个元数据字段） */
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

/** flat 是否含实际工艺内容（排除 parameter_id / seq_idx 等元数据） */
export function hasFlatParameterContent(flat: ProcessParameterFlat | null | undefined): boolean {
  if (!flat) return false
  const f = flat as Record<string, unknown>
  return PROCESS_FLAT_FIELDS.some((k) => f[k] !== null && f[k] !== undefined)
}

/** flat payload 是否为空（翻译后无任何非 None 字段 → 调用方应把 HTTP 入参 parameter 置 null） */
export function isEmptyFlatParameter(flat: ProcessParameterFlat): boolean {
  return Object.keys(flat).length === 0
}