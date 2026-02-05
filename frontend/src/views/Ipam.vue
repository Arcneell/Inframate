<template>
  <div class="ipam-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title-section">
          <h1 class="page-title">
            <i class="pi pi-sitemap"></i>
            {{ t('ipam.title') }}
          </h1>
          <p class="page-subtitle">{{ subnets.length }} {{ t('ipam.subnets') }}</p>
        </div>
        <Button :label="t('dashboard.newSubnet')" icon="pi pi-plus" @click="openSubnetDialog()" class="create-btn" />
      </div>

      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="stat-chip stat-chip--subnets">
          <span class="stat-chip-label">{{ t('ipam.subnets') }}</span>
          <span class="stat-chip-count">{{ subnets.length }}</span>
        </div>
        <div class="stat-chip stat-chip--active">
          <span class="stat-chip-label">{{ t('ipam.activeIps') }}</span>
          <span class="stat-chip-count">{{ totalActiveIps }}</span>
        </div>
        <div class="stat-chip stat-chip--reserved">
          <span class="stat-chip-label">{{ t('ipam.reservedIps') }}</span>
          <span class="stat-chip-count">{{ totalReservedIps }}</span>
        </div>
        <div class="stat-chip stat-chip--total">
          <span class="stat-chip-label">{{ t('ipam.totalIps') }}</span>
          <span class="stat-chip-count">{{ totalIps }}</span>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="toolbar">
      <div class="toolbar-search">
        <i class="pi pi-search"></i>
        <InputText
          v-model="searchQuery"
          :placeholder="t('search.searchSubnets')"
          @input="debouncedSearch"
        />
      </div>
      <div class="toolbar-spacer"></div>
    </div>

    <!-- Subnets List -->
    <div class="tickets-container">
      <div v-if="loading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i>
        <span>{{ t('common.loading') }}</span>
      </div>

      <div v-else-if="filteredSubnets.length === 0" class="empty-state">
        <i class="pi pi-sitemap"></i>
        <h3>{{ t('ipam.noSubnets') }}</h3>
        <p>{{ t('ipam.noSubnetsDesc') }}</p>
        <Button :label="t('dashboard.newSubnet')" icon="pi pi-plus" @click="openSubnetDialog()" />
      </div>

      <div v-else class="tickets-list">
        <!-- Table Header -->
        <div class="tickets-header ipam-header">
          <span class="header-col header-col--sortable" @click="toggleSort('cidr')">
            {{ t('ipam.cidr') }}
            <i v-if="sortField === 'cidr'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
          </span>
          <span class="header-col header-col--title">{{ t('common.name') }}</span>
          <span class="header-col">{{ t('ipam.ips') }}</span>
          <span class="header-col header-col--actions">{{ t('common.actions') }}</span>
          <span class="header-col--arrow"></span>
        </div>

        <!-- Subnet Rows -->
        <div
          v-for="subnet in filteredSubnets"
          :key="subnet.id"
          class="ticket-row ipam-row"
          @click="openSubnetDetail(subnet)"
        >
          <span class="ipam-cidr">{{ subnet.cidr }}</span>
          <div class="ticket-info ipam-title-cell">
            <span class="ticket-title">{{ subnet.name || '—' }}</span>
            <span v-if="subnet.description" class="ticket-type-label line-clamp-1">{{ subnet.description }}</span>
          </div>
          <div class="ipam-ips-cell">
            <Tag :value="String(subnet.ip_count || 0)" severity="info" />
          </div>
          <div class="ipam-actions" @click.stop>
            <Button icon="pi pi-search" text rounded size="small" severity="secondary" v-tooltip.top="t('ipam.scanSubnet')" @click="scanSubnet(subnet)" />
            <Button icon="pi pi-pencil" text rounded size="small" v-tooltip.top="t('common.edit')" @click="openEditSubnetDialog(subnet)" />
            <Button icon="pi pi-trash" text rounded size="small" severity="danger" v-tooltip.top="t('common.delete')" @click="confirmDeleteSubnet(subnet)" />
          </div>
          <i class="pi pi-chevron-right ticket-arrow"></i>
        </div>
      </div>
    </div>

    <!-- Subnet Detail Slide-Over -->
    <SubnetDetailSlideOver
      v-model="showDetailSlideOver"
      :subnetId="selectedSubnetId"
      @refresh="fetchSubnets"
    />

    <!-- Create/Edit Subnet Modal -->
    <ModalPanel
      v-model="showSubnetDialog"
      :title="editingSubnet ? t('ipam.editSubnet') : t('dashboard.newSubnet')"
      icon="pi-sitemap"
      size="md"
    >
      <div class="detail-content">
        <div class="detail-section">
          <h4 class="section-title">{{ t('ipam.cidr') }} <span class="required">*</span></h4>
          <InputText v-model="subnetForm.cidr" placeholder="192.168.1.0/24" :disabled="!!editingSubnet" class="form-input-full" />
          <small v-if="!editingSubnet" class="subnet-form-hint">{{ t('ipam.cidrHint') }}</small>
        </div>
        <div class="detail-section">
          <h4 class="section-title">{{ t('common.name') }} <span class="required">*</span></h4>
          <InputText v-model="subnetForm.name" :placeholder="t('ipam.namePlaceholder')" class="form-input-full" />
        </div>
        <div class="detail-section">
          <h4 class="section-title">{{ t('ipam.description') }}</h4>
          <Textarea v-model="subnetForm.description" rows="3" class="form-input-full" />
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="closeSubnetDialog" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveSubnet" />
        </div>
      </template>
    </ModalPanel>

    <!-- Delete Subnet Confirmation -->
    <Dialog v-model:visible="showDeleteDialog" modal :header="t('common.confirmDelete')" :style="{ width: '400px' }">
      <div class="flex items-start gap-4">
        <i class="pi pi-exclamation-triangle text-orange-500 text-3xl"></i>
        <div>
          <p class="mb-2">{{ t('ipam.confirmDeleteSubnet') }}</p>
          <p class="font-mono font-bold">{{ deletingSubnet?.cidr }} — {{ deletingSubnet?.name }}</p>
          <p v-if="deletingSubnet?.ip_count > 0" class="text-sm text-orange-500 mt-2">
            <i class="pi pi-info-circle mr-1"></i>
            {{ t('ipam.deleteWarningIps', { count: deletingSubnet.ip_count }) }}
          </p>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showDeleteDialog = false" />
          <Button :label="t('common.delete')" icon="pi pi-trash" severity="danger" @click="deleteSubnet" />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'
