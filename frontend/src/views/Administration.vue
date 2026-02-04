<template>
  <div class="admin-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title-section">
          <h1 class="page-title">
            <i class="pi pi-cog"></i>
            {{ t('admin.title') }}
          </h1>
          <p class="page-subtitle">{{ t('admin.subtitle') }}</p>
        </div>
      </div>

      <!-- Navigation Pills -->
      <div class="nav-pills">
        <button class="nav-pill" :class="{ active: activeSection === 'general' }" @click="activeSection = 'general'">
          <i class="pi pi-sliders-h"></i>
          {{ t('admin.general.title') }}
        </button>
        <button class="nav-pill" :class="{ active: activeSection === 'security' }" @click="activeSection = 'security'">
          <i class="pi pi-shield"></i>
          {{ t('admin.security.title') }}
        </button>
        <button class="nav-pill" :class="{ active: activeSection === 'email' }" @click="activeSection = 'email'">
          <i class="pi pi-envelope"></i>
          {{ t('admin.email.title') }}
        </button>
        <button class="nav-pill" :class="{ active: activeSection === 'sla' }" @click="activeSection = 'sla'">
          <i class="pi pi-clock"></i>
          {{ t('admin.sla.title') }}
        </button>
        <button class="nav-pill" :class="{ active: activeSection === 'maintenance' }" @click="activeSection = 'maintenance'">
          <i class="pi pi-wrench"></i>
          {{ t('admin.maintenance.title') }}
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="admin-content">
      <!-- General Settings -->
      <div v-if="activeSection === 'general'" class="settings-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="pi pi-sliders-h"></i>
            {{ t('admin.general.configuration') }}
          </h2>
        </div>

        <div class="settings-card">
          <div class="settings-grid">
            <div class="setting-item">
              <label>{{ t('admin.general.siteName') }}</label>
              <InputText v-model="settings.site_name" placeholder="Inframate" />
            </div>
            <div class="setting-item">
              <label>{{ t('admin.general.siteUrl') }}</label>
              <InputText v-model="settings.site_url" placeholder="http://localhost:3000" />
            </div>
            <div class="setting-item">
              <label>{{ t('admin.general.defaultLanguage') }}</label>
              <Dropdown v-model="settings.default_language" :options="languageOptions" optionLabel="label" optionValue="value" class="admin-dropdown" />
            </div>
            <div class="setting-item">
              <label>{{ t('admin.general.sessionTimeout') }}</label>
              <InputNumber v-model="settings.session_timeout_minutes" :min="5" :max="1440" suffix=" min" />
            </div>
            <div class="setting-item">
              <label>{{ t('admin.general.itemsPerPage') }}</label>
              <InputNumber v-model="settings.items_per_page" :min="10" :max="100" />
            </div>
          </div>
          <div class="settings-actions">
            <Button :label="t('common.save')" icon="pi pi-check" @click="saveCategory('general')" :loading="saving" />
          </div>
        </div>
      </div>

      <!-- Security Settings -->
      <div v-if="activeSection === 'security'" class="settings-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="pi pi-shield"></i>
            {{ t('admin.security.configuration') }}
          </h2>
        </div>

        <div class="settings-card">
          <div class="settings-grid">
            <div class="setting-item">
              <label>{{ t('admin.security.minPasswordLength') }}</label>
              <InputNumber v-model="settings.min_password_length" :min="6" :max="32" />
            </div>
            <div class="setting-item">
              <label>{{ t('admin.security.loginRateLimit') }}</label>
              <InputNumber v-model="settings.login_rate_limit" :min="1" :max="20" suffix=" /min" />
            </div>
            <div class="setting-item">
              <label>{{ t('admin.security.sessionConcurrentLimit') }}</label>
              <InputNumber v-model="settings.session_concurrent_limit" :min="1" :max="20" />
            </div>
            <div class="setting-item setting-item--toggle">
              <label>{{ t('admin.security.requireMfaForAdmins') }}</label>
              <InputSwitch v-model="settings.require_mfa_for_admins" />
            </div>
          </div>
          <div class="settings-actions">
            <Button :label="t('common.save')" icon="pi pi-check" @click="saveCategory('security')" :loading="saving" />
          </div>
        </div>
      </div>

      <!-- Email Integration -->
      <div v-if="activeSection === 'email'" class="settings-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="pi pi-envelope"></i>
            {{ t('admin.email.title') }}
          </h2>
        </div>

        <!-- Connected Accounts -->
        <div class="settings-card">
          <div class="card-header">
            <div class="card-title">
              <i class="pi pi-link"></i>
              {{ t('admin.email.connectedAccounts') }}
            </div>
          </div>

          <!-- No connection yet -->
          <div v-if="!emailConfig.id" class="empty-connections">
            <i class="pi pi-inbox"></i>
            <p>{{ t('admin.email.noConnection') }}</p>
          </div>

          <!-- Connected account -->
          <div v-else class="connected-account">
            <div class="account-info">
              <div class="account-icon" :class="emailConfig.provider_type">
                <i :class="emailConfig.provider_type === 'microsoft_365' ? 'pi pi-microsoft' : 'pi pi-envelope'"></i>
              </div>
              <div class="account-details">
                <span class="account-name">{{ emailConfig.m365_mailbox || emailConfig.from_email || emailConfig.smtp_host || t('admin.email.emailAccount') }}</span>
                <span class="account-type">{{ emailConfig.provider_type === 'microsoft_365' ? 'Microsoft 365' : 'SMTP/IMAP' }}</span>
              </div>
              <Tag :value="emailConfig.is_active ? t('status.active') : t('status.inactive')" :severity="emailConfig.is_active ? 'success' : 'secondary'" />
            </div>
            <div class="account-actions">
              <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDeleteConfig" v-tooltip.top="t('common.delete')" />
            </div>
          </div>

          <!-- Connect Buttons (only show if no config) -->
          <div v-if="!emailConfig.id" class="connect-buttons">
            <button class="connect-btn connect-btn--microsoft" @click="connectMicrosoft365">
              <i class="pi pi-microsoft"></i>
              <span>{{ t('admin.email.connectMicrosoft365') }}</span>
            </button>
            <button class="connect-btn connect-btn--smtp" @click="connectSmtpImap">
              <i class="pi pi-envelope"></i>
              <span>{{ t('admin.email.connectSmtpImap') }}</span>
            </button>
          </div>
        </div>

        <!-- Notification Settings -->
        <div class="settings-card">
          <div class="card-header">
            <div class="card-title">
              <i class="pi pi-bell"></i>
              {{ t('admin.email.outboundNotifications') }}
            </div>
            <p class="card-description">{{ t('admin.email.outboundNotificationsDesc') }}</p>
          </div>

          <div class="notification-toggles">
            <div class="notification-toggle">
              <div class="toggle-info">
                <span class="toggle-label">{{ t('admin.email.notifyTicketCreated') }}</span>
                <span class="toggle-desc">{{ t('admin.email.notifyTicketCreatedDesc') }}</span>
              </div>
              <InputSwitch v-model="settings.email_notify_ticket_created" />
            </div>
            <div class="notification-toggle">
              <div class="toggle-info">
                <span class="toggle-label">{{ t('admin.email.notifyTicketAssigned') }}</span>
                <span class="toggle-desc">{{ t('admin.email.notifyTicketAssignedDesc') }}</span>
              </div>
              <InputSwitch v-model="settings.email_notify_ticket_assigned" />
            </div>
            <div class="notification-toggle">
              <div class="toggle-info">
                <span class="toggle-label">{{ t('admin.email.notifyCommentAdded') }}</span>
                <span class="toggle-desc">{{ t('admin.email.notifyCommentAddedDesc') }}</span>
              </div>
              <InputSwitch v-model="settings.email_notify_comment_added" />
            </div>
            <div class="notification-toggle">
              <div class="toggle-info">
                <span class="toggle-label">{{ t('admin.email.notifyTicketResolved') }}</span>
                <span class="toggle-desc">{{ t('admin.email.notifyTicketResolvedDesc') }}</span>
              </div>
              <InputSwitch v-model="settings.email_notify_ticket_resolved" />
            </div>
            <div class="notification-toggle">
              <div class="toggle-info">
                <span class="toggle-label">{{ t('admin.email.notifySlaWarning') }}</span>
                <span class="toggle-desc">{{ t('admin.email.notifySlaWarningDesc') }}</span>
              </div>
              <InputSwitch v-model="settings.email_notify_sla_warning" />
            </div>
            <div class="notification-toggle">
              <div class="toggle-info">
                <span class="toggle-label">{{ t('admin.email.notifySlaBreach') }}</span>
                <span class="toggle-desc">{{ t('admin.email.notifySlaBreachDesc') }}</span>
              </div>
              <InputSwitch v-model="settings.email_notify_sla_breach" />
            </div>
          </div>

          <div class="settings-actions">
            <Button :label="t('common.save')" icon="pi pi-check" @click="saveCategory('email_notifications')" :loading="saving" />
          </div>
        </div>

        <!-- Inbound Email Settings -->
        <div class="settings-card">
          <div class="card-header">
            <div class="card-title">
              <i class="pi pi-inbox"></i>
              {{ t('admin.email.inboundEmail') }}
            </div>
            <p class="card-description">{{ t('admin.email.inboundEmailDesc') }}</p>
          </div>

          <div class="notification-toggle" style="margin-bottom: 1.5rem;">
            <div class="toggle-info">
              <span class="toggle-label">{{ t('admin.email.enableInbound') }}</span>
              <span class="toggle-desc">{{ t('admin.email.enableInboundDesc') }}</span>
            </div>
            <InputSwitch v-model="settings.email_inbound_enabled" />
          </div>

          <div v-if="settings.email_inbound_enabled" class="settings-grid">
            <!-- Folder selection - for all providers, disabled if no connection -->
            <div class="setting-item">
              <label>{{ t('admin.email.inboundFolder') }}</label>
              <Dropdown
                v-model="inboundFolderId"
                :options="availableFolders"
                optionLabel="displayName"
                optionValue="id"
                :placeholder="emailConfig.id ? t('admin.email.selectFolder') : t('admin.email.connectFirst')"
                :loading="loadingFolders"
                :disabled="!emailConfig.id"
                @focus="loadFolders"
                class="admin-dropdown"
              />
              <small>{{ emailConfig.id ? t('admin.email.inboundFolderHint') : t('admin.email.connectAccountFirst') }}</small>
            </div>
            <div class="setting-item">
              <label>{{ t('admin.email.pollInterval') }}</label>
              <InputNumber v-model="settings.email_inbound_poll_interval" :min="30" :max="600" suffix=" sec" />
            </div>
            <div class="setting-item">
              <label>{{ t('admin.email.allowedDomains') }}</label>
              <InputText v-model="settings.email_inbound_allowed_domains" :placeholder="t('admin.email.allowedDomainsPlaceholder')" />
            </div>
          </div>

          <div class="settings-actions">
            <Button :label="t('admin.email.pollNow')" icon="pi pi-refresh" severity="secondary" @click="triggerPollInbox" :loading="pollingInbox" :disabled="!settings.email_inbound_enabled || !emailConfig.id" />
            <Button :label="t('common.save')" icon="pi pi-check" @click="saveInboundSettings" :loading="saving" />
          </div>
        </div>

        <!-- Email Logs -->
        <div class="settings-card email-logs-card">
          <div class="card-header">
            <div class="card-title">
              <i class="pi pi-history"></i>
              {{ t('admin.email.logs') }}
            </div>
          </div>

          <TabView class="logs-tabs">
            <TabPanel :header="t('admin.email.sentEmails')">
              <DataTable :value="sentEmails" :loading="loadingLogs" paginator :rows="10" stripedRows
                :emptyMessage="t('common.noData')" class="compact-table">
                <Column field="created_at" :header="t('common.date')" sortable style="width: 150px">
                  <template #body="{ data }">{{ formatDate(data.created_at) }}</template>
                </Column>
                <Column field="email_type" :header="t('admin.email.type')" sortable style="width: 130px" />
                <Column field="recipient_email" :header="t('admin.email.recipient')" sortable />
                <Column field="subject" :header="t('admin.email.subject')" />
                <Column field="status" :header="t('common.status')" style="width: 100px">
                  <template #body="{ data }">
                    <Tag :value="data.status" :severity="data.status === 'sent' ? 'success' : data.status === 'failed' ? 'danger' : 'warning'" />
                  </template>
                </Column>
              </DataTable>
            </TabPanel>
            <TabPanel :header="t('admin.email.receivedEmails')">
              <DataTable :value="inboundEmails" :loading="loadingLogs" paginator :rows="10" stripedRows
                :emptyMessage="t('common.noData')" class="compact-table">
                <Column field="received_at" :header="t('common.date')" sortable style="width: 150px">
                  <template #body="{ data }">{{ formatDate(data.received_at) }}</template>
                </Column>
                <Column field="from_email" :header="t('admin.email.sender')" sortable />
                <Column field="subject" :header="t('admin.email.subject')" />
                <Column field="processing_status" :header="t('common.status')" style="width: 100px">
                  <template #body="{ data }">
                    <Tag :value="data.processing_status" :severity="data.processing_status === 'processed' ? 'success' : data.processing_status === 'error' ? 'danger' : 'info'" />
                  </template>
                </Column>
                <Column :header="t('admin.email.result')" style="width: 120px">
                  <template #body="{ data }">
                    <span v-if="data.processing_result?.ticket_id">Ticket #{{ data.processing_result.ticket_id }}</span>
                  </template>
                </Column>
              </DataTable>
            </TabPanel>
          </TabView>
        </div>
      </div>

      <!-- SLA Policies -->
      <div v-if="activeSection === 'sla'" class="settings-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="pi pi-clock"></i>
            {{ t('admin.sla.policies') }}
          </h2>
          <p class="section-description">{{ t('admin.sla.policiesDesc') }}</p>
        </div>

        <div class="settings-card">
          <div class="card-header">
            <div class="card-title">{{ t('admin.sla.policies') }}</div>
            <Button :label="t('admin.sla.addPolicy')" icon="pi pi-plus" size="small" @click="openSlaDialog()" />
          </div>

          <div v-if="slaPolicies.length === 0" class="empty-state-inline">
            <i class="pi pi-clock"></i>
            <p>{{ t('admin.sla.noPolicies') }}</p>
            <Button :label="t('admin.sla.addPolicy')" icon="pi pi-plus" @click="openSlaDialog()" />
          </div>

          <div v-else class="sla-list">
            <div v-for="policy in slaPolicies" :key="policy.id" class="sla-item">
              <div class="sla-info">
                <div class="sla-name">
                  {{ policy.name }}
                  <Tag v-if="policy.is_default" :value="t('admin.sla.default')" severity="info" class="default-tag" />
                </div>
                <div class="sla-meta">
                  <span><i class="pi pi-bolt"></i> {{ t('admin.sla.priority.critical') }}: {{ formatDuration(policy.critical_response_time) }} / {{ formatDuration(policy.critical_resolution_time) }}</span>
                  <span><i class="pi pi-exclamation-triangle"></i> {{ t('admin.sla.priority.high') }}: {{ formatDuration(policy.high_response_time) }} / {{ formatDuration(policy.high_resolution_time) }}</span>
                </div>
              </div>
              <div class="sla-actions">
                <Button icon="pi pi-pencil" text rounded @click="openSlaDialog(policy)" />
                <Button icon="pi pi-trash" text rounded severity="danger" @click="confirmDeleteSla(policy)" :disabled="policy.is_default" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Maintenance Settings -->
      <div v-if="activeSection === 'maintenance'" class="settings-section">
        <div class="section-header">
          <h2 class="section-title">
            <i class="pi pi-wrench"></i>
            {{ t('admin.maintenance.configuration') }}
          </h2>
        </div>

        <div class="settings-card">
          <div class="notification-toggle" style="margin-bottom: 1.5rem;">
            <div class="toggle-info">
              <span class="toggle-label">{{ t('admin.maintenance.enableMode') }}</span>
              <span class="toggle-desc">{{ t('admin.maintenance.enableModeDesc') }}</span>
            </div>
            <InputSwitch v-model="settings.maintenance_mode" />
          </div>

          <div v-if="settings.maintenance_mode" class="setting-item setting-item--full">
            <label>{{ t('admin.maintenance.message') }}</label>
            <Textarea v-model="settings.maintenance_message" rows="3" />
          </div>

          <div class="settings-grid" style="margin-top: 1.5rem;">
            <div class="setting-item">
              <label>{{ t('admin.maintenance.auditRetention') }}</label>
              <InputNumber v-model="settings.audit_log_retention_days" :min="7" :max="365" suffix=" days" />
            </div>
            <div class="setting-item setting-item--toggle">
              <label>{{ t('admin.maintenance.enableBackup') }}</label>
              <InputSwitch v-model="settings.backup_enabled" />
            </div>
          </div>

          <div class="settings-actions">
            <Button :label="t('common.save')" icon="pi pi-check" @click="saveCategory('maintenance')" :loading="saving" />
          </div>
        </div>
      </div>
    </div>

    <!-- Microsoft 365 Connection Dialog -->
    <Dialog v-model:visible="showM365Dialog" :header="t('admin.email.connectMicrosoft365')" modal :style="{ width: '550px' }" class="config-dialog">
      <div class="connection-steps">
        <div class="step-info">
          <i class="pi pi-info-circle"></i>
          <p>{{ t('admin.email.m365Instructions') }}</p>
        </div>

        <!-- Error message -->
        <div v-if="connectionError" class="connection-error">
          <i class="pi pi-times-circle"></i>
          <div>
            <strong>{{ t('admin.email.connectionFailed') }}</strong>
            <p>{{ connectionError }}</p>
          </div>
        </div>

        <div class="config-form">
          <div class="form-group">
            <label>{{ t('admin.email.tenantId') }} <span class="required">*</span></label>
            <InputText v-model="m365Form.tenant_id" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </div>
          <div class="form-group">
            <label>{{ t('admin.email.clientId') }} <span class="required">*</span></label>
            <InputText v-model="m365Form.client_id" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
          </div>
          <div class="form-group">
            <label>{{ t('admin.email.clientSecret') }} <span class="required">*</span></label>
            <Password v-model="m365Form.client_secret" toggleMask :feedback="false" inputClass="w-full" />
          </div>
          <div class="form-group">
            <label>{{ t('admin.email.mailbox') }} <span class="required">*</span></label>
            <InputText v-model="m365Form.mailbox" placeholder="support@company.com" />
            <small>{{ t('admin.email.mailboxHint') }}</small>
          </div>
          <div class="form-group">
            <label>{{ t('admin.email.fromName') }}</label>
            <InputText v-model="m365Form.from_name" placeholder="Inframate Support" />
          </div>
        </div>
      </div>

      <template #footer>
        <Button :label="t('common.cancel')" text @click="showM365Dialog = false" />
        <Button :label="t('admin.email.testAndConnect')" icon="pi pi-check" @click="testAndSaveM365Config" :loading="savingEmail" />
      </template>
    </Dialog>

    <!-- SMTP/IMAP Connection Dialog -->
    <Dialog v-model:visible="showSmtpDialog" :header="t('admin.email.connectSmtpImap')" modal :style="{ width: '650px' }" class="config-dialog">
      <!-- Error message -->
      <div v-if="connectionError" class="connection-error">
        <i class="pi pi-times-circle"></i>
        <div>
          <strong>{{ t('admin.email.connectionFailed') }}</strong>
          <p>{{ connectionError }}</p>
        </div>
      </div>

      <TabView class="smtp-tabs">
        <TabPanel :header="t('admin.email.smtpConfig')">
          <div class="config-form">
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('admin.email.smtpHost') }} <span class="required">*</span></label>
                <InputText v-model="smtpForm.smtp_host" placeholder="smtp.example.com" />
              </div>
              <div class="form-group form-group--small">
                <label>{{ t('admin.email.smtpPort') }}</label>
                <InputNumber v-model="smtpForm.smtp_port" :min="1" :max="65535" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('admin.email.smtpUsername') }}</label>
                <InputText v-model="smtpForm.smtp_username" />
              </div>
              <div class="form-group">
                <label>{{ t('admin.email.smtpPassword') }}</label>
                <Password v-model="smtpForm.smtp_password" toggleMask :feedback="false" inputClass="w-full" />
              </div>
            </div>
            <div class="form-group form-group--inline">
              <Checkbox v-model="smtpForm.smtp_use_tls" :binary="true" inputId="smtp_tls" />
              <label for="smtp_tls">{{ t('admin.email.useTls') }}</label>
            </div>
          </div>
        </TabPanel>
        <TabPanel :header="t('admin.email.imapConfig')">
          <div class="config-form">
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('admin.email.imapHost') }}</label>
                <InputText v-model="smtpForm.imap_host" placeholder="imap.example.com" />
              </div>
              <div class="form-group form-group--small">
                <label>{{ t('admin.email.imapPort') }}</label>
                <InputNumber v-model="smtpForm.imap_port" :min="1" :max="65535" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>{{ t('admin.email.imapFolder') }}</label>
                <InputText v-model="smtpForm.imap_folder" placeholder="INBOX" />
              </div>
            </div>
            <div class="form-group form-group--inline">
              <Checkbox v-model="smtpForm.imap_use_ssl" :binary="true" inputId="imap_ssl" />
              <label for="imap_ssl">{{ t('admin.email.useSsl') }}</label>
            </div>
          </div>
        </TabPanel>
        <TabPanel :header="t('admin.email.senderSettings')">
          <div class="config-form">
            <div class="form-group">
              <label>{{ t('admin.email.fromEmail') }} <span class="required">*</span></label>
              <InputText v-model="smtpForm.from_email" placeholder="noreply@company.com" />
            </div>
            <div class="form-group">
              <label>{{ t('admin.email.fromName') }}</label>
              <InputText v-model="smtpForm.from_name" placeholder="Inframate Support" />
            </div>
            <div class="form-group">
              <label>{{ t('admin.email.replyTo') }}</label>
              <InputText v-model="smtpForm.reply_to_email" placeholder="support@company.com" />
            </div>
          </div>
        </TabPanel>
      </TabView>

      <template #footer>
        <Button :label="t('common.cancel')" text @click="showSmtpDialog = false" />
        <Button :label="t('admin.email.testAndConnect')" icon="pi pi-check" @click="testAndSaveSmtpConfig" :loading="savingEmail" />
      </template>
    </Dialog>

    <!-- SLA Policy Dialog -->
    <Dialog v-model:visible="slaDialogVisible" :header="editingSla ? t('admin.sla.editPolicy') : t('admin.sla.addPolicy')" modal :style="{ width: '700px' }" class="config-dialog">
      <div class="config-form">
        <div class="form-row">
          <div class="form-group">
            <label>{{ t('admin.sla.policyName') }} <span class="required">*</span></label>
            <InputText v-model="slaForm.name" />
          </div>
          <div class="form-group">
            <label>{{ t('admin.sla.description') }}</label>
            <InputText v-model="slaForm.description" />
          </div>
        </div>

        <div class="sla-times-section">
          <h4>{{ t('admin.sla.slaTimes') }}</h4>
          <p class="help-text">{{ t('admin.sla.slaTimesDesc') }}</p>

          <table class="sla-times-table">
            <thead>
              <tr>
                <th>{{ t('tickets.priority') }}</th>
                <th>{{ t('admin.sla.responseTime') }} (min)</th>
                <th>{{ t('admin.sla.resolutionTime') }} (min)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><Tag severity="danger">{{ t('tickets.priorities.critical') }}</Tag></td>
                <td><InputNumber v-model="slaForm.critical_response_time" :min="1" /></td>
                <td><InputNumber v-model="slaForm.critical_resolution_time" :min="1" /></td>
              </tr>
              <tr>
                <td><Tag severity="warn">{{ t('tickets.priorities.high') }}</Tag></td>
                <td><InputNumber v-model="slaForm.high_response_time" :min="1" /></td>
                <td><InputNumber v-model="slaForm.high_resolution_time" :min="1" /></td>
              </tr>
              <tr>
                <td><Tag severity="warning">{{ t('tickets.priorities.medium') }}</Tag></td>
                <td><InputNumber v-model="slaForm.medium_response_time" :min="1" /></td>
                <td><InputNumber v-model="slaForm.medium_resolution_time" :min="1" /></td>
              </tr>
              <tr>
                <td><Tag severity="info">{{ t('tickets.priorities.low') }}</Tag></td>
                <td><InputNumber v-model="slaForm.low_response_time" :min="1" /></td>
                <td><InputNumber v-model="slaForm.low_resolution_time" :min="1" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="business-hours-section">
          <h4>{{ t('admin.sla.businessHours') }}</h4>

          <div class="form-group form-group--inline" style="margin-bottom: 1rem;">
            <Checkbox v-model="slaForm.business_hours_only" :binary="true" inputId="business_hours" />
            <label for="business_hours">{{ t('admin.sla.businessHoursOnly') }}</label>
          </div>

          <div v-if="slaForm.business_hours_only" class="form-row">
            <div class="form-group">
              <label>{{ t('admin.sla.startTime') }}</label>
              <InputText v-model="slaForm.business_start" placeholder="09:00" />
            </div>
            <div class="form-group">
              <label>{{ t('admin.sla.endTime') }}</label>
              <InputText v-model="slaForm.business_end" placeholder="18:00" />
            </div>
            <div class="form-group form-group--full">
              <label>{{ t('admin.sla.businessDays') }}</label>
              <MultiSelect v-model="slaForm.business_days" :options="dayOptions" optionLabel="label" optionValue="value" />
            </div>
          </div>
        </div>

        <div class="form-group form-group--inline">
          <Checkbox v-model="slaForm.is_default" :binary="true" inputId="sla_default" />
          <label for="sla_default">{{ t('admin.sla.setAsDefault') }}</label>
        </div>
      </div>

      <template #footer>
        <Button :label="t('common.cancel')" text @click="slaDialogVisible = false" />
        <Button :label="t('common.save')" icon="pi pi-check" @click="saveSlaPolicy" :loading="savingSla" />
      </template>
    </Dialog>

    <!-- Delete SLA Confirmation -->
    <Dialog v-model:visible="deleteSlaDialogVisible" :header="t('common.confirm')" modal :style="{ width: '400px' }">
      <p>{{ t('admin.sla.confirmDelete') }}</p>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="deleteSlaDialogVisible = false" />
        <Button :label="t('common.delete')" severity="danger" @click="deleteSlaPolicy" :loading="deletingSla" />
      </template>
    </Dialog>

    <!-- Delete Email Config Confirmation -->
    <Dialog v-model:visible="deleteConfigDialogVisible" :header="t('common.confirm')" modal :style="{ width: '400px' }">
      <p>{{ t('admin.email.confirmDeleteConfig') }}</p>
      <template #footer>
        <Button :label="t('common.cancel')" text @click="deleteConfigDialogVisible = false" />
        <Button :label="t('common.delete')" severity="danger" @click="deleteEmailConfig" :loading="deletingConfig" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import api from '../api'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import InputSwitch from 'primevue/inputswitch'
