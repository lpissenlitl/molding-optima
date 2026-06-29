<template>
  <div>
    <h1 style="text-align: center">稳定性评估测试试验表</h1>
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

      <el-divider content-position="center">
        <span style="color: blue">测试数据记录表</span>
      </el-divider>

      <el-form-item label="模具测试次数" label-width="9rem">
        <el-select
          v-model="detail_info.trial_no"
          @change="onTrialNoChanged"
          :allow-create="true"
          filterable
        >
          <el-option
            v-for="item in trial_no_options"
            :key="item"
            :label="item"
            :value="item"
          >
          </el-option>
        </el-select>
      </el-form-item>

      <el-table
        :data="tableDataComputed"
        size="mini"
        height-current-row
        :cell-style="{ padding: '8px' }"
        style="width: 100%"
      >
        <el-table-column
          prop="title"
          label="测试序号"
          align="center"
          width="120"
        >
        </el-table-column>

        <el-table-column
          prop="cycle_time"
          label="循环时间（s）"
          align="center"
          min-width="120"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.cycle_time"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="injection_time"
          label="射胶时间（s）"
          align="center"
          min-width="120"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.injection_time"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="measure_time"
          label="计量时间（s）"
          align="center"
          min-width="120"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.measure_time"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="residual_posi"
          label="残余量位置（mm）"
          align="center"
          min-width="120"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.residual_posi"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="metering_ending_position"
          label="计量终止位置（mm）"
          align="center"
          min-width="120"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.metering_ending_position"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="injection_pres"
          label="射胶峰压"
          align="center"
          min-width="120"
        >
          <template #header>
            <div>射胶峰压</div>
            <div>{{detail_info.pressure_unit}}</div>
          </template>
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.injection_pres"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="tipacking_presme"
          label="保压切换压力（MPa）"
          align="center"
          min-width="120"
        >
          <template #header>
            <div>保压切换压力</div>
            <div>{{detail_info.pressure_unit}}</div>
          </template>
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.packing_pres"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column>

        <!-- <el-table-column
          prop="backing_pres"
          label="背压（MPa）"
          align="center"
          min-width="120"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.backing_pres"
              :disabled="scope.$index >= detail_info.trial_no"
            ></el-input>
          </template>
        </el-table-column> -->
      </el-table>
    </el-form>

    <div style="height: 35px" />

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
  </div>
</template>

<script>
import {
  stabilityAssessMethod,
  machineTrialsMethod,
  getOptions,
  projectMethod,
  machineMethod
} from "@/api";
import { UserModule } from "@/store/modules/user";
import { initArray } from "@/utils/array-help";

