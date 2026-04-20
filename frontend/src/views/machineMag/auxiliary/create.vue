<template>
  <div class="createAuxiliary">
    <div class="AuxiliaryInfo">
      <el-card>
        <div slot="header" class="clearfix">
          辅机描述
        </div>

        <el-form 
          ref="form_info" 
          size="mini" 
          label-width="10rem" 
          label-position="right" 
          :model="auxiliary_info" 
          :rules="rules"
          :inline="true"
        >
          <el-form-item 
            label="辅机类型" 
            prop="auxiliary_type"
          >
            <el-select 
              v-model="auxiliary_info.auxiliary_type" 
              placeholder="请选择" 
              filterable allow-create 
              default-first-option 
              clearable
            >
              <el-option 
                v-for="item in auxiliary_type_options" 
                :key="item.value" 
                :label="item.label" 
                :value="item.label"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="辅机编号" 
            prop="serial_num"
          >
            <el-input v-model="auxiliary_info.serial_num"></el-input>
          </el-form-item>

          <el-form-item 
            label="通讯接口" 
            prop="communication_interface"
          >
            <el-select v-model="auxiliary_info.communication_interface">
              <el-option label="开通" :value="1"></el-option>
              <el-option label="未开通" :value="0"></el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="辅机品牌" 
            prop="manufacture"
          >
            <el-select 
              v-model="auxiliary_info.manufacture" 
              placeholder="请选择" 
              filterable 
              allow-create 
              default-first-option 
              clearable
            >
              <el-option 
                v-for="item in auxiliary_manu_options" 
                :key="item.value" 
                :label="item.label" 
                :value="item.label"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="辅机型号" 
            prop="auxiliary_trademark"
          >
            <el-input v-model="auxiliary_info.auxiliary_trademark"></el-input>
          </el-form-item>
        </el-form>
      </el-card>

      <div style="height: 4px" />

      <el-card>
        <div slot="header" class="clearfix">
          连接注塑机
        </div>

        <el-form 
          size="mini" 
          label-width="10rem" 
          label-position="right" 
          :model="auxiliary_info" 
          :rules="rules" 
          :inline="true"
        >
          <el-form-item 
            label="注塑机来源" 
            prop="data_source"
          >
            <el-autocomplete
              v-model="auxiliary_info.machine_data_source"
              placeholder="注塑机来源"
              clearable
              style="width:10rem"
              :fetch-suggestions="queryDataSourceList"
              @select="handleDataSourceSelect"
            >
            </el-autocomplete>
          </el-form-item>

          <el-form-item 
            label="注塑机型号" 
            prop="trademark"
          >
            <el-autocomplete
              v-model="auxiliary_info.machine_trademark"
              placeholder="注塑机型号"
              clearable
              style="width:10rem"
              :fetch-suggestions="queryTrademarkList"
              @select="handleTrademarkSelect"
            >
            </el-autocomplete>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div class="nextButton">
      <el-button 
        v-if="dialog"
        type="danger" 
        size="small" 
        @click="$emit('close')" 
      >
        取  消
      </el-button>
      <el-button 
        v-else
        type="danger"
        size="small"
        @click="resetView" 
      >
        重  置
      </el-button>
      <el-button
        v-if="id" 
        type="primary" 
        size="small" 
        :loading="update_loading" 
        @click="saveAuxiliaryDetail"
        :disabled="!$store.state.user.userinfo.permissions.includes('update_machine')"
      >
        更  新
      </el-button>
      <el-button
        v-else
        type="primary" 
        size="small" 
        :loading="save_loading" 
        @click="saveAuxiliaryDetail"
        :disabled="!$store.state.user.userinfo.permissions.includes('add_machine')"
      >
        保  存
      </el-button>
    </div>
  </div>
</template>

<script>
import { auxiliaryTypeOptions, auxiliaryManuOptions } from '@/utils/machine-const';
import { auxiliaryMethod, getOptions } from '@/api';
import { UserModule } from '@/store/modules/user';

