<template>
  <div class="login-container">
    <el-form 
      ref="loginForm" 
      :model="login_form" 
      :rules="login_rules" 
      class="login-form"
      auto-complete="on" 
      label-position="left"
    >
      <div class="form-header">
        <h3 class="title">
          试模专家系统
        </h3>
        <!-- 原始文字: Molding Expert -->
        <p class="subtitle">
          <span class="letter" style="--i:0">M</span><span class="letter" style="--i:1">o</span><span class="letter" style="--i:2">l</span><span class="letter" style="--i:3">d</span><span class="letter" style="--i:4">i</span><span class="letter" style="--i:5">n</span><span class="letter" style="--i:6">g</span>
          <span class="space"></span>
          <span class="letter" style="--i:8">E</span><span class="letter" style="--i:9">x</span><span class="letter" style="--i:10">p</span><span class="letter" style="--i:11">e</span><span class="letter" style="--i:12">r</span><span class="letter" style="--i:13">t</span>
        </p>
      </div>
      
      <el-form-item prop="username">
        <span class="svg-container">
          <svg-icon name="user" />
        </span>
        <el-input 
          v-model="login_form.username" 
          name="username" 
          type="text" 
          auto-complete="on" 
          placeholder="用户名"
          style="width: 85%;"
        />
      </el-form-item>

      <el-form-item prop="password">
        <span class="svg-container">
          <svg-icon name="password" />
        </span>
        <el-input
          :type="pwd_type"
          v-model="login_form.password"
          name="password"
          auto-complete="on"
          placeholder="密码"
          style="width: 85%;"
          @keyup.enter.native="handleLogin"
        />
        <span class="show-pwd" @click="togglePwd">
          <svg-icon :name="pwd_type === 'password' ? 'eye-off' : 'eye-on'" />
        </span>
      </el-form-item>

      <el-form-item>
        <el-button 
          :loading="loading" 
          type="primary" 
          style="width:100%;" 
          @click.native.prevent="handleLogin"
        >
          登 录
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script lang="ts">
import { isValidUsername } from "@/utils/validate"
import { Component, Vue, Watch } from "vue-property-decorator"
import { UserModule } from "@/store/modules/user"
import { Route } from "vue-router"
import { ElForm } from "element-ui/types/form"
import { login } from "@/api"
import { isNative } from "@/utils/auth"

const validateUsername = (rule: any, value: string, callback: any) => {
  if (!isValidUsername(value)) {
    callback(new Error("请输入正确的用户名"))
  } else {
    callback()
  }
}

const validatePass = (rule: any, value: string, callback: any) => {
  if (value.length < 5) {
    callback(new Error("密码不能小于5位"))
  } else {
    callback()
  }
}

@Component
export default class Login extends Vue {
  // Data: 使用 snake_case（与后端字段一致）
  private login_form = {
    username: "",
    password: "",
  }
  
  private login_rules = {
    username: [{ required: true, trigger: "blur", validator: validateUsername }],
    password: [{ required: true, trigger: "blur", validator: validatePass }],
  }
  
  private loading = false
  private pwd_type = "password"
  private redirect: string | undefined = undefined

  @Watch("$route", { immediate: true })
  private onRouteChange(route: Route) {
    this.redirect = route.query && route.query.redirect as string
  }

  // Methods: 使用 camelCase
  private togglePwd() {
    if (this.pwd_type === "password") {
      this.pwd_type = ""
    } else {
      this.pwd_type = "password"
    }
  }

  private handleLogin() {
    (this.$refs.loginForm as ElForm).validate((valid: boolean) => {
      if (valid) {
        const ua = navigator.userAgent.toLowerCase()
        this.loading = true
        login({
          username: this.login_form.username.trim(),
          password: this.login_form.password.trim(),
          ua,
        }).then((res) => {
          if (res.status === 0) {
            UserModule.setLoginData(res.data)
            if (isNative) {
              this.$router.push({ path: "/" })
            } else {
              this.$router.push({ path: this.redirect || "/" })
            }
          }
        }).finally(() => {
          this.loading = false
        })
      } else {
        return false
      }
    })
  }
}
</script>

<style lang="scss">
@import "src/styles/variables.scss";

.login-container {
  .el-input {
    input {
      background: transparent;
      border: 0px;
      -webkit-appearance: none;
      color: $lightGray;

      &:-webkit-autofill {
        box-shadow: 0 0 0px 1000px $loginBg inset !important;
        -webkit-box-shadow: 0 0 0px 1000px $loginBg inset !important;
        -webkit-text-fill-color: #fff !important;
      }
    }
  }
}
</style>

<style lang="scss" scoped>
@import "src/styles/variables.scss";

.login-container {
  position: fixed;
  height: 100%;
  width: 100%;
  background-color: $loginBg;

  .login-form {
    position: absolute;
    left: 0;
    right: 0;
    width: 520px;
    max-width: 100%;
    padding: 35px 35px 15px 35px;
    margin: 120px auto;
  }

  .form-header {
    text-align: center;
    margin-bottom: 40px;

    .title {
      font-size: 38px;
      font-weight: 600;
      color: $lightGray;
      margin: 0 0 12px 0;
      letter-spacing: 4px;
    }

    .subtitle {
      font-size: 14px;
      color: $darkGray;
      margin: 0;
      letter-spacing: 3px;
      text-transform: uppercase;
      height: 20px;

      .letter {
        display: inline-block;
        color: #FFFFFF;
        animation: letterBounce 1.2s ease-in-out infinite;
        animation-delay: calc(var(--i) * 0.06s);
      }

      .space {
        display: inline-block;
        width: 0.5em;
      }
    }
  }
}

@keyframes letterBounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-3px);
  }
}

.login-container {
  .el-input {
    display: inline-block;
    width: 85%;
  }

  .el-form-item {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.1);
    border-radius: 5px;
    color: #454545;
  }

  .svg-container {
    padding: 6px 5px 6px 10px;
    color: $darkGray;
    vertical-align: middle;
    width: 30px;
    display: inline-block;
  }

  .show-pwd {
    position: absolute;
    right: 10px;
    top: 7px;
    font-size: 16px;
    color: $darkGray;
    cursor: pointer;
    user-select: none;
  }
}
</style>