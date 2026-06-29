<template>
  <div>
    <el-form 
      ref="methodForm" 
      label-width="6rem"
      size="small" 
      :inline="true"
    >
      <el-form-item 
        label="子规则库编号" 
        prop="subrule_no"
      >
        <el-autocomplete 
          v-model="rule_method.subrule_no"
          :fetch-suggestions="querySubRuleNoList"
          @select="setSubruleNo"
          placeholder="请输入内容"
          clearable
          :debounce="0"
        >
        </el-autocomplete>
      </el-form-item>
      <el-form-item label="制品类别" prop="product_small_type">
        <el-autocomplete 
          v-model="rule_method.product_small_type"
          :fetch-suggestions="queryMethodProductType"
          placeholder="请输入内容"
          :debounce="0"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="塑料简称" prop="polymer_abbreviation">
        <el-autocomplete 
          v-model="rule_method.polymer_abbreviation"
          :fetch-suggestions="queryMethodPolymerAbbreviation"
          placeholder="请输入内容"
          :debounce="0"
        >
        </el-autocomplete>
      </el-form-item>

      <h3>条件部分</h3>
      
      <div 
        v-for="(item, idx) in rule_method.preconditions" 
        :key="idx"
      >
        <el-tooltip class="item" effect="dark" content="前置条件类型" placement="top">
          <el-form-item label="条件类型" prop="conditiontype">
            <el-select 
              v-model="item.conditiontype"
              style="width: 8rem"
              @change="resetRowValue(item, 'precondition')"
            >
              <el-option label="普通前置条件" value="普通前置条件"></el-option>
              <el-option label="缺陷前置条件" value="缺陷前置条件"></el-option>
            </el-select>
          </el-form-item>
        </el-tooltip>

        <el-form-item label="关键字">
          <el-select 
            v-if="item.conditiontype==='普通前置条件'" 
            v-model="item.keyword" 
            prop="keyword"
            style="width: 8rem"
          >
            <el-option 
              v-for="option, index in normalKeywordOptions"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>
          <el-select 
            v-else-if="item.conditiontype==='缺陷前置条件'" 
            v-model="item.keyword" 
            prop="keyword"
            style="width: 8rem"
          >
            <el-option 
              v-for="option, index in defectKeywordOptions"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>

          <el-select 
            v-else 
            v-model="item.keyword" 
            prop="keyword"
            style="width: 8rem"
          >
          </el-select>
        </el-form-item>

        <el-form-item label="描述">
          <el-select 
            v-model="item.describe" 
            prop="describe"
            style="width: 8rem"
          >
            <template v-if="item.conditiontype === '普通前置条件'">
              <el-option
                v-for="key, value in paraLevelMap"
                :key="value"
                :label="key"
                :value="value"
              ></el-option>
            </template>
            <template v-if="item.conditiontype === '缺陷前置条件'">
              <el-option
                v-for="key, value in defectLevelMap"
                :key="value"
                :label="key"
                :value="value"
              ></el-option>
            </template>
          </el-select>
        </el-form-item>

        <el-button 
          v-if=" idx > 0 || rule_method.preconditions.length > 1"
          type="danger"
          circle 
          icon="el-icon-minus" 
          size="small" 
          @click="subPrecondition(idx)" 
        ></el-button>
        
        <el-button 
          v-if=" idx === rule_method.preconditions.length - 1"
          circle 
          type="success"
          icon="el-icon-plus"
          size="small" 
          @click="addPrecondition()"
        ></el-button>
      </div>
    </el-form>

    <el-form 
      ref="form" 
      label-width="5rem" 
      size="small"
      :inline="true"
    >
      <h3>结论部分</h3>

      <div 
        v-for="(item, idx) in rule_method.solutions" 
        :key="idx"
      >
        <el-form-item label="条件类型">
          <el-select 
            v-model="item.conditiontype" 
            prop="conditiontype"
            style="width: 8rem" 
          >
            <el-option label="结论条件" value="结论条件"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="关键字">
          <el-select 
            v-model="item.keyword" 
            prop="keyword"
            style="width: 8rem"
            @change="concludeChange"
          >
            <el-option 
              v-for="option, index in concludeKeywordOptions"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="动作">
          <el-select 
            v-model="item.action" 
            prop="action"
            style="width: 8rem"
            @change="concludeChange"
          >
            <template v-if="item.conditiontype === '结论条件'">
              <el-option
                v-for="key, value in actionMap"
                :key="value"
                :label="key"
                :value="value"
              ></el-option>
            </template>
          </el-select>
        </el-form-item>
        <el-form-item label="描述" v-if="item.action!='adjust'">
          <el-tooltip
            effect="dark"
            content="请输入0-100以内的小数"
            placement="right-end"
          >
            <el-input 
              v-model="item.describe" 
              style="width:15rem"
              placeholder="请输入0-100以内的小数" 
            ></el-input>
          </el-tooltip>
        </el-form-item>
        <el-form-item label="描述" v-else>
          <el-input 
            style="width:15rem"
            v-model="item.describe" 
          ></el-input>
        </el-form-item>

        <el-button 
          v-if=" idx > 0 || rule_method.solutions.length > 1"
          circle 
          type="danger"
          icon="el-icon-minus" 
          size="small"
          @click="subSolution(idx)" 
        ></el-button>
        
        <el-button 
          v-if=" idx === rule_method.solutions.length - 1"
          circle 
          type="success"
          icon="el-icon-plus"
          size="small"
          @click="addSolution()"
        ></el-button>
      </div>
    </el-form>

    <hr />

    <div style="text-align: center">
      <el-button 
        type="primary"
        size="small" 
        @click="generateRule" 
        style="width: 8rem"
      >
        生成规则
      </el-button>
    </div>

    <div style="height: 10px" />

    <el-form 
      label-width="5rem" 
      :inline="false"
    >
      <el-form-item label="规则描述" prop="rule_description">
        <el-input 
          type="textarea" 
          :readonly="true"
          v-model="rule_method.rule_description" 
          rows="4" 
          placeholder="请输入内容" 
        ></el-input>
      </el-form-item>

      <br />

      <el-form-item label="规则解释" prop="rule_explanation">
        <el-input 
          type="textarea" 
          :readonly="true"
          v-model="rule_method.rule_explanation" 
          rows="4" 
          placeholder="请输入内容"
        ></el-input>
      </el-form-item>
    </el-form>

    <div style="text-align: center">
      <el-button 
        size="small"
        type="danger"
        @click="cancel"
        style="width: 6rem"
      >
        取 消
      </el-button>
      <el-button 
        v-if="!ruleMethodId"
        size="small" 
        type="primary"
        @click="addRuleMethod" 
        style="width: 6rem"
      >
        添 加
      </el-button>

      <el-button 
        v-if="ruleMethodId" 
        size="small"
        type="primary" 
        @click="updateRuleMethod" 
        style="width: 6rem"
      >
        更 新
      </el-button>
    </div>
  </div>
