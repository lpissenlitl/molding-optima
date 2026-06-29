<template>
  <div>
    <el-form         
      ref="form"
      :inline="true"
      size="mini"
      label-width="4.5rem"
    >
      <el-form-item label="制品类别">
        <el-autocomplete 
          v-model="product_type"
          :fetch-suggestions="queryMethodProductType"
          clearable
          placeholder="请点击选择制品"
          style="width: 10rem"
          :debounce="0"
        >
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="塑料简称">
        <el-autocomplete 
          v-model="polys_abbreviation"
          :fetch-suggestions="queryMethodPolymerAbbreviation"
          clearable
          placeholder="请点击选择塑料"
          style="width: 9rem"
          :debounce="0"
        >
        </el-autocomplete>
      </el-form-item>
      <el-button
        type="danger"
        size="mini"
        @click="resetToBase()"
        style="width: 8rem;margin-right: 10px"
      >
        重置到基本规则库
      </el-button>
    </el-form>
    <el-steps ref="steps" :active="form_info.active" finish-status="success">
      <el-step v-for="(step, index) in stepsList" :key="index" :title="step"></el-step>
    </el-steps>

    <el-form ref="form" :inline="true" size="mini" label-width="3rem">
      <el-form-item label="缺陷">
        <el-input size="mini" v-model="item.defect_name" style="width:6rem"></el-input>
      </el-form-item>
      <rule-flow-detail
        ref="subRule"
        :rule-flow="ruleFlowData"
        :current-defect="currentDefect"
        @change-flow="setRuleFlow"
        :active-collapse="['1']"
        :is-show="false"
      >
      </rule-flow-detail>
      <div style="text-align: center">          
        <el-button
          @click="previousStep"
          style="width: 8rem"
          size="small"
          type="primary"
          v-if="item.defect_name != '短射'"
          :loading="loading"
        >
          上一步
        </el-button>   
        <el-button
          @click="nextStep"
          style="width: 8rem"
          size="small"
          type="primary"
          v-if="item.defect_name != lastLabel"
          :loading="loading"
        >
          下一步
        </el-button>
        <el-button
          @click="finishSubRule"
          style="width: 8rem"
          size="small"
          type="primary"
          v-else
          :loading="loading"
        >
          完成
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script>
import ruleFlowDetail from "@/components/flowGraph/ruleFlowDetail.vue";
import { getRuleFlowMethod, setRuleFlowMethod, getOptions } from "@/api";
import { datetimeTodayStr } from '@/utils/datetime';
import {defects_const, getLastLabel} from "@/utils/process_const";

