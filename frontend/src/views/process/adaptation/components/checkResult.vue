<template>
  <div>
    <el-table
      v-for="(config, index) in tableConfig"
      :key="index"
      :data="config.data"
      style="width: 100%"
      :cell-style="tableCellStyle"
      :header-cell-style="{
        'background-color': 'lightblue',
        'color': '#000',
        'font-size': 'var(--basic-font-size)',
        'padding': '10px 0px'
      }"
    >
      <el-table-column
        v-for="column in getVisibleColumns(columnsSetting, config.columns)"
        :key="column.prop"
        :prop="column.prop"
        :label="column.label"
        :min-width="column.width"
        :align="column.align"
        :header-align="column.header_align"
        :sortable="column.sortable"
        :show-overflow-tooltip="column.tooltip"
      >
        <template #default="scope">
          <el-link
            v-if="column.prop === 'jump' && scope.row.suggest !== '✔'"
            type="primary"
            @click="updateInfo(config.datasource)"
          >
            去填写
          </el-link>
          <div v-else>
            {{ scope.row[column.prop] }}
          </div>
        </template>
      </el-table-column>
    </el-table>
    <div style="height: 20px"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

// 单/多色注塑机类型（影射到数字）
const MachineTypeOptions: Record<string, number> = {
  "单色注塑机": 1,
  "双色注塑机": 2,
  "三色注塑机": 3,
  "四色注塑机": 4,
  "五色注塑机": 5,
  "六色注塑机": 6,
  "七色注塑机": 7,
}

// 单/多色模具类型
const MoldTypeOptions: Record<string, number> = {
  "单色模具": 1,
  "双色模具": 2,
  "三色模具": 3,
  "四色模具": 4,
  "五色模具": 5,
  "六色模具": 6,
  "七色模具": 7,
}

// 模具 ↔ 注塑机适配规则
const adaptionProperties = [
  { property: "mold_type", name: "射台数量", injection: "machine_type", injt_name: "射台数量", percentage: [1], unit: "Ton" },
  { property: "min_clamping_force", name: "最小锁模力", injection: "max_clamping_force", injt_name: "最大锁模力", percentage: [0.85, 1], unit: "Ton" },
  { property: "size_horizon", name: "模具尺寸（横）", injection: "min_mold_size_horizon", injt_name: "最小容模尺寸（横）", percentage: [0], unit: "mm" },
  { property: "size_horizon", name: "模具尺寸（横）", injection: "max_mold_size_horizon", injt_name: "最大容模尺寸（横）", percentage: [1], unit: "mm" },
  { property: "mold_width", name: "模具尺寸（竖）", injection: "min_mold_width", injt_name: "最小容模尺寸（竖）", percentage: [0], unit: "mm" },
  { property: "mold_width", name: "模具尺寸（竖）", injection: "max_mold_width", injt_name: "最大容模尺寸（竖）", percentage: [1], unit: "mm" },
  { property: "size_thickness", name: "模具厚度", injection: "min_mold_thickness", injt_name: "最小容模厚度", percentage: [0], unit: "mm" },
  { property: "size_thickness", name: "模具厚度", injection: "max_mold_thickness", injt_name: "最大容模厚度", percentage: [1], unit: "mm" },
  { property: "ejector_force", name: "顶出力", injection: "max_ejection_force", injt_name: "最大顶出力", percentage: [1], unit: "kN" },
  { property: "ejector_stroke", name: "顶出行程", injection: "max_ejection_stroke", injt_name: "最大顶出行程", percentage: [1], unit: "mm" },
]

const moldProperties = [
  { property: "mold_type", name: "模具类别", unit: "", suggest: "必填" },
  { property: "product_total_weight", name: "总注射重量", unit: "g", suggest: "必填" },
  { property: "size_horizon", name: "模具尺寸（横）", unit: "mm", suggest: "必填" },
  { property: "mold_width", name: "模具尺寸（竖）", unit: "mm", suggest: "必填" },
  { property: "size_thickness", name: "模具厚度", unit: "mm", suggest: "必填" },
  { property: "min_clamping_force", name: "最小锁模力", unit: "Ton", suggest: "必填" },
  { property: "mold_opening_stroke", name: "开模行程", unit: "mm", suggest: "必填" },
  { property: "ejector_force", name: "顶出力", unit: "kN", suggest: "必填" },
  { property: "ejector_stroke", name: "顶出行程", unit: "mm", suggest: "必填" },
]

