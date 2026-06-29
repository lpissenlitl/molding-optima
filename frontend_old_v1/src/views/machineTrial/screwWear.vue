<template>
  <div>
    <h1 style="text-align: center">螺杆磨损测试试验表</h1>

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
          style="width: 10rem"
          :fetch-suggestions="queryMacDataSourceList"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="注塑机型号" prop="machine_trademark">
        <el-autocomplete
          v-model="detail_info.machine_trademark"
          placeholder="注塑机型号"
          clearable
          style="width: 10rem"
          :fetch-suggestions="queryTrademarkList"
          @select="handleTrademarkSelect"
        >
          <template slot-scope="{ item }">
            <el-tooltip
              effect="dark"
              :content="'设备编码: ' + [item.serial_no? item.serial_no: '未知']"
              placement="right-end"
            >
              <div
                style="
                  width: auto;
                  overflow: hidden;
                  text-overflow: ellipsis;
                  white-space: nowrap;
                "
              >
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
          style="width: 10rem"
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
          style="width: 10rem"
          :fetch-suggestions="queryPolymerTrademarkList"
          @select="handlePolySelect"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="模具编号" prop="mold_no">
        <el-autocomplete
          v-model="detail_info.mold_no"
          :fetch-suggestions="queryMoldNo"
          placeholder="模具编号"
          @select="handleMoldNoSelect"
          style="width: 10rem"
        >
        </el-autocomplete>
      </el-form-item>

      <el-form-item label="制品名称">
        <el-input v-model="detail_info.product_name"></el-input>
      </el-form-item>

      <el-form-item label="模穴数">
        <el-input v-model="detail_info.cavity_num"></el-input>
      </el-form-item>

      <el-form-item label="测试人员">
        <el-input v-model="detail_info.trial_name"></el-input>
      </el-form-item>

      <el-divider content-position="center">
        <span style="color: blue">测试数据记录表</span>
      </el-divider>

      <el-form-item label="注射单元">
        <el-select
          v-model="detail_info.inject_part" 
          placeholder="请选择" 
          style="width: 10rem"
          @change="handleInjectPart"
        >
          <el-option
            v-for="item, index in inject_part_options"
            :key="index"
            :label="item.label"
            :value="item.value"
          ></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="注塑机螺杆最大行程">
        <el-input readonly size="mini" v-model="detail_info.max_injection_stroke">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="注射起始位置">
        <el-input type="number" size="mini" v-model="detail_info.injection_starting_position">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="间隔">
        <el-input type="number" size="mini" v-model="detail_info.interval">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>
      <br>
      <div style="text-align: center">
        <el-button
          size="mini"
          type="primary"
          @click="initSettingVelocity" 
        >
          确定
        </el-button>
      </div>

      <el-table
        style="width: 100%"
        height-current-row
        :data="tableDataCoumputed" 
        :height="tableHeight"
        :cell-style="{padding: '4px'}"
      >
        <el-table-column prop="title" label="模次" align="center" width="150">
        </el-table-column>

        <el-table-column
          v-for="i in 7"
          :key="i"
          :prop="String(i)"
          :label="'#' + String(i)"
          align="center"
          min-width="120"
        >
          <template slot-scope="scope">
            <el-input
              type="number" 
              size="mini"
              v-model="scope.row.sections[i - 1]"
              :disabled="scope.row.title == '理论值(g)'||scope.row.title == '螺杆前进行程(mm)'||scope.row.title == '体积(cm³)'"
            ></el-input>
          </template>
        </el-table-column>
      </el-table>

      <el-collapse v-model="active_names">
        <el-collapse-item class="collapseItemTitle" name="chart" title="理论值与实际值关系曲线">
          <v-chart style="margin:auto" :options="chart_options" @click="onChartClick" />
        </el-collapse-item>
      </el-collapse>

      <div class="nextButton">
        <el-button type="danger" size="small" @click="resetView">
          重 置
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
    </el-form>
  </div>
</template>

<script>
let echarts = require('echarts/lib/echarts');
require('echarts/lib/chart/bar');
require('echarts/lib/component/tooltip');
require('echarts/lib/component/title');

import { getOptions, projectMethod, polymerMethod, screwWearMethod, machineTrialsMethod} from "@/api";
import { UserModule } from "@/store/modules/user";
import { initArray } from "@/utils/array-help";
import * as unit_change from "@/utils/unit-change"

