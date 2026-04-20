<template>
  <div>
    <div class="search">
      <el-form
        :inline="true"
        size="mini"
        label-width="8rem"
      >
        <el-form-item
          label="模流分析编号"
          prop="mold_flow_no"
        >
          <el-autocomplete
            v-model="query.mold_flow_no"
            :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'mold_flow_no')})"
            placeholder="请输入内容"
            suffix-icon="el-icon-search"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item
          label="分析序列"
          prop="analytical_sequence"
        >
          <el-autocomplete
            v-model="query.analytical_sequence"
            :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'analytical_sequence')})"
            placeholder="请输入内容"
            suffix-icon="el-icon-search"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item
          label="注塑机型号"
          prop="machine_trademark"
        >
          <el-autocomplete
            v-model="query.machine_trademark"
            :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'mold_flow_machine_trademark')})"
            placeholder="请输入内容"
            suffix-icon="el-icon-search"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item
          label="塑料牌号"
          prop="poly_trademark"
        >
          <el-autocomplete
            v-model="query.poly_trademark"
            :fetch-suggestions="((str, cb) => {querySuggestionOptions(str,cb,'poly_trademark')})"
            placeholder="请输入内容"
            suffix-icon="el-icon-search"
          >
          </el-autocomplete>
        </el-form-item>
        <el-form-item
          label="日期"
          prop="created_at"
        >
          <el-date-picker
            v-model="query.created_at"
            placeholder="选择日期"
            format="yyyy-MM-dd"
            value-format="yyyy-MM-dd"
            type="date"
            style="width:10rem"
          >
          </el-date-picker>
        </el-form-item>
        <el-form-item style="float:right">
          <el-button
            type="primary"
            @click="queryListData(true)"
            style="width: 6rem; margin-left: 10px"
          >
            搜索
          </el-button>
          <el-button
            type="danger"
            @click="reloadListData"
            style="width: 6rem"
          >
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    <el-table
      v-loading="listLoading"
      size="mini"
      border
      fit
      style="width: 100%"
      :data="listData.items"
      :height="tableHeight"
      :row-style="tableRowStyle"
      :cell-style="tableCellStyle"
      :header-cell-style="tableHeaderStyle"
    >
      <el-table-column type="index" label="序号" width="45" align="center">
      </el-table-column>
      <template v-for="(column, index) in columns_setting">
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
            <span v-if="column.prop === 'analytical_read'">
              <el-button
                size="mini"
                type="primary"
                @click="readMoldFlowData(scope.row)"
              >
                读取
              </el-button>
            </span>
            <span v-else-if="column.prop === 'doc_link'">
              <el-link
                type="primary"
                size="mini"
                @click="checkMoldFlow(scope.row.doc_link)"
              >
                查看模流文档
              </el-link>
            </span> 
            <span v-else-if="column.prop === 'upload_ppt'">
              <span v-if="scope.row.ppt_link">
                <el-link
                  type="primary"
                  size="mini"
                  @click="checkMoldFlow(scope.row.ppt_link)"
                >
                  查看模流PPT
                </el-link>
              </span>
              <span v-else>
                <upload-single-file
                  style="display: inline-block"
                  :value="moldflowPptInfo(scope.row)"
                  search-type="mold_flow_ppt"
                  @upload-file-info="onFileUploaded"
                >
                </upload-single-file>
              </span>
            </span>
            <span v-else-if="column.prop === 'delete_data'">
              <el-button
                size="mini"
                type="danger"
                icon="el-icon-delete"
                @click="deleteMoldFlow(scope.row)"
                style="margin: 0"
              >
                删除
              </el-button>
            </span>
            <span v-else>
              {{ scope.row[column.prop] }}
            </span>
          </template>
        </el-table-column>
      </template>
    </el-table>
  </div>
</template>

