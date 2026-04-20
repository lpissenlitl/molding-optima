<template>
  <div>
    <div style="height: 20px"></div>
    <el-collapse
      v-model="form_info.active_collapse"
      class="collapseItemTitle"
      accordion
    >
      <el-collapse-item title="1.选择机器" name="1">
        <query-machine-list
          ref="queryMachineList"
          :query-detail="query"
          @queryStart="listLoading = true"
          @queryFinish="onQueryFinish"
        >
        </query-machine-list>

        <div class="row-toolbutton">
          <div style="float: right">
            <el-button-group>
              <el-button
                size="mini"
                type="primary"
                icon="el-icon-plus"
                @click="addAdaptive"
              >
                加入适配
              </el-button>
              <el-button
                size="mini"
                type="danger"
                icon="el-icon-minus"
                @click="cancelAdaptive"
              >
                取消适配
              </el-button>
            </el-button-group>
          </div>
        </div>
        <div style="height: 8px" />
        <machine-undistributed 
          ref="undistributedMachine"
          :query-detail="query"
          :undistributed-data="undistributedData"
          :table-height="mactableHeight"
          :mac-columns-setting="mac_columns_setting"
          :mac-table-header-style="tableHeaderStyle"
          :mac-table-row-style="mactableRowStyle"
          :mac-table-cell-style="mactableCellStyle"
          @query-machine-list="getListData"
        >
        </machine-undistributed>
        <machine-distributed 
          ref="distributedMachine"
          :distributed-data="distributedData"
          :table-height="mactableHeight"
          :mac-columns-setting="mac_columns_setting"
          :mac-table-header-style="tableHeaderStyle"
          :mac-table-row-style="mactableRowStyle"
          :mac-table-cell-style="mactableCellStyle"
        >
        </machine-distributed>
        
        <el-divider class="precondition-divider" content-position="center"></el-divider>
        <div style="text-align: center">
          <el-button
            @click="nextStep"
            style="width: 8rem"
            size="small"
            type="primary"
          >
            下一步
          </el-button>
        </div>
      </el-collapse-item>
      <el-collapse-item title="2.适配机器" name="2">
  
        <el-table
          size="mini"
          border
          ref="singleTable"
          :data="tableData"
          highlight-current-row
          style="width: 100%"
          :row-style="tableRowStyle"
          :cell-style="tableCellStyle"
          :header-cell-style="tableHeaderStyle"
        > 
          <el-table-column property="mold_desc" label="" width="135" align="left" fixed></el-table-column>
          <el-table-column property="mold_info" label="" width="130" align="center" fixed></el-table-column>
          <el-table-column property="desc" label="" width="130" align="left" fixed></el-table-column>
          <template v-for="item,index in machine_num">
            <el-table-column
              :key="index"
              :prop="'value'+(index+1)"
              :label="String(index+1)"
              width="129"
              align="center"
            > 
              <template slot-scope="scope">
                <span v-if="scope.row.mold_desc !== '约机'">
                  {{ scope.row.values[index] }}
                </span>
              </template>
            </el-table-column>
          </template>
        </el-table>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script>
