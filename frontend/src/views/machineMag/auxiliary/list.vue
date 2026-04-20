<template>
  <div>
    <query-auxiliary-list
      ref="queryAuxiliaryList"
      :query-detail="query"
      @queryStart="listLoading = true"
      @queryFinish="onQueryFinish"
    >
    </query-auxiliary-list>
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
        <!-- <el-button-group> -->
        <el-button
          type="primary"
          size="mini"
          icon="el-icon-plus"
          @click="addAuxiliary"
          :disabled="!$store.state.user.userinfo.permissions.includes('add_machine')"
        >
          添加辅机
        </el-button>
        <el-button
          type="danger"
          size="mini"
          icon="el-icon-delete"
          @click="deleteAuxiliary"
          style="margin: 0"
          :disabled="!$store.state.user.userinfo.permissions.includes('delete_machine')"
        >
          删除辅机
        </el-button>
        <el-button
          size="mini"
          type="primary"
          @click="setTableView"
          icon="el-icon-setting"
          style="margin: 0"
        >
          配置表格
        </el-button>
      </div>
      <div style="height: 8px" />
      <el-table
        v-loading="listLoading"
        size="mini"
        stripe
        border
        fit
        highlight-current-row
        :height="tableHeight"
        :row-style="tableRowStyle"
        :cell-style="tableCellStyle"
        :header-cell-style="tableHeaderStyle"
        :data="listData.items"
        @sort-change="sortList"
        @row-dblclick="rowDoubleClicked"
        @selection-change="handleSelectionChange"
      >
        <el-table-column
          type="selection"
          width="40"
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
              <div v-if="column.prop === 'auxiliary_type'">
                <el-button 
                  type="text" 
                  size="mini"            
                  @click="editMachine(scope.row)"
                >
                  {{ scope.row[column.prop] }}
                </el-button>
              </div>
              <div v-else>
                {{ scope.row[column.prop] }}
              </div>
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
      <auxiliary-detail
        :id="auxiliary_detail.id"
        :view-type="viewType"
        :show-update.sync="showAuxiliaryDetail"
        @close="refreshView"
      >
      </auxiliary-detail>
      <table-setting
        :table-data="columns_setting"
        :show-dialog.sync="showTableSetting"
        @close="refreshTable"
      >
      </table-setting>
    </div>
  </div>
</template>

<script>
import { auxiliaryMethod } from '@/api';
import { AppModule } from '@/store/modules/app';
import { UserModule } from '@/store/modules/user';
import QueryAuxiliaryList from './subView/queryAuxiliaryList.vue';
import AuxiliaryDetail from './detail.vue';
import TableSetting from "@/components/tableSetting/tableSetting";

export default {
  components: { QueryAuxiliaryList, AuxiliaryDetail, TableSetting },
  data() {
    return {
      query: {
        company_id: UserModule.company_id,

        auxiliary_type: "",
        serial_no: "",

        page_no: 1,
        page_size: 100
      },
      auxiliary_detail: {
        id: null
      },
      viewType: null,
      listData: {},
      listLoading: false,
      multipleSelection: [],
      columns_setting: [
        { visible: true, label: "辅机品牌", prop: "manufacture", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "辅机型号", prop: "auxiliary_trademark", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "辅机类型", prop: "auxiliary_type", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "设备编码", prop: "serial_num", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "注塑机来源", prop: "machine_data_source", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "注塑机型号", prop: "machine_trademark", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        // { visible: true, label: "出厂日期", prop: "manufacture_date", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false}, 
      ],
      tableHeaderStyle: { 'background-color': 'lightblue', 'color': '#000', 'font-size': '12px', 'padding': '10px 0px' },
      tableRowStyle: { },
      tableCellStyle: { 'padding': '7px 0px' },
      tableHeight: "45rem",
      showAuxiliaryDetail: false,
      showTableSetting: false, // 显示表格设置界面
    }
  },
  created() {
    this.loadViewSetting()
  },
  mounted() {
    this.getListData()
  },
  methods: {
    loadViewSetting() {
      let custom_setting = AppModule.customSetting
      if(custom_setting && custom_setting.aux_list_columns_setting) {
        if (custom_setting.id == UserModule.id) {
          this.columns_setting = custom_setting.aux_list_columns_setting
        }
      }
    },
    getListData() {
      this.$refs.queryAuxiliaryList.queryListData()
    },
    onQueryFinish(auxiliaryList) {
      this.listData = auxiliaryList
      this.listLoading = false
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
    addAuxiliary() {
      this.$router.push('/machine/auxiliary/create')
    },
    deleteAuxiliary() {
      if (this.multipleSelection.length == 0) {
        this.$message('无选中项。');
        return
      }

      let delete_auxiliary = ""
      let auxiliary_trademark_list = []
      let auxiliary_id_list = []
      for (let i = 0; i < this.multipleSelection.length; ++i) {
        auxiliary_trademark_list.push(this.multipleSelection[i].auxiliary_trademark)
        auxiliary_id_list.push(this.multipleSelection[i].id)
      }
      delete_auxiliary = auxiliary_trademark_list.join("、")

      this.$confirm(`确认删除以下辅机？\r\n ${ delete_auxiliary }`, '删除辅机', {
        confirmButtonText: '确定',        
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        auxiliaryMethod.multipleDel({
        "auxiliary_id_list": auxiliary_id_list
        }).then(res => {
          if(res.status === 0){
            this.$message({ type: 'success', message: '删除成功!' })
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
      this.showTableSetting = true
    },
    refreshTable() {
      this.auxiliary_detail.id = null
      this.viewType = null
      this.showTableSetting = false

      this.getListData()
    },
    sortList(sort) {
      this.query.$orderby = sort.prop
      this.listLoading = true
      this.getListData()
    },
    handleSelectionChange(val) {
      this.multipleSelection = val;
    },
    editMachine(row) {
      this.auxiliary_detail.id = row.id
      this.viewType = "edit"
      this.showAuxiliaryDetail = true
    },
    rowDoubleClicked(row) {
      this.editMachine(row)
    },
    refreshView() {
      this.auxiliary_detail.id = null
      this.viewType = null
      this.showAuxiliaryDetail = false

      this.getListData()
    },
    handleSizeChange(val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange(val) {
      this.query.page_no = val
      this.getListData()
    },
  },
  watch: {
    "columns_setting": {
      handler: function() {
        let custom_setting = AppModule.customSetting
        custom_setting.user_id = UserModule.id
        custom_setting.aux_list_columns_setting = this.columns_setting
        localStorage.setItem("custom_setting", JSON.stringify(custom_setting))
      },
      deep: true
    },
  }
}
</script>

<style>
</style>