export default {
  name: "StabilityAssessment",
  data() {
    return {
      detail_info: {
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
        trial_name: UserModule.engineer,
        mold_trial_date: null,
        pressure_unit: null,

        trial_no: 30,
        table_data: initArray(36, {
          title: null,
          cycle_time: null,
          injection_time: null,
          measure_time: null,
          residual_posi: null,
          metering_ending_position: null,
          injection_pres: null,
          packing_pres: null,
          backing_pres: null,
        }),
      },
      loading: false,
      trial_no_options: [],
      table_column: [
        "cycle_time",
        "injection_time",
        "measure_time",
        "residual_posi",
        "metering_ending_position",
        "injection_pres",
        "packing_pres",
        "backing_pres",
      ],
      mac_data_source_list: [],
      mac_trademark_list: [],
      poly_abbreviation_list: [],
      poly_trademark_dict: [],
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
  props: {
    id: {
      type: Number,
      default: null,
    },
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
    this.constructTableData();
    this.loadData();
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
      this.detail_info.asset_no = item.asset_no;
      this.update_machine_unit(item)
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
    createStateFilter(queryString) {
      return (state) => {
        return (
          state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
        );
      };
    },
    handleMacDataSourceSelect() {
      getOptions("machine_trademark", {
        data_source: this.detail_info.machine_data_source,
      }).then((res) => {
        if (res.status === 0 && Array.isArray(res.data)) {
          this.mac_trademark_list.length = 0;
          for (let i = 0; i < res.data.length; ++i) {
            this.mac_trademark_list.push({
              id: res.data[i].id,
              value: res.data[i].trademark,
            });
          }
        }
      });
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
    handleMoldNoSelect(item) {
      projectMethod.getDetail(item.mold_id).then((res) => {
        if (res.data.mold_info.product_infos.length > 0) {
          this.detail_info.product_name =
            res.data.mold_info.product_infos[0].product_name;
        }
        this.detail_info.cavity_num = res.data.mold_info.cavity_num;
      });
    },
    constructTableData() {
      let result_title = [
        "MAX",
        "AVERAGE",
        "MIN",
        "偏差",
        "偏差率(%)",
        "可接收范围(%)",
      ];
      let table_row_count = this.detail_info.table_data.length;
      for (let i = 0; i < table_row_count; ++i) {
        let table_row = this.detail_info.table_data[i];
        if (i < table_row_count - 6) {
          table_row.title = String(i + 1);
        } else if (i < table_row_count - 1) {
          table_row.title = result_title[i - (table_row_count - 6)];
        } else if (i == table_row_count - 1) {
          table_row.title = result_title[i - (table_row_count - 6)];
          table_row.cycle_time = 10;
          table_row.injection_time = 5;
          table_row.measure_time = 10;
          table_row.residual_posi = 5;
          table_row.metering_ending_position = 10;
          table_row.injection_pres = 10;
          table_row.packing_pres = 10;
          table_row.backing_pres = 10;
        }
      }

      this.trial_no_options = [];
      for (let i = 1; i <= 30; ++i) {
        this.trial_no_options.push(i);
      }
    },
    onTrialNoChanged(val) {
      if (Number(val) <= Number(this.detail_info.table_data.length - 6)) {
        let beg = Number(val);
        let end = Number(this.detail_info.table_data.length) - 6;
        this.detail_info.table_data.splice(beg, end - beg);
      } else if (Number(val) > Number(this.detail_info.table_data.length - 6)) {
        let beg = Number(this.detail_info.table_data.length - 6);
        let end = Number(val);
        for (let i = beg; i < end; ++i) {
          this.detail_info.table_data.splice(i, 0, {
            title: i + 1,
            cycle_time: null,
            injection_time: null,
            measure_time: null,
            residual_posi: null,
            metering_ending_position: null,
            injection_pres: null,
            packing_pres: null,
            backing_pres: null,
          });
        }
      }
    },
    loadData() {
      if (this.id) {
        stabilityAssessMethod
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
              machine_trial_type: "stability_assessment",
              mold_no: this.detail_info.mold_no,
              machine_data_source: this.detail_info.machine_data_source,
              asset_no: this.detail_info.asset_no,
              polymer_trademark: this.detail_info.polymer_trademark,
              polymer_abbreviation: this.detail_info.polymer_abbreviation,
              product_name: this.detail_info.product_name,
              machine_trademark: this.detail_info.machine_trademark,
            };

            machineTrialsMethod
              .add(machine_trial_index)
              .then((res) => {
                if (res.status == 0) {
                  this.detail_info.machine_trial_id = res.data.id;

                  stabilityAssessMethod.add(this.detail_info).then((res) => {
                    if (res.status == 0) {
                      this.$message({ message: "保存成功！", type: "success" });
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
              machine_trial_type: "stability_assessment",
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
                  stabilityAssessMethod
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

        trial_no: 30,
        table_data: initArray(36, {
          title: null,
          cycle_time: null,
          injection_time: null,
          measure_time: null,
          residual_posi: null,
          metering_ending_position: null,
          injection_pres: null,
          packing_pres: null,
          backing_pres: null,
        }),
      };
      this.constructTableData();
    },
    updateResult(ave, min, max, dev, dev_ratio, column) {
      let table_column = this.table_column;
      this.detail_info.table_data[Number(this.detail_info.trial_no) + 0][
        table_column[column]
      ] = max;
      this.detail_info.table_data[Number(this.detail_info.trial_no) + 1][
        table_column[column]
      ] = ave;
      this.detail_info.table_data[Number(this.detail_info.trial_no) + 2][
        table_column[column]
      ] = min;
      this.detail_info.table_data[Number(this.detail_info.trial_no) + 3][
        table_column[column]
      ] = dev;
      this.detail_info.table_data[Number(this.detail_info.trial_no) + 4][
        table_column[column]
      ] = dev_ratio;
    },
  },
  watch: {},
  computed: {
    tableDataComputed() {
      let trial_result = {
        max: initArray(8, 0),
        min: initArray(8, 99999999),
        average: initArray(8, null),
        total: initArray(8, 0),
        count: initArray(8, 0),
        deviation: initArray(8, null),
        deviation_ratio: initArray(8, null),
      };

      let table_column = this.table_column;

      for (let i = 0; i < this.detail_info.trial_no; ++i) {
        let table_row = this.detail_info.table_data[i];

        for (let j = 0; j < table_column.length; ++j) {
          if (table_row[table_column[j]]) {
            trial_result.count[j]++;
            trial_result.total[j] += Number(table_row[table_column[j]]);

            if (
              Number(trial_result.max[j]) <= Number(table_row[table_column[j]])
            ) {
              trial_result.max[j] = table_row[table_column[j]];
            }

            if (
              Number(trial_result.min[j]) >= Number(table_row[table_column[j]])
            ) {
              trial_result.min[j] = table_row[table_column[j]];
            }
          }

          if (trial_result.max[j] && trial_result.min[j]) {
            trial_result.deviation[j] = Number(
              trial_result.max[j] - trial_result.min[j]
            ).toFixed(2);
          }

          if (trial_result.count[j] > 0) {
            if (trial_result.total[j] && trial_result.count[j]) {
              trial_result.average[j] = Number(
                trial_result.total[j] / trial_result.count[j]
              ).toFixed(2);
            }

            if (trial_result.deviation[j] && trial_result.average[j]) {
              trial_result.deviation_ratio[j] = Number(
                (trial_result.deviation[j] / trial_result.average[j]) * 100
              ).toFixed(2);
            }

            this.updateResult(
              trial_result.average[j],
              trial_result.min[j],
              trial_result.max[j],
              trial_result.deviation[j],
              trial_result.deviation_ratio[j],
              j
            );
          } else {
            this.updateResult(null, null, null, null, null, j);
          }
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

.el-select {
  width: 6rem;
}
</style>