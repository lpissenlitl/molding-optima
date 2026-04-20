<template>
  <div>
    <h1 style="text-align: center">动态止逆阀测试试验表</h1>

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
        <p style="text-indent: 2em">确定注塑机止逆环在注射过程中的可靠性。</p>
        <span id="colors">测试原理</span>：
        <p style="text-indent: 2em">
          有时，由于螺杆头部部件损伤等原因，会出现起不到止逆环的作用。
          在注塑期间，由于压力极大，塑料会回流到螺杆头后面。
          这通常由两种泄露：一种是在填充阶段，螺杆快速向前运动过程中的塑料泄露，
          称其为止逆环的动态泄露；另一种是在保压阶段，螺杆运动非常缓慢，
          这段时间的泄露称其为止逆环的静态泄露。止逆环动态泄露的重复性也就是生产中每次的泄露情况是否一致。这关系到生产时，塑料制品品质的稳定性。
        </p>
        <span id="colors">测试标准</span>：
        <p style="text-indent: 2em">可接收的变化百分比在3%之内。</p>
        <span id="colors">测试设备</span>：
        <ol>
          <li>闭环系统控制的注射机</li>
          <li>短射时能够自动或半自动生产的模具</li>
          <li>精确到产品重量1%的天平</li>
        </ol>
        <span id="colors">测试方法</span>：
        <ol>
          <li>设置注塑机以标准的两阶段工艺运行。</li>
          <li>关掉保压压力和时间。</li>
          <li>连续注射10模，记录制品（和流道）的重量。</li>
          <li>计算差异。</li>
        </ol>
      </el-card>

      <div style="height: 12px" />

      <el-divider content-position="center">
        <span style="color: blue">测试数据记录表</span>
      </el-divider>

      <el-table
        :data="tableDataComputed"
        size="mini"
        height-current-row
        :cell-style="{ padding: '8px' }"
        style="width: 100%"
      >
        <el-table-column prop="title" label="模次" align="center" width="150">
        </el-table-column>

        <el-table-column
          v-for="i in 10"
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
            ></el-input>
          </template>
        </el-table-column>
      </el-table>

      <div style="height: 30px" />

      <el-form-item label="总计">
        <el-input v-model="detail_info.total_weight">
          <span slot="suffix">g</span>
        </el-input>
      </el-form-item>

      <el-form-item label="平均值">
        <el-input v-model="detail_info.avg_product_weight">
          <span slot="suffix">g</span>
        </el-input>
      </el-form-item>

      <el-form-item label="最重的">
        <el-input v-model="detail_info.max_product_weight">
          <span slot="suffix">g</span>
        </el-input>
      </el-form-item>

      <el-form-item label="最轻的">
        <el-input v-model="detail_info.min_product_weight">
          <span slot="suffix">g</span>
        </el-input>
      </el-form-item>

      <br />

      <el-form-item label="偏差">
        <el-input v-model="detail_info.product_weight_diff">
          <span slot="suffix">g</span>
        </el-input>
      </el-form-item>

      <el-form-item label="偏差率">
        <el-input v-model="detail_info.deviation_ratio">
          <span slot="suffix">%</span>
        </el-input>
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
  checkRingDynamicMethod,
  machineTrialsMethod,
  getOptions,
  projectMethod,
} from "@/api";
import { UserModule } from "@/store/modules/user";
import { initArray } from "@/utils/array-help";

export default {
  name: "CheckRingDynamic",
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

        table_data: [
          {
            title: "制品总重量（g）",
            sections: initArray(10, null),
          },
        ],

        total_weight: null,
        avg_product_weight: null,
        max_product_weight: null,
        min_product_weight: null,
        product_weight_diff: null,
        deviation_ratio: null,
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
        if (res.data.mold_info.product_infos.length > 0) {
          this.detail_info.product_name =
            res.data.mold_info.product_infos[0].product_name;
        }
        this.detail_info.cavity_num = res.data.mold_info.cavity_num;
      });
    },
    loadData() {
      if (this.id) {
        checkRingDynamicMethod
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
      this.loading = true
      this.$refs["detail_info"].validate((valid) => {
        if (valid) {
          if (!this.detail_info.machine_trial_id) {
            let machine_trial_index = {
              company_id: UserModule.company_id,
              machine_trial_type: "check_ring_dynamic",
              machine_data_source: this.detail_info.machine_data_source,
              asset_no: this.detail_info.asset_no,
              mold_no: this.detail_info.mold_no,
              polymer_abbreviation: this.detail_info.polymer_abbreviation,
              polymer_trademark: this.detail_info.polymer_trademark,
              product_name: this.detail_info.product_name,
              machine_trademark: this.detail_info.machine_trademark,
            };
            machineTrialsMethod
              .add(machine_trial_index)
              .then((res) => {
                if (res.status == 0) {
                  this.detail_info.machine_trial_id = res.data.id;

                  checkRingDynamicMethod.add(this.detail_info).then((res) => {
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
              machine_trial_type: "check_ring_dynamic",
              machine_data_source: this.detail_info.machine_data_source,
              asset_no: this.detail_info.asset_no,
              mold_no: this.detail_info.mold_no,
              polymer_abbreviation: this.detail_info.polymer_abbreviation,
              polymer_trademark: this.detail_info.polymer_trademark,
              product_name: this.detail_info.product_name,
              machine_trademark: this.detail_info.machine_trademark,
            };
            machineTrialsMethod
              .edit(machine_trial_index, this.detail_info.machine_trial_id)
              .then((res) => {
                if (res.status == 0) {
                  checkRingDynamicMethod
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

        table_data: [
          {
            title: "制品总重量（g）",
            sections: initArray(10, null),
          },
        ],

        total_weight: null,
        avg_product_weight: null,
        max_product_weight: null,
        min_product_weight: null,
        product_weight_diff: null,
        deviation_ratio: null,
      };
    },
    updateResult(total, ave, min, max) {
      this.detail_info.total_weight = total;
      this.detail_info.avg_product_weight = ave;
      this.detail_info.max_product_weight = max;
      this.detail_info.min_product_weight = min;

      if (max && min) {
        this.detail_info.product_weight_diff = Math.abs(max - min).toFixed(2);
      } else {
        this.detail_info.product_weight_diff = null;
      }

      if (ave && min && max) {
        this.detail_info.deviation_ratio = (((max - min) * 100) / ave).toFixed(
          2
        );
      } else {
        this.detail_info.deviation_ratio = null;
      }
    },
  },
  computed: {
    tableDataComputed() {
      let total_weight = 0;
      let ave_weight = 0;
      let count = 0;
      let min = 99999999;
      let max = 0;
      let product_weights = this.detail_info.table_data[0].sections;
      for (let i = 0; i < 10; ++i) {
        if (product_weights[i] == null) {
          continue;
        } else {
          ++count;
        }

        if (Number(max) <= Number(product_weights[i])) {
          max = product_weights[i];
        }

        if (Number(min) >= Number(product_weights[i])) {
          min = product_weights[i];
        }

        total_weight += Number(product_weights[i]);
      }

      if (count > 0) {
        ave_weight = (total_weight / count).toFixed(2);
        this.updateResult(total_weight, ave_weight, min, max);
      } else {
        this.updateResult(null, null, null, null);
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
#inputSize .el-input {
  width: 8rem !important;
}

.el-form-item .el-input {
  width: 10rem;
}

.el-card {
  font-size: 15px;
  line-height: 21px;
}
</style>
