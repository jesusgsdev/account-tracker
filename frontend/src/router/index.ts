import { createRouter, createWebHistory } from 'vue-router'
import { authApi } from '@/api/client'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/accounts',
      name: 'accounts',
      component: () => import('@/views/AccountsView.vue'),
    },
    {
      path: '/market-trackers',
      name: 'market-trackers',
      component: () => import('@/views/MarketTrackersView.vue'),
    },
    {
      path: '/audit',
      name: 'audit',
      component: () => import('@/views/AuditView.vue'),
    },
    {
      path: '/data',
      name: 'data',
      component: () => import('@/views/DataView.vue'),
    },
    {
      path: '/property',
      name: 'property',
      component: () => import('@/views/PropertyView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const user = await authApi.check()
  if (to.name !== 'login' && !user) return { name: 'login' }
  if (to.name === 'login' && user) return { name: 'dashboard' }
})

export default router
