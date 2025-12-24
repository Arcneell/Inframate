<template>
  <div class="flex gap-6 h-full">
    <!-- Sidebar Menu -->
    <div class="w-64 flex-shrink-0">
      <div class="card p-0 overflow-hidden">
        <div class="p-4 border-b" style="border-color: var(--border-color);">
          <h3 class="font-bold text-lg">{{ t('dcim.title') }}</h3>
        </div>
        <nav class="p-2">
          <div
            @click="activeSection = 'racks'"
            :class="['flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-colors', activeSection === 'racks' ? 'bg-blue-500 text-white' : 'hover:bg-gray-100 dark:hover:bg-gray-800']"
          >
            <i class="pi pi-server"></i>
            <span class="font-medium">{{ t('dcim.racks') }}</span>
          </div>

          <div
            @click="activeSection = 'pdus'"
            :class="['flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-colors', activeSection === 'pdus' ? 'bg-blue-500 text-white' : 'hover:bg-gray-100 dark:hover:bg-gray-800']"
          >
            <i class="pi pi-bolt"></i>
            <span class="font-medium">{{ t('dcim.pdus') }}</span>
          </div>

          <div
            @click="activeSection = 'rackView'"
            :class="['flex items-center gap-3 px-4 py-3 rounded-lg cursor-pointer transition-colors', activeSection === 'rackView' ? 'bg-blue-500 text-white' : 'hover:bg-gray-100 dark:hover:bg-gray-800']"
          >
            <i class="pi pi-th-large"></i>
            <span class="font-medium">{{ t('dcim.rackView') }}</span>
          </div>
        </nav>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-hidden">
      <!-- Racks Section -->
      <div v-if="activeSection === 'racks'" class="card h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">{{ t('dcim.racks') }}</h3>
          <Button :label="t('dcim.newRack')" icon="pi pi-plus" @click="openRackDialog()" />
        </div>

        <div class="flex gap-3 mb-4">
          <Dropdown v-model="filterLocation" :options="locationOptions" optionLabel="label" optionValue="id" :placeholder="t('filters.allLocations')" showClear class="w-64" />
        </div>

        <div class="flex-1 overflow-auto">
          <DataTable :value="filteredRacks" stripedRows paginator :rows="10" class="text-sm">
            <Column field="name" :header="t('common.name')" sortable></Column>
            <Column :header="t('inventory.location')">
              <template #body="slotProps">
                <span v-if="slotProps.data.location">
                  {{ slotProps.data.location.site }}
                  <span v-if="slotProps.data.location.building"> / {{ slotProps.data.location.building }}</span>
                  <span v-if="slotProps.data.location.room"> / {{ slotProps.data.location.room }}</span>
                </span>
              </template>
            </Column>
            <Column field="height_u" :header="t('dcim.heightU')" style="width: 100px">
              <template #body="slotProps">{{ slotProps.data.height_u }}U</template>
            </Column>
            <Column :header="t('dcim.dimensions')" style="width: 150px">
              <template #body="slotProps">{{ slotProps.data.width_mm }} x {{ slotProps.data.depth_mm }} mm</template>
            </Column>
            <Column field="max_power_kw" :header="t('dcim.maxPower')" style="width: 120px">
              <template #body="slotProps">{{ slotProps.data.max_power_kw ? slotProps.data.max_power_kw + ' kW' : '-' }}</template>
            </Column>
            <Column :header="t('common.actions')" style="width: 120px">
              <template #body="slotProps">
                <div class="flex gap-1">
                  <Button icon="pi pi-eye" text rounded size="small" @click="viewRackLayout(slotProps.data)" v-tooltip.top="t('dcim.viewLayout')" />
                  <Button icon="pi pi-pencil" text rounded size="small" @click="openRackDialog(slotProps.data)" v-tooltip.top="t('common.edit')" />
                  <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="confirmDeleteRack(slotProps.data)" v-tooltip.top="t('common.delete')" />
                </div>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>

      <!-- PDUs Section -->
      <div v-if="activeSection === 'pdus'" class="card h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">{{ t('dcim.pdus') }}</h3>
          <Button :label="t('dcim.newPdu')" icon="pi pi-plus" @click="openPduDialog()" />
        </div>

        <div class="flex-1 overflow-auto">
          <DataTable :value="pdus" stripedRows paginator :rows="10" class="text-sm">
            <Column field="name" :header="t('common.name')" sortable></Column>
            <Column :header="t('dcim.racks')">
              <template #body="slotProps">
                {{ getRackName(slotProps.data.rack_id) || '-' }}
              </template>
            </Column>
            <Column field="pdu_type" :header="t('inventory.type')">
              <template #body="slotProps">
                <Tag :value="slotProps.data.pdu_type" />
              </template>
            </Column>
            <Column field="total_ports" :header="t('dcim.ports')" style="width: 100px"></Column>
            <Column :header="t('dcim.maxPower')" style="width: 150px">
              <template #body="slotProps">
                {{ slotProps.data.max_amps ? slotProps.data.max_amps + 'A' : '-' }} / {{ slotProps.data.voltage }}V
              </template>
            </Column>
            <Column field="phase" :header="t('dcim.phase')" style="width: 100px"></Column>
            <Column :header="t('common.actions')" style="width: 100px">
              <template #body="slotProps">
                <div class="flex gap-1">
                  <Button icon="pi pi-pencil" text rounded size="small" @click="openPduDialog(slotProps.data)" />
                  <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="confirmDeletePdu(slotProps.data)" />
                </div>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>

      <!-- Rack View Section -->
      <div v-if="activeSection === 'rackView'" class="card h-full flex flex-col">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">{{ t('dcim.rackView') }}</h3>
          <Dropdown v-model="selectedRackId" :options="racks" optionLabel="name" optionValue="id" :placeholder="t('dcim.selectRack')" class="w-64" @change="loadRackLayout" />
        </div>

        <div v-if="rackLayout" class="flex-1 overflow-auto">
          <div class="flex gap-6">
            <!-- Rack Visualization -->
            <div class="flex-1">
              <div class="border rounded-lg p-4" style="border-color: var(--border-color); background: var(--bg-app);">
                <div class="text-center mb-4 font-bold">{{ rackLayout.rack?.name }}</div>
                <div class="flex flex-col-reverse">
                  <div v-for="slot in rackLayout.layout" :key="slot.u" class="flex items-center border-b" style="border-color: var(--border-color);">
                    <div class="w-12 text-center text-xs opacity-60 py-2">U{{ slot.u }}</div>
                    <div
                      class="flex-1 py-2 px-3 text-sm transition-colors"
                      :class="[
                        slot.equipment ? (slot.equipment.is_start ? 'bg-blue-500 text-white rounded' : 'bg-blue-400 text-white') : 'hover:bg-gray-100 dark:hover:bg-gray-800',
                        slot.equipment?.status !== 'in_service' ? 'opacity-60' : ''
                      ]"
                    >
                      <template v-if="slot.equipment?.is_start">
                        {{ slot.equipment.name }}
                        <span v-if="slot.equipment.height_u > 1" class="opacity-70">({{ slot.equipment.height_u }}U)</span>
                      </template>
                      <template v-else-if="!slot.equipment">
                        <span class="opacity-30">{{ t('dcim.empty') }}</span>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- PDUs in Rack -->
            <div class="w-64">
              <h4 class="font-semibold mb-3">{{ t('dcim.pdus') }}</h4>
              <div v-if="rackLayout.pdus?.length">
                <div v-for="pdu in rackLayout.pdus" :key="pdu.id" class="p-3 rounded-lg mb-2" style="background: var(--bg-app);">
                  <i class="pi pi-bolt mr-2 text-yellow-500"></i>
                  {{ pdu.name }}
                </div>
              </div>
              <p v-else class="opacity-50 text-sm">{{ t('dcim.noPdus') }}</p>
            </div>
          </div>
        </div>

        <div v-else class="flex-1 flex items-center justify-center opacity-50">
          {{ t('dcim.selectRackToView') }}
        </div>
      </div>
    </div>

    <!-- Rack Dialog -->
    <Dialog v-model:visible="showRackDialog" modal :header="editingRack ? t('dcim.editRack') : t('dcim.newRack')" :style="{ width: '500px' }">
      <div class="flex flex-col gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('common.name') }} <span class="text-red-500">*</span></label>
          <InputText v-model="rackForm.name" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('inventory.location') }} <span class="text-red-500">*</span></label>
          <Dropdown v-model="rackForm.location_id" :options="locationOptions" optionLabel="label" optionValue="id" class="w-full" />
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('dcim.heightU') }}</label>
            <InputNumber v-model="rackForm.height_u" class="w-full" :min="1" :max="50" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('dcim.widthMm') }}</label>
            <InputNumber v-model="rackForm.width_mm" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('dcim.depthMm') }}</label>
            <InputNumber v-model="rackForm.depth_mm" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('dcim.maxPowerKw') }}</label>
          <InputNumber v-model="rackForm.max_power_kw" class="w-full" :minFractionDigits="1" :maxFractionDigits="2" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('inventory.notes') }}</label>
          <Textarea v-model="rackForm.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showRackDialog = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveRack" />
        </div>
      </template>
    </Dialog>

    <!-- PDU Dialog -->
    <Dialog v-model:visible="showPduDialog" modal :header="editingPdu ? t('dcim.editPdu') : t('dcim.newPdu')" :style="{ width: '500px' }">
      <div class="flex flex-col gap-4">
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('common.name') }} <span class="text-red-500">*</span></label>
          <InputText v-model="pduForm.name" class="w-full" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('dcim.racks') }}</label>
          <Dropdown v-model="pduForm.rack_id" :options="racks" optionLabel="name" optionValue="id" class="w-full" showClear />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('inventory.type') }}</label>
            <Dropdown v-model="pduForm.pdu_type" :options="pduTypeOptions" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('dcim.totalPorts') }}</label>
            <InputNumber v-model="pduForm.total_ports" class="w-full" :min="1" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('dcim.maxAmps') }}</label>
            <InputNumber v-model="pduForm.max_amps" class="w-full" :minFractionDigits="1" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('dcim.voltage') }}</label>
            <Dropdown v-model="pduForm.voltage" :options="voltageOptions" class="w-full" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">{{ t('dcim.phase') }}</label>
            <Dropdown v-model="pduForm.phase" :options="phaseOptions" class="w-full" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">{{ t('inventory.notes') }}</label>
          <Textarea v-model="pduForm.notes" rows="2" class="w-full" />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showPduDialog = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="savePdu" />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useToast } from 'primevue/usetoast';
