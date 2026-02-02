<template>
  <SlideOver
    v-model="visible"
    :title="ticket?.title || ''"
    :subtitle="ticket?.ticket_number || ''"
    icon="pi-ticket"
    size="xl"
  >
    <div v-if="loading" class="flex justify-center py-12">
      <i class="pi pi-spinner pi-spin text-3xl"></i>
    </div>

    <div v-else-if="ticket" class="space-y-6">
      <!-- Quick Stats -->
      <div class="grid grid-cols-4 gap-3">
        <div class="stat-card p-3 rounded-lg text-center">
          <div class="text-xs mb-1">{{ t('ipam.status') }}</div>
          <Tag :value="ticket.status" :severity="getStatusSeverity(ticket.status)" />
        </div>
        <div class="stat-card p-3 rounded-lg text-center">
          <div class="text-xs mb-1">{{ t('tickets.priority') }}</div>
          <Tag :value="ticket.priority" :severity="getPrioritySeverity(ticket.priority)" />
        </div>
        <div class="stat-card p-3 rounded-lg text-center">
          <div class="text-xs mb-1">{{ t('inventory.type') }}</div>
          <Tag :value="ticket.ticket_type" />
        </div>
        <div class="stat-card p-3 rounded-lg text-center">
          <div class="text-xs mb-1">{{ t('tickets.category') }}</div>
          <span class="font-medium text-sm">{{ ticket.category || '-' }}</span>
        </div>
      </div>

      <!-- SLA Status Card with Dynamic Countdown -->
      <div v-if="ticket.sla_due_date && ticket.status !== 'closed'" class="sla-card" :class="slaStatusClass">
        <div class="sla-header">
          <div class="sla-icon">
            <i :class="slaIcon"></i>
          </div>
          <div class="sla-info">
            <div class="sla-title">{{ slaTitle }}</div>
            <div class="sla-subtitle">{{ t('tickets.slaDue') }}: {{ formatDateTime(ticket.sla_due_date) }}</div>
          </div>
          <div class="sla-countdown">
            <template v-if="!ticket.sla_breached && slaTimeRemaining.total > 0">
              <span class="countdown-value">{{ slaTimeRemaining.hours }}</span>
              <span class="countdown-label">h</span>
              <span class="countdown-value">{{ slaTimeRemaining.minutes }}</span>
              <span class="countdown-label">m</span>
              <span class="countdown-value">{{ slaTimeRemaining.seconds }}</span>
              <span class="countdown-label">s</span>
            </template>
            <template v-else-if="ticket.sla_breached">
              <span class="countdown-breached">{{ t('tickets.breached') }}</span>
            </template>
          </div>
        </div>
        <div class="sla-progress">
          <div class="sla-progress-bar" :style="{ width: `${slaProgressPercent}%` }"></div>
        </div>
        <div class="sla-details">
          <span v-if="ticket.first_response_at" class="sla-detail-item sla-detail-success">
            <i class="pi pi-check-circle"></i>
            {{ t('tickets.firstResponseAt') }}: {{ formatDateTime(ticket.first_response_at) }}
          </span>
          <span v-else-if="ticket.first_response_due" class="sla-detail-item">
            <i class="pi pi-clock"></i>
            {{ t('tickets.firstResponseDue') }}: {{ formatDateTime(ticket.first_response_due) }}
          </span>
        </div>
      </div>

      <!-- Description -->
      <section class="detail-section">
        <h4 class="section-title">
          <i class="pi pi-align-left"></i>
          {{ t('tickets.description') }}
        </h4>
        <div class="section-content">
          <p class="whitespace-pre-wrap">{{ ticket.description }}</p>
        </div>
      </section>

      <!-- Ticket Info -->
      <section class="detail-section">
        <h4 class="section-title">
          <i class="pi pi-info-circle"></i>
          {{ t('common.details') }}
        </h4>
        <div class="section-content grid grid-cols-2 gap-4">
          <div>
            <div class="label">{{ t('tickets.requester') }}</div>
            <div class="value flex items-center gap-2">
              <div class="w-6 h-6 rounded-full bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center">
                <span class="text-xs font-bold text-white">{{ getInitials(ticket.requester_name) }}</span>
              </div>
              {{ ticket.requester_name || '-' }}
            </div>
          </div>
          <div>
            <div class="label">{{ t('tickets.assignedTo') }}</div>
            <div class="value flex items-center gap-2">
              <template v-if="ticket.assigned_to_name">
                <div class="w-6 h-6 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                  <span class="text-xs font-bold text-white">{{ getInitials(ticket.assigned_to_name) }}</span>
                </div>
                {{ ticket.assigned_to_name }}
              </template>
              <span v-else class="text-muted">{{ t('tickets.unassigned') }}</span>
            </div>
          </div>
          <div>
            <div class="label">{{ t('tickets.createdAt') }}</div>
            <div class="value">{{ formatDateTime(ticket.created_at) }}</div>
          </div>
          <div>
            <div class="label">{{ t('tickets.slaDue') }}</div>
            <div class="value" :class="{ 'text-danger': ticket.sla_breached }">
              {{ ticket.sla_due_date ? formatDateTime(ticket.sla_due_date) : '-' }}
            </div>
          </div>
        </div>
      </section>

      <!-- Related Equipment -->
      <section v-if="ticket.equipment_id" class="detail-section">
        <h4 class="section-title">
          <i class="pi pi-box"></i>
          {{ t('tickets.relatedEquipment') }}
        </h4>
        <div class="section-content">
          <div
            class="linked-item p-3 rounded-lg flex items-center justify-between cursor-pointer"
            @click="navigateTo('equipment', ticket.equipment_id)"
          >
            <div class="flex items-center gap-3">
              <i class="pi pi-box"></i>
              <div>
                <div class="font-medium">{{ ticket.equipment_name || `Equipment #${ticket.equipment_id}` }}</div>
              </div>
            </div>
            <i class="pi pi-chevron-right"></i>
          </div>
        </div>
      </section>

      <!-- Comments -->
      <section class="detail-section">
        <h4 class="section-title flex items-center justify-between">
          <span class="flex items-center gap-2">
            <i class="pi pi-comments"></i>
            {{ t('tickets.comments') }}
          </span>
          <span class="text-sm font-normal text-muted">{{ visibleComments.length }}</span>
        </h4>
        <div class="section-content">
          <div v-if="visibleComments.length" class="space-y-3 max-h-64 overflow-auto">
            <div
              v-for="comment in visibleComments"
              :key="comment.id"
              class="p-3 rounded-lg"
              :class="comment.is_internal ? 'bg-warning-light border-l-4 border-warning' : 'linked-item'"
            >
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center flex-shrink-0">
                  <span class="text-xs font-bold text-white">{{ getInitials(comment.username) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex justify-between items-start mb-1">
                    <span class="font-medium">{{ comment.username || 'System' }}</span>
                    <span class="text-xs text-muted">{{ formatDateTime(comment.created_at) }}</span>
                  </div>
                  <p class="text-sm whitespace-pre-wrap">{{ comment.content }}</p>
                  <Tag v-if="comment.is_internal" value="Internal" severity="warning" class="mt-2 text-xs" />
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-muted">{{ t('tickets.noComments') }}</div>
        </div>
      </section>

      <!-- Resolution (if resolved) -->
      <section v-if="ticket.resolution" class="detail-section">
        <h4 class="section-title">
          <i class="pi pi-check-circle"></i>
          {{ t('tickets.resolution') }}
        </h4>
        <div class="section-content">
          <div class="p-3 rounded-lg" style="background-color: var(--success-light); border-left: 4px solid var(--success);">
            <div class="flex items-center gap-2 mb-2">
              <Tag :value="ticket.resolution_code || 'fixed'" severity="success" />
              <span class="text-sm text-muted">{{ formatDateTime(ticket.resolved_at) }}</span>
            </div>
            <p class="whitespace-pre-wrap">{{ ticket.resolution }}</p>
          </div>
        </div>
      </section>

      <!-- History -->
      <section class="detail-section">
        <h4 class="section-title flex items-center justify-between">
          <span class="flex items-center gap-2">
            <i class="pi pi-history"></i>
            {{ t('tickets.history') }}
          </span>
          <span class="text-sm font-normal text-muted">{{ ticket.history?.length || 0 }}</span>
        </h4>
        <div class="section-content">
          <div v-if="ticket.history?.length" class="space-y-2 max-h-48 overflow-auto">
            <div v-for="item in ticket.history" :key="item.id" class="flex items-center gap-3 text-sm py-2 history-item">
              <i class="pi pi-circle-fill text-xs" style="color: var(--primary)"></i>
              <span class="text-muted text-xs">{{ formatDateTime(item.created_at) }}</span>
              <span class="font-medium">{{ item.username || 'System' }}</span>
              <span class="text-secondary">{{ formatHistoryAction(item) }}</span>
            </div>
          </div>
          <div v-else class="text-sm text-muted">{{ t('tickets.noHistory') }}</div>
        </div>
      </section>
    </div>

    <template #footer>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-2">
          <Button
            v-if="canManageTickets && ticket?.status !== 'resolved' && ticket?.status !== 'closed'"
            :label="t('tickets.resolve')"
            icon="pi pi-check"
            severity="success"
            size="small"
            @click="$emit('resolve', ticket)"
          />
          <Button
            v-if="canManageTickets && ticket?.status === 'resolved'"
            :label="t('tickets.close')"
            icon="pi pi-lock"
            size="small"
            @click="$emit('close', ticket)"
          />
        </div>
        <Button
          :label="t('common.edit')"
          icon="pi pi-pencil"
          @click="$emit('edit', ticket)"
        />
      </div>
    </template>
  </SlideOver>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../../stores/auth'
import api from '../../api'
import SlideOver from './SlideOver.vue'

const props = defineProps({
  modelValue: Boolean,
  ticketId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'edit', 'resolve', 'close'])

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

// State
const ticket = ref(null)
const loading = ref(false)

// Computed
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const canManageTickets = computed(() => {
  const role = authStore.user?.role
  if (role === 'admin' || role === 'superadmin') return true
  if (role === 'tech') {
    const perms = authStore.user?.permissions || []
    return perms.includes('tickets_admin')
  }
  return false
})

const visibleComments = computed(() => {
  if (!ticket.value?.comments) return []
  if (canManageTickets.value) return ticket.value.comments
  return ticket.value.comments.filter(c => !c.is_internal)
})

const isSlaNearBreach = computed(() => {
  if (!ticket.value?.sla_due_date || ticket.value.sla_breached) return false
  const dueDate = new Date(ticket.value.sla_due_date)
  const now = new Date()
  const hoursRemaining = (dueDate - now) / (1000 * 60 * 60)
  return hoursRemaining > 0 && hoursRemaining < 4
})

// SLA countdown timer
const currentTime = ref(new Date())
let slaTimer = null

const startSlaTimer = () => {
  if (slaTimer) clearInterval(slaTimer)
  slaTimer = setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
}

const stopSlaTimer = () => {
  if (slaTimer) {
    clearInterval(slaTimer)
    slaTimer = null
  }
}

// SLA time remaining calculation
const slaTimeRemaining = computed(() => {
  if (!ticket.value?.sla_due_date) return { total: 0, hours: 0, minutes: 0, seconds: 0 }

  const dueDate = new Date(ticket.value.sla_due_date)
  const now = currentTime.value
  const diff = dueDate - now

  if (diff <= 0) return { total: 0, hours: 0, minutes: 0, seconds: 0 }

  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  return {
    total: diff,
    hours: String(hours).padStart(2, '0'),
    minutes: String(minutes).padStart(2, '0'),
    seconds: String(seconds).padStart(2, '0')
  }
})

// SLA progress percentage (from creation to due date)
const slaProgressPercent = computed(() => {
  if (!ticket.value?.sla_due_date || !ticket.value?.created_at) return 0

  const created = new Date(ticket.value.created_at)
  const due = new Date(ticket.value.sla_due_date)
  const now = currentTime.value

  const total = due - created
  const elapsed = now - created

  if (total <= 0) return 100
  const percent = Math.min(100, Math.max(0, (elapsed / total) * 100))
  return percent
})

// SLA status class
const slaStatusClass = computed(() => {
  if (ticket.value?.sla_breached) return 'sla-breached'
  if (slaProgressPercent.value >= 90) return 'sla-critical'
  if (slaProgressPercent.value >= 75) return 'sla-warning'
  return 'sla-ok'
})

// SLA icon
const slaIcon = computed(() => {
  if (ticket.value?.sla_breached) return 'pi pi-exclamation-circle'
  if (slaProgressPercent.value >= 90) return 'pi pi-exclamation-triangle'
  if (slaProgressPercent.value >= 75) return 'pi pi-clock'
  return 'pi pi-check-circle'
})

// SLA title
const slaTitle = computed(() => {
  if (ticket.value?.sla_breached) return t('tickets.slaBreached')
  if (slaProgressPercent.value >= 90) return t('tickets.slaCritical')
  if (slaProgressPercent.value >= 75) return t('tickets.slaNearBreach')
  return t('tickets.slaOnTrack')
})

// Methods
const loadTicketDetails = async () => {
  if (!props.ticketId) return

  loading.value = true
  try {
    const response = await api.get(`/tickets/${props.ticketId}`)
    ticket.value = response.data

    // Load comments
    try {
      const commentsResponse = await api.get(`/tickets/${props.ticketId}/comments`)
      ticket.value.comments = commentsResponse.data || []
    } catch {
      ticket.value.comments = []
    }

    // Load history
    try {
      const historyResponse = await api.get(`/tickets/${props.ticketId}/history`)
      ticket.value.history = historyResponse.data || []
    } catch {
      ticket.value.history = []
    }
  } catch (error) {
    console.error('Failed to load ticket details:', error)
  } finally {
    loading.value = false
  }
}

const navigateTo = (type, id) => {
  visible.value = false
  switch (type) {
    case 'equipment':
      router.push(`/inventory?id=${id}`)
      break
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

const getInitials = (name) => {
  if (!name) return '?'
  return name.substring(0, 2).toUpperCase()
}

const formatHistoryAction = (item) => {
  if (item.action === 'created') return t('tickets.historyCreated')
  if (item.action === 'status_changed') {
    return `${t('tickets.historyStatusChanged')} ${item.old_value} → ${item.new_value}`
  }
  if (item.action === 'assigned') {
    return `${t('tickets.historyAssigned')} ${item.new_value || t('tickets.unassigned')}`
  }
  if (item.action === 'priority_changed') {
    return `${t('tickets.historyPriorityChanged')} ${item.old_value} → ${item.new_value}`
  }
  return item.action
}

// Severity helpers
const getStatusSeverity = (status) => {
  const severities = {
    new: 'info',
    open: 'warning',
    pending: 'secondary',
    resolved: 'success',
    closed: 'contrast'
  }
  return severities[status] || null
}

const getPrioritySeverity = (priority) => {
  const severities = {
    critical: 'danger',
    high: 'warning',
    medium: 'info',
    low: 'secondary'
  }
  return severities[priority] || null
}

// Watch for changes
watch(() => [props.modelValue, props.ticketId], ([isVisible, id]) => {
  if (isVisible && id) {
    loadTicketDetails()
    startSlaTimer()
  } else {
    stopSlaTimer()
  }
}, { immediate: true })

// Cleanup on unmount
import { onUnmounted } from 'vue'
onUnmounted(() => {
  stopSlaTimer()
})
</script>

<style scoped>
.detail-section {
  border-bottom: 1px solid var(--border-default);
  padding-bottom: 1.5rem;
}

.detail-section:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
  color: var(--primary);
}

.section-content .label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.section-content .value {
  font-weight: 500;
  color: var(--text-primary);
}

.section-content p {
  color: var(--text-primary);
}

.stat-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card .text-xs {
  color: var(--text-secondary);
}

.linked-item {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  transition: all 0.15s ease;
}

.linked-item:hover {
  transform: translateX(4px);
  background-color: var(--bg-hover);
  border-color: var(--primary);
}

.text-muted {
  color: var(--text-muted);
}

.text-secondary {
  color: var(--text-secondary);
}

.text-danger {
  color: var(--danger);
}

.text-warning {
  color: var(--warning);
}

.bg-danger-light {
  background-color: var(--danger-light);
}

.bg-warning-light {
  background-color: var(--warning-light);
}

.border-danger {
  border-color: var(--danger);
}

.border-warning {
  border-color: var(--warning);
}

.font-medium {
  color: var(--text-primary);
}

.linked-item .font-medium {
  color: var(--text-primary);
}

.history-item {
  border-bottom: 1px solid var(--border-default);
}

.history-item:last-child {
  border-bottom: none;
}

/* SLA Card Styles */
.sla-card {
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;
}

.sla-card.sla-ok {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(34, 197, 94, 0.05) 100%);
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.sla-card.sla-warning {
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.1) 0%, rgba(234, 179, 8, 0.05) 100%);
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.sla-card.sla-critical {
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(249, 115, 22, 0.05) 100%);
  border: 1px solid rgba(249, 115, 22, 0.3);
  animation: pulse-critical 2s ease-in-out infinite;
}

.sla-card.sla-breached {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.08) 100%);
  border: 1px solid rgba(239, 68, 68, 0.4);
}

