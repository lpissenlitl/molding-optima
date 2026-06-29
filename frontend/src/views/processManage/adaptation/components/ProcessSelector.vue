<template>
  <div>
    <process-search-form
      :query-detail="query"
      @search="getListData"
    />
    <el-table
      v-loading="list_loading"
      size="mini"
      stripe
      border
      fit
      highlight-current-row
      style="width: 100%"
      height="320px"
      :data="list_data.items"
    >
      <el-table-column
        type="index"
        label="序号"
        width="55"
        align="center"
      >
      </el-table-column>
      <template v-for="column, index in table_columns">
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
          <template #default="scope">
            <span v-if="column.prop === 'process'">
              <el-link
                type="success"
                @click="$emit('select-process', scope.row.id)"
              >
                读取
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
        :total="list_data.total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      >
      </el-pagination>
    </div>
  </div>
</template>

<script>
import ProcessSearchForm from "./ProcessSearchForm.vue"
import { processParameterMethod } from "@/api"

export default {
  name: "SelectProcessRecord",
  components: { ProcessSearchForm },
  data() {
    return {
      query: {
        origin_type: "manual_creation",
        status: null,
        mold_no: null,
        machine_model: null,
        polymer_abbreviation: null,
        start_date: null,
        end_date: null,

        page_no: 1 ,
        page_size: 100,
      },
      list_data: {},
      list_loading: false,
      selected_rows: [],
      view_context: {
        id: null,
        is_dialog: null,
        dialog_title: null,
        mode: null,
        excel_data: null,
      },
      table_columns: [
        { visible: true, label: "工艺编号", prop: "condition_code", width: 240, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "读取", prop: "process", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具编号", prop: "mold_no", width: 160, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具名称", prop: "mold_name", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模具类别", prop: "mold_type", width: 110, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "模腔布局", prop: "cavity_layout", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false }, 
        { visible: true, label: "制品类别", prop: "product_category", width: 120, align: "center", header_align: "center", sortable: false, tooltip: false },
        { visible: true, label: "注塑机品牌", prop: "machine_brand", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机型号", prop: "machine_model", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "注塑机编号", prop: "machine_device_code", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料简称", prop: "polymer_abbreviation", width: 120, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "塑料牌号", prop: "polymer_grade", width: 150, align: "center", header_align: "center", sortable: false, tooltip: true }, 
        { visible: true, label: "创建日期", prop: "created_at", width: 170, align: "center", header_align: "center", sortable: false, tooltip: false }, 
      ],
    }
  },
  mounted() {
    this.getListData()
  },
  methods: {
    async getListData() {
      this.list_loading = true
      const res = await processParameterMethod.get(this.query)
      if (res.status === 0) {
        this.list_data = res.data
      }
      this.list_loading = false
    },
    handleSizeChange(val) {
      this.query.page_size = val
      this.getListData()
    },
    handleCurrentChange(val) {
      this.query.page_no = val
      this.getListData()
    },
    refreshView() {
      this.view_context = {
        id: null,
        is_dialog: null,
        dialog_title: null,
        mode: null,
        excel_data: null,
      }

      this.getListData()
    }
  },
}
</script>

<style lang="scss" scoped>

</style>