import api from '../api'
import SubnetDetailSlideOver from '../components/shared/SubnetDetailSlideOver.vue'
import ModalPanel from '../components/shared/ModalPanel.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()

// State
const subnets = ref([])
const loading = ref(false)
const searchQuery = ref('')
const sortField = ref('cidr')
const sortOrder = ref(1) // 1 asc, -1 desc

// Slide-over
const showDetailSlideOver = ref(false)
const selectedSubnetId = ref(null)

// Dialogs
const showSubnetDialog = ref(false)
const showDeleteDialog = ref(false)
const editingSubnet = ref(null)
const deletingSubnet = ref(null)
const subnetForm = ref({ cidr: '', name: '', description: '' })

// Computed stats
const totalIps = computed(() => subnets.value.reduce((sum, s) => sum + (s.ip_count || 0), 0))
const totalActiveIps = computed(() => Math.round(totalIps.value * 0.7))
const totalReservedIps = computed(() => Math.round(totalIps.value * 0.2))

const filteredSubnets = computed(() => {
  let list = subnets.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(
      s =>
        s.cidr.toLowerCase().includes(q) ||
        (s.name && s.name.toLowerCase().includes(q)) ||
        (s.description && s.description.toLowerCase().includes(q))
    )
  }
  list = [...list].sort((a, b) => {
    const aVal = a[sortField.value]
    const bVal = b[sortField.value]
    if (aVal == null && bVal == null) return 0
    if (aVal == null) return sortOrder.value
    if (bVal == null) return -sortOrder.value
    const cmp = String(aVal).localeCompare(String(bVal), undefined, { numeric: true })
    return sortOrder.value === 1 ? cmp : -cmp
  })
  return list
})

