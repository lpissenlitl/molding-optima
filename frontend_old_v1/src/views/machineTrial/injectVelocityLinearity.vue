<template>
  <div>
    <h1 style="text-align: center">注射速度线性测试试验表</h1>

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

      <el-card shadow="never">
        <span id="colors">测试目的</span>：
        <p style="text-indent: 2em">评估注塑机的注射速度控制能力。</p>
        <span id="colors">测试原理</span>：
        <p style="text-indent: 2em">
          注塑机速度线性度反映的是注塑机的速度控制能力，
          是比较设定速度与实际速度之间的差异。这个差异越大，
          说明注塑机的速度控制性能越差。最理想的注塑机是速度线性度为0，
          设定速度与实际速度之间没有差异。
        </p>
        <span id="colors">测试标准</span>：
        <p style="text-indent: 2em">
          通常，对于精密注塑来讲， 速度线性度的绝对值小于10%，是可以接受的。
        </p>
        <span id="colors">测试设备</span>：
        <ol>
          <li>注塑机</li>
          <li>模具</li>
        </ol>
        <span id="colors">测试方法</span>：
        <ol>
          <li>
            确保射胶量大于最大射胶量的30%。如果小于30%，用空射或空转来测试。
          </li>
          <li>设置注塑机以标准的两阶段成型工艺运行。</li>
          <li>关掉保压压力和时间。</li>
          <li>用最快的射胶速度，调整切换位置使零件达到90%满。</li>
          <li>设置注射时间足够大。</li>
          <li>设置注射速度足够低。</li>
          <li>注射一模，记录填充时间。</li>
          <li>速度增加一倍，注射后记录填充时间。</li>
          <li>速度再增加一倍。</li>
          <li>连续增加速度一倍，直到达到最大速度。</li>
        </ol>
      </el-card>

      <div style="height: 12px" />

      <el-divider content-position="center">
        <span style="color: blue">测试数据记录表</span>
      </el-divider>

      <el-form-item label="计量终止位置" prop="metering_ending_position">
        <el-input
          v-model="detail_info.metering_ending_position"
          style="width: 8rem"
        >
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item
        label="计量后松退距离"
        prop="decompressure_distance_after_metering"
      >
        <el-input
          v-model="detail_info.decompressure_distance_after_metering"
          style="width: 8rem"
        >
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="切换位置" prop="vp_switch_position">
        <el-input v-model="detail_info.vp_switch_position" style="width: 8rem">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="线性行程" prop="injection_distance">
        <el-input
          v-model="detail_info.injection_distance"
          style="width: 8rem"
          :disabled="true"
        >
          <span slot="suffix">mm</span>
        </el-input>
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
          type="index"
          align="center"
          label="测试序号"
          width="80"
        >
        </el-table-column>

        <el-table-column
          prop="setting_inject_velo"
          label="设定注射速度（mm/s）"
          align="center"
          width="160"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.setting_inject_velo"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="theory_fill_time"
          label="理论填充时间（s）"
          align="center"
          width="160"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.theory_fill_time"
              :disabled="true"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="actual_fill_time"
          label="实际填充时间（s）"
          align="center"
          width="160"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.actual_fill_time"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="actual_inject_velo"
          label="实际注射速度（mm/s）"
          align="center"
          width="160"
        >
          <template slot-scope="scope">
            <el-input
              size="mini"
              v-model="scope.row.actual_inject_velo"
              :disabled="true"
            ></el-input>
          </template>
        </el-table-column>

        <el-table-column
          prop="deviation_ratio"
          label="差异百分比（%）"
          align="center"
          width="160"
        >
          <template slot-scope="scope">
            <el-form>
              <el-input
                size="mini"
                v-model="scope.row.deviation_ratio"
                :disabled="true"
              ></el-input>
            </el-form>
          </template>
        </el-table-column>
      </el-table>

      <div style="height: 30px"></div>

      <el-form-item label="平均差异百分比">
        <el-input v-model="detail_info.ave_deviation_ratio">
          <span slot="suffix">%</span>
        </el-input>
      </el-form-item>

      <el-form-item label="实际线性范围">
        <el-input v-model="detail_info.act_linear_range"></el-input>
      </el-form-item>

      <br />

      <el-form-item label="螺杆最大行程">
        <el-input v-model="detail_info.screw_max_stroke">
          <span slot="suffix">mm</span>
        </el-input>
      </el-form-item>

      <el-form-item label="螺杆使用比例">
        <el-input v-model="detail_info.screw_used_ratio"></el-input>
      </el-form-item>
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
  injectVeloLineMethod,
  machineTrialsMethod,
  getOptions,
  projectMethod,
} from "@/api";
import { UserModule } from "@/store/modules/user";
import { initArray } from "@/utils/array-help";