import Password from 'primevue/password'
import Checkbox from 'primevue/checkbox'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const { t } = useI18n()
const toast = useToast()

// Navigation
const activeSection = ref('general')

// State
const saving = ref(false)
const savingEmail = ref(false)
const pollingInbox = ref(false)
const loadingLogs = ref(false)
const loadingFolders = ref(false)
const sentEmails = ref([])
const inboundEmails = ref([])
const m365Folders = ref([])
const imapFolders = ref([])
const inboundFolderId = ref(null)
const connectionError = ref('')

// Computed: available folders based on provider type
const availableFolders = computed(() => {
  if (emailConfig.provider_type === 'microsoft_365') {
    return m365Folders.value
  } else if (emailConfig.provider_type === 'smtp_imap') {
    return imapFolders.value
  }
  return []
})

// Email dialogs
const showM365Dialog = ref(false)
const showSmtpDialog = ref(false)
const deleteConfigDialogVisible = ref(false)
const deletingConfig = ref(false)

// SLA state
const loadingSla = ref(false)
const savingSla = ref(false)
const deletingSla = ref(false)
const slaPolicies = ref([])
const slaDialogVisible = ref(false)
const deleteSlaDialogVisible = ref(false)
const editingSla = ref(null)
const slaToDelete = ref(null)