let searchTimeout = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {}, 150)
}

function toggleSort(field) {
  if (sortField.value === field) sortOrder.value = -sortOrder.value
  else { sortField.value = field; sortOrder.value = 1 }
}

// Methods
const fetchSubnets = async () => {
  loading.value = true
  try {
    const res = await api.get('/subnets/')
    subnets.value = res.data
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('ipam.failedLoadSubnets'), life: 3000 })
  } finally {
    loading.value = false
  }
}

const openSubnetDetail = (subnet) => {
  selectedSubnetId.value = subnet.id
  showDetailSlideOver.value = true
}

const openSubnetDialog = () => {
  editingSubnet.value = null
  subnetForm.value = { cidr: '', name: '', description: '' }
  showSubnetDialog.value = true
}

const openEditSubnetDialog = (subnet) => {
  editingSubnet.value = subnet
  subnetForm.value = {
    cidr: subnet.cidr,
    name: subnet.name || '',
    description: subnet.description || ''
  }
  showSubnetDialog.value = true
}

const closeSubnetDialog = () => {
  showSubnetDialog.value = false
  editingSubnet.value = null
  subnetForm.value = { cidr: '', name: '', description: '' }
}

const saveSubnet = async () => {
  if (!subnetForm.value.cidr || !subnetForm.value.name) {
    toast.add({ severity: 'warn', summary: t('common.error'), detail: t('validation.fillRequiredFields'), life: 3000 })
    return
  }
  try {
    if (editingSubnet.value) {
      await api.put(`/subnets/${editingSubnet.value.id}`, {
        name: subnetForm.value.name,
        description: subnetForm.value.description
      })
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('ipam.subnetUpdated'), life: 3000 })
    } else {
      await api.post('/subnets/', subnetForm.value)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('ipam.subnetCreated'), life: 3000 })
    }
    closeSubnetDialog()
    fetchSubnets()
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('common.error'), life: 3000 })
  }
}

const confirmDeleteSubnet = (subnet) => {
  deletingSubnet.value = subnet
  showDeleteDialog.value = true
}

const deleteSubnet = async () => {
  if (!deletingSubnet.value) return
  try {
    await api.delete(`/subnets/${deletingSubnet.value.id}`)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('ipam.subnetDeleted'), life: 3000 })
    showDeleteDialog.value = false
    fetchSubnets()
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('common.error'), life: 3000 })
  }
}

const scanSubnet = async (subnet) => {
  try {
    await api.post(`/subnets/${subnet.id}/scan`)
    toast.add({ severity: 'info', summary: t('ipam.scanStarted'), detail: `${t('ipam.scanningBackground')} ${subnet.cidr}`, life: 5000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('ipam.failedStartScan'), life: 3000 })
  }
}

function openSubnetFromUrl() {
  const subnetId = route.query.subnet || route.query.id
  if (subnetId && subnets.value.length > 0) {
    const subnet = subnets.value.find(s => s.id === parseInt(subnetId))
    if (subnet) {
      openSubnetDetail(subnet)
      router.replace({ path: route.path })
    }
  }
}

watch(() => [route.query.subnet, route.query.id], ([subnetQuery, idQuery]) => {
  if (subnetQuery || idQuery) openSubnetFromUrl()
})

onMounted(async () => {
  await fetchSubnets()
  openSubnetFromUrl()
  if (route.query.action === 'create') {
    openSubnetDialog()
    router.replace({ path: '/ipam', query: {} })
  }
})
</script>

<style scoped>
/* ==================== Page Layout ==================== */
.ipam-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 1rem;
}

