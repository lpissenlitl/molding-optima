<template>
  <div>
    <h1 style="text-align: center">载荷敏感度测试试验表</h1>

    <div style="height: 12px" />

    <el-form
      ref="detail_info"
      size="mini"
      :inline="true"
      label-width="9rem"
      label-position="right"
      :rules="rules"
      :model="detail_info"
    >
      <el-divider content-position="center">
        <span style="color: blue">基本信息</span>
      </el-divider>

      <el-form-item label="注塑机来源" prop="machine_data_source">
        <el-autocomplete
          v-model="detail_info.machine_data_source"
          placeholder="注塑机来源"
          clearable
          style="width:10rem"
          :fetch-suggestions="queryMacDataSourceList"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="注塑机型号" prop="machine_trademark">
        <el-autocomplete
          v-model="detail_info.machine_trademark"
          placeholder="注塑机型号"
          clearable
          style="width:10rem"
          :fetch-suggestions="queryTrademarkList"
          @select="handleTrademarkSelect"
        >
          <template slot-scope="{ item }">
            <el-tooltip
              effect="dark"
              :content="'设备编码: ' + [item.serial_no? item.serial_no: '未知']"
              placement="right-end"
            >
              <div style="width:auto;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                {{ item.value }}
              </div>
            </el-tooltip>
          </template>
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="设备编码">
        <el-input v-model="detail_info.asset_no"></el-input>
      </el-form-item>

      <el-form-item label="塑料简称" prop="polymer_abbreviation">
        <el-autocomplete
          v-model="detail_info.polymer_abbreviation"
          placeholder="塑料简称"
          clearable
          style="width:10rem"
          :fetch-suggestions="queryAbbreviationList"
          @select="handleAbbreviationSelect"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="塑料牌号" prop="polymer_trademark">
        <el-autocomplete
          v-model="detail_info.polymer_trademark"
          placeholder="塑料牌号"
          clearable
          style="width:10rem"
          :fetch-suggestions="queryPolymerTrademarkList"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="模具编号" prop="mold_no">
        <el-autocomplete
          v-model="detail_info.mold_no" 
          :fetch-suggestions="queryMoldNo"
          placeholder="模具编号"
          @select="handleMoldNoSelect"
        > 
        </el-autocomplete>
      </el-form-item>
      
      <el-form-item label="制品名称">
        <el-input v-model="detail_info.product_name"></el-input>
      </el-form-item>

      <el-form-item label="模穴数">
        <el-input v-model="detail_info.cavity_num"></el-input>
      </el-form-item>

      <!-- <el-form-item label="成型周期">
        <el-input v-model="detail_info.cycle"></el-input>
      </el-form-item> -->

      <el-form-item label="测试人员">
        <el-input v-model="detail_info.trial_name"></el-input>
      </el-form-item>

      <el-card shadow="never">
        <span id="colors">测试目的</span>：
        <p style="text-indent: 2em">
          确定注塑机对负载的敏感性。载荷敏感度是用来衡量注塑机注射单元速度受压力变化影响的性能指标。
        </p>
        <span id="colors">测试原理</span>：
        <p style="text-indent: 2em">
          注塑机载荷敏感度的数值越小，说明注射速度受载荷（注射时，螺杆所受阻力）变化的影响越小，注塑机的注射速度就越稳定。
          在填充期间，注射速度稳定，则表明生产工艺稳定。所以，注塑机的稳定性就好。
          相反，注塑机载荷敏感度的数值越大，说明注射速度受载荷（注射时，螺杆所受阻力）变化的影响越大，注塑机的注射速度就不稳定。
          在填充期间，注射速度不稳定，表明生产工艺就不稳定。所以，注塑机的稳定性就差。
        </p>
        <span id="colors">测试标准</span>：
        <p style="text-indent: 2em">
          通常，对于精密注塑来说，载荷敏感度的绝对值要小于5%。
        </p>
        <span id="colors">测试设备</span>：
        <ol>
          <li>闭环系统控制的注塑机</li>
          <li>数据曲线采集装置</li>
          <li>空射用的夹具</li>
        </ol>
        <span id="colors">测试方法</span>：
        <ol>
          <li>如需要，安装射胶压力测试系统。</li>
          <li>设置注塑机以标准的两阶段成型工艺运行。</li>
          <li>关掉保压压力。</li>
          <li>注射一模短射的零件，记录填充时间和压力峰值。</li>
          <li>射台后退，进行注射。</li>
          <li>记录空射的填充时间和压力峰值。</li>
          <li>用公式计算结果。</li>
        </ol>
      </el-card>

      <div style="height: 12px" />

      <el-divider content-position="center">
        <span style="color: blue">测试数据记录表</span>
      </el-divider>

      <div style="text-align:center">
        <div style="width:400px" />
        <el-table
          :data="tableDataComputed"
          size="mini"
          height-current-row
          :cell-style="{ padding: '8px' }"
        >
          <el-table-column 
            prop="title" 
            label="项目" 
            align="center"
            width="100"
          >
          </el-table-column>

          <el-table-column 
            prop="inj_time_nomal" 
            label="填充时间（模具）/s" 
            align="center"
            width="200"
          >
            <template slot-scope="scope">
              <el-input size="mini" v-model="scope.row.inj_time_nomal"></el-input>
            </template>
          </el-table-column>

          <el-table-column 
            prop="inj_time_empty" 
            label="填充时间（空射）/s" 
            align="center"
            width="200"
          >
            <template slot-scope="scope">
              <el-input size="mini" v-model="scope.row.inj_time_empty"></el-input>
            </template>
          </el-table-column>

          <el-table-column 
            prop="peak_pres_nomal" 
            label="压力峰值（模具）/MPa" 
            align="center"
            width="200"
          >
            <template #header>
              <div>压力峰值（模具）</div>
              <div>{{ detail_info.pressure_unit }}</div>
            </template>
            <template slot-scope="scope">
              <el-input size="mini" v-model="scope.row.peak_pres_nomal"></el-input>
            </template>
          </el-table-column>

          <el-table-column 
            prop="peak_pres_empty" 
            label="压力峰值（空射）/MPa" 
            align="center"
            width="200"
          >
            <template #header>
              <div>压力峰值（空射）</div>
              <div>{{ detail_info.pressure_unit }}</div>
            </template>
            <template slot-scope="scope">
              <el-input size="mini" v-model="scope.row.peak_pres_empty"></el-input>
            </template>
          </el-table-column>

          <el-table-column 
            prop="result" 
            label="实际结果/%" 
            align="center"
            width="200"
          >
            <template slot-scope="scope">
              <el-input size="mini" v-model="scope.row.result"></el-input>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-form>

    <div style="height:35px" />
    
    <div class="nextButton">
      <el-button 
        type="danger"
        size="small"
        @click="resetView"
      >
        重  置
      </el-button>

      <el-button
        type="primary"
        size="small"
        @click="saveData"
        :loading="loading"
      >
        {{ detail_info.machine_trial_id ? "更  新" : "保  存" }}
      </el-button>
    </div>
  </div>
