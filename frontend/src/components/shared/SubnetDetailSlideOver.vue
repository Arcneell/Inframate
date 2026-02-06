<template>
  <SlideOver
    v-model="visible"
    :title="subnet?.cidr || ''"
    :subtitle="subnet?.name || ''"
    icon="pi-sitemap"
    size="full"
  >
    <div v-if="loading" class="flex justify-center py-12">
      <i class="pi pi-spinner pi-spin text-3xl"></i>
    </div>

    <div v-else-if="subnet" class="space-y-6">
      <!-- Quick Stats (thème global = stat-card p-3 rounded-lg) -->
      <div class="grid grid-cols-3 gap-3">
        <div class="stat-card p-3 rounded-lg text-center">
          <div class="text-xs mb-1">{{ t('ipam.totalIps') }}</div>
          <div class="stat-value stat-value--total">{{ ipData.total }}</div>
        </div>
        <div class="stat-card p-3 rounded-lg text-center">
          <div class="text-xs mb-1">{{ t('ipam.activeIps') }}</div>
          <div class="stat-value stat-value--active">{{ activeCount }}</div>
        </div>
        <div class="stat-card p-3 rounded-lg text-center">
          <div class="text-xs mb-1">{{ t('ipam.reservedIps') }}</div>
          <div class="stat-value stat-value--reserved">{{ reservedCount }}</div>
        </div>
      </div>

      <!-- Détails sous-réseau (même structure que Ticket) -->
      <section class="detail-section">
        <h4 class="section-title">
          <i class="pi pi-info-circle"></i>
          {{ t('common.details') }}
        </h4>
        <div class="section-content grid grid-cols-2 gap-4">
          <div>
            <div class="label">{{ t('ipam.cidr') }}</div>
            <div class="value font-mono">{{ subnet.cidr }}</div>
          </div>
          <div>
            <div class="label">{{ t('common.name') }}</div>
            <div class="value">{{ subnet.name || '—' }}</div>
          </div>
          <div v-if="subnet.description" class="col-span-2">
            <div class="label">{{ t('ipam.description') }}</div>
            <div class="value whitespace-pre-wrap">{{ subnet.description }}</div>
          </div>
        </div>
      </section>

      <!-- Adresses IP -->
      <section class="detail-section">
        <h4 class="section-title flex items-center justify-between flex-wrap gap-2">
          <span class="flex items-center gap-2">
            <i class="pi pi-list"></i>
            {{ t('ipam.allocatedIps') }}
          </span>
          <span class="text-sm font-normal text-secondary">{{ ipData.total }} {{ t('ipam.addressesFound') }}</span>
          <Button icon="pi pi-plus" size="small" class="add-ip-btn" @click="showAddIpDialog = true" v-tooltip.left="t('ipam.addIp')" />
        </h4>
        <div class="section-content">
          <div class="flex gap-2 mb-4 ipam-toolbar-filters flex-wrap">
            <Dropdown
              v-model="statusFilter"
              :options="statusFilterOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('filters.allStatuses')"
              showClear
              class="info-dropdown w-40"
            />
            <InputText v-model="searchQuery" :placeholder="t('search.searchIps')" class="flex-1 min-w-[150px]" />
          </div>

          <div class="bulk-bar flex items-center gap-3 mb-4 p-3 rounded-lg">
            <Checkbox :modelValue="isAllOnPageSelected" @update:modelValue="toggleSelectAllOnPage" :binary="true" class="select-all-checkbox" />
            <span class="bulk-bar-selection-text">
              <template v-if="selectedIps.length > 0">{{ selectedIps.length }} {{ t('common.selected') }}</template>
              <template v-else>{{ t('common.selectAll') }}</template>
            </span>
            <div class="flex-1"></div>
            <template v-if="selectedIps.length > 0">
              <Button :label="t('bulk.openBulkActions')" icon="pi pi-list-check" size="small" @click="showBulkDialog = true" />
              <Button icon="pi pi-times" text rounded size="small" @click="selectedIps = []" v-tooltip.top="t('common.clearSelection')" />
            </template>
          </div>

          <div v-if="loadingIps" class="flex justify-center py-8">
            <i class="pi pi-spinner pi-spin text-2xl opacity-50"></i>
          </div>

          <div v-else-if="ipData.items.length" class="space-y-2">
            <div
              v-for="ip in filteredIps"
              :key="ip.id"
              class="ip-item p-3 rounded-lg flex items-center justify-between gap-4 flex-wrap"
              :class="{ 'ip-item--selected': isIpSelected(ip) }"
            >
              <div class="flex items-center gap-4 flex-1 min-w-0">
                <Checkbox :modelValue="isIpSelected(ip)" @update:modelValue="toggleIpSelection(ip)" :binary="true" @click.stop />
                <span class="font-mono text-sm font-medium shrink-0">{{ ip.address }}</span>
                <span v-if="ip.hostname" class="text-sm text-secondary truncate">{{ ip.hostname }}</span>
                <span v-if="ip.equipment" class="flex items-center gap-2 text-sm">
                  <i class="pi pi-box text-primary"></i>
                  <span class="font-medium text-primary hover:underline cursor-pointer" @click.stop="navigateToEquipment(ip.equipment)">{{ ip.equipment.name }}</span>
                </span>
                <span v-else class="text-muted">—</span>
              </div>
              <div class="flex items-center gap-3 shrink-0 ip-item-actions">
                <span v-if="ip.mac_address" class="font-mono text-xs text-secondary">{{ ip.mac_address }}</span>
                <Tag :value="getStatusLabel(ip.status)" :severity="getStatusSeverity(ip.status)" class="ip-status-tag" />
                <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click.stop="confirmDeleteIp(ip)" v-tooltip.left="t('common.delete')" />
              </div>
            </div>

            <div v-if="ipData.total > 0" class="flex justify-center pt-4">
              <Paginator
                :rows="pageSize"
                :totalRecords="ipData.total"
                :first="currentPage * pageSize"
                :rowsPerPageOptions="[25, 50, 100, 200]"
                @page="onPageChange"
                template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
              />
            </div>
          </div>

          <div v-else class="text-sm text-muted text-center py-8">
            <i class="pi pi-inbox text-4xl mb-2 opacity-30"></i>
            <p>{{ t('ipam.noIps') }}</p>
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <div class="flex items-center gap-3">
        <Button
          :label="t('ipam.scanSubnet')"
          icon="pi pi-search"
          severity="secondary"
          outlined
          @click="scanSubnet"
        />
        <Button
          :label="t('ipam.addIp')"
          icon="pi pi-plus"
          @click="showAddIpDialog = true"
        />
      </div>
    </template>
  </SlideOver>

  <!-- Add IP Dialog -->
  <Dialog v-model:visible="showAddIpDialog" modal :header="t('ipam.manualIpAllocation')" :style="{ width: '400px' }" @keydown.enter="onIpDialogEnter">
    <div class="flex flex-col gap-4 mt-2 add-ip-form">
      <div class="flex flex-col gap-2">
        <label for="ipaddr" class="form-label">{{ t('ipam.ipAddress') }} <span class="text-red-500">*</span></label>
        <InputText id="ipaddr" v-model="newIp.address" :placeholder="getIpPlaceholder()" class="form-input" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="hostname" class="form-label">{{ t('ipam.hostname') }}</label>
        <InputText id="hostname" v-model="newIp.hostname" class="form-input" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="mac" class="form-label">{{ t('ipam.mac') }}</label>
        <InputText id="mac" v-model="newIp.mac_address" placeholder="00:00:00:00:00:00" class="form-input" />
      </div>
      <div class="flex flex-col gap-2">
        <label for="status" class="form-label">{{ t('ipam.status') }}</label>
        <Dropdown id="status" v-model="newIp.status" :options="ipStatusOptions" optionLabel="label" optionValue="value" class="w-full transparent-dropdown" />
      </div>
    </div>
    <template #footer>
      <div class="flex justify-end gap-3">
        <Button :label="t('common.cancel')" severity="secondary" outlined @click="showAddIpDialog = false" />
        <Button :label="t('common.add')" icon="pi pi-check" @click="createIp" />
      </div>
    </template>
  </Dialog>

  <!-- Delete IP Confirmation -->
  <Dialog v-model:visible="showDeleteIpDialog" modal :header="t('common.confirmDelete')" :style="{ width: '400px' }">
    <div class="flex items-start gap-4 delete-ip-dialog-body">
      <i class="pi pi-exclamation-triangle text-orange-500 text-3xl"></i>
      <div>
        <p class="mb-2 dialog-text">{{ t('ipam.confirmDeleteIp') }}</p>
        <p class="font-mono font-bold dialog-value">{{ deletingIp?.address }}</p>
      </div>
    </div>
    <template #footer>
      <div class="flex justify-end gap-3">
        <Button :label="t('common.cancel')" severity="secondary" outlined @click="showDeleteIpDialog = false" />
        <Button :label="t('common.delete')" icon="pi pi-trash" severity="danger" @click="deleteIp" />
      </div>
    </template>
  </Dialog>

  <!-- Bulk Actions Dialog -->
  <Dialog v-model:visible="showBulkDialog" modal :header="t('bulk.title')" :style="{ width: '450px' }">
    <div class="space-y-4">
      <!-- Selection Summary -->
      <div class="p-4 rounded-xl selection-summary">
        <div class="flex items-center gap-3">
          <div class="action-icon">
            <i class="pi pi-check-square"></i>
          </div>
          <div>
            <div class="text-2xl font-bold text-theme-primary">{{ selectedIps.length }}</div>
            <div class="text-sm text-theme-secondary">{{ t('bulk.elementsSelected') }}</div>
          </div>
        </div>
      </div>

      <!-- Change Status Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click="showBulkStatusAction = !showBulkStatusAction">
        <div class="flex items-center gap-4">
          <div class="action-icon">
            <i class="pi pi-sync"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.changeStatus') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.changeStatusDesc') }}</div>
          </div>
          <i :class="['pi transition-transform', showBulkStatusAction ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
        </div>
        <div v-if="showBulkStatusAction" class="mt-4 pt-4 border-t bulk-status-border" @click.stop>
          <Dropdown v-model="bulkStatus" :options="bulkStatusOptions" optionLabel="label" optionValue="value"
                    :placeholder="t('ipam.changeStatus')" class="w-full mb-3 transparent-dropdown" />
          <Button :label="t('bulk.applyToAll', { count: selectedIps.length })" icon="pi pi-check"
                  class="w-full" @click="applyBulkStatus" :disabled="!bulkStatus" :loading="bulkLoading" />
        </div>
      </div>

      <!-- Export Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click="showBulkExportAction = !showBulkExportAction">
        <div class="flex items-center gap-4">
          <div class="action-icon action-icon-export">
            <i class="pi pi-download"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.exportToCsv') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.exportToCsvDesc') }}</div>
          </div>
          <i :class="['pi transition-transform', showBulkExportAction ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
        </div>
        <div v-if="showBulkExportAction" class="mt-4 pt-4 border-t bulk-status-border" @click.stop>
          <div class="mb-3">
            <label class="block text-sm font-medium mb-2 action-desc">{{ t('bulk.selectColumns') }}</label>
            <div class="export-columns-grid">
              <div v-for="col in exportColumnOptions" :key="col.value" class="flex items-center gap-2">
                <Checkbox v-model="exportColumns" :inputId="'ip-export-' + col.value" :value="col.value" />
                <label :for="'ip-export-' + col.value" class="text-sm cursor-pointer action-desc">{{ col.label }}</label>
              </div>
            </div>
          </div>
          <div class="flex gap-2 mb-3">
            <Button :label="t('bulk.selectAll')" text size="small" @click="exportColumns = exportColumnOptions.map(c => c.value)" />
            <Button :label="t('bulk.deselectAll')" text size="small" @click="exportColumns = []" />
          </div>
          <div class="mb-3">
            <label class="block text-sm font-medium mb-2 action-desc">{{ t('bulk.exportFormat') }}</label>
            <div class="export-format-selector">
              <div v-for="fmt in exportFormatOptions" :key="fmt.value"
                   class="format-option" :class="{ active: exportFormat === fmt.value }"
                   @click="exportFormat = fmt.value">
                <i :class="fmt.icon"></i>
                <span>{{ fmt.label }}</span>
              </div>
            </div>
          </div>
          <Button :label="t('bulk.exportSelected', { count: selectedIps.length })" icon="pi pi-download"
                  class="w-full" @click="applyBulkExport" :disabled="exportColumns.length === 0" :loading="bulkLoading" />
        </div>
      </div>

      <!-- Release Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click.stop="applyBulkRelease">
        <div class="flex items-center gap-4">
          <div class="action-icon action-icon-warning">
            <i class="pi pi-undo"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.releaseItems') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.releaseItemsDesc') }}</div>
          </div>
          <i class="pi pi-chevron-right"></i>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center">
        <Button :label="t('common.clearSelection')" text size="small" @click="selectedIps = []; showBulkDialog = false" />
        <Button :label="t('common.close')" severity="secondary" outlined @click="showBulkDialog = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'
