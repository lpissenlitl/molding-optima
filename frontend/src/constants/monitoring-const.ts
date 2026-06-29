// 监控系统相关常量

// 设备状态枚举
export const DEVICE_STATUS = {
  RUNNING: "running",      // 运行中
  STANDBY: "standby",      // 待机/调机
  ALARM: "alarm",          // 故障报警
  OFFLINE: "offline"       // 离线
}

// 设备状态文本映射
export const DEVICE_STATUS_TEXT = {
  [DEVICE_STATUS.RUNNING]: "运行中",
  [DEVICE_STATUS.STANDBY]: "待机/调机",
  [DEVICE_STATUS.ALARM]: "故障报警",
  [DEVICE_STATUS.OFFLINE]: "离线"
}

// 设备状态图标映射
export const DEVICE_STATUS_ICON = {
  [DEVICE_STATUS.RUNNING]: "el-icon-success",
  [DEVICE_STATUS.STANDBY]: "el-icon-warning",
  [DEVICE_STATUS.ALARM]: "el-icon-error",
  [DEVICE_STATUS.OFFLINE]: "el-icon-circle-close"
}

// 告警状态枚举
export const ALARM_STATUS = {
  PENDING: "pending",      // 未处理
  RECOVERED: "recovered",  // 已恢复
  CONFIRMED: "confirmed"   // 已确认
}

// 告警状态文本映射
export const ALARM_STATUS_TEXT = {
  [ALARM_STATUS.PENDING]: "未处理",
  [ALARM_STATUS.RECOVERED]: "已恢复",
  [ALARM_STATUS.CONFIRMED]: "已确认"
}

// 告警类型枚举
export const ALARM_TYPES = {
  TEMPERATURE: "temperature",  // 温度异常
  PRESSURE: "pressure",        // 压力异常
  DOOR: "door",               // 门安全异常
  TIMER: "timer",             // 时间异常
  EQUIPMENT: "equipment"       // 设备异常
}

// 告警类型图标映射
export const ALARM_TYPE_ICONS = {
  [ALARM_TYPES.TEMPERATURE]: "el-icon-coin",
  [ALARM_TYPES.DOOR]: "el-icon-lock",
  [ALARM_TYPES.PRESSURE]: "el-icon-trophy",
  [ALARM_TYPES.TIMER]: "el-icon-time",
  [ALARM_TYPES.EQUIPMENT]: "el-icon-warning-outline"
}

// OEE等级定义
export const OEE_LEVELS = {
  HIGH: { min: 90, label: "优秀", color: "#67C23A" },    // 绿色
  MEDIUM: { min: 70, label: "良好", color: "#E6A23C" },  // 黄色
  LOW: { min: 0, label: "待改进", color: "#F56C6C" }     // 红色
}

// 工艺参数类型
export const PARAMETER_TYPES = {
  INJECTION: "injection",      // 注射参数
  VP_SWITCH: "vp_switch",      // VP切换参数
  HOLD_PRESSURE: "hold_pressure", // 保压参数
  METERING: "metering",        // 计量参数
  TEMPERATURE: "temperature",  // 温度参数
  RETROFIT: "retrofit"         // 松退参数
}

// 工艺参数单位
export const PARAMETER_UNITS = {
  PRESSURE: "MPa",             // 压力单位
  SPEED: "mm/s",               // 速度单位
  POSITION: "mm",              // 位置单位
  TIME: "s",                   // 时间单位
  TEMPERATURE: "°C",           // 温度单位
  RPM: "rpm",                  // 转速单位
  PERCENT: "%"                 // 百分比单位
}

// 工艺参数默认值
export const DEFAULT_PARAM_VALUES = {
  [PARAMETER_TYPES.INJECTION]: {
    pressure: [120, 100, 80, 60, 50, 40],  // 注射压力(MPa)
    speed: [85, 65, 45, 35, 30, 25],       // 注射速度(mm/s)
    position: [120, 80, 40, 30, 20, 10]    // 注射位置(mm)
  },
  [PARAMETER_TYPES.HOLD_PRESSURE]: {
    pressure: [30, 25, 20, 15, 10],         // 保压压力(MPa)
    speed: [20, 15, 12, 8, 5],             // 保压速度(mm/s)
    time: [3.5, 2.0, 1.5, 1.0, 0.8]       // 保压时间(s)
  },
  [PARAMETER_TYPES.METERING]: {
    pressure: [80, 60, 50, 40],             // 计量压力(MPa)
    screwSpeed: [120, 80, 70, 60],          // 螺杆转速(rpm)
    backPressure: [8, 6, 5, 4],             // 背压(MPa)
    position: [180, 120, 100, 80]           // 位置(mm)
  },
  [PARAMETER_TYPES.TEMPERATURE]: {
    temperature: [220, 215, 210, 205, 200, 195, 190, 185, 180] // 温度(°C)
  }
}

// VP切换方式
export const VP_SWITCH_METHODS = {
  POSITION: "position",        // 位置
  TIME: "time",               // 时间
  BOTH: "both",               // 时间&位置
  PRESSURE: "pressure",       // 压力
  SPEED: "speed"              // 速度
}