const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Francais', value: 'fr' }
]

const dayOptions = [
  { label: t('admin.sla.days.monday'), value: 0 },
  { label: t('admin.sla.days.tuesday'), value: 1 },
  { label: t('admin.sla.days.wednesday'), value: 2 },
  { label: t('admin.sla.days.thursday'), value: 3 },
  { label: t('admin.sla.days.friday'), value: 4 },
  { label: t('admin.sla.days.saturday'), value: 5 },
  { label: t('admin.sla.days.sunday'), value: 6 }
]

// Email configuration
const emailConfig = reactive({
  id: null,
  provider_type: '',
  is_active: true,
  m365_mailbox: '',
  m365_folder_id: '',
  smtp_host: '',
  from_email: '',
  from_name: 'Inframate'
})

// M365 form
const m365Form = reactive({
  tenant_id: '',
  client_id: '',
  client_secret: '',
  mailbox: '',
  from_name: 'Inframate'
})

// SMTP form
const smtpForm = reactive({
  smtp_host: '',
  smtp_port: 587,
  smtp_username: '',
  smtp_password: '',
  smtp_use_tls: true,
  imap_host: '',
  imap_port: 993,
  imap_use_ssl: true,
  imap_folder: 'INBOX',
  from_email: '',
  from_name: 'Inframate',
  reply_to_email: ''
})

