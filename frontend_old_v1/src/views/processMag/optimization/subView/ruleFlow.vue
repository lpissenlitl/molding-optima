<template>
  <div>
    <div style="height: 20px"></div>
    <div style="float: left">
      <div slot="header" class="clearfix">
        <span>基础规则库</span>
      </div>
      <div style="height: 30px"></div>
      <el-form ref="form" :inline="true" size="mini" label-width="3rem">
        <el-form-item label="缺陷">
          <el-select v-model="flaw" prop="flaw" style="width:8rem" @change="handleDefect">
            <el-option
              v-for="(option, index) in defectOptions"
              :key="index"
              :label="option.label"
              :value="option.label"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item style="text-align: center">
          <el-button
            type="primary"
            size="mini"
            @click="newDefect"
            style="width: 8rem"
          >
            新增缺陷
          </el-button>
        </el-form-item>
        <el-form-item style="text-align: center">
          <el-button
            type="primary"
            size="mini"
            @click="checkRuleDetail"
            style="width: 8rem"
          >
            查看详细规则
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="mini"
            @click="addSubruleRule"
            style="width: 8rem"
          >
            新建子规则库
          </el-button>
        </el-form-item>
        <rule-flow-detail
          :rule-flow="ruleFlowData"
          :current-defect="currentDefect"
          @change-rule-flow="setGraphData"
          :is-show="true"
          :is-defect="flaw"
        >
        </rule-flow-detail>
      </el-form>
      <div style="height: 12px"></div>
      <rule-flow :graph-data-parent="graphData"></rule-flow>
    </div>
    <div style="float: right">
      <div slot="header" class="clearfix">
        <span>子规则库</span>
      </div>
      <div style="height: 30px"></div>
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
            @select="findSubRule"
            clearable
            :debounce="0"
            placeholder="点击选择制品"
            style="width: 8rem"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="塑料简称">
          <el-autocomplete 
            v-model="polys_abbreviation"
            :fetch-suggestions="queryMethodPolymerAbbreviation"
            clearable
            placeholder="点击选择塑料"
            style="width: 9rem"
            :debounce="0"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="编号">
          <el-autocomplete
            v-model="subrule_no" 
            style="width:10rem"
            placeholder="子规则库编号"
            suffix-icon="el-icon-search"
            clearable
            :fetch-suggestions="querySubRuleNoList"
            @select="handleSubruleNo"
            :trigger-on-focus="true"
          > 
          </el-autocomplete>
        </el-form-item>
        <el-button
          type="danger"
          size="mini"
          @click="reset"
          style="width: 8rem;margin-right: 10px"
        >
          重置
        </el-button>

        <el-divider />
        <el-form-item label="缺陷">
          <el-select 
            v-model="defect" 
            prop="defect" 
            style="width:10rem" 
            @change="handleSubDefect"
          >
            <el-option
              v-for="(option, index) in subDefectOptions"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item style="text-align: center" v-if="subrule_no">
          <el-button
            type="primary"
            size="mini"
            @click="checkDetail"
            style="width: 8rem"
          >
            查看详细规则
          </el-button>
          <el-button
            type="danger"
            size="mini"
            @click="deleteRule"
            style="width: 8rem"
          >
            删除该子规则
          </el-button>       
        </el-form-item>
      </el-form>
      <rule-flow-detail 
        :rule-flow="subruleFormData"          
        :current-defect="currentSubDefect"
        @change-rule-flow="setSubruleGraphData"
        :is-show="true"
        :active-collapse="active_collapse"
        :is-defect="defect"
      ></rule-flow-detail>
      <div style="height: 12px"></div>
      <rule-flow 
        :graph-data-parent="subruleData"
      ></rule-flow>
    </div>
    <el-dialog
      title="子规则"
      :visible.sync="showSubrule"
      width="75%"
      @closeDialog="closeSubruleDialog"
    >
      <rule-subrule-detail
        @close-dialog="closeSubruleDialog"
      >
      </rule-subrule-detail>
    </el-dialog>
    <el-dialog
      title="新增缺陷"
      :visible.sync="showNewDefect"
      width="50%"
      @closeDialog="showNewDefect=false"
    >
      <el-form 
        ref="newDefect" 
        :model="defectInfo" 
        :inline="true" 
        size="mini" 
        label-width="8rem" 
        :rules="rules"
      >
        <el-tooltip class="item" effect="dark" content="请输入新缺陷的中文名称,一般是两个字" placement="top-start">
          <el-form-item label="缺陷名称(中文)" prop="new_defect_name">
            <el-input v-model="defectInfo.new_defect_name"></el-input>
          </el-form-item>
        </el-tooltip>
        <el-tooltip class="item" effect="dark" content="请输入新缺陷的英文名称,全部大写,没有特殊字符,包括_-等连接线" placement="top-start">
          <el-form-item label="缺陷英文(大写)" prop="new_defect_desc">
            <el-input v-model="defectInfo.new_defect_desc"></el-input>
          </el-form-item>
        </el-tooltip>
        <el-form-item label="参考缺陷" prop="refer_defect">
          <el-select v-model="defectInfo.refer_defect" prop="refer_defect" style="width:8rem">
            <el-option
              v-for="(option, index) in defectOptions"
              :key="index"
              :label="option.label"
              :value="option.label"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <div style="text-align: center; margin-top: 1rem;">
          <el-form-item>
            <el-button
              type="primary"
              size="mini"
              @click="addNewDefect"
              style="width: 8rem"
            >
              确认新增
            </el-button>
          </el-form-item> 
        </div>
      </el-form>
    </el-dialog>
  </div>