import api from '../../api'
import SlideOver from './SlideOver.vue'

const props = defineProps({
  modelValue: Boolean,
  subnetId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const router = useRouter()
const toast = useToast()
const { t } = useI18n()

// State
const subnet = ref(null)
const ipData = ref({ items: [], total: 0, skip: 0, limit: 50 })
const loading = ref(false)
const loadingIps = ref(false)
const showAddIpDialog = ref(false)
const showDeleteIpDialog = ref(false)
const deletingIp = ref(null)
const newIp = ref({ address: '', hostname: '', mac_address: '', status: 'active' })

// Pagination and filtering
const pageSize = ref(50)
const currentPage = ref(0)
const statusFilter = ref(null)
const searchQuery = ref('')

// Bulk operations
const selectedIps = ref([])
const bulkStatus = ref(null)
const bulkLoading = ref(false)
const showBulkDialog = ref(false)
const showBulkStatusAction = ref(false)
const showBulkExportAction = ref(false)
const exportColumns = ref([])
const exportFormat = ref('xlsx')

const exportColumnOptions = [
  { value: 'address', label: 'Address' },
  { value: 'subnet', label: 'Subnet' },
  { value: 'status', label: 'Status' },
  { value: 'hostname', label: 'Hostname' },
  { value: 'mac_address', label: 'MAC Address' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'last_scanned_at', label: 'Last Scanned' }
]

const exportFormatOptions = [
  { label: 'Excel (.xlsx)', value: 'xlsx', icon: 'pi pi-file-excel' },
  { label: 'CSV (.csv)', value: 'csv', icon: 'pi pi-file' }
]

const bulkStatusOptions = computed(() => [
  { label: t('status.available'), value: 'available' },
  { label: t('status.reserved'), value: 'reserved' },
  { label: t('status.assigned'), value: 'assigned' },
  { label: t('status.dhcp'), value: 'dhcp' }
])

const ipStatusOptions = computed(() => [
  { label: t('status.available'), value: 'available' },
  { label: t('status.active'), value: 'active' },
  { label: t('status.reserved'), value: 'reserved' }
])

const isAllOnPageSelected = computed(() => {
  if (filteredIps.value.length === 0) return false
  return filteredIps.value.every(ip => isIpSelected(ip))
})

const isIpSelected = (ip) => selectedIps.value.some(s => s.id === ip.id)

const toggleIpSelection = (ip) => {
  const index = selectedIps.value.findIndex(s => s.id === ip.id)
  if (index === -1) {
    selectedIps.value.push(ip)
  } else {
    selectedIps.value.splice(index, 1)
  }
}

const toggleSelectAllOnPage = () => {
  if (isAllOnPageSelected.value) {
    // Deselect all on page
    const idsOnPage = filteredIps.value.map(ip => ip.id)
    selectedIps.value = selectedIps.value.filter(s => !idsOnPage.includes(s.id))
  } else {
    // Select all on page
    filteredIps.value.forEach(ip => {
      if (!isIpSelected(ip)) {
        selectedIps.value.push(ip)
      }
    })
  }
}

const getStatusLabel = (status) => {
  const statusMap = {
    'active': t('status.active'),
    'reserved': t('status.reserved'),
    'available': t('status.available'),
    'assigned': t('status.assigned'),
    'dhcp': t('status.dhcp')
  }
  return statusMap[status] || status
}

// Computed
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const statusFilterOptions = computed(() => [
  { label: t('status.active'), value: 'active' },
  { label: t('status.reserved'), value: 'reserved' },
  { label: t('status.available'), value: 'available' }
])

const activeCount = computed(() => {
  return ipData.value.items.filter(ip => ip.status === 'active').length
})

const reservedCount = computed(() => {
  return ipData.value.items.filter(ip => ip.status === 'reserved').length
})

const filteredIps = computed(() => {
  let result = ipData.value.items

  if (statusFilter.value) {
    result = result.filter(ip => ip.status === statusFilter.value)
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(ip =>
      ip.address.toLowerCase().includes(query) ||
      (ip.hostname && ip.hostname.toLowerCase().includes(query)) ||
      (ip.mac_address && ip.mac_address.toLowerCase().includes(query)) ||
      (ip.equipment?.name && ip.equipment.name.toLowerCase().includes(query))
    )
  }

  return result
})

// Methods
const loadSubnetDetails = async () => {
  if (!props.subnetId) return

  loading.value = true
  try {
    // Load all subnets and find the one we need
    const response = await api.get('/subnets/')
    subnet.value = response.data.find(s => s.id === props.subnetId)

    // Load IPs
    await loadIps()
  } catch (error) {
    console.error('Failed to load subnet details:', error)
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('ipam.failedLoadSubnet'), life: 3000 })
  } finally {
    loading.value = false
  }
}