export default {
  props: {
    id: {
      type: Number,
      default: null,
    },
    dialog: {
      type: Boolean,
      default: false
    },
    viewType: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      auxiliary_info: {
        company_id: UserModule.company_id,
        id: null,

        auxiliary_type: "",
        serial_num: null,
        communication_interface: 0,
        manufacture: "",
        auxiliary_trademark: "",

        machine_id: null,
        machine_data_source: "",
        machine_trademark: ""
      },
      rules: {
        serial_num: [
          { required: true, message: '辅机编号不能为空！' }
        ]
      },
      export_loading: false,
      update_loading: false,
      save_loading: false,
      auxiliary_type_options: auxiliaryTypeOptions,
      auxiliary_manu_options: auxiliaryManuOptions,
      machine_datasource_options: [],
      machine_trademark_options: [],
    }
  },
  mounted() {
    getOptions("machine_data_source", {})
    .then(res => {
      if (res.status === 0) {
        this.machine_datasource_options.length = 0
        for (let i = 0; i < res.data.length; ++i) {
          this.machine_datasource_options.push({ "value": res.data[i].value })
        }
      }
    })

    this.getAuxiliaryDetail()
  },
  methods: {
    getTrademarkList(params) {
      getOptions("machine_trademark", {"data_source": this.auxiliary_info.machine_data_source})
      .then(res => {
        if (res.status === 0 && Array.isArray(res.data)) {
          this.machine_trademark_options.length = 0
          for (let i = 0; i < res.data.length; ++i) {
            this.machine_trademark_options.push({ "id": res.data[i].id, "value": res.data[i].trademark })
          }
        }
      })
    },
    queryDataSourceList(queryString, cb) {
      var machine_datasource_options = this.machine_datasource_options;
      var results = queryString ? machine_datasource_options.filter(this.createStateFilter(queryString)) : machine_datasource_options;
      cb(results);
    },
    queryTrademarkList(queryString, cb) {
      var machine_trademark_options = this.machine_trademark_options;
      var results = queryString ? machine_trademark_options.filter(this.createStateFilter(queryString)) : machine_trademark_options;
      cb(results);
    },
    createStateFilter(queryString) {
      return (state) => {
        return (state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
      };
    },
    handleDataSourceSelect(item) {
      this.auxiliary_info.machine_data_source = item.value
      this.getTrademarkList({ "data_source": this.auxiliary_info.machine_data_source })
    },
    handleTrademarkSelect(item) {
      this.auxiliary_info.machine_id = item.id
      this.auxiliary_info.machine_trademark = item.value
    },
    getAuxiliaryDetail() {
      if (this.id) {
        auxiliaryMethod.getDetail(this.id)
        .then(res => {
          if (res.status === 0) {
            this.auxiliary_info = res.data

            if (this.viewType == "edit") {

            } else if (this.viewType == "copy") {
              this.auxiliary_info.id = null
              this.auxiliary_info.serial_num = ""
            }
          }
        })
      }
    },
    saveAuxiliaryDetail() {
      this.$refs.form_info.validate((valid) => {
        if (valid) {
          if (this.id) {
            auxiliaryMethod.edit(this.auxiliary_info, this.id)
            .then(res => {
              if (res.status === 0) {
                this.$message({ message: '编辑成功！', type: 'success' })
              }
            })
          } else {
            auxiliaryMethod.add(this.auxiliary_info)
            .then(res => {
              if (res.status === 0) {
                this.$message({ message: '新增成功！', type: 'success' })
              }
            })
          }

          this.$emit('close')
          this.$router.push('/machine/auxiliary/list')
        }
      })
    },
    resetView() {
      this.auxiliary_info = {
        company_id: UserModule.company_id,
        id: null,

        auxiliary_type: "",
        serial_num: null,
        communication_interface: 0,
        manufacture: "",
        auxiliary_trademark: "",

        machine_id: null,
        machine_data_source: "",
        machine_trademark: ""
      }
    }
  },
  watch: {
    id() {
      if (this.id) {
        this.getAuxiliaryDetail()
      }
    },
  }

}
</script>

<style lang="scss" scoped>

.el-input {
  width: 10rem;
}
.el-select {
  width: 10rem;
}
</style>