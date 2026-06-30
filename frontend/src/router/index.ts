/**
 * molding-optima 路由配置
 *
 * 设计源头：molding-expert/molding-expert-web/src/router/index.ts
 * 业务边界：不引入 schedule / inventory / mold-trial / monitoring / costing / notice / moldflow
 *
 * 模块：
 * - /login           登录
 * - /mold            模具管理（moldManage）
 * - /equipment       设备管理（machineManage）
 * - /process         工艺管理（processManage - 核心）
 * - /polymer         材料管理（polymerManage + fillerManage）
 * - /admin           权限管理（superManage）
 */
import Vue from 'vue'
import Router from 'vue-router'
import Layout from '@/views/layout/layout.vue'

Vue.use(Router)

// 解决重复路由点击报错
const originalPush = Router.prototype.push
Router.prototype.push = function push(location: any) {
  return (originalPush.call(this, location) as any).catch((err: any) => { err })
}

export default new Router({
  mode: 'history',
  scrollBehavior: (to, from, savedPosition) => {
    if (savedPosition) return savedPosition
    return { x: 0, y: 0 }
  },
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/login',
      component: () => import('@/views/login/index.vue'),
      meta: { hidden: true },
    },
    {
      path: '/404',
      component: () => import('@/views/404.vue'),
      meta: { hidden: true },
    },
    {
      path: '/',
      redirect: '/process/parameter/list',
    },
    {
      // ========== 模具管理 ==========
      path: '/mold',
      component: Layout,
      redirect: '/mold/list',
      name: 'mold_manage',
      meta: { title: '模具管理', icon: 'mdi:tools', perm: 'mold_manage' },
      children: [
        {
          path: 'list',
          name: 'mold_list',
          component: () => import('@/views/moldManage/MoldList.vue'),
          meta: { title: '模具列表', icon: 'mdi:view-grid', perm: 'mold_list' },
        },
        {
          path: 'create',
          name: 'mold_create',
          component: () => import('@/views/moldManage/MoldForm.vue'),
          meta: { title: '新增模具', icon: 'mdi:plus-circle', perm: 'add_mold', hidden: true },
        },
        {
          path: 'project/list',
          name: 'project_list',
          component: () => import('@/views/moldManage/ProjectList.vue'),
          meta: { title: '项目列表', icon: 'mdi:briefcase', perm: 'project_list' },
        },
        {
          path: 'project/create',
          name: 'project_create',
          component: () => import('@/views/moldManage/ProjectForm.vue'),
          meta: { title: '新增项目', icon: 'mdi:plus-circle', perm: 'add_project', hidden: true },
        },
      ],
    },
    {
      // ========== 设备管理 ==========
      path: '/equipment',
      component: Layout,
      redirect: '/equipment/injection/list',
      name: 'machine',
      meta: { title: '设备管理', icon: 'mdi:factory', perm: 'machine_manage' },
      children: [
        {
          path: 'injection/list',
          name: 'injection_list',
          component: () => import('@/views/machineManage/InjectionMachineList.vue'),
          meta: { title: '机器列表', icon: 'mdi:server-outline', perm: 'machine_list' },
        },
        {
          path: 'injection/create',
          name: 'injection_create',
          component: () => import('@/views/machineManage/InjectionMachineForm.vue'),
          meta: { title: '新增机器', icon: 'mdi:plus-circle', perm: 'add_machine' },
        },
        {
          path: 'auxiliary/list',
          name: 'auxiliary_list',
          component: () => import('@/views/machineManage/AuxiliaryEquipmentList.vue'),
          meta: { title: '辅助装置', icon: 'mdi:tools', perm: 'auxiliary_list' },
        },
      ],
    },
    {
      // ========== 工艺管理（核心）==========
      path: '/process',
      component: Layout,
      redirect: '/process/parameter/list',
      name: 'process',
      meta: { title: '工艺管理', icon: 'mdi:cog-outline', perm: 'process_manage' },
      children: [
        {
          path: 'parameter/list',
          name: 'process_parameter_list',
          component: () => import('@/views/processManage/parameter/ProcessParameterList.vue'),
          meta: { title: '工艺列表', icon: 'mdi:tune', perm: 'process_list' },
        },
        {
          path: 'parameter/create',
          name: 'process_parameter_create',
          component: () => import('@/views/processManage/parameter/ProcessParameterCreate.vue'),
          meta: { title: '工艺录入', icon: 'mdi:plus-circle', perm: 'process_entry' },
        },
        {
          path: 'parameter/transplant',
          name: 'process_transplant',
          component: () => import('@/views/processManage/adaptation/ProcessParameterTransplant.vue'),
          meta: { title: '工艺移植', icon: 'mdi:transfer', perm: 'process_transplant' },
        },
      ],
    },
    {
      // ========== 材料管理 ==========
      path: '/polymer',
      component: Layout,
      redirect: '/polymer/list',
      name: 'polymer',
      meta: { title: '材料管理', icon: 'mdi:flask-outline', perm: 'polymer_manage' },
      children: [
        {
          path: 'list',
          name: 'polymer_list',
          component: () => import('@/views/polymerManage/PolymerList.vue'),
          meta: { title: '材料列表', icon: 'mdi:beaker', perm: 'polymer_list' },
        },
        {
          path: 'create',
          name: 'polymer_create',
          component: () => import('@/views/polymerManage/PolymerForm.vue'),
          meta: { title: '新增材料', icon: 'mdi:plus-circle', perm: 'add_polymer' },
        },
        {
          path: 'filler/list',
          name: 'filler_list',
          component: () => import('@/views/fillerManage/FillerList.vue'),
          meta: { title: '填充物信息', icon: 'mdi:grain', perm: 'polymer_list' },
        },
        {
          path: 'filler/create',
          name: 'filler_create',
          component: () => import('@/views/fillerManage/FillerCreate.vue'),
          meta: { title: '新增填充物', icon: 'mdi:plus-circle', perm: 'add_polymer' },
        },
      ],
    },
    {
      // ========== 管理员（公司/组织/角色/用户）==========
      path: '/admin',
      component: Layout,
      redirect: '/admin/user/list',
      name: 'admin',
      meta: { title: '权限管理', icon: 'mdi:cog', perm: 'permission_manage' },
      children: [
        {
          path: 'company/list',
          name: 'company_list',
          component: () => import('@/views/superManage/CompanyList.vue'),
          meta: { title: '公司管理', icon: 'mdi:office-building', perm: 'company_manage' },
        },
        {
          path: 'company/create',
          name: 'company_create',
          component: () => import('@/views/superManage/CompanyCreate.vue'),
          meta: { title: '新增公司', icon: 'mdi:plus-circle', perm: 'add_company', hidden: true },
        },
        {
          path: 'organization/tree',
          name: 'organization_tree',
          component: () => import('@/views/superManage/OrganizationTree.vue'),
          meta: { title: '组织管理', icon: 'mdi:sitemap', perm: 'department_manage' },
        },
        {
          path: 'role/list',
          name: 'role_list',
          component: () => import('@/views/superManage/RoleList.vue'),
          meta: { title: '角色管理', icon: 'mdi:shield-account', perm: 'role_manage' },
        },
        {
          path: 'role/create',
          name: 'role_create',
          component: () => import('@/views/superManage/RoleCreate.vue'),
          meta: { title: '新增角色', icon: 'mdi:plus-circle', perm: 'add_role', hidden: true },
        },
        {
          path: 'user/list',
          name: 'user_list',
          component: () => import('@/views/superManage/UserList.vue'),
          meta: { title: '用户管理', icon: 'mdi:account-group', perm: 'user_manage' },
        },
        {
          path: 'user/create',
          name: 'user_create',
          component: () => import('@/views/superManage/UserCreate.vue'),
          meta: { title: '新增用户', icon: 'mdi:account-plus', perm: 'add_user', hidden: true },
        },
      ],
    },
    {
      path: '*',
      redirect: '/404',
      meta: { hidden: true },
    },
  ],
})