const loadIps = async () => {
  if (!props.subnetId) return

  loadingIps.value = true
  try {
    const response = await api.get(`/subnets/${props.subnetId}/ips/`, {
      params: {
        skip: currentPage.value * pageSize.value,
        limit: pageSize.value
      }
    })
    ipData.value = {
      items: response.data.items || [],
      total: response.data.total || 0,
      skip: response.data.skip || 0,
      limit: response.data.limit || pageSize.value
    }
  } catch (error) {
    console.error('Failed to load IPs:', error)
    ipData.value = { items: [], total: 0, skip: 0, limit: pageSize.value }
  } finally {
    loadingIps.value = false
  }
}

const onPageChange = (event) => {
  currentPage.value = event.page
  if (event.rows !== pageSize.value) {
    pageSize.value = event.rows
  }
  loadIps()
}

const getIpPlaceholder = () => {
  if (!subnet.value?.cidr) return '192.168.1.1'
  // Extract network part from CIDR
  const cidr = subnet.value.cidr
  const parts = cidr.split('/')
  if (parts.length > 0) {
    const network = parts[0].split('.')
    if (network.length === 4) {
      return `${network[0]}.${network[1]}.${network[2]}.x`
    }
  }
  return '192.168.1.1'
}

const createIp = async () => {
  if (!newIp.value.address) {
    toast.add({ severity: 'warn', summary: t('common.error'), detail: t('validation.fillRequiredFields'), life: 3000 })
    return
  }
  try {
    await api.post(`/subnets/${props.subnetId}/ips/`, newIp.value)
    showAddIpDialog.value = false
    newIp.value = { address: '', hostname: '', mac_address: '', status: 'active' }
    await loadIps()
    emit('refresh')
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('ipam.ipAllocated'), life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('ipam.failedAllocateIp'), life: 3000 })
  }
}

