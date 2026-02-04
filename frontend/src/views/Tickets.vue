<template>
  <div class="tickets-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title-section">
          <h1 class="page-title">
            <i class="pi pi-ticket"></i>
            {{ t('tickets.title') }}
          </h1>
          <p class="page-subtitle">{{ stats.total }} {{ t('tickets.totalTickets') }}</p>
        </div>
        <Button :label="t('tickets.newTicket')" icon="pi pi-plus" @click="openTicketDialog()" class="create-btn" />
      </div>

      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="stat-chip" :class="{ active: filters.status === null }" @click="setFilter('status', null)">
          <span class="stat-chip-label">{{ t('tickets.allTickets') }}</span>
          <span class="stat-chip-count">{{ stats.total }}</span>
        </div>
        <div class="stat-chip stat-chip--new" :class="{ active: filters.status === 'new' }" @click="setFilter('status', 'new')">
          <span class="stat-chip-label">{{ t('tickets.statusNew') }}</span>
          <span class="stat-chip-count">{{ stats.new }}</span>
        </div>
        <div class="stat-chip stat-chip--open" :class="{ active: filters.status === 'open' }" @click="setFilter('status', 'open')">
          <span class="stat-chip-label">{{ t('tickets.statusOpen') }}</span>
          <span class="stat-chip-count">{{ stats.open }}</span>
        </div>
        <div class="stat-chip stat-chip--pending" :class="{ active: filters.status === 'pending' }" @click="setFilter('status', 'pending')">
          <span class="stat-chip-label">{{ t('tickets.statusPending') }}</span>
          <span class="stat-chip-count">{{ stats.pending }}</span>
        </div>
        <div class="stat-chip stat-chip--resolved" :class="{ active: filters.status === 'resolved' }" @click="setFilter('status', 'resolved')">
          <span class="stat-chip-label">{{ t('tickets.statusResolved') }}</span>
          <span class="stat-chip-count">{{ stats.resolved }}</span>
        </div>
        <div class="stat-chip stat-chip--closed" :class="{ active: filters.status === 'closed' }" @click="setFilter('status', 'closed')">
          <span class="stat-chip-label">{{ t('tickets.statusClosed') }}</span>
          <span class="stat-chip-count">{{ stats.closed || 0 }}</span>
        </div>
        <div v-if="stats.sla_breached > 0" class="stat-chip stat-chip--danger">
          <i class="pi pi-exclamation-triangle"></i>
          <span class="stat-chip-count">{{ stats.sla_breached }} SLA</span>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="toolbar">
      <div class="toolbar-search">
        <i class="pi pi-search"></i>
        <InputText v-model="filters.search" :placeholder="t('tickets.search')" @input="debouncedSearch" />
      </div>

      <span class="toolbar-separator"></span>

      <div class="toolbar-filter">
        <span class="filter-label">{{ t('tickets.priority') }}</span>
        <Dropdown v-model="filters.priority" :options="priorityOptions" optionLabel="label" optionValue="value"
                  :placeholder="t('common.all')" showClear @change="loadTickets" />
      </div>

      <div class="toolbar-filter">
        <span class="filter-label">{{ t('tickets.type') }}</span>
        <Dropdown v-model="filters.ticket_type" :options="typeOptions" optionLabel="label" optionValue="value"
                  :placeholder="t('common.all')" showClear @change="loadTickets" />
      </div>

      <span class="toolbar-separator"></span>

      <label class="my-tickets-toggle">
        <Checkbox v-model="filters.my_tickets" :binary="true" @change="loadTickets" />
        <span>{{ t('tickets.myTickets') }}</span>
      </label>

      <div class="toolbar-spacer"></div>

      <div v-if="selectedTickets.length > 0 && canManageTickets" class="toolbar-selection">
        <span class="selection-count">{{ selectedTickets.length }} {{ t('common.selected') }}</span>
        <Button icon="pi pi-list-check" :label="t('bulk.openBulkActions')" size="small" @click="showBulkSlideOver = true" />
        <Button icon="pi pi-times" text rounded size="small" @click="selectedTickets = []" />
      </div>
    </div>

    <!-- Tickets List -->
    <div class="tickets-container">
      <div v-if="loading" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i>
        <span>{{ t('common.loading') }}</span>
      </div>

      <div v-else-if="tickets.length === 0" class="empty-state">
        <i class="pi pi-inbox"></i>
        <h3>{{ t('tickets.noTickets') }}</h3>
        <p>{{ t('tickets.noTicketsDesc') }}</p>
        <Button :label="t('tickets.newTicket')" icon="pi pi-plus" @click="openTicketDialog()" />
      </div>

      <div v-else class="tickets-list">
        <!-- Table Header -->
        <div class="tickets-header">
          <div v-if="canManageTickets" class="header-checkbox" @click.stop>
            <Checkbox
              :modelValue="allPageTicketsSelected"
              :binary="true"
              @update:modelValue="toggleSelectAllPage"
              :indeterminate="somePageTicketsSelected"
              v-tooltip.top="allPageTicketsSelected ? t('common.deselectAll') : t('common.selectAllOnPage')"
            />
          </div>
          <span class="header-col header-col--sortable" @click="toggleSort('ticket_number')">
            {{ t('tickets.ticketNumber') }}
            <i v-if="sortField === 'ticket_number'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
          </span>
          <span class="header-col header-col--title">{{ t('tickets.ticketTitle') }}</span>
          <span class="header-col">{{ t('tickets.status') }}</span>
          <span class="header-col header-col--sortable" @click="toggleSort('assigned_to_id')">
            {{ t('tickets.assignedTo') }}
            <i v-if="sortField === 'assigned_to_id'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
          </span>
          <span class="header-col header-col--sortable" @click="toggleSort('created_at')">
            {{ t('tickets.createdAt') }}
            <i v-if="sortField === 'created_at'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
          </span>
          <span class="header-col--arrow"></span>
        </div>

        <!-- Tickets Rows -->
        <div v-for="ticket in tickets" :key="ticket.id"
             class="ticket-row"
             :class="{ 'ticket-row--selected': isTicketSelected(ticket.id) }"
             @click="openTicketDetail({ data: ticket })">

          <div v-if="canManageTickets" class="ticket-checkbox" @click.stop>
            <Checkbox :modelValue="isTicketSelected(ticket.id)" :binary="true" @update:modelValue="toggleTicketSelection(ticket)" />
          </div>

          <span class="ticket-number">{{ ticket.ticket_number }}</span>

          <div class="ticket-info">
            <span class="ticket-title">{{ ticket.title }}</span>
            <span class="ticket-type-label">{{ t(`tickets.type${capitalize(ticket.ticket_type)}`) }}</span>
          </div>

          <div class="ticket-tags">
            <Tag :value="t(`tickets.status${capitalize(ticket.status)}`)" :severity="getStatusSeverity(ticket.status)" />
            <Tag :value="t(`tickets.priority${capitalize(ticket.priority)}`)" :severity="getPrioritySeverity(ticket.priority)" />
          </div>

          <div class="ticket-users">
            <span class="ticket-user">
              <i class="pi pi-user"></i>
              {{ ticket.requester_name || '-' }}
            </span>
            <span class="ticket-assignee" :class="{ 'unassigned': !ticket.assigned_to_name }">
              <i class="pi pi-arrow-right"></i>
              {{ ticket.assigned_to_name || t('tickets.unassigned') }}
            </span>
          </div>

          <span class="ticket-date">{{ formatDateTime(ticket.created_at) }}</span>

          <i class="pi pi-chevron-right ticket-arrow"></i>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="ticketsTotal > 0" class="pagination">
        <Paginator
          :rows="ticketsRows"
          :totalRecords="ticketsTotal"
          :first="ticketsFirst"
          :rowsPerPageOptions="[10, 15, 25, 50]"
          @page="onTicketsPage"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
        />
      </div>
    </div>

    <!-- Create/Edit Ticket Modal -->
    <ModalPanel v-model="showTicketDialog"
                :title="editingTicket ? t('tickets.editTicket') : t('tickets.newTicket')"
                icon="pi-ticket"
                size="xl">
      <div class="detail-content">
        <!-- Info Grid with dropdowns -->
        <div class="detail-info-grid detail-info-grid--form">
          <div class="info-item">
            <span class="info-label">{{ t('tickets.ticketType') }}</span>
            <Dropdown v-model="ticketForm.ticket_type" :options="typeOptions" optionLabel="label" optionValue="value" class="info-dropdown" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('tickets.category') }}</span>
            <Dropdown v-model="ticketForm.category" :options="categoryOptions" optionLabel="label" optionValue="value"
                      showClear :placeholder="t('common.select')" class="info-dropdown" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('tickets.impact') }}</span>
            <Dropdown v-model="ticketForm.impact" :options="impactOptions" optionLabel="label" optionValue="value" class="info-dropdown" />
          </div>
          <div v-if="canManageTickets" class="info-item">
            <span class="info-label">{{ t('tickets.ticketPriority') }}</span>
            <Dropdown v-model="ticketForm.priority" :options="priorityOptions" optionLabel="label" optionValue="value" class="info-dropdown" />
          </div>
          <div v-if="canManageTickets" class="info-item">
            <span class="info-label">{{ t('tickets.assignTo') }}</span>
            <Dropdown v-model="ticketForm.assigned_to_id" :options="users" optionLabel="username" optionValue="id"
                      showClear :placeholder="t('tickets.selectUser')" class="info-dropdown" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('tickets.relatedEquipment') }}</span>
            <Dropdown v-model="ticketForm.equipment_id" :options="equipment" optionLabel="name" optionValue="id"
                      showClear :placeholder="t('tickets.selectEquipment')" filter class="info-dropdown" />
          </div>
        </div>

        <!-- Title Section -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-tag"></i>
            {{ t('tickets.ticketTitle') }} <span class="required">*</span>
          </h4>
          <InputText v-model="ticketForm.title" :placeholder="t('tickets.ticketTitlePlaceholder')" class="form-input-full" />
        </div>

        <!-- Description Section with Rich Text Editor -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-align-left"></i>
            {{ t('tickets.description') }} <span class="required">*</span>
          </h4>
          <RichTextEditor
            v-model="ticketForm.description"
            :placeholder="t('tickets.descriptionPlaceholder')"
            :max-length="50000"
            min-height="150px"
            @image-upload="handleDescriptionImageUpload"
          />
        </div>

        <!-- Attachments Section with Drag & Drop -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-paperclip"></i>
            {{ t('tickets.attachments') }}
          </h4>
          <FileDropZone
            v-model="ticketAttachments"
            :multiple="true"
            accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar"
            :max-size="10485760"
            :max-files="5"
            @error="handleAttachmentError"
          />
        </div>
      </div>

      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showTicketDialog = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveTicket" :loading="saving" />
        </div>
      </template>
    </ModalPanel>

    <!-- Ticket Detail Modal -->
    <ModalPanel v-model="showDetailDialog"
                :title="currentTicket?.title"
                :subtitle="currentTicket?.ticket_number"
                icon="pi-ticket"
                size="xl"
                @content-ready="onDetailModalReady">
      <div v-if="currentTicket && detailContentReady" class="detail-content">
        <!-- Status Tags -->
        <div class="detail-tags">
          <Tag :value="t(`tickets.status${capitalize(currentTicket.status)}`)"
               :severity="getStatusSeverity(currentTicket.status)" />
          <Tag :value="t(`tickets.priority${capitalize(currentTicket.priority)}`)"
               :severity="getPrioritySeverity(currentTicket.priority)" />
          <Tag :value="t(`tickets.type${capitalize(currentTicket.ticket_type)}`)" severity="secondary" />
        </div>

        <!-- Info Grid -->
        <div class="detail-info-grid">
          <div class="info-item">
            <span class="info-label">{{ t('tickets.requester') }}</span>
            <span class="info-value">{{ currentTicket.requester_name || '-' }}</span>
          </div>
          <div v-if="canManageTickets" class="info-item">
            <span class="info-label">{{ t('tickets.assignedTo') }}</span>
            <div class="info-value-with-action">
              <span>{{ currentTicket.assigned_to_name || t('tickets.unassigned') }}</span>
              <Button icon="pi pi-pencil" text rounded size="small" @click="showAssignDialog = true" />
            </div>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('tickets.createdAt') }}</span>
            <span class="info-value">{{ formatDateTime(currentTicket.created_at) }}</span>
          </div>
          <div v-if="currentTicket.sla_due_date" class="info-item">
            <span class="info-label">{{ t('tickets.slaDue') }}</span>
            <span class="info-value" :class="{ 'text-red-400': new Date(currentTicket.sla_due_date) < new Date() }">
              {{ formatDateTime(currentTicket.sla_due_date) }}
            </span>
          </div>
          <div v-if="currentTicket.equipment_name" class="info-item">
            <span class="info-label">{{ t('tickets.relatedEquipment') }}</span>
            <span class="info-value">{{ currentTicket.equipment_name }}</span>
          </div>
          <div v-if="currentTicket.category" class="info-item">
            <span class="info-label">{{ t('tickets.category') }}</span>
            <span class="info-value">{{ currentTicket.category }}</span>
          </div>
        </div>

        <!-- Description -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-align-left"></i>
            {{ t('tickets.description') }}
          </h4>
          <div class="description-box" v-html="sanitizeHtml(currentTicket.description)"></div>
        </div>

        <!-- Resolution -->
        <div v-if="currentTicket.resolution" class="detail-section">
          <h4 class="section-title section-title--success">
            <i class="pi pi-check-circle"></i>
            {{ t('tickets.resolution') }}
          </h4>
          <div class="resolution-box" v-html="sanitizeHtml(currentTicket.resolution)"></div>
        </div>

        <!-- Conversation -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-comments"></i>
            {{ t('tickets.conversation') }} ({{ currentTicket.comments?.length || 0 }})
          </h4>
          <div class="conversation-container">
            <template v-for="comment in sortedComments" :key="comment.id">
              <div v-if="canManageTickets || !comment.is_internal"
                   class="message"
                   :class="{
                     'message--requester': isRequesterComment(comment),
                     'message--tech': !isRequesterComment(comment),
                     'message--internal': comment.is_internal
                   }">
                <div class="message-avatar">
                  <img v-if="comment.user_avatar" :src="`/api/v1/avatars/${comment.user_avatar}`" alt="">
                  <span v-else>{{ getInitials(comment.username) }}</span>
                </div>
                <div class="message-bubble">
                  <div class="message-header">
                    <span class="message-author">{{ comment.username || 'System' }}</span>
                    <Tag v-if="comment.is_internal" :value="t('tickets.internalNote')" severity="warning" class="message-tag" />
                    <span class="message-time">{{ formatDateTime(comment.created_at) }}</span>
                  </div>
                  <div class="message-content" v-html="sanitizeHtml(comment.content)"></div>
                </div>
              </div>
            </template>
            <div v-if="!currentTicket.comments?.length" class="conversation-empty">
              <i class="pi pi-comments"></i>
              <span>{{ t('tickets.noComments') }}</span>
              <p>{{ t('tickets.startConversation') }}</p>
            </div>
          </div>

          <!-- Add Reply -->
          <div class="reply-section">
            <!-- Ticket closed/resolved - show reopen message -->
            <div v-if="currentTicket.status === 'resolved' || currentTicket.status === 'closed'" class="reply-closed">
              <i class="pi pi-lock"></i>
              <span>{{ t('tickets.replyClosed') }}</span>
              <Button v-if="canManageTickets" :label="t('tickets.reopen')" icon="pi pi-refresh" size="small" severity="secondary" outlined @click="reopenCurrentTicket" />
            </div>
            <!-- Normal reply form -->
            <template v-else>
              <div class="reply-header">
                <i class="pi pi-reply"></i>
                <span>{{ t('tickets.writeReply') }}</span>
              </div>
              <RichTextEditor
                v-model="newComment"
                :placeholder="t('tickets.replyPlaceholder')"
                min-height="100px"
                :max-length="50000"
              />
              <div class="reply-actions">
                <div v-if="canManageTickets" class="internal-toggle">
                  <Checkbox v-model="commentInternal" :binary="true" inputId="internal" />
                  <label for="internal">
                    <i class="pi pi-lock"></i>
                    {{ t('tickets.internalNote') }}
                  </label>
                </div>
                <div v-else></div>
                <Button :label="t('tickets.sendReply')" icon="pi pi-send" size="small"
                        @click="postComment" :disabled="!newCommentHasContent" />
              </div>
            </template>
          </div>
        </div>

        <!-- History -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-history"></i>
            {{ t('tickets.history') }}
          </h4>
          <div class="history-list">
            <div v-for="item in currentTicket.history" :key="item.id" class="history-item">
              <i class="pi pi-circle-fill"></i>
              <span class="history-time">{{ formatDateTime(item.created_at) }}</span>
              <span class="history-user">{{ item.username || 'System' }}</span>
              <span class="history-action">{{ formatHistoryAction(item) }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- Loading skeleton while fetching full ticket data -->
      <div v-else class="detail-skeleton">
        <div class="flex gap-2 mb-4">
          <Skeleton width="5rem" height="1.5rem" borderRadius="9999px" />
          <Skeleton width="4rem" height="1.5rem" borderRadius="9999px" />
          <Skeleton width="5rem" height="1.5rem" borderRadius="9999px" />
        </div>
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div><Skeleton height="1rem" class="mb-2" /><Skeleton width="60%" /></div>
          <div><Skeleton height="1rem" class="mb-2" /><Skeleton width="70%" /></div>
          <div><Skeleton height="1rem" class="mb-2" /><Skeleton width="50%" /></div>
          <div><Skeleton height="1rem" class="mb-2" /><Skeleton width="40%" /></div>
        </div>
        <Skeleton height="1.5rem" width="8rem" class="mb-3" />
        <Skeleton height="6rem" class="mb-6" />
        <Skeleton height="1.5rem" width="10rem" class="mb-3" />
        <Skeleton height="4rem" />
      </div>

      <template #footer>
        <div class="detail-actions">
          <!-- Status Actions (Tech/Admin only) -->
          <div v-if="canManageTickets && currentTicket && detailContentReady" class="action-buttons">
            <Button v-if="currentTicket.status === 'new' || currentTicket.status === 'pending'"
                    :label="t('tickets.markOpen')" icon="pi pi-play" size="small"
                    @click="updateStatus('open')" />
            <Button v-if="currentTicket.status !== 'resolved' && currentTicket.status !== 'closed'"
                    :label="t('tickets.markPending')" icon="pi pi-pause" size="small" severity="warning"
                    @click="updateStatus('pending')" />
            <Button v-if="currentTicket.status !== 'resolved' && currentTicket.status !== 'closed'"
                    :label="t('tickets.resolve')" icon="pi pi-check" size="small" severity="success"
                    @click="showResolveDialog = true" />
            <Button v-if="currentTicket.status !== 'new' && currentTicket.status !== 'closed'"
                    :label="t('tickets.close')" icon="pi pi-lock" size="small" severity="secondary"
                    @click="showCloseDialog = true" />
            <Button v-if="currentTicket.status === 'resolved' || currentTicket.status === 'closed'"
                    :label="t('tickets.reopen')" icon="pi pi-refresh" size="small" severity="danger"
                    @click="reopenCurrentTicket" />
          </div>
          <div v-else></div>
          <Button :label="t('common.close')" severity="secondary" outlined @click="showDetailDialog = false" />
        </div>
      </template>
    </ModalPanel>

    <!-- Resolve Modal -->
    <ModalPanel v-model="showResolveDialog"
                :title="t('tickets.resolveTicket')"
                icon="pi-check-circle"
                size="md">
      <div class="form-grid">
        <div class="form-group form-group--full">
          <label class="form-label">{{ t('tickets.resolution') }} <span class="required">*</span></label>
          <Textarea v-model="resolutionText" rows="4" class="w-full" :placeholder="t('tickets.resolutionPlaceholder')" />
        </div>
        <div class="form-group form-group--full">
          <label class="form-label">{{ t('tickets.resolutionCode') }}</label>
          <Dropdown v-model="resolutionCode" :options="resolutionCodes" optionLabel="label" optionValue="value" class="w-full transparent-dropdown" />
        </div>
      </div>
      <template #footer>
        <div class="modal-actions">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showResolveDialog = false" />
          <Button :label="t('tickets.resolve')" icon="pi pi-check" severity="success" @click="resolveCurrentTicket"
                  :disabled="!resolutionText.trim()" />
        </div>
      </template>
    </ModalPanel>

    <!-- Assign Modal -->
    <ModalPanel v-model="showAssignDialog"
                :title="t('tickets.assignTicket')"
                icon="pi-user"
                size="sm">
      <div class="form-group">
        <label class="form-label">{{ t('tickets.assignTo') }}</label>
        <Dropdown v-model="assignToUserId" :options="users" optionLabel="username" optionValue="id"
                  class="w-full transparent-dropdown" :placeholder="t('tickets.selectUser')" />
      </div>
      <template #footer>
        <div class="modal-actions">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showAssignDialog = false" />
          <Button :label="t('tickets.assign')" icon="pi pi-user" @click="assignCurrentTicket" :disabled="!assignToUserId" />
        </div>
      </template>
    </ModalPanel>

    <!-- Close Ticket Modal -->
    <ModalPanel v-model="showCloseDialog"
                :title="t('tickets.closeTicket')"
                icon="pi-lock"
                size="md">
      <div class="close-dialog-content">
        <p class="close-info">{{ t('tickets.closeInfo') }}</p>

        <!-- Only show resolution options if not already resolved -->
        <div v-if="currentTicket?.status !== 'resolved'" class="form-grid">
          <div class="form-group form-group--full">
            <label class="form-label">{{ t('tickets.closeReason') }}</label>
            <Dropdown
              v-model="closeReasonCode"
              :options="closeReasonOptions"
              optionLabel="label"
              optionValue="value"
              class="w-full transparent-dropdown"
              :placeholder="t('common.select')"
            />
          </div>
          <div class="form-group form-group--full">
            <label class="form-label">{{ t('tickets.closeNote') }}</label>
            <Textarea
              v-model="closeNote"
              rows="3"
              class="w-full"
              :placeholder="t('tickets.closeNotePlaceholder')"
            />
          </div>
        </div>
      </div>
      <template #footer>
        <div class="modal-actions">
          <Button :label="t('common.cancel')" severity="secondary" outlined @click="showCloseDialog = false" />
          <Button :label="t('tickets.confirmClose')" icon="pi pi-lock" @click="closeCurrentTicket" />
        </div>
      </template>
    </ModalPanel>

    <!-- Bulk Actions Slide-Over -->
    <BulkActionsSlideOver
      v-model="showBulkSlideOver"
      :title="t('bulk.title')"
      :selectedCount="selectedTickets.length"
      @clear-selection="selectedTickets = []; showBulkSlideOver = false"
    >
      <!-- Assign Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click="showBulkAssignAction = !showBulkAssignAction">
        <div class="flex items-center gap-4">
          <div class="action-icon">
            <i class="pi pi-user"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.assignTo') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.assignToDesc') }}</div>
          </div>
          <i :class="['pi transition-transform', showBulkAssignAction ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
        </div>
        <div v-if="showBulkAssignAction" class="mt-4 pt-4 border-t" style="border-color: var(--border-default);" @click.stop>
          <Dropdown v-model="bulkAssignee" :options="usersWithUnassign" optionLabel="username" optionValue="id"
                    :placeholder="t('tickets.assignTo')" class="w-full mb-3 transparent-dropdown" />
          <Button :label="t('bulk.applyToAll', { count: selectedTickets.length })" icon="pi pi-check"
                  class="w-full" @click="applyBulkAssign" :disabled="bulkAssignee === undefined" :loading="bulkLoading" />
        </div>
      </div>

      <!-- Change Priority Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click="showBulkPriorityAction = !showBulkPriorityAction">
        <div class="flex items-center gap-4">
          <div class="action-icon action-icon-warning">
            <i class="pi pi-flag"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.changePriority') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.changePriorityDesc') }}</div>
          </div>
          <i :class="['pi transition-transform', showBulkPriorityAction ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
        </div>
        <div v-if="showBulkPriorityAction" class="mt-4 pt-4 border-t" style="border-color: var(--border-default);" @click.stop>
          <Dropdown v-model="bulkPriority" :options="priorityOptions" optionLabel="label" optionValue="value"
                    :placeholder="t('tickets.priority')" class="w-full mb-3 transparent-dropdown" />
          <Button :label="t('bulk.applyToAll', { count: selectedTickets.length })" icon="pi pi-check"
                  class="w-full" @click="applyBulkPriority" :disabled="!bulkPriority" :loading="bulkLoading" />
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
        <div v-if="showBulkStatusAction" class="mt-4 pt-4 border-t" style="border-color: var(--border-default);" @click.stop>
          <Dropdown v-model="bulkStatus" :options="bulkStatusOptions" optionLabel="label" optionValue="value"
                    :placeholder="t('tickets.status')" class="w-full mb-3 transparent-dropdown" />
          <Button :label="t('bulk.applyToAll', { count: selectedTickets.length })" icon="pi pi-check"
                  class="w-full" @click="applyBulkStatus" :disabled="!bulkStatus" :loading="bulkLoading" />
        </div>
      </div>

      <!-- Change Type Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click="showBulkTypeAction = !showBulkTypeAction">
        <div class="flex items-center gap-4">
          <div class="action-icon action-icon-info">
            <i class="pi pi-tag"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.changeType') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.changeTypeDesc') }}</div>
          </div>
          <i :class="['pi transition-transform', showBulkTypeAction ? 'pi-chevron-up' : 'pi-chevron-down']"></i>
        </div>
        <div v-if="showBulkTypeAction" class="mt-4 pt-4 border-t" style="border-color: var(--border-default);" @click.stop>
          <Dropdown v-model="bulkType" :options="typeOptions" optionLabel="label" optionValue="value"
                    :placeholder="t('tickets.type')" class="w-full mb-3 transparent-dropdown" />
          <Button :label="t('bulk.applyToAll', { count: selectedTickets.length })" icon="pi pi-check"
                  class="w-full" @click="applyBulkType" :disabled="!bulkType" :loading="bulkLoading" />
        </div>
      </div>

      <!-- Close Action -->
      <div class="action-card p-4 rounded-xl cursor-pointer" @click="applyBulkClose">
        <div class="flex items-center gap-4">
          <div class="action-icon action-icon-success">
            <i class="pi pi-lock"></i>
          </div>
          <div class="flex-1">
            <div class="font-semibold action-title">{{ t('bulk.closeItems') }}</div>
            <div class="text-sm action-desc">{{ t('bulk.closeItemsDesc') }}</div>
          </div>
          <i class="pi pi-chevron-right"></i>
        </div>
      </div>
    </BulkActionsSlideOver>
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, onUnmounted, watch, defineAsyncComponent, markRaw } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { useI18n } from 'vue-i18n';
import { useTicketsStore } from '../stores/tickets';
import { useAuthStore } from '../stores/auth';
import { useUIStore } from '../stores/ui';
import Breadcrumbs from '../components/shared/Breadcrumbs.vue';
import BulkActionsSlideOver from '../components/shared/BulkActionsSlideOver.vue';
import ModalPanel from '../components/shared/ModalPanel.vue';
import api from '../api';

