import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    component: () => import('@/views/HomeView.vue'),
    meta: { layout: 'default' },
  },
  {
    path: '/search',
    component: () => import('@/views/SearchView.vue'),
    meta: { layout: 'default' },
  },
  {
    path: '/product/:id',
    component: () => import('@/views/ProductDetail.vue'),
    meta: { layout: 'default' },
  },
  {
    path: '/publish',
    component: () => import('@/views/PublishView.vue'),
    meta: { layout: 'default', requiresAuth: true },
  },
  {
    path: '/chat',
    component: () => import('@/views/ChatList.vue'),
    meta: { layout: 'default', requiresAuth: true },
  },
  {
    path: '/chat/:id',
    component: () => import('@/views/ChatView.vue'),
    meta: { layout: 'chat', requiresAuth: true },
  },
  {
    path: '/profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { layout: 'default', requiresAuth: true },
  },
  {
    path: '/profile/:id',
    component: () => import('@/views/ProfileView.vue'),
    meta: { layout: 'default' },
  },
  {
    path: '/my-products',
    component: () => import('@/views/MyProducts.vue'),
    meta: { layout: 'default', requiresAuth: true },
  },
  {
    path: '/my-orders',
    component: () => import('@/views/MyOrders.vue'),
    meta: { layout: 'default', requiresAuth: true },
  },
  {
    path: '/login',
    component: () => import('@/views/LoginView.vue'),
    meta: { layout: 'blank', guest: true },
  },
  {
    path: '/register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { layout: 'blank', guest: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (to.meta.guest && auth.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
