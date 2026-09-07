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

  // layout 容器（包裹业务页面）
  // 业务边界：6 个顶级模块
  // - 模具管理、设备管理、工艺管理、材料管理、权限管理、项目管理
  {
    path: '/',
    component: () => import('@/views/layout/layout.vue'),
    redirect: '/dashboard',
    children: [
      // 看板（叶子，首页入口）
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '看板', icon: 'mdi:view-dashboard' },
      },

      // 模具管理（alwaysShow：多子菜单分组）
      // 模具表单（新增/编辑）走独立页面，不占用独立菜单项
      // RESTful 风格路由：
      // - /mold/new         新建
      // - /mold/:id/edit    编辑
      // - /mold/new?project_id=X    从项目跳转创建（带项目上下文）
      // new / edit 用 hidden=true，在菜单中隐藏（侧边栏过滤）
      {
        path: 'mold',
        component: ParentView,
        redirect: '/mold/list',
        meta: { title: '模具管理', icon: 'mdi:cube-outline', alwaysShow: true },
        children: [
          { path: 'list',      name: 'mold-list',  component: () => import('@/views/mold/pages/MoldList.vue'),  meta: { title: '模具列表', icon: 'mdi:view-list' } },
          { path: 'new',       name: 'mold-new',   component: () => import('@/views/mold/pages/MoldForm.vue'), meta: { title: '新建模具', hidden: true } },
          { path: ':id/edit',  name: 'mold-edit',  component: () => import('@/views/mold/pages/MoldForm.vue'), meta: { title: '编辑模具', hidden: true } },
        ],
      },

      // 项目管理（独立顶级模块）
      // 表单页（form.vue）同时处理新建和编辑（RESTful 风格路由）
      // - /project/new           新建
      // - /project/:id/edit      编辑
      // new / edit 用 hidden=true，在菜单中隐藏（侧边栏过滤）
      {
        path: 'project',
        component: ParentView,
        redirect: '/project/list',
        meta: { title: '项目管理', icon: 'mdi:briefcase-outline', alwaysShow: true },
        children: [
          { path: 'list',      name: 'project-list',  component: () => import('@/views/project/pages/ProjectList.vue'), meta: { title: '项目列表', icon: 'mdi:view-list' } },
          { path: 'new',       name: 'project-new',   component: () => import('@/views/project/pages/ProjectForm.vue'), meta: { title: '新建项目', hidden: true } },
          { path: ':id/edit',  name: 'project-edit',  component: () => import('@/views/project/pages/ProjectForm.vue'), meta: { title: '编辑项目', hidden: true } },
        ],
      },

      // 工艺管理（核心）
      {
        path: 'process',
        component: ParentView,
        redirect: '/process/parameter',
        meta: { title: '工艺管理', icon: 'mdi:chart-line' },
        children: [
          { path: 'parameter',    name: 'process-parameter',    component: BusinessPlaceholder, meta: { title: '工艺列表', icon: 'mdi:tune' } },
          { path: 'optimization', name: 'process-optimization', component: BusinessPlaceholder, meta: { title: '优化记录', icon: 'mdi:lightbulb-on-outline' } },
          { path: 'rules',        name: 'process-rules',        component: BusinessPlaceholder, meta: { title: '优化规则', icon: 'mdi:format-list-checks' } },
        ],
      },

      // 设备管理
      {
        path: 'equipment',
        component: ParentView,
        redirect: '/equipment/injection',
        meta: { title: '设备管理', icon: 'mdi:factory' },
        children: [
          { path: 'injection', name: 'equipment-injection', component: BusinessPlaceholder, meta: { title: '机器列表', icon: 'mdi:server-outline' } },
          { path: 'auxiliary', name: 'equipment-auxiliary', component: BusinessPlaceholder, meta: { title: '辅助装置', icon: 'mdi:tools' } },
        ],
      },

      // 材料管理
      {
        path: 'polymer',
        component: ParentView,
        redirect: '/polymer/list',
        meta: { title: '材料管理', icon: 'mdi:flask-outline' },
        children: [
          { path: 'list',   name: 'polymer-list',   component: BusinessPlaceholder, meta: { title: '材料列表', icon: 'mdi:beaker-outline' } },
          { path: 'filler', name: 'polymer-filler', component: BusinessPlaceholder, meta: { title: '填充物',   icon: 'mdi:grain' } },
        ],
      },

      // 权限管理（alwaysShow：4 个子菜单分组）
      //
      // meta 规范：
      // - permission：访问该路由所需的权限码（用于路由守卫）
      // - breadcrumb：面包屑显示名称（默认 = title）
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