const confirmDeleteIp = (ip) => {
  deletingIp.value = ip
  showDeleteIpDialog.value = true
}

const deleteIp = async () => {
  if (!deletingIp.value) return
  try {
    await api.delete(`/subnets/${props.subnetId}/ips/${deletingIp.value.id}`)
    showDeleteIpDialog.value = false
    await loadIps()
    emit('refresh')
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('ipam.ipDeleted'), life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('common.error'), life: 3000 })
  }
}

const scanSubnet = async () => {
  try {
    const response = await api.post(`/subnets/${props.subnetId}/scan`)
    if (response.data?.message) {
      toast.add({ severity: 'info', summary: t('ipam.scanStarted'), detail: `${t('ipam.scanningBackground')} ${subnet.value?.cidr}`, life: 5000 })
    }
  } catch (error) {
    const detail = error.response?.data?.detail || error.response?.data?.message || t('ipam.failedStartScan')
    toast.add({ severity: 'error', summary: t('common.error'), detail: detail, life: 5000 })
  }
}

const navigateToEquipment = (equipment) => {
  visible.value = false
  router.push(`/inventory?equipment=${equipment.id}`)
}

const getStatusSeverity = (status) => {
  switch (status) {
    case 'active': return 'success'
    case 'reserved': return 'warning'
    case 'available': return 'info'
    default: return null
  }
}

