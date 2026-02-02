<template>
  <div
    class="file-drop-zone"
    :class="{
      'drag-over': isDragOver,
      'has-files': files.length > 0,
      'disabled': disabled
    }"
    @dragenter.prevent="handleDragEnter"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
    @click="triggerFileInput"
  >
    <input
      ref="fileInput"
      type="file"
      :multiple="multiple"
      :accept="accept"
      style="display: none"
      @change="handleFileSelect"
    />

    <!-- Drop zone content when empty -->
    <div v-if="files.length === 0" class="drop-zone-content">
      <div class="drop-icon" :class="{ 'animate-bounce': isDragOver }">
        <i class="pi pi-cloud-upload"></i>
      </div>
      <div class="drop-text">
        <span class="drop-primary">{{ t('files.dropzone') }}</span>
        <span class="drop-secondary">{{ t('files.dropzoneOr') }} {{ t('files.browse').toLowerCase() }}</span>
      </div>
      <div v-if="maxSize" class="drop-hint">
        {{ t('files.maxSize', { size: formatFileSize(maxSize) }) }}
      </div>
    </div>

    <!-- File list when files are selected -->
    <div v-else class="files-list">
      <div v-for="(file, index) in files" :key="index" class="file-item">
        <div class="file-icon">
          <i :class="getFileIcon(file)"></i>
        </div>
        <div class="file-info">
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">{{ formatFileSize(file.size) }}</span>
        </div>
        <button
          type="button"
          class="file-remove"
          @click.stop="removeFile(index)"
          :title="t('common.remove')"
        >
          <i class="pi pi-times"></i>
        </button>
      </div>

      <!-- Add more files button -->
      <div v-if="multiple" class="add-more" @click.stop="triggerFileInput">
        <i class="pi pi-plus"></i>
        <span>{{ t('files.addMore') }}</span>
      </div>
    </div>

    <!-- Upload progress -->
    <div v-if="uploading" class="upload-overlay">
      <div class="upload-progress">
        <i class="pi pi-spin pi-spinner"></i>
        <span>{{ t('files.uploading') }}...</span>
        <div v-if="uploadProgress > 0" class="progress-bar">
          <div class="progress-fill" :style="{ width: `${uploadProgress}%` }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  multiple: {
    type: Boolean,
    default: true
  },
  accept: {
    type: String,
    default: '*/*'
  },
  maxSize: {
    type: Number,
    default: null // in bytes
  },
  maxFiles: {
    type: Number,
    default: 10
  },
  disabled: {
    type: Boolean,
    default: false
  },
  uploading: {
    type: Boolean,
    default: false
  },
  uploadProgress: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update:modelValue', 'files-added', 'file-removed', 'error'])

const { t } = useI18n()

// Refs
const fileInput = ref(null)
const isDragOver = ref(false)
let dragCounter = 0

// Computed
const files = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Methods
const triggerFileInput = () => {
  if (!props.disabled) {
    fileInput.value?.click()
  }
}

const handleDragEnter = (e) => {
  if (props.disabled) return
  dragCounter++
  isDragOver.value = true
}

const handleDragOver = (e) => {
  if (props.disabled) return
  e.dataTransfer.dropEffect = 'copy'
}

const handleDragLeave = (e) => {
  if (props.disabled) return
  dragCounter--
  if (dragCounter === 0) {
    isDragOver.value = false
  }
}

const handleDrop = (e) => {
  if (props.disabled) return
  isDragOver.value = false
  dragCounter = 0

  const droppedFiles = Array.from(e.dataTransfer.files)
  addFiles(droppedFiles)
}

const handleFileSelect = (e) => {
  const selectedFiles = Array.from(e.target.files)
  addFiles(selectedFiles)
  // Reset input
  e.target.value = ''
}

