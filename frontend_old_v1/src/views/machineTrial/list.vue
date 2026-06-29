<template>
  <div>
    <div class="search">
      <el-form
        :inline="true"
        :model="query"
        size="mini"
        label-width="8rem"
      >
        <el-form-item 
          label="注塑机来源"
          prop="data_source"
        >
          <el-autocomplete
            v-model="query.data_source"
            placeholder="注塑机来源"
            clearable
            style="width:10rem"
            :fetch-suggestions="queryMacDataSourceList"
            @select="handleMacDataSourceSelect"
          >
          </el-autocomplete>
        </el-form-item>

        <el-form-item 
          label="注塑机型号"
          prop="machine_trademark"
        >
          <el-autocomplete
            v-model="query.machine_trademark"
            placeholder="注塑机型号"
            clearable
            style="width:10rem"
            :fetch-suggestions="queryMacTrademarkList"
          >
          </el-autocomplete>
        </el-form-item>

        <el-form-item 
          label="测试类别"
          prop="machine_trial_type"
        >
          <el-select
            v-model="query.machine_trial_type"
            placeholder="测试类别"
            clearable
            style="width:10rem"
          >
            <el-option
              v-for="item, index in macTrialTypeOptions"
              :key="index"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="测试日期">
          <el-date-picker
            v-model="query.trial_start_date"
            value-format="yyyy-MM-dd"
            type="date"
            placeholder="开始日期"
            style="width:10rem"
          >
          </el-date-picker>
          <span>-</span>
          <el-date-picker
            v-model="query.trial_end_date"
            value-format="yyyy-MM-dd"
            type="date"
            placeholder="结束日期"
            style="width:10rem"
          >
          </el-date-picker>
        </el-form-item>

        <el-form-item style="float:right">
          <el-button
            type="primary"
            style="width: 6rem; margin-left:10px"
            @click="queryListData(true)"
          >
            搜索
          </el-button>
          <el-button 
            type="danger" 
            style="width: 6rem"
            @click="reloadListData" 
          >
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    <div class="row-toolbutton">
      <div style="float:left">
        <el-button-group>
          <el-button
            size="mini"
            @click="changeTableSize('small')"
          >
            small
          </el-button>
          <el-button
            size="mini"
            @click="changeTableSize('normal')"
          >
            normal
          </el-button>
          <el-button
            size="mini"
            @click="changeTableSize('large')"
          >
            large
          </el-button>
        </el-button-group>
      </div>
      <div style="float:right">
        <el-button-group>
          <el-button
            type="danger"
            size="mini"
            icon="el-icon-delete"
            @click="deleteMachineTrial"
            style="margin: 0"
          >
            删除测试
          </el-button>
          <el-button
            size="mini"
            type="primary"
            icon="el-icon-setting"
            @click="setTableView"
          >
            配置表格
          </el-button>
        </el-button-group>
      </div>
    </div>
    <div style="height: 8px" />
    <el-table
      ref="reservationTable"
      v-loading="listLoading"
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      style="width: 100%"
      :data="listData.items"
      :height="tableHeight"
      :row-style="tableRowStyle"
      :cell-style="tableCellStyle"
      :header-cell-style="tableHeaderStyle"
      @sort-change="sortList"
      @row-dblclick="rowDoubleClicked"
      @selection-change="handleSelectionChange"
    >
      <el-table-column
        type="selection"
        width="40"
        align="center"
        :selectable="setRowSelectable"
      >
      </el-table-column>
      <el-table-column
        type="index"
        label="序号"
        width="45"
        align="center"
      >
      </el-table-column>
      <template v-for="column, index in columns_setting">
        <el-table-column
          v-if="column.visible"
          :key="index"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.width"
          :header-align="column.header_align"
          :align="column.align"
          :sortable="column.sortable"
          :show-overflow-tooltip="column.tooltip"
        >
          <template slot-scope="scope">
            <span v-if="column.prop === 'created_at'">
              {{ scope.row.created_at === null ? null : scope.row.created_at.slice(0, 10) }}
            </span>
            <span v-else-if="column.prop == 'machine_trial_type'">
              {{ scope.row.machine_trial_type === null ? null : macTrialTypeMap[scope.row.machine_trial_type] }}
            </span>
            <span 
              v-else-if="column.prop === 'review'"
            >
              <el-link 
                type="primary"
                size="mini"
                @click="editMachineTrial(scope.row)"
              >
                查看
              </el-link>
            </span>
            <span 
              v-else-if="column.prop === 'report'"
            >
              <el-link 
                type="primary"
                size="mini"
                @click="generateReport(scope.row)"
              >
                报告
              </el-link>
            </span>
            <span v-else>
              {{ scope.row[column.prop] }}
            </span>
          </template>
        </el-table-column>
      </template>
    </el-table>
    <div class="pagination">
      <el-pagination
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="query.page_no"
        :page-sizes="$store.state.app.pageSizeArray"
        :page-size="query.page_size"
        :total="listData.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
    <machine-trial-detail
      :id="machine_trial_detail.id"
      :trial-type="trialType"
      :show-update.sync="showMachineTrialDetail"
      @close="refreshView"
    >
    </machine-trial-detail>
    <table-setting
      :table-data="columns_setting"
      :show-dialog.sync="showTableSetting"
      @close="refreshTable"
    >
    </table-setting>
  </div>
