<template>
  <div>
    <div style="height: 30px"></div>
    <el-table
      size="mini"
      border
      ref="singleTable"
      :data="tableData"
      highlight-current-row
      style="width: 100%"
      :row-style="tableRowStyle"
      :cell-style="tableCellStyle"
      :show-header="false"
      :span-method="organizeTable"
    >
      <el-table-column property="desc" label="" width="130" align="center"></el-table-column>
      <template v-for="item,index in machine_num">
        <el-table-column
          :key="index"
          :prop="'value'+(index+1)"
          label=""
          width="129"
          align="center"
        >
          <template slot-scope="scope">
            <span v-if="scope.row.desc === '工艺编号'">
              <el-link type="primary" @click="editProcessRecord(index)">
                {{ scope.row['value'+(index+1)] }}
              </el-link>
            </span>
            <span v-else>
              {{ scope.row['value'+(index+1)] }}
            </span>
          </template>
        </el-table-column>
      </template>
    </el-table>
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
import { getOptions, processRecordMethod } from "@/api";
import ProcessRecordDetail from './detail.vue'
export default {
  name: "TransplantAdaptation",
  components: { ProcessRecordDetail },
  data() {
    return {
      tableData: [
        {
          desc: "参数",
        },
        {
          desc: "",
        },
        {
          desc: "注射量",
        },
        {
          desc: "VP切换位置",
        },
        {
          desc: "垫料",
        },
        {
          desc: "注射时间",
        },
        {
          desc: "设置注射速度",
        },
        {
          desc: "设置注射压力",
        },
        {
          desc: "保压",
        },
        {
          desc: "背压",
        },
        {
          desc: "螺杆转速",
        },
        {
          desc: "是否适配",
        },
        {
          desc: "工艺编号",
        },
      ],
      colorData: [],
      listLoading: false,
      tableHeight: "45rem",
      machine_num: 12,
      process_detail: {
        id: null,
      },
      viewType: null,
      showProcessRecordDetail: false,
    };
  },
  mounted(){
    getOptions("process_machine_adaption",{"form_input":this.$route.query.process_id})
    .then( res => {
      if(res.status == 0) {
        this.tableData = res.data.table_data
        this.colorData = res.data.color_data
        this.machine_num = (res.data.machine_num+1)*2
      }
    })    
  },
  methods: {
    tableRowStyle({ row, rowIndex }) {},
    tableCellStyle({ row, column, rowIndex, columnIndex }) {
      if (this.colorData && JSON.stringify(this.colorData)!=="[]" && this.tableData && JSON.stringify(this.tableData)!=="[]") {
        let col
        let bgcol
        for (let i = 2 ; i < this.colorData.length; i++) {
          for (let j = 1; j < 9; j++) {
            if (rowIndex == i) {
              if (columnIndex === j) {
                col = this.colorData[i]["value"+j]
              }
            }
          }
        }
        let arr = []
        Object.values(this.tableData[11]).forEach(val => {
          arr.push(val)
        })
        for (let i = 0; i < arr.length; i++) {
          if (arr[i] == "是") {
            if (columnIndex === i) {
              bgcol = "rgb(144,238,144)"
              col = "black"
            }
          }
        }
        return {color: col,backgroundColor: bgcol}
      }
    },
    organizeTable({ row, column, rowIndex, columnIndex }) {
      if (rowIndex === 0 && columnIndex === 1) {
        return [1, 2]
      } else if (rowIndex === 0 && columnIndex === 2) {
        return [1, 2]
      } else if (rowIndex === 0 && columnIndex === 3) {
        return [1, 2]
      } else if (rowIndex === 0 && columnIndex === 4) {
        return [1, 2]
      } else if (rowIndex === 0 && columnIndex === 5) {
        return [1, 2]
      } else if (rowIndex === 0 && columnIndex === 6) {
        return [1, 2]
      }
      if (rowIndex === 12 && columnIndex === 1) {
        return [1, 2]
      } else if (rowIndex === 12 && columnIndex === 2) {
        return [1, 2]
      } else if (rowIndex === 12 && columnIndex === 3) {
        return [1, 2]
      } else if (rowIndex === 12 && columnIndex === 4) {
        return [1, 2]
      } else if (rowIndex === 12 && columnIndex === 5) {
        return [1, 2]
      } else if (rowIndex === 12 && columnIndex === 6) {
        return [1, 2]
      }
      if (rowIndex === 13 && columnIndex === 1) {
        return [1, 2]
      } else if (rowIndex === 13 && columnIndex === 2) {
        return [1, 2]
      } else if (rowIndex === 13 && columnIndex === 3) {
        return [1, 2]
      } else if (rowIndex === 13 && columnIndex === 4) {
        return [1, 2]
      } else if (rowIndex === 13 && columnIndex === 5) {
        return [1, 2]
      } else if (rowIndex === 13 && columnIndex === 6) {
        return [1, 2]
      } 
    },
    editProcessRecord(index) {
      let pro_id = this.tableData[13]['value'+(index+1)]
      this.process_detail.id = pro_id
      this.viewType = "edit"
      this.showProcessRecordDetail = true
    },
    refreshView() {
      this.process_detail.id = null
      this.viewType = null
      this.showProcessRecordDetail = false
    },
  },
};
</script>

<style lang="scss" scoped>

</style>