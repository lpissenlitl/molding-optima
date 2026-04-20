<template>
  <div>
    <el-table :data="moldTableData" style="width: 100%" :cell-style="tableCellStyle">
      <el-table-column prop="mold" label="模具" width="150">
      </el-table-column>
      <el-table-column prop="parameter" label="参数" width="300">
      </el-table-column>
      <el-table-column prop="suggest" label="建议" width="150">
      </el-table-column>
      <el-table-column prop="" label="" width="100">
        <template slot-scope="scope">
          <el-link type="primary" @click="writeMoldData(scope.row.mold)">去填写</el-link>
        </template>
      </el-table-column>
    </el-table>
    <el-table :data="originTableData" style="width: 100%" :cell-style="tableCellStyle">
      <el-table-column prop="machine" label="机台" width="150">
      </el-table-column>
      <el-table-column prop="parameter" label="参数" width="300">
      </el-table-column>
      <el-table-column prop="suggest" label="建议" width="150">
      </el-table-column>
      <el-table-column prop="" label="" width="100">
        <template slot-scope="scope">
          <el-link type="primary" @click="writeMachineData(scope.row.machine)">去填写</el-link>
        </template>
      </el-table-column>
    </el-table>
    <div style="height: 20px"></div>
    <el-table :data="transplantTableData" style="width: 100%" :cell-style="tableCellStyle">
      <el-table-column prop="machine" label="机台" width="150">
      </el-table-column>
      <el-table-column prop="parameter" label="参数" width="300">
      </el-table-column>
      <el-table-column prop="suggest" label="建议" width="150">
      </el-table-column>
      <el-table-column prop="suggest" label="" width="100">
        <template slot-scope="scope">
          <el-link type="primary" @click="writeMachineData(scope.row.machine)">去填写</el-link>
        </template>
      </el-table-column>
    </el-table>
    <el-table :data="adaptionTableData" style="width: 100%" :cell-style="tableCellStyle">
      <el-table-column prop="mold" label="模具与转换机台适配" width="150">
      </el-table-column>
      <el-table-column prop="parameter" label="参数" width="300">
      </el-table-column>
      <el-table-column prop="suggest" label="建议" width="150">
      </el-table-column>
    </el-table>
    <el-checkbox v-model="checkMold" style="background-color: yellow;">校验模具参数</el-checkbox>
    <el-checkbox v-model="checkEjector" style="background-color: yellow;">转换开合模顶针参数</el-checkbox>
  </div>
</template>