// Lazy-loaded heavy components (only loaded when needed)
const RichTextEditor = defineAsyncComponent(() =>
  import('../components/shared/RichTextEditor.vue')
);
const FileDropZone = defineAsyncComponent(() =>
  import('../components/shared/FileDropZone.vue')
);

const route = useRoute();
const router = useRouter();

const { t } = useI18n();
const toast = useToast();
const ticketsStore = useTicketsStore();
const authStore = useAuthStore();
const uiStore = useUIStore();

// User info for permission checks
const currentUser = computed(() => authStore.user);

// Breadcrumbs
const breadcrumbItems = computed(() => [
  { label: t('tickets.title'), icon: 'pi-ticket' }
])

// Permission check: can manage tickets (tech with tickets_admin, admin, superadmin)
const canManageTickets = computed(() => {
  if (!currentUser.value) return false;
  const role = currentUser.value.role;

  // Admin and superadmin always can manage tickets
  if (role === 'admin' || role === 'superadmin') return true;

  // Tech with tickets_admin permission can manage tickets
  if (role === 'tech') {
    return authStore.hasPermission('tickets_admin');
  }

  return false;
});

// State - using shallowRef for large lists to improve performance
const tickets = shallowRef([]);
const stats = ref({ total: 0, new: 0, open: 0, pending: 0, resolved: 0, closed: 0, sla_breached: 0 });
const currentTicket = shallowRef(null);
const users = shallowRef([]);
const equipment = shallowRef([]);
const loading = ref(false);
const saving = ref(false);