@keyframes pulse-critical {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

.sla-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.sla-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sla-ok .sla-icon {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.sla-warning .sla-icon {
  background: rgba(234, 179, 8, 0.2);
  color: #eab308;
}

.sla-critical .sla-icon {
  background: rgba(249, 115, 22, 0.2);
  color: #f97316;
}

.sla-breached .sla-icon {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.sla-icon i {
  font-size: 18px;
}

.sla-info {
  flex: 1;
  min-width: 0;
}

.sla-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.sla-subtitle {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.sla-countdown {
  display: flex;
  align-items: baseline;
  gap: 2px;
  font-family: 'JetBrains Mono', monospace;
}

.countdown-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.countdown-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-right: 4px;
}

.countdown-breached {
  font-size: 12px;
  font-weight: 600;
  color: #ef4444;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sla-progress {
  height: 6px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 10px;
}

.sla-progress-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 1s ease;
}

.sla-ok .sla-progress-bar {
  background: linear-gradient(90deg, #22c55e, #4ade80);
}

.sla-warning .sla-progress-bar {
  background: linear-gradient(90deg, #eab308, #facc15);
}

.sla-critical .sla-progress-bar {
  background: linear-gradient(90deg, #f97316, #fb923c);
}

.sla-breached .sla-progress-bar {
  background: linear-gradient(90deg, #ef4444, #f87171);
  width: 100% !important;
}

.sla-details {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.sla-detail-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.sla-detail-item i {
  font-size: 12px;
}

.sla-detail-success {
  color: #22c55e;
}

.sla-detail-success i {
  color: #22c55e;
}
</style>