const machineProperties = [
  { property: "min_mold_size_horizon", name: "最小容模尺寸（横）", unit: "mm", suggest: "必填" },
  { property: "max_mold_size_horizon", name: "最大容模尺寸（横）", unit: "mm", suggest: "必填" },
  { property: "min_mold_width", name: "最小容模尺寸（竖）", unit: "mm", suggest: "必填" },
  { property: "max_mold_width", name: "最大容模尺寸（竖）", unit: "mm", suggest: "必填" },
  { property: "min_mold_thickness", name: "最小容模厚度", unit: "mm", suggest: "必填" },
  { property: "max_mold_thickness", name: "最大容模厚度", unit: "mm", suggest: "必填" },
  { property: "locate_hole_diameter", name: "定位孔直径", unit: "mm", suggest: "必填" },
  { property: "max_clamping_force", name: "最大锁模力", unit: "Ton", suggest: "必填" },
  { property: "max_mold_open_stroke", name: "最大开模行程", unit: "mm", suggest: "必填" },
  { property: "max_ejection_force", name: "最大顶出力", unit: "kN", suggest: "必填" },
  { property: "max_ejection_stroke", name: "最大顶出行程", unit: "mm", suggest: "必填" },
  { property: "drive_system", name: "驱动方式", suggest: "必填" },
]

const injectionProperties = [
  { property: "screw_diameter", name: "螺杆直径", unit: "mm", suggest: "必填" },
  { property: "max_injection_stroke", name: "最大注射行程", unit: "mm", suggest: "必填" },
  { property: "max_injection_weight", name: "最大注射重量", unit: "g", suggest: "必填" },
  { property: "nozzle_hole_diameter", name: "喷嘴孔直径", unit: "mm", suggest: "必填" },
  { property: "nozzle_sphere_radius", name: "喷嘴球半径", unit: "mm", suggest: "必填" },
  { property: "max_injection_pressure", name: "最大注射压力", unit: "MPa", suggest: "必填" },
  { property: "max_injection_velocity", name: "最大注射速度", unit: "mm/s", suggest: "必填" },
  { property: "max_holding_pressure", name: "最大保压压力", unit: "MPa", suggest: "必填" },
  { property: "max_holding_velocity", name: "最大保压速度", unit: "mm/s", suggest: "必填" },
  { property: "max_metering_pressure", name: "最大计量压力", unit: "MPa", suggest: "必填" },
  { property: "max_screw_rotation_speed", name: "最大螺杆转速", unit: "rpm", suggest: "必填" },
  { property: "max_metering_back_pressure", name: "最大计量背压", unit: "MPa", suggest: "必填" },
  { property: "max_decompression_pressure", name: "最大松退压力", unit: "MPa", suggest: "必填" },
  { property: "max_decompression_velocity", name: "最大松退速度", unit: "mm/s", suggest: "必填" },
  { property: "max_set_injection_pressure", name: "最大可设定注射压力", unit: "pressure_unit", suggest: "必填" },
  { property: "max_set_injection_velocity", name: "最大可设定注射速度", unit: "velocity_unit", suggest: "必填" },
  { property: "max_set_holding_pressure", name: "最大可设定保压压力", unit: "pressure_unit", suggest: "必填" },
  { property: "max_set_holding_velocity", name: "最大可设定保压速度", unit: "velocity_unit", suggest: "必填" },
  { property: "max_set_metering_pressure", name: "最大可设定计量压力", unit: "pressure_unit", suggest: "必填" },
  { property: "max_set_screw_rotation_speed", name: "最大可设定螺杆转速", unit: "screw_rotation_unit", suggest: "必填" },
  { property: "max_set_metering_back_pressure", name: "最大可设定计量背压", unit: "back_pressure_unit", suggest: "必填" },
  { property: "max_set_decompression_pressure", name: "最大可设定松退压力", unit: "pressure_unit", suggest: "必填" },
  { property: "max_set_decompression_velocity", name: "最大可设定松退速度", unit: "velocity_unit", suggest: "必填" },
]