</template>

<script>
import ruleFlow from "@/components/flowGraph";
import ruleFlowDetail from "@/components/flowGraph/ruleFlowDetail.vue";
import { getRuleFlowMethod, setRuleFlowMethod, getOptions, deleteRule, newDefectMethod } from "@/api";
import RuleSubruleDetail from './ruleSubruleDetail.vue';
import {defects_const} from "@/utils/process_const";

export default {
  components: { ruleFlow, ruleFlowDetail, RuleSubruleDetail },
  data() {
    return {
      graphData: {},
      subruleData: {},
      flaw: "短射",
      product_type: null,
      polys_abbreviation: null,
      subrule_no: null,
      ruleFlowData: {
        rule_library: "基础库",
        rule_type: "基础库",
        product_small_type: null,
        polymer_abbreviation: null,
        enable: 1,
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
                    }
                  ]
                }
              ],
            }
          }
        ]
      },
      subruleFormData: {
        rule_library:null,
        rule_type:null,
        product_small_type:null,
        polymer_abbreviation:null,
        enable:null,
        defect_data:[
          {
            defect_name:null,
            defect_desc:null,
            graph_data:{},
            rule_method:{
              total_pre_num : null,
              total_solution_num : null,
              sub_solution_num_list:[],
              solution_ways:[],
              preconditions: [
                {
                  conditiontype: null,
                  keyword: null,
                  describe: null,
                  status:null,
                  solutions: [
                    {
                      conditiontype: null,
                      keyword: null,
                      describe: null,
                      action: null,
                      action_key:null,
                    }
                  ]
                }
              ],
            },
          },
        ],
      },
      currentDefect: 0,
      currentSubDefect: 0,
      defect:null,
      defectOptions:defects_const,
      subDefectOptions:[],  // 根据子规则库自动生成
      showSubrule: false,
      active_collapse: [],
      showNewDefect: false,
      defectInfo:{
        new_defect_name:null,  // 中文
        new_defect_desc:null,  // 大写字母
        refer_defect:"短射",
      },
      rules: {
        new_defect_desc: [
          { required: true, message: '缺陷英文不能为空！' }
        ],
        new_defect_name: [
          { required: true, message: '缺陷名称不能为空！' }
        ]
      },
    };
  },
  methods: {},
  mounted() {
    getOptions("defect_list", []).then(res=>{
      this.defectOptions = res.data
    })
    this.getRuleFlow();
  },
  methods: {
    isUpperCase(str) {
      // 正则表达式匹配全大写字母
      return /^[A-Z]+$/.test(str);
    },
    checkDesc(){
      if(!this.isUpperCase(this.defectInfo.new_defect_desc)){
        this.$message({message:"请检查缺陷英文是否全部大写字母,并且没有特殊符号", type: 'warning'})
        return false
      }
      const existingDescs = this.defectOptions.map(item => item.desc);
      if(existingDescs.includes(this.defectInfo.new_defect_desc)){
        this.$message({message:"请检查缺陷英文与已有缺陷英文重复", type: 'warning'})
        return false
      }
      const existingLabel = this.defectOptions.map(item => item.label);
      if(existingLabel.includes(this.defectInfo.new_defect_name)){
        this.$message({message:"请检查缺陷名称与已有缺陷名称重复", type: 'warning'})
        return false
      }
      return true
    },
    addNewDefect(){
      this.$refs.newDefect.validate((valid) => {
        if (valid) {
          // 做校验,检查是否合格:不能重复,没有特殊字符,都是大写
          let result = this.checkDesc()
          if(result){    
            let rule_keyword = {
              name: this.defectInfo.new_defect_desc,
              comment: this.defectInfo.new_defect_name,
              level:3,
              all_range_min: 0,
              all_range_max: 1,
              action_max_val: -1,
              keyword_type: "缺陷",
              deleted: 0,
              rule_type: "基础库",
              show_on_page: 1      
            }
            if(this.defectOptions.length<=49){
              // 以目前预留id,可以再增加33个,id最大=400,如果超过33个了,那么使用数据auto increment
              rule_keyword["id"] = 351 + this.defectOptions.length
            }
            newDefectMethod({
              rule_keyword: rule_keyword,
              refer_defect: this.defectInfo.refer_defect,
              previous_length: this.defectOptions.length
            }).then(res=>{
              this.$message({message:"新增缺陷成功", type: 'success'})
              getOptions("defect_list", []).then(res=>{
                this.defectOptions = res.data
              })
              this.getRuleFlow();
            })
            this.showNewDefect = false
          }
        }
      })
    },
    newDefect(){
      this.showNewDefect = true
    },
    deleteRule(){
      deleteRule(this.subrule_no).then(res => {
        this.$message({message:"成功删除子规则库"+this.subrule_no+"!", type: 'success'})
      })
    },
    queryOptions(str, column) {
      str = str == null ? "" : str 
      let promptList = []
      if (column) {
        getOptions(column, { "form_input": str, "db_table": "rule_flow", "product_small_type": this.product_type, "polymer_abbreviation": this.polys_abbreviation })
        .then( res => {
          if(res.status == 0) {
            for(let i = 0; i < res.data.length; i++) {
              promptList.push({ value: res.data[i] })
            }
          }
        })
      } 
      return promptList
    },
    querySubRuleNoList(str, cb){
      let results = this.queryOptions(str, "rule_library")
      cb(results)
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
    findSubRule(){
      // 选择制品类别后,去数据库查找,把找到的最新的一条子规则的塑料和编号,填上去,并且显示对应流程图
      let result = this.queryOptions("", "rule_library")
      setTimeout(() => {
        if(result && result.length>0){
          this.subrule_no = result[0].value
          this.handleSubruleNo()
        }
      },700)
    },
    getRuleFlow() {
      getRuleFlowMethod().then((res) => {
        if (
          res.status == 0 &&
          JSON.stringify(res.data) != "{}" &&
          res.data.defect_data
        ) {
          this.ruleFlowData = res.data;
          this.graphData.nodes = res.data.defect_data[0].graph_data.nodes;
          this.graphData.edges = res.data.defect_data[0].graph_data.edges;
          this.$set(this.graphData);
        }
      });
    },
    handleDefect(val) {
      // 根据当前的缺陷,展示相应的缺陷流程
      let defect_name = null
      let defect_desc = null
      const index = this.defectOptions.findIndex(option => option.label === val);
      defect_name = this.defectOptions[index].label
      defect_desc = this.defectOptions[index].desc  

      this.handleRuleFlow(defect_name, defect_desc)
      // 子规则库也同时显示相应的缺陷
      if(this.subrule_no){
        this.defect = String(defect_name)
        this.handleSubRuleFlow(defect_name, defect_desc)
      }
    },
    handleRuleFlow(defect_name, defect_desc){
      let current_defect = null
      for(let i = 0;i <this.ruleFlowData.defect_data.length;i++){
        if(defect_name == this.ruleFlowData.defect_data[i].defect_name){
          current_defect = i
        }
      }
      if (current_defect != null) {
        this.currentDefect = current_defect;
        this.graphData = {};
        this.graphData.nodes =
          this.ruleFlowData.defect_data[current_defect].graph_data.nodes;
        this.graphData.edges =
          this.ruleFlowData.defect_data[current_defect].graph_data.edges;
        this.$set(this.graphData);
      } else {
        let defect_data = {
          defect_name: defect_name,
          defect_desc: defect_desc,
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
                solutions: [
                  {
                    conditiontype: null,
                    keyword: null,
                    describe: null,
                    action: null,
                    action_key:null,
                  },
                ],
              },
            ],
          },
        };
        this.currentDefect = this.ruleFlowData.defect_data.length;
        this.ruleFlowData.defect_data.push(defect_data);
        this.graphData = {};
      }
    },
    handleSubRuleFlow(defect_name, defect_desc){
      let current_sub_defect = null
      for(let i = 0;i <this.subruleFormData.defect_data.length;i++){
        if(defect_name == this.subruleFormData.defect_data[i].defect_name){
          current_sub_defect = i
        }
      }
      if (current_sub_defect != null) {
        this.currentSubDefect = current_sub_defect;
        this.subruleData = {};
        this.subruleData.nodes =
          this.subruleFormData.defect_data[current_sub_defect].graph_data.nodes;
        this.subruleData.edges =
          this.subruleFormData.defect_data[current_sub_defect].graph_data.edges;
        this.$set(this.subruleData);
      } else {
        let current_option = this.subDefectOptions.length
        this.subDefectOptions.push(
          {label: defect_name, value: current_option, desc: defect_desc}
        )
        this.defect = String(defect_name)
        let defect_data = {
          defect_name: defect_name,
          defect_desc: defect_desc,
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
                solutions: [
                  {
                    conditiontype: null,
                    keyword: null,
                    describe: null,
                    action: null,
                    action_key:null,
                  },
                ],
              },
            ],
          },
        };
        this.currentSubDefect = this.subruleFormData.defect_data.length;
        this.subruleFormData.defect_data.push(defect_data);
        this.subruleData = {};
      }
    }, 
    handleSubDefect(val){
      // 根据当前的缺陷,展示相应的缺陷流程
      let defect_name = null
      let defect_desc = null
      for(let i = 0;i <this.subDefectOptions.length;i++){
        if(val == this.subDefectOptions[i].value){
          defect_name = this.subDefectOptions[i].label
          defect_desc = this.subDefectOptions[i].desc
        }
      }
      // 同步基本规则库的缺陷下拉框
      this.flaw = defect_name
      // 基本规则库和子规则库都显示相应缺陷
      this.handleRuleFlow(defect_name, defect_desc)
      this.handleSubRuleFlow(defect_name, defect_desc)
    },
    handleSubruleNo() {
      getRuleFlowMethod({ rule_library: this.subrule_no }).then((res) => {
        if (
          res.status == 0 &&
          JSON.stringify(res.data) != "{}" &&
          res.data.defect_data
        ) {
          this.subruleData.nodes = res.data.defect_data[0].graph_data.nodes;
          this.subruleData.edges = res.data.defect_data[0].graph_data.edges;
          this.subruleFormData = res.data
          this.polys_abbreviation = res.data.polymer_abbreviation
          this.product_type = res.data.product_small_type
          this.setSubDefectOptions()
          this.$set(this.subruleData);
          this.defect = "0"
          this.handleSubDefect("0")
        }
      });
    },
    changeSwitch() {
      setRuleFlowMethod(this.subruleFormData).then(res => {
        if (res.status === 0) {
          this.$message({message:"激活状态修改成功!", type: 'success'})
        }
      })
    },
    setSubDefectOptions(){
      this.subDefectOptions = []
      for(let i=0;i<this.subruleFormData.defect_data.length;i++){
        this.subDefectOptions.push({
          label: this.subruleFormData.defect_data[i].defect_name, value: String(i), desc: this.subruleFormData.defect_data[i].defect_desc
        })
      }
    },
    setGraphData(rule_flow){
      this.graphData = rule_flow.defect_data[this.currentDefect].graph_data
      this.$set(this.graphData);
      // 保存到mongo数据库
      setRuleFlowMethod(rule_flow).then(res =>{
        this.$message({
          type: 'success',
          message: '流程图修改成功!'
        });
      })
    },
    setSubruleGraphData(rule_flow) {
      this.subruleData = rule_flow.defect_data[this.currentSubDefect].graph_data
      this.$set(this.subruleData);
      // 保存到mongo数据库
      setRuleFlowMethod(rule_flow).then(res =>{
        this.$message({
          type: 'success',
          message: '流程图修改成功!'
        });
      })
    },
    checkDetail(){
      this.$router.push({
        path: '/process/optimize/rule',
        query: {
          rule_type: '子规则库',
          subrule_no: this.subrule_no,
          product_type: this.product_type,
          polys_abbreviation: this.polys_abbreviation
        }  
      })
    },
    checkRuleDetail() {
      this.$router.push({
        path: '/process/optimize/rule',
        query: {
          rule_type: '基础库',
        }  
      })
    },
    addSubruleRule() {
      // 先判断基础库中是否包含了所有缺陷,如果没有,跳转到基础库中增加
      // 按顺序增加
      if(this.ruleFlowData.defect_data.length<12){
        this.$message({
          type: 'warning',
          message: '先到基础规则库中增加所有缺陷的流程图!'
        })
      } else {
        this.showSubrule = true
      }
    },
    closeSubruleDialog(rule_flow) {
      this.subruleFormData = rule_flow
      this.currentSubDefect = 0
      this.showSubrule = false
      // 把刚才新加的子规则库显示在右边
      this.subrule_no = rule_flow.rule_library
      this.defect = '短射'
      this.handleSubruleNo()
    },
    reset() {
      this.product_type = null
      this.polys_abbreviation = null
      this.subrule_no = null
      this.subruleData = {}
      this.defect = null,
      this.subruleFormData = {
        rule_library:null,
        rule_type:null,
        product_small_type:null,
        polymer_abbreviation:null,
        enable:null,
        defect_data:[
          {
            defect_name:null,
            defect_desc:null,
            graph_data:{},
            rule_method:{
              total_pre_num : null,
              total_solution_num : null,
              sub_solution_num_list:[],
              solution_ways:[],
              preconditions: [
                {
                  conditiontype: null,
                  keyword: null,
                  describe: null,
                  status:null,
                  solutions: [
                    {
                      conditiontype: null,
                      keyword: null,
                      describe: null,
                      action: null,
                      action_key:null,
                    }
                  ]
                }
              ],
            },
          },
        ],
      }
      this.active_collapse = []
    }
  },
  watch: {},
};
</script>

<style scoped lang="scss">

</style>
