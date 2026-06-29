<template>
  <div>
    <el-card class="box-card">
      <div slot="header" class="clearfix">
        <span>规则关键词</span>
        <el-button 
          type="primary" 
          size="mini" 
          style="float: right; width: 6rem"
          @click="addRuleKeyword"
        >
          新建关键词
        </el-button>
      </div>
      <div>
        <el-form 
          label-width="8rem" 
          :inline="true" 
          size="mini"
        >
          <el-form-item 
            label="关键词定义" 
            prop="name"
          >
            <el-autocomplete 
              v-model="keywordQuery.name"
              :fetch-suggestions="((str, cb) => {querySuggestionOptions(str, cb,'rule_keyword')})"
              placeholder="请输入内容"
              :debounce="0"
              clearable
            >
            </el-autocomplete>
          </el-form-item>
          <el-form-item 
            label="关键词类型" 
            prop="keyword_type"
          >
            <el-select 
              v-model="keywordQuery.keyword_type"
            >
              <el-option label="缺陷" value="缺陷"></el-option>
              <el-option label="参数" value="参数"></el-option>
            </el-select>
          </el-form-item>
          <div style="float: right">
            <el-button 
              type="primary" 
              size="mini" 
              style="width: 6rem"
              @click="refreshKeywordView(reset=true)"
            >
              搜索
            </el-button>
          </div>
        </el-form>
      </div>
      <br />
      <div>
        <el-table 
          border 
          height="600px"
          :data="keywordTableData"
          v-loading="keywordLoading"
        >
          <el-table-column
            type="index"
            label="序号"
            width="55"
            align="center"
          >
          </el-table-column>
          <template v-for="item in keywordTable">
            <el-table-column 
              :key="item.id" 
              :prop="item.prop" 
              :label="item.label"
              :header-align="item.header_align"
              :align="item.align"
              :show-overflow-tooltip="item.tooltip"
              :min-width="item.width"
            >
              <template #default="scope">
                <div v-if="item.prop === 'operation'">
                  <el-button 
                    type="primary"
                    size="mini"
                    style="width: 4rem"
                    @click="editKeyword(scope.row)"
                  >
                    编辑
                  </el-button>
                  <el-button 
                    type="danger" 
                    size="mini"
                    style="width: 4rem"
                    @click="deleteKeyword(scope.row)" 
                  >
                    删除
                  </el-button>
                </div>
                <div v-else>
                  <span>{{ scope.row[item.prop] }}</span>
                </div>
              </template>
            </el-table-column>
          </template>
        </el-table>
        <el-pagination
          layout="total, sizes, prev, pager, next, jumper"
          :current-page="keywordQuery.page_no"
          :page-size="keywordQuery.page_size"
          :total="keywordQuery.total"
          :page-sizes="$store.state.app.pageSizeArray"
          @size-change="handleKeywordSizeChange"
          @current-change="handleKeywordCurrentChange"
        />
      </div>
    </el-card>
    <el-card class="library">
      <div slot="header" class="clearfix">
        <span>规则库管理</span>
        <el-button 
          type="primary" 
          size="mini"
          style="float: right; width: 6rem"
          @click="addRuleMethod"
        >
          新建规则
        </el-button>
      </div>
      <div>
        <el-form 
          label-width="8rem" 
          :inline="true" 
          size="mini"
        >
          <el-form-item 
            label="制品大类(行业)" 
            prop="product_industry"
          >
            <el-select
              allow-create
              clearable
              filterable
              v-model="methodQuery.product_industry"
            >
              <el-option
                v-for="(option, index) in product_industry_options"
                :key="index"
                :label="option.label"
                :value="option.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item 
            label="制品中类(商品)" 
            prop="product_category"
          >
            <el-select
              allow-create
              clearable
              filterable
              v-model="methodQuery.product_category"
            >
              <el-option
                v-for="(option, index) in product_category_options"
                :key="index"
                :label="option.label"
                :value="option.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item 
            label="制品小类(品类)" 
            prop="product_type"
          >
            <el-select
              allow-create
              clearable
              filterable
              v-model="methodQuery.product_type"
            >
              <el-option
                v-for="(option, index) in product_type_options"
                :key="index"
                :label="option.label"
                :value="option.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item 
            label="塑料简称" 
            prop="polymer_abbreviation"
          >
            <el-autocomplete 
              v-model="methodQuery.polymer_abbreviation"
              :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'polymer_abbreviation')})"
              placeholder="请输入内容"
              :debounce="0"
              clearable
            >
            </el-autocomplete>
          </el-form-item>
          <!-- <el-form-item label="自动规则" prop="is_auto">
            <el-input v-model="methodQuery.is_auto">
            </el-input>
          </el-form-item> -->
          <el-form-item 
            label="启用状态" 
            prop="enable"
          >
            <el-select 
              v-model="methodQuery.keyword_type"
            >
              <el-option label="启用" value="1"></el-option>
              <el-option label="禁用" value="0"></el-option>
            </el-select>
          </el-form-item>
          <div style="float: right">
            <el-button 
              type="primary" 
              size="mini" 
              style="width: 6rem"
              @click="refreshMethodView(reset=true)"
            >
              搜索
            </el-button>
          </div>
        </el-form>
      </div>
      <br />
      <div>
        <template>
          <el-table
            border
            height="750px"
            :data="methodTableData"
            v-loading="methodLoading"
          >
            <el-table-column
              type="index"
              label="序号"
              width="55"
              align="center"
            >
            </el-table-column>
            <template v-for="item in methodTable">
              <el-table-column 
                :key="item.id" 
                :prop="item.prop" 
                :label="item.label"
                :header-align="item.header_align"
                :align="item.align"
                :show-overflow-tooltip="item.tooltip"
                :min-width="item.width"
              >
                <template #default="scope">
                  <div v-if="item.prop === 'operation'">
                    <el-button 
                      type="primary"
                      size="mini" 
                      style="width: 4rem"
                      @click="editRuleMethod(scope.row)"
                    >
                      编辑
                    </el-button>
                    <el-button 
                      type="danger" 
                      size="mini" 
                      style="width: 4rem"
                      @click="deleteRuleMethod(scope.row)"
                    >
                      删除
                    </el-button>
                  </div>
                  <div v-else-if="item.prop === 'enable'">
                    <el-button 
                      type="text" 
                      size="mini" 
                      :style="scope.row[item.prop] === 1 ? 'color: lime' : 'color: gray'"
                      @click="updateRuleMethodEnable(scope.row.id, scope.row[item.prop])"
                    >
                      {{ scope.row[item.prop] === 1 ? "启用" : "禁用" }}
                    </el-button>
                  </div>
                  <div v-else>
                    <span>{{ scope.row[item.prop] }}</span>
                  </div>
                </template>
              </el-table-column>
            </template>
          </el-table>
          <el-pagination
            layout="total, sizes, prev, pager, next, jumper"
            :current-page="methodQuery.page_no"
            :page-size="methodQuery.page_size"
            :total="methodQuery.total"
            :page-sizes="$store.state.app.pageSizeArray"
            @size-change="handleMethodSizeChange"
            @current-change="handleMethodCurrentChange"
          />
        </template>
      </div>
    </el-card>
    <el-dialog
      title="工艺关键词"
      :visible.sync="showKeyword"
      width="50%"
      @closeDialog="closeKeywordDialog"
    >
      <rule-keyword-detail
        :rule-keyword-id="ruleKeywordId"
        :rule-keyword="keywordFormData"
        @close-dialog="closeKeywordDialog"
      >
      </rule-keyword-detail>
    </el-dialog>
    <el-dialog
      title="优化规则"
      :visible.sync="showMethod"
      width="55%"
      @closeDialog="closeMethodDialog"
    >
      <rule-method-detail
        :rule-method-id="ruleMethodId"
        :rule-method="methodFormData"
        @close-dialog="closeMethodDialog"
      >
      </rule-method-detail>
    </el-dialog>
  </div>
