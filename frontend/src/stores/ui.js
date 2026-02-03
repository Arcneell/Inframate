/**
 * UI Store (Pinia) - Performance Optimized
 * Manages UI state: theme, language, sidebar, notifications, overlays, and caching.
 */
import { defineStore } from 'pinia'
import { ref, computed, shallowRef, markRaw } from 'vue'

// Cache TTL in milliseconds (30 seconds)
const CACHE_TTL = 30000

export const useUIStore = defineStore('ui', () => {
  // =============================================
  // THEME & LANGUAGE STATE
  // =============================================
  const isDark = ref(localStorage.getItem('theme') === 'dark')
  const currentLang = ref(localStorage.getItem('lang') || 'en')
  const sidebarCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')

  // =============================================
  // LOADING STATE
  // =============================================
  const globalLoading = ref(false)
  const loadingMessage = ref('')

  // =============================================
  // OVERLAY MANAGEMENT (for nested menus)
  // =============================================
  // Stack of active overlays with their close handlers
  const overlayStack = shallowRef([])

  /**
   * Register an overlay (modal/slideover) - freezes parent overlays
   */
  function registerOverlay(type, closeHandler) {
    const currentStack = [...overlayStack.value]

    // Freeze the previous overlay if exists
    if (currentStack.length > 0) {
      const lastOverlay = currentStack[currentStack.length - 1]
      if (lastOverlay.freezeCallback) {
        lastOverlay.freezeCallback()
      }
    }

    currentStack.push({
      type,
      closeHandler: markRaw(closeHandler),
      timestamp: Date.now(),
      freezeCallback: null,
      unfreezeCallback: null
    })

    overlayStack.value = currentStack
  }

  /**
   * Register freeze/unfreeze callbacks for an overlay
   */
  function setOverlayCallbacks(freezeCallback, unfreezeCallback) {
    const currentStack = [...overlayStack.value]
    if (currentStack.length > 0) {
      currentStack[currentStack.length - 1].freezeCallback = markRaw(freezeCallback)
      currentStack[currentStack.length - 1].unfreezeCallback = markRaw(unfreezeCallback)
      overlayStack.value = currentStack
    }
  }

  /**
   * Unregister an overlay - unfreezes parent overlay
   */
  function unregisterOverlay(type) {
    const currentStack = [...overlayStack.value]
    const index = currentStack.findLastIndex(o => o.type === type)

    if (index > -1) {
      currentStack.splice(index, 1)
      overlayStack.value = currentStack

      // Unfreeze the new top overlay if exists
      if (currentStack.length > 0) {
        const lastOverlay = currentStack[currentStack.length - 1]
        if (lastOverlay.unfreezeCallback) {
          lastOverlay.unfreezeCallback()
        }
      }
    }
  }

  /**
   * Close all overlays
   */
  function closeAllOverlays() {
    const stack = [...overlayStack.value].reverse()
    for (const overlay of stack) {
      if (overlay.closeHandler) {
        overlay.closeHandler()
      }
    }
    overlayStack.value = []
  }

  /**
   * Check if any overlay is open
   */
  const hasActiveOverlay = computed(() => overlayStack.value.length > 0)

  /**
   * Get the count of active overlays
   */
  const overlayCount = computed(() => overlayStack.value.length)

  // =============================================
  // DATA CACHING SYSTEM
  // =============================================
  // Cache storage using shallowRef for performance
  const dataCache = shallowRef(new Map())

  /**
   * Get cached data if not expired
   * @param {string} key - Cache key
   * @returns {any|null} - Cached data or null if expired/not found
   */
  function getCachedData(key) {
    const cache = dataCache.value
    const entry = cache.get(key)

    if (!entry) return null

    const now = Date.now()
    if (now - entry.timestamp > CACHE_TTL) {
      // Expired - remove from cache
      const newCache = new Map(cache)
      newCache.delete(key)
      dataCache.value = newCache
      return null
    }

    return entry.data
  }

  /**
   * Set data in cache
   * @param {string} key - Cache key
   * @param {any} data - Data to cache
   * @param {number} ttl - Optional custom TTL in ms
   */
  function setCachedData(key, data, ttl = CACHE_TTL) {
    const newCache = new Map(dataCache.value)
    newCache.set(key, {
      data: markRaw(data),
      timestamp: Date.now(),
      ttl
    })
    dataCache.value = newCache
  }

  /**
   * Invalidate a specific cache entry
   */
  function invalidateCache(key) {
    const newCache = new Map(dataCache.value)
    newCache.delete(key)
    dataCache.value = newCache
  }

  /**
   * Invalidate all cache entries matching a prefix
   */
  function invalidateCachePrefix(prefix) {
    const newCache = new Map()
    for (const [key, value] of dataCache.value) {
      if (!key.startsWith(prefix)) {
        newCache.set(key, value)
      }
    }
    dataCache.value = newCache
  }

  /**
   * Clear all cache
   */
  function clearCache() {
    dataCache.value = new Map()
  }

  // =============================================
  // THEME FUNCTIONS
  // =============================================
  const themeClass = computed(() => isDark.value ? 'dark' : 'light')
  const langIcon = computed(() => currentLang.value === 'en' ? '🇫🇷' : '🇺🇸')

  function toggleTheme() {
    isDark.value = !isDark.value
    updateThemeClass()
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  function setTheme(dark) {
    isDark.value = dark
    updateThemeClass()
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }

  function updateThemeClass() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // =============================================
  // LANGUAGE FUNCTIONS
  // =============================================
  function toggleLang() {
    currentLang.value = currentLang.value === 'en' ? 'fr' : 'en'
    localStorage.setItem('lang', currentLang.value)
  }

  function setLang(lang) {
    if (lang === 'en' || lang === 'fr') {
      currentLang.value = lang
      localStorage.setItem('lang', lang)
    }
  }

  // =============================================
  // SIDEBAR FUNCTIONS
  // =============================================
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value)
  }

  // =============================================
  // LOADING FUNCTIONS
  // =============================================
  function setLoading(loading, message = '') {
    globalLoading.value = loading
    loadingMessage.value = message
  }

  // =============================================
  // INITIALIZATION
  // =============================================
  function init() {
    // Theme - default to light for new users
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'dark') {
      isDark.value = true
    } else {
      isDark.value = false
    }
    updateThemeClass()

    // Language
    const savedLang = localStorage.getItem('lang')
    if (savedLang) {
      currentLang.value = savedLang
    }

    // Sidebar
    const savedSidebar = localStorage.getItem('sidebarCollapsed')
    if (savedSidebar) {
      sidebarCollapsed.value = savedSidebar === 'true'
    }
  }

  // Watch for system theme changes
  if (typeof window !== 'undefined') {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        isDark.value = e.matches
        updateThemeClass()
      }
    })

    // Handle Escape key to close top overlay
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && overlayStack.value.length > 0) {
        const topOverlay = overlayStack.value[overlayStack.value.length - 1]
        if (topOverlay.closeHandler) {
          topOverlay.closeHandler()
        }
      }
    })
  }

  return {
    // State
    isDark,
    currentLang,
    sidebarCollapsed,
    globalLoading,
    loadingMessage,

    // Computed
    themeClass,
    langIcon,
    hasActiveOverlay,
    overlayCount,

    // Theme Actions
    toggleTheme,
    setTheme,

    // Language Actions
    toggleLang,
    setLang,

    // Sidebar Actions
    toggleSidebar,

    // Loading Actions
    setLoading,

    // Overlay Management
    registerOverlay,
    unregisterOverlay,
    setOverlayCallbacks,
    closeAllOverlays,

    // Caching
    getCachedData,
    setCachedData,
    invalidateCache,
    invalidateCachePrefix,
    clearCache,

    // Init
    init
  }
})
