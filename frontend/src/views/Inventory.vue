<template>
  <div class="inventory-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title-section">
          <h1 class="page-title">
            <i class="pi pi-box"></i>
            {{ t('inventory.title') }}
          </h1>
          <p class="page-subtitle">{{ equipmentStats.total }} {{ t('inventory.equipment') }}</p>
        </div>
        <Button v-if="activeTab === 'equipment'" :label="t('inventory.newEquipment')" icon="pi pi-plus" @click="openEquipmentDialog()" class="create-btn" />
        <Button v-else :label="t('common.add')" icon="pi pi-plus" @click="openConfigFormDialog()" class="create-btn" />
      </div>

      <!-- Stats Bar (inside header when on equipment tab) -->
      <div v-if="activeTab === 'equipment'" class="stats-bar">
        <div class="stat-chip" :class="{ active: filterStatus === null }" @click="setStatusFilter(null)">
          <span class="stat-chip-label">{{ t('common.all') }}</span>
          <span class="stat-chip-count">{{ equipmentStats.total }}</span>
        </div>
        <div class="stat-chip stat-chip--in-service" :class="{ active: filterStatus === 'in_service' }" @click="setStatusFilter('in_service')">
          <span class="stat-chip-label">{{ t('status.inService') }}</span>
          <span class="stat-chip-count">{{ equipmentStats.in_service }}</span>
        </div>
        <div class="stat-chip stat-chip--in-stock" :class="{ active: filterStatus === 'in_stock' }" @click="setStatusFilter('in_stock')">
          <span class="stat-chip-label">{{ t('status.inStock') }}</span>
          <span class="stat-chip-count">{{ equipmentStats.in_stock }}</span>
        </div>
        <div class="stat-chip stat-chip--maintenance" :class="{ active: filterStatus === 'maintenance' }" @click="setStatusFilter('maintenance')">
          <span class="stat-chip-label">{{ t('status.maintenance') }}</span>
          <span class="stat-chip-count">{{ equipmentStats.maintenance }}</span>
        </div>
        <div class="stat-chip stat-chip--retired" :class="{ active: filterStatus === 'retired' }" @click="setStatusFilter('retired')">
          <span class="stat-chip-label">{{ t('status.retired') }}</span>
          <span class="stat-chip-count">{{ equipmentStats.retired }}</span>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="nav-tabs">
        <button
          v-for="tab in navTabs"
          :key="tab.key"
          class="nav-tab"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <i :class="['pi', tab.icon]"></i>
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="nav-tab-count">{{ tab.count }}</span>
        </button>
      </div>
    </div>

    <!-- =============================== EQUIPMENT TAB =============================== -->
    <template v-if="activeTab === 'equipment'">
      <!-- Filters & Search -->
      <div class="toolbar">
        <div class="toolbar-search">
          <i class="pi pi-search"></i>
          <InputText v-model="searchQuery" :placeholder="t('inventory.searchEquipment')" @input="debouncedSearch" />
        </div>

        <span class="toolbar-separator"></span>

        <div class="toolbar-filter">
          <span class="filter-label">{{ t('inventory.type') }}</span>
          <Dropdown v-model="filterType" :options="typeFilterOptions" optionLabel="name" optionValue="id"
                    :placeholder="t('common.all')" showClear @change="onFilterChange" />
        </div>

        <div class="toolbar-filter">
          <span class="filter-label">{{ t('inventory.location') }}</span>
          <Dropdown v-model="filterLocation" :options="locationOptions" optionLabel="label" optionValue="id"
                    :placeholder="t('common.all')" showClear @change="onFilterChange" />
        </div>

        <span class="toolbar-separator"></span>

        <div class="toolbar-spacer"></div>

        <div v-if="selectedEquipment.length > 0" class="toolbar-selection">
          <span class="selection-count">{{ selectedEquipment.length }} {{ t('common.selected') }}</span>
          <Button icon="pi pi-list-check" :label="t('bulk.openBulkActions')" size="small" @click="showBulkSlideOver = true" />
          <Button icon="pi pi-times" text rounded size="small" @click="selectedEquipment = []" />
        </div>
      </div>

      <!-- Equipment List -->
      <div class="tickets-container">
        <div v-if="loadingEquipment" class="loading-state">
          <i class="pi pi-spin pi-spinner"></i>
          <span>{{ t('common.loading') }}</span>
        </div>

        <div v-else-if="equipment.length === 0" class="empty-state">
          <i class="pi pi-box"></i>
          <h3>{{ t('inventory.noEquipment') }}</h3>
          <p>{{ t('inventory.noEquipmentDesc') }}</p>
          <Button :label="t('inventory.newEquipment')" icon="pi pi-plus" @click="openEquipmentDialog()" />
        </div>

        <div v-else class="tickets-list">
          <!-- Table Header -->
          <div class="tickets-header inventory-header">
            <div class="header-checkbox" @click.stop>
              <Checkbox
                :modelValue="allPageSelected"
                :binary="true"
                @update:modelValue="toggleSelectAllPage"
                :indeterminate="somePageSelected"
                v-tooltip.top="allPageSelected ? t('common.deselectAll') : t('common.selectAllOnPage')"
              />
            </div>
            <span class="header-col header-col--sortable header-col--title" @click="toggleSort('name')">
              {{ t('common.name') }}
              <i v-if="sortField === 'name'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
            </span>
            <span class="header-col">{{ t('inventory.model') }}</span>
            <span class="header-col">{{ t('inventory.location') }}</span>
            <span class="header-col">{{ t('ipam.status') }}</span>
            <span class="header-col header-col--actions">{{ t('common.actions') }}</span>
            <span class="header-col--arrow"></span>
          </div>

          <!-- Equipment Rows -->
          <div
            v-for="eq in equipment"
            :key="eq.id"
            class="ticket-row inventory-row"
            :class="{ 'ticket-row--selected': isSelected(eq.id) }"
            @click="openEquipmentDetail(eq)"
          >
            <div class="ticket-checkbox" @click.stop>
              <Checkbox :modelValue="isSelected(eq.id)" :binary="true" @update:modelValue="toggleSelection(eq)" />
            </div>

            <div class="ticket-info">
              <span class="ticket-title">{{ eq.name }}</span>
              <span v-if="eq.model?.equipment_type" class="ticket-type-label">
                <i :class="['pi', eq.model.equipment_type.icon]" style="font-size: 0.625rem;"></i>
                {{ eq.model.equipment_type.name }}
              </span>
              <span v-else-if="eq.serial_number" class="ticket-type-label">{{ eq.serial_number }}</span>
            </div>

            <div class="inventory-model-cell">
              <span v-if="eq.model" class="model-text">
                {{ eq.model.manufacturer?.name }} {{ eq.model.name }}
              </span>
              <span v-else class="text-muted">—</span>
            </div>

            <div class="inventory-location-cell">
              <span v-if="eq.location" class="location-text">
                {{ eq.location.site }}<template v-if="eq.location.building"> / {{ eq.location.building }}</template><template v-if="eq.location.room"> / {{ eq.location.room }}</template>
              </span>
              <span v-else class="text-muted">—</span>
            </div>

            <div class="ticket-tags">
              <Tag :value="getStatusLabel(eq.status)" :severity="getStatusSeverity(eq.status)" />
            </div>

            <div class="inventory-actions" @click.stop>
              <Button icon="pi pi-pencil" text rounded size="small" v-tooltip.top="t('common.edit')" @click="openEquipmentDialog(eq)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" v-tooltip.top="t('common.delete')" @click="confirmDeleteEquipment(eq)" />
            </div>

            <i class="pi pi-chevron-right ticket-arrow"></i>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="equipmentTotal > 0" class="pagination">
          <Paginator
            :rows="equipmentRows"
            :totalRecords="equipmentTotal"
            :first="equipmentFirst"
            :rowsPerPageOptions="[10, 15, 25, 50]"
            @page="onEquipmentPage"
            template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
          />
        </div>
      </div>
    </template>

    <!-- =============================== MANUFACTURERS TAB =============================== -->
    <template v-if="activeTab === 'manufacturers'">
      <div class="toolbar">
        <div class="toolbar-search">
          <i class="pi pi-search"></i>
          <InputText v-model="configSearch" :placeholder="t('inventory.searchManufacturers')" @input="configSearch = $event.target.value" />
        </div>
        <div class="toolbar-spacer"></div>
      </div>
      <div class="tickets-container">
        <div v-if="filteredManufacturers.length === 0" class="empty-state">
          <i class="pi pi-building"></i>
          <h3>{{ t('inventory.noManufacturers') }}</h3>
          <Button :label="t('inventory.newManufacturer')" icon="pi pi-plus" @click="openConfigFormDialog()" />
        </div>
        <div v-else class="tickets-list">
          <div class="tickets-header config-grid-header config-grid--manufacturer">
            <span class="header-col header-col--title">{{ t('common.name') }}</span>
            <span class="header-col">{{ t('inventory.website') }}</span>
            <span class="header-col">{{ t('inventory.notes') }}</span>
            <span class="header-col header-col--actions">{{ t('common.actions') }}</span>
          </div>
          <div v-for="mf in filteredManufacturers" :key="mf.id" class="ticket-row config-grid-row config-grid--manufacturer">
            <div class="config-cell-name">
              <i class="pi pi-building config-cell-icon"></i>
              <span>{{ mf.name }}</span>
            </div>
            <div class="config-cell-detail">
              <a v-if="mf.website" :href="mf.website" target="_blank" rel="noopener" @click.stop class="config-link">{{ mf.website }}</a>
              <span v-else class="text-muted">—</span>
            </div>
            <div class="config-cell-detail">
              <span v-if="mf.notes" class="config-notes-preview">{{ mf.notes }}</span>
              <span v-else class="text-muted">—</span>
            </div>
            <div class="config-cell-actions" @click.stop>
              <Button icon="pi pi-pencil" text rounded size="small" @click="openConfigFormDialog(mf)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="deleteManufacturer(mf.id)" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- =============================== MODELS TAB =============================== -->
    <template v-if="activeTab === 'models'">
      <div class="toolbar">
        <div class="toolbar-search">
          <i class="pi pi-search"></i>
          <InputText v-model="configSearch" :placeholder="t('inventory.searchModels')" @input="configSearch = $event.target.value" />
        </div>
        <span class="toolbar-separator"></span>
        <div class="toolbar-filter">
          <span class="filter-label">{{ t('inventory.manufacturer') }}</span>
          <Dropdown v-model="configFilterManufacturer" :options="manufacturers" optionLabel="name" optionValue="id"
                    :placeholder="t('common.all')" showClear />
        </div>
        <div class="toolbar-filter">
          <span class="filter-label">{{ t('inventory.type') }}</span>
          <Dropdown v-model="configFilterType" :options="types" optionLabel="name" optionValue="id"
                    :placeholder="t('common.all')" showClear />
        </div>
        <div class="toolbar-spacer"></div>
      </div>
      <div class="tickets-container">
        <div v-if="filteredModels.length === 0" class="empty-state">
          <i class="pi pi-th-large"></i>
          <h3>{{ t('inventory.noModels') }}</h3>
          <Button :label="t('inventory.newModel')" icon="pi pi-plus" @click="openConfigFormDialog()" />
        </div>
        <div v-else class="tickets-list">
          <div class="tickets-header config-grid-header config-grid--model">
            <span class="header-col header-col--title">{{ t('common.name') }}</span>
            <span class="header-col">{{ t('inventory.manufacturer') }}</span>
            <span class="header-col">{{ t('inventory.type') }}</span>
            <span class="header-col header-col--actions">{{ t('common.actions') }}</span>
          </div>
          <div v-for="md in filteredModels" :key="md.id" class="ticket-row config-grid-row config-grid--model">
            <div class="config-cell-name">
              <i v-if="md.equipment_type?.icon" :class="'pi ' + md.equipment_type.icon + ' config-cell-icon'"></i>
              <span>{{ md.name }}</span>
            </div>
            <div class="config-cell-detail">{{ md.manufacturer?.name || '—' }}</div>
            <div class="config-cell-detail">
              <Tag v-if="md.equipment_type" :value="md.equipment_type.name" severity="info" />
              <span v-else class="text-muted">—</span>
            </div>
            <div class="config-cell-actions" @click.stop>
              <Button icon="pi pi-pencil" text rounded size="small" @click="openConfigFormDialog(md)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="deleteModel(md.id)" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- =============================== TYPES TAB =============================== -->
    <template v-if="activeTab === 'types'">
      <div class="toolbar">
        <div class="toolbar-search">
          <i class="pi pi-search"></i>
          <InputText v-model="configSearch" :placeholder="t('inventory.searchTypes')" @input="configSearch = $event.target.value" />
        </div>
        <div class="toolbar-spacer"></div>
      </div>
      <div class="tickets-container">
        <div v-if="filteredTypes.length === 0" class="empty-state">
          <i class="pi pi-tags"></i>
          <h3>{{ t('inventory.noTypes') }}</h3>
          <Button :label="t('inventory.newType')" icon="pi pi-plus" @click="openConfigFormDialog()" />
        </div>
        <div v-else class="tickets-list">
          <div class="tickets-header config-grid-header config-grid--type">
            <span class="header-col header-col--title">{{ t('common.name') }}</span>
            <span class="header-col">{{ t('inventory.icon') }}</span>
            <span class="header-col">{{ t('inventory.hierarchyLevel') }}</span>
            <span class="header-col">{{ t('remote.remoteExecution') }}</span>
            <span class="header-col header-col--actions">{{ t('common.actions') }}</span>
          </div>
          <div v-for="tp in filteredTypes" :key="tp.id" class="ticket-row config-grid-row config-grid--type">
            <div class="config-cell-name">
              <i :class="'pi ' + tp.icon + ' config-cell-icon'"></i>
              <span>{{ tp.name }}</span>
            </div>
            <div class="config-cell-detail">
              <code class="icon-code">{{ tp.icon }}</code>
            </div>
            <div class="config-cell-detail">
              <span v-if="tp.hierarchy_level !== undefined && tp.hierarchy_level !== null" class="hierarchy-badge" :style="{ background: getHierarchyColor(tp.hierarchy_level) }">
                {{ tp.hierarchy_level }}
              </span>
              <span class="hierarchy-label">{{ getHierarchyLabel(tp.hierarchy_level) }}</span>
            </div>
            <div class="config-cell-detail">
              <Tag v-if="tp.supports_remote_execution" value="Remote" severity="success" />
              <span v-else class="text-muted">—</span>
            </div>
            <div class="config-cell-actions" @click.stop>
              <Button icon="pi pi-pencil" text rounded size="small" @click="openConfigFormDialog(tp)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="deleteType(tp.id)" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- =============================== LOCATIONS TAB =============================== -->
    <template v-if="activeTab === 'locations'">
      <div class="toolbar">
        <div class="toolbar-search">
          <i class="pi pi-search"></i>
          <InputText v-model="configSearch" :placeholder="t('inventory.searchLocations')" @input="configSearch = $event.target.value" />
        </div>
        <div class="toolbar-spacer"></div>
      </div>
      <div class="tickets-container">
        <div v-if="filteredLocations.length === 0" class="empty-state">
          <i class="pi pi-map-marker"></i>
          <h3>{{ t('inventory.noLocations') }}</h3>
          <Button :label="t('inventory.newLocation')" icon="pi pi-plus" @click="openConfigFormDialog()" />
        </div>
        <div v-else class="tickets-list">
          <div class="tickets-header config-grid-header config-grid--location">
            <span class="header-col header-col--title">{{ t('inventory.site') }}</span>
            <span class="header-col">{{ t('inventory.building') }}</span>
            <span class="header-col">{{ t('inventory.room') }}</span>
            <span class="header-col header-col--actions">{{ t('common.actions') }}</span>
          </div>
          <div v-for="lc in filteredLocations" :key="lc.id" class="ticket-row config-grid-row config-grid--location">
            <div class="config-cell-name">
              <i class="pi pi-map-marker config-cell-icon"></i>
              <span>{{ lc.site }}</span>
            </div>
            <div class="config-cell-detail">{{ lc.building || '—' }}</div>
            <div class="config-cell-detail">{{ lc.room || '—' }}</div>
            <div class="config-cell-actions" @click.stop>
              <Button icon="pi pi-pencil" text rounded size="small" @click="openConfigFormDialog(lc)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="deleteLocation(lc.id)" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- =============================== SUPPLIERS TAB =============================== -->
    <template v-if="activeTab === 'suppliers'">
      <div class="toolbar">
        <div class="toolbar-search">
          <i class="pi pi-search"></i>
          <InputText v-model="configSearch" :placeholder="t('inventory.searchSuppliers')" @input="configSearch = $event.target.value" />
        </div>
        <div class="toolbar-spacer"></div>
      </div>
      <div class="tickets-container">
        <div v-if="filteredSuppliers.length === 0" class="empty-state">
          <i class="pi pi-truck"></i>
          <h3>{{ t('inventory.noSuppliers') }}</h3>
          <Button :label="t('inventory.newSupplier')" icon="pi pi-plus" @click="openConfigFormDialog()" />
        </div>
        <div v-else class="tickets-list">
          <div class="tickets-header config-grid-header config-grid--supplier">
            <span class="header-col header-col--title">{{ t('common.name') }}</span>
            <span class="header-col">{{ t('inventory.contactEmail') }}</span>
            <span class="header-col">{{ t('inventory.phone') }}</span>
            <span class="header-col">{{ t('inventory.website') }}</span>
            <span class="header-col header-col--actions">{{ t('common.actions') }}</span>
          </div>
          <div v-for="sp in filteredSuppliers" :key="sp.id" class="ticket-row config-grid-row config-grid--supplier">
            <div class="config-cell-name">
              <i class="pi pi-truck config-cell-icon"></i>
              <span>{{ sp.name }}</span>
            </div>
            <div class="config-cell-detail">
              <a v-if="sp.contact_email" :href="'mailto:' + sp.contact_email" @click.stop class="config-link">{{ sp.contact_email }}</a>
              <span v-else class="text-muted">—</span>
            </div>
            <div class="config-cell-detail">{{ sp.phone || '—' }}</div>
            <div class="config-cell-detail">
              <a v-if="sp.website" :href="sp.website" target="_blank" rel="noopener" @click.stop class="config-link">{{ sp.website }}</a>
              <span v-else class="text-muted">—</span>
            </div>
            <div class="config-cell-actions" @click.stop>
              <Button icon="pi pi-pencil" text rounded size="small" @click="openConfigFormDialog(sp)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" @click="deleteSupplier(sp.id)" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- =============================== MODALS & SLIDE-OVERS =============================== -->

    <!-- Equipment Detail Slide-Over -->
    <EquipmentDetailSlideOver
      v-model="showDetailSlideOver"
      :equipmentId="selectedEquipmentId"
      @edit="handleEditFromSlideOver"
    />

    <!-- Create/Edit Equipment Modal -->
    <ModalPanel
      v-model="showEquipmentDialog"
      :title="editingEquipment ? t('inventory.editEquipment') : t('inventory.newEquipment')"
      icon="pi-box"
      size="xl"
    >
      <div class="detail-content">
        <!-- Info Grid -->
        <div class="detail-info-grid detail-info-grid--form">
          <div class="info-item">
            <span class="info-label">{{ t('inventory.model') }}</span>
            <Dropdown v-model="equipmentForm.model_id" :options="models" optionLabel="name" optionValue="id"
                      :placeholder="t('inventory.model')" showClear filter class="info-dropdown">
              <template #option="slotProps">
                {{ slotProps.option.manufacturer?.name }} - {{ slotProps.option.name }}
              </template>
            </Dropdown>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('ipam.status') }}</span>
            <Dropdown v-model="equipmentForm.status" :options="statusOptions" optionLabel="label" optionValue="value" class="info-dropdown" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.location') }}</span>
            <Dropdown v-model="equipmentForm.location_id" :options="locationOptions" optionLabel="label" optionValue="id"
                      :placeholder="t('inventory.location')" showClear class="info-dropdown" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.supplier') }}</span>
            <Dropdown v-model="equipmentForm.supplier_id" :options="suppliers" optionLabel="name" optionValue="id"
                      :placeholder="t('inventory.supplier')" showClear class="info-dropdown" />
          </div>
        </div>

        <!-- Name -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-tag"></i>
            {{ t('common.name') }} <span class="required">*</span>
          </h4>
          <InputText v-model="equipmentForm.name" :placeholder="t('inventory.equipmentName')" class="form-input-full" />
        </div>

        <!-- Serial & Asset Tag -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-id-card"></i>
            {{ t('inventory.identification') }}
          </h4>
          <div class="detail-info-grid detail-info-grid--form">
            <div class="info-item">
              <span class="info-label">{{ t('inventory.serialNumber') }}</span>
              <InputText v-model="equipmentForm.serial_number" class="form-input-full" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('inventory.assetTag') }}</span>
              <InputText v-model="equipmentForm.asset_tag" class="form-input-full" />
            </div>
          </div>
        </div>

        <!-- Dates -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-calendar"></i>
            {{ t('common.dates') }}
          </h4>
          <div class="detail-info-grid detail-info-grid--form">
            <div class="info-item">
              <span class="info-label">{{ t('inventory.purchaseDate') }}</span>
              <Calendar v-model="equipmentForm.purchase_date" dateFormat="yy-mm-dd" class="form-input-full" showIcon />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('inventory.warrantyExpiry') }}</span>
              <Calendar v-model="equipmentForm.warranty_expiry" dateFormat="yy-mm-dd" class="form-input-full" showIcon />
            </div>
          </div>
        </div>

        <!-- DCIM Rack Placement -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-server"></i>
            {{ t('dcim.rackPlacement') }}
          </h4>
          <div class="detail-info-grid detail-info-grid--form" >
            <div class="info-item">
              <span class="info-label">{{ t('dcim.racks') }}</span>
              <Dropdown v-model="equipmentForm.rack_id" :options="racks" optionLabel="name" optionValue="id"
                        :placeholder="t('dcim.selectRack')" showClear class="info-dropdown" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('dcim.positionU') }}</span>
              <InputNumber v-model="equipmentForm.position_u" class="form-input-full" :placeholder="t('dcim.positionUPlaceholder')" :min="1" :max="42" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('dcim.heightU') }}</span>
              <InputNumber v-model="equipmentForm.height_u" class="form-input-full" :placeholder="t('dcim.heightUPlaceholder')" :min="1" :max="42" />
            </div>
          </div>
        </div>

        <!-- Remote Execution (conditional) -->
        <div v-if="selectedModelSupportsRemoteExecution" class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-bolt"></i>
            {{ t('remote.remoteExecution') }}
          </h4>
          <div class="detail-info-grid detail-info-grid--form" >
            <div class="info-item">
              <span class="info-label">{{ t('remote.remoteIp') }}</span>
              <InputText v-model="equipmentForm.remote_ip" placeholder="192.168.1.100" class="form-input-full" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('remote.remotePort') }}</span>
              <InputNumber v-model="equipmentForm.remote_port" class="form-input-full" :placeholder="'22'" :min="1" :max="65535" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('remote.osType') }}</span>
              <Dropdown v-model="equipmentForm.os_type" :options="osTypeOptions" :placeholder="t('remote.osType')" class="info-dropdown" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('remote.connectionType') }}</span>
              <Dropdown v-model="equipmentForm.connection_type" :options="connectionTypeOptions" :placeholder="t('remote.connectionType')" class="info-dropdown" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('auth.username') }}</span>
              <InputText v-model="equipmentForm.remote_username" class="form-input-full" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('auth.password') }}</span>
              <Password v-model="equipmentForm.remote_password" class="form-input-full" :feedback="false" toggleMask />
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-comment"></i>
            {{ t('inventory.notes') }}
          </h4>
          <Textarea v-model="equipmentForm.notes" rows="3" class="form-input-full" />
        </div>
      </div>

      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showEquipmentDialog = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveEquipment" />
        </div>
      </template>
    </ModalPanel>

    <!-- Delete Equipment Confirmation -->
    <Dialog v-model:visible="showDeleteEquipmentDialog" modal :header="t('common.confirmDelete')" :style="{ width: '400px' }">
      <div class="flex items-start gap-4">
        <i class="pi pi-exclamation-triangle text-orange-500 text-3xl"></i>
        <div>
          <p class="mb-2">{{ t('common.confirmDeleteItem') }}</p>
          <p class="font-bold">{{ deletingEquipment?.name }}</p>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showDeleteEquipmentDialog = false" />
          <Button :label="t('common.delete')" icon="pi pi-trash" severity="danger" @click="deleteEquipment" />
        </div>
      </template>
    </Dialog>

    <!-- Link IP Dialog -->
    <ModalPanel v-model="showLinkIpDialog" :title="t('ip.linkIp')" icon="pi-link" size="sm">
      <div v-if="linkingEquipment" class="detail-content">
        <div class="detail-section">
          <div class="p-3 rounded-lg" style="background-color: var(--bg-secondary);">
            <span style="color: var(--text-secondary);">{{ t('inventory.equipment') }}:</span>
            <strong class="ml-2">{{ linkingEquipment.name }}</strong>
          </div>
        </div>

        <div v-if="linkingEquipment.ip_addresses?.length" class="detail-section">
          <h4 class="section-title">{{ t('ip.linkedIps') }}</h4>
          <div v-for="ip in linkingEquipment.ip_addresses" :key="ip.id" class="flex items-center justify-between p-3 rounded-lg mb-2" style="background-color: var(--bg-secondary);">
            <span class="font-mono" style="color: var(--text-primary);">{{ ip.address }}</span>
            <Button icon="pi pi-times" text rounded size="small" severity="danger" @click="unlinkIp(ip.id)" />
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">{{ t('ip.availableIps') }}</h4>
          <Dropdown v-model="selectedIpToLink" :options="availableIps" optionLabel="address" optionValue="id"
                    :placeholder="t('ip.selectIp')" class="form-input-full" showClear>
            <template #option="slotProps">
              <span class="font-mono">{{ slotProps.option.address }}</span>
              <span v-if="slotProps.option.hostname" class="ml-2" style="color: var(--text-secondary);">({{ slotProps.option.hostname }})</span>
            </template>
          </Dropdown>
          <p v-if="!availableIps.length" class="text-sm mt-2" style="color: var(--text-muted);">{{ t('ip.noAvailableIps') }}</p>
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showLinkIpDialog = false" />
          <Button :label="t('ip.linkIp')" icon="pi pi-link" @click="linkIp" :disabled="!selectedIpToLink" />
        </div>
      </template>
    </ModalPanel>

    <!-- Bulk Actions Slide-Over -->
    <BulkActionsSlideOver
      v-model="showBulkSlideOver"
      :title="t('bulk.title')"
      :selectedCount="selectedEquipment.length"
      @clear-selection="selectedEquipment = []; showBulkSlideOver = false"
    >
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
        <div v-if="showBulkStatusAction" class="mt-4 pt-4 border-t" style="border-color: var(--border-default);" @click.stop>
          <Dropdown v-model="bulkStatus" :options="statusOptions" optionLabel="label" optionValue="value"
                    :placeholder="t('inventory.changeStatus')" class="w-full mb-3" />
          <Button :label="t('bulk.applyToAll', { count: selectedEquipment.length })" icon="pi pi-check"
                  class="w-full" @click="applyBulkStatus" :disabled="!bulkStatus" :loading="bulkLoading" />
        </div>
      </div>

      <!-- Change Location Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click="showBulkLocationAction = !showBulkLocationAction">
        <div class="flex items-center gap-4">
          <div class="action-icon action-icon-warning">
            <i class="pi pi-map-marker"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.changeLocation') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.changeLocationDesc') }}</div>
          </div>
          <i :class="['pi transition-transform', showBulkLocationAction ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
        </div>
        <div v-if="showBulkLocationAction" class="mt-4 pt-4 border-t" style="border-color: var(--border-default);" @click.stop>
          <Dropdown v-model="bulkLocation" :options="locationOptionsWithClear" optionLabel="label" optionValue="id"
                    :placeholder="t('inventory.changeLocation')" class="w-full mb-3" />
          <Button :label="t('bulk.applyToAll', { count: selectedEquipment.length })" icon="pi pi-check"
                  class="w-full" @click="applyBulkLocation" :disabled="bulkLocation === undefined" :loading="bulkLoading" />
        </div>
      </div>

      <!-- Delete Action -->
      <div class="action-card action-card-danger p-4 rounded-xl cursor-pointer" @click="confirmBulkDelete">
        <div class="flex items-center gap-4">
          <div class="action-icon action-icon-danger">
            <i class="pi pi-trash"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold" style="color: var(--danger);">{{ t('bulk.deleteItems') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.deleteItemsDesc') }}</div>
          </div>
          <i class="pi pi-chevron-right"></i>
        </div>
      </div>
    </BulkActionsSlideOver>

    <!-- Bulk Delete Confirmation -->
    <Dialog v-model:visible="showBulkDeleteDialog" modal :header="t('common.confirmDelete')" :style="{ width: '450px' }">
      <div class="flex items-start gap-4">
        <i class="pi pi-exclamation-triangle text-orange-500 text-3xl"></i>
        <div>
          <p class="mb-2">{{ t('inventory.confirmBulkDelete', { count: selectedEquipment.length }) }}</p>
          <p class="text-sm" style="color: var(--text-muted);">{{ t('common.actionIrreversible') }}</p>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showBulkDeleteDialog = false" />
          <Button :label="t('common.delete')" icon="pi pi-trash" severity="danger" @click="executeBulkDelete" :loading="bulkLoading" />
        </div>
      </template>
    </Dialog>

    <!-- =============================== CONFIG FORM MODALS =============================== -->

    <!-- Manufacturer Form Modal -->
    <ModalPanel v-model="showManufacturerForm" :title="editingManufacturer ? t('common.edit') + ' ' + t('inventory.manufacturer') : t('inventory.newManufacturer')" icon="pi-building" size="lg">
      <div class="detail-content">
        <div class="detail-info-grid detail-info-grid--form">
          <div class="info-item">
            <span class="info-label">{{ t('common.name') }} <span class="required">*</span></span>
            <InputText v-model="manufacturerForm.name" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.website') }}</span>
            <InputText v-model="manufacturerForm.website" placeholder="https://" class="form-input-full" />
          </div>
        </div>
        <div class="detail-section">
          <h4 class="section-title"><i class="pi pi-comment"></i> {{ t('inventory.notes') }}</h4>
          <Textarea v-model="manufacturerForm.notes" rows="2" class="form-input-full" />
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showManufacturerForm = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveManufacturer" />
        </div>
      </template>
    </ModalPanel>

    <!-- Model Form Modal -->
    <ModalPanel v-model="showModelForm" :title="editingModel ? t('common.edit') + ' ' + t('inventory.model') : t('inventory.newModel')" icon="pi-th-large" size="lg">
      <div class="detail-content">
        <div class="detail-info-grid detail-info-grid--form" >
          <div class="info-item">
            <span class="info-label">{{ t('common.name') }} <span class="required">*</span></span>
            <InputText v-model="modelForm.name" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.manufacturer') }} <span class="required">*</span></span>
            <Dropdown v-model="modelForm.manufacturer_id" :options="manufacturers" optionLabel="name" optionValue="id" :placeholder="t('inventory.manufacturer')" class="info-dropdown" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.type') }} <span class="required">*</span></span>
            <Dropdown v-model="modelForm.equipment_type_id" :options="types" optionLabel="name" optionValue="id" :placeholder="t('inventory.type')" class="info-dropdown">
              <template #option="slotProps">
                <i :class="'pi ' + slotProps.option.icon + ' mr-2'"></i>
                {{ slotProps.option.name }}
              </template>
            </Dropdown>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showModelForm = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveModel" />
        </div>
      </template>
    </ModalPanel>

    <!-- Type Form Modal -->
    <ModalPanel v-model="showTypeForm" :title="editingType ? t('common.edit') + ' ' + t('inventory.type') : t('inventory.newType')" icon="pi-tags" size="lg">
      <div class="detail-content">
        <div class="detail-info-grid detail-info-grid--form" >
          <div class="info-item">
            <span class="info-label">{{ t('common.name') }} <span class="required">*</span></span>
            <InputText v-model="typeForm.name" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.icon') }}</span>
            <Dropdown v-model="typeForm.icon" :options="iconOptions" class="info-dropdown">
              <template #value="slotProps">
                <span v-if="slotProps.value"><i :class="'pi ' + slotProps.value" style="margin-right: 0.5rem;"></i> {{ slotProps.value }}</span>
                <span v-else>{{ t('inventory.icon') }}</span>
              </template>
              <template #option="slotProps">
                <i :class="'pi ' + slotProps.option" style="margin-right: 0.5rem;"></i> {{ slotProps.option }}
              </template>
            </Dropdown>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.hierarchyLevel') }}</span>
            <Dropdown v-model="typeForm.hierarchy_level" :options="hierarchyLevelOptions" optionLabel="label" optionValue="value" class="info-dropdown">
              <template #option="slotProps">
                <div class="flex items-center gap-2">
                  <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white" :style="{ background: slotProps.option.color }">{{ slotProps.option.value }}</span>
                  <span>{{ slotProps.option.label }}</span>
                </div>
              </template>
            </Dropdown>
          </div>
        </div>
        <div class="flex items-center gap-2 mt-3">
          <Checkbox v-model="typeForm.supports_remote_execution" binary inputId="supports_remote_cfg" />
          <label for="supports_remote_cfg" class="text-sm cursor-pointer" style="color: var(--text-primary);">{{ t('remote.supportsRemoteExecution') }}</label>
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showTypeForm = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveType" />
        </div>
      </template>
    </ModalPanel>

    <!-- Location Form Modal -->
    <ModalPanel v-model="showLocationForm" :title="editingLocation ? t('common.edit') + ' ' + t('inventory.location') : t('inventory.newLocation')" icon="pi-map-marker" size="lg">
      <div class="detail-content">
        <div class="detail-info-grid detail-info-grid--form" >
          <div class="info-item">
            <span class="info-label">{{ t('inventory.site') }} <span class="required">*</span></span>
            <InputText v-model="locationForm.site" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.building') }}</span>
            <InputText v-model="locationForm.building" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.room') }}</span>
            <InputText v-model="locationForm.room" class="form-input-full" />
          </div>
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showLocationForm = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveLocation" />
        </div>
      </template>
    </ModalPanel>

    <!-- Supplier Form Modal -->
    <ModalPanel v-model="showSupplierForm" :title="editingSupplier ? t('common.edit') + ' ' + t('inventory.supplier') : t('inventory.newSupplier')" icon="pi-truck" size="lg">
      <div class="detail-content">
        <div class="detail-info-grid detail-info-grid--form">
          <div class="info-item">
            <span class="info-label">{{ t('common.name') }} <span class="required">*</span></span>
            <InputText v-model="supplierForm.name" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.contactEmail') }}</span>
            <InputText v-model="supplierForm.contact_email" type="email" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.phone') }}</span>
            <InputText v-model="supplierForm.phone" class="form-input-full" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('inventory.website') }}</span>
            <InputText v-model="supplierForm.website" placeholder="https://" class="form-input-full" />
          </div>
        </div>
        <div class="detail-section">
          <h4 class="section-title"><i class="pi pi-comment"></i> {{ t('inventory.notes') }}</h4>
          <Textarea v-model="supplierForm.notes" rows="2" class="form-input-full" />
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showSupplierForm = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveSupplier" />
        </div>
      </template>
    </ModalPanel>
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'
import api from '../api'
import EquipmentDetailSlideOver from '../components/shared/EquipmentDetailSlideOver.vue'
import BulkActionsSlideOver from '../components/shared/BulkActionsSlideOver.vue'
import ModalPanel from '../components/shared/ModalPanel.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()