// Lazy loading state for modals
const detailContentReady = ref(false);
const createContentReady = ref(false);

// Pagination state
const ticketsTotal = ref(0);
const ticketsFirst = ref(0);
const ticketsRows = ref(15);

// Sorting
const sortField = ref('created_at');
const sortOrder = ref(-1); // -1 = desc, 1 = asc

// Filters
const filters = ref({
  status: null,
  priority: null,
  ticket_type: null,
  category: null,
  search: '',
  my_tickets: false
});

// Dialogs
const showTicketDialog = ref(false);
const showDetailDialog = ref(false);
const showResolveDialog = ref(false);
const showAssignDialog = ref(false);
const showCloseDialog = ref(false);

// Close dialog form
const closeNote = ref('');
const closeReasonCode = ref(null);

// Forms
const editingTicket = ref(null);
const ticketForm = ref({
  title: '',
  description: '',
  ticket_type: 'incident',
  category: null,
  priority: 'medium',
  impact: 'medium',
  urgency: 'medium',
  assigned_to_id: null,
  equipment_id: null
});

const newComment = ref('');
const commentInternal = ref(false);
const resolutionText = ref('');
const resolutionCode = ref('fixed');
const assignToUserId = ref(null);

// Attachments for new tickets
const ticketAttachments = ref([]);

