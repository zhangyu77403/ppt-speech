import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, ensureAuth, notify } from './store'

const routes = [
  { path: '/', name: 'home', component: () => import('./views/Landing.vue') },
  { path: '/login', name: 'login', component: () => import('./views/Login.vue'), meta: { bare: true } },
  { path: '/app/:id', name: 'workspace', component: () => import('./views/Workspace.vue'), meta: { auth: true } },
  { path: '/history', name: 'history', component: () => import('./views/History.vue'), meta: { auth: true } },
  { path: '/present/:id', name: 'present', component: () => import('./views/Present.vue'), meta: { auth: true, bare: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  if (!to.meta.auth) return true
  // ?demo=1 时自动以体验账号进入，方便分享演示链接
  if (to.query.demo === '1') {
    if (await ensureAuth()) return true
  }
  if (isLoggedIn()) {
    const ok = await ensureAuth()
    if (ok) return true
  }
  notify('请先登录后继续', 'warn')
  return { name: 'login', query: { next: to.fullPath } }
})

export default router
