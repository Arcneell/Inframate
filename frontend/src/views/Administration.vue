<template>
  <div class="p-6">
    <!-- Breadcrumbs -->
    <Breadcrumbs :items="breadcrumbItems" />

    <h1 class="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-6">{{ t('admin.title') }}</h1>

    <TabView v-model:activeIndex="activeTab" class="admin-tabs">
      <!-- SMTP Settings -->
      <TabPanel :header="t('admin.smtp.title')">
        <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">{{ t('admin.smtp.configuration') }}</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.smtp.host') }}</label>
              <InputText v-model="settings.smtp_host" :placeholder="t('admin.smtp.hostPlaceholder')" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.smtp.port') }}</label>
              <InputNumber v-model="settings.smtp_port" :min="1" :max="65535" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.smtp.username') }}</label>
              <InputText v-model="settings.smtp_username" :placeholder="t('admin.smtp.usernamePlaceholder')" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.smtp.password') }}</label>
              <Password v-model="settings.smtp_password" :placeholder="t('admin.smtp.passwordPlaceholder')" toggleMask :feedback="false" class="w-full" inputClass="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.smtp.fromEmail') }}</label>
              <InputText v-model="settings.smtp_from_email" :placeholder="t('admin.smtp.fromEmailPlaceholder')" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.smtp.fromName') }}</label>
              <InputText v-model="settings.smtp_from_name" placeholder="Inframate" class="w-full" />
            </div>

            <div class="flex items-center gap-2 md:col-span-2">
              <Checkbox v-model="settings.smtp_use_tls" :binary="true" inputId="smtp_tls" />
              <label for="smtp_tls" class="text-sm text-zinc-700 dark:text-zinc-300">{{ t('admin.smtp.useTls') }}</label>
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <Button :label="t('common.save')" icon="pi pi-save" @click="saveCategory('smtp')" :loading="saving" />
            <Button :label="t('admin.smtp.testConnection')" icon="pi pi-send" severity="secondary" @click="testSmtp" :loading="testing" />
          </div>
        </div>
      </TabPanel>

      <!-- General Settings -->
      <TabPanel :header="t('admin.general.title')">
        <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">{{ t('admin.general.configuration') }}</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.general.siteName') }}</label>
              <InputText v-model="settings.site_name" placeholder="Inframate" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.general.siteUrl') }}</label>
              <InputText v-model="settings.site_url" placeholder="http://localhost:3000" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.general.defaultLanguage') }}</label>
              <Dropdown v-model="settings.default_language" :options="languageOptions" optionLabel="label" optionValue="value" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.general.sessionTimeout') }}</label>
              <InputNumber v-model="settings.session_timeout_minutes" :min="5" :max="1440" suffix=" min" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.general.itemsPerPage') }}</label>
              <InputNumber v-model="settings.items_per_page" :min="10" :max="100" class="w-full" />
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <Button :label="t('common.save')" icon="pi pi-save" @click="saveCategory('general')" :loading="saving" />
          </div>
        </div>
      </TabPanel>

      <!-- Security Settings -->
      <TabPanel :header="t('admin.security.title')">
        <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">{{ t('admin.security.configuration') }}</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.security.minPasswordLength') }}</label>
              <InputNumber v-model="settings.min_password_length" :min="6" :max="32" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.security.loginRateLimit') }}</label>
              <InputNumber v-model="settings.login_rate_limit" :min="1" :max="20" suffix=" /min" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.security.sessionConcurrentLimit') }}</label>
              <InputNumber v-model="settings.session_concurrent_limit" :min="1" :max="20" class="w-full" />
            </div>

            <div class="flex items-center gap-2">
              <Checkbox v-model="settings.require_mfa_for_admins" :binary="true" inputId="require_mfa" />
              <label for="require_mfa" class="text-sm text-zinc-700 dark:text-zinc-300">{{ t('admin.security.requireMfaForAdmins') }}</label>
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <Button :label="t('common.save')" icon="pi pi-save" @click="saveCategory('security')" :loading="saving" />
          </div>
        </div>
      </TabPanel>

      <!-- Notifications Settings -->
      <TabPanel :header="t('admin.notifications.title')">
        <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">{{ t('admin.notifications.configuration') }}</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex items-center gap-2 md:col-span-2">
              <Checkbox v-model="settings.email_notifications_enabled" :binary="true" inputId="email_notif" />
              <label for="email_notif" class="text-sm text-zinc-700 dark:text-zinc-300">{{ t('admin.notifications.emailEnabled') }}</label>
            </div>

            <div class="flex items-center gap-2 md:col-span-2">
              <Checkbox v-model="settings.ticket_notification_email" :binary="true" inputId="ticket_notif" />
              <label for="ticket_notif" class="text-sm text-zinc-700 dark:text-zinc-300">{{ t('admin.notifications.ticketEmail') }}</label>
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.notifications.contractExpiryDays') }}</label>
              <InputNumber v-model="settings.contract_expiry_notification_days" :min="1" :max="90" suffix=" days" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.notifications.licenseExpiryDays') }}</label>
              <InputNumber v-model="settings.license_expiry_notification_days" :min="1" :max="90" suffix=" days" class="w-full" />
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <Button :label="t('common.save')" icon="pi pi-save" @click="saveCategory('notifications')" :loading="saving" />
          </div>
        </div>
      </TabPanel>

      <!-- Maintenance Settings -->
      <TabPanel :header="t('admin.maintenance.title')">
        <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm">
          <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">{{ t('admin.maintenance.configuration') }}</h3>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="flex items-center gap-2 md:col-span-2">
              <Checkbox v-model="settings.maintenance_mode" :binary="true" inputId="maintenance" />
              <label for="maintenance" class="text-sm text-zinc-700 dark:text-zinc-300">{{ t('admin.maintenance.enableMode') }}</label>
            </div>

            <div class="flex flex-col gap-2 md:col-span-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.maintenance.message') }}</label>
              <Textarea v-model="settings.maintenance_message" rows="3" class="w-full" />
            </div>

            <div class="flex flex-col gap-2">
              <label class="text-sm font-medium text-zinc-700 dark:text-zinc-300">{{ t('admin.maintenance.auditRetention') }}</label>
              <InputNumber v-model="settings.audit_log_retention_days" :min="7" :max="365" suffix=" days" class="w-full" />
            </div>

            <div class="flex items-center gap-2">
              <Checkbox v-model="settings.backup_enabled" :binary="true" inputId="backup" />
              <label for="backup" class="text-sm text-zinc-700 dark:text-zinc-300">{{ t('admin.maintenance.enableBackup') }}</label>
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <Button :label="t('common.save')" icon="pi pi-save" @click="saveCategory('maintenance')" :loading="saving" />
          </div>
        </div>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import api from '../api'