const addFiles = (newFiles) => {
  const validFiles = []
  const errors = []

  for (const file of newFiles) {
    // Check max files
    if (files.value.length + validFiles.length >= props.maxFiles) {
      errors.push(t('files.tooManyFiles', { count: props.maxFiles }))
      break
    }

    // Check file size
    if (props.maxSize && file.size > props.maxSize) {
      errors.push(t('files.fileTooLarge', { size: formatFileSize(props.maxSize) }))
      continue
    }

    // Check accept types
    if (props.accept !== '*/*') {
      const acceptTypes = props.accept.split(',').map(t => t.trim())
      const isValid = acceptTypes.some(type => {
        if (type.startsWith('.')) {
          return file.name.toLowerCase().endsWith(type.toLowerCase())
        }
        if (type.endsWith('/*')) {
          return file.type.startsWith(type.replace('/*', '/'))
        }
        return file.type === type
      })
      if (!isValid) {
        errors.push(t('files.invalidType', { name: file.name }))
        continue
      }
    }

    validFiles.push(file)
  }

  if (errors.length > 0) {
    emit('error', errors)
  }

  if (validFiles.length > 0) {
    if (props.multiple) {
      files.value = [...files.value, ...validFiles]
    } else {
      files.value = [validFiles[0]]
    }
    emit('files-added', validFiles)
  }
}

const removeFile = (index) => {
  const removed = files.value[index]
  files.value = files.value.filter((_, i) => i !== index)
  emit('file-removed', removed)
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

const getFileIcon = (file) => {
  const type = file.type || ''
  const name = file.name || ''

  if (type.startsWith('image/')) return 'pi pi-image'
  if (type.startsWith('video/')) return 'pi pi-video'
  if (type.startsWith('audio/')) return 'pi pi-volume-up'
  if (type === 'application/pdf') return 'pi pi-file-pdf'
  if (type.includes('word') || name.endsWith('.doc') || name.endsWith('.docx')) return 'pi pi-file-word'
  if (type.includes('excel') || name.endsWith('.xls') || name.endsWith('.xlsx')) return 'pi pi-file-excel'
  if (type.includes('zip') || type.includes('rar') || type.includes('7z')) return 'pi pi-box'
  return 'pi pi-file'
}

// Expose methods
defineExpose({
  clear: () => { files.value = [] },
  addFiles
})
</script>

<style scoped>
.file-drop-zone {
  position: relative;
  border: 2px dashed var(--border-default);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-secondary);
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.file-drop-zone:hover:not(.disabled) {
  border-color: var(--primary);
  background: var(--bg-hover);
}

.file-drop-zone.drag-over {
  border-color: var(--primary);
  background: rgba(var(--primary-rgb), 0.1);
  transform: scale(1.01);
}

.file-drop-zone.has-files {
  padding: 16px;
}

.file-drop-zone.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Drop zone content */
.drop-zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.drop-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}

.drop-icon i {
  font-size: 24px;
  color: var(--primary);
}

.drop-icon.animate-bounce {
  animation: bounce 0.5s ease infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.drop-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.drop-primary {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}

.drop-secondary {
  font-size: 13px;
  color: var(--text-muted);
}

.drop-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Files list */
.files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  transition: all 0.15s ease;
}

.file-item:hover {
  border-color: var(--primary);
}

.file-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-icon i {
  font-size: 16px;
  color: var(--primary);
}

.file-info {
  flex: 1;
  min-width: 0;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: var(--text-muted);
}

.file-remove {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.file-remove:hover {
  background: var(--danger-light);
  color: var(--danger);
}

.add-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  border: 1px dashed var(--border-default);
  border-radius: 8px;
  color: var(--text-muted);
  font-size: 13px;
  transition: all 0.15s ease;
}

.add-more:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: var(--primary-light);
}

/* Upload overlay */
.upload-overlay {
  position: absolute;
  inset: 0;
  background: rgba(var(--bg-primary-rgb), 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.upload-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-primary);
}

.upload-progress i {
  font-size: 24px;
  color: var(--primary);
}

.progress-bar {
  width: 150px;
  height: 4px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 2px;
  transition: width 0.2s ease;
}
</style>