const onIpDialogEnter = (event) => {
  if (event.target.tagName !== 'TEXTAREA') {
    event.preventDefault()
    createIp()
  }
}

// Bulk operations functions
const applyBulkStatus = async () => {
  if (!bulkStatus.value || selectedIps.value.length === 0) return
  bulkLoading.value = true
  try {
    const response = await api.post('/subnets/ips/bulk-status', {
      ip_ids: selectedIps.value.map(ip => ip.id),
      status: bulkStatus.value
    })
    const result = response.data
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('ipam.bulkStatusSuccess', { count: result.processed }), life: 3000 })
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('ipam.bulkStatusPartial', { processed: result.processed, failed: result.failed }), life: 3000 })
    }
    selectedIps.value = []
    bulkStatus.value = null
    showBulkDialog.value = false
    showBulkStatusAction.value = false
    await loadIps()
    emit('refresh')
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('common.error'), life: 3000 })
  } finally {
    bulkLoading.value = false
  }
}

const applyBulkRelease = async () => {
  if (selectedIps.value.length === 0) return
  bulkLoading.value = true
  try {
    const ipIds = selectedIps.value.map(ip => ip.id).filter(id => id != null)
    if (ipIds.length === 0) return
    const response = await api.post('/subnets/ips/bulk-release', { ip_ids: ipIds })
    const result = response.data
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('ipam.bulkReleaseSuccess', { count: result.processed }), life: 3000 })
      selectedIps.value = []
      showBulkDialog.value = false
      await loadIps()
      emit('refresh')
    } else {
      const errDetail = (result.errors && result.errors.length) ? result.errors.join('; ') : t('ipam.bulkReleasePartial', { processed: result.processed, failed: result.failed })
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: errDetail, life: 5000 })
    }
  } catch (error) {
    const detail = error.response?.data?.detail
    const msg = Array.isArray(detail) ? detail.map(e => e.msg || e).join('; ') : (typeof detail === 'string' ? detail : t('common.error'))
    toast.add({ severity: 'error', summary: t('common.error'), detail: msg, life: 5000 })
  } finally {
    bulkLoading.value = false
  }
}

