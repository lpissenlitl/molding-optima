<template>
  <div class="departmentCreate">
    <el-dialog 
      v-el-drag-dialog
      :title="id?'编辑部门':'新增部门'" 
      :visible.sync="showDialog"
      :show-update="showUpdate" 
      :close-on-click-modal="false"
      @close="resetView" 
    >
      <el-form 
        ref="form_info" 
        :model="detail_info" 
        :rules="rules" 
        size="mini" 
        label-width="8rem" 
      >
        <el-form-item label="组织名称" prop="company_id">
          <el-select v-model="detail_info.company_id">
            <el-option 
              v-for="company in company_options"
              :key="company.value"
              :label="company.label"
              :value="company.value"
            ></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="detail_info.name"></el-input>
        </el-form-item>
        <el-form-item label="部门缩写" prop="abbreviation">
          <el-input v-model="detail_info.abbreviation"></el-input>
        </el-form-item>
        <el-form-item label="部门编号" prop="serial_number">
          <el-input v-model="detail_info.serial_number"></el-input>
        </el-form-item>
        <el-form-item label="负责人" prop="header">
          <el-input v-model="detail_info.header"></el-input>
        </el-form-item>
        <el-form-item label="部门描述" prop="description">
          <el-input type="textarea" v-model="detail_info.description" rows="4" style="width: 400px"></el-input>
        </el-form-item>
        <el-form-item label="部门属性" prop="attribute">
          <el-input type="textarea" v-model="detail_info.attribute" rows="2" style="width: 400px"></el-input>
        </el-form-item>
        <el-form-item label="激活">
          <el-tooltip content="如果不激活,则将禁用该部门下任何人员使用权限">
            <el-switch v-model="detail_info.deleted"></el-switch>
          </el-tooltip>
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="resetView" size="small">取 消</el-button>
        <el-button v-if="id" type="primary" :loading="loading" @click="updateDetail" size="small">更 新</el-button>
        <el-button v-else type="primary" :loading="loading" @click="saveDetail" size="small">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { departmentsMethod, getOptions } from "@/api";

export default {
  props: {
    showUpdate: {
      type:Boolean,
      default: false
    },
    id: {
      type: Number,
      default:null,
    }
  },
  data() {
    return {
      detail_info: {
        company_id: null,
        name: null,
        abbreviation: null,
        serial_number: null,
        header: null,
        description: null,
        attribute: null,
        deleted: null,
      },
      rules: {
        company_id: [
          { required: true, message: '请选择组织名称', trigger: 'blur' },
        ],
        name: [
          { required: true, message: '部门名称不能为空', trigger: 'blur' }
        ]
      },
      company_options: [],
      loading: false,
      showDialog: this.showUpdate,
    }
  },
  created() {
    this.initView()
  },
  mounted() {
    if(this.id) {
      this.getDetail()
    }
  },
  methods: {
    initView() {
      getOptions("company_option")
      .then(res => {
        if (res.status === 0) {
          this.company_options = res.data
        }
      })
    },
    getDetail() {
      departmentsMethod.getDetail(this.id)
      .then(res => {
        if(res.status === 0) {
          this.detail_info = res.data
          this.detail_info.deleted = !res.data.deleted
        }
      })
    },
    saveDetail() {
      this.$refs.form_info.validate(valid => {
        if (valid) {
          let department_info = {
            company_id: this.detail_info.company_id,
            name: this.detail_info.name,
            abbreviation: this.detail_info.abbreviation,
            serial_number: this.detail_info.serial_number,
            header: this.detail_info.header,
            description: this.detail_info.description,
            attribute: this.detail_info.attribute,
            deleted: this.detail_info.deleted? 0:1
          }
          departmentsMethod.add(department_info)
          .then(res => {
            if (res.status === 0) {
              this.$message({message:'新增部门成功！' ,type:'success'})
            }
          }).finally( () => {
            this.resetView()
          })
        }
      })
    },
    updateDetail() {
      this.$refs.form_info.validate(valid => {
        if(valid) {
          let department_info = {
            company_id: this.detail_info.company_id,
            name: this.detail_info.name,
            abbreviation: this.detail_info.abbreviation,
            serial_number: this.detail_info.serial_number,
            header: this.detail_info.header,
            description: this.detail_info.description,
            attribute: this.detail_info.attribute,
            deleted:this.detail_info.deleted? 0:1
          }
          departmentsMethod.edit(department_info, this.id)
          .then(res => {
            if (res.status === 0) {
              this.$message({message: '编辑成功。', type: 'success'})
            }
          }).finally( () => {
            this.resetView()
          })
        }
      })
    },
    resetView() {
      this.detail_info = {
        company_id: null,
        name: null,
        abbreviation: null,
        serial_number: null,
        header: null,
        description: null,
        attribute: null,
        deleted: null,
      }
      this.$emit('close-dialog')
    }
  },
  watch: {
    showUpdate: function () {
      this.showDialog = this.showUpdate
      if(this.id) {
        this.getDetail()
      }
    }
  }
}
</script>

<style scoped>

</style>