// Bulk operations state
const selectedTickets = ref([]);
const bulkAssignee = ref(undefined);
const bulkPriority = ref(null);
const bulkStatus = ref(null);
const bulkType = ref(null);
const bulkLoading = ref(false);
const showBulkSlideOver = ref(false);
const showBulkAssignAction = ref(false);
const showBulkPriorityAction = ref(false);
const showBulkStatusAction = ref(false);
const showBulkTypeAction = ref(false);

// Users with unassign option for bulk operations
const usersWithUnassign = computed(() => {
  return [{ id: null, username: t('tickets.unassign') }, ...users.value];
});

// Bulk status options
const bulkStatusOptions = computed(() => [
  { label: t('tickets.statusNew'), value: 'new' },
  { label: t('tickets.statusOpen'), value: 'open' },
  { label: t('tickets.statusPending'), value: 'pending' },
  { label: t('tickets.statusResolved'), value: 'resolved' },
  { label: t('tickets.statusClosed'), value: 'closed' }
]);

// Options (computed for i18n reactivity)
const priorityOptions = computed(() => [
  { label: t('tickets.priorityCritical'), value: 'critical' },
  { label: t('tickets.priorityHigh'), value: 'high' },
  { label: t('tickets.priorityMedium'), value: 'medium' },
  { label: t('tickets.priorityLow'), value: 'low' }
]);

const typeOptions = computed(() => [
  { label: t('tickets.typeIncident'), value: 'incident' },
  { label: t('tickets.typeRequest'), value: 'request' },
  { label: t('tickets.typeProblem'), value: 'problem' },
  { label: t('tickets.typeChange'), value: 'change' }
]);

const categoryOptions = computed(() => [
  { label: t('tickets.categoryHardware'), value: 'hardware' },
  { label: t('tickets.categorySoftware'), value: 'software' },
  { label: t('tickets.categoryNetwork'), value: 'network' },
  { label: t('tickets.categoryAccess'), value: 'access' },
  { label: t('tickets.categoryOther'), value: 'other' }
]);

const impactOptions = computed(() => [
  { label: t('tickets.impactHigh'), value: 'high' },
  { label: t('tickets.impactMedium'), value: 'medium' },
  { label: t('tickets.impactLow'), value: 'low' }
]);

const resolutionCodes = computed(() => [
  { label: t('tickets.codeFixed'), value: 'fixed' },
  { label: t('tickets.codeWorkaround'), value: 'workaround' },
  { label: t('tickets.codeCannotReproduce'), value: 'cannot_reproduce' },
  { label: t('tickets.codeDuplicate'), value: 'duplicate' },
  { label: t('tickets.codeUserError'), value: 'user_error' }
]);

const closeReasonOptions = computed(() => [
  { label: t('tickets.closeReasonResolved'), value: 'resolved' },
  { label: t('tickets.closeReasonDuplicate'), value: 'duplicate' },
  { label: t('tickets.closeReasonWithdrawn'), value: 'withdrawn' },
  { label: t('tickets.closeReasonNoResponse'), value: 'no_response' },
  { label: t('tickets.closeReasonOutOfScope'), value: 'out_of_scope' }
]);

// Helpers
const capitalize = (str) => str ? str.charAt(0).toUpperCase() + str.slice(1) : '';

const getInitials = (name) => {
  if (!name) return '?';
  return name.substring(0, 2).toUpperCase();
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString();
};

const getStatusSeverity = (status) => {
  switch (status) {
    case 'new': return 'info';
    case 'open': return 'warning';
    case 'pending': return 'secondary';
    case 'resolved': return 'success';
    case 'closed': return 'contrast';
    default: return null;
  }
};

const getPrioritySeverity = (priority) => {
  switch (priority) {
    case 'critical': return 'danger';
    case 'high': return 'warning';
    case 'medium': return 'info';
    case 'low': return 'success';
    default: return null;
  }
};

const formatHistoryAction = (item) => {
  if (item.action === 'created') return t('tickets.historyCreated');
  if (item.action === 'commented') return t('tickets.historyCommented');
  if (item.action === 'resolved') return t('tickets.historyResolved');
  if (item.action === 'closed') return t('tickets.historyClosed');
  if (item.action === 'reopened') return t('tickets.historyReopened');
  if (item.action === 'assigned') return `${t('tickets.historyAssigned')} ${item.new_value || ''}`;
  if (item.action === 'status_changed') return `${t('tickets.historyStatusChanged')} ${item.old_value} → ${item.new_value}`;
  if (item.action === 'updated') return `${t('tickets.historyUpdated')} ${item.field_name}`;
  return item.action;
};

