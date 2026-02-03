/**
 * Vue 3 Application Entry Point
 * Performance Optimized
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import i18n, { initLang } from './i18n/index.js'
// style.css en non-bloquant : si 468 (proxy/WAF) ou autre échec, l'app reste utilisable
import('./style.css').catch(() => {})

// PrimeVue
import PrimeVue from 'primevue/config'
import 'primevue/resources/themes/lara-dark-teal/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'

// PrimeVue Components
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import Card from 'primevue/card'
import Textarea from 'primevue/textarea'
import FileUpload from 'primevue/fileupload'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import Calendar from 'primevue/calendar'
import Checkbox from 'primevue/checkbox'
import Password from 'primevue/password'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import ContextMenu from 'primevue/contextmenu'
import Paginator from 'primevue/paginator'

// Create Vue app
const app = createApp(App)

// Create Pinia store
const pinia = createPinia()

// Use plugins
app.use(pinia)
app.use(router)
app.use(i18n)
app.use(PrimeVue, { ripple: false }) // Disable ripple for performance
app.use(ToastService)

// Initialize theme before mount (prevents flash and ensures consistent state)
const initTheme = () => {
  const savedTheme = localStorage.getItem('theme')
  // Default to light theme for new users
  if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}
initTheme()

// =============================================
// PERFORMANCE DIRECTIVES
// =============================================

/**
 * v-lazy-src: Lazy load images using IntersectionObserver
 * Usage: <img v-lazy-src="imageUrl" />
 */
app.directive('lazy-src', {
  mounted(el, binding) {
    const loadImage = () => {
      el.src = binding.value
      el.classList.add('lazy-loaded')
    }

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            loadImage()
            observer.unobserve(el)
          }
        })
      }, { rootMargin: '50px' })

      observer.observe(el)
      el._lazyObserver = observer
    } else {
      loadImage()
    }
  },
  unmounted(el) {
    if (el._lazyObserver) {
      el._lazyObserver.disconnect()
    }
  }
})

/**
 * v-click-outside: Detect clicks outside element
 * Usage: <div v-click-outside="handleOutsideClick">
 */
app.directive('click-outside', {
  mounted(el, binding) {
    el._clickOutsideHandler = (event) => {
      if (!(el === event.target || el.contains(event.target))) {
        binding.value(event)
      }
    }
    document.addEventListener('click', el._clickOutsideHandler, { passive: true })
  },
  unmounted(el) {
    document.removeEventListener('click', el._clickOutsideHandler)
  }
})

/**
 * v-debounce-input: Debounce input events
 * Usage: <input v-debounce-input:300="handleInput" />
 */
app.directive('debounce-input', {
  mounted(el, binding) {
    const delay = parseInt(binding.arg) || 300
    let timeout = null

    el._debounceHandler = (event) => {
      clearTimeout(timeout)
      timeout = setTimeout(() => {
        binding.value(event.target.value)
      }, delay)
    }

    el.addEventListener('input', el._debounceHandler, { passive: true })
  },
  unmounted(el) {
    el.removeEventListener('input', el._debounceHandler)
  }
})

/**
 * v-focus-trap: Trap focus within element (for modals/overlays)
 * Usage: <div v-focus-trap>
 */
app.directive('focus-trap', {
  mounted(el) {
    const focusableSelectors = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

    el._trapFocus = (event) => {
      if (event.key !== 'Tab') return

      const focusableElements = el.querySelectorAll(focusableSelectors)
      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]

      if (event.shiftKey && document.activeElement === firstElement) {
        lastElement?.focus()
        event.preventDefault()
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        firstElement?.focus()
        event.preventDefault()
      }
    }

    el.addEventListener('keydown', el._trapFocus)

    // Focus first element on mount
    requestAnimationFrame(() => {
      const firstFocusable = el.querySelector(focusableSelectors)
      firstFocusable?.focus()
    })
  },
  unmounted(el) {
    el.removeEventListener('keydown', el._trapFocus)
  }
})

/**
 * v-scroll-lock: Lock body scroll when element is visible
 * Usage: <div v-scroll-lock="isOpen">
 */
app.directive('scroll-lock', {
  updated(el, binding) {
    if (binding.value) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  },
  unmounted() {
    document.body.style.overflow = ''
  }
})

// Register PrimeVue directive
app.directive('tooltip', Tooltip)

// Register global components
app.component('Button', Button)
app.component('InputText', InputText)
app.component('InputNumber', InputNumber)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Dialog', Dialog)
app.component('Dropdown', Dropdown)
app.component('Card', Card)
app.component('Textarea', Textarea)
app.component('FileUpload', FileUpload)
app.component('Tag', Tag)
app.component('Toast', Toast)
app.component('Calendar', Calendar)
app.component('Checkbox', Checkbox)
app.component('Password', Password)
app.component('TabView', TabView)
app.component('TabPanel', TabPanel)
app.component('ProgressBar', ProgressBar)
app.component('Skeleton', Skeleton)
app.component('ContextMenu', ContextMenu)
app.component('Paginator', Paginator)

// Initialize language
initLang()

// =============================================
// PERFORMANCE OPTIMIZATIONS
// =============================================

// Disable Vue devtools in production for performance
if (import.meta.env.PROD) {
  app.config.performance = false
  app.config.devtools = false
}

// Global error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', instance)
  console.error('Info:', info)
}

// Mount app
app.mount('#app')
