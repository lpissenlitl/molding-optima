/**
 * molding-optima 路由配置
 *
 * 模块：
 * - /login           登录
 * - /admin           公司/组织/角色/用户管理（superManage）
 * - /process         工艺管理（processManage）- 核心
 * - /polymer         材料管理（polymerManage）
 * - /filler          填充物管理（fillerManage）
 *
 * 后续迁移 vue3 + element-plus 时重构
 */
import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

import Layout from '@/views/layout/layout.vue'

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
      component: Layout,
      redirect: '/process/conditions',
    },
    {
      // ========== 工艺管理（核心）==========
      path: '/process',
      component: Layout,
      redirect: '/process/conditions',
      name: 'process',
      meta: { title: '工艺管理', icon: 'mdi:cog-outline', perm: 'process_manage' },
      children: [
        {
          path: 'conditions',
          name: 'process_condition_list',
          component: () => import('@/views/processManage/condition/ConditionList.vue'),
          meta: { title: '工艺列表', icon: 'mdi:tune', perm: 'process_list' },
        },
        {
          path: 'conditions/create',
          name: 'process_condition_create',
          component: () => import('@/views/processManage/condition/ConditionForm.vue'),
          meta: { title: '录入工艺', icon: 'mdi:plus-circle', perm: 'process_entry' },
        },
        {
          path: 'conditions/:id',
          name: 'process_condition_detail',
          component: () => import('@/views/processManage/condition/ConditionDetail.vue'),
          meta: { title: '工艺详情', icon: 'mdi:information-outline', perm: 'process_list', hidden: true },
        },
        {
          path: 'transplant',
          name: 'process_transplant',
          component: () => import('@/views/processManage/transplant/Transplant.vue'),
          meta: { title: '工艺移植', icon: 'mdi:transfer', perm: 'process_transplant' },
        },
        {
          path: 'optimize',
          name: 'process_optimize',
          component: () => import('@/views/processManage/optimize/Optimize.vue'),
          meta: { title: '工艺优化', icon: 'mdi:rocket-launch', perm: 'process_optimize' },
        },
        {
          path: 'expert',
          name: 'process_expert',
          component: () => import('@/views/processManage/expert/Expert.vue'),
          meta: { title: '专家调优', icon: 'mdi:account-tie', perm: 'process_optimize' },
        },
      ],
    },
    {
      // ========== 主数据：模具/机器/材料/填充物 ==========
      path: '/mold',
      component: Layout,
      redirect: '/mold/list',
      name: 'mold',
      meta: { title: '模具管理', icon: 'mdi:tools', perm: 'mold_manage' },
      children: [
        {
          path: 'list',
          name: 'mold_list',
          component: () => import('@/views/superManage/MoldList.vue'),
          meta: { title: '模具列表', icon: 'mdi:view-grid', perm: 'mold_list' },
        },
      ],
    },
    {
      path: '/machine',
      component: Layout,
      redirect: '/machine/list',
      name: 'machine',
      meta: { title: '设备管理', icon: 'mdi:factory', perm: 'machine_manage' },
      children: [
        {
          path: 'list',
          name: 'machine_list',
          component: () => import('@/views/superManage/MachineList.vue'),
          meta: { title: '机器列表', icon: 'mdi:server-outline', perm: 'machine_list' },
        },
      ],
    },
    {
      path: '/polymer',
      component: Layout,
      redirect: '/polymer/list',
      name: 'polymer',
      meta: { title: '材料管理', icon: 'mdi:flask-outline', perm: 'polymer_manage' },
      children: [
        {
          path: 'list',
          name: 'polymer_list',
          component: () => import('@/views/polymerManage/list.vue'),
          meta: { title: '材料列表', icon: 'mdi:beaker', perm: 'polymer_list' },
        },
        {
          path: 'create',
          name: 'polymer_create',
          component: () => import('@/views/polymerManage/create.vue'),
          meta: { title: '新增材料', icon: 'mdi:plus-circle', perm: 'add_polymer' },
        },
      ],
    },
    {
      path: '/filler',
      component: Layout,
      redirect: '/filler/list',
      name: 'filler',
      meta: { title: '填充物管理', icon: 'mdi:grain', perm: 'polymer_manage' },
      children: [
        {
          path: 'list',
          name: 'filler_list',
          component: () => import('@/views/fillerManage/FillerList.vue'),
          meta: { title: '填充物列表', icon: 'mdi:grain', perm: 'polymer_list' },
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
          path: 'user/list',
          name: 'user_list',
          component: () => import('@/views/superManage/UserList.vue'),
          meta: { title: '用户管理', icon: 'mdi:account-group', perm: 'user_manage' },
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
