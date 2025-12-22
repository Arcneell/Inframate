import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import Ipam from './views/Ipam.vue'
import ScriptRunner from './views/ScriptRunner.vue'
import Topology from './views/Topology.vue'
import Login from './views/Login.vue'
import Settings from './views/Settings.vue'

const routes = [
  { path: '/login', component: Login, name: 'Login' },
  { path: '/', component: Dashboard, name: 'Dashboard' },
  { path: '/ipam', component: Ipam, name: 'IP Address Management' },
  { path: '/topology', component: Topology, name: 'Network Topology' },
  { path: '/scripts', component: ScriptRunner, name: 'Script Automation' },
  { path: '/settings', component: Settings, name: 'Settings' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const publicPages = ['/login'];
  const authRequired = !publicPages.includes(to.path);
  const loggedIn = localStorage.getItem('token');

  if (authRequired && !loggedIn) {
    return next('/login');
  }

  // If logged in and trying to access login page, redirect to dashboard
  if (loggedIn && to.path === '/login') {
    return next('/');
  }

  next();
});

export default router