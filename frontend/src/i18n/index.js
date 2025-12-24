/**
 * Vue I18n Configuration
 * Single source of truth for internationalization.
 */
import { createI18n } from 'vue-i18n'
import { computed } from 'vue'
import en from './locales/en.json'
import fr from './locales/fr.json'

const messages = {
  en,
  fr
}

// Get saved language or default to English
const savedLang = localStorage.getItem('lang') || 'en'

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: savedLang,
  fallbackLocale: 'en',
  messages,
  globalInjection: true,
  silentTranslationWarn: true,
  silentFallbackWarn: true
})

/**
 * Initialize language from localStorage.
 */
export function initLang() {
  const saved = localStorage.getItem('lang')
  if (saved && (saved === 'en' || saved === 'fr')) {
    i18n.global.locale.value = saved
    document.documentElement.setAttribute('lang', saved)
  }
}

/**
 * Set the current locale.
 */
export function setLocale(locale) {
  if (locale === 'en' || locale === 'fr') {
    i18n.global.locale.value = locale
    localStorage.setItem('lang', locale)
    document.documentElement.setAttribute('lang', locale)
  }
}

/**
 * Toggle between EN and FR.
 */
export function toggleLang() {
  const newLocale = i18n.global.locale.value === 'en' ? 'fr' : 'en'
  setLocale(newLocale)
  return newLocale
}

/**
 * Get current locale.
 */
export function getLocale() {
  return i18n.global.locale.value
}

/**
 * Computed property for language icon (shows flag to switch TO).
 */
export const langIcon = computed(() => i18n.global.locale.value === 'en' ? '🇫🇷' : '🇺🇸')

export default i18n
