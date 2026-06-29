<template>
  <div>
    <el-card shadow="hover" id="origin_machine">
      <div slot="header" class="clearfix" style="text-align:center">
        <span>工艺条件检索</span>
      </div>
      <process-selector @select-process="onProcessSelected" />
    </el-card>

    <el-card shadow="hover">
      <div slot="header" class="clearfix" style="text-align:center">
        <span>转换前工艺条件</span>
      </div>
      <process-condition 
        ref="originProcessCondition"
        mode="view"
        :process-condition="origin_process.condition"
      />
      <process-parameter 
        :process-parameter="origin_process.parameter"
        :machine-info="origin_process.condition.machine_info"
      />
    </el-card>

    <el-card shadow="hover" id="transfer_machine">
      <div slot="header" class="clearfix" style="text-align:center">
        <span>转换后工艺条件</span>
      </div>
      <process-condition 
        ref="targetProcessCondition"
        mode="transplant"
        :process-condition="target_process.condition"
      />
      <process-parameter 
        :process-parameter="target_process.parameter"
        :machine-info="target_process.condition.machine_info"
      />
      <el-drawer
        :visible.sync="show_error_drawer"
        title="参数校验失败"
        direction="rtl"
        size="400px"
      >
        <div class="error-list" style="padding: 16px;">
          <el-alert
            v-for="(error, index) in error_list"
            :key="index"
            type="warning"
            :closable="false"
            show-icon
            style="margin-bottom: 12px;"
          >
            {{ error.invalid_desc }}
          </el-alert>

          <el-empty
            v-if="error_list.length === 0"
            description="暂无错误信息"
            style="margin-top: 40px;"
          />
        </div>
      </el-drawer>
    </el-card>

    <div class="bottom-center-actions">
      <el-button-group>
        <el-button 
          type="danger" 
          size="small" 
          @click="resetView"
        >
          重置界面
        </el-button>
        <el-button 
          type="success" 
          size="small" 
          @click="transplantOriginalProcess"
        >
          执行工艺移植
        </el-button>
        <el-button
          type="warning" 
          size="small"
          @click="validateTransplantedProcess"
        >
          校验工艺参数
        </el-button>
        <el-button 
          type="primary" 
          size="small" 
          @click="saveTransplantedProcess"
        >
          保存移植工艺
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script>
import ProcessSelector from "./components/ProcessSelector.vue"
import ProcessCondition from "@/components/process/ProcessCondition.vue"
import ProcessParameter from "./components/ProcessParameter.vue"
import { injectionProcessForm } from "@/constants/process-const"
import { getProcessParameterFrontend, saveProcessParameterFrontend, transplantProcessParameter } from "@/api"

// ========== 工艺参数校验配置 ==========

// 字段名称映射（用于动态生成校验项名称）
const FIELD_NAMES = {
  // 注射参数
  inj_pres: "注射压力",
  inj_spd: "注射速度",
  inj_pos: "注射位置",
  // VP切换
  vps_pos: "VP切换位置",
  vps_pres: "VP切换压力",
  // 保压参数
  hold_pres: "保压压力",
  hold_spd: "保压速度",
  hold_t: "保压时间",
  // 计量参数
  met_pres: "计量压力",
  met_rot_spd: "计量螺杆转速",
  met_back_pres: "计量背压",
  met_pos: "计量位置",
  // 松退参数
  pre_decomp_pres: "储前松退压力",
  pre_decomp_spd: "储前松退速度",
  pst_decomp_pres: "储后松退压力",
  pst_decomp_spd: "储后松退速度",
  // 终止位置
  met_end_pos: "计量终止位置",
  max_injection_stroke: "最大注射行程",
}

// 注塑机参数上限字段映射
const MACHINE_LIMITS = {
  max_set_injection_pressure: "最大可设定注射压力",
  max_set_injection_speed: "最大可设定注射速度",
  max_set_holding_pressure: "最大可设定保压压力",
  max_set_holding_speed: "最大可设定保压速度",
  max_set_metering_pressure: "最大可设定计量压力",
  max_set_screw_rotation_speed: "最大可设定计量螺杆转速",
  max_set_metering_back_pressure: "最大可设定计量背压",
  max_set_decompression_pressure: "最大可设定射退压力",
  max_decompression_speed: "最大可设定射退速度",
  max_injection_stroke: "最大注射行程",
}