// ==================== Active Tab ====================
const activeTab = ref('equipment')
const configSearch = ref('')
const configFilterManufacturer = ref(null)
const configFilterType = ref(null)

const switchTab = (tab) => {
  activeTab.value = tab
  configSearch.value = ''
  configFilterManufacturer.value = null
  configFilterType.value = null
}

// ==================== Equipment State ====================
const equipment = shallowRef([])
const loadingEquipment = ref(false)
const equipmentTotal = ref(0)
const equipmentFirst = ref(0)
const equipmentRows = ref(25)
const searchQuery = ref('')

// Stats
const equipmentStats = ref({ total: 0, in_service: 0, in_stock: 0, maintenance: 0, retired: 0 })

// Sorting
const sortField = ref('name')
const sortOrder = ref(1)

// Filters
const filterStatus = ref(null)
const filterType = ref(null)
const filterLocation = ref(null)

// Selection
const selectedEquipment = ref([])

// Detail slide-over
const showDetailSlideOver = ref(false)
const selectedEquipmentId = ref(null)

// Equipment dialog
const showEquipmentDialog = ref(false)
const editingEquipment = ref(null)
const equipmentForm = ref({
  name: '', serial_number: '', asset_tag: '', status: 'in_service',
  purchase_date: null, warranty_expiry: null, notes: '',
  model_id: null, location_id: null, supplier_id: null,
  remote_ip: '', os_type: null, connection_type: null,
  remote_username: '', remote_password: '', remote_port: null,
  rack_id: null, position_u: null, height_u: null
})