// Sanitize HTML content for safe rendering (enhanced regex-based sanitization)
const sanitizeHtml = (html) => {
  if (!html) return '';
  // Check if content contains HTML tags
  if (!/<[^>]+>/.test(html)) {
    // Plain text - convert newlines to <br> for backward compatibility
    return html.replace(/\n/g, '<br>');
  }
  // Simple sanitization: allow only safe tags and attributes
  const allowedTags = ['p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre', 'ul', 'ol', 'li', 'blockquote', 'a', 'h2', 'h3', 'b', 'i', 'img'];

  // Remove script tags and event handlers
  let clean = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+="[^"]*"/gi, '')
    .replace(/on\w+='[^']*'/gi, '')
    .replace(/javascript:/gi, '');

  // Remove disallowed tags but keep their content
  const tagRegex = /<\/?([a-z][a-z0-9]*)\b[^>]*>/gi;
  clean = clean.replace(tagRegex, (match, tagName) => {
    if (allowedTags.includes(tagName.toLowerCase())) {
      // Keep allowed tags but remove dangerous attributes
      return match
        .replace(/\s+style\s*=\s*["'][^"']*["']/gi, '')
        .replace(/\s+onclick\s*=\s*["'][^"']*["']/gi, '')
        .replace(/\s+onerror\s*=\s*["'][^"']*["']/gi, '');
    }
    // Remove tag but this regex only removes the tag, not content
    return '';
  });

  return clean;
};

// Check if comment is from the ticket requester
const isRequesterComment = (comment) => {
  return comment.user_id === currentTicket.value?.requester_id;
};

// Computed property for sorted comments
const sortedComments = computed(() => {
  if (!currentTicket.value?.comments) return [];
  return [...currentTicket.value.comments].sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at)
  );
});

// Check if comment has actual content (not just empty HTML)
const newCommentHasContent = computed(() => {
  if (!newComment.value) return false;
  const textContent = newComment.value.replace(/<[^>]*>/g, '').trim();
  return textContent.length > 0;
});

// Debounced search
let searchTimeout = null;
const debouncedSearch = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    ticketsFirst.value = 0; // Reset to first page on search
    loadTickets();
  }, 300);
};

// Handle tickets page change
const onTicketsPage = (event) => {
  ticketsFirst.value = event.first;
  ticketsRows.value = event.rows;
  loadTickets();
};

// Data loading
const loadTickets = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    params.append('skip', ticketsFirst.value);
    params.append('limit', ticketsRows.value);
    if (filters.value.status) params.append('status', filters.value.status);
    if (filters.value.priority) params.append('priority', filters.value.priority);
    if (filters.value.ticket_type) params.append('ticket_type', filters.value.ticket_type);
    if (filters.value.search) params.append('search', filters.value.search);
    if (filters.value.my_tickets) params.append('my_tickets', 'true');
    if (sortField.value) params.append('sort', sortField.value);
    params.append('order', sortOrder.value === -1 ? 'desc' : 'asc');

    const [ticketsRes, statsRes] = await Promise.all([
      api.get(`/tickets/?${params}`),
      api.get('/tickets/stats')
    ]);
    tickets.value = ticketsRes.data.items;
    ticketsTotal.value = ticketsRes.data.total;
    stats.value = statsRes.data;
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Failed to load tickets' });
  } finally {
    loading.value = false;
  }
};

const loadReferenceData = async () => {
  try {
    const results = await Promise.allSettled([
      api.get('/users/'),
      api.get('/inventory/equipment/', { params: { limit: 500 } }) // Get a reasonable number for dropdown
    ]);
    // Handle partial failures gracefully
    if (results[0].status === 'fulfilled') users.value = results[0].value.data;
    if (results[1].status === 'fulfilled') {
      const eqData = results[1].value.data;
      equipment.value = eqData.items || eqData; // Handle both paginated and non-paginated response
    }
  } catch {
    // Error handled by API interceptor
  }
};

const setFilter = (key, value) => {
  filters.value[key] = value;
  ticketsFirst.value = 0; // Reset to first page on filter change
  loadTickets();
};

const toggleSort = (field) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === -1 ? 1 : -1;
  } else {
    sortField.value = field;
    sortOrder.value = -1;
  }
  loadTickets();
};

// Ticket CRUD
const openTicketDialog = (ticket = null) => {
  editingTicket.value = ticket;
  ticketAttachments.value = []; // Reset attachments
  if (ticket) {
    ticketForm.value = { ...ticket };
  } else {
    ticketForm.value = {
      title: '',
      description: '',
      ticket_type: 'incident',
      category: null,
      priority: 'medium',
      impact: 'medium',
      urgency: 'medium',
      assigned_to_id: null,
      equipment_id: null
    };
  }
  showTicketDialog.value = true;
};

// Handle image upload from rich text editor
const handleDescriptionImageUpload = async (file, callback) => {
  try {
    // For now, convert to base64. In production, upload to server and return URL.
    const reader = new FileReader();
    reader.onload = (e) => {
      callback(e.target.result);
    };
    reader.readAsDataURL(file);
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('files.uploadFailed') });
  }
};

// Handle attachment errors
const handleAttachmentError = (errors) => {
  errors.forEach(error => {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: error });
  });
};