// SLA form
const slaForm = reactive({
  id: null,
  name: '',
  description: '',
  critical_response_time: 15,
  critical_resolution_time: 240,
  high_response_time: 60,
  high_resolution_time: 480,
  medium_response_time: 240,
  medium_resolution_time: 1440,
  low_response_time: 480,
  low_resolution_time: 2880,
  business_hours_only: true,
  business_start: '09:00',
  business_end: '18:00',
  business_days: [0, 1, 2, 3, 4],
  is_default: false
})

// Settings
const settings = reactive({
  site_name: 'Inframate',
  site_url: 'http://localhost:3000',
  default_language: 'en',
  session_timeout_minutes: 30,
  items_per_page: 25,
  min_password_length: 8,
  require_mfa_for_admins: false,
  login_rate_limit: 5,
  session_concurrent_limit: 5,
  maintenance_mode: false,
  maintenance_message: '',
  audit_log_retention_days: 90,
  backup_enabled: false,
  email_notify_ticket_created: true,
  email_notify_ticket_assigned: true,
  email_notify_comment_added: true,
  email_notify_ticket_resolved: true,
  email_notify_sla_warning: true,
  email_notify_sla_breach: true,
  email_inbound_enabled: false,
  email_inbound_poll_interval: 60,
  email_inbound_allowed_domains: ''
})