const applyBulkExport = async () => {
  if (selectedIps.value.length === 0 || exportColumns.value.length === 0) return
  bulkLoading.value = true
  try {
    const response = await api.post(
      '/export/ip-addresses/bulk',
      {
        ip_ids: selectedIps.value.map(ip => ip.id),
        columns: exportColumns.value,
        format: exportFormat.value
      },
      { responseType: 'blob' }
    )
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const ext = exportFormat.value === 'xlsx' ? 'xlsx' : 'csv'
    link.setAttribute('download', `ip_addresses_export_${timestamp}.${ext}`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('bulk.exportSuccess', { count: selectedIps.value.length }), life: 3000 })
    exportColumns.value = []
    showBulkExportAction.value = false
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('common.error'), life: 3000 })
  } finally {
    bulkLoading.value = false
  }
}

// Watch for changes
watch(() => [props.modelValue, props.subnetId], ([isVisible, id]) => {
  if (isVisible && id) {
    currentPage.value = 0
    statusFilter.value = null
    searchQuery.value = ''
    selectedIps.value = []
    bulkStatus.value = null
    showBulkDialog.value = false
    showBulkStatusAction.value = false
    showBulkExportAction.value = false
    loadSubnetDetails()
  }
}, { immediate: true })
</script>

<style scoped>
/* Aligné sur le thème global (TicketDetailSlideOver) */

/* Bouton + visible */
.add-ip-btn {
  background-color: var(--primary) !important;
  border-color: var(--primary) !important;
  color: white !important;
}

