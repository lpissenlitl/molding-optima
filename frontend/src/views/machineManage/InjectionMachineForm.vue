<template>
  <div>
    <el-form 
      ref="machineInfoForm" 
      size="mini" 
      label-width="10rem" 
      label-position="right"
      :model="injection_machine" 
      :rules="rules"
      :inline="true"
    >
      <el-card>
        <div slot="header" class="clearfix">
          机器描述
        </div>

        <template v-for="(item, index) in basic_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`form_item_${index}`"
            :label="item.label" 
            :prop="item.prop"
          >
            <el-input 
              v-if="item.type=='input'"
              v-model="injection_machine[item.prop]"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>

            <el-select
              v-else-if="item.type === 'select'"
              v-model="injection_machine[item.prop]"
              filterable 
              @change="(val) => item.onChange && item.onChange(val)"
              :allow-create="item.allow_create"
              :clearable="item.clearable"
            >
              <el-option
                v-for="(option, opt_idx) in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            
            <el-autocomplete
              v-if="item.type=='autocomplete'"
              v-model.trim="injection_machine[item.prop]" 
              :placeholder="item.placeholder || '请输入内容'"
              clearable
              @clear="query[item.prop]=null"
              :debounce="0"
              :fetch-suggestions="$querySuggestions({
                table: item.table,
                column: item.column,
              })"
            > 
            </el-autocomplete>
            
            <el-date-picker
              v-else-if="item.type=='date'"
              v-model="injection_machine[item.prop]"
              type="date"
              placeholder="选择日期"
              value-format="yyyy-MM-dd"
            ></el-date-picker>
          </el-form-item>
        </template>
      </el-card>

      <el-card>
        <div slot="header" class="clearfix">
          注射单元
        </div>
        <el-tabs 
          class="molding-tabs" 
          v-model="active_tab_index"
        >
          <el-tab-pane
            v-for="(injection_unit, index) in injection_machine.injection_units"
            :key="index"
            :label="'注射部件-#' + String(index + 1)"
            :name="String(index)"
          >
            <injection-unit-form 
              ref="injectionUnits"
              :injection-unit="injection_unit"
            />
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <el-card>
        <div slot="header" class="clearfix">
          锁模单元
        </div>

        <template v-for="(item, index) in clamping_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`clamping_item_${index}`"
            :label="item.label" 
            :prop="item.prop"
          >
            <el-input 
              v-if="item.type=='input'"
              v-model="injection_machine[item.prop]"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>

            <el-input 
              v-else-if="item.type=='number'"
              v-model="injection_machine[item.prop]"
              v-number="item.fixed || 2"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>


            <el-select
              v-else-if="item.type === 'select'"
              v-model="injection_machine[item.prop]"
              filterable 
              :allow-create="item.allow_create"
              :clearable="item.clearable"
            >
              <el-option
                v-for="(option, opt_idx) in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            
            <el-autocomplete
              v-if="item.type=='autocomplete'"
              v-model.trim="injection_machine[item.prop]" 
              :placeholder="item.placeholder || '请输入内容'"
              clearable
              @clear="query[item.prop]=null"
              :debounce="0"
              :fetch-suggestions="$querySuggestions({
                table: item.table,
                column: item.column,
              })"
            > 
            </el-autocomplete>
            
            <el-date-picker
              v-else-if="item.type=='date'"
              v-model="injection_machine[item.prop]"
              type="date"
              placeholder="选择日期"
              value-format="yyyy-MM-dd"
            ></el-date-picker>
          </el-form-item>
        </template>
      </el-card>

      
      <el-card>
        <div slot="header" class="clearfix">
          顶出系统
        </div>
        
        <template v-for="(item, index) in ejection_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`ejection_item_${index}`"
            :label="item.label" 
            :prop="item.prop"
          >
            <el-input 
              v-if="item.type=='number'"
              v-model="injection_machine[item.prop]"
              v-number="item.fixed || 2"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>

            <el-select
              v-else-if="item.type === 'select'"
              v-model="injection_machine[item.prop]"
              filterable 
              :allow-create="item.allow_create"
              :clearable="item.clearable"
            >
              <el-option
                v-for="(option, opt_idx) in item.options"
                :key="opt_idx"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>
        </template>
      </el-card>

      <el-card>
        <div slot="header" class="clearfix">
          配套参数
        </div>

        <template v-for="(item, index) in supporting_form_items">
          <el-divider 
            v-if="item.type=='divider'" 
            :key="`divider_${index}`"
            content-position="center"
          >
            {{ item.label }}
          </el-divider>
          
          <el-form-item 
            v-else 
            :key="`form_item_${index}`"
            :label="item.label" 
            :prop="item.prop"
          >
            <el-input 
              v-if="item.type=='number'"
              v-model="injection_machine[item.prop]"
              v-number="item.fixed || 2"
              :placeholder="item.placeholder || `请输入${item.label}`"
            >
              <span slot="suffix" v-if="item.unit">{{ item.unit }}</span>
            </el-input>
            
            <el-date-picker
              v-else-if="item.type=='date'"
              v-model="injection_machine[item.prop]"
              type="date"
              placeholder="选择日期"
              value-format="yyyy-MM-dd"
            ></el-date-picker>
          </el-form-item>
        </template>
      </el-card>
    </el-form>

    <div class="floating-actions-right">
      <el-button
        v-if="injection_machine.id" 
        type="success" 
        size="small"
        :loading="export_loading" 
        @click="exportMachineToExcel" 
      >
        导  出
      </el-button>
      <el-button 
        v-if="view_context.is_dialog"
        type="danger"
        size="small" 
        @click="$emit('close')" 
      >
        返  回
      </el-button>
      <el-button 
        v-else
        type="danger"
        size="small"
        @click="resetView" 
      >
        重  置
      </el-button>
      <el-button
        v-if="injection_machine.id"
        type="primary" 
        size="small" 
        :loading="update_loading" 
        @click="saveMachineInfo"
      >
        更  新
      </el-button>
      <el-button
        v-else
        type="primary" 
        size="small" 
        :loading="save_loading" 
        @click="saveMachineInfo"
      >
        保  存
      </el-button>
    </div>
  </div>
