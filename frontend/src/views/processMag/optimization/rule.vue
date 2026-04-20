<template>
  <div>
    <el-card class="box-card">
      <div class="clearfix" style="height:30px">
        <span>规则库选择</span>
        <el-select v-model="subruleQuery.rule_type" size="mini" style="margin-left:10px">
          <el-option label="基础库" value="基础库"></el-option>
          <el-option label="子规则库" value="子规则库"></el-option>
        </el-select>
      </div>
      <div style="height:10px"></div>
      <div>
        <el-form 
          label-width="6.3rem" 
          :inline="true" 
          size="mini"
        >
          <el-form-item 
            label="子规则库编号" 
            prop="subrule_no"
          >
            <el-autocomplete 
              v-model="subruleQuery.subrule_no"
              :fetch-suggestions="querySubRuleNoList"
              @select="getPriority"
              placeholder="请输入内容"
              clearable
              :debounce="0"
            >
            </el-autocomplete>
          </el-form-item>

          <el-form-item 
            label="制品类别" 
            prop="product_small_type"
          >
            <el-autocomplete 
              v-model="subruleQuery.product_small_type"
              :fetch-suggestions="queryMethodProductType"
              placeholder="请输入内容"
              clearable
              :debounce="0"
            >
            </el-autocomplete>
          </el-form-item>

          <el-form-item 
            label="塑料简称" 
            prop="polymer_abbreviation"
          >
            <el-autocomplete 
              v-model="subruleQuery.polymer_abbreviation"
              :fetch-suggestions="queryMethodPolymerAbbreviation"
              placeholder="请输入内容"
              clearable
              :debounce="0"
            >
            </el-autocomplete>
          </el-form-item>
          
          <div style="float: right">
            <el-button 
              type="primary" 
              size="mini" 
              style="width: 6rem"
              @click="refreshSubruleView(true)"
            >
              搜索
            </el-button>
            <el-button
              type="danger"
              size="mini" 
              @click="reloadData"
              style="width: 6rem"
            >
              重置
            </el-button>
          </div>
        </el-form>
      </div>
    </el-card>
    <el-card class="library">
      <div slot="header" class="clearfix">
        <span>规则库管理</span>
        <el-button 
          type="primary" 
          size="mini"
          style="float: right; width: 6rem; margin: 0 10px;"
          @click="addRuleMethod"
        >
          新建规则
        </el-button>
        <el-button 
          type="primary" 
          size="mini" 
          style="float: right; width: 6rem"
          @click="exportRule('has_explanation')"
        >
          导出有注释
        </el-button>
        <el-button 
          type="primary" 
          size="mini" 
          style="float: right; width: 6rem"
          @click="exportRule('no_explanation')"
        >
          导出无注释
        </el-button>
        <el-upload 
          style="display:inline-block; margin: 0 10px;" 
          action="" 
          :show-file-list="false" 
          :http-request="importRule"
        >
          <el-button 
            type="success" 
            size="mini" 
            icon="el-icon-folder-opened"
          >
            导入
          </el-button>
        </el-upload>   
      </div>

      <div>
        <el-form 
          label-width="5rem" 
          :inline="true" 
          size="mini"
        >
          <el-form-item 
            label="缺陷" 
            prop="defect_name"
          >
            <el-autocomplete 
              v-model="methodQuery.defect_name"
              :fetch-suggestions="queryMethodDefect"
              placeholder="请输入内容"
              clearable
              @select="getPriority"
              :debounce="0"
            >
            </el-autocomplete>
          </el-form-item>

          <el-form-item 
            label="启用状态" 
            prop="enable"
          >
            <el-select 
              v-model="methodQuery.enable"
            >
              <el-option label="启用" value="1"></el-option>
              <el-option label="禁用" value="0"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item 
            label="严重程度" 
            prop="rule_explanation"
          >
            <el-select 
              v-model="methodQuery.rule_explanation"
              clearable
            >
              <el-option label="轻微" value="轻微"></el-option>
              <el-option label="中等" value="中等"></el-option>
              <el-option label="严重" value="严重"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item 
            label="修正方式" 
            prop="correction"
          >
            <el-select 
              v-model="correction"
              clearable
            >
              <el-option label="常规" value="常规"></el-option>
              <el-option label="弹窗" value="弹窗"></el-option>
            </el-select>
          </el-form-item>

          <div style="float: right">
            <el-button 
              type="primary" 
              size="mini" 
              style="width: 6rem"
              @click="refreshMethodView(true)"
            >
              搜索
            </el-button>
            <el-button 
              type="danger" 
              size="mini" 
              style="width: 6rem"
              @click="reloadMethodData"
            >
              重置
            </el-button>
          </div>
        </el-form>
      </div>

      <br />
      <div>
        <template>
          <el-table
            border
            height="350px"
            :data="methodTableData"
            v-loading="methodLoading"
          >
            <el-table-column
              type="index"
              label="序号"
              width="50"
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
                <template slot-scope="scope">
                  <div v-if="item.prop === 'operate'">
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

    <el-card  
      class="library"
      v-show="methodQuery.defect_name"
    >      
      <div slot="header" class="clearfix">
        <span>优先级</span>
      </div>
      <el-table 
        border 
        height="400px"
        :data="priorityData"
        v-loading="keywordLoading"
        :cell-style="{'padding': '1px 0px' }"
      >
        <el-table-column
          type="index"
          label="序号"
          width="50"
          align="center"
        >
        </el-table-column>
        
        <template v-for="item in priorityTable">
          <el-table-column 
            :key="item.id" 
            :prop="item.prop" 
            :label="item.label"
            :header-align="item.header_align"
            :align="item.align"
            :show-overflow-tooltip="item.tooltip"
            :min-width="item.width"
          >
            <template slot-scope="scope">
              <div v-if="item.prop === 'priority'">
                <el-input v-model="scope.row[item.prop]" @input="scope.row[item.prop]=checkNumberFormat(scope.row[item.prop])"></el-input>
              </div>
              <div v-else>
                <span>{{ scope.row[item.prop] }}</span>
              </div>
            </template>
          </el-table-column>
        </template>
      </el-table>
      <div style="text-align: center;">          
        <el-button   
          size="mini"       
          type="primary" 
          @click="confirmPriority()" 
        >
          设置优先级
        </el-button>
      </div>
    </el-card> 
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
              :fetch-suggestions="queryKeywordName"
              placeholder="请输入内容"
              :debounce="0"
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

          <el-form-item 
            label="查看全部" 
            prop="show_all"
          >
            <el-select 
              v-model="show_all"
            >
              <el-option label="全部" value="0"></el-option>
              <el-option label="仅可见" value="1"></el-option>
            </el-select>
          </el-form-item>

          <div style="float: right">
            <el-button 
              type="primary" 
              size="mini" 
              style="width: 6rem"
              @click="refreshKeywordView(true)"
            >
              搜索
            </el-button>
            <el-button 
              type="danger" 
              size="mini" 
              style="width: 6rem"
              @click="reloadKeywordData"
            >
              重置
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
            width="45"
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
              <template slot-scope="scope">
                <div v-if="item.prop === 'operate'">
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
                <div v-if="item.prop === 'show_on_page'">
                  <el-switch
                    v-model="scope.row.show_on_page"
                    @change="changeSwitch(scope.row)"
                  >
                  </el-switch>
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

    <el-dialog
      title="工艺关键词"
      :visible.sync="showKeyword"
      width="60%"
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
      width="60%"
      @closeDialog="closeMethodDialog"
    >
      <rule-method-detail
        :rule-method-id="ruleMethodId"
        :rule-method="methodFormData"
        @close-dialog="closeMethodDialog"
        :rule-type="subruleQuery.rule_type"
        :subrule_no="subruleQuery.subrule_no"
      >
      </rule-method-detail>
    </el-dialog>
  </div>
