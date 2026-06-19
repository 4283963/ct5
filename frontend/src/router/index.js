import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/diagnosis',
    name: 'Diagnosis',
    component: () => import('@/views/Diagnosis.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