</template>

<script>
import { machineTrialsMethod, exportMachineTrialReport, getOptions } from '@/api'
import { AppModule } from '@/store/modules/app'
import { UserModule } from '@/store/modules/user'
import MachineTrialDetail from "./detail.vue"
import TableSetting from "@/components/tableSetting/tableSetting"
import { getFullReportUrl } from '@/utils/assert'
export default {
  name: "MachineTrialList",
  components: { MachineTrialDetail, TableSetting },
  data() {
    return {
      query: {
        company_id: UserModule.company_id,

        data_source: null,
        machine_trademark: null,
        machine_trial_type: null,
        trial_start_date: null,
        trial_end_date: null,

        page_no: 1,
        page_size: 100,
      },
      machine_trial_detail: {
        id: null
      },
      listData: {
        items: [],
        total: 0
      },
      listLoading: false,
      multipleSelection: [],
      columns_setting: [
        { visible: true, label: "测试类别", prop: "machine_trial_type", width: 150, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "查看详情", prop: "review", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "查看报告", prop: "report", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "注塑机型号", prop: "machine_trademark", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "模具编号", prop: "mold_no", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "制品名称", prop: "product_name", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "塑料", prop: "polymer_abbreviation", width: 80, align: "center", header_align: "center", sortable: false, tooltip: true}, 
        { visible: true, label: "测试日期", prop: "created_at", width: 130, align: "center", header_align: "center", sortable: false, tooltip: false}, 
      ],
      tableHeaderStyle: { 'background-color': 'lightblue', 'color': '#000', 'font-size': '12px', 'padding': '10px 0px' },
      tableRowStyle: { },
      tableCellStyle: { 'padding': '7px 0px' },
      tableHeight: '45rem',
      trialType: null,
      showMachineTrialDetail: false,
      showTableSetting: false, // 显示表格设置界面
      macTrialTypeOptions: [
        { label: "载荷敏感度测试", value: "load_sensitivity" },
        { label: "动态止逆环测试", value: "check_ring_dynamic" },
        { label: "静态止逆环测试", value: "check_ring_static" },
        { label: "注射速度线性测试", value: "inject_velocity_linearity" },
        { label: "稳定性评估测试", value: "stability_assessment" },
        { label: "模板变形测试", value: "mould_board_deflection" },
        { label: "螺杆磨损测试", value: "screw_wear" }
      ],
      macTrialTypeMap: {
        "load_sensitivity": "载荷敏感度测试",
        "check_ring_dynamic": "动态止逆环测试",
        "check_ring_static": "静态止逆环测试",
        "inject_velocity_linearity": "注射速度线性测试",
        "stability_assessment": "稳定性评估测试",
        "mould_board_deflection": "模板变形测试",
        "screw_wear":"螺杆磨损测试"
      },
      mac_data_source_list: [],
      mac_trademark_list: [],
    }
  },
  created() {
    this.loadViewSetting()
    getOptions("machine_data_source", {})
    .then(res => {
      if(res.status === 0) {
        this.mac_data_source_list.length = 0
        for (let i = 0; i < res.data.length; i++) {
          this.mac_data_source_list.push({"value": res.data[i].value})
        }
      }
    })
  },
  mounted() {
    this.queryListData()
  },
  methods: {
    loadViewSetting() {
      let custom_setting = AppModule.customSetting
      if (custom_setting && custom_setting.machine_trial_list_columns_setting) {
        if (custom_setting.id == UserModule.id) {
          this.columns_setting = custom_setting.machine_trial_list_columns_setting
        }
      }
    },
    queryMacDataSourceList(queryString, cb) {
      var mac_data_source_list = this.mac_data_source_list;
      var results = queryString ? mac_data_source_list.filter(this.createStateFilter(queryString)) : mac_data_source_list;
      cb(results);
    },
    queryMacTrademarkList(queryString, cb) {
      var mac_trademark_list = this.mac_trademark_list;
      var results = queryString ? mac_trademark_list.filter(this.createStateFilter(queryString)) : mac_trademark_list;
      cb(results);
    },
    createStateFilter(queryString) {
      return (state) => {
        return (state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
      };
    },
    handleMacDataSourceSelect(item) {
      getOptions("machine_trademark", {"data_source": this.query.data_source})
      .then(res => {
        if (res.status === 0 && Array.isArray(res.data)) {
          this.mac_trademark_list.length = 0
          for (let i = 0; i < res.data.length; i++) {
            this.mac_trademark_list.push({"id": res.data[i].id, "value": res.data[i].trademark})
          }
        }
      })
    },
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      machineTrialsMethod.get(this.query)
      .then(res => {
        if (res.status == 0) {
          this.listData = res.data
        }
      })
    },
    reloadListData() {
      this.query.data_source = null
      this.query.machine_trademark = null
      this.query.machine_trial_type = null
      this.query.trial_start_date = null
      this.query.trial_end_date = null

      this.queryListData(true)
    },
    getListData() {
      this.queryListData()
    },
    changeTableSize(size) {
      if (size === "small") {
        this.tableCellStyle = { 'padding': '1px 0px' }
      } else if (size === "normal") {
        this.tableCellStyle = { 'padding': '7px 0px' }
      } else if (size === "large") {
        this.tableCellStyle = { 'padding': '12px 0px' }
      } else {
        ;
      }
    },
    deleteMachineTrial() {
      if (this.multipleSelection.length == 0) {
        this.$message('无选中项！')
        return
      }

      let machine_trial_id_list = []
      for (let i = 0; i < this.multipleSelection.length; i++) {
        machine_trial_id_list.push(this.multipleSelection[i].id)
      }

      this.$confirm(`确认删除测试？`,"删除测试",{
        confirmButtonText: "确定",
        concelButtonTest: "取消",
        type: "warning",
      }).then(() => {
        machineTrialsMethod.multipleDel({
          "machine_trial_id_list":machine_trial_id_list
        }).then((res) => {
          if(res.status === 0) {
            this.$message({type: "success",message: "删除成功!"})
            this.getListData()
          }
        })
      }).catch(() => {
        this.$message({
          type: 'info',
          message: '已取消删除'
        })
      })
    },
    setTableView() {
      this.showTableSetting = true;
    },
    refreshTable() {
      this.machine_trial_detail.id = null,
      this.trialType = null
      this.showTableSetting = false

      this.getListData()
    },
    sortList(sort) {
      this.query.$orderby = sort.prop
      this.getListData()
    },
    setRowSelectable(row, index) {
      return true
    },
    handleSelectionChange(val) {
      this.multipleSelection = val;
    },
    editMachineTrial(row) {
      this.machine_trial_detail.id = row.id
      this.trialType = row.machine_trial_type
      this.showMachineTrialDetail = true
    },
    rowDoubleClicked(row) {
      this.editMachineTrial(row)
    },
    refreshView() {
      this.machine_trial_detail.id = null
      this.trialType = null
      this.showMachineTrialDetail = false

      this.getListData()
    },
    handleSizeChange(val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange (val) {
      this.query.page_no = val
      this.getListData()
    },
    generateReport(row){
      this.loading = true
      exportMachineTrialReport({
        "machine_trial_id": row.id,
      }).then(res => {
        if (res.status === 0) {
          this.$message({message:'报告生成成功!',type:'success'});
          window.location.href = getFullReportUrl(res.data.url)
        }
      }).finally(() => {
        this.loading = false
      });
    },
  },
  watch: {
    "columns_setting": {
      handler: function() {
        let custom_setting = AppModule.customSetting
        custom_setting.user_id = UserModule.id
        custom_setting.machine_trial_list_columns_setting = this.columns_setting
        localStorage.setItem("custom_setting", JSON.stringify(custom_setting))
      },
      deep: true
    },
  }
}
</script>

<style>

</style>