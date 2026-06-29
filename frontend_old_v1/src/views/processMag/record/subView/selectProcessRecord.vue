<template>
  <div>
    <query-record-list
      ref="queryRecordList"
      :query-detail="query"
      @queryStart="listLoading = true"
      @queryFinish="onQueryFinish"
    >
    </query-record-list>
    <el-table
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
    >
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
            <span v-if="column.prop === 'process_no'">
              <el-link
                type="primary"
                @click="editProcessRecord(scope.row)"
              >
                {{ scope.row[column.prop] }}
              </el-link>
            </span>
            <span v-else-if="column.prop === 'process'">
              <el-link
                type="success"
                @click="loadProcessRecord(scope.row)"
              >
                读取
              </el-link>
            </span>
            <span v-else-if="column.prop === 'machine_adaption'">
              <el-link
                type="success"
                @click="checkMachineAdaption(scope.row)"
              >
                <span v-if="scope.row.machine_adaption.length>0">
                  查看
                </span>
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
    <process-record-detail
      :id="process_detail.id"
      :view-type="viewType"
      :show-update.sync="showProcessRecordDetail"
      @close="refreshView"
    >
    </process-record-detail>
  </div>
</template>

<script>
import { UserModule } from '@/store/modules/user';
import { dateToday } from '@/utils/datetime';
import QueryRecordList from "./queryRecordList.vue";
import ProcessRecordDetail from "../detail.vue";

export default {
  name: "SelectProcessRecord",
  components: { QueryRecordList, ProcessRecordDetail },
  data() {
    return {
      query: {
        company_id: UserModule.company_id,
        status: 2,

        mold_no: null,
        gate_type: null,
        product_type: null,
        product_name: null,
        machine_data_source: null,
        machine_trademark: null,
        start_date: null,
        end_date: null,

        page_no: 1 ,
        page_size: 100,
      },
      process_detail: {
        id: null,
      },
      viewType: null,
      listData: {},
      listLoading: false,
      columns_setting: [
        { visible: true, label: "模具编号", prop: "mold_no", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "工艺编号", prop: "process_no", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "数据来源", prop: "data_sources", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "工艺参数", prop: "process", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "注塑机来源", prop: "machine_data_source", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "注塑机型号", prop: "machine_trademark", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "制品类别", prop: "product_type", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品名称", prop: "product_name", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料缩写", prop: "polymer_abbreviation", width: 80, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "塑料牌号", prop: "polymer_trademark", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "创建日期", prop: "created_at", width: 130, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
      tableHeaderStyle: { 'background-color': 'lightblue', 'color': '#000', 'font-size': '12px', 'padding': '10px 0px' },
      tableRowStyle: { },
      tableCellStyle: { 'padding': '7px 0px' },
      tableHeight: '15rem',
      showProcessRecordDetail: false,
    }
  },
  mounted() {
    this.getListData()
  },
  methods: {
    getListData() {
      this.$refs.queryRecordList.queryListData()
    },
    onQueryFinish(recordList) {
      this.listData = recordList
      this.listLoading = false
    },
    loadProcessRecord(row) {
      this.$emit("select-process", row.id)
    },
    editProcessRecord(row) {
      this.process_detail.id = row.id
      this.viewType = "edit"
      this.showProcessRecordDetail = true
    },
    refreshView() {
      this.process_detail.id = null
      this.viewType = null
      this.showProcessRecordDetail = false

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
    checkMachineAdaption(row){
      this.$router.push({
        path:"/process/record/adaptation",
        query:{
          process_id: row.id,
        }
      })
    }
  },
}
</script>

<style>

</style>