export default {
  name: "InjectVelocityLinearity",
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

        metering_ending_position: null,
        decompressure_distance_after_metering: null,
        vp_switch_position: null,
        injection_distance: null,

        table_data: initArray(10, {
          title: "模次",
          setting_inject_velo: null,
          theory_fill_time: null,
          actual_fill_time: null,
          actual_inject_velo: null,
          deviation_ratio: null,
        }),

        ave_deviation_ratio: null,
        act_linear_range: null,
        screw_max_stroke: null,
        screw_used_ratio: null,
      },
      loading: false,
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
            this.detail_info.screw_max_stroke =
              res.data[i].max_injection_stroke;
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
        this.detail_info.product_name =
          res.data.mold_info.product_infos[0].product_name;
        this.detail_info.cavity_num = res.data.mold_info.cavity_num;
      });
    },
    loadData() {
      if (this.id) {
        injectVeloLineMethod
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
              machine_trial_type: "inject_velocity_linearity",
              machine_data_source: this.detail_info.machine_data_source,
              asset_no: this.detail_info.asset_no,
              polymer_trademark: this.detail_info.polymer_trademark,
              mold_no: this.detail_info.mold_no,
              polymer_abbreviation: this.detail_info.polymer_abbreviation,
              product_name: this.detail_info.product_name,
              machine_trademark: this.detail_info.machine_trademark,
            };

            machineTrialsMethod
              .add(machine_trial_index)
              .then((res) => {
                if (res.status == 0) {
                  this.detail_info.machine_trial_id = res.data.id;

                  injectVeloLineMethod.add(this.detail_info).then((res) => {
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
              machine_trial_type: "inject_velocity_linearity",
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
                  injectVeloLineMethod
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

        metering_ending_position: null,
        decompressure_distance_after_metering: null,
        vp_switch_position: null,
        injection_distance: null,

        table_data: initArray(10, {
          title: "模次",
          setting_inject_velo: null,
          theory_fill_time: null,
          actual_fill_time: null,
          actual_inject_velo: null,
          deviation_ratio: null,
        }),

        ave_deviation_ratio: null,
        act_linear_range: null,
        screw_max_stroke: null,
        screw_used_ratio: null,
      };
    },
    updateResult(ave, max, min) {
      this.detail_info.ave_deviation_ratio = ave;
      if (min && max) this.detail_info.act_linear_range = min + "~~" + max;
      else this.detail_info.act_linear_range = null;
    },
  },
  watch: {
    detail_info: {
      handler: function () {
        if (
          this.detail_info.metering_ending_position &&
          this.detail_info.decompressure_distance_after_metering &&
          this.detail_info.vp_switch_position
        ) {
          this.detail_info.injection_distance =
            Number(this.detail_info.metering_ending_position) +
            Number(this.detail_info.decompressure_distance_after_metering) -
            Number(this.detail_info.vp_switch_position);
        }

        if (
          this.detail_info.injection_distance &&
          this.detail_info.screw_max_stroke
        ) {
          this.detail_info.screw_used_ratio = (
            Number(this.detail_info.injection_distance) /
            Number(this.detail_info.screw_max_stroke)
          ).toFixed(2);
        }
      },
      deep: true,
    },
  },
  computed: {
    tableDataComputed() {
      let inject_distance = this.detail_info.injection_distance;
      let total = 0;
      let ave = 0;
      let count = 0;
      let min = 99999999;
      let max = -99999999;

      for (let i = 0; i < 10; ++i) {
        let table_row = this.detail_info.table_data[i];

        if (inject_distance && table_row.setting_inject_velo) {
          table_row.theory_fill_time = (
            Number(inject_distance) / Number(table_row.setting_inject_velo)
          ).toFixed(2);
        }

        if (inject_distance && table_row.actual_fill_time) {
          table_row.actual_inject_velo = (
            Number(inject_distance) / Number(table_row.actual_fill_time)
          ).toFixed(2);
        }

        if (table_row.actual_inject_velo && table_row.setting_inject_velo) {
          ++count;
          table_row.deviation_ratio = (
            ((Number(table_row.actual_inject_velo) -
              Number(table_row.setting_inject_velo)) *
              100) /
            Number(table_row.setting_inject_velo)
          ).toFixed(2);
          total += Number(table_row.deviation_ratio);

          if (Number(max) <= Number(table_row.deviation_ratio)) {
            max = table_row.deviation_ratio;
          }

          if (Number(min) >= Number(table_row.deviation_ratio)) {
            min = table_row.deviation_ratio;
          }
        }
      }

      if (count > 0) {
        ave = (total / count).toFixed(2);
        this.updateResult(ave, max, min);
      } else {
        this.updateResult(null, null, null);
      }

      return this.detail_info.table_data;
    },
  },
};
</script>

<style lang="scss" scoped>
#colors {
  color: red;
}

.el-form-item .el-input {
  width: 10rem;
}

.el-card {
  font-size: 15px;
  line-height: 21px;
}
</style>
