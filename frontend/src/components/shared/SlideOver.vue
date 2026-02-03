<template>
  <Teleport to="body">
    <!-- Backdrop - v-show pour le conteneur, animation CSS -->
    <div
      v-show="isOpen"
      ref="backdropRef"
      class="slideover-backdrop"
      :class="{ 'slideover-backdrop--visible': showContent }"
      @click="handleBackdropClick"
    ></div>

    <!-- Panel - v-show pour la structure, v-if pour le contenu lourd -->
    <div
      v-show="isOpen"
      ref="panelRef"
      :class="[
        'slideover-panel',
        sizeClass,
        position === 'right' ? 'slideover-panel--right' : 'slideover-panel--left',
        { 'slideover-panel--visible': showContent },
        { 'slideover-panel--frozen': isFrozen }
      ]"
    >
      <!-- Header - toujours rendu pour structure stable -->
      <div class="slideover-header">
        <div class="slideover-header-content">
          <i v-if="icon" :class="['pi', icon, 'slideover-icon']"></i>
          <div class="slideover-titles">
            <h2 class="slideover-title">{{ title }}</h2>
            <p v-if="subtitle" class="slideover-subtitle">{{ subtitle }}</p>
          </div>
        </div>
        <Button
          icon="pi pi-times"
          text
          rounded
          :disabled="isTransitioning"
          @click="close"
          v-tooltip.left="'Close'"
        />
      </div>

      <!-- Content - v-if pour lazy render après animation -->
      <div class="slideover-content">
        <template v-if="contentReady">
          <slot></slot>
        </template>
        <template v-else>
          <!-- Skeleton pendant le chargement -->
          <div class="slideover-skeleton">
            <Skeleton height="2rem" class="mb-3" />
            <Skeleton height="1rem" class="mb-2" />
            <Skeleton height="1rem" class="mb-2" />
            <Skeleton height="1rem" width="70%" class="mb-4" />
            <Skeleton height="8rem" class="mb-3" />
            <Skeleton height="1rem" class="mb-2" />
            <Skeleton height="1rem" width="50%" />
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div v-if="$slots.footer" class="slideover-footer">
        <template v-if="contentReady">
          <slot name="footer"></slot>
        </template>
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
    validator: (v) => ['sm', 'md', 'lg', 'xl', 'full'].includes(v)
  },
  position: {
    type: String,
    default: 'right',
    validator: (v) => ['left', 'right'].includes(v)
  },
  // Performance options
  lazyContent: {
    type: Boolean,
    default: true
  },
  transitionDuration: {
    type: Number,
    default: 300
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
    sm: 'slideover-panel--sm',
    md: 'slideover-panel--md',
    lg: 'slideover-panel--lg',
    xl: 'slideover-panel--xl',
    full: 'slideover-panel--full'
  }
  return sizes[props.size] || sizes.md
})

// Méthodes
const open = async () => {
  isOpen.value = true
  isTransitioning.value = true
  document.body.style.overflow = 'hidden'

  // Register with UI store for nested menu management
  uiStore.registerOverlay('slideover', close)

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

  // Unregister from UI store
  uiStore.unregisterOverlay('slideover')

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
  if (!isTransitioning.value) {
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
    uiStore.unregisterOverlay('slideover')
  }
})
</script>

<style scoped>
/* Backdrop - GPU accelerated */
.slideover-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 40;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  will-change: opacity;
}

.slideover-backdrop--visible {
  opacity: 1;
  visibility: visible;
}

/* Panel - GPU accelerated avec translate3d */
.slideover-panel {
  position: fixed;
  top: 0;
  bottom: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-card-solid);
  box-shadow: var(--shadow-xl);
  will-change: transform;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slideover-panel--right {
  right: 0;
  transform: translate3d(100%, 0, 0);
}

.slideover-panel--left {
  left: 0;
  transform: translate3d(-100%, 0, 0);
}

.slideover-panel--visible {
  transform: translate3d(0, 0, 0);
}

/* Frozen state - disable interactions */
.slideover-panel--frozen {
  pointer-events: none;
  filter: brightness(0.7);
}

.slideover-panel--frozen::after {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 100;
}

/* Sizes */
.slideover-panel--sm { width: 20rem; }
.slideover-panel--md { width: 24rem; }
.slideover-panel--lg { width: 32rem; }
.slideover-panel--xl { width: 40rem; }
.slideover-panel--full { width: 100%; max-width: 48rem; }

/* Header */
.slideover-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-default);
  flex-shrink: 0;
}

.slideover-header-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.slideover-icon {
  font-size: 1.25rem;
  color: var(--primary);
}

.slideover-titles {
  min-width: 0;
}

.slideover-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.slideover-subtitle {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Content */
.slideover-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1.5rem;
  overscroll-behavior: contain;
}

/* Skeleton */
.slideover-skeleton {
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Footer */
.slideover-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border-default);
  flex-shrink: 0;
}

/* Responsive */
@media (max-width: 640px) {
  .slideover-panel--sm,
  .slideover-panel--md,
  .slideover-panel--lg,
  .slideover-panel--xl {
    width: 100%;
  }
}
</style>