</template>

<script>
import { loadSensitivityMethod, machineTrialsMethod, getOptions, projectMethod, machineMethod } from "@/api"
import { UserModule } from "@/store/modules/user"

export default {
  name: "LoadSensitivity",
  data() {
    return {
      detail_info: {
        machine_trial_id: null,
        mold_no: null,
        polymer_abbreviation: null,
        polymer_trademark: null,
        cycle: null,
        product_name: null,
        cavity_num: null,
        machine_data_source: null,
        machine_trademark: null,
        asset_no: null,
        trial_name: UserModule.engineer,
        mold_trial_date: null,
        pressure_unit: "MPa",

        table_data: [{
          title: "高速",
          inj_time_nomal: null,
          inj_time_empty: null,
          peak_pres_nomal: null,
          peak_pres_empty: null,
          result: null,
        }, {
          title: "中速",
          inj_time_nomal: null,
          inj_time_empty: null,
          peak_pres_nomal: null,
          peak_pres_empty: null,
          result: null,
        }, {
          title: "低速",
          inj_time_nomal: null,
          inj_time_empty: null,
          peak_pres_nomal: null,
          peak_pres_empty: null,
          result: null,
        }]
      },
      loading: false,
      mac_data_source_list: [],
      mac_trademark_list: [],
      poly_abbreviation_list: [],
      poly_trademark_dict: [],
      rules: {
        "mold_no": [
          { required: true, message: '模具编号不能为空' },
        ],
        "machine_data_source": [
          { required: true, message:'注塑机来源不能为空' },
        ],
        "machine_trademark": [
          { required: true, message:'注塑机型号不能为空' },
        ],
        "polymer_abbreviation": [
          { required: true, message:'塑料简称不能为空' },
        ],
        "polymer_trademark": [
          { required: true, message:'塑料牌号不能为空' },
        ],
      }
    };
  },
  props: {
    id: {
      type: Number,
      default: null
    }
  },
  created() {
    getOptions("machine_data_source", {})
    .then(res => {
      if (res.status === 0) {
        this.mac_data_source_list.length = 0
        for (let i = 0; i < res.data.length; ++i) {
          this.mac_data_source_list.push({ "value": res.data[i].value })
        }
      }
    }),
    getOptions("polymer_abbreviation")
    .then(res => {
      // 塑料简称
      if (res.status === 0 && Array.isArray(res.data)) {
        this.poly_abbreviation_list.length = 0
        for (let i = 0; i < res.data.length; ++i) {
          this.poly_abbreviation_list.push({ "value": res.data[i].value })
        }
      }
    })
  },
  mounted() {
    this.loadData()
  },
  methods: {
    queryMacDataSourceList(queryString, cb) {
      var mac_data_source_list = this.mac_data_source_list;
      var results = queryString ? mac_data_source_list.filter(this.createStateFilter(queryString)) : mac_data_source_list;
      cb(results);
    },
    queryAbbreviationList(queryString, cb) {
      var poly_abbreviation_list = this.poly_abbreviation_list;
      var results = queryString ? poly_abbreviation_list.filter(this.createStateFilter(queryString)) : poly_abbreviation_list;
      cb(results)
    },
    queryPolymerTrademarkList(queryString, cb) {
      var poly_trademark_dict = this.poly_trademark_dict;
      var results = queryString ? poly_trademark_dict.filter(this.createStateFilter(queryString)) : poly_trademark_dict;
      cb(results)
    },
    queryTrademarkList(queryString, cb) {
      queryString = queryString == null ? "" : queryString

      if (!this.detail_info.machine_data_source) {
        return []
      }

      let promptList = []
      getOptions("machine_trademark", {
        "data_source": this.detail_info.machine_data_source,
        "trademark": queryString
      }).then(res => {
        if (res.status == 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
              serial_no: res.data[i].serial_no
            })
          }
          cb(promptList)
        }
      })
    },
    queryMoldNo(str, cb) {
      str = str == null ? "" : str 
      let promptList = []
      getOptions("mold_no", {"form_input": str,"db_table": "mold"})
      .then( res => {
        if(res.status == 0) {
          for(let i = 0; i < res.data.length; i++) {
            promptList.push(res.data[i])
          }
        }
      })
      cb(promptList)
    },
    handleTrademarkSelect(item) {
      this.detail_info.asset_no = item.asset_no
      this.update_machine_unit(item)
    },
    createStateFilter(queryString) {
      return (state) => {
        return (state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
      };
    },
    handleMacDataSourceSelect() {
      getOptions("machine_trademark", {"data_source": this.detail_info.machine_data_source})
      .then(res => {
        if (res.status === 0 && Array.isArray(res.data)) {
          this.mac_trademark_list.length = 0
          for (let i = 0; i < res.data.length; ++i) {
            this.mac_trademark_list.push({ "id": res.data[i].id, "value": res.data[i].trademark})
          }
        }
      });
    },
    handleAbbreviationSelect() {
      getOptions("polymer_trademark", {"abbreviation": this.detail_info.polymer_abbreviation})
      .then(res => {
        if (res.status === 0 && Array.isArray(res.data)) {
          this.poly_trademark_dict.length = 0
          for (let i = 0; i < res.data.length; ++i) {
            this.poly_trademark_dict.push({ "id": res.data[i].id, "value": res.data[i].trademark })
          }

        }
      });
    },
    handleMoldNoSelect(item) {
      projectMethod.getDetail(item.mold_id)
      .then(res => {
        if(res.data.mold_info.product_infos.length>0){
          this.detail_info.product_name = res.data.mold_info.product_infos[0].product_name
        }
        this.detail_info.cavity_num = res.data.mold_info.cavity_num
      })
    },
    loadData() {
      if (this.id) {
        loadSensitivityMethod.get({
          "machine_trial_id": this.id
        }).then(res => {
          if (res.status == 0) {
            if (res.data && JSON.stringify(res.data) != "{}") {
              this.detail_info = res.data
            } else {
              this.detail_info.machine_trial_id = this.id
            }
          }
        })
      }
    },
    update_machine_unit(item) {
      if(item.id){
        machineMethod.getDetail(item.id)
        .then(res => {
          if (res.status === 0) {
            this.detail_info.pressure_unit = res.data.pressure_unit
          }
        })
      }
    },
    unit_exchange(pressure, unit){
      if(unit=="kgf/cm²"){
        return pressure*14.5
      }
      if(unit=="bar"){
        return pressure*14.5
      }
      if(unit=="MPa"){
        return pressure*145
      }
      else{
        return pressure
      }
    },
    saveData() {
      this.loading = true
      this.$refs["detail_info"].validate((valid) => {
        if(valid) {
          if (!this.detail_info.machine_trial_id) {
            let machine_trial_index = {
              "company_id": UserModule.company_id,
              "machine_trial_type": "load_sensitivity",
              "machine_data_source": this.detail_info.machine_data_source,
              "asset_no": this.detail_info.asset_no,
              "polymer_trademark": this.detail_info.polymer_trademark,
              "mold_no": this.detail_info.mold_no,
              "polymer_abbreviation": this.detail_info.polymer_abbreviation,
              "product_name": this.detail_info.product_name,
              "machine_trademark": this.detail_info.machine_trademark,
              "pressure_unit": this.detail_info.pressure_unit,
          }
  
          machineTrialsMethod.add(machine_trial_index)
            .then(res => {
              if (res.status == 0) {
                this.detail_info.machine_trial_id = res.data.id

                loadSensitivityMethod.add(this.detail_info)
                .then(res => {
                  if (res.status == 0) {
                    this.$message({ message: "保存成功！", type: 'success' })
                    this.$emit("close")
                  }
                })
              }
            })
            .finally(() => {
              this.loading = false
            })
          } else {
            let machine_trial_index = {
              "company_id": UserModule.company_id,
              "machine_trial_type": "load_sensitivity",
              "machine_data_source": this.detail_info.machine_data_source,
              "asset_no": this.detail_info.asset_no,
              "polymer_trademark": this.detail_info.polymer_trademark,
              "mold_no": this.detail_info.mold_no,
              "polymer_abbreviation": this.detail_info.polymer_abbreviation,
              "product_name": this.detail_info.product_name,
              "machine_trademark": this.detail_info.machine_trademark,
            }
            machineTrialsMethod.edit(machine_trial_index ,this.detail_info.machine_trial_id)
            .then(res => {
              if (res.status == 0) {
                loadSensitivityMethod.add(this.detail_info)
                .then(res => {
                  this.$message({ message: "编辑成功！", type: 'success' })
                  this.$emit("close")
                })
                .finally(() => {
                  this.loading = false
                })
              }
            })
          }
        } else {
          this.loading = false
        }
      })
    },
    resetView() {
      this.detail_info = {
        machine_trial_id: null,
        mold_no: null,
        machine_data_source: null,
        asset_no: null,
        polymer_abbreviation: null,
        polymer_trademark: null,
        cycle: null,
        product_name: null,
        cavity_num: null,
        machine_trademark: null,
        trial_name: null,
        mold_trial_date: null,

        table_data: [{
          title: "高速",
          inj_time_nomal: null,
          inj_time_empty: null,
          peak_pres_nomal: null,
          peak_pres_empty: null,
          result: null,
        }, {
          title: "中速",
          inj_time_nomal: null,
          inj_time_empty: null,
          peak_pres_nomal: null,
          peak_pres_empty: null,
          result: null,
        }, {
          title: "低速",
          inj_time_nomal: null,
          inj_time_empty: null,
          peak_pres_nomal: null,
          peak_pres_empty: null,
          result: null,
        }]
      }
    }
  },
  computed: {
    tableDataComputed() {
      for (let i = 0; i < this.detail_info.table_data.length; ++i) {
        let table_row = this.detail_info.table_data[i]
        
        if (table_row.inj_time_nomal && table_row.inj_time_empty
        && table_row.peak_pres_nomal && table_row.peak_pres_empty) {
          let a = (table_row.inj_time_nomal - table_row.inj_time_empty) * 100 / table_row.inj_time_nomal
          let b = (this.unit_exchange(table_row.peak_pres_nomal, this.detail_info.pressure_unit) - 
            this.unit_exchange(table_row.peak_pres_empty, this.detail_info.pressure_unit)) / 10000
          table_row.result = Number(Math.abs(a / b).toFixed(2))
        } else {
          table_row.result = null
        }
      }
      return this.detail_info.table_data;
    },
  },
};
</script>

<style lang="scss" scoped>

.el-form-item .el-input {
  width: 10rem;
}

#colors {
  color: red;
}

.el-card {
  font-size: 15px;
  line-height: 21px;
}
</style>