// VP切换方式文本
export const VP_SWITCH_METHOD_TEXTS = {
  [VP_SWITCH_METHODS.POSITION]: "位置",
  [VP_SWITCH_METHODS.TIME]: "时间",
  [VP_SWITCH_METHODS.BOTH]: "时间&位置",
  [VP_SWITCH_METHODS.PRESSURE]: "压力",
  [VP_SWITCH_METHODS.SPEED]: "速度"
}

// 松退模式
export const RETROFIT_MODES = {
  NONE: 0,                    // 无
  DISTANCE: 1,                // 距离
  TIME: 2                     // 时间
}

// 松退模式文本
export const RETROFIT_MODE_TEXTS = {
  [RETROFIT_MODES.NONE]: "否",
  [RETROFIT_MODES.DISTANCE]: "距离",
  [RETROFIT_MODES.TIME]: "时间"
}

// 设定工艺参数模板
export const SETTING_PROCESS_TEMPLATE = {
  injection: {
    stage: 3,
    max_stage: 6,
    table_data: [
      { label: "压力", unit: "MPa", sections: [null, null, null, null, null, null] },
      { label: "速度", unit: "mm/s", sections: [null, null, null, null, null, null] },
      { label: "位置", unit: "mm", sections: [null, null, null, null, null, null] }
    ],
    injection_time: null,
    delay_time: null,
    cooling_time: null
  },
  vp_switch: {
    mode: 0, // 0:位置, 1:时间, 2:时间&位置, 3:压力, 4:速度
    position: null,
    time: null,
    pressure: null,
    velocity: null
  },
  holding: {
    stage: 3,
    max_stage: 5,
    table_data: [
      { label: "压力", unit: "MPa", sections: [null, null, null, null, null] },
      { label: "速度", unit: "mm/s", sections: [null, null, null, null, null] },
      { label: "时间", unit: "s", sections: [null, null, null, null, null] }
    ]
  },
  metering: {
    stage: 1,
    max_stage: 4,
    table_data: [
      { label: "压力", unit: "MPa", sections: [null, null, null, null, null] },
      { label: "螺杆转速", unit: "rpm", sections: [null, null, null, null, null] },
      { label: "背压", unit: "MPa", sections: [null, null, null, null, null] },
      { label: "位置", unit: "mm", sections: [null, null, null, null, null] }
    ],
    pre_decompress_mode: 0, // 0:否, 1:距离, 2:时间
    post_decompress_mode: 1, // 0:否, 1:距离, 2:时间
    decompress_table_data: [
      { label: "储前", pressure: null, velocity: null, distance: null, time: null },
      { label: "储后", pressure: null, velocity: null, distance: null, time: null }
    ],
    delay_time: null,
    ending_position: null
  },
  barrel_temperature: {
    stage: 5,
    max_stage: 10,
    table_data: [
      { label: "温度", unit: "℃", sections: [null, null, null, null, null, null, null, null, null, null] }
    ]
  }
}

// 设定工艺参数（MOCK 数据）
export const MOCK_SETTING_PROCESS = {
  injection: {
    stage: 3,
    max_stage: 6,
    table_data: [
      { label: "压力", unit: "MPa", sections: [120, 100, 80, null, null, null] },
      { label: "速度", unit: "mm/s", sections: [85, 65, 45, null, null, null] },
      { label: "位置", unit: "mm", sections: [120, 80, 40, null, null, null] }
    ],
    injection_time: 3.2,
    delay_time: 0.5,
    cooling_time: 28.5
  },
  vp_switch: {
    mode: 0, // 0:位置, 1:时间, 2:时间&位置, 3:压力, 4:速度
    position: 35,
    time: 0,
    pressure: 0,
    velocity: 0
  },
  holding: {
    stage: 3,
    max_stage: 5,
    table_data: [
      { label: "压力", unit: "MPa", sections: [30, 25, 20, null, null] },
      { label: "速度", unit: "mm/s", sections: [20, 15, 12, null, null] },
      { label: "时间", unit: "s", sections: [3.5, 2.0, 1.5, null, null] }
    ]
  },
  metering: {
    stage: 2,
    max_stage: 4,
    table_data: [
      { label: "压力", unit: "MPa", sections: [80, 60, null, null] },
      { label: "螺杆转速", unit: "rpm", sections: [120, 80, null, null] },
      { label: "背压", unit: "MPa", sections: [8, 6, null, null] },
      { label: "位置", unit: "mm", sections: [180, 120, null, null] }
    ],
    pre_decompress_mode: 0, // 0:否, 1:距离, 2:时间
    post_decompress_mode: 0,
    decompress_table_data: [
      { label: "储前", pressure: 5, velocity: 40, distance: 15, time: 2.0 },
      { label: "储后", pressure: 5, velocity: 30, distance: 10, time: 1.5 }
    ],
    delay_time: 0.5,
    ending_position: 178.5
  },
  barrel_temperature: {
    stage: 5,
    max_stage: 9,
    table_data: [
      { label: "温度", unit: "℃", sections: [220, 215, 210, 205, 200, null, null, null, null] }
    ]
  }
}