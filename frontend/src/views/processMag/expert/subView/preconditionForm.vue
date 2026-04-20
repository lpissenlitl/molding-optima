<template>
  <el-form
    ref="form"
    :inline="true"
    :model="precondition_detail"
    :rules="rules"
    size="mini"
    label-width="10rem"
  >
    <el-divider class="precondition-divider" content-position="center">
      <span>机器&材料</span>
    </el-divider>

    <el-form-item
      label="注塑机来源"
      prop="machine_data_source"
    >
      <el-autocomplete
        v-model="precondition_detail.machine_data_source"
        placeholder="注塑机来源"
        clearable
        :fetch-suggestions="queryMacDataSourceOptions"
        suffix-icon="el-icon-search"
      >
      </el-autocomplete>
    </el-form-item>

    <el-form-item
      label="注塑机型号"
      prop="machine_trademark"
    >
      <el-autocomplete
        v-model="precondition_detail.machine_trademark"
        placeholder="注塑机型号"
        clearable
        style="width:10rem"
        :fetch-suggestions="queryMacTrademarkOptions"
        @select="handleMacTrademarkSelect"
        suffix-icon="el-icon-search"
      >
        <template slot-scope="{ item }">
          <el-tooltip
            effect="dark"
            :content="'设备编码: ' + [item.serial_no? item.serial_no: '未知']"
            placement="right-end"
          >
            <div style="width:auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
              {{ item.value }}
            </div>
          </el-tooltip>
        </template>
      </el-autocomplete>
    </el-form-item>

    <el-form-item
      label="塑料简称"
      prop="polymer_abbreviation"
    >
      <el-autocomplete
        v-model="precondition_detail.polymer_abbreviation"
        placeholder="塑料简称"
        clearable
        :fetch-suggestions="queryPolyAbbreviationOptions"
        suffix-icon="el-icon-search"
      >
      </el-autocomplete>
    </el-form-item>

    <el-form-item
      label="塑料牌号"
      prop="polymer_trademark"
    >
      <el-autocomplete
        v-model="precondition_detail.polymer_trademark"
        placeholder="塑料牌号"
        clearable
        :fetch-suggestions="queryPolyTrademarkOptions"
        @select="handlePolyTrademarkSelect"
        suffix-icon="el-icon-search"
      >
      </el-autocomplete>
    </el-form-item>

    <el-form-item
      label="推荐熔体温度"
      prop="recommend_melt_temperature"
    >
      <el-input
        v-model="precondition_detail.recommend_melt_temperature"
        :disabled="true" 
      >
        <span slot="suffix">℃</span>
      </el-input>
    </el-form-item>

    <el-divider class="precondition-divider" content-position="center">
      <span>模具信息</span>
    </el-divider>

    <el-form-item
      label="模具编号"
      prop="mold_no"
    >
      <el-tooltip 
        class="item" 
        effect="dark" 
        content="在模具列表中填写相关信息,通过编号检索" 
        placement="top-start"
      >
        <el-autocomplete 
          v-model.trim="precondition_detail.mold_no"
          type="text" 
          :fetch-suggestions="queryMoldNoOptions"
          placeholder="请选择"
          clearable
          :debounce="0"
          @select="handleMoldNoSelect"
          suffix-icon="el-icon-search"
        >
        </el-autocomplete>
      </el-tooltip>
    </el-form-item>

    <el-form-item
      label="型腔数"
      prop="cavity_num"
    >
      <el-input
        v-model="precondition_detail.cavity_num"
        :disabled="true" 
      ></el-input>
    </el-form-item>

    <el-form-item 
      label="注塑周期要求"
      prop="inject_cycle_require"
    >
      <el-input 
        v-model.trim="precondition_detail.inject_cycle_require"
        :disabled="true"
      >
        <span slot="suffix">s</span>
      </el-input>
    </el-form-item>
    <el-form-item 
      label="绑定规则库"
      prop="subrule_no"
    >
      <el-input 
        v-model.trim="precondition_detail.subrule_no"
        :disabled="true"
      >
      </el-input>
    </el-form-item>
    <el-divider class="precondition-divider" content-position="center">
      <span>制品信息</span>
    </el-divider>
    <el-form-item 
      label="注射单元"
      prop="inject_part"
    >
      <el-select
        v-model="precondition_detail.inject_part"
        placeholder="请选择"
        @change="selectInjector"
      >
        <el-option 
          v-for="option, index in inject_part_options"
          :key="index"
          :label="option.label"
          :value="option.value"
        ></el-option>
      </el-select>
    </el-form-item>
    <el-form-item 
      label="射台编码"
      prop="machine_serial_no"
    >
      <el-input 
        v-model.trim="precondition_detail.machine_serial_no"
        :disabled="true"
      >
      </el-input>
    </el-form-item>
    <el-form-item
      label="制品类别"
      prop="product_type"
    >
      <el-select
        v-model="precondition_detail.product_type"
        placeholder="请选择"
        :disabled="true" 
      >
        <el-option
          v-for="item in product_type_options"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        >
        </el-option>
      </el-select>
    </el-form-item>

    <el-form-item
      label="制品编号"
      prop="product_no"
    >
      <el-input
        :disabled="true"
        v-model="precondition_detail.product_no"
      ></el-input>
    </el-form-item>

    <el-form-item
      label="制品名称"
      prop="product_name"
    >
      <el-input
        type="text"
        v-model="precondition_detail.product_name"
        :disabled="true" 
      ></el-input>
    </el-form-item>

    <el-form-item
      label="平均壁厚"
      prop="product_ave_thickness"
    >
      <el-input
        type="text"
        v-model="precondition_detail.product_ave_thickness"
        :disabled="true" 
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item
      label="最大壁厚"
      prop="product_max_thickness"
    >
      <el-input
        type="text"
        v-model="precondition_detail.product_max_thickness"
        :disabled="true" 
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item
      label="制品流长"
      prop="product_max_length"
    >
      <el-input
        type="text"
        v-model="precondition_detail.product_max_length"
        :disabled="true" 
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item
      label="制品总重量"
      prop="product_total_weight"
    >
      <el-tooltip
        effect="dark"
        content="制品总重量"
        placement="right-end"
      >
        <el-input
          type="text"
          v-model="precondition_detail.product_total_weight"
          :disabled="true" 
        >
          <span slot="suffix">g</span>
        </el-input>
      </el-tooltip>
    </el-form-item>

    <el-divider class="precondition-divider" content-position="center">
      <span>浇注系统</span>
    </el-divider>

    <el-form-item
      label="流道长度"
      prop="runner_length"
    >
      <el-input
        type="text"
        v-model="precondition_detail.runner_length"
        :disabled="true" 
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item
      label="流道重量"
      prop="runner_weight"
    >
      <el-input
        type="text"
        v-model="precondition_detail.runner_weight"
        :disabled="true" 
      >
        <span slot="suffix">g</span>
      </el-input>
    </el-form-item>

    <el-form-item
      label="浇口类别"
      prop="gate_type"
    >
      <el-select
        v-model="precondition_detail.gate_type"
        placeholder="请选择"
        :disabled="true" 
      >
        <el-option
          v-for="item in gate_type_options"
          :key="item.val"
          :label="item.label"
          :value="item.value"
        >
        </el-option>
      </el-select>
    </el-form-item>

    <el-form-item
      label="浇口数量"
      prop="gate_num"
    >
      <el-input
        type="text"
        v-model="precondition_detail.gate_num"
        :disabled="true" 
      >
      </el-input>
    </el-form-item>

    <el-form-item
      label="浇口形状"
      prop="gate_shape"
    >
      <el-select
        v-model="precondition_detail.gate_shape"
        placeholder="请选择"
        :disabled="true" 
      >
        <el-option label="圆形" value="圆形"></el-option>
        <el-option label="矩形" value="矩形"></el-option>
      </el-select>
    </el-form-item>

    <el-form-item
      v-if="false" 
      label="浇口横截面积"
      prop="gate_area"
    >
      <el-input
        type="number"
        v-model="precondition_detail.gate_area"
        :disabled="true" 
      ></el-input>
    </el-form-item>

    <el-form-item
      v-if="precondition_detail.gate_shape === '圆形'"
      label="浇口半径(圆)"
      prop="gate_radius"
    >
      <el-input
        type="number"
        v-model="precondition_detail.gate_radius"
        :disabled="true" 
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item
      v-if="precondition_detail.gate_shape === '矩形'" 
      label="浇口长(矩形)"
      prop="gate_length"
    >
      <el-input
        type="number"
        v-model="precondition_detail.gate_length"
        :disabled="true" 
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item
      v-if="precondition_detail.gate_shape === '矩形'" 
      label="浇口宽(矩形)"
      prop="gate_width"
    >
      <el-input
        type="number"
        v-model="precondition_detail.gate_width"
        :disabled="true" 
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="流道类别"
      prop="runner_type"
    >
      <el-select 
        v-model="precondition_detail.runner_type"
        :disabled="true" 
      >
        <el-option label="热流道" value="热流道"></el-option>
        <el-option label="冷流道" value="冷流道"></el-option>
        <el-option label="热转冷" value="热转冷"></el-option>
      </el-select>
    </el-form-item>

    <el-form-item label="热流道段数" prop="hot_runner_num" v-if="precondition_detail.runner_type=='热流道'">
      <el-select :disabled="true" v-model="precondition_detail.hot_runner_num">
        <el-option
          v-for="(option, index) in 36"
          :key="index"
          :label="option"
          :value="option"
        >
        </el-option>
      </el-select>
    </el-form-item>
    <el-form-item label="阀口数量" prop="valve_num" v-if="precondition_detail.runner_type=='热流道'&&precondition_detail.gate_type=='针阀式'">
      <el-input
        type="number"
        v-model="precondition_detail.valve_num"
        :disabled="true" 
      />
    </el-form-item>
  </el-form>
