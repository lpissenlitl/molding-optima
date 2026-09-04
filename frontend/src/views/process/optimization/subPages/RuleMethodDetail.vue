<template>
  <div>
    <el-form 
      ref="methodForm" 
      label-width="5rem"
      size="small" 
      :inline="true"
    >
      <el-form-item label="制品类别" prop="product_type">
        <el-autocomplete 
          v-model="rule_method.product_type"
          :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'product_type')})"
          placeholder="请输入内容"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="塑料简称" prop="polymer_abbreviation">
        <el-autocomplete 
          v-model="rule_method.polymer_abbreviation"
          :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'polymer_abbreviation')})"
          placeholder="请输入内容"
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
        <el-form-item label="描述">
          <el-select 
            v-model="item.describe" 
            prop="describe"
            style="width: 8rem"
          >
            <template v-if="item.conditiontype === '结论条件'">
              <el-option
                v-for="key, value in adjustLevelMap"
                :key="value"
                :label="key"
                :value="value"
              ></el-option>
            </template>
          </el-select>
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
import { ruleDetailMethod, ruleKeywordMethod } from "@/api"

export default ({
  name: "RuleMethodDetail",
  props: {
    ruleMethod: {
      type: Object,
      default: () => ({
        product_type: null,
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
      paraLevelMap: { low: "偏低", mid: "适当", high: "偏高" },
      defectLevelMap: { low: "轻微", mid: "中等", high: "严重" },
      actionMap: {  add: "增高" , reduce: "降低" },
      adjustLevelMap: { low: "少量", mid: "中等", high: "大量" },
      defectKeywordOptions: [
        { label: "IP0", value: "IP0" },
        { label: "IP1", value: "IP1" }
      ],
      concludeKeywordOptions: [
        { label: "IP0", value: "IP0" },
        { label: "IP1", value: "IP1" }
      ],
    }
  },
  created() {
    this.initView()
  },
  methods: {
    async querySuggestionOptions(input_str, cb, db_column) {
      let selections = [];
      if (["polymer_abbreviation", "product_type"].includes(db_column)) {
        selections = await this.queryOptions(input_str, "rule_method", db_column);
      }
      cb(selections);
    },
    initView() {
      ruleKeywordMethod.get()
      .then(res => {
        if (res.status === 0) {
          let keywords = res.data.items
          this.keywordMap = {}
          this.concludeKeywordOptions.length = 0
          this.normalKeywordOptions.length = 0
          this.defectKeywordOptions.length = 0
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
            } else if (keywords[i].keyword_type === "缺陷") {
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
        solu_exp += this.keywordMap[solution.keyword] + this.actionMap[solution.action] +  this.adjustLevelMap[solution.describe]
      } 
      this.rule_method.rule_description = precon_desc + solu_desc
      this.rule_method.rule_explanation = precon_exp + solu_exp
    }, 
    validateForm() {
      for (let i = 0; i < this.rule_method.preconditions.length; i++) {
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
      return true
    },
    addRuleMethod() {
      if (this.validateForm()) {
        this.generateRule()

        let rule_method = {
          polymer_abbreviation: this.rule_method.polymer_abbreviation,
          product_type: this.rule_method.product_type,
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
          polymer_abbreviation: this.rule_method.polymer_abbreviation,
          product_type: this.rule_method.product_type,
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
      this.rule_method.polymer_abbreviation = null
      this.rule_method.product_type = null
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
    }
  },
  watch: {
    ruleMethod: function() {
      this.rule_method = this.ruleMethod
    }
  }
})
</script>

<style scoped lang="scss">

</style>