// Delete dialog
const showDeleteEquipmentDialog = ref(false)
const deletingEquipment = ref(null)

// Link IP dialog
const showLinkIpDialog = ref(false)
const linkingEquipment = ref(null)
const selectedIpToLink = ref(null)
const availableIps = ref([])

// Bulk operations
const showBulkSlideOver = ref(false)
const showBulkDeleteDialog = ref(false)
const showBulkStatusAction = ref(false)
const showBulkLocationAction = ref(false)
const bulkStatus = ref(null)
const bulkLocation = ref(undefined)
const bulkLoading = ref(false)

// ==================== Configuration State ====================
const manufacturers = ref([])
const models = ref([])
const types = ref([])
const locations = ref([])
const suppliers = ref([])
const racks = ref([])

// Config form modals
const showManufacturerForm = ref(false)
const showModelForm = ref(false)
const showTypeForm = ref(false)
const showLocationForm = ref(false)
const showSupplierForm = ref(false)

// Config editing states
const editingManufacturer = ref(null)
const editingModel = ref(null)
const editingType = ref(null)
const editingLocation = ref(null)
const editingSupplier = ref(null)

// Config forms
const manufacturerForm = ref({ name: '', website: '', notes: '' })
const modelForm = ref({ name: '', manufacturer_id: null, equipment_type_id: null })
const typeForm = ref({ name: '', icon: 'pi-box', supports_remote_execution: false, hierarchy_level: 3 })
const locationForm = ref({ site: '', building: '', room: '' })
const supplierForm = ref({ name: '', contact_email: '', phone: '', website: '', notes: '' })