const categoryKeys = {
  general: ['site_name', 'site_url', 'default_language', 'session_timeout_minutes', 'items_per_page'],
  security: ['min_password_length', 'require_mfa_for_admins', 'login_rate_limit', 'session_concurrent_limit'],
  maintenance: ['maintenance_mode', 'maintenance_message', 'audit_log_retention_days', 'backup_enabled'],
  email_notifications: ['email_notify_ticket_created', 'email_notify_ticket_assigned', 'email_notify_comment_added', 'email_notify_ticket_resolved', 'email_notify_sla_warning', 'email_notify_sla_breach'],
  email_inbound: ['email_inbound_enabled', 'email_inbound_poll_interval', 'email_inbound_allowed_domains']
}

// Load functions
const loadSettings = async () => {
  try {
    const response = await api.get('/settings/')
    response.data.forEach(setting => {
      if (setting.key in settings) {
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
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('admin.errors.loadFailed'), life: 3000 })
  }
}

const saveCategory = async (category) => {
  saving.value = true
  try {
    const keys = categoryKeys[category]
    for (const key of keys) {
      let value = settings[key]
      if (typeof value === 'boolean') {
        value = value ? 'true' : 'false'
      } else if (typeof value === 'number') {
        value = value.toString()
      }
      await api.put(`/settings/${key}`, { value })
    }
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('admin.messages.saved'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('admin.errors.saveFailed'), life: 3000 })
  } finally {
    saving.value = false
  }
}

// Email configuration
const loadEmailConfig = async () => {
  try {
    const response = await api.get('/email/configurations')
    if (response.data.length > 0) {
      Object.assign(emailConfig, response.data[0])
      // Initialize folder based on provider type
      if (emailConfig.provider_type === 'microsoft_365') {
        inboundFolderId.value = emailConfig.m365_folder_id || null
      } else if (emailConfig.provider_type === 'smtp_imap') {
        inboundFolderId.value = emailConfig.imap_folder || 'INBOX'
      }
    }
  } catch {
    // No config yet
  }
}