</template>

<script>
import { ruleDetailMethod, ruleKeywordMethod, getOptions, getRuleFlowMethod } from "@/api"

export default ({
  name: "RuleMethodDetail",
  props: {
    ruleMethod: {
      type: Object,
      default: () => ({
        product_small_type: null,
        polymer_abbreviation: null,
        preconditions: [],
        solutions: [],
        rule_description: null,
        rule_explanation: null
      })
    },
    ruleMethodId: {
      type: Number,
      default: null
    },
    ruleType: {
      type: String,
      default: null
    },
    subruleNo: {
      type: String,
      default: null
    } 
  },
  data() {
    return {
      rule_method: this.ruleMethod,
      normalKeywordOptions: [
        { label: "IP0", value: "IP0" },
        { label: "IP1", value: "IP1" }
      ],
      keywordMap: {},
      paraLevelMap: { low: "偏低", 
      // mid: "适当", 
      high: "偏高", worse:"不合理" },
      defectLevelMap: { low: "轻微", mid: "中等", high: "严重" },
      actionMap: {  add: "增加" , reduce: "减小", adjust:"弹窗"},
      defectKeywordOptions: [
        { label: "IP0", value: "IP0" },
        { label: "IP1", value: "IP1" }
      ],
      concludeKeywordOptions: [
        { label: "IP0", value: "IP0" },
        { label: "IP1", value: "IP1" }
      ],
      concludeDescribe: new Map([
          ["CLAMP", "锁模力"],
          ["CUSION", "残留量"],
          ["NT", "喷嘴温度"],
          ["IPOS", "注射位置"],
          ["ET", "下料口温度"]
      ]),
      defect_name: null,
      defect_desc: null,
    }
  },
  created() {
    this.initView()
  },
  methods: {
    setSubruleNo(){
      getRuleFlowMethod({ rule_library: this.rule_method.subrule_no }).then((res) => {
        if (
          res.status == 0 &&
          JSON.stringify(res.data) != "{}"
        ) {
          this.rule_method.polymer_abbreviation = res.data.polymer_abbreviation
          this.rule_method.product_small_type = res.data.product_small_type
        }
      });
    },
    querySubRuleNoList(str, cb) {
      str = str == null ? "" : str 
      let promptList = []
      getOptions("rule_library", { "form_input": str, "db_table": "rule_flow" })
      .then( res => {
        if(res.status == 0) {
          for(let i = 0; i < res.data.length; i++) {
            promptList.push({ value: res.data[i] })
          }
        }
      })
      cb(promptList)
    }, 
    queryMethodProductType(str, cb) {
      str = (str == null ? "" : str)
      let promptList = []
      getOptions("product_small_type", { "form_input": str, "db_table": "mold" })
      .then( res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({ value: res.data[i] })
          }
        }
      })
      cb(promptList)
    },
    queryMethodPolymerAbbreviation(str, cb) {
      str = (str == null ? "" : str)
      let promptList = []
      getOptions("polymer_abbreviation")
      .then( res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({ value: res.data[i].value })
          }
        }
      })
      cb(promptList)
    },
    initView() {
      // ruleKeywordMethod.get({"rule_type":this.ruleType,"subrule_no":this.subruleNo})
      // 读取参数:rule_type:基础库,keyword_type:参数: 查询每个子规则库对应的
      // 如果是基础库,那么读取基础库的参数
      // 如果是子规则库,那么读取子规则库的参数
      let query = null
      if(this.ruleType === "基础库"){
        query = {"rule_type":"基础库","keyword_type":"参数"}
      }else if(this.ruleType === "子规则库"){
        query = {"rule_type":"子规则库","keyword_type":"参数", "subrule_no":this.rule_method.subrule_no}
      }
      ruleKeywordMethod.get(query)
      .then(res => {
        if (res.status === 0) {
          let keywords = res.data.items
          // this.keywordMap = {}
          this.normalKeywordOptions.length = 0
          this.concludeKeywordOptions.length = 0
          for (let i = 0; i < keywords.length; ++i) {
            if (keywords[i].keyword_type === "参数") {
              this.normalKeywordOptions.push({ 
                label: keywords[i].comment, 
                value: keywords[i].name 
              })
              this.concludeKeywordOptions.push({ 
                label: keywords[i].comment, 
                value: keywords[i].name 
              })        
            } 
            this.keywordMap[keywords[i].name] = keywords[i].comment
          }
        }
      })  
      // 读取缺陷:rule_type:基础库,keyword_type:缺陷: 公用一套
      ruleKeywordMethod.get({"rule_type":"基础库","keyword_type":"缺陷"})
      .then(res => {
        if (res.status === 0) {
          let keywords = res.data.items
          // this.keywordMap = {}
          this.defectKeywordOptions.length = 0
          for (let i = 0; i < keywords.length; ++i) {
            if (keywords[i].keyword_type === "缺陷") {
              this.defectKeywordOptions.push({ 
                label: keywords[i].comment, 
                value: keywords[i].name 
              })
            } 
            this.keywordMap[keywords[i].name] = keywords[i].comment
          }
        }
      }) 
    },
    resetRowValue(precondition, type) {
      if (type === "precondition") {
        precondition.keyword = null
        precondition.describe = null
      }
    },
    addPrecondition() {
      this.rule_method.preconditions.push({
        conditiontype: null,
        keyword: null,
        describe: null
      })
    },
    subPrecondition(index) {
      this.rule_method.preconditions.splice(index, 1)
    },
    addSolution() {
      this.rule_method.solutions.push({
        conditiontype: null,
        keyword: null,
        describe: null, 
        action: null
      })
    },
    subSolution(index) {
      this.rule_method.solutions.splice(index, 1)
    },
    generateRule() {
      if (this.validateForm()) {
      let precon_desc = "IF "
      let precon_exp = "如果"
      for (let i = 0; i < this.rule_method.preconditions.length; i++) {
        let precondition = this.rule_method.preconditions[i]
        if (i != 0) {
          precon_desc += " AND "
          precon_exp += ","
        }
        precon_desc += precondition.keyword + "_" + precondition.describe
        precon_exp += this.keywordMap[precondition.keyword] + (precondition.conditiontype === "普通前置条件" ? 
          this.paraLevelMap[precondition.describe] : this.defectLevelMap[precondition.describe])
      }
      let solu_desc = " THEN "
      let solu_exp = ",那么"
      for (let i = 0; i < this.rule_method.solutions.length; i++) {
        let solution = this.rule_method.solutions[i]
        if (i != 0) {
          solu_desc += " AND "
          solu_exp += ","
        }
        solu_desc += solution.keyword + "_" + solution.action + "_" + solution.describe
        solu_exp += this.keywordMap[solution.keyword] + this.actionMap[solution.action] + solution.describe
      } 
      this.rule_method.rule_description = precon_desc + solu_desc
      this.rule_method.rule_explanation = precon_exp + solu_exp
      }
    }, 
    validateForm() {
      for (let i = 0; i < this.rule_method.preconditions.length; i++) {
        if (this.rule_method.preconditions[i].conditiontype == "缺陷前置条件") {
          this.defect_desc = this.rule_method.preconditions[i].keyword
          this.defect_name = this.defectKeywordOptions.find(option => option.value === this.defect_desc)?.label
        }
        if (!this.rule_method.preconditions[i].conditiontype) {
          this.$message({
            type: 'warning',
            message: '条件部分条件类型不能为空'
          });  
          return false
        }
        if (!this.rule_method.preconditions[i].keyword) {
          this.$message({
            type: 'warning',
            message: '条件部分关键字不能为空'
          });  
          return false
        }
        if (!this.rule_method.preconditions[i].describe) {
          this.$message({
            type: 'warning',
            message: '条件部分描述不能为空'
          });  
          return false
        } 
      }
      for (let i = 0; i < this.rule_method.solutions.length; i++) {
        if (!this.rule_method.solutions[i].conditiontype) {
          this.$message({
            type: 'warning',
            message: '结论部分条件类型不能为空'
          });  
          return false
        }
        if (!this.rule_method.solutions[i].keyword) {
          this.$message({
            type: 'warning',
            message: '结论部分关键字不能为空'
          });  
          return false
        }
        if (!this.rule_method.solutions[i].describe) {
          this.$message({
            type: 'warning',
            message: '结论部分描述不能为空'
          }); 
          return false
        } 
        if (!this.rule_method.solutions[i].action) {
          this.$message({
            type: 'warning',
            message: '结论部分动作不能为空'
          }); 
          return false
        } 
      }
      if(!this.rule_method.subrule_no){
        this.$message({
            type: 'warning',
            message: '子规则库编号不能为空'
          });  
          return false
      }
      return true
    },
    addRuleMethod() {
      if (this.validateForm()) {
        this.generateRule()
        // 默认添加子规则库,并且条件部件的缺陷只有一个
        let rule_method = {
          subrule_no: this.rule_method.subrule_no,
          rule_type: '子规则库',
          defect_name:this.defect_name,
          defect_desc:this.defect_desc,
          polymer_abbreviation: this.rule_method.polymer_abbreviation,
          product_small_type: this.rule_method.product_small_type,
          rule_description: this.rule_method.rule_description,
          rule_explanation: this.rule_method.rule_explanation,
          is_auto: 0,
          enable: 1
        }
 
        ruleDetailMethod.add(rule_method)
        .then(res => {
          if (res.status === 0) {
            this.$message({
              type: "success",
              message: "新增规则成功！"
            })
          } else {
            this.$message({
              type: "error",
              message: "新增规则失败！"
            })
          }
        }).finally(() => {
          this.resetView()
        })
      }
    },
    updateRuleMethod() {
      if(this.validateForm()) {
        this.generateRule()

        let rule_method = {
          subrule_no: this.rule_method.subrule_no, 
          defect_name:this.defect_name,
          defect_desc:this.defect_desc,
          rule_type: this.rule_method.rule_type,
          polymer_abbreviation: this.rule_method.polymer_abbreviation,
          product_small_type: this.rule_method.product_small_type,
          rule_description: this.rule_method.rule_description,
          rule_explanation: this.rule_method.rule_explanation,
          is_auto: 0,
          enable: 1
        }

        ruleDetailMethod.edit(rule_method, this.ruleMethodId)
        .then(res => {
          if (res.status === 0) {
            this.$message({
              type: "success",
              message: "更新规则成功！"
            })
          } else {
            this.$message({
              type: "error",
              message: "更新规则失败！"
            })
          }
        }).finally(() => {
          this.resetView()
        })
      }
    },
    cancel() {
      this.resetView()
    },
    resetView() {
      this.rule_method.subrule_no = null,
      this.defect_desc = null,
      this.defect_name = null,
      this.rule_type = null,
      this.rule_method.polymer_abbreviation = null
      this.rule_method.product_small_type = null
      this.rule_method.preconditions = [{
        conditiontype: '缺陷前置条件',
        keyword: null,
        describe: null
      }]
      this.rule_method.solutions = [{
        conditiontype: '结论条件',
        keyword: null,
        describe: null,
        action: null            
      }]
      this.rule_method.rule_description = null
      this.rule_method.rule_explanation = null
      this.$emit("close-dialog")
    },
    concludeChange(){
      for(let i=0;i<this.rule_method.solutions.length;i++){
        if(this.concludeDescribe.has(this.rule_method.solutions[i].keyword)){
          this.rule_method.solutions[i].action  = "adjust"
          this.rule_method.solutions[i].describe  = "请检查"+this.getConcludeDescribe(this.rule_method.solutions[i].keyword)+"是否不合理。"
        }
      }
    },
    getConcludeDescribe(keyword) {
      return this.concludeDescribe.get(keyword)
    }
  },
  watch: {
    ruleMethod: function() {
      this.rule_method = this.ruleMethod
    },
    "rule_method.subrule_no":function() {
      this.initView()
    }
  }
})
</script>

<style scoped lang="scss">

</style>
