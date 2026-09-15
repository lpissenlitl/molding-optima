// molding-optima 路由（Vue Router 4）
// 设计原则：
// - 路由是菜单的唯一真理之源（sidebar 自动从 router 生成）
// - 默认 2 级菜单（视觉简洁），alwaysShow=true 可强制显示父级
// - 中间层路由用 ParentView 占位（无真实页面）

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import ParentView from '@/views/layout/components/parentView.vue'
import Placeholder from '@/views/placeholder/index.vue'

// 业务模块占位组件（演示用，业务迁移完成后替换）
const BusinessPlaceholder = Placeholder

const routes: RouteRecordRaw[] = [
  // 登录（无 layout）
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/index.vue'),
    meta: { hidden: true, title: '登录' },
  },

  // 404（无 layout）
  {
    path: '/404',
    name: 'not-found',
    component: () => import('@/views/404.vue'),
    meta: { hidden: true, title: '404' },
  },

  // layout 容器
  {
    path: '/',
    component: () => import('@/views/layout/layout.vue'),
    redirect: '/dashboard',
    children: [
      // 看板
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '看板', icon: 'mdi:view-dashboard' },
      },

      // 模具管理（项目作为子菜单）
      {
        path: 'mold',
        component: ParentView,
        redirect: '/mold/list',
        meta: { title: '模具管理', icon: 'mdi:cube-outline', alwaysShow: true },
        children: [
          {
            path: 'list',
            name: 'mold-list',
            component: () => import('@/views/mold/pages/MoldList.vue'),
            meta: { title: '模具列表', icon: 'mdi:view-list' },
          },
          {
            path: 'new',
            name: 'mold-new',
            component: () => import('@/views/mold/pages/MoldForm.vue'),
            meta: { title: '新建模具', hidden: true },
          },
          {
            path: ':id/edit',
            name: 'mold-edit',
            component: () => import('@/views/mold/pages/MoldForm.vue'),
            meta: { title: '编辑模具', hidden: true },
          },
          {
            path: 'project/list',
            name: 'mold-project-list',
            component: () => import('@/views/project/pages/ProjectList.vue'),
            meta: { title: '项目列表', icon: 'mdi:briefcase-outline' },
          },
          {
            path: 'project/new',
            name: 'mold-project-new',
            component: () => import('@/views/project/pages/ProjectForm.vue'),
            meta: { title: '新建项目', hidden: true },
          },
          {
            path: 'project/:id/edit',
            name: 'mold-project-edit',
            component: () => import('@/views/project/pages/ProjectForm.vue'),
            meta: { title: '编辑项目', hidden: true },
          },
        ],
      },

      // 工艺管理
      {
        path: 'process',
        component: ParentView,
        redirect: '/process/parameter',
        meta: { title: '工艺管理', icon: 'mdi:chart-line' },
        children: [
          // 工艺参数视图（基于 ProcessCondition 载体）
          {
            path: 'parameter',
            name: 'process-parameter',
            component: () => import('@/views/process/parameter/pages/ProcessParameterList.vue'),
            meta: { title: '工艺参数', icon: 'mdi:tune' },
          },
          {
            path: 'parameter/new',
            name: 'process-parameter-new',
            component: () => import('@/views/process/parameter/pages/ProcessParameterForm.vue'),
            meta: { title: '新建工艺', hidden: true },
          },
          {
            path: 'parameter/:id/edit',
            name: 'process-parameter-edit',
            component: () => import('@/views/process/parameter/pages/ProcessParameterForm.vue'),
            meta: { title: '编辑工艺', hidden: true },
          },
          {
            path: 'parameter/:id/detail',
            name: 'process-parameter-detail',
            component: () => import('@/views/process/parameter/pages/ProcessParameterForm.vue'),
            meta: { title: '工艺详情', hidden: true },
          },
          {
            path: 'optimization',
            name: 'process-optimization',
            component: BusinessPlaceholder,
            meta: { title: '优化记录', icon: 'mdi:lightbulb-on-outline' },
          },
          {
            path: 'rules',
            name: 'process-rules',
            component: () => import('@/views/process/rule/pages/RuleLibraryList.vue'),
            meta: { title: '规则中心', icon: 'mdi:format-list-checks' },
          },
          {
            path: 'rules/:libraryId(\\d+)',
            name: 'process-rules-detail',
            component: () => import('@/views/process/rule/pages/RuleLibraryDetail.vue'),
            meta: { title: '规则库详情', hidden: true, activeMenu: '/process/rules' },
          },
        ],
      },

      // 设备管理（2026-09-09 重构：物理目录拆为 injection/auxiliary，路由统一前缀）
      {
        path: 'equipment',
        component: ParentView,
        redirect: '/equipment/injection/list',
        meta: { title: '设备管理', icon: 'mdi:factory', alwaysShow: true },
        children: [
          // 注塑机
          {
            path: 'injection/list',
            name: 'equipment-injection-list',
            component: () => import('@/views/injection/pages/InjectionMachineList.vue'),
            meta: { title: '注塑机列表', icon: 'mdi:server-outline' },
          },
          {
            path: 'injection/new',
            name: 'equipment-injection-new',
            component: () => import('@/views/injection/pages/InjectionMachineForm.vue'),
            meta: { title: '新建注塑机', hidden: true },
          },
          {
            path: 'injection/:id/edit',
            name: 'equipment-injection-edit',
            component: () => import('@/views/injection/pages/InjectionMachineForm.vue'),
            meta: { title: '编辑注塑机', hidden: true },
          },
          {
            path: 'injection/:id/copy',
            name: 'equipment-injection-copy',
            component: () => import('@/views/injection/pages/InjectionMachineForm.vue'),
            meta: { title: '复制注塑机', hidden: true },
          },
          // 辅机
          {
            path: 'auxiliary/list',
            name: 'equipment-auxiliary-list',
            component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentList.vue'),
            meta: { title: '辅机列表', icon: 'mdi:tools' },
          },
          {
            path: 'auxiliary/new',
            name: 'equipment-auxiliary-new',
            component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentForm.vue'),
            meta: { title: '新建辅机', hidden: true },
          },
          {
            path: 'auxiliary/:id/edit',
            name: 'equipment-auxiliary-edit',
            component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentForm.vue'),
            meta: { title: '编辑辅机', hidden: true },
          },
          {
            path: 'auxiliary/:id/copy',
            name: 'equipment-auxiliary-copy',
            component: () => import('@/views/auxiliary/pages/AuxiliaryEquipmentForm.vue'),
            meta: { title: '复制辅机', hidden: true },
          },
        ],
      },

      // 材料管理（2026-09-08 重构：物理目录独立，路由统一前缀）
      {
        path: 'material',
        component: ParentView,
        redirect: '/material/polymer/list',
        meta: { title: '材料管理', icon: 'mdi:flask-outline', alwaysShow: true },
        children: [
          {
            path: 'polymer/list',
            name: 'material-polymer-list',
            component: () => import('@/views/polymer/pages/PolymerList.vue'),
            meta: { title: '塑料列表', icon: 'mdi:beaker-outline' },
          },
          {
            path: 'polymer/new',
            name: 'material-polymer-new',
            component: () => import('@/views/polymer/pages/PolymerForm.vue'),
            meta: { title: '新建塑料', hidden: true },
          },
          {
            path: 'polymer/:id/edit',
            name: 'material-polymer-edit',
            component: () => import('@/views/polymer/pages/PolymerForm.vue'),
            meta: { title: '编辑塑料', hidden: true },
          },
          {
            path: 'polymer/:id/copy',
            name: 'material-polymer-copy',
            component: () => import('@/views/polymer/pages/PolymerForm.vue'),
            meta: { title: '复制塑料', hidden: true },
          },
          {
            path: 'filler/list',
            name: 'material-filler-list',
            component: () => import('@/views/filler/pages/FillerList.vue'),
            meta: { title: '填充物列表', icon: 'mdi:grain' },
          },
          {
            path: 'filler/new',
            name: 'material-filler-new',
            component: () => import('@/views/filler/pages/FillerForm.vue'),
            meta: { title: '新建填充物', hidden: true },
          },
          {
            path: 'filler/:id/edit',
            name: 'material-filler-edit',
            component: () => import('@/views/filler/pages/FillerForm.vue'),
            meta: { title: '编辑填充物', hidden: true },
          },
          {
            path: 'filler/:id/copy',
            name: 'material-filler-copy',
            component: () => import('@/views/filler/pages/FillerForm.vue'),
            meta: { title: '复制填充物', hidden: true },
          },
        ],
      },

      // 权限管理
      {
        path: 'admin',
        component: ParentView,
        redirect: '/admin/user',
        meta: {
          title: '权限管理',
          icon: 'mdi:shield-account',
          alwaysShow: true,
          permission: 'permission_manage',
          breadcrumb: '权限管理',
        },
        children: [
          {
            path: 'company',
            name: 'admin-company',
            component: () => import('@/views/admin/company/CompanyList.vue'),
            meta: {
              title: '公司管理',
              icon: 'mdi:office-building-outline',
              permission: 'company_manage',
              breadcrumb: '公司管理',
            },
          },
          {
            path: 'organization',
            name: 'admin-organization',
            component: () => import('@/views/admin/organization/OrganizationTree.vue'),
            meta: {
              title: '组织架构',
              icon: 'mdi:sitemap-outline',
              permission: 'department_manage',
              breadcrumb: '组织架构',
            },
          },
          {
            path: 'role',
            name: 'admin-role',
            component: () => import('@/views/admin/role/RoleList.vue'),
            meta: {
              title: '角色管理',
              icon: 'mdi:shield-account-outline',
              permission: 'role_manage',
              breadcrumb: '角色管理',
            },
          },
          {
            path: 'user',
            name: 'admin-user',
            component: () => import('@/views/admin/user/UserList.vue'),
            meta: {
              title: '用户管理',
              icon: 'mdi:account-multiple-outline',
              permission: 'user_manage',
              breadcrumb: '用户管理',
            },
          },
        ],
      },
    ],
  },

  // 兜底路由
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404',
    meta: { hidden: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

export default router