</template>

<script>
import * as machine_const from "@/constants/machine-const"
import { machineMethod } from "@/api"
import { getFullFileUrl } from "@/utils/assert"
import InjectionUnitForm from "./components/InjectionUnitForm.vue"
import { createValidateAndFocus } from "@/utils/form-helper"

export default {
  name: "InjectionMachineForm",
  components: {
    InjectionUnitForm
  },
  props: {
    viewContext: {
      type: Object,
      default: () => ({
        id: null,
        is_dialog: false,
        mode: null,
        excel_data: null
      })
    }
  },
  data() {
    return {
      view_context: this.viewContext,
      injection_machine: structuredClone(machine_const.machineInfoForm),
      basic_form_items: [
        // --- 基础信息 ---
        { label: "设备编号", prop: "device_no", type: "input", placeholder: "设备唯一标识" },
        { label: "品牌", prop: "brand", type: "select", allow_create: true, clearable: true, options: machine_const.injectionMachineBrandOptions },
        { label: "制造商", prop: "manufacturer", type: "select", allow_create: true, clearable: true, options: machine_const.injectionMachineManufacturerOptions },
        { label: "设备型号", prop: "model", type: "autocomplete", table: "injection_molding_machine", column: "model" },
        { label: "设备位置", prop: "location", type: "autocomplete", table: "injection_molding_machine", column: "location", placeholder: "格式：xx工厂-xx车间-xx区" },
        { label: "设备类型", prop: "machine_type", type: "select", options: machine_const.machineTypeOptions },
        { label: "射台数量", prop: "unit_count", type: "select", options: machine_const.injectionUnitCountOptions, onChange: this.onUnitCountChanged },
        { label: "驱动系统", prop: "drive_system", type: "select", options: machine_const.driveSystemOptions },
        { label: "资产编号", prop: "asset_no", type: "input", placeholder: "内部资产编号" },
        // --- 控制器信息 ---
        { label: "控制器信息", type: "divider" },
        { label: "控制器型号", prop: "controller_model", type: "select", allow_create: true, clearable: true, options: machine_const.controllerModelOptions },
        { label: "控制器版本", prop: "controller_version", type: "select", allow_create: true, clearable: true, options: machine_const.controllerVersionOptions },
        { label: "通讯接口", prop: "is_comm_enabled", type: "select", options: machine_const.commAbilityOptions },
        { label: "通讯协议", prop: "communication_protocol", type: "select", options: machine_const.communicationProtocolOptions },
        { label: "通讯 IP", prop: "communication_ip", type: "input", placeholder: "格式：192.168.1.1" },
        // { label: "上次通讯时间", prop: "last_comm_time", type: "datetime" },
        // --- 单位系统信息 ---
        { label: "默认单位系统", type: "divider" },
        { label: "压力单位", prop: "pressure_unit", type: "select", options: machine_const.pressureUnitOptions },
        { label: "速度单位", prop: "speed_unit", type: "select", options: machine_const.speedUnitOptions },
        { label: "位置单位", prop: "position_unit", type: "select", options: machine_const.positionUnitOptions },
        { label: "时间单位", prop: "time_unit", type: "select", options: machine_const.timeUnitOptions },
        { label: "背压单位", prop: "back_pressure_unit", type: "select", options: machine_const.pressureUnitOptions },
        { label: "螺杆转速单位", prop: "screw_rotation_unit", type: "select", options: machine_const.screwRotationUnitOptions },
        { label: "温度单位", prop: "temperature_unit", type: "select", options: machine_const.temperatureUnitOptions },
        { label: "锁模力单位", prop: "clamping_force_unit", type: "select", options: machine_const.clampingForceUnitOptions }
      ],
      clamping_form_items: [
        // --- 模板与结构参数 ---
        { label: "模板与结构参数", type: "divider" },
        { label: "定模板宽度", prop: "fixed_platen_width", type: "number", unit: "mm", fixed: 2, placeholder: "水平方向尺寸（左右）" },
        { label: "定模板高度", prop: "fixed_platen_height", type: "number", unit: "mm", fixed: 2, placeholder: "垂直方向尺寸（上下）" },
        { label: "定模板厚度", prop: "fixed_platen_thickness", type: "number", unit: "mm", fixed: 2, placeholder: "定模板本体厚度" },
        { label: "动模板宽度", prop: "moving_platen_width", type: "number", unit: "mm", fixed: 2, placeholder: "水平方向尺寸（左右）" },
        { label: "动模板高度", prop: "moving_platen_height", type: "number", unit: "mm", fixed: 2, placeholder: "垂直方向尺寸（上下）" },
        { label: "动模板厚度", prop: "moving_platen_thickness", type: "number", unit: "mm", fixed: 2, placeholder: "动模板本体厚度" },

        // --- 拉杆（格林柱）参数 ---
        { label: "拉杆参数", type: "divider" },
        { label: "拉杆间距（宽）", prop: "tie_bar_spacing_width", type: "number", unit: "mm", fixed: 2, placeholder: "拉杆内侧水平净距" },
        { label: "拉杆间距（高）", prop: "tie_bar_spacing_height", type: "number", unit: "mm", fixed: 2, placeholder: "拉杆内侧垂直净距" },
        { label: "拉杆直径", prop: "tie_bar_diameter", type: "number", unit: "mm", fixed: 2, placeholder: "单根拉杆直径" },
        { label: "拉杆数量", prop: "tie_bar_count", type: "number", unit: "个", fixed: 0, placeholder: "通常为4根" },

        // --- 容模能力 ---
        { label: "容模能力", type: "divider" },
        { label: "最小模板间距", prop: "min_platen_spacing", type: "number", unit: "mm", fixed: 2, placeholder: "模板可闭合的最小距离" },
        { label: "最大模板间距", prop: "max_platen_spacing", type: "number", unit: "mm", fixed: 2, placeholder: "模板可打开的最大距离" },
        { label: "最小容模宽度", prop: "min_mold_length", type: "number", unit: "mm", fixed: 2, placeholder: "可安装模具最小长度" },
        { label: "最大容模宽度", prop: "max_mold_length", type: "number", unit: "mm", fixed: 2, placeholder: "可安装模具最大长度" },
        { label: "最小容模高度", prop: "min_mold_width", type: "number", unit: "mm", fixed: 2, placeholder: "可安装模具最小宽度" },
        { label: "最大容模高度", prop: "max_mold_width", type: "number", unit: "mm", fixed: 2, placeholder: "可安装模具最大宽度" },
        { label: "最小容模厚度", prop: "min_mold_thickness", type: "number", unit: "mm", fixed: 2, placeholder: "可安装模具最小总厚" },
        { label: "最大容模厚度", prop: "max_mold_thickness", type: "number", unit: "mm", fixed: 2, placeholder: "可安装模具最大总厚" },
        { label: "最大开模行程", prop: "max_opening_stroke", type: "number", unit: "mm", fixed: 2, placeholder: "最大开模距离" },

        // --- 锁模性能 ---
        { label: "锁模性能", type: "divider" },
        { label: "锁模类型", prop: "clamping_type", type: "select", options: machine_const.clampingTypeOptions },
        { label: "最大锁模力", prop: "max_clamping_force", type: "number", unit: "Ton", fixed: 0, placeholder: "数值即可，如：1500" },
      ],
      ejection_form_items: [
        // --- 顶出系统 ---
        { label: "顶出类型", prop: "ejection_type", type: "select", allow_create: true, clearable: true, options: machine_const.ejectionTypeOptions },
        { label: "顶出模式", prop: "ejection_mode", type: "select", allow_create: true, clearable: true, options: machine_const.ejectionModeOptions },
        { label: "顶出行程", prop: "ejection_stroke", type: "number", unit: "mm", fixed: 2 },
        { label: "顶出力", prop: "ejection_force", type: "number", unit: "kN", fixed: 2 },
      ],
      supporting_form_items: [
        // --- 安装与空间参数 ---
        { label: "安装与空间参数", type: "divider" },
        { label: "机台外形尺寸（长）", prop: "size_length", type: "number", unit: "mm", fixed: 2, placeholder: "含油箱、电柜等突出部分" },
        { label: "机台外形尺寸（宽）", prop: "size_width", type: "number", unit: "mm", fixed: 2, placeholder: "含操作面板或侧向附件" },
        { label: "机台外形尺寸（高）", prop: "size_height", type: "number", unit: "mm", fixed: 2, placeholder: "至最高点，含料斗/报警灯" },
        { label: "机台重量", prop: "machine_weight", type: "number", unit: "kg", fixed: 0, placeholder: "整机干重" },

        // --- 电气与能耗参数 ---
        { label: "电气与能耗参数", type: "divider" },
        { label: "电机功率", prop: "motor_power", type: "number", unit: "kW", fixed: 1, placeholder: "主驱动电机额定功率" },
        { label: "电热功率", prop: "heater_power", type: "number", unit: "kW", fixed: 1, placeholder: "总加热功率" },
        { label: "额定功率", prop: "rated_power", type: "number", unit: "kW", fixed: 1, placeholder: "整机最大输入功率）" },

        // --- 设备生命周期信息 ---
        { label: "日期信息", type: "divider" },
        { label: "制造日期", prop: "manufacture_date", type: "date", placeholder: "设备出厂日期" },
        { label: "投产日期", prop: "commissioning_date", type: "date", placeholder: "首次正式投入生产日期" }
      ],
      rules: {
        model: [
          { required: true, message: "设备型号不能为空!" }
        ],
        device_no: [
          { required: true, message: "设备编号不能为空!" }
        ],
        max_clamping_force: [
          { required: true, message: "最大锁模力不能为空!" }
        ],
      },
      active_tab_index: "0",
      export_loading: false,
      update_loading: false,
      save_loading: false,
    }
  },
  watch: {
    viewContext: {
      handler: function() {
        this.view_context = this.viewContext
        this.initializeView()
      },
      deep: true
    },
    "injection_machine.pressure_unit": function() {
      this.injection_machine.injection_units.forEach((injection_unit) => { 
        injection_unit.pressure_unit = this.injection_machine.pressure_unit
      })
    },
    "injection_machine.speed_unit": function() {
      this.injection_machine.injection_units.forEach((injection_unit) => { 
        injection_unit.speed_unit = this.injection_machine.speed_unit
      })
    },
    "injection_machine.position_unit": function() {
      this.injection_machine.injection_units.forEach((injection_unit) => { 
        injection_unit.position_unit = this.injection_machine.position_unit
      })
    },
    "injection_machine.back_pressure_unit": function() {
      this.injection_machine.injection_units.forEach((injection_unit) => { 
        injection_unit.back_pressure_unit = this.injection_machine.back_pressure_unit
      })
    },
    "injection_machine.screw_rotation_unit": function() {
      this.injection_machine.injection_units.forEach((injection_unit) => { 
        injection_unit.screw_rotation_unit = this.injection_machine.screw_rotation_unit
      })
    },
    "injection_machine.time_unit": function() {
      this.injection_machine.injection_units.forEach((injection_unit) => { 
        injection_unit.time_unit = this.injection_machine.time_unit
      })
    },
    "injection_machine.temperature_unit": function() {
      this.injection_machine.injection_units.forEach((injection_unit) => { 
        injection_unit.temperature_unit = this.injection_machine.temperature_unit
      })
    }
  },
  mounted() {
    this.initializeView()
  },
  methods: {
    async initializeView() {
      if (this.view_context.id) {
        this.injection_machine.id = this.view_context.id
      } else if (this.$route.query.id) {
        this.injection_machine.id = this.$route.query.id
      } else if (this.view_context.mode == "import") {
        this.injection_machine = this.view_context.excel_data
      }

      this.getMachineInfo(this.injection_machine.id)
    },
    onUnitCountChanged(val) {
      let bef = this.injection_machine.injection_units.length
      if (bef < val) {
        for (let i = bef; i < val; ++i) {
          this.injection_machine.injection_units.push(structuredClone(machine_const.injectionUnitForm))
        }
      } else if (bef > val) {
        this.injection_machine.injection_units.splice(val, bef - val)
      }
      this.active_tab_index = String(val - 1)
    },
    exportMachineToExcel() {
      // exportReport({
      //   "resource": "injection_machine",
      //   "injection_machine": this.injection_machine
      // }).then(res => {
      //   if (res.status === 0 && res.data.url) {
      //     window.location.href = getFullFileUrl(res.data.url)
      //     this.$message({ message: "导出成功。", type: "success" })
      //     this.$emit("close")
      //   }
      // })
    },
    async getMachineInfo(id) {
      if (!id) return

      // 从数据库读取参数
      const res = await machineMethod.getDetail(this.injection_machine.id)
      if (res.status === 0) {
        this.injection_machine = res.data
      } else {
        this.$message({ message: res.message, type: "error" })
      }
    },
    async saveMachineInfo() {
      if (!this.$hasPermission("update_machine")) {
        return this.$message("无机器信息的编辑权限")
      }
      const validate = createValidateAndFocus(this)
      let access = true

      // 校验机器参数
      access = await validate(this.$refs.machineInfoForm)
      if (!access) return

      // 校验射台参数
      for (let i = 0; i < this.$refs.injectionUnits.length; i++) {
        const component = this.$refs.injectionUnits[i]
        access = await component.checkFormDataValid()
        if (!access) {
          this.active_tab_index = String(i)
          return
        }
      }

      if (this.injection_machine.id) {
        // 更新设备参数
        const res = await machineMethod.edit(this.injection_machine, this.injection_machine.id)
        if (res.status === 0) {
          this.$message({ message: "编辑成功！", type: "success" })
          this.$emit("close")
        }
      } else {
        // 新增设备参数
        const res = await machineMethod.add(this.injection_machine)
        if (res.status === 0) {
          this.$message({ message: "新增成功！", type:"success" })
          this.$router.push("/equipment/injection/list")
        }
      }
    },
    resetView() {      
      this.injection_machine = structuredClone(machine_const.machineInfoForm)
    },
  }
}
</script>

<style lang="scss" scoped>

</style>