.add-ip-btn:hover {
  background-color: var(--primary-dark, #0284c7) !important;
}

/* Checkbox visible en dark mode */
.select-all-checkbox :deep(.p-checkbox-box),
.ip-item :deep(.p-checkbox-box) {
  border-color: var(--border-strong) !important;
  background-color: var(--bg-secondary) !important;
}

.select-all-checkbox :deep(.p-checkbox-box.p-highlight),
.ip-item :deep(.p-checkbox-box.p-highlight) {
  background-color: var(--primary) !important;
  border-color: var(--primary) !important;
}

:root.dark .select-all-checkbox :deep(.p-checkbox-box),
:root.dark .ip-item :deep(.p-checkbox-box) {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background-color: rgba(255, 255, 255, 0.05) !important;
}

:root.dark .select-all-checkbox :deep(.p-checkbox-box.p-highlight),
:root.dark .ip-item :deep(.p-checkbox-box.p-highlight) {
  background-color: var(--primary) !important;
  border-color: var(--primary) !important;
}

:root.dark .select-all-checkbox :deep(.p-checkbox-box .p-checkbox-icon),
:root.dark .ip-item :deep(.p-checkbox-box .p-checkbox-icon) {
  color: white !important;
}

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

.stat-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card .text-xs {
  color: var(--text-secondary);
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
}

.stat-value--total { color: var(--primary); }
.stat-value--active { color: #22c55e; }
.stat-value--reserved { color: #f59e0b; }

.ip-item {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  transition: all 0.15s ease;
}

.ip-item:hover {
  background-color: var(--bg-hover);
  border-color: var(--border-strong);
}

.ip-item--selected {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary);
}

.ip-item-actions {
  display: flex;
  align-items: center;
}

.ip-status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ip-status-tag:deep(.p-tag) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.text-secondary {
  color: var(--text-secondary);
}

.text-muted {
  color: var(--text-muted);
}

.text-theme-primary { color: var(--text-primary); }
.text-theme-secondary { color: var(--text-secondary); }

/* Bulk dialog */
.action-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  margin-bottom: 0.75rem;
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-light);
}

.action-icon i { color: var(--primary); }
.action-icon-warning { background: var(--warning-light); }
.action-icon-warning i { color: var(--warning); }

.action-icon-export { background: rgba(34, 197, 94, 0.15); }
.action-icon-export i { color: #22c55e; }

.export-columns-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem 1rem;
}
.export-columns-grid label { color: var(--text-secondary); }

.export-format-selector { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.format-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-default);
  cursor: pointer;
  transition: all 0.15s ease;
}
.format-option:hover { border-color: var(--border-strong); }
.format-option.active { border-color: var(--primary); background: var(--primary-light); }

.selection-summary {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
}

.action-card .action-title { color: var(--text-primary); }
.action-card .action-desc { color: var(--text-secondary); }

.bulk-status-border { border-color: var(--border-default); }

/* Dropdowns : même style que Tickets / Knowledge (transparent & minimal) */
.ipam-toolbar-filters .info-dropdown:deep(.p-dropdown),
.ipam-toolbar-filters :deep(.info-dropdown.p-dropdown),
.info-dropdown:deep(.p-dropdown),
:deep(.info-dropdown.p-dropdown) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 0 !important;
  width: 100%;
  position: relative;
}

.info-dropdown:deep(.p-dropdown.p-focus),
.info-dropdown:deep(.p-dropdown:hover),
:deep(.info-dropdown.p-dropdown.p-focus),
:deep(.info-dropdown.p-dropdown:hover) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.info-dropdown:deep(.p-dropdown .p-dropdown-label),
:deep(.info-dropdown .p-dropdown-label) {
  padding: 0.25rem 3rem 0.25rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  background: transparent !important;
}

.info-dropdown:deep(.p-dropdown .p-dropdown-label.p-placeholder),
:deep(.info-dropdown .p-dropdown-label.p-placeholder) {
  color: var(--text-secondary);
}

.info-dropdown:deep(.p-dropdown .p-dropdown-trigger),
:deep(.info-dropdown .p-dropdown-trigger) {
  position: absolute;
  right: 1.25rem;
  top: 0;
  bottom: 0;
  margin: auto;
  height: fit-content;
  width: auto;
  color: var(--text-muted);
  background: transparent !important;
}

.info-dropdown:deep(.p-dropdown .p-dropdown-clear-icon),
:deep(.info-dropdown .p-dropdown-clear-icon) {
  position: absolute;
  right: 0.5rem;
  top: 0;
  bottom: 0;
  margin: auto;
  height: fit-content;
  color: var(--text-muted);
}

.info-dropdown:deep(.p-dropdown .p-dropdown-clear-icon:hover),
:deep(.info-dropdown .p-dropdown-clear-icon:hover) {
  color: var(--primary);
}

