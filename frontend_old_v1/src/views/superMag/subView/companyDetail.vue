<template>
  <div class="saveUpdate">
    <el-dialog 
      v-el-drag-dialog
      :title="id?'编辑企业':'新增企业'" 
      :visible.sync="showDialog" 
      :show-update="showUpdate"
      :close-on-click-modal="false"
      @close="resetView" 
    >
      <el-form 
        ref="form_info" 
        :model="detail_info" 
        :inline="true"
        :rules="rules" 
        size="mini"
        label-width="8rem"
      >
        <el-row>
          <el-form-item 
            label="企业名称" 
            prop="name"
          >
            <el-input 
              v-model="detail_info.name"
            ></el-input>
            <el-button 
              type="success" 
              v-if="this.id" 
              @click="updateCompanyInfo"
            >
              更新企业信息
            </el-button>
          </el-form-item>
        </el-row>

        <el-row>
          <el-form-item 
            label="企业描述" 
            prop="description"
          >
            <el-input 
              v-model="detail_info.description"
              type="textarea" 
              autosize 
              style="width: 25rem"
            ></el-input>
          </el-form-item>
        </el-row>

        <el-row>
          <el-form-item 
            label="管理员用户名" 
            prop="admin"
          >
            <el-input 
              v-model.trim="detail_info.admin" 
              oninput="value=value.replace(/[^A-Z0-9a-z_]/g, '')"
              placeholder="请输入用户名"
            ></el-input>
          </el-form-item>
        </el-row>

        <el-row>
          <el-form-item 
            label="管理员密码" 
            prop="password"
          >
            <el-input 
              :type="pwdType" 
              v-model="detail_info.password"
              oninput="value=value.replace(/[^A-Z0-9a-z!@#$%.]/g, '')"
              placeholder="请输入密码"
              auto-complete="new-password"
            >
              <i slot="suffix" :class="icon" @click="showPwd"></i>
            </el-input>
          </el-form-item>
        </el-row>

        <el-row>
          <el-form-item 
            label="再次输入密码" 
            prop="check_pwd" 
          >
            <el-input 
              :type="pwdType" 
              v-model="detail_info.check_pwd"
              oninput="value=value.replace(/[^A-Z0-9a-z!@#$%.]/g, '')"
              placeholder="请再次输入密码"
              auto-complete="new-password"
            >
              <i slot="suffix" :class="icon" @click="showPwd"></i>
            </el-input>
          </el-form-item>
        </el-row>
      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button 
          type="danger"
          @click="resetView" 
          size="small"
          style="width:6rem"
        >
          返  回
        </el-button>
        <el-button 
          v-if="id" 
          type="primary" 
          :loading="loading" 
          style="width:6rem"
          size="small"
          @click="updateDetail"
        >
          更  新
        </el-button>
        <el-button 
          v-else 
          type="primary" 
          :loading="loading" 
          style="width:6rem"
          @click="saveDetail" 
          size="small"
        >
          保  存
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
  import { companiesMethod , usersMethod, managersMethod} from "@/api"
  export default {
    props: {
      showUpdate: {
        type: Boolean,
        default: false
      },
      id: {
        type: Number,
        default: null
      }
    },
    data() {
      var validatePassword = (rule, value, callback) => {
        if (this.detail_info.check_pwd === '') {
          callback(new Error('请再次输入密码'));
        } else if (this.detail_info.check_pwd !== this.detail_info.password) {
          callback(new Error('两次输入密码不一致!'));
        } else {
          callback();
        }
      };
      return {
        detail_info: {
          name: null,
          description: null,
          level: 1,
          admin: null,
          password: null,
          check_pwd: null,
          admin_id: null,
          admin_roles: [],
          admin_groups: []
        },
        icon: "el-input__icon el-icon-view",
        pwdType: "text",
        UserInfo:{},
        rules: {
          name: [
            { required: true, message: '请输入企业名称', trigger: 'blur' },
          ],
          admin: [
            { required: true, message: '请输入用户名', trigger: 'blur' },
          ],
          password: [
            { required: true, message: '请输入密码', trigger: 'blur' },
            { min: 6, message: '密码不得小于6位', trigger: 'blur' },
          ],
          check_pwd: [
            { required: true, message: '请再次输入密码', trigger: 'blur' },
            { min: 6, message: '密码不得小于6位', trigger: 'blur' },
            { validator: validatePassword, trigger: 'blur' },
          ],
        },
        loading: false,
        showDialog: this.showUpdate,
      }
    },
    created() {
      if(this.id) {
        this.getDetail()
      }
    },
    methods: {
      showPwd() {
        if (this.pwdType === 'password') {
          this.pwdType = "text";
          this.icon = "el-input__icon el-icon-loading";
        } else {
          this.pwdType = "password";
          this.icon = "el-input__icon el-icon-view";
        }
      },
      getDetail() {
        companiesMethod.getDetail(this.id)
        .then(res => {
          if(res.status === 0) {
            // 企业信息
            this.detail_info.name = res.data.name
            this.detail_info.description = res.data.description
            this.detail_info.level = res.data.level
            this.detail_info.admin_id = res.data.admin_id
            if (res.data.admin_id) {
              usersMethod.getDetail(res.data.admin_id)
              .then(res => {
                if (res.status === 0) {
                  this.detail_info.admin = res.data.name
                  this.detail_info.password = null
                  this.detail_info.check_pwd = null
                  this.detail_info.admin_roles = res.data.role_ids
                  this.detail_info.admin_groups = res.data.group_ids
                }
              })
            }
          }
        })
      },
      saveDetail() {
        this.$refs.form_info.validate(valid => {
          if(valid) {
            let company_info = {
              name: this.detail_info.name,
              description: this.detail_info.description,
              level: this.detail_info.level,
              admin_user: this.detail_info.admin,
              admin_passwd: this.detail_info.password,
            }
            companiesMethod.add(company_info)
            .then(res => {
              if(res.status === 0) {
                this.$message({ message: '新增企业成功。', type: 'success' })
              }
            })
            .finally(() => {
              this.resetView()
            })
          }
        })
      },
      updateCompanyInfo() {
        if (this.detail_info.name) {
          let company_info = {
            name: this.detail_info.name,
            description: this.detail_info.description,
          }
          companiesMethod.edit(company_info, this.id)
          .then(res => {
            if (res.status === 0) {
              this.$message({ message: '更新企业信息成功!', type: 'success' })
            }
          })

        } else {
          this.$message({ message: '企业名称不能为空!', type: 'error' })
        }
      },
      updateDetail() {
        this.$refs.form_info
        .validate(valid => {
          if(valid) {
            let company_info = {
              name: this.detail_info.name,
              description: this.detail_info.description
            }
            companiesMethod.edit(company_info, this.id)
            .then(res => {
              if(res.status === 0) {
                if (this.detail_info.admin_id) {
                  usersMethod.edit({
                    enable: 1,
                    is_super: 0,
                    name: this.detail_info.admin,
                    engineer: this.detail_info.name,
                    password: this.detail_info.password,
                    role_ids: this.detail_info.admin_roles,
                    group_ids: this.detail_info.admin_groups
                  }, this.detail_info.admin_id)
                  .then(res => {
                    if (res.status === 0) {
                    }
                  })
                } else {
                  // 增加第一个企业管理员用户。
                  let user_info = {
                    enable: 1,
                    is_super: 0,
                    name: this.detail_info.admin,
                    engineer: this.detail_info.name,
                    password: this.detail_info.password,
                    company_id: this.id
                  }
                  usersMethod.add(user_info)
                  .then(res => {
                    if (res.status === 0) {
                      companiesMethod.edit({
                        admin_id: res.data.id
                      }, res.data.company_id)
                      .then(res => {
                      })

                      this.$message({ message: '新增企业管理员成功。', type: 'success' })
                    }
                  })
                }

                this.$message({ message: '编辑成功。', type: 'success' })
              }
            }).finally( () => {
              this.resetView()
            })
          }
        })
      },
      resetView() {
        this.$emit('close-dialog')
        this.detail_info = {
          name: null,
          description: null,
          level: 1,
          admin: null,
          password: null,
          check_pwd: null,
          admin_id: null,
        }
      }
    },
    watch: {
      showUpdate() {
        this.showDialog = this.showUpdate
        if (this.id) {
          this.getDetail()
        }
      },
      "detail_info.password" () {
        if (this.detail_info.password) {
          this.pwdType = "password"
        } else {
          this.pwdType = "text"
        }
      }
    }
  }
</script>

<style lang="scss" scoped>
  .el-input {
    width: 12rem;
  }
</style>