export default {
  name: "ScrewWear",
  props: {
    id: {
      type: Number,
      default: null,
    },
  },
  data() {
    return {
      detail_info: {
        machine_trial_id: null,
        mold_no: null,
        machine_id:null,
        polymer_id:null,
        mold_id:null,
        machine_data_source: null,
        asset_no: null,
        injectors: [],
        polymer_abbreviation: null,
        polymer_trademark: null,
        cycle: null,
        product_name: null,
        cavity_num: null,
        machine_trademark: null,
        trial_name: UserModule.engineer,
        mold_trial_date: null,

        inject_part: null,
        max_injection_stroke: null,
        injection_starting_position: null,
        interval: null,

        melt_density: null,

        table_data: [
          {
            title: "停止位置(mm)",
            sections: initArray(7, null),
          },
          {
            title: "螺杆前进行程(mm)",
            sections: initArray(7, null),
          },
          {
            title: "理论值(g)",
            sections: initArray(7, null),
          },{
            title: "制品+流道(g)",
            sections: initArray(7, null),
          },{
            title: "体积(cm³)",
            sections: initArray(7, null),
          }
        ]
      },
      active_names: [ "chart" ],
      chart_options: {
        title:{ text:'' },
        tooltip:{
          trigger:'axis',
        },
        legend: {
          y: 'bottom',
          x: 'center',
          data:['1','2']
        },
        xAxis: {
          type: 'value',
          scale: false,
          name:"螺杆前进的行程(mm)",
          nameTextStyle: {
            padding: [0, 0, -60, -250]    // 四个数字分别为上右下左与原位置距离
          },
          axisLabel: {
            formatter:"{value}"
          },
          splitLine: {
            show:false
          },
        },
        yAxis: {
          type: "value",
          scale: false,
          name:"制品+流道重量(g)",
          axisLabel: {
            formatter: "{value}"
          },
          splitLine: {
            show: false
          }
        },
        series: [
          {
            name:'理论值',
            type:'line',
            data:[],
          },
          {
            name:'制品+流道重量',
            type:'line',
            data:[]
          }
        ]
      },
      loading: false,
      tableHeight: 240,
      mac_data_source_list: [],
      mac_trademark_list: [],
      poly_abbreviation_list: [],
      poly_trademark_dict: [],
      idx: null,
      rules: {
        mold_no: [{ required: true, message: "模具编号不能为空" }],
        machine_data_source: [
          { required: true, message: "注塑机来源不能为空" },
        ],
        machine_trademark: [{ required: true, message: "注塑机型号不能为空" }],
        polymer_abbreviation: [{ required: true, message: "塑料简称不能为空" }],
        polymer_trademark: [{ required: true, message: "塑料牌号不能为空" }],
      },
    };
  },
  created() {
    getOptions("machine_data_source", {}).then((res) => {
      if (res.status === 0) {
        this.mac_data_source_list.length = 0;
        for (let i = 0; i < res.data.length; ++i) {
          this.mac_data_source_list.push({ value: res.data[i].value });
        }
      }
    }),
    getOptions("polymer_abbreviation").then((res) => {
      // 塑料简称
      if (res.status === 0 && Array.isArray(res.data)) {
        this.poly_abbreviation_list.length = 0;
        for (let i = 0; i < res.data.length; ++i) {
          this.poly_abbreviation_list.push({ value: res.data[i].value });
        }
      }
    });
  },
  mounted() {
    this.loadData()
  },
  methods: {
    queryMacDataSourceList(queryString, cb) {
      var mac_data_source_list = this.mac_data_source_list;
      var results = queryString
        ? mac_data_source_list.filter(this.createStateFilter(queryString))
        : mac_data_source_list;
      cb(results);
    },
    queryAbbreviationList(queryString, cb) {
      var poly_abbreviation_list = this.poly_abbreviation_list;
      var results = queryString
        ? poly_abbreviation_list.filter(this.createStateFilter(queryString))
        : poly_abbreviation_list;
      cb(results);
    },
    queryPolymerTrademarkList(queryString, cb) {
      var poly_trademark_dict = this.poly_trademark_dict;
      var results = queryString
        ? poly_trademark_dict.filter(this.createStateFilter(queryString))
        : poly_trademark_dict;
      cb(results);
    },
    queryTrademarkList(queryString, cb) {
      queryString = queryString == null ? "" : queryString;

      if (!this.detail_info.machine_data_source) {
        return [];
      }

      let promptList = [];
      getOptions("machine_trademark", {
        data_source: this.detail_info.machine_data_source,
        trademark: queryString,
      }).then((res) => {
        if (res.status == 0) {
          for (let i = 0; i < res.data.length; ++i) {
            promptList.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
              serial_no: res.data[i].serial_no,
              injectors: res.data[i].injectors
            });
          }
          cb(promptList);
        }
      });
    },
    queryMoldNo(str, cb) {
      str = str == null ? "" : str;
      let promptList = [];
      getOptions("mold_no", { form_input: str, db_table: "mold" }).then(
        (res) => {
          if (res.status == 0) {
            for (let i = 0; i < res.data.length; i++) {
              promptList.push(res.data[i]);
            }
          }
        }
      );
      cb(promptList);
    },
    handleTrademarkSelect(item) {
      this.detail_info.asset_no = item.asset_no
      this.detail_info.injectors = item.injectors
      this.detail_info.machine_id = item.id
    },
    handleInjectPart(item) {
      this.idx = item
      this.detail_info.max_injection_stroke = this.detail_info.injectors[Number(item)].max_injection_stroke
    },
    createStateFilter(queryString) {
      return (state) => {
        return (
          state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
        );
      };
    },
    handleAbbreviationSelect() {
      getOptions("polymer_trademark", {
        abbreviation: this.detail_info.polymer_abbreviation,
      }).then((res) => {
        if (res.status === 0 && Array.isArray(res.data)) {
          this.poly_trademark_dict.length = 0;
          for (let i = 0; i < res.data.length; ++i) {
            this.poly_trademark_dict.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
            });
          }
        }
      });
    },
    handlePolySelect(item) {
      polymerMethod.getDetail(item.id)
      .then(res => {
        if (res.status === 0) {
          // 拿材料密度
          this.detail_info.melt_density = res.data.melt_density
          this.detail_info.polymer_id = res.data.id
        }
      })
    },
    handleMoldNoSelect(item) {
      projectMethod.getDetail(item.mold_id).then((res) => {
        if (res.data.mold_info.product_infos.length > 0) {
          this.detail_info.product_name =
            res.data.mold_info.product_infos[0].product_name;
        }
        this.detail_info.cavity_num = res.data.mold_info.cavity_num;
        this.detail_info.mold_id = item.mold_id
      });
    },
    initSettingVelocity() {
      if (!this.detail_info.injection_starting_position) {
        this.$alert("请填写合适的注射起始位置！", "提示！", {
          confirmButtonText: '确定'
        })
        return
      }

      if (!this.detail_info.interval) {
        this.$alert("请填写合适的间隔位置！", "提示！", {
          confirmButtonText: '确定'
        })
        return
      }

      if (Number(this.detail_info.injection_starting_position) > Number(this.detail_info.max_injection_stroke)) {
        this.$alert("注射起始位置不能大于注塑机螺杆最大行程！", "提示！", {
          confirmButtonText: '确定'
        })
        return
      }

      for (let i = 0; i < 7; i++) {
        this.detail_info.table_data[0].sections[i] = Number(this.detail_info.injection_starting_position) - (this.detail_info.interval*(i+1))
        this.detail_info.table_data[1].sections[i] = Number(this.detail_info.interval) + Number(this.detail_info.interval*i)
        this.detail_info.table_data[2].sections[i] = (unit_change.getScrewArea(this.detail_info.injectors[Number(this.idx)]) * this.detail_info.table_data[1].sections[i]
        * this.detail_info.melt_density/1000).toFixed(2)
      }
      this.$set(this.detail_info.table_data)
    },
    loadData() {
      if (this.id) {
        screwWearMethod
          .get({
            machine_trial_id: this.id,
          })
          .then((res) => {
            if (res.status == 0) {
              if (res.data && JSON.stringify(res.data) != "{}") {
                this.detail_info = res.data;
              } else {
                this.detail_info.machine_trial_id = this.id;
              }
            }
          }); 
      }
    },
    saveData() {
      this.loading = true;
      this.$refs["detail_info"].validate((valid) => {
        if (valid) {
          if (!this.detail_info.machine_trial_id) {
            let machine_trial_index = {
              company_id: UserModule.company_id,
              machine_trial_type: "screw_wear",
              machine_data_source: this.detail_info.machine_data_source,
              asset_no: this.detail_info.asset_no,
              polymer_trademark: this.detail_info.polymer_trademark,
              mold_no: this.detail_info.mold_no,
              polymer_abbreviation: this.detail_info.polymer_abbreviation,
              product_name: this.detail_info.product_name,
              machine_trademark: this.detail_info.machine_trademark,

              mold_id: this.detail_info.mold_id,
              machine_id:this.detail_info.machine_id,
              polymer_id:this.detail_info.polymer_id
            };

            machineTrialsMethod
              .add(machine_trial_index)
              .then((res) => {
                if (res.status == 0) {
                  this.detail_info.machine_trial_id = res.data.id;

                  screwWearMethod
                    .add(this.detail_info)
                    .then((res) => {
                      if (res.status == 0) {
                        this.$message({
                          message: "保存成功！",
                          type: "success",
                        });
                        this.$emit("close");
                      }
                    });
                }
              })
              .finally(() => {
                this.loading = false;
              });
          } else {
            let machine_trial_index = {
              company_id: UserModule.company_id,
              machine_trial_type: "screw_wear",
              machine_data_source: this.detail_info.machine_data_source,
              asset_no: this.detail_info.asset_no,
              polymer_trademark: this.detail_info.polymer_trademark,
              mold_no: this.detail_info.mold_no,
              polymer_abbreviation: this.detail_info.polymer_abbreviation,
              product_name: this.detail_info.product_name,
              machine_trademark: this.detail_info.machine_trademark,
            };
            machineTrialsMethod
              .edit(machine_trial_index, this.detail_info.machine_trial_id)
              .then((res) => {
                if (res.status == 0) {
                  screwWearMethod
                    .add(this.detail_info)
                    .then((res) => {
                      this.$message({ message: "编辑成功！", type: "success" });
                      this.$emit("close");
                    })
                    .finally(() => {
                      this.loading = false;
                    });
                }
              });
          }
        } else {
          this.loading = false
        }
      });
    },
    resetView() {
      this.detail_info = {
        machine_trial_id: null,
        mold_no: null,
        machine_id:null,
        polymer_id:null,
        mold_id:null,
        machine_data_source: null,
        asset_no: null,
        polymer_abbreviation: null,
        polymer_trademark: null,
        cycle: null,
        product_name: null,
        cavity_num: null,
        machine_trademark: null,
        trial_name: UserModule.engineer,
        mold_trial_date: null,

        inject_part: null,
        max_injection_stroke: null,
        injection_starting_position: null,
        interval: 10,

        melt_density: null,

        table_data: [
          {
            title: "停止位置(mm)",
            sections: initArray(7, null),
          },
          {
            title: "螺杆前进行程(mm)",
            sections: initArray(7, null),
          },
          {
            title: "理论值(g)",
            sections: initArray(7, null),
          },{
            title: "制品+流道(g)",
            sections: initArray(7, null),
          },{
            title: "体积(cm³)",
            sections: initArray(7, null),
          }
        ]
      }
    },
    setChartData() {
      let data1 = [];
      let data2 = []
      for (let i = 0; i < 7; i++) {
        let x = Number(this.detail_info.table_data[1].sections[i])
        let y1 = Number(this.detail_info.table_data[2].sections[i])

        let y2 = Number(this.detail_info.table_data[3].sections[i])
        data1.push([x,y1])
        data2.push([x,y2])
      }
      this.chart_options.series[0].data = data1
      this.chart_options.series[1].data = data2
    },
    onChartClick(e) {
    }
  },
  computed: {
    tableDataCoumputed: function() {
      this.detail_info.table_data[3].sections.forEach(element => {
        if (element) {
          this.setChartData()
        }
      });
      for (let i = 0; i < 7; i++) {
        this.detail_info.table_data[4].sections[i] = (this.detail_info.table_data[3].sections[i]/this.detail_info.melt_density).toFixed(2) 
      }
      return this.detail_info.table_data;
    },
    inject_part_options: function() {
      let options = [
        {label: "主射台", value: "0"},
        {label: "副射台", value: "1"},
        {label: "三射台", value: "2"},
        {label: "四射台", value: "3"},
        {label: "五射台", value: "4"},
        {label: "六射台", value: "5"},
        {label: "七射台", value: "6"}
      ]
      options = options.slice(0, this.detail_info.injectors.length)
      return options
    }
  },
  watch: {
    
  }
};
</script>

<style lang="scss" scoped>
.el-form-item .el-input {
  width: 10rem;
}

</style>