/* transparent-dropdown (dialogs) */
.transparent-dropdown:deep(.p-dropdown),
:deep(.transparent-dropdown.p-dropdown) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 0 !important;
  width: 100%;
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-label),
:deep(.transparent-dropdown .p-dropdown-label) {
  padding: 0.5rem 3.5rem 0.5rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  background: transparent !important;
  display: flex;
  align-items: center;
  min-height: 2.25rem;
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-label.p-placeholder),
:deep(.transparent-dropdown .p-dropdown-label.p-placeholder) {
  color: var(--text-secondary);
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-trigger),
:deep(.transparent-dropdown .p-dropdown-trigger) {
  position: absolute;
  right: 1.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: auto;
  color: var(--text-muted);
  background: transparent !important;
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-clear-icon),
:deep(.transparent-dropdown .p-dropdown-clear-icon) {
  position: absolute;
  right: 0.5rem;
  top: 0;
  bottom: 0;
  margin: auto;
  height: fit-content;
  color: var(--text-muted);
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-clear-icon:hover),
:deep(.transparent-dropdown .p-dropdown-clear-icon:hover) {
  color: var(--primary);
}

.form-label { font-size: 0.875rem; font-weight: 500; color: var(--text-primary); }
.form-input { width: 100%; }

/* ==================== Dark theme ==================== */
:root.dark .section-title { color: var(--primary); }
:root.dark .section-content .label { color: #94a3b8; }
:root.dark .section-content .value { color: #f1f5f9; }
:root.dark .stat-card .text-xs { color: #94a3b8; }
:root.dark .stat-value--total { color: #38bdf8; }
:root.dark .stat-value--active { color: #4ade80; }
:root.dark .stat-value--reserved { color: #fbbf24; }
:root.dark .text-secondary { color: #94a3b8; }
:root.dark .text-muted { color: #64748b; }
:root.dark .ip-item .font-mono,
:root.dark .ip-item .font-medium { color: #e2e8f0; }
:root.dark .ip-item .text-primary { color: #38bdf8; }
:root.dark .ip-item span[class*="text-secondary"] { color: #94a3b8; }
:root.dark .ip-item span[class*="text-muted"] { color: #64748b; }
.bulk-bar { background-color: var(--bg-secondary); border: 1px solid var(--border-default); min-height: 48px; }
.bulk-bar:has(.p-checkbox-box.p-highlight) { border-color: var(--primary); }
.bulk-bar-selection-text { font-weight: 500; font-size: 0.875rem; color: var(--text-primary); }
:root.dark .bulk-bar-selection-text,
:root.dark .bulk-bar span,
:root.dark .selection-summary .text-theme-primary { color: #e2e8f0; }
:root.dark .selection-summary .text-theme-secondary { color: #94a3b8; }
:root.dark .action-card .action-title { color: #f1f5f9; }
:root.dark .action-card .action-desc { color: #94a3b8; }
:root.dark .form-label { color: #e2e8f0; }
:root.dark .add-ip-form .p-inputtext { background: rgba(255,255,255,0.05) !important; border-color: rgba(255,255,255,0.1); color: #f1f5f9; }
:root.dark .add-ip-form .p-inputtext::placeholder { color: #64748b; }
:root.dark .info-dropdown:deep(.p-dropdown .p-dropdown-label),
:root.dark :deep(.info-dropdown .p-dropdown-label) { color: #e2e8f0; }
:root.dark .info-dropdown:deep(.p-dropdown .p-dropdown-label.p-placeholder),
:root.dark :deep(.info-dropdown .p-dropdown-label.p-placeholder) { color: #94a3b8; }
:root.dark .transparent-dropdown:deep(.p-dropdown .p-dropdown-label),
:root.dark :deep(.transparent-dropdown .p-dropdown-label) { color: #e2e8f0; }
:root.dark .transparent-dropdown:deep(.p-dropdown .p-dropdown-label.p-placeholder),
:root.dark :deep(.transparent-dropdown .p-dropdown-label.p-placeholder) { color: #94a3b8; }
:root.dark .ips-empty p,
:root.dark .text-sm.text-muted { color: #94a3b8; }
:root.dark .delete-ip-dialog-body .dialog-text { color: #e2e8f0; }
:root.dark .delete-ip-dialog-body .dialog-value { color: #f1f5f9; }
:root.dark .export-columns-grid label { color: #94a3b8; }
:root.dark .format-option { border-color: rgba(255,255,255,0.1); color: #e2e8f0; }
:root.dark .format-option.active { border-color: var(--primary); background: rgba(14, 165, 233, 0.2); color: #f1f5f9; }
</style>