import { getOptions } from "@/api";
import { UserModule } from '@/store/modules/user'
import QueryMachineList from './subView/queryMachineList.vue';
import MachineUndistributed from './subView/machineUndistributed.vue'
import MachineDistributed from './subView/machineDistributed.vue'
import { ProjectsInfoModule } from '@/store/modules/projects';
export default {
  components: { QueryMachineList, MachineUndistributed, MachineDistributed },
  name: "MachineAdaptation",
  data() {
    return {
      query: {
        company_id: UserModule.company_id,
        data_source: null,
        trademark: null,
        machine_type: null,
        power_method: null,
        propulsion_axis: null,
        serial_no: "",
        manufacturer: "",

        page_no: 1,
        page_size: 100
      },
      form_info: {
        active: 0,
        active_collapse: ["1"],
      },
      tableData: [
        {
          "mold_desc":"模具编号", 
          "mold_info":"",
          "desc": "注塑机型号",
          "values": []
        },
        {
          "desc": "注塑机编号",
          "values": []
        },
        {
          "mold_desc": "是否适配",
          "values": []
        },
        {
          "mold_desc":"模具类型", 
          "mold_info":"", 
          "desc": "注塑机类型",
          "values": []
        },
        {
          "mold_desc":"模具锁模力", 
          "mold_info":"",
          "desc": "锁模力",
          "values": []
        },
        {
          "mold_desc":"模具最大重量", 
          "mold_info":"",
          "desc": "最大注射重量",
          "values": []
        },
        // {
        //    "desc": "最大注射行程",
        //  },
        //  {
        //    "desc": "停留时间(机器)",
        //  },
        //  {
        //    "desc": "停留时间(热流道)",
        //  },
        //  {
        //    "desc": "停留时间(总和)",
        //  },
        {
          "mold_desc":"模具尺寸(横)", 
          "mold_info":"",
          "desc": "最小容模尺寸(横)",
          "values": []
        },
        {
          "mold_desc":"模具尺寸(竖)", 
          "mold_info":"",
          "desc": "最小容模尺寸(竖)",
          "values": []
        },
        {
          "mold_desc":"模具厚度", 
          "mold_info":"",
          "desc": "最小容模厚度",
          "values": []
        },
        {
          "mold_desc":"模具尺寸(横)", 
          "mold_info":"",
          "desc": "最大容模尺寸(横)",
          "values": []
        },
        {
          "mold_desc":"模具尺寸(竖)", 
          "mold_info":"",
          "desc": "最大容模尺寸(竖)",
          "values": []
        },
        {
          "mold_desc":"模具厚度", 
          "mold_info":"",   
          "desc": "最大容模厚度",
          "values": []
        },
        {
          "mold_desc":"模具定位圈直径", 
          "mold_info":"",
          "desc": "定位圈直径",
          "values": []
        },
        {
          "mold_desc":"模具顶出力", 
          "mold_info":"",
          "desc": "顶出力",
          "values": []
        },
        {
          "mold_desc":"模具顶出行程", 
          "mold_info":"", 
          "desc": "顶出行程",
          "values": []
        },
        {
          "mold_desc":"模具开模行程", 
          "mold_info":"",
          "desc": "最大开模行程",
          "values": []
        },
        {
          "mold_desc":"模具喷嘴球径", 
          "mold_info":"",    
          "desc": "喷嘴球径",
          "values": []
        },
        {
          "mold_desc":"模具喷嘴孔径", 
          "mold_info":"",  
          "desc": "喷嘴孔径",
          "values": []
        },
        {
          "mold_desc":"约机", 
          "mold_info":"",  
          "desc": "",
          "values": []
        },
        {
          "mold_desc":"注塑机id", 
          "mold_info":"",  
          "desc": "",
          "values": []
        },
      ],
      colorData: [],
      listLoading: false,
      tableHeaderStyle: {
        "background-color": "lightblue",
        color: "#000",
        "font-size": "12px",
        padding: "10px 0px",
        "text-align": "center",
      },
      tableHeight: "45rem",
      machine_num: 10,
      mactableRowStyle: { },
      mactableCellStyle: { 'padding': '7px 0px' },
      mactableHeight: 250,
      undistributedData: {},
      distributedData: {},
      isShowReservation: false,
      mac_columns_setting: [
        { visible: true, label: "注塑机品牌", prop: "manufacturer", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "注塑机型号", prop: "trademark", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "设备编码", prop: "serial_no", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "资产编号", prop: "asset_no", width: 100, align: "center", header_align: "center", sortable: true, tooltip: false}, 
        { visible: true, label: "最大注射重量", prop: "max_injection_weight", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "最大注射速度", prop: "max_injection_velocity", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "最大注射行程", prop: "max_injection_stroke", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true}, 
        { visible: true, label: "最大注射压力", prop: "max_injection_pressure", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true}, 
        { visible: true, label: "最大保压压力", prop: "max_holding_pressure", width: 100, align: "center", header_align: "center", sortable: false, tooltip: true}, 
        { visible: true, label: "最大螺杆转速", prop: "max_screw_rotation_speed", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "塑化能力", prop: "plasticizing_capacity", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "螺杆直径", prop: "screw_diameter", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "出厂日期", prop: "manufacture_date", width: 100, align: "center", header_align: "center", sortable: false, tooltip: false}, 
        { visible: true, label: "更新日期", prop: "updated_at", width: 140, align: "center", header_align: "center", sortable: false, tooltip: false}, 
      ]
    };
  },
  mounted(){
    // 如果之前适配过,那么直接读取适配结果
    if(ProjectsInfoModule.selectedProject.adaption){
      this.form_info.active++
      this.form_info.active_collapse = ["2"]
      this.tableData = ProjectsInfoModule.selectedProject.adaption.table_data
      this.colorData = ProjectsInfoModule.selectedProject.adaption.color_data
      this.machine_num = ProjectsInfoModule.selectedProject.adaption.machine_num
      this.showReservation()
    }
    this.getListData()
  },
  methods: {
    tableRowStyle({ row, rowIndex }) {
      if (rowIndex === 19) {
        return {display: 'none'}
      }
    },
    tableCellStyle({ row, column, rowIndex, columnIndex }) {
      if (this.colorData && JSON.stringify(this.colorData)!=="[]" && this.tableData && JSON.stringify(this.tableData)!=="[]") {
        let count = this.colorData[4].values.length
        let col
        let bgcol
        for (let i = 3 ; i < this.colorData.length; i++) {
          for (let j = 0; j < count; j++) {
            if (rowIndex == i) {
              if (columnIndex === j+3) {
                col = this.colorData[i].values[j]
              }
            }
          }
        }

        if (rowIndex === 2 && columnIndex > 2) {
          bgcol = 'rgb(254, 220, 220)'
        }
        if (columnIndex === 0 || columnIndex === 1) {
          bgcol = 'rgb(237, 245, 255)'
        }
        if (columnIndex === 2) {
          bgcol = 'rgb(237, 245, 255)'
        }

        let arr = []
        Object.values(this.tableData[18]).forEach(val => {
          arr.push(val)
        })
        for (let i = 0; i < this.tableData[2].values.length; i++) {
          if (this.tableData[2].values[i] == "是") {
            if (columnIndex === i+3) {
              bgcol = "rgb(212, 249, 212)"
              for (let j = 1; j < this.colorData[4].values.length; j++) {
                if (rowIndex == i) {
                  if (this.colorData[i].values[j] != "rgb(255,160,0)") {
                    col = "black"
                  }
                }
              }
            }
          }
        }
        return {color: col,backgroundColor: bgcol}
      }
    },
    nextStep() {
      let machine_id_list = []
      for(let i = 0;i<this.distributedData.total;i++){
        machine_id_list.push(this.distributedData.items[i].id)
      }

      if(JSON.stringify(machine_id_list) != "[]"){
        this.form_info.active++
        this.form_info.active_collapse = ["2"]
        getOptions("machine_adaption",{"form_input":this.$route.query.project_id, "machine_id_list":machine_id_list})
        .then( res => {
          if(res.status == 0) {
            this.tableData = res.data.table_data
            this.colorData = res.data.color_data
            this.machine_num = res.data.machine_num
            this.showReservation()
          }
        })
      } else {
        this.$message({type: 'warning', message: '请选择注塑机'})
        return
      }
    },
    addAdaptive() {
      let selections = this.$refs.undistributedMachine.multipleSelection
      if (selections.length === 0) {
        this.$message({type: 'warning', message: '请选择注塑机'})
        return
      }
      let tempDistributedData = { items: [], total: 0 }
      for (let i = 0; i < selections.length; i++) {
        tempDistributedData.items.push(selections[i])
        tempDistributedData.total++
      }
      this.distributedData = tempDistributedData
    },
    cancelAdaptive() {
      let selections = this.$refs.distributedMachine.multipleSelection
      if (selections.length === 0) {
        this.$message({type: 'warning', message: '请选择已加入适配的注塑机'})
        return
      }
      for (let i = 0; i < selections.length; i++) {
        for (let j = 0; j < this.distributedData.items.length; j++) {
          if (selections[i].id == this.distributedData.items[j].id) {
            this.distributedData.items.splice(j,1)
            this.distributedData.total--
          }
        }
      }
      return this.distributedData
    },
    getListData() {
      this.listLoading = true
      this.$refs.queryMachineList.queryListData();
    },
    onQueryFinish(machineList) {
      this.undistributedData = machineList
      this.listLoading = false
    },
    showReservation(){
      for (let i = 0; i < this.machine_num; i++) {
        if (this.tableData[2].values[i] === "是"&&this.tableData.length>=14) {
          this.tableData[18].values[i] = true
        }
      }
    },
  },
  watch: {
  }
};
</script>

<style lang="scss" scoped>
</style>>