</template>

<script>
import { getOptions } from '@/api';
import { productTypeOptions, gateTypeOptions } from '@/utils/mold-const';
import suggestionOptions from "@/mixins/suggestionOptions.vue";

export default {
  name: "ProcessOptimizePreconditionForm",
  mixins: [suggestionOptions],
  props: {
    maxInjectPart: {
      type: Number,
      default: 0
    },
    preconditionDetail: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      precondition_detail: this.preconditionDetail,
      rules: {
        machine_data_source: [{ required: true, message: '请选择注塑机来源' }],
        machine_id: [{ required: true, message: '请选择注塑机型号' }],
        polymer_abbreviation: [{ required: true, message: '请选择材料类型' }],
        polymer_id: [{ required: true, message: '请选择牌号' }],
        cavity_num: [{ required: true, message: '请选择模腔数' }],
        runner_length: [{ required: true, message: '请输入流道长度' }],
        runner_weight: [{ required: true, message: '请输入流道重量' }],
        gate_type: [{ required: true, message: '请选择浇口类别' }],
        gate_num: [{ required: true, message: '请输入浇口数量' }],
        gate_shape: [{ required: true, message: '请选择浇口形状' }],
        gate_radius: [{ required: true, message: '请输入浇口半径' }],
        gate_length: [{ required: true, message: '请输入浇口长' }],
        gate_width: [{ required: true, message: '请输入浇口宽' }],
        product_type: [{ required: true, message: '请确定制品类别' }],
        product_name: [{ required: true, message: '请输入制品名称'  }],
        product_total_weight: [{ required: true, message: '请输入制品总重量' }],
        product_ave_thickness: [{ required: true, message: '请输入制品平均壁厚' }],
        product_max_thickness: [{ required: true, message: '请输入制品最大壁厚' }],
        product_max_length: [{ required: true, message: '请输入制品最大流长' }]
      },
      max_inject_part: this.maxInjectPart,
      product_type_options: productTypeOptions,
      gate_type_options: gateTypeOptions,
      serial_no_list: [],
    }
  },
  methods: {
    queryMacDataSourceOptions(queryString, cb) {
      cb(this.queryOptions(queryString, "data_source", "machine"))
    },
    queryMacTrademarkOptions(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      if (!this.precondition_detail.machine_data_source) {
        return []
      }

      let promptList = []
      getOptions("machine_trademark", {
        "data_source": this.precondition_detail.machine_data_source,
        "trademark": queryString
      }).then(res => {
        if (res.status == 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
              serial_no: res.data[i].serial_no,
              max_inject_part: res.data[i].injectors.length,
              serial_no_list: res.data[i].injectors
            })
          }
          cb(promptList)
        }
      })
    },
    handleMacTrademarkSelect(item) {
      this.precondition_detail.machine_id = item.id
      // 初始化页面时,max_inject_part由制品的射台数决定;如果注塑机型号变更,那么max_inject_part会跟着注塑机射台数变化
      this.max_inject_part = item.max_inject_part
      this.serial_no_list = item.serial_no_list
    },
    selectInjector(){
      this.precondition_detail.machine_serial_no = this.serial_no_list[this.precondition_detail.inject_part].serial_no
    },
    queryPolyAbbreviationOptions(queryString, cb) {
      cb(this.queryOptions(queryString, "abbreviation", "polymer"))
    },
    queryPolyTrademarkOptions(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      if (!this.precondition_detail.polymer_abbreviation ) {
        return []
      }

      let promptList = []
      getOptions("polymer_trademark", {
        "abbreviation": this.precondition_detail.polymer_abbreviation ,
        "trademark": queryString
      }).then(res => {
        if (res.status == 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
              category: res.data[i].category,
              recommend_melt_temperature: res.data[i].recommend_melt_temperature
            })
          }
          cb(promptList)
        }
      })
    },
    handlePolyTrademarkSelect(item) {
      this.precondition_detail.polymer_id = item.id
      this.precondition_detail.recommend_melt_temperature = item.recommend_melt_temperature
    },
    queryMoldNoOptions(input, cb) {
      input = input == null ? "" : input
      let promptList = []
      getOptions("mold_no", {
        "form_input": input,
        "db_table": "mold"
      }).then(res => {
        if (res.status == 0) {
          res.data.forEach(element => {
            promptList.push(element)
          })
        }
      })
      cb(promptList)
    },
    handleMoldNoSelect(item) {
      this.precondition_detail.mold_id = item.mold_id
    },
  },
  computed: {
    inject_part_options: function() {
      let options = [
        { label: "主射台", value: "0" },
        { label: "副射台", value: "1" },
        { label: "三射台", value: "2" }
      ]
      
      options = options.slice(0, this.max_inject_part == 0 ? 1 : this.max_inject_part)
      return options
    }
  },
  watch: {
    maxInjectPart() {
      this.max_inject_part = this.maxInjectPart
    },
    preconditionDetail() {
      this.precondition_detail = this.preconditionDetail
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-input {
    width: 10rem;
  }
  .el-select {
    width: 10rem;
  }
  .el-autocomplete {
    width: 10rem;
  }
</style>