import { useI18n } from 'vue-i18n';
import api from '../api';

const { t } = useI18n();
const toast = useToast();

// Active section
const activeSection = ref('racks');

// Data
const racks = ref([]);
const pdus = ref([]);
const locations = ref([]);
const rackLayout = ref(null);
const selectedRackId = ref(null);

// Filters
const filterLocation = ref(null);

// Dialogs
const showRackDialog = ref(false);
const showPduDialog = ref(false);

// Editing states
const editingRack = ref(null);
const editingPdu = ref(null);

// Forms
const rackForm = ref({
  name: '', location_id: null, height_u: 42, width_mm: 600, depth_mm: 1000, max_power_kw: null, notes: ''
});

const pduForm = ref({
  name: '', rack_id: null, pdu_type: 'basic', total_ports: 8, max_amps: null, voltage: 230, phase: 'single', notes: ''
});

// Options
const pduTypeOptions = ['basic', 'metered', 'switched', 'smart'];
const voltageOptions = [120, 230, 400];
const phaseOptions = ['single', 'three'];

const locationOptions = computed(() => locations.value.map(l => ({
  id: l.id,
  label: `${l.site}${l.building ? ' / ' + l.building : ''}${l.room ? ' / ' + l.room : ''}`
})));

const filteredRacks = computed(() => {
  if (!filterLocation.value) return racks.value;
  return racks.value.filter(r => r.location_id === filterLocation.value);
});