<script>
export default {
  name: "CheckResult",
  props: {
    moldInfo: {
      type: Object,
      default: () => {},
    },
    moldResult: {
      type: Object,
      default: () => [],
    },
    originResult: {
      type: Array,
      default: () => [],
    },
    transplantResult: {
      type: Array,
      default: () => [],
    },
    moldResult: {
      type: Array,
      default: () => [],
    },
    machineAdaptionResult: {
      type: Array,
      default: () => [],
    },
    originMachineInfo: {
      type: Object,
      default: () => {},
    },
    transplantMachineInfo: {
      type: Object,
      default: () => {},
    },
    sum: 0,
  },
  data() {
    return {
      mold_info: this.moldInfo,
      mold_result: this.moldResult,
      origin_result: this.originResult,
      transplant_result: this.transplantResult,
      machine_adaption_result: this.machineAdaptionResult,
      origin_machine_info: this.originMachineInfo,
      transplant_machine_info: this.transplant_machine_info,
      a: this.sum,
      isqualified: true,
      checkMold: false,
      checkEjector:false,
    };
  },
  mounted() {
    this.$nextTick(() => {
      this.checkRequired(this.origin_machine_info,this.origin_result,this.originTableData)
      this.checkRequired(this.transplant_machine_info,this.transplant_result,this.transplantTableData)
    })
  },
  methods: {
    checkAdaptionRequired(result,table_data){
      if (
        result.indexOf("注塑机射台数不足,") != -1
      ) {
          let index = result.indexOf("注塑机射台数不足,");
          table_data[index - 1].suggest = "该注塑机不适用";
      }
    },
    checkRequired(machine_info,result,table_data) {
      if (machine_info.pressure_unit == "%"){
        if (
          result.indexOf("最大注射压力为空") != -1 ||
          result.indexOf("最大注射压力为零") != -1
        ) {
          if (result.indexOf("最大注射压力为空") != -1) {
            let index = result.indexOf("最大注射压力为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大注射压力为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
        if (
          result.indexOf("最大保压压力为空") != -1 ||
          result.indexOf("最大保压压力为零") != -1
        ) {
          if (result.indexOf("最大保压压力为空") != -1) {
            let index = result.indexOf("最大保压压力为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大保压压力为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
        if (
          result.indexOf("最大计量压力为空") != -1 ||
          result.indexOf("最大计量压力为零") != -1
        ) {
          if (result.indexOf("最大计量压力为空") != -1) {
            let index = result.indexOf("最大计量压力为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大计量压力为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
      }
      if (machine_info.velocity_unit == "%") {
        if (
          result.indexOf("最大注射速度为空") != -1 ||
          result.indexOf("最大注射速度为零") != -1
        ) {
          if (result.indexOf("最大注射速度为空") != -1) {
            let index = result.indexOf("最大注射速度为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大注射速度为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
        if (
          result.indexOf("最大保压速度为空") != -1 ||
          result.indexOf("最大保压速度为零") != -1
        ) {
          if (result.indexOf("最大保压速度为空") != -1) {
            let index = result.indexOf("最大保压速度为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大保压速度为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
        if (
          result.indexOf("最大松退速度为空") != -1 ||
          result.indexOf("最大松退速度为零") != -1
        ) {
          if (result.indexOf("最大松退速度为空") != -1) {
            let index = result.indexOf("最大松退速度为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大松退速度为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
      }
      if (machine_info.screw_rotation_unit == "%") {
        if (
          result.indexOf("最大螺杆转速为空") != -1 ||
          result.indexOf("最大螺杆转速为零") != -1
        ) {
          if (result.indexOf("最大螺杆转速为空") != -1) {
            let index = result.indexOf("最大螺杆转速为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大螺杆转速为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
      }
      let ejectorSuggest = ""
      if(this.checkEjector){
        ejectorSuggest = "必填有效值(不为0)"
      }
      if(!this.checkEjector){
        ejectorSuggest = "不校验"
      }
      if (machine_info.oc_velocity_unit == "%") {
        if (
          result.indexOf("最大顶进速度为空") != -1 ||
          result.indexOf("最大顶进速度为零") != -1
        ) {
          if (result.indexOf("最大顶进速度为空") != -1) {
            let index = result.indexOf("最大顶进速度为空");
            table_data[index - 1].suggest = ejectorSuggest;
          } else {
            let index = result.indexOf("最大顶进速度为零");
            table_data[index - 1].suggest = ejectorSuggest;
          }
        }
        if (
          result.indexOf("最大顶退速度为空") != -1 ||
          result.indexOf("最大顶退速度为零") != -1
        ) {
          if (result.indexOf("最大顶退速度为空") != -1) {
            let index = result.indexOf("最大顶退速度为空");
            table_data[index - 1].suggest = ejectorSuggest;
          } else {
            let index = result.indexOf("最大顶退速度为零");
            table_data[index - 1].suggest = ejectorSuggest;
          }
        }
        if (
          result.indexOf("最大开模速度为空") != -1 ||
          result.indexOf("最大开模速度为零") != -1
        ) {
          if (result.indexOf("最大开模速度为空") != -1) {
            let index = result.indexOf("最大开模速度为空");
            table_data[index - 1].suggest = ejectorSuggest;
          } else {
            let index = result.indexOf("最大开模速度为零");
            table_data[index - 1].suggest = ejectorSuggest;
          }
        }
        if (
          result.indexOf("最大合模速度为空") != -1 ||
          result.indexOf("最大合模速度为零") != -1
        ) {
          if (result.indexOf("最大合模速度为空") != -1) {
            let index = result.indexOf("最大合模速度为空");
            table_data[index - 1].suggest = ejectorSuggest;
          } else {
            let index = result.indexOf("最大合模速度为零");
            table_data[index - 1].suggest = ejectorSuggest;
          }
        }
      }
      if (!machine_info.power_method) {
        let index = result.indexOf("动力方式为空");
        table_data[index - 1].suggest = "必填有效值";
      }
      if (result[0] == "转换机台的") {
        // 电动机转液压机,电动机没有计量压力,默认给液压机最大计量压力的75%
        if (machine_info.power_method == "液压机" || machine_info.power_method == "油压" || machine_info.power_method == "油电混" || machine_info.power_method == "电动/油压") {
          if (result.indexOf("最大计量压力为空") != -1 || result.indexOf("最大计量压力为零") != -1) {
            if (result.indexOf("最大计量压力为空") != -1) {
              let index = result.indexOf("最大计量压力为空");
              table_data[index - 1].suggest = "必填有效值(不为0)";
            } else {
              let index = result.indexOf("最大计量压力为零");
              table_data[index - 1].suggest = "必填有效值(不为0)";
            }
          }
        }
        // 转换机台最大注射行程不能为空,需要计算VP切换位置
        if (result.indexOf("最大注射行程为空") != -1 || result.indexOf("最大注射行程为零") != -1) {
          if (result.indexOf("最大注射行程为空") != -1) {
            let index = result.indexOf("最大注射行程为空");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          } else {
            let index = result.indexOf("最大注射行程为零");
            table_data[index - 1].suggest = "必填有效值(不为0)";
          }
        }
      }
      // 如果是液压机,必须提供最大注射压力(料管)和界面最大可设定压力(油压)
      if ((machine_info.power_method == "液压机" || machine_info.power_method == "油压" || machine_info.power_method == "油电混" || machine_info.power_method == "电动/油压") && machine_info.pressure_unit !="MPa"){
      
      }
      // 如果是液压机,必须有油缸面积计算压力系数,否则不能进行MPa的转换
      // if ((machine_info.power_method == "液压机" || machine_info.power_method == "油压" || machine_info.power_method == "油电混" || machine_info.power_method == "电动/油压") && machine_info.pressure_unit !="MPa"){
        // if (result.indexOf("油缸面积为空") != -1 || result.indexOf("油缸面积为零") != -1) {
        //   if (result.indexOf("油缸面积为空") != -1) {
        //     let index = result.indexOf("油缸面积为空");
        //     table_data[index - 1].suggest = "必填有效值(不为0)";
        //   } else {
        //     let index = result.indexOf("油缸面积为零");
        //     table_data[index - 1].suggest = "必填有效值(不为0)";
        //   }
        // }
        // if (result.indexOf("压力系数为空") != -1 || result.indexOf("压力系数为零") != -1) {
        //   if (result.indexOf("压力系数为空") != -1) {
        //     let index = result.indexOf("压力系数为空");
        //     table_data[index - 1].suggest = "必填有效值(不为0)";
        //   } else {
        //     let index = result.indexOf("压力系数为零");
        //     table_data[index - 1].suggest = "必填有效值(不为0)";
        //   }
        // }
      // }
    },
    judgmentRequired(mold_table_data, origin_table_data,transplant_table_data, adaption_table_data) {
      if (origin_table_data.length != 0 && transplant_table_data.length != 0 && mold_table_data.length != 0 && adaption_table_data.length != 0) {
        let sum = 0
        for (let i = 0; i < origin_table_data.length; i++) {
          if (origin_table_data[i].suggest.indexOf("必填")!=-1) {
            sum++
            break
          }
        }
  
        for (let i = 0; i < transplant_table_data.length; i++) {
          if (transplant_table_data[i].suggest.indexOf("必填")!=-1) {
            sum++
            break
          }
        }
        for (let i = 0; i < mold_table_data.length; i++) {
          if (mold_table_data[i].suggest.indexOf("必填")!=-1) {
            sum++
            break
          }
        }
  
        for (let i = 0; i < adaption_table_data.length; i++) {
          if (adaption_table_data[i].suggest.indexOf("不适用此模具")!=-1) {
            sum++
            break
          }
        }
        if (sum == 0) {
          this.isqualified = false
        } else {
          this.isqualified = true
        }
        this.$emit('transfer', this.isqualified)
      }
    },
    writeMachineData(machine) {
      let machine_info_id = null
      if (machine == "原始机台") {
        machine_info_id = this.origin_machine_info.id
      } else if (machine == "转换机台") {
        machine_info_id = this.transplant_machine_info.id
      }
      const routedata = this.$router.resolve({
        path:'/machine/injection/create',
        query:{
          id: machine_info_id
        }
      })
      window.open(routedata.href, "_blank")
    },
    writeMoldData(mold) {
      const routedata = this.$router.resolve({
        path:'/mold/create',
        query:{
          id: this.mold_info.id
        }
      })
      window.open(routedata.href, "_blank")
    },
    tableCellStyle({ row, column, rowIndex, columnIndex }) {
      let col
      if (row.suggest === '✔' && columnIndex === 2) {
        col = 'rgb(78, 201, 162)'
      } else if (row.suggest === '选填' && columnIndex === 2) {
        col = 'rgb(241, 159, 27)'
      } else if (row.suggest === '必填' && columnIndex === 2) {
        col = 'red'
      } else if (row.suggest === '完善必填参数' && columnIndex === 2) {
        col = 'red'
      } else if (row.suggest === '不适用此模具' && columnIndex === 2) {
        col = 'red'
      } else if (row.suggest === '注意' && columnIndex === 2) {
        col = 'rgb(241, 159, 27)'
      } 
      return { color: col }
    },
    checkAgain(){
      this.checkRequired(this.origin_machine_info,this.origin_result,this.originTableData)
      this.checkRequired(this.transplant_machine_info,this.transplant_result,this.transplantTableData)
      this.judgmentRequired(this.moldTableData, this.originTableData,this.transplantTableData,this.adaptionTableData)    
    } 
  },
  computed: {
    moldTableData() {
      let List = [];
      for (let i = 1; i < this.mold_result.length; i++) {
        if (this.mold_result[i] == "参数合格") {
          List.push({
            mold: "模具参数",
            parameter: "参数齐全",
            suggest: "✔",
          });
        } else if(this.checkMold){
          List.push({
            mold: "模具参数",
            parameter: this.mold_result[i],
            suggest: "必填",
          });
        } else {
          List.push({
            mold: "模具参数",
            parameter: this.mold_result[i],
            suggest: "不校验",
          });    
        }
      }
      return List;
    },
    originTableData() {
      let List = [];
      for (let i = 1; i < this.origin_result.length; i++) {
        if (this.origin_result[i] == "参数合格") {
          List.push({
            machine: "原始机台",
            parameter: "参数合格",
            suggest: "✔",
          });
        } else {
          List.push({
            machine: "原始机台",
            parameter: this.origin_result[i],
            suggest: "选填",
          });
        }
      }
      return List;
    },
    transplantTableData() {
      let List = [];
      for (let i = 1; i < this.transplant_result.length; i++) {
        // 以下和模具适配注塑机相关
        let moldRelatedItems = [
          "容模",
          "射台数",
          "锁模力",
          "注射量",
          "定位圈直径",
          "顶出",
          "开模行程",
          "喷嘴"
        ]
        let related = false
        for(let index=0;index<moldRelatedItems.length;index++){
          let moldRelated = moldRelatedItems[index]
          if(this.transplant_result[i].indexOf(moldRelated) > 0){
            related = true
          }
        }
        if(related){
          {
          // 如果与模具有关
          if(this.transplant_result[i].indexOf("注塑机") != -1 && this.checkMold){
            List.push({
              machine: "转换机台",
              parameter: this.transplant_result[i],
              suggest: "必填",
            });
          } else {
            List.push({
              machine: "转换机台",
              parameter: this.transplant_result[i],
              suggest: "不校验",
            });
          }
        } 
        }
        if(!related){
          // 如果与模具无关,与顶针开合模无关
          if (this.transplant_result[i] == "参数合格") {
            List.push({
              machine: "转换机台",
              parameter: "参数合格",
              suggest: "✔",
            });
          } else{
            if(this.transplant_result[i].indexOf("注塑机") != -1){
              List.push({
                machine: "转换机台",
                parameter: this.transplant_result[i],
                suggest: "必填",
              });
            } else {
              List.push({
                machine: "转换机台",
                parameter: this.transplant_result[i],
                suggest: "选填",
              });
            }
          }
        }
      }
      return List;
    },
    adaptionTableData() {
      let List = [];
      for (let i = 1; i < this.machine_adaption_result.length; i++) {
        if (this.machine_adaption_result[i] == "参数合格") {
          List.push({
            mold: "适配",
            parameter: "参数合格",
            suggest: "✔",
          });
        } else if (this.machine_adaption_result[i].indexOf("参数不全")!=-1 && this.checkMold) {
          List.push({
            mold: "适配",
            parameter: this.machine_adaption_result[i],
            suggest: "完善必填参数",
          });
        }else if (this.machine_adaption_result[i].indexOf("参数不全")!=-1 && !this.checkMold) {
          List.push({
            mold: "适配",
            parameter: this.machine_adaption_result[i],
            suggest: "不校验",
          });
        }else if (this.machine_adaption_result[i].indexOf("注意")!=-1) {
          List.push({
            mold: "适配",
            parameter: this.machine_adaption_result[i],
            suggest: "注意",
          });
        } else {
          List.push({
            mold: "适配",
            parameter: this.machine_adaption_result[i],
            suggest: "不适用此模具",
          });
        }
      }
      return List;
    },
  },
  watch: {
    originResult: function () {
      this.origin_result = this.originResult;
    },
    transplantResult: function () {
      this.transplant_result = this.transplantResult;
    },
    moldResult: function () {
      this.mold_result = this.moldResult;
    },
    machineAdaptionResult: function () {
      this.machine_adaption_result = this.machineAdaptionResult;
    },

    originMachineInfo: {
      handler() {
        this.origin_machine_info = this.originMachineInfo;
        this.checkRequired(this.origin_machine_info,this.origin_result,this.originTableData)
      },
      deep: true,
      immediate: true,
    },
    transplantMachineInfo: {
      handler() {
        this.transplant_machine_info = this.transplantMachineInfo;
        this.checkRequired(this.transplant_machine_info,this.transplant_result,this.transplantTableData)
      },
      deep: true,
      immediate: true,
    },
    sum: {
      handler() {
        this.a = this.sum
        this.checkAgain()
      },
      deep: true,
      immediate: true,
    },
    checkEjector: {
      handler() {
        this.checkAgain()
      },
      deep: true,
      immediate: true,
    },
  },
};
</script>

<style>
</style>