<template>
  <div class="UserSet">
    <el-dialog title="修改个人密码" :visible.sync="showDialog" @close="$emit('update:showUserSet', false)" :append-to-body="true">
      <el-form :model="userInfo" ref="saveChn" class="small-space" label-position="right" label-width="120px">
        <dialog-wrapper>
          <el-form-item prop="old_password" :rules="[{ required: true, message: '旧密码不能为空'}]" label="旧密码:">
            <el-input type="password" v-model="userInfo.old_password" auto-complete="on" placeholder="请输入旧密码"></el-input>
          </el-form-item>
          <el-form-item prop="new_password" :rules="[{ required: true, message: '新密码不能为空'}]" label="新密码:">
            <el-input type="password" v-model="userInfo.new_password" auto-complete="on" placeholder="请输入新密码"></el-input>
          </el-form-item>
          <el-form-item prop="repassword" :rules="[{ required: true, message: '确认新密码不能为空'}]" label="确认新密码:">
            <el-input type="password" v-model="userInfo.repassword" auto-complete="on" placeholder="请再次输入新密码"></el-input>
          </el-form-item>
        </dialog-wrapper>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" :loading="loading" @click="saveUserSet">确 定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import DialogWrapper from '@/components/dialogWrapper'
import { resetMyPassword } from '@/api/login'

export default {
  name: 'UserSet',
  components: { DialogWrapper },
  data() {
    return {
      showDialog: this.showUserSet,
      loading: false,

      close: false,
      reclose: false,
      userInfo: {}
    }
  },
  props: {
    showUserSet: {
      type: Boolean,
      default: false
    }
  },
  methods: {
    saveUserSet() {

      this.$refs.saveChn.validate(valid => {
        if (valid) {
          if (this.userInfo.new_password) {
            if (this.userInfo.new_password.length < 6) {
              this.$message({
                message: '新密码长度必须大于等于6！',
                type: 'warning'
              })
              return
            }
          }
          if (this.userInfo.new_password !== this.userInfo.repassword) {
            this.$message({
              message: '两次密码输入不一致！',
              type: 'warning'
            })
            return
          }
          resetMyPassword(this.userInfo).then(res => {
            if (res.status === 0) {
              this.$emit('update:showUserSet', false)
              this.$store.dispatch('FedLogOut').then(() => {
                this.$router.push({ path: '/login' })
              })
            }
          })
        }
      })
    }
  },
  watch: {
    showUserSet() {
      this.showDialog = this.showUserSet
    }
  }
}
</script>

<style lang="scss" scoped>
  .show-pwd {
    position: absolute;
    right: 10px;
    top: 3px;
    font-size: 20px;
    color: gray;
    cursor: pointer;
    user-select: none;
  }
</style>
