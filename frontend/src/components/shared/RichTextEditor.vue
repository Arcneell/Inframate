<template>
  <div class="rich-text-editor" :class="{ 'editor-focused': isFocused, 'editor-disabled': disabled }">
    <!-- Toolbar -->
    <div v-if="editor && !readonly" class="editor-toolbar">
      <div class="toolbar-group">
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('bold') }"
          @click="editor.chain().focus().toggleBold().run()"
          :disabled="disabled"
          :title="t('editor.bold')"
        >
          <span class="toolbar-text-icon bold">B</span>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('italic') }"
          @click="editor.chain().focus().toggleItalic().run()"
          :disabled="disabled"
          :title="t('editor.italic')"
        >
          <span class="toolbar-text-icon italic">I</span>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('strike') }"
          @click="editor.chain().focus().toggleStrike().run()"
          :disabled="disabled"
          :title="t('editor.strikethrough')"
        >
          <i class="pi pi-minus"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('code') }"
          @click="editor.chain().focus().toggleCode().run()"
          :disabled="disabled"
          :title="t('editor.code')"
        >
          <i class="pi pi-code"></i>
        </button>
      </div>

      <div class="toolbar-separator"></div>

      <div class="toolbar-group">
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('bulletList') }"
          @click="editor.chain().focus().toggleBulletList().run()"
          :disabled="disabled"
          :title="t('editor.bulletList')"
        >
          <i class="pi pi-list"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('orderedList') }"
          @click="editor.chain().focus().toggleOrderedList().run()"
          :disabled="disabled"
          :title="t('editor.orderedList')"
        >
          <i class="pi pi-sort-numeric-up"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('blockquote') }"
          @click="editor.chain().focus().toggleBlockquote().run()"
          :disabled="disabled"
          :title="t('editor.quote')"
        >
          <i class="pi pi-comment"></i>
        </button>
      </div>

      <div class="toolbar-separator"></div>

      <div class="toolbar-group">
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('heading', { level: 2 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
          :disabled="disabled"
          :title="t('editor.heading')"
        >
          H2
        </button>
        <button
          type="button"
          class="toolbar-btn"
          :class="{ active: editor.isActive('heading', { level: 3 }) }"
          @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
          :disabled="disabled"
          :title="t('editor.subheading')"
        >
          H3
        </button>
      </div>

      <div class="toolbar-separator"></div>

      <div class="toolbar-group">
        <button
          type="button"
          class="toolbar-btn"
          @click="setLink"
          :class="{ active: editor.isActive('link') }"
          :disabled="disabled"
          :title="t('editor.link')"
        >
          <i class="pi pi-link"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          @click="triggerImageUpload"
          :disabled="disabled"
          :title="t('editor.insertImage')"
        >
          <i class="pi pi-image"></i>
        </button>
      </div>

      <div class="toolbar-spacer"></div>

      <div class="toolbar-group">
        <button
          type="button"
          class="toolbar-btn"
          @click="editor.chain().focus().undo().run()"
          :disabled="disabled || !editor.can().undo()"
          :title="t('editor.undo')"
        >
          <i class="pi pi-undo"></i>
        </button>
        <button
          type="button"
          class="toolbar-btn"
          @click="editor.chain().focus().redo().run()"
          :disabled="disabled || !editor.can().redo()"
          :title="t('editor.redo')"
        >
          <i class="pi pi-refresh"></i>
        </button>
      </div>
    </div>

    <!-- Editor Content -->
    <EditorContent
      :editor="editor"
      class="editor-content"
      :class="{ 'editor-readonly': readonly }"
    />

    <!-- Hidden file input for image upload -->
    <input
      ref="imageInput"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleImageUpload"
    />

    <!-- Character count -->
    <div v-if="showCharCount && editor" class="editor-footer">
      <span class="char-count" :class="{ 'over-limit': maxLength && characterCount > maxLength }">
        {{ characterCount }}
        <span v-if="maxLength"> / {{ maxLength }}</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import CharacterCount from '@tiptap/extension-character-count'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  readonly: {
    type: Boolean,
    default: false
  },
  maxLength: {
    type: Number,
    default: null
  },
  showCharCount: {
    type: Boolean,
    default: false
  },
  minHeight: {
    type: String,
    default: '150px'
  }
})

const emit = defineEmits(['update:modelValue', 'blur', 'focus', 'image-upload'])

const { t } = useI18n()

// Refs
const imageInput = ref(null)
const isFocused = ref(false)