// ==================== Filtered config lists ====================
const filteredManufacturers = computed(() => {
  if (!configSearch.value) return manufacturers.value
  const q = configSearch.value.toLowerCase()
  return manufacturers.value.filter(m => m.name.toLowerCase().includes(q) || m.website?.toLowerCase().includes(q))
})

const filteredModels = computed(() => {
  let result = models.value
  if (configSearch.value) {
    const q = configSearch.value.toLowerCase()
    result = result.filter(m => m.name.toLowerCase().includes(q) || m.manufacturer?.name?.toLowerCase().includes(q))
  }
  if (configFilterManufacturer.value) {
    result = result.filter(m => m.manufacturer_id === configFilterManufacturer.value)
  }
  if (configFilterType.value) {
    result = result.filter(m => m.equipment_type_id === configFilterType.value)
  }
  return result
})

const filteredTypes = computed(() => {
  if (!configSearch.value) return types.value
  const q = configSearch.value.toLowerCase()
  return types.value.filter(t => t.name.toLowerCase().includes(q))
})

const filteredLocations = computed(() => {
  if (!configSearch.value) return locations.value
  const q = configSearch.value.toLowerCase()
  return locations.value.filter(l => l.site.toLowerCase().includes(q) || l.building?.toLowerCase().includes(q) || l.room?.toLowerCase().includes(q))
})

