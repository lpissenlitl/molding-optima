import Vue from "vue"
import Router from "vue-router"

/* Layout */
import Layout from "@/views/layout/layout.vue"

Vue.use(Router)

/*
  redirect:                      if `redirect: noredirect`, it won't redirect if click on the breadcrumb
  meta: {
    title: 'title'               the name showed in subMenu and breadcrumb (recommend set)
    icon: 'svg-name'             the icon showed in the sidebar
    breadcrumb: false            if false, the item will be hidden in breadcrumb (default is true)
    hidden: true                 if true, this route will not show in the sidebar (default is false)
  }
*/
// 解决重复路由点击报错
const originalPush = Router.prototype.push
Router.prototype.push = function push(location:any){
  return (originalPush.call(this, location) as any).catch((err:any)=>{err})
}

export default new Router({
  mode: "history",  // Disabled due to Github Pages doesn't support this, enable this if you need.
  scrollBehavior: (to, from, savedPosition) => {
    if (savedPosition) {
      return savedPosition
    } else {
      return { x: 0, y: 0 }
    }
  },
  base: process.env.BASE_URL,
  routes: [
    {
      path: "/login",
      component: () => import(/* webpackChunkName: "login" */ "@/views/login/index.vue"),
      meta: { hidden: true }
    },
    {
      path: "/404",
      component: () => import(/* webpackChunkName: "404" */ "@/views/404.vue") ,
      meta: { hidden: true }
    },
    {
      path: "/",
      component: Layout,
      redirect: "/mold/list",
    },
    {
      path: "/mold",
      component: Layout,
      redirect: "/mold/list",
      name: "mold_manage",
      meta: { title: "模具管理", icon: "project", perm: "mold_manage" },
      children: [
        {
          path: "list",
          name:"mold_list",
          component: () => import("@/views/moldMag/list.vue"),
          meta: { title: "模具列表", icon: "list", perm: "mold_list" }
        },
        {
          path: "data",
          name:"mold_data",
          component: () => import("@/views/moldMag/moldData.vue"),
          meta: { title: "模流数据", icon: "form", perm: "mold_list", hidden: true }
        },
        {
          path: "create",
          name:"mold_create",
          component: () => import("@/views/moldMag/create.vue"),
          meta: { title: "新增模具", icon: "form", perm: "add_mold", hidden: false }
        },
        {
          path: "aptation",
          name:"machinead_aptation",
          component: () => import("@/views/moldMag/machineAdaptation.vue"),
          meta: { title: "注塑机适配", icon: "list", perm: "mold_list", hidden: true }
        }
      ]
    },
    {
      path: "/process",
      component: Layout,
      redirect: "/process/record/list",
      name: "process",
      meta: { title: "工艺管理", icon: "project", perm: "process_manage" },
      children: [
        {
          path: "record/list",
          name: "process_record_list",
          component: () => import("@/views/processMag/record/list.vue"),
          meta: { title: "工艺列表", icon: "list", perm: "process_list" }
        },
        {
          path: "record/create",
          name: "process_record",
          component: () => import("@/views/processMag/record/create.vue"),
          meta: { title: "工艺录入", icon: "form", perm: "process_entry" }
        },
        {
          path: "record/transplant",
          name:"process_transplant",
          component: () => import("@/views/processMag/record/transplant.vue"),
          meta: { title: "工艺移植", icon: "component", perm: "process_transplant" }
        },
        {
          path: "optimize/list",
          name: "optimize_list",
          component: () => import("@/views/processMag/optimization/list.vue"),
          meta: { title: "优化列表", icon: "list", perm: "process_list" }
        },
        {
          path: "optimize/create",
          name: "process_optimize",
          component: () => import("@/views/processMag/optimization/create.vue"),
          meta: { title: "工艺优化", icon: "component", perm: "process_optimize" }
        },
        {
          path: "optimize/expert_record_list",
          name: "expert_record_list",
          component: () => import("@/views/processMag/expert/list.vue"),
          meta: { title: "记录列表", icon: "list", perm: "process_list" }
        }, 
        {
          path: "optimize/expert_record",
          name: "expert_record",
          component: () => import("@/views/processMag/expert/create.vue"),
          meta: { title: "专家调优", icon: "component", perm: "process_optimize" }
        },
        {
          path: "optimize/rule",
          name: "process_rule",
          component: () => import("@/views/processMag/optimization/rule.vue"),
          meta: { title: "优化规则", icon: "list", perm: "process_rule",hidden:true }
        },
        {
          path: "optimize/flow",
          name: "rule_flow",
          component: () => import("@/views/processMag/optimization/subView/ruleFlow.vue"),
          meta: { title: "规则流程图", icon: "list", perm: "process_rule" }
        },  
        {
          path: "record/adaptation",
          name: "transplant_adaptation",
          component: () => import("@/views/processMag/record/transplantAdaptation.vue"),
          meta: { title: "工艺与机器适配", icon: "component", perm: "process_transplant",hidden:true }
        },
      ]
    },
    {
      path: "/machine",
      component: Layout,
      redirect: "/machine/injection/list",
      name: "machine",
      meta: { title: "机器管理", icon: "project", perm: "machine_manage" },
      children: [
        {
          path: "injection/list",
          name: "injection_list",
          component: () => import("@/views/machineMag/injection/InjectionMachineList.vue"),
          meta: { title: "机器列表", icon: "list", perm: "machine_list" }
        },
        {
          path: "injection/create",
          name: "create_injection",
          component: () => import("@/views/machineMag/injection/CreateInjectionMachine.vue"),
          meta: { title: "新增机器", icon: "form", perm: "add_machine" }
        },
      ]
    },
    {
      path: "/polymer",
      component: Layout,
      redirect: "/polymer/list",
      name: "polymer",
      meta: { title: "材料管理", icon: "project", perm: "polymer_manage" },
      children: [
        {
          path: "list",
          name: "polymer_list",
          component: () => import("@/views/polymerMag/list.vue"),
          meta: { title: "材料列表", icon: "list", perm: "polymer_list" }
        },
        {
          path: "create",
          name: "polymer_create",
          component: () => import("@/views/polymerMag/create.vue"),
          meta: { title: "新增材料", icon: "form", perm: "add_polymer" }
        }
      ]
    },
    {
      path: "/auth",
      component: Layout,
      redirect: "/auth/user",
      name: "auth",
      meta: { title: "权限管理", icon: "lock", perm: "permission_manage" },
      children: [
        {
          path: "departmentTree",
          name: "departmentTree",
          component: () => import("@/views/userMag/groupList.vue"),
          meta: { title: "组织管理", icon: "tree", perm: "department_manage" }
        },
        {
          path: "role",
          name: "role",
          component: () => import("@/views/userMag/roleList.vue"),
          meta: { title: "角色管理", icon: "role-key", perm: "role_manage" }
        },
        {
          path: "user",
          name: "user",
          component: () => import("@/views/userMag/userList.vue"),
          meta: { title: "用户管理", icon: "user", perm: "user_manage" }
        },
      ]
    },
    {
      path: "/super",
      component: Layout,
      redirect: "/super/user",
      name: "super",
      meta: { title: "超级用户", icon: "super", perm: "super_user" },
      children: [
        {
          path: "company",
          name: "super_company",
          component: () => import("@/views/superMag/companyList.vue"),
          meta: { title: "企业管理", icon: "user", perm: "super_user" }
        },
        {
          path: "groupTree",
          name: "groupTree",
          component: () => import("@/views/superMag/groupList.vue"),
          meta: { title: "组织管理", icon: "tree", perm: "super_user" }
        },
        {
          path: "role",
          name: "super_role",
          component: () => import("@/views/superMag/roleList.vue"),
          meta: { title: "角色管理", icon: "role-key", perm: "super_user" }
        },
        {
          path: "user",
          name: "super_user",
          component: () => import("@/views/superMag/userList.vue"),
          meta: { title: "用户管理", icon: "user", perm: "super_user" }
        },
      ]
    },  
    {
      path: "*",
      redirect: "/404",
      meta: { hidden: true }
    }
  ]
})