</template>

<script>
import { ruleKeywordMethod, ruleDetailMethod } from "@/api"
import SuggestionOptions from "@/mixins/suggestionOptions.vue"
import * as mold_const from "@/constants/mold-const"
import RuleKeywordDetail from "./subView/ruleKeywordDetail.vue"
import RuleMethodDetail from "./subView/ruleMethodDetail.vue"

export default {
  components: { RuleKeywordDetail , RuleMethodDetail },
  mixins: [SuggestionOptions],
  data() {
    return {
      keywordQuery: {
        deleted: 0,
        name: null,
        keyword_type: null,

        page_no: 1, //当前页
        page_size: 100,//每页条数
        total: 2, //列表总条数
      },
      keywordTable: [
        { visible: true, label: "关键词定义", prop: "name", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "类型", prop: "keyword_type", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "注释", prop: "comment", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模糊级别", prop: "level", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "最小取值", prop: "all_range_min", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "最大取值", prop: "all_range_max", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "调整最小值", prop: "action_range_min", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "调整最大值", prop: "action_range_max", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "调整幅度", prop: "action_max_val", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "操作", prop: "operation", width: 160, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      keywordTableData:[
        { name:"IV0", keyword_type:"参数", comment:"一级注射速度", level:"3", all_range_min: "0", all_range_max: "200", action_range_min: "1", action_range_max: "5", center: "5" },
        { name:"IV0", keyword_type:"参数", comment:"一级注射速度", level:"3", all_range_min: "0", all_range_max: "200", action_range_min: "1", action_range_max: "5", center: "5" },
      ],
      keywordLoading: false,
      showKeyword: false,
      ruleKeywordId: null,
      keywordFormData: {
        name: null,
        keyword_type: null,
        comment: null,
        level: 3,
        all_range_min: null,
        all_range_max:null,
        action_range_min: null,
        action_range_max: null,
        action_max_val: null
      },
      methodQuery: {
        polymer_abbreviation: null,
        // product_industry:null,  // rule_method数据库里没有这个字段
        // product_category:null,
        product_type: null,
        is_auto: null,
        enable: null,

        page_no: 1, //当前页
        page_size: 100,//每页条数
        total: 0, //列表总条数
      },
      product_industry_options: mold_const.productIndustryOptions,
      product_category_options: null,
      product_type_options: null,
      methodTable: [
        { visible: true, label: "制品类别", prop: "product_type", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "塑料简称", prop: "polymer_abbreviation", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "规则描述", prop: "rule_description", width: 340, align: "left", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "规则解释", prop: "rule_explanation", width: 360, align: "left", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "状态", prop: "enable", width: 40, align: "center", header_align: "center", sortable: false, tooltip: false },
        // { visible: true, label: "自动规则", prop: "is_auto", width: 40, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "操作", prop: "operation", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      methodTableData: [
        { rule_process: "IF NT_LOW AND BT_LOW AND shortshot_DT3_LOW Then IP1_ADD_LOW AND IV1_LOW" , name: "如果料筒温度低，短射严重等。。" },
        { rule_process: "IF NT_LOW AND BT_LOW AND shortshot_DT3_LOW Then IP1_ADD_LOW AND IV1_LOW" , name: "如果料筒温度低，短射严重等。。" },
        { rule_process: "IF NT_LOW AND BT_LOW AND shortshot_DT3_LOW Then IP1_ADD_LOW AND IV1_LOW" , name: "如果料筒温度低，短射严重等。。" },
      ],
      methodLoading: false,
      showMethod: false,
      ruleMethodId: null,
      methodFormData: {
        polymer_abbreviation: null,
        product_type: null,
        preconditions: [{
          conditiontype: "缺陷前置条件",
          keyword: null,
          describe: null
        }],
        solutions: [{
          conditiontype: "结论条件",
          keyword: null,
          describe: null,
          action: null            
        }],
        rule_description: null,
        rule_explanation: null
      }
    }
  },
  watch: {
    "methodQuery.product_industry"() {
      const categoryOptions = {
        "家用电器": mold_const.electricApplianceOptions,
        "消费电子": mold_const.electronicOptions,
        "交通运输": mold_const.trafficOptions,
        "医疗健康": mold_const.medicalHealthOptions,
        "建材家居": mold_const.buildingFurnishingsOptions,
        "包装": mold_const.packagingOptions,
        "办公文教": mold_const.officeEducationOptions,
        "玩具休闲": mold_const.toysLeisureOptions,
      }
      this.product_category_options = categoryOptions[this.methodQuery.product_industry] || null
    },
    "methodQuery.product_category"() {
      this.product_type_options = mold_const.smallTypeOptions[this.methodQuery.product_category] || null
    }
  },
  created() {
    this.refreshKeywordView()
    this.refreshMethodView()
  },
  methods: {
    async querySuggestionOptions(input_str, cb, db_column) {let selections = []
      if (["polymer_abbreviation"].includes(db_column)) {
        selections = await this.queryOptions(input_str, "rule_method", "polymer_abbreviation")
      } else if ("rule_keyword" == db_column) {
        selections = await this.queryOptions(input_str, "rule_keyword", "name")
      }
      cb(selections)
    },
    addRuleKeyword() {
      this.showKeyword = true
    },
    closeKeywordDialog() {
      this.showKeyword = false
      this.refreshKeywordView()
    },
    editKeyword(row) {
      this.keywordFormData = row
      this.ruleKeywordId = row.id
      this.showKeyword = true
    },
    deleteKeyword(row) {
      this.$confirm("确定要删除这条规则关键词么？", "删除规则关键词", {
        confirmButtonText: "确认",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        ruleKeywordMethod.delete(row.id)
          .then(res => {
            this.refreshKeywordView()
          })
      })
    },
    handleKeywordSizeChange(val) {
      this.keywordQuery.page_size = val
      this.refreshKeywordView()
    },
    handleKeywordCurrentChange(val) {
      this.keywordQuery.page_no = val
      this.refreshKeywordView()
    },
    addRuleMethod() {
      this.showMethod = true
    },
    closeMethodDialog() {
      this.showMethod = false
      this.refreshMethodView()
    },
    ruleTransferForm(rule_description) {
      let section_list = rule_description.trim().split(" ")
      let resolve_step = 0
      let defect_list = ["SHORTSHOT", "FLASH", "SHRINKAGE", "WELDLINE", "ABERRATION", "AIRTRAP"]
      this.methodFormData.preconditions.length = 0
      this.methodFormData.solutions.length = 0

      for (let i = 0; i < section_list.length; ++i) {
        if (section_list[i] === "IF") {
          resolve_step = 1
        } else if (section_list[i] === "Then" || section_list[i] === "THEN") {
          resolve_step = 2
        } else if (section_list[i] == "AND") {
          continue
        } else {
          let words = section_list[i].split("_")
          if (resolve_step === 1) {
            if (defect_list.indexOf(words[0]) === -1) {
              this.methodFormData.preconditions.push({
                conditiontype: "普通前置条件",
                keyword: words[0],
                describe: words[1]
              })
            } else {
              this.methodFormData.preconditions.push({
                conditiontype: "缺陷前置条件",
                keyword: words[0],
                describe: words[1]
              })
            }
          } else if (resolve_step === 2) {
            if (words.length === 2) {
              this.methodFormData.solutions.push({
                conditiontype: "结论条件",
                keyword: words[0],
                describe: words[1]
              })
            } else if (words.length === 3) {
              this.methodFormData.solutions.push({
                conditiontype: "结论条件",
                keyword: words[0],
                action: words[1],
                describe: words[2]
              })
            }
          }
        }
      }

      this.methodFormData.rule_description = rule_description

      return resolve_step === 0 ? false : true
    },
    editRuleMethod(row) {
      this.ruleTransferForm(row.rule_description)
      this.methodFormData.product_type = row.product_type
      this.methodFormData.polymer_abbreviation = row.polymer_abbreviation
      this.methodFormData.rule_explanation = row.rule_explanation
      this.ruleMethodId = row.id
      this.showMethod = true
    },
    deleteRuleMethod(row) {
      this.$confirm("确定要删除这条规则么？", "删除规则", {
        confirmButtonText: "确认",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        ruleDetailMethod.delete(row.id)
          .then(res => {
            this.refreshMethodView()
          })
      })
    },
    updateRuleMethodEnable(id, enable) {
      let swt = enable === 1 ? 0 : 1
      this.$confirm(swt === 0 ? "确定禁用当前规则？" : "确定启用当前规则？", "提示", {
        confirmButtonText: "确认",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        ruleDetailMethod.edit({
          enable: swt
        }, id).then(res => {
          if (res.status === 0) {
            this.$message({
              type: "success",
              message: swt === 0 ? "已禁用当前规则！" : "已启用当前规则！"
            })
            this.refreshMethodView()
          }
        })
      })
    },
    handleMethodSizeChange(val) {
      this.methodQuery.page_size = val
      this.refreshMethodView()
    },
    handleMethodCurrentChange(val) {
      this.methodQuery.page_no = val
      this.refreshMethodView()
    },
    refreshKeywordView(reset = false) {
      if (reset) this.keywordQuery.page_no = 1

      this.keywordLoading = true
      ruleKeywordMethod.get(this.keywordQuery)
        .then(res => {
          if (res.status === 0) {
            this.keywordTableData = res.data.items
            this.keywordQuery.total = res.data.total
          }
        }).finally(() => {
          this.keywordLoading = false
        })

    },
    refreshMethodView(reset = false) {
      if (reset) this.methodQuery.page_no = 1

      this.methodLoading = true
      ruleDetailMethod.get(this.methodQuery)
        .then(res => {
          if (res.status === 0) {
            this.methodTableData = res.data.items
            this.methodQuery.total = res.data.total
          }
        }).finally(() => {
          this.methodLoading = false
        })
    }
    // addRuleDatabase(row) {
    //   ruleDetailMethod.edit({"recorded":1}, row.id).then(res => {
    //     this.$message(`成功加入规则库`)
    //   })
    // },
  }
}
</script>

<style lang="scss" scoped>
  .el-autocomplete {
    width: 10rem;
  }
  .el-input {
    width: 10rem
  }
  .el-select {
    width: 10rem
  }
  .box-card {
    margin: 10px 10px 0px 10px;
  }
  .library {
    margin: 10px 10px 0px 10px;
  }
  label {
    font-weight: bold;
  }
  .page {
    margin-top: 10px;
    margin-left: 1400px;
  }
</style>