const loadEmailLogs = async () => {
  loadingLogs.value = true
  try {
    const [sentResponse, inboundResponse] = await Promise.all([
      api.get('/email/sent', { params: { limit: 50 } }),
      api.get('/email/inbound', { params: { limit: 50 } })
    ])
    sentEmails.value = sentResponse.data
    inboundEmails.value = inboundResponse.data
  } catch {
    // Logs might not be available
  } finally {
    loadingLogs.value = false
  }
}

const loadM365Folders = async () => {
  if (!emailConfig.id || emailConfig.provider_type !== 'microsoft_365') return
  if (m365Folders.value.length > 0) return // Already loaded

  loadingFolders.value = true
  try {
    const response = await api.get(`/email/configurations/${emailConfig.id}/m365-folders`)
    m365Folders.value = response.data.folders || response.data
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('admin.email.fetchFoldersFailed'), life: 3000 })
  } finally {
    loadingFolders.value = false
  }
}

const loadImapFolders = async () => {
  if (!emailConfig.id || emailConfig.provider_type !== 'smtp_imap') return
  if (imapFolders.value.length > 0) return // Already loaded

  loadingFolders.value = true
  try {
    const response = await api.get(`/email/configurations/${emailConfig.id}/imap-folders`)
    imapFolders.value = response.data.folders || response.data
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('admin.email.fetchFoldersFailed'), life: 3000 })
  } finally {
    loadingFolders.value = false
  }
}

const loadFolders = async () => {
  if (!emailConfig.id) return
  if (emailConfig.provider_type === 'microsoft_365') {
    await loadM365Folders()
  } else if (emailConfig.provider_type === 'smtp_imap') {
    await loadImapFolders()
  }
}

const connectMicrosoft365 = () => {
  connectionError.value = ''
  Object.assign(m365Form, {
    tenant_id: '',
    client_id: '',
    client_secret: '',
    mailbox: '',
    from_name: 'Inframate'
  })
  showM365Dialog.value = true
}

const connectSmtpImap = () => {
  connectionError.value = ''
  Object.assign(smtpForm, {
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_use_tls: true,
    imap_host: '',
    imap_port: 993,
    imap_use_ssl: true,
    imap_folder: 'INBOX',
    from_email: '',
    from_name: 'Inframate',
    reply_to_email: ''
  })
  showSmtpDialog.value = true
}

const testAndSaveM365Config = async () => {
  if (!m365Form.tenant_id || !m365Form.client_id || !m365Form.client_secret || !m365Form.mailbox) {
    toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('validation.fillRequiredFields'), life: 3000 })
    return
  }

  connectionError.value = ''
  savingEmail.value = true

  try {
    // Test the connection FIRST before saving
    const testResponse = await api.post('/email/test-m365-credentials', {
      tenant_id: m365Form.tenant_id,
      client_id: m365Form.client_id,
      client_secret: m365Form.client_secret,
      mailbox: m365Form.mailbox
    })

    // If test succeeds, save the configuration
    const payload = {
      name: 'Microsoft 365',
      provider_type: 'microsoft_365',
      is_active: true,
      is_outbound_enabled: true,
      m365_tenant_id: m365Form.tenant_id,
      m365_client_id: m365Form.client_id,
      m365_client_secret: m365Form.client_secret,
      m365_mailbox: m365Form.mailbox,
      from_email: m365Form.mailbox,
      from_name: m365Form.from_name
    }

    const response = await api.post('/email/configurations', payload)

    Object.assign(emailConfig, {
      id: response.data.id,
      provider_type: 'microsoft_365',
      m365_tenant_id: m365Form.tenant_id,
      m365_client_id: m365Form.client_id,
      m365_mailbox: m365Form.mailbox,
      from_email: m365Form.mailbox,
      from_name: m365Form.from_name,
      is_active: true
    })

    showM365Dialog.value = false
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('admin.email.connectionSuccess'), life: 3000 })
  } catch (error) {
    // Show detailed error message
    const errorDetail = error.response?.data?.detail || error.message || t('admin.email.connectionFailed')
    connectionError.value = errorDetail
  } finally {
    savingEmail.value = false
  }
}

const testAndSaveSmtpConfig = async () => {
  if (!smtpForm.smtp_host || !smtpForm.from_email) {
    toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('validation.fillRequiredFields'), life: 3000 })
    return
  }

  connectionError.value = ''
  savingEmail.value = true

  try {
    // Test the SMTP connection FIRST before saving
    await api.post('/email/test-smtp-credentials', {
      smtp_host: smtpForm.smtp_host,
      smtp_port: smtpForm.smtp_port,
      smtp_username: smtpForm.smtp_username,
      smtp_password: smtpForm.smtp_password,
      smtp_use_tls: smtpForm.smtp_use_tls
    })

    // If test succeeds, save the configuration
    const payload = {
      name: 'SMTP/IMAP',
      provider_type: 'smtp_imap',
      is_active: true,
      is_outbound_enabled: true,
      is_inbound_enabled: !!smtpForm.imap_host,
      ...smtpForm
    }

    const response = await api.post('/email/configurations', payload)

    Object.assign(emailConfig, {
      id: response.data.id,
      provider_type: 'smtp_imap',
      smtp_host: smtpForm.smtp_host,
      from_email: smtpForm.from_email,
      from_name: smtpForm.from_name,
      is_active: true
    })

    showSmtpDialog.value = false
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('admin.email.connectionSuccess'), life: 3000 })
  } catch (error) {
    // Show detailed error message
    const errorDetail = error.response?.data?.detail || error.message || t('admin.email.connectionFailed')
    connectionError.value = errorDetail
  } finally {
    savingEmail.value = false
  }
}

const saveInboundSettings = async () => {
  saving.value = true
  try {
    // Save settings
    const keys = categoryKeys.email_inbound
    for (const key of keys) {
      let value = settings[key]
      if (typeof value === 'boolean') {
        value = value ? 'true' : 'false'
      } else if (typeof value === 'number') {
        value = value.toString()
      }
      await api.put(`/settings/${key}`, { value })
    }

    // Update folder based on provider type
    if (emailConfig.id && inboundFolderId.value) {
      if (emailConfig.provider_type === 'microsoft_365') {
        await api.put(`/email/configurations/${emailConfig.id}`, {
          m365_folder_id: inboundFolderId.value
        })
        emailConfig.m365_folder_id = inboundFolderId.value
      } else if (emailConfig.provider_type === 'smtp_imap') {
        await api.put(`/email/configurations/${emailConfig.id}`, {
          imap_folder: inboundFolderId.value
        })
        emailConfig.imap_folder = inboundFolderId.value
      }
    }

    toast.add({ severity: 'success', summary: t('common.success'), detail: t('admin.messages.saved'), life: 3000 })
  } catch {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('admin.errors.saveFailed'), life: 3000 })
  } finally {
    saving.value = false
  }
}