const filteredSuppliers = computed(() => {
  if (!configSearch.value) return suppliers.value
  const q = configSearch.value.toLowerCase()
  return suppliers.value.filter(s => s.name.toLowerCase().includes(q) || s.contact_email?.toLowerCase().includes(q) || s.phone?.toLowerCase().includes(q))
})

// ==================== Options ====================
const osTypeOptions = ['linux', 'windows']
const connectionTypeOptions = ['ssh', 'winrm']
const iconOptions = ['pi-server', 'pi-desktop', 'pi-mobile', 'pi-box', 'pi-database', 'pi-wifi', 'pi-globe', 'pi-print', 'pi-shield', 'pi-bolt', 'pi-cog', 'pi-sitemap', 'pi-sliders-h', 'pi-tablet', 'pi-video']

const statusOptions = computed(() => [
  { label: t('status.inService'), value: 'in_service' },
  { label: t('status.inStock'), value: 'in_stock' },
  { label: t('status.retired'), value: 'retired' },
  { label: t('status.maintenance'), value: 'maintenance' }
])

const typeFilterOptions = computed(() => types.value.map(tp => ({ id: tp.id, name: tp.name })))

const locationOptions = computed(() => locations.value.map(l => ({
  id: l.id,
  label: `${l.site}${l.building ? ' / ' + l.building : ''}${l.room ? ' / ' + l.room : ''}`
})))

const locationOptionsWithClear = computed(() => [
  { id: null, label: t('inventory.clearLocation') },
  ...locationOptions.value
])

const hierarchyLevelOptions = computed(() => [
  { value: 0, label: t('inventory.hierarchyLevelOptions.router'), color: '#7c3aed' },
  { value: 1, label: t('inventory.hierarchyLevelOptions.firewall'), color: '#dc2626' },
  { value: 2, label: t('inventory.hierarchyLevelOptions.switch'), color: '#2563eb' },
  { value: 3, label: t('inventory.hierarchyLevelOptions.server'), color: '#059669' },
  { value: 4, label: t('inventory.hierarchyLevelOptions.storage'), color: '#0891b2' },
  { value: 5, label: t('inventory.hierarchyLevelOptions.endpoint'), color: '#64748b' }
])

const navTabs = computed(() => [
  { key: 'equipment', label: t('inventory.equipment'), icon: 'pi-box', count: equipmentStats.value.total },
  { key: 'manufacturers', label: t('inventory.manufacturers'), icon: 'pi-building', count: manufacturers.value.length },
  { key: 'models', label: t('inventory.models'), icon: 'pi-th-large', count: models.value.length },
  { key: 'types', label: t('inventory.types'), icon: 'pi-tags', count: types.value.length },
  { key: 'locations', label: t('inventory.locations'), icon: 'pi-map-marker', count: locations.value.length },
  { key: 'suppliers', label: t('inventory.suppliers'), icon: 'pi-truck', count: suppliers.value.length }
])

const selectedModelSupportsRemoteExecution = computed(() => {
  if (!equipmentForm.value.model_id) return false
  const model = models.value.find(m => m.id === equipmentForm.value.model_id)
  return model?.equipment_type?.supports_remote_execution || false
})

// ==================== Helpers ====================
const getStatusSeverity = (status) => {
  switch (status) {
    case 'in_service': return 'success'
    case 'in_stock': return 'info'
    case 'retired': return 'secondary'
    case 'maintenance': return 'warning'
    default: return null
  }
}

const getStatusLabel = (status) => {
  const opt = statusOptions.value.find(o => o.value === status)
  return opt ? opt.label : status
}

const getHierarchyColor = (level) => {
  const colors = ['#7c3aed', '#dc2626', '#2563eb', '#059669', '#0891b2', '#64748b']
  return colors[level] || '#64748b'
}

const getHierarchyLabel = (level) => {
  const option = hierarchyLevelOptions.value.find(o => o.value === level)
  return option ? option.label : '-'
}

// ==================== Selection ====================
const isSelected = (id) => selectedEquipment.value.some(e => e.id === id)

const toggleSelection = (eq) => {
  const index = selectedEquipment.value.findIndex(e => e.id === eq.id)
  if (index === -1) {
    selectedEquipment.value.push(eq)
  } else {
    selectedEquipment.value.splice(index, 1)
  }
}

const allPageSelected = computed(() => {
  if (equipment.value.length === 0) return false
  return equipment.value.every(eq => isSelected(eq.id))
})

const somePageSelected = computed(() => {
  if (equipment.value.length === 0) return false
  const count = equipment.value.filter(eq => isSelected(eq.id)).length
  return count > 0 && count < equipment.value.length
})

const toggleSelectAllPage = () => {
  if (allPageSelected.value) {
    equipment.value.forEach(eq => {
      const idx = selectedEquipment.value.findIndex(e => e.id === eq.id)
      if (idx !== -1) selectedEquipment.value.splice(idx, 1)
    })
  } else {
    equipment.value.forEach(eq => {
      if (!isSelected(eq.id)) selectedEquipment.value.push(eq)
    })
  }
}

// ==================== Search & Sorting ====================
let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    equipmentFirst.value = 0
    loadEquipment()
  }, 300)
}

const toggleSort = (field) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === -1 ? 1 : -1
  } else {
    sortField.value = field
    sortOrder.value = 1
  }
  loadEquipment()
}

const setStatusFilter = (status) => {
  filterStatus.value = status
  equipmentFirst.value = 0
  loadEquipment()
  loadEquipmentStats()
}

const onFilterChange = () => {
  equipmentFirst.value = 0
  loadEquipment()
}

const onEquipmentPage = (event) => {
  equipmentFirst.value = event.first
  equipmentRows.value = event.rows
  loadEquipment()
}

// ==================== Data Loading ====================
const loadEquipment = async () => {
  loadingEquipment.value = true
  try {
    const params = {
      skip: equipmentFirst.value,
      limit: equipmentRows.value
    }
    if (filterType.value) params.type_id = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    if (filterLocation.value) params.location_id = filterLocation.value
    if (searchQuery.value) params.search = searchQuery.value

    const res = await api.get('/inventory/equipment/', { params })
    equipment.value = res.data.items
    equipmentTotal.value = res.data.total
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Failed to load equipment' })
  } finally {
    loadingEquipment.value = false
  }
}

const loadEquipmentStats = async () => {
  try {
    const statusKeys = ['in_service', 'in_stock', 'maintenance', 'retired']
    const [totalRes, ...statusResults] = await Promise.all([
      api.get('/inventory/equipment/', { params: { limit: 1 } }),
      ...statusKeys.map(status => api.get('/inventory/equipment/', { params: { status, limit: 1 } }))
    ])
    equipmentStats.value = {
      total: totalRes.data.total,
      in_service: statusResults[0].data.total,
      in_stock: statusResults[1].data.total,
      maintenance: statusResults[2].data.total,
      retired: statusResults[3].data.total
    }
  } catch {
    // Silent fail - non-critical
  }
}

const loadConfigData = async () => {
  try {
    const [mfRes, mdRes, tpRes, lcRes, spRes, rackRes] = await Promise.all([
      api.get('/inventory/manufacturers/'),
      api.get('/inventory/models/'),
      api.get('/inventory/types/'),
      api.get('/inventory/locations/'),
      api.get('/inventory/suppliers/'),
      api.get('/dcim/racks/')
    ])
    manufacturers.value = mfRes.data
    models.value = mdRes.data
    types.value = tpRes.data
    locations.value = lcRes.data
    suppliers.value = spRes.data
    racks.value = rackRes.data
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Failed to load config data' })
  }
}

const loadAvailableIps = async () => {
  try {
    const res = await api.get('/inventory/available-ips/')
    availableIps.value = res.data
  } catch {
    // Silent fail
  }
}

// ==================== Equipment CRUD ====================
const openEquipmentDetail = (eq) => {
  selectedEquipmentId.value = eq.id
  showDetailSlideOver.value = true
}

const handleEditFromSlideOver = (eq) => {
  showDetailSlideOver.value = false
  openEquipmentDialog(eq)
}

const openEquipmentDialog = (eq = null) => {
  editingEquipment.value = eq
  if (eq) {
    equipmentForm.value = {
      name: eq.name,
      serial_number: eq.serial_number || '',
      asset_tag: eq.asset_tag || '',
      status: eq.status,
      purchase_date: eq.purchase_date ? new Date(eq.purchase_date) : null,
      warranty_expiry: eq.warranty_expiry ? new Date(eq.warranty_expiry) : null,
      notes: eq.notes || '',
      model_id: eq.model_id,
      location_id: eq.location_id,
      supplier_id: eq.supplier_id,
      remote_ip: eq.remote_ip || '',
      os_type: eq.os_type || null,
      connection_type: eq.connection_type || null,
      remote_username: eq.remote_username || '',
      remote_password: '',
      remote_port: eq.remote_port || null,
      rack_id: eq.rack_id || null,
      position_u: eq.position_u || null,
      height_u: eq.height_u || null
    }
  } else {
    equipmentForm.value = {
      name: '', serial_number: '', asset_tag: '', status: 'in_service',
      purchase_date: null, warranty_expiry: null, notes: '',
      model_id: null, location_id: null, supplier_id: null,
      remote_ip: '', os_type: null, connection_type: null,
      remote_username: '', remote_password: '', remote_port: null,
      rack_id: null, position_u: null, height_u: null
    }
  }
  showEquipmentDialog.value = true
}