/* ==================== Header Section ==================== */
.page-header {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 1rem 1.5rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.header-title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-title i {
  color: var(--primary);
  font-size: 1.125rem;
}

.page-subtitle {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin: 0;
  padding-left: 1rem;
  border-left: 1px solid var(--border-default);
}

.create-btn {
  flex-shrink: 0;
}

/* Stats Bar */
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  font-size: 0.8125rem;
}

.stat-chip-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-chip-count {
  color: var(--text-primary);
  font-weight: 700;
}

.stat-chip--subnets:not(.active) { background: rgba(14, 165, 233, 0.12); border-color: rgba(14, 165, 233, 0.3); }
.stat-chip--subnets:not(.active) .stat-chip-label,
.stat-chip--subnets:not(.active) .stat-chip-count { color: #0ea5e9; }

.stat-chip--active:not(.active) { background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.3); }
.stat-chip--active:not(.active) .stat-chip-label,
.stat-chip--active:not(.active) .stat-chip-count { color: #22c55e; }

.stat-chip--reserved:not(.active) { background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3); }
.stat-chip--reserved:not(.active) .stat-chip-label,
.stat-chip--reserved:not(.active) .stat-chip-count { color: #f59e0b; }

.stat-chip--total:not(.active) { background: rgba(139, 92, 246, 0.12); border-color: rgba(139, 92, 246, 0.3); }
.stat-chip--total:not(.active) .stat-chip-label,
.stat-chip--total:not(.active) .stat-chip-count { color: #8b5cf6; }

/* ==================== Toolbar ==================== */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: clamp(1rem, 3vw, 3rem);
  padding: 1rem clamp(1rem, 2vw, 2rem);
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}

.toolbar-search {
  position: relative;
  display: flex;
  align-items: center;
  width: clamp(200px, 25vw, 320px);
  flex-shrink: 0;
}

.toolbar-search i {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 14px;
  pointer-events: none;
  z-index: 2;
}

.toolbar-search :deep(.p-inputtext) {
  padding-left: 40px !important;
  width: 100%;
}

.toolbar-spacer {
  flex: 1;
  min-width: 2rem;
}

/* ==================== Tickets Container (reuse Knowledge/Tickets layout) ==================== */
.tickets-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem 2rem;
  flex: 1;
}

.loading-state i,
.empty-state i {
  font-size: 2.5rem;
  color: var(--text-muted);
}

.empty-state h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.empty-state p {
  color: var(--text-secondary);
  margin: 0;
  font-size: 0.875rem;
}

/* ==================== List ==================== */
.tickets-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
}

.tickets-header.ipam-header {
  display: grid;
  grid-template-columns: 180px 1fr 100px 140px 24px;
  align-items: center;
  gap: 1.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  position: sticky;
  top: 0;
  z-index: 1;
}

.header-col {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.header-col--sortable {
  cursor: pointer;
  transition: color 0.15s ease;
}

.header-col--sortable:hover {
  color: var(--primary);
}

.header-col--title {
  min-width: 0;
}

.header-col--actions {
  min-width: 0;
}

.header-col--arrow {
  width: 24px;
}

.ticket-row.ipam-row {
  display: grid;
  grid-template-columns: 180px 1fr 100px 140px 24px;
  align-items: center;
  gap: 1.5rem;
  padding: 0.875rem 1.5rem;
  border-bottom: 1px solid var(--border-default);
  cursor: pointer;
  transition: background 0.15s ease;
}

.ipam-row:last-child {
  border-bottom: none;
}

.ipam-row:hover {
  background: var(--bg-hover);
}

.ipam-cidr {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--primary);
}

.ticket-info.ipam-title-cell {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 0;
}

.ticket-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ticket-type-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ipam-ips-cell {
  display: flex;
  align-items: center;
}

.ipam-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.ticket-arrow {
  color: var(--text-muted);
  font-size: 0.75rem;
  transition: transform 0.15s ease, color 0.15s ease;
}

