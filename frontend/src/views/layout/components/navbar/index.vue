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
      <!-- <template v-if="device!=='mobile'"> -->
      <!-- <header-search class="right-menu-item" />
        <error-log class="errLog-container right-menu-item hover-effect" />
        <screenfull class="right-menu-item hover-effect" />
        <el-tooltip
          :content="$t('navbar.size')"
          effect="dark"
          placement="bottom"
        >
          <size-select class="right-menu-item hover-effect" />
        </el-tooltip>
        <lang-select class="right-menu-item hover-effect" /> -->
      <!-- <help-doc class="right-menu-item hover-effect" /> -->
      <!-- </template> -->
      <el-dropdown
        class="avatar-container right-menu-item hover-effect"
        trigger="click"
      >
        <div class="avatar-wrapper">
          {{ group }}
          <el-button type="text">
            {{ name }}
            <i class="el-dropdown-icon-user">
              <svg-icon 
                class="user"
                name="user"
              /></i>
          </el-button>
        </div>
        <el-dropdown-menu slot="dropdown">
          <!-- <router-link class="inlineBlock" to="/">
            <el-dropdown-item>
              系统首页
            </el-dropdown-item>
          </router-link>
          <el-dropdown-item>
            个人中心
          </el-dropdown-item> -->
          <el-dropdown-item>
            <span style="display:block;" @click="showUserSet=true">修改密码</span>
          </el-dropdown-item>
          <el-dropdown-item divided>
            <span style="display:block;" @click="logout">退出登录</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
    <user-set :show-user-set.sync="showUserSet"></user-set>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { AppModule } from '@/store/modules/app';
import { UserModule } from '@/store/modules/user';
import Hamburger from '@/components/hamburger/index.vue';
import Breadcrumb from '@/components/breadcrumb/index.vue';
import HelpDoc from '@/components/helpDoc/index.vue';
import UserSet from '@/components/userSet/index.vue';

@Component({
  components: {
    Hamburger,
    Breadcrumb,
    HelpDoc,
    UserSet,
  },
})

export default class Navbar extends Vue {
  private showUserSet: boolean = false;

  get sidebar() {
    return AppModule.sidebar;
  }

  get device() {
    return AppModule.device.toString()
  }

  get name() {
    return UserModule.name;
  }

  get group() {
    return UserModule.group;
  }

  private toggleSideBar() {
    AppModule.ToggleSideBar(false);
  }

  private logout() {
    UserModule.LogOut().then(() => {
      this.$router.push({path: '/login'});
      // location.reload();  // 为了重新实例化vue-router对象 避免bug
    });
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
  box-shadow: 0 1px 4px rgba(0,21,41,.08);

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    float: left;
    padding: 0 15px;
    cursor: pointer;
    transition: background .3s;
    -webkit-tap-highlight-color:transparent;

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
      font-size: 16px;
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

