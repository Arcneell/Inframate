/**
 * Notification Store (Pinia)
 * Centralized notification management for the application.
 * Replaces the window.$toast hack with a proper Pinia store.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  // State
  const toastInstance = ref(null)

  /**
   * Register the PrimeVue Toast instance.
   * Called from the App.vue component after mount.
   */
  function setToastInstance(instance) {
    toastInstance.value = instance
  }

  /**
   * Show a success notification.
   */
  function success(message, detail = null, life = 3000) {
    if (toastInstance.value) {
      toastInstance.value.add({
        severity: 'success',
        summary: message,
        detail: detail,
        life: life
      })
    } else {
      console.warn('Toast instance not available:', message, detail)
    }
  }

  /**
   * Show an error notification.
   */
  function error(message, detail = null, life = 5000) {
    if (toastInstance.value) {
      toastInstance.value.add({
        severity: 'error',
        summary: message,
        detail: detail,
        life: life
      })
    } else {
      console.error('Toast instance not available:', message, detail)
    }
  }

  /**
   * Show a warning notification.
   */
  function warning(message, detail = null, life = 4000) {
    if (toastInstance.value) {
      toastInstance.value.add({
        severity: 'warn',
        summary: message,
        detail: detail,
        life: life
      })
    } else {
      console.warn('Toast instance not available:', message, detail)
    }
  }

  /**
   * Show an info notification.
   */
  function info(message, detail = null, life = 3000) {
    if (toastInstance.value) {
      toastInstance.value.add({
        severity: 'info',
        summary: message,
        detail: detail,
        life: life
      })
    } else {
      console.info('Toast instance not available:', message, detail)
    }
  }

  /**
   * Generic notification method (for compatibility).
   */
  function add(options) {
    if (toastInstance.value) {
      toastInstance.value.add(options)
    } else {
      console.warn('Toast instance not available:', options)
    }
  }

  return {
    // Actions
    setToastInstance,
    success,
    error,
    warning,
    info,
    add
  }
})
