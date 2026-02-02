<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="fade">
      <div
        v-if="modelValue"
        class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
        @click="closeOnBackdrop && $emit('update:modelValue', false)"
      ></div>
    </Transition>

    <!-- Panel -->
    <Transition name="scale">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div
          :class="['modal-panel flex flex-col shadow-2xl', sizeClass]"
          @click.stop
        >
          <!-- Header -->
          <div class="modal-header flex items-center justify-between px-6 py-4">
            <div class="flex items-center gap-3 min-w-0">
              <div v-if="icon" class="modal-icon">
                <i :class="['pi', icon, 'text-lg']"></i>
              </div>
              <div class="min-w-0">
                <h2 class="text-lg font-semibold truncate">{{ title }}</h2>
                <p v-if="subtitle" class="text-sm opacity-60 truncate">{{ subtitle }}</p>
              </div>
            </div>
            <Button
              icon="pi pi-times"
              text
              rounded
              severity="secondary"
              @click="$emit('update:modelValue', false)"
              v-tooltip.left="'Close'"
            />
          </div>

          <!-- Content -->
          <div class="modal-content flex-1 overflow-auto px-6 py-4">
            <slot></slot>
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="modal-footer px-6 py-4">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, watch } from 'vue'

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
  }
})

defineEmits(['update:modelValue'])

const sizeClass = computed(() => {
  const sizes = {
    sm: 'w-full max-w-md',
    md: 'w-full max-w-lg',
    lg: 'w-full max-w-2xl',
    xl: 'w-full max-w-4xl'
  }
  return sizes[props.size] || sizes.md
})

// Lock body scroll when open
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})
</script>

<style scoped>
.modal-panel {
  background: var(--bg-card-solid);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  max-height: calc(100vh - 2rem);
  box-shadow: var(--shadow-xl), 0 0 40px rgba(0, 0, 0, 0.1);
}

.modal-header {
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-secondary);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
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
}

.modal-content {
  background: var(--bg-card-solid);
}

.modal-footer {
  border-top: 1px solid var(--border-default);
  background: var(--bg-secondary);
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scale-enter-active,
.scale-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Dark mode adjustments */
:root.dark .modal-panel {
  background: var(--bg-card-solid);
  border-color: var(--border-default);
}

:root.dark .modal-header,
:root.dark .modal-footer {
  background: rgba(0, 0, 0, 0.2);
}

:root.dark .modal-icon {
  background: rgba(14, 165, 233, 0.15);
}
</style>