const saveEquipment = async () => {
  if (!equipmentForm.value.name) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') })
    return
  }
  try {
    const data = { ...equipmentForm.value }
    if (data.purchase_date) {
      const d = data.purchase_date instanceof Date ? data.purchase_date : new Date(data.purchase_date)
      data.purchase_date = d.toISOString()
    }
    if (data.warranty_expiry) {
      const d = data.warranty_expiry instanceof Date ? data.warranty_expiry : new Date(data.warranty_expiry)
      data.warranty_expiry = d.toISOString()
    }

    if (editingEquipment.value) {
      await api.put(`/inventory/equipment/${editingEquipment.value.id}`, data)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.equipmentUpdated') })
    } else {
      await api.post('/inventory/equipment/', data)
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.equipmentCreated') })
    }
    showEquipmentDialog.value = false
    loadEquipment()
    loadEquipmentStats()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

const confirmDeleteEquipment = (eq) => {
  deletingEquipment.value = eq
  showDeleteEquipmentDialog.value = true
}

const deleteEquipment = async () => {
  try {
    await api.delete(`/inventory/equipment/${deletingEquipment.value.id}`)
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('messages.equipmentDeleted') })
    showDeleteEquipmentDialog.value = false
    loadEquipment()
    loadEquipmentStats()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

// ==================== IP Linking ====================
const openLinkIpDialog = async (eq) => {
  linkingEquipment.value = eq
  selectedIpToLink.value = null
  await loadAvailableIps()
  showLinkIpDialog.value = true
}

const linkIp = async () => {
  if (!selectedIpToLink.value) return
  try {
    await api.post(`/inventory/equipment/${linkingEquipment.value.id}/link-ip`, { ip_address_id: selectedIpToLink.value })
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.ipLinked') })
    showLinkIpDialog.value = false
    loadEquipment()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

const unlinkIp = async (ipId) => {
  try {
    await api.delete(`/inventory/equipment/${linkingEquipment.value.id}/unlink-ip/${ipId}`)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.ipUnlinked') })
    const res = await api.get(`/inventory/equipment/${linkingEquipment.value.id}`)
    linkingEquipment.value = res.data
    await loadAvailableIps()
    loadEquipment()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

// ==================== Bulk Operations ====================
const confirmBulkDelete = () => {
  showBulkDeleteDialog.value = true
}

const executeBulkDelete = async () => {
  bulkLoading.value = true
  try {
    const response = await api.post('/inventory/equipment/bulk-delete', {
      equipment_ids: selectedEquipment.value.map(e => e.id)
    })
    const result = response.data
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('inventory.bulkDeleteSuccess', { count: result.processed }) })
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('inventory.bulkDeletePartial', { processed: result.processed, failed: result.failed }) })
    }
    showBulkDeleteDialog.value = false
    showBulkSlideOver.value = false
    selectedEquipment.value = []
    loadEquipment()
    loadEquipmentStats()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  } finally {
    bulkLoading.value = false
  }
}

const applyBulkStatus = async () => {
  if (!bulkStatus.value) return
  bulkLoading.value = true
  try {
    const response = await api.post('/inventory/equipment/bulk-status', {
      equipment_ids: selectedEquipment.value.map(e => e.id),
      status: bulkStatus.value
    })
    const result = response.data
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('inventory.bulkStatusSuccess', { count: result.processed }) })
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('inventory.bulkStatusPartial', { processed: result.processed, failed: result.failed }) })
    }
    bulkStatus.value = null
    selectedEquipment.value = []
    showBulkSlideOver.value = false
    showBulkStatusAction.value = false
    loadEquipment()
    loadEquipmentStats()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  } finally {
    bulkLoading.value = false
  }
}

const applyBulkLocation = async () => {
  if (bulkLocation.value === undefined) return
  bulkLoading.value = true
  try {
    const response = await api.post('/inventory/equipment/bulk-location', {
      equipment_ids: selectedEquipment.value.map(e => e.id),
      location_id: bulkLocation.value
    })
    const result = response.data
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('inventory.bulkLocationSuccess', { count: result.processed }) })
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('inventory.bulkLocationPartial', { processed: result.processed, failed: result.failed }) })
    }
    bulkLocation.value = undefined
    selectedEquipment.value = []
    showBulkSlideOver.value = false
    showBulkLocationAction.value = false
    loadEquipment()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  } finally {
    bulkLoading.value = false
  }
}

// ==================== Configuration CRUD ====================
const openConfigFormDialog = (item = null) => {
  switch (activeTab.value) {
    case 'manufacturers':
      editingManufacturer.value = item
      manufacturerForm.value = item ? { ...item } : { name: '', website: '', notes: '' }
      showManufacturerForm.value = true
      break
    case 'models':
      editingModel.value = item
      modelForm.value = item ? { name: item.name, manufacturer_id: item.manufacturer_id, equipment_type_id: item.equipment_type_id } : { name: '', manufacturer_id: null, equipment_type_id: null }
      showModelForm.value = true
      break
    case 'types':
      editingType.value = item
      typeForm.value = item ? { ...item } : { name: '', icon: 'pi-box', supports_remote_execution: false, hierarchy_level: 3 }
      showTypeForm.value = true
      break
    case 'locations':
      editingLocation.value = item
      locationForm.value = item ? { ...item } : { site: '', building: '', room: '' }
      showLocationForm.value = true
      break
    case 'suppliers':
      editingSupplier.value = item
      supplierForm.value = item ? { ...item } : { name: '', contact_email: '', phone: '', website: '', notes: '' }
      showSupplierForm.value = true
      break
  }
}

// Manufacturers
const saveManufacturer = async () => {
  if (!manufacturerForm.value.name) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') })
    return
  }
  try {
    if (editingManufacturer.value) {
      await api.put(`/inventory/manufacturers/${editingManufacturer.value.id}`, manufacturerForm.value)
    } else {
      await api.post('/inventory/manufacturers/', manufacturerForm.value)
    }
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.saved') })
    showManufacturerForm.value = false
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

const deleteManufacturer = async (id) => {
  if (!confirm(t('common.confirmDeleteItem'))) return
  try {
    await api.delete(`/inventory/manufacturers/${id}`)
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('messages.deleted') })
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('messages.cannotDeleteHasItems') })
  }
}

// Models
const saveModel = async () => {
  if (!modelForm.value.name || !modelForm.value.manufacturer_id || !modelForm.value.equipment_type_id) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') })
    return
  }
  try {
    if (editingModel.value) {
      await api.put(`/inventory/models/${editingModel.value.id}`, modelForm.value)
    } else {
      await api.post('/inventory/models/', modelForm.value)
    }
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.saved') })
    showModelForm.value = false
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

const deleteModel = async (id) => {
  if (!confirm(t('common.confirmDeleteItem'))) return
  try {
    await api.delete(`/inventory/models/${id}`)
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('messages.deleted') })
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('messages.cannotDeleteHasItems') })
  }
}

// Types
const saveType = async () => {
  if (!typeForm.value.name) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') })
    return
  }
  try {
    if (editingType.value) {
      await api.put(`/inventory/types/${editingType.value.id}`, typeForm.value)
    } else {
      await api.post('/inventory/types/', typeForm.value)
    }
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.saved') })
    showTypeForm.value = false
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

const deleteType = async (id) => {
  if (!confirm(t('common.confirmDeleteItem'))) return
  try {
    await api.delete(`/inventory/types/${id}`)
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('messages.deleted') })
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('messages.cannotDeleteHasItems') })
  }
}

// Locations
const saveLocation = async () => {
  if (!locationForm.value.site) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') })
    return
  }
  try {
    if (editingLocation.value) {
      await api.put(`/inventory/locations/${editingLocation.value.id}`, locationForm.value)
    } else {
      await api.post('/inventory/locations/', locationForm.value)
    }
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.saved') })
    showLocationForm.value = false
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

const deleteLocation = async (id) => {
  if (!confirm(t('common.confirmDeleteItem'))) return
  try {
    await api.delete(`/inventory/locations/${id}`)
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('messages.deleted') })
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('messages.cannotDeleteHasItems') })
  }
}

// Suppliers
const saveSupplier = async () => {
  if (!supplierForm.value.name) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') })
    return
  }
  try {
    if (editingSupplier.value) {
      await api.put(`/inventory/suppliers/${editingSupplier.value.id}`, supplierForm.value)
    } else {
      await api.post('/inventory/suppliers/', supplierForm.value)
    }
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('messages.saved') })
    showSupplierForm.value = false
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') })
  }
}

const deleteSupplier = async (id) => {
  if (!confirm(t('common.confirmDeleteItem'))) return
  try {
    await api.delete(`/inventory/suppliers/${id}`)
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('messages.deleted') })
    await loadConfigData()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('messages.cannotDeleteHasItems') })
  }
}

// ==================== Route Handling ====================
const openEquipmentFromUrl = () => {
  const equipmentId = route.query.equipment || route.query.id
  if (equipmentId) {
    selectedEquipmentId.value = parseInt(equipmentId)
    showDetailSlideOver.value = true
    router.replace({ path: route.path })
  }
}

watch(() => [route.query.equipment, route.query.id], ([equipmentQuery, idQuery]) => {
  if (equipmentQuery || idQuery) openEquipmentFromUrl()
})

// ==================== Lifecycle ====================
onMounted(async () => {
  if (route.query.status) filterStatus.value = route.query.status

  openEquipmentFromUrl()

  if (route.query.action === 'create') {
    openEquipmentDialog()
    router.replace({ path: '/inventory', query: {} })
  }

  await Promise.all([
    loadConfigData(),
    loadEquipment(),
    loadEquipmentStats()
  ])
})

onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
    searchTimeout = null
  }
})
</script>

<style scoped>
/* ==================== Page Layout ==================== */
.inventory-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 0.75rem;
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
  margin-bottom: 0.75rem;
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

/* ==================== Navigation Tabs ==================== */
.nav-tabs {
  display: flex;
  gap: 0.125rem;
  overflow-x: auto;
  border-top: 1px solid var(--border-default);
  padding-top: 0.5rem;
  margin-top: 0;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}

.nav-tab:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.nav-tab.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
  font-weight: 600;
}

.nav-tab i {
  font-size: 0.875rem;
}

.nav-tab-count {
  font-size: 0.6875rem;
  font-weight: 700;
  padding: 0.0625rem 0.375rem;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  color: var(--text-muted);
  min-width: 1.25rem;
  text-align: center;
}

.nav-tab.active .nav-tab-count {
  background: rgba(14, 165, 233, 0.15);
  color: var(--primary);
}

/* ==================== Stats Bar ==================== */
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.8125rem;
}

.stat-chip:hover {
  border-color: var(--border-strong);
}

.stat-chip.active {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: white !important;
}

.stat-chip.active .stat-chip-label,
.stat-chip.active .stat-chip-count {
  color: white !important;
}

.stat-chip-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-chip-count {
  color: var(--text-primary);
  font-weight: 700;
}