// Helpers
const getRackName = (rackId) => {
  const rack = racks.value.find(r => r.id === rackId);
  return rack?.name;
};

// Data loading
const loadData = async () => {
  try {
    const [racksRes, pdusRes, locationsRes] = await Promise.all([
      api.get('/dcim/racks/'),
      api.get('/dcim/pdus/'),
      api.get('/inventory/locations/')
    ]);
    racks.value = racksRes.data;
    pdus.value = pdusRes.data;
    locations.value = locationsRes.data;
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Failed to load data' });
  }
};

const loadRackLayout = async () => {
  if (!selectedRackId.value) {
    rackLayout.value = null;
    return;
  }
  try {
    const response = await api.get(`/dcim/racks/${selectedRackId.value}/layout`);
    rackLayout.value = response.data;
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Failed to load rack layout' });
  }
};

const viewRackLayout = (rack) => {
  selectedRackId.value = rack.id;
  activeSection.value = 'rackView';
  loadRackLayout();
};

// Rack CRUD
const openRackDialog = (rack = null) => {
  editingRack.value = rack;
  if (rack) {
    rackForm.value = { ...rack };
  } else {
    rackForm.value = { name: '', location_id: null, height_u: 42, width_mm: 600, depth_mm: 1000, max_power_kw: null, notes: '' };
  }
  showRackDialog.value = true;
};

const saveRack = async () => {
  if (!rackForm.value.name || !rackForm.value.location_id) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') });
    return;
  }
  try {
    if (editingRack.value) {
      await api.put(`/dcim/racks/${editingRack.value.id}`, rackForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('dcim.rackUpdated') });
    } else {
      await api.post('/dcim/racks/', rackForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('dcim.rackCreated') });
    }
    showRackDialog.value = false;
    loadData();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  }
};

const confirmDeleteRack = async (rack) => {
  if (!confirm(t('common.confirmDeleteItem'))) return;
  try {
    await api.delete(`/dcim/racks/${rack.id}`);
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('dcim.rackDeleted') });
    loadData();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  }
};

// PDU CRUD
const openPduDialog = (pdu = null) => {
  editingPdu.value = pdu;
  if (pdu) {
    pduForm.value = { ...pdu };
  } else {
    pduForm.value = { name: '', rack_id: null, pdu_type: 'basic', total_ports: 8, max_amps: null, voltage: 230, phase: 'single', notes: '' };
  }
  showPduDialog.value = true;
};

const savePdu = async () => {
  if (!pduForm.value.name) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') });
    return;
  }
  try {
    if (editingPdu.value) {
      await api.put(`/dcim/pdus/${editingPdu.value.id}`, pduForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('dcim.pduUpdated') });
    } else {
      await api.post('/dcim/pdus/', pduForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('dcim.pduCreated') });
    }
    showPduDialog.value = false;
    loadData();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  }
};

const confirmDeletePdu = async (pdu) => {
  if (!confirm(t('common.confirmDeleteItem'))) return;
  try {
    await api.delete(`/dcim/pdus/${pdu.id}`);
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('dcim.pduDeleted') });
    loadData();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  }
};

onMounted(loadData);
</script>
