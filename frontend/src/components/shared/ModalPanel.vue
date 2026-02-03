<template>
  <Teleport to="body">
    <!-- Backdrop - v-show pour structure, CSS pour animation -->
    <div
      v-show="isOpen"
      ref="backdropRef"
      class="modal-backdrop"
      :class="{ 'modal-backdrop--visible': showContent }"
      @click="handleBackdropClick"
    ></div>

    <!-- Modal Container - v-show pour structure stable -->
    <div
      v-show="isOpen"
      class="modal-container"
      :class="{ 'modal-container--visible': showContent }"
      @click.self="handleBackdropClick"
    >
      <!-- Panel -->
      <div
        ref="panelRef"
        :class="[
          'modal-panel',
          sizeClass,
          { 'modal-panel--visible': showContent },
          { 'modal-panel--frozen': isFrozen }
        ]"
      >
        <!-- Header - toujours rendu pour structure stable -->
        <div class="modal-header">
          <div class="modal-header-content">
            <div v-if="icon" class="modal-icon">
              <i :class="['pi', icon]"></i>
            </div>
            <div class="modal-titles">
              <h2 class="modal-title">{{ title }}</h2>
              <p v-if="subtitle" class="modal-subtitle">{{ subtitle }}</p>
            </div>
          </div>
          <Button
            icon="pi pi-times"
            text
            rounded
            severity="secondary"
            :disabled="isTransitioning"
            @click="close"
            v-tooltip.left="'Close'"
          />
        </div>

        <!-- Content - v-if pour lazy render après animation -->
        <div class="modal-content">
          <template v-if="contentReady">
            <slot></slot>
          </template>
          <template v-else>
            <!-- Skeleton pendant le chargement -->
            <div class="modal-skeleton">
              <Skeleton height="1.5rem" width="60%" class="mb-3" />
              <Skeleton height="1rem" class="mb-2" />
              <Skeleton height="1rem" class="mb-2" />
              <Skeleton height="1rem" width="80%" class="mb-4" />
              <Skeleton height="3rem" class="mb-2" />
            </div>
          </template>
        </div>

        <!-- Footer -->
        <div v-if="$slots.footer" class="modal-footer">
          <template v-if="contentReady">
            <slot name="footer"></slot>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { useUIStore } from '../../stores/ui'

const props = defineProps({
  modelValue: Boolean,
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg', 'xl'].includes(v)
  },
  closeOnBackdrop: {
    type: Boolean,
    default: true
  },
  // Performance options
  lazyContent: {
    type: Boolean,
    default: true
  },
  transitionDuration: {
    type: Number,
    default: 250
  }
})

const emit = defineEmits(['update:modelValue', 'opened', 'closed', 'content-ready'])

const uiStore = useUIStore()

// Refs
const backdropRef = ref(null)
const panelRef = ref(null)

// State
const isOpen = ref(false)
const showContent = ref(false)
const contentReady = ref(false)
const isTransitioning = ref(false)
const isFrozen = ref(false)

// Computed
const sizeClass = computed(() => {
  const sizes = {
    sm: 'modal-panel--sm',
    md: 'modal-panel--md',
    lg: 'modal-panel--lg',
    xl: 'modal-panel--xl'
  }
  return sizes[props.size] || sizes.md
})

// Méthodes
const open = async () => {
  isOpen.value = true
  isTransitioning.value = true
  document.body.style.overflow = 'hidden'

  // Register with UI store - freeze parent overlays
  uiStore.registerOverlay('modal', close)

  // Force reflow pour déclencher l'animation
  await nextTick()
  requestAnimationFrame(() => {
    showContent.value = true

    // Attendre la fin de l'animation avant de charger le contenu lourd
    setTimeout(() => {
      isTransitioning.value = false
      if (props.lazyContent) {
        contentReady.value = true
        emit('content-ready')
      }
      emit('opened')
    }, props.transitionDuration)
  })

  // Si pas de lazy loading, charger immédiatement
  if (!props.lazyContent) {
    contentReady.value = true
  }
}

const close = () => {
  if (isTransitioning.value) return

  isTransitioning.value = true
  showContent.value = false

  // Unregister from UI store - unfreeze parent overlays
  uiStore.unregisterOverlay('modal')

  setTimeout(() => {
    isOpen.value = false
    contentReady.value = false
    isTransitioning.value = false
    document.body.style.overflow = ''
    emit('update:modelValue', false)
    emit('closed')
  }, props.transitionDuration)
}

const handleBackdropClick = () => {
  if (!isTransitioning.value && props.closeOnBackdrop) {
    close()
  }
}

// Freeze/Unfreeze pour menus imbriqués
const freeze = () => {
  isFrozen.value = true
}

const unfreeze = () => {
  isFrozen.value = false
}

// Watch modelValue
watch(() => props.modelValue, (newVal) => {
  if (newVal && !isOpen.value) {
    open()
  } else if (!newVal && isOpen.value && !isTransitioning.value) {
    close()
  }
}, { immediate: true })

// Expose methods for parent components
defineExpose({
  freeze,
  unfreeze,
  close
})

// Cleanup on unmount
onBeforeUnmount(() => {
  if (isOpen.value) {
    document.body.style.overflow = ''
    uiStore.unregisterOverlay('modal')
  }
})
</script>

<style scoped>
/* Backdrop - GPU accelerated */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 40;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  will-change: opacity;
}

.modal-backdrop--visible {
  opacity: 1;
  visibility: visible;
}

/* Container for centering */
.modal-container {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  pointer-events: none;
}

.modal-container--visible {
  pointer-events: auto;
}

/* Panel - GPU accelerated avec translate3d et scale */
.modal-panel {
  display: flex;
  flex-direction: column;
  background: var(--bg-card-solid);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  max-height: calc(100vh - 2rem);
  box-shadow: var(--shadow-xl);
  opacity: 0;
  transform: translate3d(0, 0, 0) scale(0.95);
  transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  will-change: opacity, transform;
  pointer-events: auto;
}

.modal-panel--visible {
  opacity: 1;
  transform: translate3d(0, 0, 0) scale(1);
}

/* Frozen state - disable interactions */
.modal-panel--frozen {
  pointer-events: none;
  filter: brightness(0.7);
}

.modal-panel--frozen::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
  border-radius: var(--radius-xl);
}

/* Sizes */
.modal-panel--sm { width: 100%; max-width: 24rem; }
.modal-panel--md { width: 100%; max-width: 32rem; }
.modal-panel--lg { width: 100%; max-width: 42rem; }
.modal-panel--xl { width: 100%; max-width: 56rem; }

/* Header */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-secondary);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  flex-shrink: 0;
}

.modal-header-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.modal-icon {
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-light);
  color: var(--primary);
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.modal-titles {
  min-width: 0;
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.modal-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Content */
.modal-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1.5rem;
  background: var(--bg-card-solid);
  overscroll-behavior: contain;
}

/* Skeleton */
.modal-skeleton {
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Footer */
.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-default);
  background: var(--bg-secondary);
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
  flex-shrink: 0;
}

/* Dark mode */
:root.dark .modal-header,
:root.dark .modal-footer {
  background: rgba(0, 0, 0, 0.2);
}

:root.dark .modal-icon {
  background: rgba(14, 165, 233, 0.15);
}
</style>