.stat-chip--in-service:not(.active) { background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.3); }
.stat-chip--in-service:not(.active) .stat-chip-label,
.stat-chip--in-service:not(.active) .stat-chip-count { color: #22c55e; }

.stat-chip--in-stock:not(.active) { background: rgba(59, 130, 246, 0.12); border-color: rgba(59, 130, 246, 0.3); }
.stat-chip--in-stock:not(.active) .stat-chip-label,
.stat-chip--in-stock:not(.active) .stat-chip-count { color: #3b82f6; }

.stat-chip--maintenance:not(.active) { background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3); }
.stat-chip--maintenance:not(.active) .stat-chip-label,
.stat-chip--maintenance:not(.active) .stat-chip-count { color: #f59e0b; }

.stat-chip--retired:not(.active) { background: rgba(100, 116, 139, 0.12); border-color: rgba(100, 116, 139, 0.3); }
.stat-chip--retired:not(.active) .stat-chip-label,
.stat-chip--retired:not(.active) .stat-chip-count { color: #64748b; }

/* ==================== Toolbar ==================== */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: clamp(0.75rem, 3vw, 2rem);
  padding: 0.625rem clamp(1rem, 2vw, 1.5rem);
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

.toolbar-separator {
  width: 1px;
  height: 28px;
  background: var(--border-default);
  flex-shrink: 0;
}

.toolbar-filter {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.filter-label {
  font-size: 0.875rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.toolbar .toolbar-filter :deep(.p-dropdown),
.toolbar .toolbar-filter :deep(.p-dropdown.p-component) {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  min-width: 80px;
  position: relative;
  padding: 0 !important;
}

.toolbar .toolbar-filter :deep(.p-dropdown.p-focus),
.toolbar .toolbar-filter :deep(.p-dropdown:focus),
.toolbar .toolbar-filter :deep(.p-dropdown:hover),
.toolbar .toolbar-filter :deep(.p-dropdown.p-component:hover),
.toolbar .toolbar-filter :deep(.p-dropdown.p-component.p-focus) {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

.toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-label) {
  padding: 0.375rem 3.5rem 0.375rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  background: transparent !important;
}

.toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-label.p-placeholder) {
  color: var(--text-secondary);
  padding: 0.375rem 3.5rem 0.375rem 0.75rem !important;
}

.toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-trigger) {
  position: absolute;
  right: 1.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: auto;
  color: var(--text-muted);
  background: transparent !important;
}

.toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-clear-icon) {
  position: absolute;
  right: 0.5rem;
  top: 0;
  bottom: 0;
  margin: auto;
  height: fit-content;
  color: var(--text-muted);
  font-size: 0.875rem;
  cursor: pointer;
}

.toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-clear-icon:hover) {
  color: var(--primary);
}

.toolbar-spacer {
  flex: 1;
  min-width: 2rem;
}

.toolbar-selection {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  flex-shrink: 0;
}

.selection-count {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--primary);
  white-space: nowrap;
}

/* ==================== List Container ==================== */
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
  gap: 0.75rem;
  padding: 3rem 2rem;
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

.tickets-header.inventory-header {
  display: grid;
  grid-template-columns: 32px 1fr 200px 160px 100px 80px 24px;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1.25rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  position: sticky;
  top: 0;
  z-index: 1;
}