import Breadcrumbs from '../components/shared/Breadcrumbs.vue'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Password from 'primevue/password'
import Checkbox from 'primevue/checkbox'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'

const { t } = useI18n()
const toast = useToast()

// Breadcrumbs
const breadcrumbItems = computed(() => [
  { label: t('admin.title'), icon: 'pi-sliders-h' }
])

const activeTab = ref(0)
const saving = ref(false)
const testing = ref(false)

const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Francais', value: 'fr' }
]

const settings = reactive({
  // SMTP
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true,
  smtp_from_email: '',
  smtp_from_name: 'Inframate',
  // General
  site_name: 'Inframate',
  site_url: 'http://localhost:3000',
  default_language: 'en',
  session_timeout_minutes: 30,
  items_per_page: 25,
  // Security
  min_password_length: 8,
  require_mfa_for_admins: false,
  login_rate_limit: 5,
  session_concurrent_limit: 5,
  // Notifications
  email_notifications_enabled: false,
  ticket_notification_email: true,
  contract_expiry_notification_days: 30,
  license_expiry_notification_days: 30,
  // Maintenance
  maintenance_mode: false,
  maintenance_message: 'The system is currently under maintenance. Please try again later.',
  audit_log_retention_days: 90,
  backup_enabled: false
})

const categoryKeys = {
  smtp: ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_tls', 'smtp_from_email', 'smtp_from_name'],
  general: ['site_name', 'site_url', 'default_language', 'session_timeout_minutes', 'items_per_page'],
  security: ['min_password_length', 'require_mfa_for_admins', 'login_rate_limit', 'session_concurrent_limit'],
  notifications: ['email_notifications_enabled', 'ticket_notification_email', 'contract_expiry_notification_days', 'license_expiry_notification_days'],
  maintenance: ['maintenance_mode', 'maintenance_message', 'audit_log_retention_days', 'backup_enabled']
}

const loadSettings = async () => {
  try {
    const response = await api.get('/settings/')
    response.data.forEach(setting => {
      if (setting.key in settings) {
        // Convert value based on type
        if (setting.value_type === 'boolean') {
          settings[setting.key] = setting.value === 'true'
        } else if (setting.value_type === 'integer') {
          settings[setting.key] = parseInt(setting.value) || 0
        } else {
          settings[setting.key] = setting.value || ''
        }
      }
    })
  } catch {
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('admin.errors.loadFailed'),
      life: 3000
    })
  }
}

const saveCategory = async (category) => {
  saving.value = true
  try {
    const keys = categoryKeys[category]
    for (const key of keys) {
      let value = settings[key]
      // Convert boolean/number to string
      if (typeof value === 'boolean') {
        value = value ? 'true' : 'false'
      } else if (typeof value === 'number') {
        value = value.toString()
      }

      await api.put(`/settings/${key}`, { value })
    }

    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: t('admin.messages.saved'),
      life: 3000
    })
  } catch {
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('admin.errors.saveFailed'),
      life: 3000
    })
  } finally {
    saving.value = false
  }
}

const testSmtp = async () => {
  testing.value = true
  try {
    // First save SMTP settings
    await saveCategory('smtp')

    // Then test connection
    const response = await api.post('/settings/test-smtp')
    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: response.data.message,
      life: 5000
    })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: error.response?.data?.detail || t('admin.smtp.testFailed'),
      life: 5000
    })
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.admin-tabs :deep(.p-tabview-panels) {
  background: transparent;
  padding: 0;
}

.admin-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border: none;
}

.admin-tabs :deep(.p-tabview-nav-link) {
  background: transparent;
  border: none;
}
</style>
