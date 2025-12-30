<template>
  <div class="h-screen w-screen overflow-hidden flex bg-[var(--bg-app)] text-[var(--text-main)]" v-if="!isLoginPage">

    <aside class="w-64 sidebar-container flex-shrink-0 flex flex-col z-20">
      <div class="sidebar-header">
        <i class="pi pi-bolt text-blue-500 text-xl mr-3"></i>
        <span class="text-white font-bold text-lg tracking-wide">NetOps Flow</span>
      </div>

      <div class="flex-grow py-4 overflow-y-auto custom-scrollbar">
        <nav class="flex flex-col space-y-1">
            <router-link to="/" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-home mr-3"></i> {{ t('nav.dashboard') }}
                </div>
            </router-link>

            <div class="px-6 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mt-4">Helpdesk</div>

            <router-link to="/tickets" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-ticket mr-3"></i> {{ t('tickets.title') }}
                </div>
            </router-link>
            <router-link to="/knowledge" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-book mr-3"></i> {{ t('knowledge.title') }}
                </div>
            </router-link>

            <div v-if="hasPerm('ipam') || hasPerm('topology')" class="px-6 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mt-4">{{ t('nav.network') }}</div>

            <router-link v-if="hasPerm('ipam')" to="/ipam" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-table mr-3"></i> {{ t('nav.ipam') }}
                </div>
            </router-link>
            <router-link v-if="hasPerm('topology')" to="/topology" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-share-alt mr-3"></i> {{ t('nav.topology') }}
                </div>
            </router-link>

            <div v-if="hasPerm('scripts')" class="px-6 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mt-4">{{ t('nav.automation') }}</div>

            <router-link v-if="hasPerm('scripts')" to="/scripts" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-code mr-3"></i> {{ t('nav.scriptRunner') }}
                </div>
            </router-link>

            <div v-if="hasPerm('inventory')" class="px-6 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mt-4">{{ t('nav.inventory') }}</div>

            <router-link v-if="hasPerm('inventory')" to="/inventory" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-box mr-3"></i> {{ t('nav.inventory') }}
                </div>
            </router-link>
            <router-link v-if="hasPerm('inventory')" to="/dcim" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-server mr-3"></i> {{ t('dcim.title') }}
                </div>
            </router-link>
            <router-link v-if="hasPerm('inventory')" to="/contracts" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-file-edit mr-3"></i> {{ t('contracts.title') }}
                </div>
            </router-link>
            <router-link v-if="hasPerm('inventory')" to="/software" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-desktop mr-3"></i> {{ t('software.title') }}
                </div>
            </router-link>

            <div class="px-6 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mt-4">{{ t('nav.system') }}</div>

            <router-link v-if="hasPerm('settings') || user.role === 'admin'" to="/settings" custom v-slot="{ navigate, isActive }">
                <div @click="navigate" :class="['sidebar-link', isActive ? 'active' : '']">
                    <i class="pi pi-cog mr-3"></i> {{ t('nav.settings') }}
                </div>
            </router-link>
        </nav>
      </div>

      <div class="p-4 bg-gray-900 border-t border-gray-800">
          <div class="flex items-center justify-between">
              <div class="flex items-center gap-3 overflow-hidden">
                  <div class="w-8 h-8 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs uppercase">
                      {{ userInitials }}
                  </div>
                  <div class="text-sm overflow-hidden">
                      <div class="text-white font-medium truncate">{{ user.username }}</div>
                      <div class="text-gray-400 text-xs capitalize">{{ user.role }}</div>
                  </div>
              </div>
              <Button icon="pi pi-sign-out" text rounded class="!text-gray-400 hover:!text-white" @click="logout" v-tooltip.top="t('nav.logout')" />
          </div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col overflow-hidden relative">
      <header class="h-16 flex items-center justify-between px-8 z-10 flex-shrink-0 border-b" style="background-color: var(--bg-card); border-color: var(--border-color);">
          <h2 class="text-xl font-bold">{{ currentRouteName }}</h2>
          <div class="flex items-center gap-4">
              <div class="flex items-center gap-1 mr-2">
                  <button @click="setLang('en')" :class="['w-7 h-5 rounded overflow-hidden transition-all cursor-pointer focus:outline-none border', locale === 'en' ? 'scale-110 opacity-100 border-blue-500' : 'scale-90 opacity-50 hover:opacity-80 border-transparent']">
                      <svg viewBox="0 0 60 30" class="w-full h-full">
                          <clipPath id="s"><path d="M0,0 v30 h60 v-30 z"/></clipPath>
                          <clipPath id="t"><path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z"/></clipPath>
                          <g clip-path="url(#s)">
                              <path d="M0,0 v30 h60 v-30 z" fill="#012169"/>
                              <path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/>
                              <path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#t)" stroke="#C8102E" stroke-width="4"/>
                              <path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/>
                              <path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6"/>
                          </g>
                      </svg>
                  </button>
                  <span class="text-gray-400 text-sm">/</span>
                  <button @click="setLang('fr')" :class="['w-7 h-5 rounded overflow-hidden transition-all cursor-pointer focus:outline-none border', locale === 'fr' ? 'scale-110 opacity-100 border-blue-500' : 'scale-90 opacity-50 hover:opacity-80 border-transparent']">
                      <svg viewBox="0 0 3 2" class="w-full h-full">
                          <rect width="1" height="2" x="0" fill="#002395"/>
                          <rect width="1" height="2" x="1" fill="#fff"/>
                          <rect width="1" height="2" x="2" fill="#ED2939"/>
                      </svg>
                  </button>
              </div>
              <NotificationBell />
              <Button :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'" text rounded @click="toggleTheme" class="!text-slate-500 dark:!text-yellow-400 hover:bg-slate-100 dark:hover:bg-slate-700" />
          </div>
      </header>

      <div class="flex-1 overflow-auto p-8 custom-scrollbar">
        <router-view v-slot="{ Component }">
            <component :is="Component" />
        </router-view>
      </div>
    </main>
  </div>

  <div v-else class="h-screen w-screen bg-slate-900 flex items-center justify-center">
      <router-view />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import api from './api';