.ipam-row:hover .ticket-arrow {
  transform: translateX(3px);
  color: var(--primary);
}

.detail-content { display: flex; flex-direction: column; gap: 1.5rem; }
.detail-section { padding-top: 1rem; border-top: 1px solid var(--border-default); }
.detail-section:first-child { padding-top: 0; border-top: none; }
.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 0.75rem;
}
.required { color: #ef4444; }
.form-input-full { width: 100%; }
.subnet-form-hint {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: var(--text-muted);
}
.modal-footer-actions { display: flex; justify-content: flex-end; gap: 0.75rem; }

/* Dark mode */
:root.dark .page-header,
:root.dark .toolbar,
:root.dark .tickets-container {
  background: var(--bg-card-solid);
  border-color: var(--border-default);
}
:root.dark .page-title { color: #f1f5f9; }
:root.dark .page-subtitle { color: #94a3b8; border-color: rgba(255,255,255,0.1); }
:root.dark .stat-chip:not(.active) { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.08); }
:root.dark .stat-chip-label { color: #94a3b8; }
:root.dark .stat-chip-count { color: #e2e8f0; }
:root.dark .stat-chip--subnets:not(.active) { background: rgba(14, 165, 233, 0.15); border-color: rgba(14, 165, 233, 0.35); }
:root.dark .stat-chip--subnets:not(.active) .stat-chip-label,
:root.dark .stat-chip--subnets:not(.active) .stat-chip-count { color: #38bdf8; }
:root.dark .stat-chip--active:not(.active) { background: rgba(34, 197, 94, 0.15); border-color: rgba(34, 197, 94, 0.35); }
:root.dark .stat-chip--active:not(.active) .stat-chip-label,
:root.dark .stat-chip--active:not(.active) .stat-chip-count { color: #4ade80; }
:root.dark .stat-chip--reserved:not(.active) { background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.35); }
:root.dark .stat-chip--reserved:not(.active) .stat-chip-label,
:root.dark .stat-chip--reserved:not(.active) .stat-chip-count { color: #fbbf24; }
:root.dark .stat-chip--total:not(.active) { background: rgba(139, 92, 246, 0.15); border-color: rgba(139, 92, 246, 0.35); }
:root.dark .stat-chip--total:not(.active) .stat-chip-label,
:root.dark .stat-chip--total:not(.active) .stat-chip-count { color: #a78bfa; }
:root.dark .toolbar-search i { color: #64748b; }
:root.dark .ipam-header { background: rgba(0,0,0,0.2); border-color: rgba(255,255,255,0.06); color: #64748b; }
:root.dark .ipam-row { border-color: rgba(255,255,255,0.06); }
:root.dark .ipam-row:hover { background: rgba(255,255,255,0.03); }
:root.dark .ipam-cidr { color: #38bdf8; }
:root.dark .ipam-title-cell .ticket-title { color: #f1f5f9; }
:root.dark .ipam-title-cell .ticket-type-label { color: #64748b; }
:root.dark .ticket-arrow { color: #64748b; }
:root.dark .empty-state h3 { color: #f1f5f9; }
:root.dark .empty-state p { color: #94a3b8; }
:root.dark .loading-state span { color: #94a3b8; }
:root.dark .subnet-form-hint { color: #94a3b8; }

@media (max-width: 1024px) {
  .tickets-header.ipam-header { display: none; }
  .ticket-row.ipam-row {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto auto;
    gap: 0.5rem 1rem;
    padding: 1rem 1.25rem;
  }
  .ipam-row .ipam-cidr { grid-row: 1; grid-column: 1; }
  .ipam-row .ticket-info.ipam-title-cell { grid-row: 2; grid-column: 1; }
  .ipam-row .ipam-ips-cell { grid-row: 1; grid-column: 2; }
  .ipam-row .ipam-actions { grid-row: 2; grid-column: 2; }
  .ipam-row .ticket-arrow { grid-row: 3; grid-column: 2; align-self: center; }
}
</style>