<script>
import { getMoldflowListMethod, getOptions, setMoldflowMethod } from "@/api";
import suggestionOptions from "@/mixins/suggestionOptions.vue"
import { ProjectsInfoModule } from "@/store/modules/projects";
import UploadSingleFile from '@/components/uploadSingleFile'
import { getFullReportUrl } from '@/utils/assert';
export default {
  name: "MoldFlowList",
  mixins: [suggestionOptions],
  components: {
    UploadSingleFile,
  },
  props: {
    moldFlowNo: null
  },
  data() {
    return {
      moldflow_no: this.moldFlowNo,
      query: {
        project_id: ProjectsInfoModule.selectedProject.mold_info.id,
        mold_flow_no: null,
        analytical_sequence: null,
        machine_trademark: null,
        poly_trademark: null,
        created_at: null,
      },
      listData: {},
      listLoading: false,
      tableHeaderStyle: {
        "background-color": "lightblue",
        color: "#000",
        "font-size": "12px",
        padding: "10px 0px",
      },
      tableCellStyle: { padding: "7px 0px" },
      tableHeight: "20rem",
      columns_setting: [
        { visible: true, label: "模流分析编号", prop: "mold_flow_no", width: 130, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "模具编号", prop: "mold_no", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "注塑机型号", prop: "machine_trademark", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "塑料牌号", prop: "poly_trademark", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "分析序列", prop: "analytical_sequence", width: 150, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "TXT", prop: "doc_link", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "PPT", prop: "upload_ppt", width: 200, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "模流数据读取", prop: "analytical_read", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "删除数据", prop: "delete_data", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
        { visible: true, label: "日期", prop: "created_at", width: 120, align: "center", header_align: "center", sortable: true, tooltip: false },
      ],
    };
  },
  mounted() {
    this.getListData()
  },
  methods: {
    tableRowStyle({row, rowIndex}) {
      if (row.mold_flow_no == this.moldflow_no) {
        return {
          background: 'rgb(146, 205, 249)'
        }
      }
    },
    checkMoldFlow(url){
      window.location.href = getFullReportUrl(url);
    },
    moldflowPptInfo(row) {
      return {
        id: ProjectsInfoModule.selectedProject.mold_info.id,
        name: null,
        url: null,
        mold_flow_no: row.mold_flow_no
      }
    },
    getListData() {
      getMoldflowListMethod({"project_id":ProjectsInfoModule.selectedProject.mold_info.id})
      .then((res)=>{
        if(res.status === 0 && JSON.stringify(res.data)!=="{}"){
          let list = []
          res.data.forEach(item => {
            list.push({
              mold_no:item.mold_no,
              mold_flow_no:item.mold_flow_no,
              analytical_sequence:item.technology.analytical_sequence,
              machine_trademark:item.machine.trademark,
              poly_trademark:item.polymer.poly_trademark,
              created_at:item.created_at,
              ppt_link:item.ppt_link,
              project_id:item.project_id,
              doc_link: item.doc_link
            })
          })
          this.listData.items = list
          this.$set(this.listData)
          this.$forceUpdate()
        } else {
          this.listData = {}
        }
      })
    },
    sortList(sort) {
      // 排序
      this.query.$orderby = sort.prop;
      this.getListData();
    },
    querySuggestionOptions(input, cb, column) {
      cb(this.queryOptions(input, column, "moldflow"))
    },
    queryOptions(str, column) {
      str = str == null ? "" : str 
      let promptList = []
      if (column) {
        getOptions(column, { "form_input": str, "db_table": "moldflow","project_id": ProjectsInfoModule.selectedProject.mold_info.id})
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
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      getMoldflowListMethod(this.query).then((res)=>{
        if(res.status === 0 && JSON.stringify(res.data)!=="{}"){
          let list = []
          res.data.forEach(item => {
            list.push({
              mold_no:item.mold_no,
              mold_flow_no:item.mold_flow_no,
              analytical_sequence:item.technology.analytical_sequence,
              machine_trademark:item.machine.trademark,
              poly_trademark:item.polymer.poly_trademark,
              created_at:item.created_at,
              ppt_link:item.ppt_link,
              project_id:item.project_id
            })
          })
          this.listData.items = list
          this.$set(this.listData)
          this.$forceUpdate()
        } else {
          this.listData = {}
        }
      })
    },
    reloadListData() {
      this.query.mold_flow_no = null
      this.query.analytical_sequence = null
      this.query.machine_trademark = null
      this.query.poly_trademark = null
      this.query.created_at = null
      this.query.project_id = ProjectsInfoModule.selectedProject.mold_info.id

      this.queryListData(true)
    },
    deleteMoldFlow(row) {
      this.$confirm(`确认删除以下模流数据？\r\n ${row.mold_flow_no}`,"删除模流数据", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      }).then(() => {
        setMoldflowMethod({
          "project_id":row.project_id,"mold_flow_no": row.mold_flow_no,"deleted":1
        }).then((res) => {
          if (res.status === 0) {
            this.$message({ type: "success", message: "删除成功!"})
            this.getListData()
            if (row.mold_flow_no == this.moldflow_no) {
              row.mold_flow_no = null
              this.$emit("getTheMoldflow",row)
            }
          }
        })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消删除！"
        })
      })
    },
    onFileUploaded(fileInfo) {
      this.$emit("upload-file-info", fileInfo)
    },
    readMoldFlowData(row){
      this.$emit("getTheMoldflow",row)
    }
  },
  watch: {
    moldFlowNo() {
      this.moldflow_no = this.moldFlowNo
    }
  }
};
</script>

<style lang="scss" scoped>
  .el-form-item {
    .el-autocomplete {
      width: 10rem;
    }

    .el-date-picker {
      width: 10rem;
    }
  }
</style>