.header-checkbox {
  width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
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

.header-col--sortable i {
  font-size: 0.625rem;
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

.ticket-row.inventory-row {
  display: grid;
  grid-template-columns: 32px 1fr 200px 160px 100px 80px 24px;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1.25rem;
  border-bottom: 1px solid var(--border-default);
  cursor: pointer;
  transition: background 0.15s ease;
}

.inventory-row:last-child {
  border-bottom: none;
}

.inventory-row:hover {
  background: var(--bg-hover);
}

.ticket-row--selected {
  background: rgba(14, 165, 233, 0.06);
}

.ticket-checkbox {
  width: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ticket-info {
  display: flex;
  flex-direction: column;
  gap: 0.0625rem;
  min-width: 0;
}

.ticket-title {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ticket-type-label {
  font-size: 0.6875rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.inventory-model-cell {
  min-width: 0;
}

.model-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.inventory-location-cell {
  min-width: 0;
}

.location-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.text-muted {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.ticket-tags {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.inventory-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.ticket-arrow {
  color: var(--text-muted);
  font-size: 0.75rem;
  transition: transform 0.15s ease, color 0.15s ease;
}

.inventory-row:hover .ticket-arrow {
  transform: translateX(3px);
  color: var(--primary);
}

/* ==================== Pagination ==================== */
.pagination {
  display: flex;
  justify-content: center;
  padding: 0.375rem 0.75rem;
  border-top: 1px solid var(--border-default);
}

/* ==================== Config Grid ==================== */
.config-grid-header {
  display: grid;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1.25rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.025em;
  position: sticky;
  top: 0;
  z-index: 1;
}

.config-grid-row {
  display: grid;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1.25rem;
  border-bottom: 1px solid var(--border-default);
  transition: background 0.15s ease;
}

.config-grid-row:last-child {
  border-bottom: none;
}

.config-grid-row:hover {
  background: var(--bg-hover);
}

/* Manufacturer grid */
.config-grid--manufacturer {
  grid-template-columns: 1fr 200px 1fr 80px;
}

/* Model grid */
.config-grid--model {
  grid-template-columns: 1fr 180px 140px 80px;
}

/* Type grid */
.config-grid--type {
  grid-template-columns: 1fr 120px 160px 100px 80px;
}

/* Location grid */
.config-grid--location {
  grid-template-columns: 1fr 160px 160px 80px;
}

/* Supplier grid */
.config-grid--supplier {
  grid-template-columns: 1fr 200px 140px 180px 80px;
}

.config-cell-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  min-width: 0;
}

.config-cell-name span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.config-cell-icon {
  color: var(--primary);
  font-size: 0.875rem;
  flex-shrink: 0;
}

.config-cell-detail {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.config-cell-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.config-link {
  color: var(--primary);
  text-decoration: none;
  font-size: 0.8125rem;
}

.config-link:hover {
  text-decoration: underline;
}

.config-notes-preview {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.icon-code {
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-family: monospace;
}

.hierarchy-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  font-size: 0.6875rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
  margin-right: 0.375rem;
}

.hierarchy-label {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

/* ==================== Modal Sections ==================== */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-section {
  padding-top: 1rem;
  border-top: 1px solid var(--border-default);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 0.75rem;
}

.section-title .required {
  color: #ef4444;
  font-weight: normal;
}

.required {
  color: #ef4444;
}

.modal-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* ==================== Info Grid (matches Tickets pattern) ==================== */
.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

@media (min-width: 768px) {
  .detail-info-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.detail-info-grid--form {
  grid-template-columns: repeat(2, 1fr);
}

@media (min-width: 768px) {
  .detail-info-grid--form {
    grid-template-columns: repeat(3, 1fr);
  }
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ==================== Form Input Styling (matches Tickets) ==================== */
.form-input-full {
  width: 100%;
}

.form-input-full.p-inputtext,
.form-input-full.p-textarea {
  width: 100%;
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-lg) !important;
  padding: 0.75rem 1rem !important;
  font-size: 0.875rem;
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.form-input-full.p-inputtext:focus,
.form-input-full.p-textarea:focus {
  box-shadow: 0 0 0 2px var(--ring-color) !important;
}

.form-input-full.p-inputtext::placeholder,
.form-input-full.p-textarea::placeholder {
  color: var(--text-muted);
}

/* ==================== Info Dropdown (matches Tickets) ==================== */
.info-dropdown.p-dropdown,
.info-item :deep(.info-dropdown) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  padding: 0 !important;
  min-width: 0;
  width: 100%;
  position: relative;
}

.info-item :deep(.info-dropdown.p-focus),
.info-item :deep(.info-dropdown:hover) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.info-item :deep(.info-dropdown .p-dropdown-label) {
  padding: 0.25rem 3rem 0.25rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  background: transparent !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-item :deep(.info-dropdown .p-dropdown-label.p-placeholder) {
  color: var(--text-secondary);
}

.info-item :deep(.info-dropdown .p-dropdown-trigger) {
  position: absolute;
  right: 1.25rem;
  top: 0;
  bottom: 0;
  margin: auto;
  height: fit-content;
  width: auto;
  color: var(--text-muted);
}

.info-item :deep(.info-dropdown .p-dropdown-clear-icon) {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  margin: auto;
  height: fit-content;
  color: var(--text-muted);
  font-size: 0.75rem;
}

.info-item :deep(.info-dropdown .p-dropdown-clear-icon:hover) {
  color: var(--primary);
}

/* Calendar & InputNumber within info-item (match transparent style) */
.info-item :deep(.p-calendar) {
  width: 100%;
}

.info-item :deep(.p-calendar .p-inputtext) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.info-item :deep(.p-calendar .p-inputtext:focus) {
  box-shadow: none !important;
}

.info-item :deep(.p-calendar .p-datepicker-trigger) {
  background: transparent !important;
  border: none !important;
  color: var(--text-muted);
}

.info-item :deep(.p-inputnumber) {
  width: 100%;
}

.info-item :deep(.p-inputnumber .p-inputtext) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.info-item :deep(.p-inputnumber .p-inputtext:focus) {
  box-shadow: none !important;
}

.info-item :deep(.p-password) {
  width: 100%;
}

.info-item :deep(.p-password .p-inputtext) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  width: 100%;
}

/* InputText within info-item grid (transparent) */
.info-item :deep(.p-inputtext:not(.form-input-full)) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0.25rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.info-item :deep(.p-inputtext:not(.form-input-full):focus) {
  box-shadow: none !important;
}

.info-item :deep(.p-inputtext:not(.form-input-full))::placeholder {
  color: var(--text-secondary);
}

/* ==================== Form Fields in Grid (visible field appearance) ==================== */
/* Override bg-secondary blending: form controls inside info-grid get bg-card + border */

.detail-info-grid--form .info-item .form-input-full.p-inputtext {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: 0.5rem 0.75rem !important;
}

.detail-info-grid--form .info-item .form-input-full.p-inputtext:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 2px var(--ring-color) !important;
}

.detail-info-grid--form .info-item .form-input-full.p-inputtext::placeholder {
  color: var(--text-muted);
}

.detail-info-grid--form .info-item :deep(.info-dropdown) {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
}

.detail-info-grid--form .info-item :deep(.info-dropdown.p-focus),
.detail-info-grid--form .info-item :deep(.info-dropdown:hover) {
  border-color: var(--primary) !important;
}

.detail-info-grid--form .info-item :deep(.info-dropdown .p-dropdown-label) {
  padding: 0.5rem 3rem 0.5rem 0.75rem !important;
}

.detail-info-grid--form .info-item :deep(.p-calendar) {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.detail-info-grid--form .info-item :deep(.p-inputnumber) {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.detail-info-grid--form .info-item :deep(.p-password) {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.detail-info-grid--form .info-item :deep(.p-calendar .p-inputtext),
.detail-info-grid--form .info-item :deep(.p-inputnumber .p-inputtext),
.detail-info-grid--form .info-item :deep(.p-password .p-inputtext) {
  padding: 0.5rem 0.75rem !important;
}

.detail-info-grid--form .info-item :deep(.p-calendar:hover),
.detail-info-grid--form .info-item :deep(.p-inputnumber:hover),
.detail-info-grid--form .info-item :deep(.p-password:hover) {
  border-color: var(--border-strong);
}

/* ==================== Bulk Action Cards ==================== */
.action-card {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-default);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-bottom: 0.75rem;
}

.action-card:hover {
  border-color: var(--border-strong);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
  background-color: var(--bg-hover);
}

.action-card-danger:hover {
  border-color: var(--danger);
  background-color: var(--danger-light);
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

.action-icon-danger { background: var(--danger-light); }
.action-icon-danger i { color: var(--danger); }

.action-card .action-title { color: var(--text-primary); }
.action-card .action-desc { color: var(--text-secondary); }

.action-card i.pi-chevron-up,
.action-card i.pi-chevron-down,
.action-card i.pi-chevron-right {
  color: var(--text-secondary);
}

/* ==================== Dropdown Panel Overlay ==================== */
:deep(.p-dropdown-panel) {
  min-width: 180px !important;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-default);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

:deep(.p-dropdown-panel .p-dropdown-items) {
  padding: 0.25rem;
}

:deep(.p-dropdown-panel .p-dropdown-item) {
  padding: 0.5rem 0.75rem;
  font-size: 0.8125rem;
  border-radius: var(--radius-md);
  margin: 0.125rem 0;
}

:deep(.p-dropdown-panel .p-dropdown-item:hover) {
  background: var(--bg-hover);
}

:deep(.p-dropdown-panel .p-dropdown-item.p-highlight) {
  background: var(--primary-light);
  color: var(--primary);
}

/* Toolbar dark mode dropdown label */
:root.dark .toolbar-filter :deep(.p-dropdown .p-dropdown-label) {
  color: #e2e8f0;
}

:root.dark .toolbar-filter :deep(.p-dropdown .p-dropdown-label.p-placeholder) {
  color: #94a3b8;
}

:root.dark .toolbar-filter :deep(.p-dropdown .p-dropdown-trigger),
:root.dark .toolbar-filter :deep(.p-dropdown .p-dropdown-clear-icon) {
  color: #64748b;
}

/* Dark mode dropdown panel */
:root.dark :deep(.p-dropdown-panel) {
  background: var(--bg-card-solid);
  border-color: var(--border-default);
}

:root.dark :deep(.p-dropdown-panel .p-dropdown-item) {
  color: #e2e8f0;
}

:root.dark :deep(.p-dropdown-panel .p-dropdown-item:hover) {
  background: rgba(255, 255, 255, 0.06);
}

:root.dark :deep(.p-dropdown-panel .p-dropdown-item.p-highlight) {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
}

/* ==================== Dark Mode ==================== */
:root.dark .page-header,
:root.dark .toolbar,
:root.dark .tickets-container {
  background: var(--bg-card-solid);
  border-color: var(--border-default);
}
:root.dark .page-title { color: #f1f5f9; }
:root.dark .page-subtitle { color: #94a3b8; border-color: rgba(255,255,255,0.1); }

:root.dark .nav-tab { color: #94a3b8; }
:root.dark .nav-tab:hover { color: #e2e8f0; background: rgba(255,255,255,0.03); }
:root.dark .nav-tab.active { color: #38bdf8; border-bottom-color: #38bdf8; }
:root.dark .nav-tab-count { background: rgba(255,255,255,0.06); color: #64748b; }
:root.dark .nav-tab.active .nav-tab-count { background: rgba(56, 189, 248, 0.15); color: #38bdf8; }

:root.dark .stat-chip:not(.active) { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.08); }
:root.dark .stat-chip-label { color: #94a3b8; }
:root.dark .stat-chip-count { color: #e2e8f0; }

:root.dark .stat-chip--in-service:not(.active) { background: rgba(34, 197, 94, 0.15); border-color: rgba(34, 197, 94, 0.35); }
:root.dark .stat-chip--in-service:not(.active) .stat-chip-label,
:root.dark .stat-chip--in-service:not(.active) .stat-chip-count { color: #4ade80; }

:root.dark .stat-chip--in-stock:not(.active) { background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.35); }
:root.dark .stat-chip--in-stock:not(.active) .stat-chip-label,
:root.dark .stat-chip--in-stock:not(.active) .stat-chip-count { color: #60a5fa; }

:root.dark .stat-chip--maintenance:not(.active) { background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.35); }
:root.dark .stat-chip--maintenance:not(.active) .stat-chip-label,
:root.dark .stat-chip--maintenance:not(.active) .stat-chip-count { color: #fbbf24; }

:root.dark .stat-chip--retired:not(.active) { background: rgba(100, 116, 139, 0.15); border-color: rgba(100, 116, 139, 0.35); }
:root.dark .stat-chip--retired:not(.active) .stat-chip-label,
:root.dark .stat-chip--retired:not(.active) .stat-chip-count { color: #94a3b8; }

:root.dark .toolbar-search i { color: #64748b; }

:root.dark .inventory-header,
:root.dark .config-grid-header { background: rgba(0,0,0,0.2); border-color: rgba(255,255,255,0.06); color: #64748b; }
:root.dark .inventory-row,
:root.dark .config-grid-row { border-color: rgba(255,255,255,0.06); }
:root.dark .inventory-row:hover,
:root.dark .config-grid-row:hover { background: rgba(255,255,255,0.03); }
:root.dark .ticket-row--selected { background: rgba(14, 165, 233, 0.08); }
:root.dark .ticket-title { color: #f1f5f9; }
:root.dark .ticket-type-label { color: #64748b; }
:root.dark .model-text { color: #94a3b8; }
:root.dark .location-text { color: #94a3b8; }
:root.dark .ticket-arrow { color: #64748b; }

:root.dark .config-cell-name { color: #f1f5f9; }
:root.dark .config-cell-detail { color: #94a3b8; }
:root.dark .config-link { color: #38bdf8; }
:root.dark .icon-code { background: rgba(255,255,255,0.06); color: #94a3b8; }
:root.dark .hierarchy-label { color: #94a3b8; }

:root.dark .empty-state h3 { color: #f1f5f9; }
:root.dark .empty-state p { color: #94a3b8; }
:root.dark .loading-state span { color: #94a3b8; }

/* Dark mode modal sections */
:root.dark .detail-info-grid {
  background: rgba(255, 255, 255, 0.03);
}

:root.dark .info-label {
  color: #64748b;
}

:root.dark .info-item :deep(.info-dropdown .p-dropdown-label) {
  color: #e2e8f0;
}

:root.dark .info-item :deep(.info-dropdown .p-dropdown-label.p-placeholder) {
  color: #94a3b8;
}

:root.dark .info-item :deep(.info-dropdown .p-dropdown-trigger),
:root.dark .info-item :deep(.info-dropdown .p-dropdown-clear-icon) {
  color: #64748b;
}

:root.dark .form-input-full.p-inputtext,
:root.dark .form-input-full.p-textarea {
  background: rgba(255, 255, 255, 0.03) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #f1f5f9;
}

:root.dark .section-title {
  color: #38bdf8;
}

/* Dark mode form fields in grid */
:root.dark .detail-info-grid--form .info-item .form-input-full.p-inputtext {
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #f1f5f9;
}

:root.dark .detail-info-grid--form .info-item :deep(.info-dropdown) {
  background: rgba(255, 255, 255, 0.06) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

:root.dark .detail-info-grid--form .info-item :deep(.p-calendar),
:root.dark .detail-info-grid--form .info-item :deep(.p-inputnumber),
:root.dark .detail-info-grid--form .info-item :deep(.p-password) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
}

:root.dark .detail-info-grid--form .info-item .form-input-full.p-inputtext:focus,
:root.dark .detail-info-grid--form .info-item :deep(.info-dropdown.p-focus) {
  border-color: #38bdf8 !important;
}

/* ==================== Responsive ==================== */
@media (max-width: 1024px) {
  .tickets-header.inventory-header { display: none; }
  .ticket-row.inventory-row {
    grid-template-columns: 32px 1fr auto;
    grid-template-rows: auto auto;
    gap: 0.5rem 1rem;
    padding: 1rem 1.25rem;
  }
  .inventory-row .ticket-checkbox { grid-row: 1 / 3; grid-column: 1; align-self: center; }
  .inventory-row .ticket-info { grid-row: 1; grid-column: 2; }
  .inventory-row .inventory-model-cell { display: none; }
  .inventory-row .inventory-location-cell { display: none; }
  .inventory-row .ticket-tags { grid-row: 1; grid-column: 3; }
  .inventory-row .inventory-actions { grid-row: 2; grid-column: 3; }
  .inventory-row .ticket-arrow { display: none; }

  .config-grid-header { display: none; }
  .config-grid-row {
    grid-template-columns: 1fr auto !important;
    gap: 0.5rem 1rem;
  }
  .config-grid-row .config-cell-detail { display: none; }
  .config-grid-row .config-cell-actions { grid-column: 2; }

  .nav-tabs {
    gap: 0;
    -webkit-overflow-scrolling: touch;
  }
  .nav-tab {
    padding: 0.5rem 0.625rem;
    font-size: 0.75rem;
  }
  .nav-tab-count { display: none; }
}
</style>