import NotificationBell from './components/shared/NotificationBell.vue';

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const user = ref({ username: '', role: '', permissions: {} });
const isDark = ref(false);

const isLoginPage = computed(() => route.path === '/login' || route.path === '/unauthorized');
const userInitials = computed(() => (user.value.username ? user.value.username.substring(0, 2).toUpperCase() : '??'));

const currentRouteName = computed(() => {
    // Map route names to translation keys
    if(route.name === 'Dashboard') return t('nav.dashboard');
    if(route.name === 'IP Address Management') return t('nav.ipam');
    if(route.name === 'Network Topology') return t('nav.topology');
    if(route.name === 'Script Automation') return t('nav.scriptRunner');
    if(route.name === 'Inventory') return t('nav.inventory');
    if(route.name === 'Settings') return t('nav.settings');
    if(route.name === 'DCIM') return t('dcim.title');
    if(route.name === 'Contracts') return t('contracts.title');
    if(route.name === 'Software') return t('software.title');
    if(route.name === 'Tickets') return t('tickets.title');
    if(route.name === 'Knowledge Base') return t('knowledge.title');
    return route.name;
});

const setLang = (lang) => {
    locale.value = lang;
    localStorage.setItem('lang', lang);
};

const toggleTheme = () => {
    isDark.value = !isDark.value;
    updateThemeClass();
};

const updateThemeClass = () => {
    if (isDark.value) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    }
};

const initTheme = () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        isDark.value = true;
    } else {
        isDark.value = false;
    }
    updateThemeClass();
};

const hasPerm = (perm) => {
    if (user.value.role === 'admin') return true;
    return user.value.permissions && user.value.permissions[perm] === true;
};

const fetchUser = async () => {
    try {
        const res = await api.get('/me');
        user.value = res.data;
        if (!user.value.permissions) user.value.permissions = {};
    } catch (e) {
        // Handled by interceptor
    }
};

const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('user');
    router.push('/login');
};

watch(() => route.path, async (newPath) => {
    if (newPath !== '/login' && !user.value.username) {
        await fetchUser();
    }
});

onMounted(async () => {
    initTheme();
    // Initialize language from localStorage
    const savedLang = localStorage.getItem('lang') || 'en';
    locale.value = savedLang;
    if (!isLoginPage.value) {
        await fetchUser();
    }
});
</script>

<style>
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: var(--border-color);
  border-radius: 99px;
}
</style>
