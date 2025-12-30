<template>
  <div class="relative">
    <Button icon="pi pi-bell" text rounded class="!text-slate-500 dark:!text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700"
            @click="togglePanel" v-badge.danger="unreadCount || null" />

    <!-- Notification Panel -->
    <transition name="fade">
      <div v-if="showPanel" class="absolute right-0 top-12 w-80 max-h-96 overflow-hidden rounded-xl shadow-2xl z-50"
           style="background-color: var(--bg-card); border: 1px solid var(--border-color);">
        <div class="flex items-center justify-between p-4 border-b" style="border-color: var(--border-color);">
          <h3 class="font-semibold">{{ t('notifications.title') }}</h3>
          <Button v-if="notifications.length" :label="t('notifications.markAllRead')" text size="small"
                  class="!text-xs" @click="markAllRead" />
        </div>

        <div class="max-h-72 overflow-auto">
          <div v-for="notification in notifications" :key="notification.id"
               class="p-3 border-b cursor-pointer transition-colors hover:bg-white/5"
               :class="{ 'bg-sky-500/10': !notification.is_read }"
               style="border-color: var(--border-color);"
               @click="handleNotificationClick(notification)">
            <div class="flex items-start gap-3">
              <i :class="getNotificationIcon(notification)" class="text-lg mt-1"></i>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm">{{ notification.title }}</div>
                <div class="text-xs opacity-70 mt-1 line-clamp-2">{{ notification.message }}</div>
                <div class="text-xs opacity-50 mt-1">{{ formatTime(notification.created_at) }}</div>
              </div>
              <Button v-if="!notification.is_read" icon="pi pi-circle-fill" text rounded size="small"
                      class="!text-sky-500 !w-6 !h-6" @click.stop="markAsRead(notification.id)" />
            </div>
          </div>

          <div v-if="!notifications.length" class="p-8 text-center opacity-50">
            <i class="pi pi-bell-slash text-3xl mb-2"></i>
            <p>{{ t('notifications.noNotifications') }}</p>
          </div>
        </div>

        <div v-if="notifications.length" class="p-2 border-t text-center" style="border-color: var(--border-color);">
          <Button :label="t('notifications.deleteRead')" text size="small" class="!text-xs" @click="deleteRead" />
        </div>
      </div>
    </transition>

    <!-- Backdrop -->
    <div v-if="showPanel" class="fixed inset-0 z-40" @click="showPanel = false"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useNotificationsStore } from '../../stores/notifications';

const { t } = useI18n();
const router = useRouter();
const notificationsStore = useNotificationsStore();

const showPanel = ref(false);

const notifications = computed(() => notificationsStore.notifications);
const unreadCount = computed(() => notificationsStore.count.unread);

const togglePanel = async () => {
  showPanel.value = !showPanel.value;
  if (showPanel.value) {
    await notificationsStore.fetchNotifications();
  }
};

const formatTime = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diff = (now - date) / 1000;

  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return date.toLocaleDateString();
};

const getNotificationIcon = (notification) => {
  switch (notification.notification_type) {
    case 'ticket': return 'pi pi-ticket text-sky-500';
    case 'success': return 'pi pi-check-circle text-green-500';
    case 'warning': return 'pi pi-exclamation-triangle text-yellow-500';
    case 'error': return 'pi pi-times-circle text-red-500';
    default: return 'pi pi-info-circle text-blue-500';
  }
};

const handleNotificationClick = async (notification) => {
  await notificationsStore.markAsRead(notification.id);
  showPanel.value = false;

  const link = notificationsStore.getNotificationLink(notification);
  if (link) {
    router.push(link);
  }
};

const markAsRead = async (id) => {
  await notificationsStore.markAsRead(id);
};

const markAllRead = async () => {
  await notificationsStore.markAllAsRead();
};

const deleteRead = async () => {
  await notificationsStore.deleteAllRead();
};

onMounted(() => {
  notificationsStore.startPolling(30000);
});

onUnmounted(() => {
  notificationsStore.stopPolling();
});
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
