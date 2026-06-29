<template>
  <div>
    <el-form 
      ref="keywordForm" 
      :model="rule_keyword" 
      :rules="form_rules"
      label-width="8rem" 
      :inline="true"
      size="small"
    >
      <el-form-item 
        label="子规则库编号" 
        prop="subrule_no"
      >
        <el-autocomplete 
          v-model="rule_keyword.subrule_no"
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
          v-model="rule_keyword.product_small_type"
          :fetch-suggestions="queryMethodProductType"
          placeholder="请输入内容"
          :debounce="0"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="塑料简称" prop="polymer_abbreviation">
        <el-autocomplete 
          v-model="rule_keyword.polymer_abbreviation"
          :fetch-suggestions="queryMethodPolymerAbbreviation"
          placeholder="请输入内容"
          :debounce="0"
        >
        </el-autocomplete>
      </el-form-item>
      <br />
      <el-form-item 
        label="关键词" 
        prop="name"
      >
        <el-input 
          v-model="rule_keyword.name"
          oninput="value=value.replace(/[^0-9a-zA-Z]/g, '')" 
          placeholder="IV0" 
          style="width: 20rem"
        ></el-input>
      </el-form-item>

      <br />

      <el-form-item 
        label="类型" 
        prop="keyword_type"
      >
        <el-radio-group 
          v-model="rule_keyword.keyword_type"
        >
          <el-radio label="参数">参数</el-radio>
          <el-radio label="缺陷">缺陷</el-radio>
          <el-radio label="其他">其他</el-radio>
        </el-radio-group>
      </el-form-item>

      <br />

      <el-form-item 
        label="模糊级别" 
        prop="level"
      >
        <el-select 
          v-model="rule_keyword.level" 
          placeholder="请选择" 
          style="width: 8rem"
        >
          <el-option label="3" value="3"></el-option>
          <el-option label="5" value="5"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item 
        label="最小取值" 
        prop="all_range_min"
      >
        <el-input-number
          v-model="rule_keyword.all_range_min" 
          type="number" 
          style="width: 8rem"
        ></el-input-number>
      </el-form-item>

      <el-form-item 
        label="最大取值" 
        prop="all_range_max"
      >
        <el-input-number 
          v-model="rule_keyword.all_range_max" 
          type="number" 
          style="width: 8rem"
        ></el-input-number>
      </el-form-item>

      <br />

      <el-form-item 
        label="调整最小值" 
        prop="action_range_min"
      >
        <el-input-number 
          v-model="rule_keyword.action_range_min" 
          type="number" 
          :disabled="rule_keyword.keyword_type=='缺陷'"
          style="width: 8rem"
        ></el-input-number>
      </el-form-item>

      <el-form-item 
        label="调整最大值" 
        prop="action_range_max"
      >
        <el-input-number 
          v-model="rule_keyword.action_range_max" 
          type="number" 
          :disabled="rule_keyword.keyword_type=='缺陷'"
          style="width: 8rem"
        ></el-input-number>
      </el-form-item>

      <el-form-item 
        label="调整幅度限定值" 
        prop="action_max_val"
      >
        <el-input-number 
          v-model="rule_keyword.action_max_val" 
          type="number" 
          :disabled="rule_keyword.keyword_type=='缺陷'"
          style="width: 8rem"
        ></el-input-number>
      </el-form-item>

      <br />

      <el-form-item 
        label="注释" 
        prop="comment"
      >
        <el-input 
          type="textarea" 
          v-model="rule_keyword.comment" 
          placeholder="一级注射压力"
          style="width: 20rem"
        ></el-input>
      </el-form-item>
    </el-form>

    <div style="text-align: center">
      <el-button
        v-if="ruleKeywordId == null"
        type="primary" 
        size="small"
        style="width: 6rem"
        @click="saveKeyword" 
      >
        保 存
      </el-button>

      <el-button
        v-if="ruleKeywordId"
        type="primary" 
        size="small"
        style="width: 6rem"
        @click="updateKeyword" 
      >
        更 新
      </el-button>

      <el-button 
        size="small" 
        style="width: 6rem"
        @click="cancel"
      >
        取 消
      </el-button>
    </div>
  </div>
</template>

<script>
import { ruleKeywordMethod, getOptions, getRuleFlowMethod } from "@/api";

export default ({
  name: "RuleKeywordDetail",
  props: {
    ruleKeyword: {
      type: Object,
      default: () => ({
        name: null,
        keyword_type: null,
        comment: null,
        level: null,
        all_range_min: null,
        all_range_max:null,
        action_range_min: null,
        action_range_max: null,
        action_max_val: null,
        subrule_no:null,
        product_small_type:null,
        polymer_abbreviation:null,
      })
    },
    ruleKeywordId:{
      type: Number,
      default: null
    }
  },
  data() {
    return {
      rule_keyword: this.ruleKeyword,
      form_rules: {
        name: [
          { required: true, message: "关键词不能为空！" }
        ]
      }
    }
  },
  mounted() {

  },
  methods: {
    setSubruleNo(){
      getRuleFlowMethod({ rule_library: this.rule_keyword.subrule_no }).then((res) => {
        if (
          res.status == 0 &&
          JSON.stringify(res.data) != "{}"
        ) {
          this.rule_keyword.polymer_abbreviation = res.data.polymer_abbreviation
          this.rule_keyword.product_small_type = res.data.product_small_type
          this.rule_keyword.rule_type = "子规则库"
          this.rule_keyword.show_on_page = 1
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
    saveKeyword() {
      if(!this.rule_keyword.subrule_no){
        this.$message({
            type: 'warning',
            message: '子规则库编号不能为空'
          });  
          return false
      }
      this.$refs["keywordForm"].validate((valid) => {
        if (valid) {
          ruleKeywordMethod.add(this.rule_keyword)
          .then(res => {
            this.$message({
              type: res.status === 0 ? 'success' : 'error',
              message: res.status === 0 ? '保存成功！' : '保存失败！'
            })
          }).finally(()=> {
            this.resetView()
          })
        }
      })
    },
    updateKeyword() {
      this.$refs["keywordForm"].validate((valid) => {
        if (valid) {
          ruleKeywordMethod.edit(this.rule_keyword, this.ruleKeywordId)
          .then(res => {
            this.$message({
              type: res.status === 0 ? 'success' : 'error',
              message: res.status === 0 ? '更新成功！' : '更新失败！'
            })
          }).finally(()=> {
            this.resetView()
          })
        }
      })
    },
    cancel() {
      this.resetView()
    },
    resetView() {
      this.rule_keyword.name = null
      this.rule_keyword.keyword_type = null
      this.rule_keyword.comment = null
      this.rule_keyword.level = null
      this.rule_keyword.all_range_min = null
      this.rule_keyword.all_range_max = null
      this.rule_keyword.action_range_min = null
      this.rule_keyword.action_range_max = null
      this.rule_keyword.action_max_val = null
      this.subrule_no = null,
      this.product_small_type = null,
      this.polymer_abbreviation = null,
      this.$emit('close-dialog')
    }
  },
  watch: {
    "ruleKeyword": function() {
      this.rule_keyword = this.ruleKeyword
    }
  }
})
</script>

<style scoped>

</style>