const confirmDeleteConfig = () => {
  deleteConfigDialogVisible.value = true
}

const deleteEmailConfig = async () => {
  deletingConfig.value = true
  try {
    await api.delete(`/email/configurations/${emailConfig.id}`)
    Object.assign(emailConfig, { id: null, provider_type: '', m365_mailbox: '', smtp_host: '', from_email: '' })
    m365Folders.value = []
    inboundFolderId.value = null
    deleteConfigDialogVisible.value = false
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('common.deleted'), life: 3000 })
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('common.error'), life: 3000 })
  } finally {
    deletingConfig.value = false
  }
}

const triggerPollInbox = async () => {
  pollingInbox.value = true
  try {
    await api.post('/email/poll-inbox')
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('admin.email.pollTriggered'), life: 3000 })
    setTimeout(loadEmailLogs, 2000)
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('admin.email.pollFailed'), life: 3000 })
  } finally {
    pollingInbox.value = false
  }
}

// SLA Methods
const loadSlaPolicies = async () => {
  loadingSla.value = true
  try {
    const response = await api.get('/tickets/sla-policies')
    slaPolicies.value = response.data
  } catch {
    // No policies yet
  } finally {
    loadingSla.value = false
  }
}

const openSlaDialog = (policy = null) => {
  if (policy) {
    editingSla.value = policy
    Object.assign(slaForm, policy)
  } else {
    editingSla.value = null
    Object.assign(slaForm, {
      id: null,
      name: '',
      description: '',
      critical_response_time: 15,
      critical_resolution_time: 240,
      high_response_time: 60,
      high_resolution_time: 480,
      medium_response_time: 240,
      medium_resolution_time: 1440,
      low_response_time: 480,
      low_resolution_time: 2880,
      business_hours_only: true,
      business_start: '09:00',
      business_end: '18:00',
      business_days: [0, 1, 2, 3, 4],
      is_default: false
    })
  }
  slaDialogVisible.value = true
}

const saveSlaPolicy = async () => {
  if (!slaForm.name) {
    toast.add({ severity: 'warn', summary: t('common.warning'), detail: t('validation.fillRequiredFields'), life: 3000 })
    return
  }

  savingSla.value = true
  try {
    const payload = { ...slaForm }
    delete payload.id

    if (editingSla.value) {
      await api.put(`/tickets/sla-policies/${editingSla.value.id}`, payload)
    } else {
      await api.post('/tickets/sla-policies', payload)
    }

    toast.add({ severity: 'success', summary: t('common.success'), detail: t('admin.sla.policySaved'), life: 3000 })
    slaDialogVisible.value = false
    loadSlaPolicies()
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('admin.sla.policySaveFailed'), life: 3000 })
  } finally {
    savingSla.value = false
  }
}

const confirmDeleteSla = (policy) => {
  slaToDelete.value = policy
  deleteSlaDialogVisible.value = true
}

const deleteSlaPolicy = async () => {
  deletingSla.value = true
  try {
    await api.delete(`/tickets/sla-policies/${slaToDelete.value.id}`)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('admin.sla.policyDeleted'), life: 3000 })
    deleteSlaDialogVisible.value = false
    loadSlaPolicies()
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: error.response?.data?.detail || t('admin.sla.policyDeleteFailed'), life: 3000 })
  } finally {
    deletingSla.value = false
  }
}

// Utility functions
const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString()
}

const formatDuration = (minutes) => {
  if (!minutes) return '-'
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return mins > 0 ? `${hours}h${mins}m` : `${hours}h`
}

onMounted(() => {
  loadSettings()
  loadEmailConfig()
  loadEmailLogs()
  loadSlaPolicies()
})
</script>

<style scoped>
/* ==================== Page Layout ==================== */
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem clamp(1rem, 3vw, 2rem);
  min-height: 100%;
}

/* ==================== Header ==================== */
.page-header {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.header-title-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.page-title i {
  color: var(--primary);
}

.page-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

/* ==================== Navigation Pills ==================== */
.nav-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.nav-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.nav-pill:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}

.nav-pill.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.nav-pill i {
  font-size: 0.875rem;
}