// Upload attachments after ticket creation
const uploadTicketAttachments = async (ticketId) => {
  if (ticketAttachments.value.length === 0) return;

  for (const file of ticketAttachments.value) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      await api.post(`/tickets/${ticketId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    } catch (error) {
      console.error('Failed to upload attachment:', error);
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('files.someUploadsFailed') });
    }
  }
};

const saveTicket = async () => {
  // Validate required fields - strip HTML for empty check
  const descriptionText = ticketForm.value.description?.replace(/<[^>]*>/g, '').trim() || '';
  if (!ticketForm.value.title || !descriptionText) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') });
    return;
  }
  saving.value = true;
  try {
    let ticketId;
    if (editingTicket.value) {
      await api.put(`/tickets/${editingTicket.value.id}`, ticketForm.value);
      ticketId = editingTicket.value.id;
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.ticketUpdated') });
    } else {
      const response = await api.post('/tickets/', ticketForm.value);
      ticketId = response.data.id;
      // Upload attachments for new ticket
      if (ticketAttachments.value.length > 0) {
        await uploadTicketAttachments(ticketId);
      }
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.ticketCreated') });
    }
    showTicketDialog.value = false;
    ticketAttachments.value = []; // Clear attachments
    loadTickets();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    saving.value = false;
  }
};

const onTicketDialogEnter = (event) => {
  if (event.target.tagName !== 'TEXTAREA') {
    event.preventDefault();
    saveTicket();
  }
};

// Ticket detail - lazy loading pattern: open modal first, load data after animation
const openTicketDetail = async (event) => {
  // Set basic info immediately for skeleton display
  currentTicket.value = { id: event.data.id, title: event.data.title, ticket_number: event.data.ticket_number };
  detailContentReady.value = false;
  showDetailDialog.value = true;
};

// Load full ticket data after modal animation completes
const onDetailModalReady = async () => {
  if (!currentTicket.value?.id) return;
  try {
    // Check UI cache first
    const cacheKey = `ticket_${currentTicket.value.id}`;
    const cached = uiStore.getCachedData(cacheKey);
    if (cached) {
      currentTicket.value = markRaw(cached);
    } else {
      const response = await api.get(`/tickets/${currentTicket.value.id}`);
      currentTicket.value = markRaw(response.data);
      uiStore.setCachedData(cacheKey, response.data);
    }
    detailContentReady.value = true;
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Failed to load ticket' });
    showDetailDialog.value = false;
  }
};

// Open ticket by ID (used when coming from notifications)
const openTicketById = async (ticketId) => {
  // Set minimal info and open modal
  currentTicket.value = { id: ticketId };
  detailContentReady.value = false;
  showDetailDialog.value = true;
  // Clear the query param after opening
  router.replace({ path: '/tickets', query: {} });
};

const refreshCurrentTicket = async () => {
  if (currentTicket.value) {
    const response = await api.get(`/tickets/${currentTicket.value.id}`);
    currentTicket.value = markRaw(response.data);
    // Update cache
    uiStore.setCachedData(`ticket_${currentTicket.value.id}`, response.data);
  }
};

// Actions
const updateStatus = async (newStatus) => {
  try {
    await api.put(`/tickets/${currentTicket.value.id}`, { status: newStatus });
    await refreshCurrentTicket();
    loadTickets();
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.statusUpdated') });
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
};

const postComment = async () => {
  if (!newComment.value.trim()) return;
  try {
    await api.post(`/tickets/${currentTicket.value.id}/comments`, {
      content: newComment.value,
      is_internal: commentInternal.value
    });
    newComment.value = '';
    commentInternal.value = false;
    await refreshCurrentTicket();
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.commentAdded') });
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
};

const resolveCurrentTicket = async () => {
  if (!resolutionText.value.trim()) return;
  try {
    await api.post(`/tickets/${currentTicket.value.id}/resolve?resolution=${encodeURIComponent(resolutionText.value)}&resolution_code=${resolutionCode.value}`);
    showResolveDialog.value = false;
    resolutionText.value = '';
    resolutionCode.value = 'fixed';
    await refreshCurrentTicket();
    loadTickets();
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.ticketResolved') });
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
};

const closeCurrentTicket = async () => {
  try {
    const params = new URLSearchParams();
    if (closeNote.value) {
      params.append('resolution', closeNote.value);
    }
    if (closeReasonCode.value) {
      params.append('resolution_code', closeReasonCode.value);
    }

    const queryString = params.toString();
    await api.post(`/tickets/${currentTicket.value.id}/close${queryString ? '?' + queryString : ''}`);

    showCloseDialog.value = false;
    closeNote.value = '';
    closeReasonCode.value = null;

    await refreshCurrentTicket();
    loadTickets();
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.ticketClosed') });
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
};

const reopenCurrentTicket = async () => {
  try {
    await api.post(`/tickets/${currentTicket.value.id}/reopen`);
    await refreshCurrentTicket();
    loadTickets();
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.ticketReopened') });
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
};

const assignCurrentTicket = async () => {
  if (!assignToUserId.value) return;
  try {
    await api.post(`/tickets/${currentTicket.value.id}/assign?user_id=${assignToUserId.value}`);
    showAssignDialog.value = false;
    assignToUserId.value = null;
    await refreshCurrentTicket();
    loadTickets();
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.ticketAssigned') });
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
};

// Bulk operations
const applyBulkAssign = async () => {
  if (bulkAssignee.value === undefined || selectedTickets.value.length === 0) return;
  bulkLoading.value = true;
  try {
    const response = await api.post('/tickets/bulk-assign', {
      ticket_ids: selectedTickets.value.map(t => t.id),
      assigned_to_id: bulkAssignee.value
    });
    const result = response.data;
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.bulkAssignSuccess', { count: result.processed }) });
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('tickets.bulkAssignPartial', { processed: result.processed, failed: result.failed }) });
    }
    selectedTickets.value = [];
    bulkAssignee.value = undefined;
    showBulkSlideOver.value = false;
    showBulkAssignAction.value = false;
    loadTickets();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    bulkLoading.value = false;
  }
};

const applyBulkClose = async () => {
  if (selectedTickets.value.length === 0) return;
  bulkLoading.value = true;
  try {
    const response = await api.post('/tickets/bulk-close', {
      ticket_ids: selectedTickets.value.map(t => t.id)
    });
    const result = response.data;
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.bulkCloseSuccess', { count: result.processed }) });
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('tickets.bulkClosePartial', { processed: result.processed, failed: result.failed }) });
    }
    selectedTickets.value = [];
    showBulkSlideOver.value = false;
    loadTickets();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    bulkLoading.value = false;
  }
};

const applyBulkPriority = async () => {
  if (!bulkPriority.value || selectedTickets.value.length === 0) return;
  bulkLoading.value = true;
  try {
    const response = await api.post('/tickets/bulk-priority', {
      ticket_ids: selectedTickets.value.map(t => t.id),
      priority: bulkPriority.value
    });
    const result = response.data;
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.bulkPrioritySuccess', { count: result.processed }) });
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('tickets.bulkPriorityPartial', { processed: result.processed, failed: result.failed }) });
    }
    selectedTickets.value = [];
    bulkPriority.value = null;
    showBulkSlideOver.value = false;
    showBulkPriorityAction.value = false;
    loadTickets();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    bulkLoading.value = false;
  }
};

const applyBulkStatus = async () => {
  if (!bulkStatus.value || selectedTickets.value.length === 0) return;
  bulkLoading.value = true;
  try {
    const response = await api.post('/tickets/bulk-status', {
      ticket_ids: selectedTickets.value.map(t => t.id),
      status: bulkStatus.value
    });
    const result = response.data;
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.bulkStatusSuccess', { count: result.processed }) });
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('tickets.bulkStatusPartial', { processed: result.processed, failed: result.failed }) });
    }
    selectedTickets.value = [];
    bulkStatus.value = null;
    showBulkSlideOver.value = false;
    showBulkStatusAction.value = false;
    loadTickets();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    bulkLoading.value = false;
  }
};

const applyBulkType = async () => {
  if (!bulkType.value || selectedTickets.value.length === 0) return;
  bulkLoading.value = true;
  try {
    const response = await api.post('/tickets/bulk-type', {
      ticket_ids: selectedTickets.value.map(t => t.id),
      ticket_type: bulkType.value
    });
    const result = response.data;
    if (result.success) {
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('tickets.bulkTypeSuccess', { count: result.processed }) });
    } else {
      toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('tickets.bulkTypePartial', { processed: result.processed, failed: result.failed }) });
    }
    selectedTickets.value = [];
    bulkType.value = null;
    showBulkSlideOver.value = false;
    showBulkTypeAction.value = false;
    loadTickets();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    bulkLoading.value = false;
  }
};

// Selection helpers
const isTicketSelected = (ticketId) => {
  return selectedTickets.value.some(t => t.id === ticketId);
};

const toggleTicketSelection = (ticket) => {
  const index = selectedTickets.value.findIndex(t => t.id === ticket.id);
  if (index === -1) {
    selectedTickets.value.push(ticket);
  } else {
    selectedTickets.value.splice(index, 1);
  }
};

// Select all helpers
const allPageTicketsSelected = computed(() => {
  if (tickets.value.length === 0) return false;
  return tickets.value.every(ticket => isTicketSelected(ticket.id));
});

const somePageTicketsSelected = computed(() => {
  if (tickets.value.length === 0) return false;
  const selectedCount = tickets.value.filter(ticket => isTicketSelected(ticket.id)).length;
  return selectedCount > 0 && selectedCount < tickets.value.length;
});

const toggleSelectAllPage = () => {
  if (allPageTicketsSelected.value) {
    // Deselect all tickets on current page
    tickets.value.forEach(ticket => {
      const index = selectedTickets.value.findIndex(t => t.id === ticket.id);
      if (index !== -1) {
        selectedTickets.value.splice(index, 1);
      }
    });
  } else {
    // Select all tickets on current page
    tickets.value.forEach(ticket => {
      if (!isTicketSelected(ticket.id)) {
        selectedTickets.value.push(ticket);
      }
    });
  }
};

onMounted(async () => {
  // Apply URL query params for filters and sorting
  if (route.query.status) filters.value.status = route.query.status;
  if (route.query.priority) filters.value.priority = route.query.priority;
  if (route.query.sort) sortField.value = route.query.sort;
  if (route.query.order) sortOrder.value = route.query.order === 'asc' ? 1 : -1;

  // Load tickets and reference data in parallel, but wait for both
  await Promise.all([
    loadTickets(),
    loadReferenceData()
  ]);

  // Check if there's a ticket ID in the URL query params (from notification click)
  const ticketId = route.query.id;
  if (ticketId) {
    openTicketById(ticketId);
  }

  // Check if action=create in query params (from CommandBar quick action or Equipment detail)
  if (route.query.action === 'create') {
    // Pre-fill equipment_id if provided (from EquipmentDetailSlideOver)
    if (route.query.equipment_id) {
      ticketForm.value.equipment_id = parseInt(route.query.equipment_id);
    }
    openTicketDialog();
    // Clear the query params after opening dialog
    router.replace({ path: '/tickets', query: {} });
  }
});

// Cleanup debounce timer on unmount to prevent memory leaks
onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
    searchTimeout = null;
  }
});
</script>

<style scoped>
/* ==================== Page Layout ==================== */
.tickets-page {
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

/* Colored chips when NOT active */
.stat-chip--new:not(.active) { background: rgba(59, 130, 246, 0.12); border-color: rgba(59, 130, 246, 0.3); }
.stat-chip--new:not(.active) .stat-chip-label,
.stat-chip--new:not(.active) .stat-chip-count { color: #3b82f6; }

.stat-chip--open:not(.active) { background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3); }
.stat-chip--open:not(.active) .stat-chip-label,
.stat-chip--open:not(.active) .stat-chip-count { color: #f59e0b; }

.stat-chip--pending:not(.active) { background: rgba(168, 85, 247, 0.12); border-color: rgba(168, 85, 247, 0.3); }
.stat-chip--pending:not(.active) .stat-chip-label,
.stat-chip--pending:not(.active) .stat-chip-count { color: #a855f7; }

.stat-chip--resolved:not(.active) { background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.3); }
.stat-chip--resolved:not(.active) .stat-chip-label,
.stat-chip--resolved:not(.active) .stat-chip-count { color: #22c55e; }

.stat-chip--closed:not(.active) { background: rgba(100, 116, 139, 0.12); border-color: rgba(100, 116, 139, 0.3); }
.stat-chip--closed:not(.active) .stat-chip-label,
.stat-chip--closed:not(.active) .stat-chip-count { color: #64748b; }

.stat-chip--danger {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

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

/* Force dropdowns to have NO border/background - high specificity to override global styles */
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

/* Label - add padding for text spacing */
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

/* Arrow - positioned absolutely */
.toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-trigger) {
  position: absolute;
  right: 1.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: auto;
  color: var(--text-muted);
  background: transparent !important;
}

/* Clear icon - aligned with arrow */
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

.my-tickets-toggle {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
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
  white-space: nowrap;
}

/* ==================== Tickets Container ==================== */
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

/* ==================== Tickets List - Compact Row Design ==================== */
.tickets-list {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
}

/* Table Header */
.tickets-header {
  display: grid;
  grid-template-columns: 32px 120px 1fr 160px 180px 130px 24px;
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

.header-col--arrow {
  width: 24px;
}

/* Ticket Rows */
.ticket-row {
  display: grid;
  grid-template-columns: 32px 120px 1fr 160px 180px 130px 24px;
  align-items: center;
  gap: 1.5rem;
  padding: 0.875rem 1.5rem;
  border-bottom: 1px solid var(--border-default);
  cursor: pointer;
  transition: background 0.15s ease;
}

.ticket-row:last-child {
  border-bottom: none;
}

.ticket-row:hover {
  background: var(--bg-hover);
}

.ticket-row--selected {
  background: var(--primary-light);
}

.ticket-checkbox {
  width: 32px;
}

.ticket-number {
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--primary);
}

.ticket-info {
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

.ticket-tags {
  display: flex;
  gap: 0.375rem;
  flex-shrink: 0;
}

.ticket-users {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 140px;
}

.ticket-user,
.ticket-assignee {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.ticket-user i,
.ticket-assignee i {
  font-size: 0.625rem;
  color: var(--text-muted);
}

.ticket-assignee.unassigned {
  color: var(--text-muted);
  font-style: italic;
}

.ticket-date {
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.ticket-arrow {
  color: var(--text-muted);
  font-size: 0.75rem;
  transition: transform 0.15s ease, color 0.15s ease;
}

.ticket-row:hover .ticket-arrow {
  transform: translateX(3px);
  color: var(--primary);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  padding: 0.75rem;
  border-top: 1px solid var(--border-default);
}

/* Responsive */
@media (max-width: 1200px) {
  .tickets-header,
  .ticket-row {
    grid-template-columns: 32px 100px 1fr 140px 160px 110px 24px;
    gap: 1rem;
  }
}

@media (max-width: 1024px) {
  .tickets-header {
    display: none;
  }

  .ticket-row {
    grid-template-columns: auto 1fr auto;
    grid-template-rows: auto auto auto;
    gap: 0.5rem 1rem;
    padding: 1rem 1.25rem;
  }

  .ticket-checkbox {
    grid-row: 1 / 4;
  }

  .ticket-number {
    grid-row: 1;
    grid-column: 2;
  }

  .ticket-info {
    grid-row: 2;
    grid-column: 2;
  }

  .ticket-tags {
    grid-row: 1;
    grid-column: 3;
  }

  .ticket-users {
    grid-row: 3;
    grid-column: 2;
    flex-direction: row;
    gap: 1.5rem;
    min-width: auto;
  }

  .ticket-date {
    grid-row: 3;
    grid-column: 3;
  }

  .ticket-arrow {
    grid-row: 2;
    grid-column: 3;
    align-self: center;
  }

  .toolbar {
    flex-wrap: wrap;
    gap: 1.5rem;
    gap: 1rem;
  }

  .toolbar .search-input {
    width: 100%;
    order: -1;
  }

  .toolbar-spacer {
    display: none;
  }
}

/* ==================== Create Form Styles ==================== */
.create-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field-label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.375rem;
}

.required {
  color: #ef4444;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 640px) {
  .form-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

.form-col {
  display: flex;
  flex-direction: column;
}

/* ==================== Create Form (reuses detail styles) ==================== */
.detail-info-grid--form {
  grid-template-columns: repeat(2, 1fr);
}

@media (min-width: 768px) {
  .detail-info-grid--form {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Form dropdown in info grid - transparent style */
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
  background: transparent !important;
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
  cursor: pointer;
}

.info-item :deep(.info-dropdown .p-dropdown-clear-icon:hover) {
  color: var(--primary);
}

/* ==================== Unified Transparent Dropdown Style ==================== */
/* Standard UI - Transparent & Minimalist dropdown style for modals and dialogs */
/* Apply class="transparent-dropdown" to any Dropdown component */

.transparent-dropdown:deep(.p-dropdown),
:deep(.transparent-dropdown.p-dropdown) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  position: relative;
  padding: 0 !important;
  width: 100%;
}

.transparent-dropdown:deep(.p-dropdown.p-focus),
.transparent-dropdown:deep(.p-dropdown:hover),
:deep(.transparent-dropdown.p-dropdown.p-focus),
:deep(.transparent-dropdown.p-dropdown:hover) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-label),
:deep(.transparent-dropdown.p-dropdown .p-dropdown-label) {
  padding: 0.5rem 3.5rem 0.5rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  background: transparent !important;
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-label.p-placeholder),
:deep(.transparent-dropdown.p-dropdown .p-dropdown-label.p-placeholder) {
  color: var(--text-secondary);
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-trigger),
:deep(.transparent-dropdown.p-dropdown .p-dropdown-trigger) {
  position: absolute;
  right: 1.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: auto;
  color: var(--text-muted);
  background: transparent !important;
}

.transparent-dropdown:deep(.p-dropdown .p-dropdown-clear-icon),
:deep(.transparent-dropdown.p-dropdown .p-dropdown-clear-icon) {
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

.transparent-dropdown:deep(.p-dropdown .p-dropdown-clear-icon:hover),
:deep(.transparent-dropdown.p-dropdown .p-dropdown-clear-icon:hover) {
  color: var(--primary);
}

/* Full width form inputs */
.form-input-full.p-inputtext,
.form-input-full.p-textarea {
  width: 100%;
  background: var(--bg-secondary) !important;
  border: none !important;
  border-radius: var(--radius-lg) !important;
  padding: 1rem !important;
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

.section-title .required {
  color: #ef4444;
  font-weight: normal;
}

.modal-footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* Legacy form-grid for resolve/assign modals */
.form-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 640px) {
  .form-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group--full {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* ==================== Detail Modal ==================== */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

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

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.info-value {
  font-weight: 500;
  color: var(--text-primary);
}

.info-value-with-action {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 500;
  color: var(--text-primary);
}

/* Detail Sections */
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

.section-title--success {
  color: var(--success);
}

.description-box {
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  white-space: pre-wrap;
  font-size: 0.875rem;
  line-height: 1.6;
}

.resolution-box {
  padding: 1rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: var(--radius-lg);
  white-space: pre-wrap;
  font-size: 0.875rem;
  line-height: 1.6;
}

/* Images in description and resolution boxes */
.description-box img,
.resolution-box img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 0.5rem 0;
  display: block;
}

.description-box a,
.resolution-box a {
  color: var(--primary);
  text-decoration: underline;
}

.description-box p,
.resolution-box p {
  margin: 0 0 0.75em 0;
}

.description-box p:last-child,
.resolution-box p:last-child {
  margin-bottom: 0;
}

.description-box ul,
.description-box ol,
.resolution-box ul,
.resolution-box ol {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.description-box blockquote,
.resolution-box blockquote {
  border-left: 3px solid var(--primary);
  margin: 0.5em 0;
  padding-left: 1em;
  color: var(--text-secondary);
  font-style: italic;
}

.description-box code,
.resolution-box code {
  background: var(--bg-tertiary);
  border-radius: 4px;
  padding: 0.2em 0.4em;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
}

.description-box pre,
.resolution-box pre {
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 12px 16px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.description-box pre code,
.resolution-box pre code {
  background: none;
  padding: 0;
}

/* Conversation */
.conversation-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: 1rem;
}

.message {
  display: flex;
  gap: 0.75rem;
  max-width: 85%;
}

.message--requester {
  align-self: flex-start;
}

.message--tech {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message--internal .message-bubble {
  border-left: 3px solid var(--warning);
  background: rgba(var(--warning-rgb), 0.1);
}

.message-avatar {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary) 0%, #06b6d4 100%);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
}

.message--tech .message-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.message-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-bubble {
  background: var(--bg-primary);
  border-radius: 1rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-default);
}

.message--requester .message-bubble {
  border-radius: 1rem 1rem 1rem 0.25rem;
}

.message--tech .message-bubble {
  border-radius: 1rem 1rem 0.25rem 1rem;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
  flex-wrap: wrap;
}

.message-author {
  font-weight: 600;
  font-size: 0.8125rem;
  color: var(--text-primary);
}

.message-tag {
  font-size: 0.625rem;
}

.message-time {
  font-size: 0.6875rem;
  color: var(--text-muted);
  margin-left: auto;
}

.message-content {
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--text-primary);
}

.message-content p {
  margin: 0 0 0.5rem 0;
}

.message-content p:last-child {
  margin-bottom: 0;
}

.message-content ul,
.message-content ol {
  margin: 0.5rem 0;
  padding-left: 1.25rem;
}

.message-content code {
  background: var(--bg-secondary);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.message-content a {
  color: var(--primary);
}

.message-content blockquote {
  border-left: 3px solid var(--primary);
  padding-left: 0.75rem;
  margin: 0.5rem 0;
  color: var(--text-secondary);
}

.message-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 0.5rem 0;
  display: block;
}

.conversation-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--text-muted);
  text-align: center;
}

.conversation-empty i {
  font-size: 2rem;
  opacity: 0.5;
}

.conversation-empty p {
  font-size: 0.8125rem;
  margin: 0;
}

/* Reply Section */
.reply-section {
  border-top: 1px solid var(--border-default);
  padding-top: 1rem;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.reply-header i {
  color: var(--primary);
}

.reply-closed {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-size: 0.875rem;
}

.reply-closed i {
  font-size: 1rem;
}

.reply-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.75rem;
}

.internal-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
}

.internal-toggle label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  cursor: pointer;
  color: var(--text-primary);
}

.internal-toggle i {
  font-size: 0.75rem;
  color: var(--warning);
}

/* Close Dialog */
.close-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.close-info {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

/* History */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 200px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-default);
  font-size: 0.8125rem;
}

.history-item i {
  font-size: 0.5rem;
  color: var(--primary);
}

.history-time {
  color: var(--text-muted);
  flex-shrink: 0;
}

.history-user {
  font-weight: 500;
}

.history-action {
  color: var(--text-secondary);
}

/* Detail Actions */
.detail-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

/* ==================== Bulk Actions (keep existing) ==================== */
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

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-light);
}

.action-icon i {
  color: var(--primary);
}

.action-icon-warning {
  background: var(--warning-light);
}

.action-icon-warning i {
  color: var(--warning);
}

.action-icon-success {
  background: var(--success-light);
}

.action-icon-success i {
  color: var(--success);
}

.action-icon-info {
  background: var(--info-light);
}

.action-icon-info i {
  color: var(--info);
}

.action-card .action-title {
  color: var(--text-primary);
}

.action-card .action-desc {
  color: var(--text-secondary);
}

.action-card i.pi-chevron-up,
.action-card i.pi-chevron-down,
.action-card i.pi-chevron-right {
  color: var(--text-secondary);
}

/* ==================== Dark Mode Fixes ==================== */
:root.dark .page-header,
:root.dark .toolbar,
:root.dark .tickets-container {
  background: var(--bg-card-solid);
  border-color: var(--border-default);
}

:root.dark .page-title {
  color: #f1f5f9;
}

:root.dark .page-subtitle {
  color: #94a3b8;
  border-color: rgba(255, 255, 255, 0.1);
}

/* Toolbar dark mode */
:root.dark .toolbar-separator {
  background: rgba(255, 255, 255, 0.1);
}

:root.dark .filter-label {
  color: #64748b;
}

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

:root.dark .my-tickets-toggle {
  color: #e2e8f0;
}

:root.dark .toolbar-search i {
  color: #64748b;
}

/* Tickets header dark mode */
:root.dark .tickets-header {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.06);
  color: #64748b;
}

:root.dark .header-col--sortable:hover {
  color: #38bdf8;
}

/* Ticket row dark mode */
:root.dark .ticket-row {
  border-color: rgba(255, 255, 255, 0.06);
}

:root.dark .ticket-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

:root.dark .ticket-title {
  color: #f1f5f9;
}

:root.dark .ticket-type-label {
  color: #64748b;
}

:root.dark .ticket-number {
  color: #38bdf8;
}

:root.dark .ticket-user,
:root.dark .ticket-assignee {
  color: #cbd5e1;
}

:root.dark .ticket-user i,
:root.dark .ticket-assignee i {
  color: #64748b;
}

:root.dark .ticket-assignee.unassigned {
  color: #64748b;
}

:root.dark .ticket-date {
  color: #64748b;
}

:root.dark .ticket-arrow {
  color: #64748b;
}

/* Stat chips dark mode */
:root.dark .stat-chip:not(.active) {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

:root.dark .stat-chip.active {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
}

:root.dark .stat-chip.active .stat-chip-label,
:root.dark .stat-chip.active .stat-chip-count {
  color: white !important;
}

:root.dark .stat-chip-label {
  color: #94a3b8;
}

:root.dark .stat-chip-count {
  color: #e2e8f0;
}

/* Colored chips in dark mode */
:root.dark .stat-chip--new:not(.active) { background: rgba(59, 130, 246, 0.15); border-color: rgba(59, 130, 246, 0.35); }
:root.dark .stat-chip--new:not(.active) .stat-chip-label,
:root.dark .stat-chip--new:not(.active) .stat-chip-count { color: #60a5fa; }

:root.dark .stat-chip--open:not(.active) { background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.35); }
:root.dark .stat-chip--open:not(.active) .stat-chip-label,
:root.dark .stat-chip--open:not(.active) .stat-chip-count { color: #fbbf24; }

:root.dark .stat-chip--pending:not(.active) { background: rgba(168, 85, 247, 0.15); border-color: rgba(168, 85, 247, 0.35); }
:root.dark .stat-chip--pending:not(.active) .stat-chip-label,
:root.dark .stat-chip--pending:not(.active) .stat-chip-count { color: #c084fc; }

:root.dark .stat-chip--resolved:not(.active) { background: rgba(34, 197, 94, 0.15); border-color: rgba(34, 197, 94, 0.35); }
:root.dark .stat-chip--resolved:not(.active) .stat-chip-label,
:root.dark .stat-chip--resolved:not(.active) .stat-chip-count { color: #4ade80; }

:root.dark .stat-chip--closed:not(.active) { background: rgba(148, 163, 184, 0.15); border-color: rgba(148, 163, 184, 0.35); }
:root.dark .stat-chip--closed:not(.active) .stat-chip-label,
:root.dark .stat-chip--closed:not(.active) .stat-chip-count { color: #94a3b8; }

/* My tickets toggle */
:root.dark .my-tickets-toggle {
  color: #e2e8f0;
}

/* Selection count */
:root.dark .selection-count {
  color: #38bdf8;
}

/* Empty state */
:root.dark .empty-state h3 {
  color: #f1f5f9;
}

:root.dark .empty-state p {
  color: #94a3b8;
}

/* Detail modal dark mode */
:root.dark .field-label,
:root.dark .form-label,
:root.dark .section-title,
:root.dark .comment-author,
:root.dark .history-user,
:root.dark .info-value,
:root.dark .info-value-with-action,
:root.dark .internal-toggle label {
  color: #f1f5f9;
}

:root.dark .detail-info-grid,
:root.dark .description-box,
:root.dark .comment-item {
  background: rgba(255, 255, 255, 0.03);
}

:root.dark .info-label,
:root.dark .comment-time,
:root.dark .history-time {
  color: #64748b;
}

:root.dark .comment-text,
:root.dark .description-box,
:root.dark .history-action {
  color: #cbd5e1;
}

/* Form inputs in dark mode */
:root.dark :deep(.p-inputtext),
:root.dark :deep(.p-dropdown),
:root.dark :deep(.p-textarea) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.1);
  color: #f1f5f9;
}

:root.dark :deep(.p-inputtext:focus),
:root.dark :deep(.p-dropdown:focus),
:root.dark :deep(.p-textarea:focus) {
  border-color: var(--primary);
}

:root.dark :deep(.p-dropdown-panel) {
  background: var(--bg-card-solid);
  border-color: var(--border-default);
}

:root.dark :deep(.p-dropdown-item) {
  color: #f1f5f9;
}

:root.dark :deep(.p-dropdown-item:hover) {
  background: rgba(255, 255, 255, 0.05);
}

:root.dark :deep(.p-dropdown-label) {
  color: #f1f5f9;
}

/* Resolution box in dark mode */
:root.dark .resolution-box {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.4);
  color: #86efac;
}

/* Responsive */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .header-title-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .page-subtitle {
    padding-left: 0;
    border-left: none;
  }

  .toolbar-left {
    width: 100%;
  }

  .search-input {
    max-width: none;
    width: 100%;
  }
}
</style>