export default {
  name: "RuleSubruleDetail",
  components: { ruleFlowDetail },
  props: {
  },
  data() {
    return {
      stepsList:defects_const.map(defect => defect.label),
      product_type:null,
      polys_abbreviation:null,
      form_info: {
        active: 0,
      },
      ruleFlowData: {
        rule_library: null,
        rule_type: null,
        product_small_type: null,
        polymer_abbreviation: null,
        enable: null,
        defect_data: [
          {
            defect_name: null,
            defect_desc: null,
            graph_data: {},
            rule_method: {
              total_pre_num: null,
              total_solution_num: null,
              sub_solution_num_list: [],
              solution_ways: [],
              preconditions: [
                {
                  conditiontype: null,
                  keyword: null,
                  describe: null,
                  status: null,
                  solutions: [
                    {
                      conditiontype: null,
                      keyword: null,
                      describe: null,
                      action: null,
                      action_key: null,
                    },
                  ],
                },
              ],
            },
          },
        ],
      },
      currentDefect:0,
      rule_no: null,
      loading: false,
      item:{
        defect_name: null,
        defect_desc: null,
        graph_data: {},
        rule_method: {
          total_pre_num: null,
          total_solution_num: null,
          sub_solution_num_list: [],
          solution_ways: [],
          preconditions: [
            {
              conditiontype: null,
              keyword: null,
              describe: null,
              status: null,
              solutions: [
                {
                  conditiontype: null,
                  keyword: null,
                  describe: null,
                  action: null,
                  action_key: null,
                }
              ]
            }
          ],
        }
      },
      lastLabel: getLastLabel(defects_const),
      defectOptions: defects_const
    };
  },
  mounted() {
    getOptions("defect_list", []).then(res=>{
      this.defectOptions = res.data
      this.stepsList = this.defectOptions.map(defect => defect.label)
      this.lastLabel = getLastLabel(this.defectOptions)
    })   
    this.reset()
  },
  methods: {
    resetToBase(){
      this.$confirm(`确定要重置到基础规则库么？页面上的修改将丢失`, '重置', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }).then(() => {
        this.reset()
        this.form_info.active = 0;
        this.currentDefect = 0;
        this.item = this.ruleFlowData.defect_data[this.currentDefect]
      })
    },
    reset(){
      getRuleFlowMethod({"rule_type":"基础库"}).then(res => {
      if (res.status === 0) {
        if(JSON.stringify(res.data) != "{}"){
          this.ruleFlowData = res.data
          this.item = this.ruleFlowData.defect_data[0]
        }
      }
    })
    },
    queryMethodProductType(str, cb) {
      str = str == null ? "" : str
      let promptList = []
      getOptions("product_small_type", {"form_input": str, "db_table": "rule_method" })
      .then(res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; i++) {
            promptList.push({value: res.data[i]})
          }
        }
      })
      cb(promptList)
    },
    queryMethodPolymerAbbreviation(str, cb) {
      str = str == null ? "" : str
      let promptList = []
      getOptions("polymer_abbreviation", {"form_input": str, "db_table": "polymer" })
      .then(res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; i++) {
            promptList.push({value: res.data[i].value})
          }
        }
      })
      cb(promptList)
    },
    nextStep() {
      // 先做验证,不能为空
      // 如果一整条都为空, 那么直接删除.
      // {'defect_data': {0: {'graph_data': {'nodes': {24: {'text': ['Not a valid string.']}}}}}}
      let is_valid = true
      let defect_data = this.ruleFlowData.defect_data[this.currentDefect]
      let preconditions = defect_data.rule_method.preconditions
      for(let i=0;i<preconditions.length;i++){
        if(preconditions[i].keyword == null){
          is_valid = false
          this.$message({
            type: 'warning',
            message: '有工况为空,请填上或删除这条规则!'
          }) 
          return
        }
        if(preconditions[i].status == null){
          is_valid = false
          this.$message({
            type: 'warning',
            message: '有状态为空,请填上或删除这条规则!'
          }) 
          return
        }
        let solutions = preconditions[i].solutions
        for(let j=0;j<solutions.length;j++){
          if(solutions[j].keyword == null){
            is_valid = false
            this.$message({
              type: 'warning',
              message: '有调整为空,请填上或删除这条规则!'
            }) 
            return
          }
          if(solutions[j].action == null){
            is_valid = false
            this.$message({
              type: 'warning',
              message: '有参数为空,请填上或删除这条规则!'
            }) 
            return
          }   
        }
      }
      if(is_valid){
        this.form_info.active++;
        this.$refs.subRule.generateGraphData()
        if(this.currentDefect++>this.defectOptions.length) this.currentDefect = 0;
        this.item = this.ruleFlowData.defect_data[this.currentDefect]
      }
    },
    previousStep(){
      this.form_info.active--;
      this.currentDefect--;
        this.item = this.ruleFlowData.defect_data[this.currentDefect]
    },
    setRuleFlow(rule_flow) {
      this.ruleFlowData = rule_flow
    },
    saveRuleFlow() {
      this.loading = true
      if(this.ruleFlowData.rule_library=="基础库"){
        this.ruleFlowData.enable = 1
        this.ruleFlowData.product_small_type = this.product_type
        this.ruleFlowData.polymer_abbreviation = this.polys_abbreviation
        this.ruleFlowData.rule_type = "子规则库"
        this.ruleFlowData.rule_library = "R" + datetimeTodayStr()
      }
      setRuleFlowMethod(this.ruleFlowData).then(res => {
        this.$message({
          type: 'success',
          message: '成功新增子规则!'
        })
      })
      .finally(() => {
        this.loading = false
      })
    },
    finishSubRule(){
      if(!this.product_type){
        this.$message({
          type: 'warning',
          message: '请填写制品类别!'
        })    
      }
      else{
        this.$refs.subRule.generateGraphData()
        this.saveRuleFlow()
        this.$emit('close-dialog', this.ruleFlowData)
      }
    }
  },
  watch:{
  }
};
</script>

<style lang="scss" scoped>

</style>>