</template>

<script>
import { ruleKeywordMethod, ruleDetailMethod, getOptions, exportRuleMethod, importRuleMethod, getRuleFlowMethod} from "@/api";
import RuleKeywordDetail from './subView/ruleKeywordDetail.vue';
import RuleMethodDetail from './subView/ruleMethodDetail.vue';
import {defects_const} from "@/utils/process_const";
import { getFullReportUrl } from '@/utils/assert';

export default {
  components: { RuleKeywordDetail , RuleMethodDetail},
  data() {
    return {
      show_all: '0',
      correction: null,
      subruleQuery: {
        rule_type: null,
        subrule_no: null,
        defect_name: null,
        product_small_type: null,
        polymer_abbreviation: null,
        show_on_page: null,
        page_no: 1,
        page_size:100
      },
      keywordQuery: {
        name: null,
        keyword_type: null,
        show_on_page: null,

        page_no: 1, //当前页
        page_size: 100,//每页条数
        total: 2, //列表总条数
      },
      keywordTable: [
        { visible: true, label: "子规则库编号", prop: "subrule_no", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "是否可见", prop: "show_on_page", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "关键词定义", prop: "name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "类型", prop: "keyword_type", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "注释", prop: "comment", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模糊级别", prop: "level", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "最小取值", prop: "all_range_min", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "最大取值", prop: "all_range_max", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "调整最小值", prop: "action_range_min", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "调整最大值", prop: "action_range_max", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "调整幅度限定值", prop: "action_max_val", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "操作", prop: "operate", width: 160, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      keywordTableData:[
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
        defect_name: null,
        polymer_abbreviation: null,
        product_small_type: null,
        is_auto: null,
        enable: null,
        rule_description: null,
        rule_explanation: null,

        page_no: 1, //当前页
        page_size: 100,//每页条数
        total: 0, //列表总条数
      },
      methodTable: [
        { visible: true, label: "子规则库编号", prop: "subrule_no", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "缺陷", prop: "defect_name", width: 60, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "制品类别", prop: "product_small_type", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "塑料简称", prop: "polymer_abbreviation", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "规则描述", prop: "rule_description", width: 310, align: "left", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "规则解释", prop: "rule_explanation", width: 300, align: "left", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "状态", prop: "enable", width: 40, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "操作", prop: "operate", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      methodTableData: [
      ],
      methodLoading: false,
      showMethod: false,
      ruleMethodId: null,
      methodFormData: {
        subrule_no:null,
        polymer_abbreviation: null,
        product_small_type: null,
        preconditions: [{
          conditiontype: '缺陷前置条件',
          keyword: null,
          describe: null
        }],
        solutions: [{
          conditiontype: '结论条件',
          keyword: null,
          describe: null,
          action: null            
        }],
        rule_description: null,
        rule_explanation: null
      },
      defectOptions:defects_const,
      currentProduct:null,
      currentPolymer:null,
      priorityData:[],
      priorityTable: [
        { visible: true, label: "关键字", prop: "keyword", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "优先级(0~2 有效数字1位)", prop: "priority", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
      ],
      filteredData: [],
      defectListCache: null
    }
  },
  created() {
  },
  mounted() {
    getOptions("defect_list", []).then(res=>{
      this.defectOptions = res.data
      this.refreshSubruleView()
    })
    if (this.$route.query.subrule_no) {
      this.subruleQuery.rule_type = this.$route.query.rule_type
      this.subruleQuery.subrule_no = this.$route.query.subrule_no
      this.subruleQuery.product_small_type = this.$route.query.product_type
      this.subruleQuery.polymer_abbreviation = this.$route.query.polys_abbreviation
      // 为了导入规则时,避免手动修改制品类别和塑料简称
      this.currentPolymer = this.$route.query.polys_abbreviation
      this.currentProduct = this.$route.query.product_type
    } else if (this.$route.query.rule_type) {
      this.subruleQuery.rule_type = this.$route.query.rule_type
    }
  },
  methods: {    
    // 定义提取 THEN 后面 _ 前面字符串的函数
    extractThenAction(ruleDescription) {
      const match = ruleDescription.match(/THEN\s+([^_]+)/i);
      return match ? match[1] : null;
    },
    // 使用 map 方法遍历 filteredData 并提取所需字符串
    extractThenActionsWithPriority(filteredData) {
      return filteredData
        .map(item => {
          const ruleDescription = item.rule_description || '';
          const thenAction = this.extractThenAction(ruleDescription);
          const priority = item.priority !== undefined && item.priority !== null ? item.priority : 1;
          return thenAction !== null ? { keyword: thenAction, priority: priority } : null;
        })
        .filter(item => item !== null); // 过滤掉无效条目
    },
    async getPriority(){
      if(this.subruleQuery.subrule_no){
        this.subruleQuery.rule_type = "子规则库"
      }
      await this.refreshSubruleView()
      this.filteredData = this.methodTableData.filter(item => item.defect_name === this.methodQuery.defect_name);
      const thenActionsWithPriority =this.extractThenActionsWithPriority(this.filteredData);
      this.priorityData = Array.from(
        new Map(thenActionsWithPriority.map(item => [item.keyword, item]))
      ).map(([_, value]) => value);
    },
    async confirmPriority(){
      this.keywordLoading = true
      for(let i=0;i<this.filteredData.length;i++){
        const item = this.filteredData[i];
        const keyword = this.extractThenAction(item.rule_description)

        // 查找 priorityData 中具有相同 keyword 的项
        const priorityItem = this.priorityData.find(p => p.keyword === keyword);

        // 如果没有找到对应项或 priority 不一致，则打印消息
        if (!item.priority || priorityItem.priority !== item.priority) {
          this.filteredData[i].priority = priorityItem.priority
          await ruleDetailMethod.edit(this.filteredData[i], item.id).then(res => {
          })
        }        
      }
      this.keywordLoading = false
      this.$message({ message: '优先级设置成功', type: 'success' })
    },
    exportRule(flag){
      if (!this.subruleQuery.subrule_no) {
        this.$message('请选择要导出的子规则库编号')
        return
      }
      this.$confirm(`确认导出以下子规则库？\r\n ${ this.subruleQuery.subrule_no }`, "导出子规则库", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        exportRuleMethod({flag:flag, subrule_no:this.subruleQuery.subrule_no})
        .then(res => {
          if(res.status === 0 && res.data.url) {
            this.$message({ message: '导出成功。', type: 'success' })
            window.location.href = getFullReportUrl(res.data.url)
          }
        })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消导出！"
        })
      })
    },
    importRule(data){
      if (!this.subruleQuery.subrule_no) {
        this.$message('请选择要导入的子规则库编号')
        return
      }
      let message=`这些规则将被导入到${this.subruleQuery.subrule_no},`
      if(this.currentProduct){
        message+=`对应制品${this.currentProduct},`
      }
      if(this.currentPolymer){
        message+=`塑料简称${this.currentPolymer},`
      } 
      this.$confirm(`这些规则将被导入到${this.subruleQuery.subrule_no},对应制品${this.currentProduct},塑料简称${this.currentPolymer},确认导入么？`, '导入规则', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }).then(() => {
        let params = new FormData()
        params.append('file', data.file)
        params.append('subrule_no', this.subruleQuery.subrule_no)
        params.append('product_small_type', this.currentProduct)
        params.append('polymer_abbreviation', this.currentPolymer)
  
        importRuleMethod(params).then(res => {
          this.$message({
            message: `导入成功。<br><br>${res.data.message}`,
            type: 'success',
            dangerouslyUseHTMLString: true // 允许使用 HTML 字符串
          });
        })
        return 0
      })
    },
    queryKeywordName(str, cb) {
      str = (str == null ? "" : str)
      let promptList = []
      getOptions("name", { "form_input": str, "db_table": "rule_keyword" })
      .then( res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({ value: res.data[i] })
          }
        }
      })
      cb(promptList)
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
    queryMethodDefect(str, cb) {
      str = str == null ? "" : str
      // 如果缓存存在且搜索字符串为空或与缓存匹配，则直接使用缓存
      if (this.defectListCache && (str === "" || this.defectListCache.some(item => item.value.includes(str)))) {
        return cb(this.defectListCache);
      }
      let promptList = []
      getOptions("defect_name", { "form_input": str, "db_table": "rule_method" })
      .then(res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; i++) {
            promptList.push({value: res.data[i]})
          }
          this.defectListCache = promptList
        } else {
          this.defectListCache = null
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
      getOptions("polymer_abbreviation", { "form_input": str, "db_table": "polymer" })
      .then( res => {
        if (res.status === 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({ value: res.data[i].value })
          }
        }
      })
      cb(promptList)
    },
    addRuleKeyword() {
      this.showKeyword = true;
    },
    closeKeywordDialog() {
      this.showKeyword = false;
      this.refreshKeywordView()
    },
    editKeyword(row) {
      this.keywordFormData = row
      this.ruleKeywordId = row.id
      this.showKeyword = true;
    },
    deleteKeyword(row) {
      this.$confirm(`确定要删除这条规则关键词么？`, '删除规则关键词', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
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
      this.methodFormData = {
        subrule_no: this.subruleQuery.subrule_no,
        product_small_type: this.subruleQuery.product_small_type,
        polymer_abbreviation: this.subruleQuery.polymer_abbreviation,
        preconditions: [{
          conditiontype: '缺陷前置条件',
          keyword: null,
          describe: null
        }],
        solutions: [{
          conditiontype: '结论条件',
          keyword: null,
          describe: null,
          action: null            
        }],
        rule_description: null,
        rule_explanation: null
      }
      this.showMethod = true;
    },
    closeMethodDialog() {
      this.showMethod = false;
      this.refreshMethodView()
    },
    ruleTransferForm(rule_description) {
      let section_list = rule_description.trim().split(" ")
      let resolve_step = 0
      let defect_list = this.defectOptions.map(defect => defect.desc)
      this.methodFormData.preconditions.length = 0
      this.methodFormData.solutions.length = 0

      for (let i = 0; i < section_list.length; ++i) {
        if (section_list[i] === 'IF') {
          resolve_step = 1
        } else if (section_list[i] === 'Then' || section_list[i] === 'THEN') {
          resolve_step = 2
        } else if (section_list[i] == 'AND') {
          continue
        } else {
          let words = section_list[i].split('_')
          if (resolve_step === 1) {
            if (defect_list.indexOf(words[0]) === -1) {
              this.methodFormData.preconditions.push({
                conditiontype: '普通前置条件',
                keyword: words[0],
                describe: words[1]
              })
            } else {
              this.methodFormData.preconditions.push({
                conditiontype: '缺陷前置条件',
                keyword: words[0],
                describe: words[1]
              })
            }
          } else if (resolve_step === 2) {
            if (words.length === 2) {
              this.methodFormData.solutions.push({
                conditiontype: '结论条件',
                keyword: words[0],
                describe: words[1]
              })
            } else if (words.length === 3) {
              this.methodFormData.solutions.push({
                conditiontype: '结论条件',
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
      this.methodFormData.subrule_no = row.subrule_no
      this.methodFormData.product_small_type = row.product_small_type
      this.methodFormData.polymer_abbreviation = row.polymer_abbreviation
      this.methodFormData.rule_explanation = row.rule_explanation
      this.ruleMethodId = row.id
      this.showMethod = true;
    },
    deleteRuleMethod(row) {
      this.$confirm(`确定要删除这条规则么？`, '删除规则', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }).then(() => {
        ruleDetailMethod.delete(row.id)
        .then(res => {
          this.refreshMethodView() 
        })
      })
    },
    updateRuleMethodEnable(id, enable) {
      let swt = enable === 1 ? 0 : 1
      this.$confirm(swt === 0 ? `确定禁用当前规则？` : `确定启用当前规则？`, '提示', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning',
      }).then(() => {
        ruleDetailMethod.edit({
          enable: swt
        }, id).then(res => {
          if (res.status === 0) {
            this.$message({
              type: 'success',
              message: swt === 0 ? '已禁用当前规则！' : '已启用当前规则！'
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
    async refreshKeywordView(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      try {
        this.keywordLoading = true;

        if (this.show_all === "0") {
          this.keywordQuery.show_on_page = null; // 全部
        } else if (this.show_all === "1") {
          this.keywordQuery.show_on_page = 1; // 仅可见
        }

        const query = {
          rule_type: this.subruleQuery.rule_type,
          subrule_no: this.subruleQuery.subrule_no,
          product_small_type: this.subruleQuery.product_small_type,
          polymer_abbreviation: this.subruleQuery.polymer_abbreviation,
          name: this.keywordQuery.name,
          keyword_type: this.keywordQuery.keyword_type,
          show_on_page: this.keywordQuery.show_on_page,
          page_no: this.keywordQuery.page_no,
          page_size: this.keywordQuery.page_size
        };

        // 使用 await 等待 API 请求完成
        const res = await ruleKeywordMethod.get(query);

        if (res.status === 0) {
          this.keywordTableData = res.data.items;
          this.keywordQuery.total = res.data.total;
        }
      } catch (error) {
        console.error('Error fetching keyword view:', error);
        throw error; // 可选：重新抛出错误以便调用者可以处理
      } finally {
        this.keywordLoading = false;
      }
    },
    async refreshMethodView(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      try {
        this.methodLoading = true;

        if (this.correction === "常规") {
          this.methodQuery.rule_description = 'add';
        } else if (this.correction === "弹窗") {
          this.methodQuery.rule_description = 'adjust';
        } else {
          this.methodQuery.rule_description = null;
        }

        const query = {
          rule_type: this.subruleQuery.rule_type,
          subrule_no: this.subruleQuery.subrule_no,
          product_small_type: this.subruleQuery.product_small_type,
          polymer_abbreviation: this.subruleQuery.polymer_abbreviation,
          defect_name: this.methodQuery.defect_name,
          enable: this.methodQuery.enable,
          is_auto: this.methodQuery.is_auto,
          rule_description: this.methodQuery.rule_description,
          rule_explanation: this.methodQuery.rule_explanation,
          page_no: this.methodQuery.page_no,
          page_size: this.methodQuery.page_size
        };

        // 使用 await 等待 API 请求完成
        const res = await ruleDetailMethod.get(query);
        if (res.status === 0) {
          this.$set(this, 'methodTableData', res.data.items);
          this.methodQuery.total = res.data.total;
          if(this.methodTableData.length>0){
            this.subruleQuery.polymer_abbreviation = this.methodTableData[0].polymer_abbreviation
            this.subruleQuery.product_small_type = this.methodTableData[0].product_small_type
            // 在导入规则的时候,避免制品类别和塑料简称被手动修改,此处保存下来
            this.currentPolymer = this.methodTableData[0].polymer_abbreviation
            this.currentProduct = this.methodTableData[0].product_small_type
          }
        }
      } catch (error) {
        console.error('Error fetching method view:', error);
        throw error; // 可选：重新抛出错误以便调用者可以处理
      } finally {
        this.methodLoading = false;
      }
    },
    async refreshSubruleView(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      this.methodLoading = true;
      this.keywordLoading = true;

      try {
        await this.refreshMethodView();
        await this.refreshKeywordView();
      } catch (error) {
        console.error('Error refreshing subrule view:', error);
      } finally {
        this.methodLoading = false;
        this.keywordLoading = false;
      }
    },
    changeSwitch(row) {
      // 全部关键字有100多个,实际子规则库用到的只有一少部分,只显示用到的这些关键字
      ruleKeywordMethod.edit({
        "show_on_page": row.show_on_page
      }, row.id).then(res => {
        if (res.status === 0) {
          this.$message({message:"可见状态修改成功!", type: 'success'})
        }
      })
    },
    reloadData() {
      this.subruleQuery = {
        rule_type: null,
        subrule_no: null,
        product_small_type: null,
        polymer_abbreviation: null,
        page_size:100,
        page_no:1
      }
      this.refreshSubruleView(true)
    },
    reloadMethodData() {
      this.methodQuery = {
        defect_name: null,
        polymer_abbreviation: null,
        product_small_type: null,
        is_auto: null,
        enable: null,
        rule_description: null,
        rule_explanation: null,
        page_size:100,
        page_no:1
      }
      this.correction = null
      this.refreshMethodView(true)
    },
    reloadKeywordData() {
      this.keywordQuery = {
        name: null,
        keyword_type: null,
        show_on_page: null,
        page_size:100,
        page_no:1
      }
      this.show_all = '0'
      this.refreshKeywordView(true)
    }
  },
  watch:{
  }
}
</script>

<style lang="scss" scoped>
  .el-input {
    width: 9rem
  }
  .el-select {
    width: 8rem
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
  .el-autocomplete {
    width: 9rem;
  }
</style>