const props = withDefaults(
  defineProps<{
    originProcess?: Record<string, any>
    transplantProcess?: Record<string, any>
  }>(),
  {
    originProcess: () => ({}),
    transplantProcess: () => ({}),
  }
)

const router = useRouter()

// 列设置
const columnsSetting = [
  { visible: true, label: "模具属性", prop: "mold", width: 180, align: "left", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "原始机台属性", prop: "origin_machine", width: 180, align: "left", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "转换机台属性", prop: "transplant_machine", width: 180, align: "left", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "射台属性", prop: "injection", width: 180, align: "left", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "注塑机适配", prop: "adaption", width: 180, align: "left", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "值", prop: "parameter", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "单位", prop: "unit", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "描述", prop: "description", width: 300, align: "center", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "建议", prop: "suggest", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
  { visible: true, label: "", prop: "jump", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
]

// 表格配置（clickHandler 在下方定义后赋值）
const tableConfig = ref<Array<{ type: string; datasource: string; columns: string[]; data: any[]; clickHandler: any }>>([
  {
    type: "moldTableData",
    datasource: "mold",
    columns: ["mold", "parameter", "unit", "suggest", "jump"],
    data: [],
    clickHandler: () => {},
  },
  {
    type: "originTableData",
    datasource: "origin_machine",
    columns: ["origin_machine", "parameter", "unit", "suggest", "jump"],
    data: [],
    clickHandler: () => {},
  },
  {
    type: "originInjectorData",
    datasource: "origin_machine",
    columns: ["injection", "parameter", "unit", "suggest", "jump"],
    data: [],
    clickHandler: () => {},
  },
  {
    type: "transplantTableData",
    datasource: "transplant_machine",
    columns: ["transplant_machine", "parameter", "unit", "suggest", "jump"],
    data: [],
    clickHandler: () => {},
  },
  {
    type: "transplantInjectorData",
    datasource: "transplant_machine",
    columns: ["injection", "parameter", "unit", "suggest", "jump"],
    data: [],
    clickHandler: () => {},
  },
  {
    type: "adaptionTableData",
    datasource: "adaption",
    columns: ["adaption", "description", "suggest"],
    data: [],
    clickHandler: "",
  },
])

function getVisibleColumns(columnsSetting: any[], requiredProps: string[]) {
  return columnsSetting.filter(column => requiredProps.includes(column.prop))
}

function checkProcess(originProcess: any, transplantProcess: any) {
  const unitArray = [
    "pressure_unit",
    "velocity_unit",
    "screw_rotation_unit",
    "back_pressure_unit",
  ]

  const checkProperties = (type: string, info: any, properties: any[], prefix = "") => {
    let data: any[] = []
    properties.forEach(e => {
      let prop = e.property
      let value: any = null
      let unit: any = e.unit
      let suggest: any = e.suggest
      if (info[prop] === undefined || info[prop] === null) {
        value = "缺失"
      } else if (info[prop] === 0) {
        value = info[prop]
      } else {
        value = info[prop]
        suggest = "✔"
      }

      if (unitArray.includes(unit)) {
        unit = info[unit]
      }

      data.push({
        [type]: prefix + e.name,
        parameter: value,
        unit: unit,
        suggest: suggest,
      })
    })
    return data
  }

  const checkAdaption = (type: string, injt: any, mold: any) => {
    let data: any[] = []
    if (injt && mold) {
      adaptionProperties.forEach(e => {
        let prop = e.property
        let desc: any = null
        let label = e.name
        let injt_prop = e.injection
        let suggest: any = null
        let unit = e.unit

        // 解决模具字段描述重复的问题
        let mold_prefix = ""
        if (!label.includes("模具")) {
          mold_prefix = "模具"
        }

        if (mold[prop] && injt[injt_prop]) {
          if (prop == "mold_type") {
            if (MoldTypeOptions[mold.mold_type] > MachineTypeOptions[injt.machine_type]) {
              desc = `模具类型为${mold.mold_type}，注塑机类型为${injt.machine_type}，注塑机射台数量不足！`
              suggest = "不适用"
            } else {
              desc = `模具类型为${mold.mold_type}，注塑机类型为${injt.machine_type}，注塑机满足生产要求。`
              suggest = "适用"
            }
          } else {
            if (e.percentage.length == 3) {
              if (Number(mold[prop]) < Number(injt[injt_prop]) * Number(e.percentage[0])) {
                desc = `${mold_prefix}${e.name}为${mold[prop]}，小于注塑机${e.injt_name}的${e.percentage[0] * 100}%，使用时需注意！`
                suggest = "注意"
              } else if (Number(mold[prop]) < Number(injt[injt_prop]) * Number(e.percentage[1])) {
                desc = `${mold_prefix}${e.name}为${mold[prop]}，大于注塑机${e.injt_name}的${e.percentage[0] * 100}%，小于注塑机${e.injt_name}的${e.percentage[1] * 100}%，适合生产。`
                suggest = "适用"
              } else if (Number(mold[prop]) < Number(injt[injt_prop]) * Number(e.percentage[2])) {
                desc = `${mold_prefix}${e.name}为${mold[prop]}，大于注塑机${e.injt_name}的${e.percentage[1] * 100}%，小于注塑机${e.injt_name}的${e.percentage[2] * 100}%，使用时需注意！`
                suggest = "注意"
              } else {
                desc = `${mold_prefix}${e.name}为${mold[prop]}，大于注塑机${e.injt_name}的${e.percentage[0] * 100}%，不适合生产！`
                suggest = "不适用"
              }
            } else if (e.percentage.length == 2) {
              if (Number(mold[prop]) < Number(injt[injt_prop]) * Number(e.percentage[0])) {
                desc = `${mold_prefix}${e.name}为${mold[prop]}${unit}，小于注塑机${e.injt_name}的${e.percentage[0] * 100}%，使用时需注意！`
                suggest = "注意"
              } else if (Number(mold[prop]) < Number(injt[injt_prop]) * Number(e.percentage[1])) {
                desc = `${mold_prefix}${e.name}为${mold[prop]}${unit}，大于注塑机${e.injt_name}的${e.percentage[0] * 100}%，小于注塑机${e.injt_name}的${e.percentage[1] * 100}%，适合生产。`
                suggest = "适用"
              } else {
                desc = `${mold_prefix}${e.name}为${mold[prop]}${unit}，大于注塑机${e.injt_name}的${e.percentage[0] * 100}%，不适合生产！`
                suggest = "不适用"
              }
            } else if (e.percentage.length == 1) {
              if (e.percentage[0] == 0) {
                if (Number(mold[prop]) < Number(injt[injt_prop])) {
                  desc = `${mold_prefix}${e.name}为${mold[prop]}${unit}，小于注塑机${e.injt_name} ${injt[injt_prop]}${unit}，不适合生产！`
                  suggest = "不适用"
                } else {
                  desc = `${mold_prefix}${e.name}为${mold[prop]}${unit}，适配注塑机${e.injt_name} ${injt[injt_prop]}${unit}，适合生产。`
                  suggest = "适用"
                }
              } else {
                if (Number(mold[prop]) > Number(injt[injt_prop])) {
                  desc = `${mold_prefix}${e.name}为${mold[prop]}${unit}，大于注塑机${e.injt_name} ${injt[injt_prop]}${unit}，不适合生产！`
                  suggest = "不适用"
                } else {
                  desc = `${mold_prefix}${e.name}为${mold[prop]}${unit}，适配注塑机${e.injt_name} ${injt[injt_prop]}${unit}，适合生产。`
                  suggest = "适用"
                }
              }
            }
          }
        } else {
          desc = ""
          if (!mold[prop]) {
            desc += `${mold_prefix}${e.name}数据不存在，`
          }
          if (!injt[injt_prop]) {
            desc += `注塑机${e.injt_name}数据不存在，`
          }
          desc += "数据不完整，无法进行比对！"
          suggest = "不适用"
        }

        data.push({
          [type]: label,
          description: desc,
          suggest: suggest,
        })
      })
    }
    return data
  }

  for (let i = 0; i < tableConfig.value.length; ++i) {
    const config = tableConfig.value[i]
    if (config.type == "moldTableData") {
      config.data = checkProperties("mold", originProcess.basic_mold_info, moldProperties)
    } else if (config.type == "originTableData") {
      config.data = checkProperties("origin_machine", originProcess.basic_machine_info, machineProperties)
    } else if (config.type == "originInjectorData") {
      config.data.length = 0
      for (let i = 0; i < originProcess.injection_station_details.length; i++) {
        const injectionDetail = originProcess.injection_station_details[i].injection_detail
        const validatedData = checkProperties("injection", injectionDetail, injectionProperties, `射台#${i + 1}：`)
        config.data = [...config.data, ...validatedData]
      }
    } else if (config.type == "transplantTableData") {
      config.data = checkProperties("transplant_machine", transplantProcess.basic_machine_info, machineProperties)
    } else if (config.type == "transplantInjectorData") {
      config.data.length = 0
      for (let i = 0; i < transplantProcess.injection_station_details.length; i++) {
        const injectionDetail = transplantProcess.injection_station_details[i].injection_detail
        const validatedData = checkProperties("injection", injectionDetail, injectionProperties, `射台#${i + 1}：`)
        config.data = [...config.data, ...validatedData]
      }
    } else if (config.type == "adaptionTableData") {
      config.data = checkAdaption("adaption", transplantProcess.basic_machine_info, transplantProcess.basic_mold_info)
    }
  }
}

function updateInfo(view: string) {
  if (view == "mold") {
    const routedata = router.resolve({
      path: `/mold/${props.originProcess.basic_mold_info.id}/edit`,
    })
    window.open(routedata.href, "_blank")
  } else if (view == "origin_machine") {
    const routedata = router.resolve({
      path: "/machine/injection/create",
      query: {
        id: props.originProcess.basic_machine_info.id,
      },
    })
    window.open(routedata.href, "_blank")
  } else if (view == "transplant_machine") {
    const routedata = router.resolve({
      path: "/machine/injection/create",
      query: {
        id: props.transplantProcess.basic_machine_info.id,
      },
    })
    window.open(routedata.href, "_blank")
  }
}

function tableCellStyle({ row, column, rowIndex, columnIndex }: any) {
  let col = "black"
  if (row.suggest === "✔" && columnIndex === 3) {
    col = "rgb(78, 201, 162)"
  } else if (row.suggest === "选填" && columnIndex === 3) {
    col = "rgb(241, 159, 27)"
  } else if (row.suggest === "必填" && columnIndex === 3) {
    col = "red"
  } else if (row.suggest === "适用" && columnIndex === 2) {
    col = "rgb(78, 201, 162)"
  } else if (row.suggest === "不适用" && columnIndex === 2) {
    col = "red"
  } else if (row.suggest === "注意" && columnIndex === 2) {
    col = "rgb(241, 159, 27)"
  }
  return { color: col }
}

// 绑定 clickHandler（函数引用必须在函数定义后）
tableConfig.value.forEach(config => {
  if (config.clickHandler === "" || typeof config.clickHandler === "function") {
    if (config.type !== "adaptionTableData") {
      config.clickHandler = (datasource: string) => updateInfo(datasource)
    }
  }
})

// 监听 props 变化，触发 checkProcess
watch(
  () => [props.originProcess, props.transplantProcess],
  () => {
    checkProcess(props.originProcess, props.transplantProcess)
  },
  { deep: true, immediate: true }
)
</script>