import { createRouter, createWebHistory } from 'vue-router'
import { api } from '../api'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/RegisterView.vue') },
  { path: '/', name: 'Dashboard', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/contests/:id', name: 'ContestDetail', component: () => import('../views/ContestDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/challenges', name: 'ChallengeList', component: () => import('../views/ChallengeListView.vue'), meta: { requiresAuth: true } },
  { path: '/challenges/:id', name: 'ChallengeDetail', component: () => import('../views/ChallengeDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/defend/:id', name: 'DefenseUpload', component: () => import('../views/DefenseUploadView.vue'), meta: { requiresAuth: true } },
  { path: '/leaderboard', name: 'Leaderboard', component: () => import('../views/LeaderboardView.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  // Redirect admin paths to Flask backend
  if (to.path.startsWith('/admin')) {
    window.location.href = to.fullPath
    return
  }

  if (to.meta.requiresAuth) {
    try {
      await api.me()
      next()
    } catch {
      next({ name: 'Login', query: { redirect: to.fullPath } })
    }
  } else {
    next()
  }
})

export default router