// ========== 模式数值常量（与后端 models.py 保持一致）==========

// VP切换模式 vps_mode
const VPS_MODE = {
  POSITION: 0,      // 位置
  TIME: 1,          // 时间
  TIME_POSITION: 2, // 时间&位置
  PRESSURE: 3,      // 压力
  SPEED: 4,         // 速度
}

// 松退控制模式 pre_met_decomp_mode / pst_met_decomp_mode
const DECOMP_MODE = {
  NONE: 0,     // 否（无控制）
  DISTANCE: 1, // 距离
  TIME: 2,     // 时间
}

export default {
  name: "ProcessTransplant",
  components: { 
    ProcessSelector, 
    ProcessCondition,
    ProcessParameter,
  }, 
  data() {
    return {
      origin_process: structuredClone(injectionProcessForm),
      target_process: structuredClone(injectionProcessForm),
      error_list: [],
      show_error_drawer: false,
      show_drawer: false
    }
  },
  watch: {
    "origin_process.condition": {
      handler() {
        // 目标工艺的模具信息与材料信息与原工艺一致
        this.target_process.condition.mold_info = this.origin_process.condition.mold_info
        this.target_process.condition.shot_index = this.origin_process.condition.shot_index
        this.target_process.condition.polymer_info = this.origin_process.condition.polymer_info
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    async onProcessSelected(id) {
      if (!id) {
        return this.$message({ message: "无效id, 读取工艺参数失败!", type: "warning" })
      }
      const res = await getProcessParameterFrontend(id)
      if (res.status === 0) {
        const { condition, parameter } = res.data
        Object.assign(this.origin_process.condition, condition)
        if (parameter?.setting_process) {
          this.origin_process.parameter.id = parameter.id
          this.origin_process.parameter.setting_process = parameter.setting_process
        }
      } else {
        this.$message({ message: "读取失败, 无工艺参数记录！", type: "warning" })
      }
    },

    // ========== 校验逻辑优化 ==========
    
    // 安全获取 table_data 中的值
    getTableValue(tableData, row, col) {
      return tableData?.[row]?.sections?.[col]
    },
    
    // 构建校验项
    buildCheckItem(name, value, compareVal, compareName) {
      return {
        name,
        value: Number(value),
        compare_val: Number(compareVal),
        compare_name: compareName,
        invalid_desc: compareName ? `${name} 超出 ${compareName} 限制！` : `${name} 数据缺失或无效！`
      }
    },

    validateTransplantedProcess() {
      const check_list = []
      const process_ = this.target_process.parameter.setting_process
      const mac_info = this.target_process.condition.machine_info
      const injt_info = this.target_process.condition.injection_unit
      
      // 获取设备限制值
      const get_limit = (field) => injt_info?.[field]
      
      // 校验是否为液压机
      const is_hydraulic = mac_info?.drive_system?.includes("液")
      
      // === 1. 注射参数 ===
      const injection_ = process_.injection
      const inj_table = injection_?.table_data || []
      for (let i = 0; i < (injection_?.stage || 0); i++) {
        // 压力
        check_list.push(this.buildCheckItem(
          `注射${i + 1}段压力`,
          this.getTableValue(inj_table, 0, i),
          get_limit("max_set_injection_pressure"),
          FIELD_NAMES.inj_pres + MACHINE_LIMITS.max_set_injection_pressure
        ))
        // 速度
        check_list.push(this.buildCheckItem(
          `注射${i + 1}段速度`,
          this.getTableValue(inj_table, 1, i),
          get_limit("max_set_injection_speed"),
          FIELD_NAMES.inj_spd + MACHINE_LIMITS.max_set_injection_speed
        ))
        // 位置（与前一段位置或储料1段位置比较）
        const pos_compare_val = i === 0 
          ? this.getTableValue(process_?.metering?.table_data, 3, 0)
          : this.getTableValue(inj_table, 2, i - 1)
        const pos_compare_name = i === 0 ? "储料1段位置" : `注射${i}段位置`
        check_list.push(this.buildCheckItem(
          `注射${i + 1}段位置`,
          this.getTableValue(inj_table, 2, i),
          pos_compare_val,
          pos_compare_name
        ))
      }
      
      // === 2. VP切换 ===
      const vp_switch = process_?.vp_switch
      if (vp_switch?.mode === VPS_MODE.POSITION) {
        const vp_pos_compare_val = injection_?.stage === 1
          ? this.getTableValue(process_?.metering?.table_data, 3, 0)
          : this.getTableValue(inj_table, 2, injection_?.stage - 2)
        const vp_pos_compare_name = injection_?.stage === 1 ? "储料1段位置" : `注射${injection_?.stage - 1}段位置`
        check_list.push(this.buildCheckItem("VP切换位置", vp_switch.position, vp_pos_compare_val, vp_pos_compare_name))
      } else if (vp_switch?.mode === VPS_MODE.PRESSURE) {
        check_list.push(this.buildCheckItem("VP切换压力", vp_switch.pressure, get_limit("max_set_injection_pressure"), FIELD_NAMES.vps_pres + MACHINE_LIMITS.max_set_injection_pressure))
      }
      
      // === 3. 保压参数 ===
      const holding_ = process_?.holding
      const hold_table = holding_?.table_data || []
      for (let i = 0; i < (holding_?.stage || 0); i++) {
        check_list.push(this.buildCheckItem(
          `保压${i + 1}段压力`, this.getTableValue(hold_table, 0, i), get_limit("max_set_holding_pressure"),
          FIELD_NAMES.hold_pres + MACHINE_LIMITS.max_set_holding_pressure
        ))
        check_list.push(this.buildCheckItem(
          `保压${i + 1}段速度`, this.getTableValue(hold_table, 1, i), get_limit("max_set_holding_speed"),
          FIELD_NAMES.hold_spd + MACHINE_LIMITS.max_set_holding_speed
        ))
      }
      
      // === 4. 计量参数 ===
      const metering_ = process_?.metering
      const met_table = metering_?.table_data || []
      for (let i = 0; i < (metering_?.stage || 0); i++) {
        // 压力（仅液压机校验）
        if (is_hydraulic) {
          check_list.push(this.buildCheckItem(
            `计量${i + 1}段压力`, this.getTableValue(met_table, 0, i), get_limit("max_set_metering_pressure"),
            FIELD_NAMES.met_pres + MACHINE_LIMITS.max_set_metering_pressure
          ))
        }
        check_list.push(this.buildCheckItem(
          `计量${i + 1}段螺杆转速`, this.getTableValue(met_table, 1, i), get_limit("max_set_screw_rotation_speed"),
          FIELD_NAMES.met_rot_spd + MACHINE_LIMITS.max_set_screw_rotation_speed
        ))
        check_list.push(this.buildCheckItem(
          `计量${i + 1}段背压`, this.getTableValue(met_table, 2, i), get_limit("max_set_metering_back_pressure"),
          FIELD_NAMES.met_back_pres + MACHINE_LIMITS.max_set_metering_back_pressure
        ))
        // 位置
        const met_pos_compare_val = i === metering_?.stage - 1 ? metering_?.ending_position : this.getTableValue(met_table, 3, i + 1)
        const met_pos_compare_name = i === metering_?.stage - 1 ? "计量终止位置" : `计量${i + 2}段位置`
        check_list.push(this.buildCheckItem(
          `计量${i + 1}段位置`, this.getTableValue(met_table, 3, i), met_pos_compare_val, met_pos_compare_name
        ))
      }
      
      // === 5. 松退参数 ===
      const decomp_data = metering_?.decompress_table_data || []
      if (metering_?.pre_decompress_mode !== DECOMP_MODE.NONE && decomp_data[0]) {
        check_list.push(this.buildCheckItem("储前松退压力", decomp_data[0].pressure, get_limit("max_set_decompression_pressure"), FIELD_NAMES.pre_decomp_pres + MACHINE_LIMITS.max_set_decompression_pressure))
        check_list.push(this.buildCheckItem("储前松退速度", decomp_data[0].velocity, get_limit("max_decompression_speed"), FIELD_NAMES.pre_decomp_spd + MACHINE_LIMITS.max_decompression_speed))
      }
      if (metering_?.post_decompress_mode !== DECOMP_MODE.NONE && decomp_data[1]) {
        check_list.push(this.buildCheckItem("储后松退压力", decomp_data[1].pressure, get_limit("max_set_decompression_pressure"), FIELD_NAMES.pst_decomp_pres + MACHINE_LIMITS.max_set_decompression_pressure))
        check_list.push(this.buildCheckItem("储后松退速度", decomp_data[1].velocity, get_limit("max_decompression_speed"), FIELD_NAMES.pst_decomp_spd + MACHINE_LIMITS.max_decompression_speed))
      }
      
      // === 6. 计量终止位置 ===
      check_list.push(this.buildCheckItem("计量终止位置", metering_?.ending_position, get_limit("max_injection_stroke"), FIELD_NAMES.met_end_pos + MACHINE_LIMITS.max_injection_stroke))
      
      // === 执行校验 ===
      const invalid_list = check_list.filter(item => {
        if (item.compare_val == null) return false
        if (item.value == null || isNaN(item.value)) {
          item.invalid_desc = `${item.name} 数据缺失或无效！`
          return true
        }
        if (isNaN(item.compare_val)) {
          item.invalid_desc = `${item.compare_name} 数据缺失或无效！`
          return true
        }
        return item.value > item.compare_val
      })
      
      this.error_list = invalid_list
      if (invalid_list.length > 0) {
        this.show_error_drawer = true
        return false
      }
      return true
    },

    async transplantOriginalProcess() {
      const origin_valid = await this.$refs.originProcessCondition.checkFormDataValid()
      if (!origin_valid) {
        this.$message({ message: "请检查原始工艺数据，可读取历史工艺信息或手动输入工艺信息", type: "warning" })
        return false
      }

      const target_valid = await this.$refs.targetProcessCondition.checkFormDataValid()
      if (!target_valid) {
        this.$message({ message: "请输入要转换的设备信息！", type: "warning" })
        return false
      }

      // 获取源和目标工艺条件的 ID
      const origin_condition_id = this.origin_process.condition.id
      const target_condition_id = this.target_process.condition.id

      if (!origin_condition_id || !target_condition_id) {
        this.$message({ message: "缺少工艺条件ID，无法执行移植", type: "warning" })
        return false
      }

      try {
        // 调用后端工艺移植接口
        const res = await transplantProcessParameter({
          origin_condition_id,
          target_condition_id
        })

        if (res.status === 0) {
          // 用后端返回的转换后参数替换目标工艺参数
          this.target_process.parameter.setting_process = res.data.target_setting_process
          this.$message({ message: "工艺参数转换完成", type: "success" })
        } else {
          this.$message({ message: res.message || "工艺参数转换失败", type: "error" })
        }
      } catch (error) {
        console.error("工艺移植失败:", error)
        this.$message({ message: "工艺参数转换失败，请重试", type: "error" })
      }
    },

    async saveTransplantedProcess() {
      const target_valid = await this.$refs.targetProcessCondition.checkFormDataValid()
      if (!target_valid) {
        this.$message({ message: "请输入要转换的设备信息！", type: "warning" })
        return false
      }

      const condition = {
        status: "draft",
        origin_type: "manual_creation",
        mold_id: this.target_process.condition.mold_info.id,
        shot_index: this.target_process.condition.shot_index,
        injection_machine_id: this.target_process.condition.machine_info.id,
        injection_index: this.target_process.condition.injection_index,
        polymer_id: this.target_process.condition.polymer_info.id,
      }

      const injection_process = {
        condition,
        parameter: {
          setting_process: this.target_process.parameter.setting_process
        }
      }

      const res = await saveProcessParameterFrontend(injection_process)
      if (res.status === 0) {
        this.$message.success("转换后工艺已保存成功")
        this.$router.push("/process/parameter/list")
      }
    },

    resetView() {
      this.origin_process = structuredClone(injectionProcessForm)
      this.target_process = structuredClone(injectionProcessForm)
    },
  }
}
</script>

<style lang="scss" scoped>
  .buttonGroup {
    z-index: 999;
    position: fixed;
    text-align: center;
    width: 100%;
    bottom: 5px;
    font-size: 11px;
    line-height: 32px;
    margin: 0;
    height: 40px;
    .el-button {
      width: 8rem;
    }
  }
</style>