// Editor instance
const editor = useEditor({
  content: props.modelValue,
  editable: !props.disabled && !props.readonly,
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [2, 3]
      }
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: {
        class: 'editor-link'
      }
    }),
    Image.configure({
      inline: true,
      allowBase64: true,
      HTMLAttributes: {
        class: 'editor-image'
      }
    }),
    Placeholder.configure({
      placeholder: props.placeholder || t('editor.placeholder')
    }),
    CharacterCount.configure({
      limit: props.maxLength
    })
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
  onFocus: () => {
    isFocused.value = true
    emit('focus')
  },
  onBlur: () => {
    isFocused.value = false
    emit('blur')
  }
})

// Character count
const characterCount = computed(() => {
  return editor.value?.storage.characterCount.characters() || 0
})

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  if (editor.value && newValue !== editor.value.getHTML()) {
    editor.value.commands.setContent(newValue, false)
  }
})

// Watch for disabled changes
watch(() => props.disabled, (newValue) => {
  editor.value?.setEditable(!newValue && !props.readonly)
})

// Methods
const setLink = () => {
  const previousUrl = editor.value.getAttributes('link').href
  const url = window.prompt('URL', previousUrl)

  if (url === null) return

  if (url === '') {
    editor.value.chain().focus().extendMarkRange('link').unsetLink().run()
    return
  }

  editor.value.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}

const triggerImageUpload = () => {
  imageInput.value?.click()
}

const handleImageUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return

  // Convert to base64 and insert directly
  const reader = new FileReader()
  reader.onload = (e) => {
    editor.value.chain().focus().setImage({ src: e.target.result }).run()
  }
  reader.readAsDataURL(file)

  // Also emit event for parent if they want to handle it differently (e.g., upload to server)
  emit('image-upload', file)

  // Reset input
  event.target.value = ''
}

// Cleanup
onBeforeUnmount(() => {
  editor.value?.destroy()
})

// Expose methods for parent component
defineExpose({
  getHTML: () => editor.value?.getHTML(),
  getText: () => editor.value?.getText(),
  focus: () => editor.value?.commands.focus(),
  clear: () => editor.value?.commands.clearContent()
})
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid var(--border-default);
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-primary);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.rich-text-editor.editor-focused {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb), 0.1);
}

.rich-text-editor.editor-disabled {
  opacity: 0.6;
  pointer-events: none;
  background: var(--bg-secondary);
}

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-secondary);
  flex-wrap: wrap;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 2px;
}

.toolbar-separator {
  width: 1px;
  height: 24px;
  background: var(--border-default);
  margin: 0 8px;
}

.toolbar-spacer {
  flex: 1;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.15s ease;
}

.toolbar-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.toolbar-btn.active {
  background: var(--primary-light);
  color: var(--primary);
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.toolbar-btn i {
  font-size: 14px;
}

.toolbar-text-icon {
  font-size: 14px;
  font-weight: 700;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.toolbar-text-icon.bold {
  font-weight: 900;
}

.toolbar-text-icon.italic {
  font-style: italic;
}

/* Editor Content */
.editor-content {
  min-height: v-bind(minHeight);
  padding: 12px 16px;
}

.editor-content :deep(.ProseMirror) {
  min-height: v-bind(minHeight);
  outline: none;
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
}

.editor-content :deep(.ProseMirror p) {
  margin: 0 0 0.75em 0;
}

.editor-content :deep(.ProseMirror p:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(.ProseMirror h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 1em 0 0.5em 0;
  color: var(--text-primary);
}

.editor-content :deep(.ProseMirror h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 1em 0 0.5em 0;
  color: var(--text-primary);
}

.editor-content :deep(.ProseMirror ul),
.editor-content :deep(.ProseMirror ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.editor-content :deep(.ProseMirror li) {
  margin: 0.25em 0;
}

.editor-content :deep(.ProseMirror blockquote) {
  border-left: 3px solid var(--primary);
  margin: 0.5em 0;
  padding-left: 1em;
  color: var(--text-secondary);
  font-style: italic;
}

.editor-content :deep(.ProseMirror code) {
  background: var(--bg-secondary);
  border-radius: 4px;
  padding: 0.2em 0.4em;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
  color: var(--danger);
}

.editor-content :deep(.ProseMirror pre) {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 12px 16px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.editor-content :deep(.ProseMirror pre code) {
  background: none;
  padding: 0;
  color: var(--text-primary);
}

.editor-content :deep(.editor-link) {
  color: var(--primary);
  text-decoration: underline;
  cursor: pointer;
}

.editor-content :deep(.editor-image) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  margin: 0.5em 0;
}

.editor-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--text-muted);
  pointer-events: none;
  height: 0;
}

.editor-readonly {
  background: var(--bg-secondary);
}

/* Footer */
.editor-footer {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px;
  border-top: 1px solid var(--border-default);
  background: var(--bg-secondary);
}

.char-count {
  font-size: 12px;
  color: var(--text-muted);
}

.char-count.over-limit {
  color: var(--danger);
  font-weight: 600;
}
</style>