/* ==================== Content ==================== */
.admin-content {
  flex: 1;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-header {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-title i {
  color: var(--primary);
}

.section-description {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

/* ==================== Settings Card ==================== */
.settings-card {
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.card-title i {
  color: var(--text-muted);
}

.card-description {
  margin: 0.25rem 0 0 0;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

/* ==================== Settings Grid ==================== */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-item label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.setting-item small {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.setting-item--toggle {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.setting-item--full {
  grid-column: 1 / -1;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-default);
}

/* ==================== Email Section ==================== */
.empty-connections {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 2rem;
  color: var(--text-muted);
}

.empty-connections i {
  font-size: 2rem;
}

.empty-connections p {
  margin: 0;
  font-size: 0.875rem;
}

.connected-account {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
}

.account-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.account-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 1.25rem;
}

.account-icon.microsoft_365 {
  background: rgba(0, 120, 212, 0.1);
  color: #0078d4;
}

.account-icon.smtp_imap {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.account-details {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.account-name {
  font-weight: 600;
  color: var(--text-primary);
}

.account-type {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.account-actions {
  display: flex;
  gap: 0.25rem;
}

.connect-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.connect-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-radius: var(--radius-lg);
  border: 2px dashed var(--border-default);
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--text-secondary);
  flex: 1;
  min-width: 200px;
  justify-content: center;
}

.connect-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

.connect-btn i {
  font-size: 1.25rem;
}

.connect-btn--microsoft:hover {
  border-color: #0078d4;
  color: #0078d4;
  background: rgba(0, 120, 212, 0.08);
}

.connect-btn--smtp:hover {
  border-color: #22c55e;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.08);
}

/* ==================== Connection Error ==================== */
.connection-error {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: #dc2626;
  margin-bottom: 1rem;
}

.connection-error i {
  flex-shrink: 0;
  font-size: 1.25rem;
  margin-top: 2px;
}

.connection-error strong {
  display: block;
  margin-bottom: 0.25rem;
}

.connection-error p {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  word-break: break-word;
}

/* ==================== Notification Toggles ==================== */
.notification-toggles {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.notification-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.toggle-info {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.toggle-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
}

.toggle-desc {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ==================== SLA List ==================== */
.sla-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sla-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.sla-info {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.sla-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: var(--text-primary);
}

.default-tag {
  font-size: 0.625rem;
}

.sla-meta {
  display: flex;
  gap: 1.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.sla-meta span {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.sla-actions {
  display: flex;
  gap: 0.25rem;
}

.empty-state-inline {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
  text-align: center;
}

.empty-state-inline i {
  font-size: 2.5rem;
  color: var(--text-secondary);
  opacity: 0.7;
}

.empty-state-inline p {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--text-secondary);
  font-weight: 500;
}

/* ==================== Dialog Forms ==================== */
.config-dialog :deep(.p-dialog-content) {
  padding: 1.5rem;
}

.connection-steps {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.step-info {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(59, 130, 246, 0.08);
  border-radius: var(--radius-md);
  color: #3b82f6;
}

.step-info i {
  flex-shrink: 0;
  margin-top: 2px;
}

.step-info p {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.5;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group small {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.form-group--small {
  max-width: 120px;
}

.form-group--inline {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.form-group--full {
  grid-column: 1 / -1;
}

.required {
  color: var(--danger);
}

/* ==================== SLA Dialog ==================== */
.sla-times-section,
.business-hours-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-default);
}

.sla-times-section h4,
.business-hours-section h4 {
  margin: 0 0 0.25rem 0;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}

.help-text {
  margin: 0 0 1rem 0;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.sla-times-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.sla-times-table th {
  padding: 0.75rem;
  text-align: left;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-default);
}

.sla-times-table td {
  padding: 0.75rem;
  border-bottom: 1px solid var(--border-default);
}

.sla-times-table tr:last-child td {
  border-bottom: none;
}

.sla-times-table :deep(.p-inputnumber) {
  width: 100%;
}

/* ==================== Logs Tabs ==================== */
.email-logs-card .logs-tabs :deep(.p-tabview-panels) {
  padding: 0;
  background: transparent;
}

.email-logs-card .logs-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border-bottom: 1px solid var(--border-default);
}

.email-logs-card .logs-tabs :deep(.p-tabview-nav-link) {
  background: transparent;
}

.email-logs-card .compact-table :deep(.p-datatable) {
  background: transparent;
}

.email-logs-card .compact-table :deep(.p-datatable-wrapper) {
  background: transparent;
}

.email-logs-card .compact-table :deep(.p-datatable-thead > tr > th) {
  padding: 0.625rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  background: var(--bg-secondary);
  color: var(--text-muted);
  border-color: var(--border-default);
}

.email-logs-card .compact-table :deep(.p-datatable-tbody > tr) {
  background: transparent;
}

.email-logs-card .compact-table :deep(.p-datatable-tbody > tr > td) {
  padding: 0.625rem 1rem;
  font-size: 0.8125rem;
  background: transparent;
  border-color: var(--border-default);
  color: var(--text-primary);
}

.email-logs-card .compact-table :deep(.p-datatable-tbody > tr:nth-child(even)) {
  background: var(--bg-secondary);
}

.email-logs-card .compact-table :deep(.p-paginator) {
  background: transparent;
  border-color: var(--border-default);
}

/* ==================== SMTP Dialog Tabs ==================== */
.smtp-tabs :deep(.p-tabview) {
  background: transparent;
}

.smtp-tabs :deep(.p-tabview-panels) {
  padding: 1rem 0 0 0;
  background: transparent;
}

.smtp-tabs :deep(.p-tabview-panel) {
  background: transparent;
}

.smtp-tabs :deep(.p-tabview-nav) {
  background: transparent;
  border-bottom: 1px solid var(--border-default);
}

.smtp-tabs :deep(.p-tabview-nav-link) {
  background: transparent;
}

.smtp-tabs :deep(.p-tabview-nav li.p-highlight .p-tabview-nav-link) {
  background: transparent;
}

/* Config dialog general fixes for light theme */
.config-dialog :deep(.p-dialog) {
  background: var(--bg-card);
}

.config-dialog :deep(.p-dialog-header) {
  background: var(--bg-card);
}

.config-dialog :deep(.p-dialog-content) {
  background: var(--bg-card);
}

.config-dialog :deep(.p-dialog-footer) {
  background: var(--bg-card);
}

/* ==================== Admin Dropdown Style ==================== */
/* Clean dropdown style for settings pages */
.admin-dropdown:deep(.p-dropdown),
:deep(.admin-dropdown.p-dropdown) {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-default) !important;
  border-radius: var(--radius-md) !important;
  box-shadow: none !important;
  outline: none !important;
  position: relative;
  padding: 0 !important;
  width: 100%;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.admin-dropdown:deep(.p-dropdown.p-focus),
.admin-dropdown:deep(.p-dropdown:hover),
:deep(.admin-dropdown.p-dropdown.p-focus),
:deep(.admin-dropdown.p-dropdown:hover) {
  background: var(--bg-secondary) !important;
  border-color: var(--primary) !important;
  box-shadow: none !important;
}

.admin-dropdown:deep(.p-dropdown .p-dropdown-label),
:deep(.admin-dropdown.p-dropdown .p-dropdown-label) {
  padding: 0.625rem 2.5rem 0.625rem 0.875rem !important;
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--text-primary);
  background: transparent !important;
}

.admin-dropdown:deep(.p-dropdown .p-dropdown-label.p-placeholder),
:deep(.admin-dropdown.p-dropdown .p-dropdown-label.p-placeholder) {
  color: var(--text-muted);
}

.admin-dropdown:deep(.p-dropdown .p-dropdown-trigger),
:deep(.admin-dropdown.p-dropdown .p-dropdown-trigger) {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  width: auto;
  color: var(--text-muted);
  background: transparent !important;
}

.admin-dropdown:deep(.p-dropdown .p-dropdown-clear-icon),
:deep(.admin-dropdown.p-dropdown .p-dropdown-clear-icon) {
  position: absolute;
  right: 2rem;
  top: 0;
  bottom: 0;
  margin: auto;
  height: fit-content;
  color: var(--text-muted);
  font-size: 0.75rem;
  cursor: pointer;
}

.admin-dropdown:deep(.p-dropdown .p-dropdown-clear-icon:hover),
:deep(.admin-dropdown.p-dropdown .p-dropdown-clear-icon:hover) {
  color: var(--primary);
}

/* Disabled state */
.admin-dropdown:deep(.p-dropdown.p-disabled),
:deep(.admin-dropdown.p-dropdown.p-disabled) {
  background: var(--bg-tertiary) !important;
  border-color: var(--border-default) !important;
  opacity: 0.6;
  cursor: not-allowed;
}

.admin-dropdown:deep(.p-dropdown.p-disabled .p-dropdown-label),
:deep(.admin-dropdown.p-dropdown.p-disabled .p-dropdown-label) {
  color: var(--text-muted);
}

/* ==================== Responsive ==================== */
@media (max-width: 768px) {
  .nav-pills {
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 0.5rem;
  }

  .nav-pill {
    flex-shrink: 0;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .connect-buttons {
    flex-direction: column;
  }

  .sla-meta {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>
