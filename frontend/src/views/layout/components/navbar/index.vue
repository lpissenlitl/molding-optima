<template>
  <div class="navbar">
    <hamburger 
      id="hamburger-container"
      class="hamburger-container"
      :is-active="sidebar.opened" 
      :toggle-click="toggleSideBar" 
    />
    <breadcrumb 
      id="breadcrumb-container"
      class="breadcrumb-container"
    />
    <div class="right-menu">
      <el-dropdown
        class="avatar-container right-menu-item hover-effect"
        trigger="click"
      >
        <div class="avatar-wrapper">
          {{ organization_name }}
          <el-button type="text">
            {{ username }}
            <i class="el-dropdown-icon-user">
              <svg-icon 
                class="user"
                name="user"
              /></i>
          </el-button>
        </div>
        <el-dropdown-menu slot="dropdown">
          <el-dropdown-item>
            <span 
              style="display:block;" 
              @click="showUserSet=true"
            >
              修改密码
            </span>
          </el-dropdown-item>
          <el-dropdown-item divided>
            <span 
              style="display:block;" 
              @click="logout"
            >
              退出登录
            </span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
    <user-set :show-user-set.sync="showUserSet"></user-set>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from "vue-property-decorator"
import { AppModule } from "@/store/modules/app"
import { UserModule } from "@/store/modules/user"
import Hamburger from "@/components/hamburger/index.vue"
import Breadcrumb from "@/components/breadcrumb/index.vue"
import UserSet from "@/components/userSet/index.vue"

@Component({
  components: {
    Hamburger,
    Breadcrumb,
    UserSet,
  },
})

export default class Navbar extends Vue {
  private showUserSet: boolean = false

  get sidebar() {
    return AppModule.sidebar
  }

  get device() {
    return AppModule.device.toString()
  }

  get username() {
    return UserModule.username
  }

  get organization_name() {
    return UserModule.organization_name
  }

  private toggleSideBar() {
    AppModule.ToggleSideBar(false)
  }

  private logout() {
    UserModule.LogOut().then(() => {
      this.$router.push({ path: "/login" })
      // location.reload();  // 为了重新实例化vue-router对象 避免bug
    })
  }
}
</script>

<style lang="scss" scoped>
.navbar {
  height: 40px;
  overflow: hidden;
  position: relative;
  background: #fff;
  right: 0;
  box-shadow: 0 1px 4px rgb(37,67,115);

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    float: left;
    padding: 0 15px;
    cursor: pointer;
    transition: background .3s;
    -webkit-tap-highlight-color: transparent;

    &:hover {
      background: rgba(0, 0, 0, .025)
    }
  }

  .breadcrumb-container {
    line-height: 40px;
    float: left;
  }

  .errLog-container {
    display: inline-block;
    vertical-align: top;
  }

  .right-menu {
    float: right;
    height: 100%;
    line-height: 30px;

    &:focus {
      outline: none;
    }

    .right-menu-item {
      display: inline-block;
      padding: 5px 8px;
      height: 100%;
      font-size: var(--basic-font-size);
      color: #5a5e66;
      vertical-align: top;

      &.hover-effect {
        cursor: pointer;
        transition: background .3s;

        &:hover {
          background: rgba(0, 0, 0, .025)
        }
      }
    }

    .avatar-container {
      margin-right: 25px;

      .avatar-wrapper {
        margin: -5px 5px;
        position: relative;

        // .user-avatar {
        //   cursor: pointer;
        //   width: 40px;
        //   height: 40px;
        //   border-radius: 10px;
        // }

        .el-dropdown-icon-user {
          cursor: pointer;
          position: absolute;
          right: -20px;
          top: 15px;
          font-size: 12px;
        }
      }
    }
  }
}
</style>

