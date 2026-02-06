<template>
  <div class="knowledge-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-title-section">
          <h1 class="page-title">
            <i class="pi pi-book"></i>
            {{ t('knowledge.title') }}
          </h1>
          <p class="page-subtitle">{{ stats.total }} {{ t('knowledge.articles') }}</p>
        </div>
        <Button v-if="canManageKnowledge" :label="t('knowledge.newArticle')" icon="pi pi-plus" @click="openArticleDialog()" class="create-btn" />
      </div>

      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="stat-chip" :class="{ active: filterStatus === 'all' }" @click="setFilterStatus('all')">
          <span class="stat-chip-label">{{ t('common.all') }}</span>
          <span class="stat-chip-count">{{ stats.total }}</span>
        </div>
        <div class="stat-chip stat-chip--published" :class="{ active: filterStatus === 'published' }" @click="setFilterStatus('published')">
          <span class="stat-chip-label">{{ t('knowledge.published') }}</span>
          <span class="stat-chip-count">{{ stats.published }}</span>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div class="toolbar">
      <div class="toolbar-search">
        <i class="pi pi-search"></i>
        <InputText v-model="searchQuery" :placeholder="t('knowledge.searchArticles')" @input="debouncedSearch" />
      </div>

      <span class="toolbar-separator"></span>

      <div class="toolbar-filter">
        <span class="filter-label">{{ t('knowledge.category') }}</span>
        <Dropdown
          v-model="selectedCategoryId"
          :options="categoryOptions"
          optionLabel="name"
          optionValue="id"
          :placeholder="t('filters.allCategories')"
          showClear
          @change="onCategoryChange"
        />
      </div>

      <span class="toolbar-separator"></span>

      <label v-if="canManageKnowledge" class="my-tickets-toggle">
        <Checkbox v-model="showDrafts" :binary="true" inputId="showDrafts" @change="loadArticles" />
        <span>{{ t('knowledge.draft') }}</span>
      </label>

      <div class="toolbar-spacer"></div>

      <Button v-if="canManageKnowledge" icon="pi pi-cog" :label="t('knowledge.manageCategories')" text size="small" @click="showCategoryDialog = true" />
    </div>

    <!-- Articles List -->
    <div class="tickets-container">
      <div v-if="loadingArticles" class="loading-state">
        <i class="pi pi-spin pi-spinner"></i>
        <span>{{ t('common.loading') }}</span>
      </div>

      <div v-else-if="articles.length === 0" class="empty-state">
        <i class="pi pi-book"></i>
        <h3>{{ t('knowledge.articles') }}</h3>
        <p>{{ t('common.noData') }}</p>
        <Button v-if="canManageKnowledge" :label="t('knowledge.newArticle')" icon="pi pi-plus" @click="openArticleDialog()" />
      </div>

      <div v-else class="tickets-list">
        <!-- Table Header -->
        <div class="tickets-header knowledge-header">
          <span class="header-col header-col--sortable" @click="toggleSort('title')">
            {{ t('knowledge.articleTitle') }}
            <i v-if="sortField === 'title'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
          </span>
          <span class="header-col">{{ t('knowledge.category') }}</span>
          <span class="header-col">{{ t('knowledge.published') }}</span>
          <span class="header-col header-col--sortable" @click="toggleSort('view_count')">
            {{ t('common.views') }}
            <i v-if="sortField === 'view_count'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
          </span>
          <span class="header-col header-col--sortable" @click="toggleSort('created_at')">
            {{ t('common.updatedAt') }}
            <i v-if="sortField === 'created_at'" :class="['pi', sortOrder === -1 ? 'pi-sort-amount-down' : 'pi-sort-amount-up']"></i>
          </span>
          <span class="header-col--arrow"></span>
        </div>

        <!-- Article Rows -->
        <div
          v-for="article in articles"
          :key="article.id"
          class="ticket-row knowledge-row"
          @click="openArticleDetail(article)"
        >
          <div class="ticket-info knowledge-title-cell">
            <span class="ticket-title">{{ article.title }}</span>
            <span v-if="article.summary" class="ticket-type-label line-clamp-1">{{ article.summary }}</span>
          </div>
          <div class="knowledge-category-cell">
            <span v-if="article.category_name || article.category" class="category-badge">{{ article.category_name || article.category }}</span>
            <span v-else class="text-muted">—</span>
          </div>
          <div class="ticket-tags">
            <Tag v-if="!article.is_published" :value="t('knowledge.draft')" severity="warning" />
            <Tag v-if="article.is_internal" :value="t('knowledge.internal')" severity="secondary" />
            <span v-if="article.is_published && !article.is_internal" class="status-published">{{ t('knowledge.published') }}</span>
          </div>
          <span class="ticket-date knowledge-views">{{ article.view_count ?? 0 }}</span>
          <span class="ticket-date">{{ formatDate(article.updated_at || article.created_at) }}</span>
          <i class="pi pi-chevron-right ticket-arrow"></i>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="articlesTotal > 0" class="pagination">
        <Paginator
          :rows="articlesLimit"
          :totalRecords="articlesTotal"
          :first="articlesFirst"
          :rowsPerPageOptions="[10, 15, 25, 50]"
          @page="onPage"
          template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
        />
      </div>
    </div>

    <!-- Article Detail Modal -->
    <ModalPanel
      v-model="showDetailDialog"
      :title="currentArticle?.title"
      :subtitle="currentArticle?.slug"
      icon="pi-book"
      size="xl"
      @content-ready="onDetailModalReady"
    >
      <div v-if="currentArticle && detailContentReady" class="detail-content">
        <div class="detail-tags">
          <Tag v-if="currentArticle.category_name || currentArticle.category" :value="currentArticle.category_name || currentArticle.category" />
          <Tag v-for="tag in (currentArticle.tags || [])" :key="tag" :value="tag" severity="secondary" />
          <Tag v-if="!currentArticle.is_published" :value="t('knowledge.draft')" severity="warning" />
          <Tag v-if="currentArticle.is_internal" :value="t('knowledge.internal')" severity="secondary" />
        </div>

        <div class="detail-info-grid">
          <div class="info-item">
            <span class="info-label">{{ t('knowledge.author') }}</span>
            <span class="info-value">{{ currentArticle.author_name || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('common.createdAt') }}</span>
            <span class="info-value">{{ formatDateTime(currentArticle.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('common.views') }}</span>
            <span class="info-value">{{ currentArticle.view_count ?? 0 }}</span>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-align-left"></i>
            {{ t('knowledge.content') }}
          </h4>
          <div class="description-box knowledge-content" v-html="sanitizeHtml(currentArticle.content)"></div>
        </div>

        <!-- Feedback -->
        <div class="detail-section">
          <h4 class="section-title">
            <i class="pi pi-thumbs-up"></i>
            {{ t('knowledge.wasHelpful') }}
          </h4>
          <div v-if="!feedbackSubmitted" class="feedback-actions">
            <Button :label="t('knowledge.yes')" icon="pi pi-thumbs-up" size="small" outlined @click="submitFeedback(true)" />
            <Button :label="t('knowledge.no')" icon="pi pi-thumbs-down" size="small" outlined severity="secondary" @click="submitFeedback(false)" />
          </div>
          <div v-else class="feedback-thanks">
            <i class="pi pi-check"></i>
            {{ t('knowledge.feedbackThanks') }}
          </div>
        </div>
      </div>

      <div v-else class="detail-skeleton">
        <div class="flex gap-2 mb-4">
          <Skeleton width="5rem" height="1.5rem" borderRadius="9999px" />
          <Skeleton width="4rem" height="1.5rem" borderRadius="9999px" />
        </div>
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div><Skeleton height="1rem" class="mb-2" /><Skeleton width="60%" /></div>
          <div><Skeleton height="1rem" class="mb-2" /><Skeleton width="70%" /></div>
        </div>
        <Skeleton height="1.5rem" width="8rem" class="mb-3" />
        <Skeleton height="6rem" class="mb-6" />
      </div>

      <template #footer>
        <div class="detail-actions">
          <div v-if="canManageKnowledge && currentArticle && detailContentReady" class="action-buttons">
            <Button :label="t('knowledge.editArticle')" icon="pi pi-pencil" size="small" @click="openArticleDialog(currentArticle); showDetailDialog = false" />
            <Button v-if="!currentArticle.is_published" :label="t('knowledge.publish')" icon="pi pi-check" size="small" severity="success" @click="publishArticle(currentArticle.id)" />
            <Button v-else :label="t('knowledge.unpublish')" icon="pi pi-eye-slash" size="small" severity="warning" @click="unpublishArticle(currentArticle.id)" />
            <Button icon="pi pi-trash" size="small" severity="danger" @click="confirmDeleteArticle(currentArticle); showDetailDialog = false" />
          </div>
          <div v-else></div>
          <Button :label="t('common.close')" severity="secondary" outlined @click="showDetailDialog = false" />
        </div>
      </template>
    </ModalPanel>

    <!-- Create/Edit Article Modal -->
    <ModalPanel
      v-model="showArticleDialog"
      :title="editingArticle ? t('knowledge.editArticle') : t('knowledge.newArticle')"
      icon="pi-book"
      size="xl"
    >
      <div class="detail-content">
        <div class="detail-section">
          <h4 class="section-title">{{ t('knowledge.articleTitle') }} <span class="required">*</span></h4>
          <InputText v-model="articleForm.title" :placeholder="t('knowledge.articleTitle')" class="form-input-full" />
        </div>
        <div class="detail-section">
          <h4 class="section-title">{{ t('knowledge.summary') }}</h4>
          <InputText v-model="articleForm.summary" :placeholder="t('knowledge.summaryPlaceholder')" class="form-input-full" />
        </div>
        <div class="detail-info-grid detail-info-grid--form">
          <div class="info-item">
            <span class="info-label">{{ t('knowledge.category') }}</span>
            <Dropdown v-model="articleForm.category_id" :options="categoryOptions" optionLabel="name" optionValue="id" showClear :placeholder="t('knowledge.selectCategory')" class="info-dropdown" />
          </div>
          <div class="info-item">
            <span class="info-label">{{ t('knowledge.tags') }}</span>
            <div class="tags-field">
              <span v-for="(tag, idx) in articleForm.tags" :key="idx" class="tag-pill">
                {{ tag }}
                <button type="button" class="tag-pill-remove" :aria-label="t('common.remove')" @click="removeTag(idx)">
                  <i class="pi pi-times"></i>
                </button>
              </span>
              <input
                v-model="tagInputValue"
                type="text"
                class="tags-input"
                :placeholder="articleForm.tags.length ? '' : t('knowledge.tagsPlaceholder')"
                @keydown.enter.prevent="addTag"
              />
            </div>
          </div>
        </div>
        <div class="detail-section">
          <h4 class="section-title">{{ t('knowledge.content') }} <span class="required">*</span></h4>
          <RichTextEditor
            v-model="articleForm.content"
            :placeholder="t('knowledge.contentPlaceholder')"
            :max-length="50000"
            min-height="200px"
            @image-upload="handleContentImageUpload"
          />
        </div>
        <div class="detail-section flex gap-6">
          <label class="flex items-center gap-2 cursor-pointer">
            <Checkbox v-model="articleForm.is_published" :binary="true" inputId="published" />
            <span>{{ t('knowledge.published') }}</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <Checkbox v-model="articleForm.is_internal" :binary="true" inputId="internal" />
            <span>{{ t('knowledge.internal') }}</span>
          </label>
        </div>
      </div>
      <template #footer>
        <div class="modal-footer-actions">
          <Button :label="t('common.cancel')" severity="secondary" text @click="showArticleDialog = false" />
          <Button :label="t('common.save')" icon="pi pi-check" @click="saveArticle" :loading="saving" />
        </div>
      </template>
    </ModalPanel>

    <!-- Manage Categories Modal -->
    <ModalPanel v-model="showCategoryDialog" :title="t('knowledge.manageCategories')" icon="pi pi-folder" size="lg">
      <div class="detail-content">
        <div class="detail-section category-form-section">
          <h4 class="section-title">{{ editingCategory ? t('knowledge.editCategory') : t('knowledge.addCategory') }}</h4>
          <div class="detail-info-grid detail-info-grid--form">
            <div class="info-item">
              <span class="info-label">{{ t('common.name') }} <span class="required">*</span></span>
              <InputText v-model="categoryForm.name" :placeholder="t('knowledge.categoryName')" class="form-input-full" />
            </div>
            <div class="info-item">
              <span class="info-label">{{ t('common.icon') }}</span>
              <Dropdown v-model="categoryForm.icon" :options="iconOptions" optionLabel="label" optionValue="value" class="info-dropdown" :placeholder="t('knowledge.selectIcon')">
                <template #value="slotProps">
                  <div v-if="slotProps.value" class="flex items-center gap-2">
                    <i :class="slotProps.value"></i>
                    <span>{{ getIconLabel(slotProps.value) }}</span>
                  </div>
                  <span v-else>{{ slotProps.placeholder }}</span>
                </template>
                <template #option="slotProps">
                  <div class="flex items-center gap-2">
                    <i :class="slotProps.option.value"></i>
                    <span>{{ slotProps.option.label }}</span>
                  </div>
                </template>
              </Dropdown>
            </div>
          </div>
          <div class="detail-section">
            <span class="info-label block mb-2">{{ t('common.color') }}</span>
            <div class="flex items-center gap-3 flex-wrap">
              <div v-for="color in colorPresets" :key="color"
                   class="w-7 h-7 rounded cursor-pointer transition-transform hover:scale-110 border-2"
                   :class="categoryForm.color === color ? 'border-primary ring-2 ring-offset-2' : 'border-transparent'"
                   :style="{ backgroundColor: color }"
                   @click="categoryForm.color = color" />
              <InputText v-model="categoryForm.color" class="w-24 text-sm" placeholder="#0ea5e9" />
            </div>
          </div>
          <div class="flex justify-end gap-2 mt-4">
            <Button v-if="editingCategory" :label="t('common.cancel')" size="small" severity="secondary" outlined @click="resetCategoryForm" />
            <Button :label="editingCategory ? t('common.update') : t('common.add')" size="small" icon="pi pi-check" @click="saveCategory" :loading="savingCategory" />
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">{{ t('knowledge.existingCategories') }}</h4>
          <div v-if="categories.length === 0" class="text-center py-6 text-muted">
            {{ t('knowledge.noCategoriesYet') }}
          </div>
          <div v-else class="space-y-2">
            <div v-for="cat in categories" :key="cat.id" class="category-list-item">
              <i :class="cat.icon || 'pi pi-folder'" :style="{ color: cat.color }"></i>
              <span class="flex-1 font-medium">{{ cat.name }}</span>
              <span class="text-sm text-muted">{{ cat.article_count }} {{ t('knowledge.articles') }}</span>
              <Button icon="pi pi-pencil" text rounded size="small" @click="editCategory(cat)" />
              <Button icon="pi pi-trash" text rounded size="small" severity="danger" :disabled="cat.article_count > 0" v-tooltip="cat.article_count > 0 ? t('knowledge.cannotDeleteWithArticles') : ''" @click="confirmDeleteCategory(cat)" />
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <Button :label="t('common.close')" severity="secondary" @click="showCategoryDialog = false" />
      </template>
    </ModalPanel>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, markRaw, defineAsyncComponent } from 'vue';
import { useToast } from 'primevue/usetoast';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../stores/auth';
import { useUIStore } from '../stores/ui';
import api from '../api';
import ModalPanel from '../components/shared/ModalPanel.vue';

const RichTextEditor = defineAsyncComponent(() =>
  import('../components/shared/RichTextEditor.vue')
);

const { t } = useI18n();
const toast = useToast();
const authStore = useAuthStore();
const uiStore = useUIStore();

const currentUser = computed(() => authStore.user);
const canManageKnowledge = computed(() => {
  if (!currentUser.value) return false;
  if (['admin', 'superadmin'].includes(currentUser.value.role)) return true;
  if (currentUser.value.role === 'tech') return authStore.hasPermission('knowledge');
  return false;
});

// State
const articles = ref([]);
const categories = ref([]);
const loadingArticles = ref(false);
const saving = ref(false);
const filterStatus = ref('all'); // 'all' | 'published'
const stats = ref({ total: 0, published: 0 });
const searchQuery = ref('');
const selectedCategoryId = ref(null);
const showDrafts = ref(false);
const articlesTotal = ref(0);
const articlesFirst = ref(0);
const articlesLimit = ref(15);
const sortField = ref('created_at');
const sortOrder = ref(-1); // -1 desc, 1 asc

const showDetailDialog = ref(false);
const currentArticle = ref(null);
const detailContentReady = ref(false);
const feedbackSubmitted = ref(false);

const showArticleDialog = ref(false);
const editingArticle = ref(null);
const articleForm = ref({
  title: '',
  summary: '',
  content: '',
  category_id: null,
  tags: [],
  is_published: false,
  is_internal: false
});
const tagInputValue = ref('');

const showCategoryDialog = ref(false);
const editingCategory = ref(null);
const savingCategory = ref(false);
const categoryForm = ref({
  name: '',
  description: '',
  icon: 'pi pi-folder',
  color: '#0ea5e9'
});

const colorPresets = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316', '#6366f1', '#84cc16'];

const categoryOptions = computed(() => [
  { id: null, name: t('filters.allCategories') },
  ...categories.value
]);

const iconOptions = [
  { label: 'Dossier', value: 'pi pi-folder' },
  { label: 'Dossier ouvert', value: 'pi pi-folder-open' },
  { label: 'Fichier', value: 'pi pi-file' },
  { label: 'Livre', value: 'pi pi-book' },
  { label: 'Question', value: 'pi pi-question-circle' },
  { label: 'Info', value: 'pi pi-info-circle' },
  { label: 'Outils', value: 'pi pi-wrench' },
  { label: 'Serveur', value: 'pi pi-server' },
  { label: 'Réseau', value: 'pi pi-sitemap' },
  { label: 'Sécurité', value: 'pi pi-shield' },
  { label: 'Utilisateurs', value: 'pi pi-users' },
  { label: 'Code', value: 'pi pi-code' },
  { label: 'Tag', value: 'pi pi-tag' },
  { label: 'Liste', value: 'pi pi-list' }
];

function getIconLabel(iconValue) {
  const o = iconOptions.find(x => x.value === iconValue);
  return o ? o.label : iconValue;
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString();
}

function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString();
}

// Sanitize HTML for safe display (same logic as Tickets)
function sanitizeHtml(html) {
  if (!html) return '';
  if (!/<[^>]+>/.test(html)) {
    return html.replace(/\n/g, '<br>');
  }
  const allowedTags = ['p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre', 'ul', 'ol', 'li', 'blockquote', 'a', 'h2', 'h3', 'b', 'i', 'img'];
  let clean = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/on\w+="[^"]*"/gi, '')
    .replace(/on\w+='[^']*'/gi, '')
    .replace(/javascript:/gi, '');
  const tagRegex = /<\/?([a-z][a-z0-9]*)\b[^>]*>/gi;
  clean = clean.replace(tagRegex, (match, tagName) => {
    if (allowedTags.includes(tagName.toLowerCase())) {
      return match
        .replace(/\s+style\s*=\s*["'][^"']*["']/gi, '')
        .replace(/\s+onclick\s*=\s*["'][^"']*["']/gi, '')
        .replace(/\s+onerror\s*=\s*["'][^"']*["']/gi, '');
    }
    return '';
  });
  return clean;
}

function handleContentImageUpload(file, callback) {
  try {
    const reader = new FileReader();
    reader.onload = (e) => callback(e.target.result);
    reader.readAsDataURL(file);
  } catch (err) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: t('knowledge.imageUploadFailed') });
  }
}

let searchTimeout = null;
function debouncedSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    articlesFirst.value = 0;
    loadArticles();
  }, 300);
}

function setFilterStatus(status) {
  filterStatus.value = status;
  articlesFirst.value = 0;
  loadArticles();
  loadStats();
}

function onCategoryChange() {
  articlesFirst.value = 0;
  loadArticles();
}

function toggleSort(field) {
  if (sortField.value === field) sortOrder.value = sortOrder.value === -1 ? 1 : -1;
  else { sortField.value = field; sortOrder.value = -1; }
  loadArticles();
}

function onPage(event) {
  articlesFirst.value = event.first;
  articlesLimit.value = event.rows;
  loadArticles();
}

async function loadStats() {
  try {
    if (!canManageKnowledge.value) {
      const res = await api.get('/knowledge/articles?limit=1&skip=0&published_only=true');
      const n = res.data.total ?? 0;
      stats.value = { total: n, published: n };
    } else {
      const [allRes, pubRes] = await Promise.all([
        api.get('/knowledge/articles?limit=1&skip=0&published_only=false'),
        api.get('/knowledge/articles?limit=1&skip=0&published_only=true')
      ]);
      stats.value = {
        total: allRes.data.total ?? 0,
        published: pubRes.data.total ?? 0
      };
    }
  } catch {
    stats.value = { total: 0, published: 0 };
  }
}

async function loadArticles() {
  loadingArticles.value = true;
  try {
    const params = new URLSearchParams();
    params.append('skip', articlesFirst.value);
    params.append('limit', articlesLimit.value);
    if (searchQuery.value) params.append('search', searchQuery.value);
    if (selectedCategoryId.value) params.append('category_id', selectedCategoryId.value);

    if (!canManageKnowledge.value) {
      params.append('published_only', 'true');
    } else {
      params.append('published_only', filterStatus.value === 'published' ? 'true' : 'false');
    }

    const res = await api.get(`/knowledge/articles?${params}`);
    articles.value = res.data.items;
    articlesTotal.value = res.data.total;
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Failed to load articles' });
  } finally {
    loadingArticles.value = false;
  }
}

async function loadCategories() {
  try {
    const res = await api.get('/knowledge/categories');
    categories.value = res.data;
  } catch {
    categories.value = [];
  }
}

function openArticleDetail(article) {
  currentArticle.value = { id: article.id, title: article.title, slug: article.slug };
  detailContentReady.value = false;
  feedbackSubmitted.value = false;
  showDetailDialog.value = true;
}

async function onDetailModalReady() {
  if (!currentArticle.value?.slug) return;
  try {
    const cacheKey = `knowledge_article_${currentArticle.value.id}`;
    const cached = uiStore.getCachedData(cacheKey);
    if (cached) {
      currentArticle.value = markRaw(cached);
    } else {
      const res = await api.get(`/knowledge/articles/${currentArticle.value.slug}`);
      currentArticle.value = markRaw(res.data);
      uiStore.setCachedData(cacheKey, res.data);
    }
    detailContentReady.value = true;
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || 'Article not found' });
    showDetailDialog.value = false;
  }
}

function addTag() {
  const v = tagInputValue.value?.trim();
  if (!v) return;
  if (!articleForm.value.tags.includes(v)) {
    articleForm.value.tags = [...articleForm.value.tags, v];
  }
  tagInputValue.value = '';
}

function removeTag(index) {
  articleForm.value.tags = articleForm.value.tags.filter((_, i) => i !== index);
}

function openArticleDialog(article = null) {
  editingArticle.value = article;
  tagInputValue.value = '';
  if (article) {
    articleForm.value = {
      title: article.title,
      summary: article.summary || '',
      content: article.content,
      category_id: article.category_id,
      tags: article.tags ? [...article.tags] : [],
      is_published: article.is_published,
      is_internal: article.is_internal
    };
  } else {
    articleForm.value = {
      title: '',
      summary: '',
      content: '',
      category_id: null,
      tags: [],
      is_published: false,
      is_internal: false
    };
  }
  showArticleDialog.value = true;
}

async function saveArticle() {
  const contentText = articleForm.value.content?.replace(/<[^>]*>/g, '').trim() || '';
  if (!articleForm.value.title?.trim() || !contentText) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') });
    return;
  }
  saving.value = true;
  try {
    if (editingArticle.value) {
      await api.put(`/knowledge/articles/${editingArticle.value.id}`, articleForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('knowledge.articleUpdated') });
    } else {
      await api.post('/knowledge/articles', articleForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('knowledge.articleCreated') });
    }
    showArticleDialog.value = false;
    loadArticles();
    loadCategories();
    loadStats();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    saving.value = false;
  }
}

async function confirmDeleteArticle(article) {
  if (!confirm(t('common.confirmDeleteItem'))) return;
  try {
    await api.delete(`/knowledge/articles/${article.id}`);
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('knowledge.articleDeleted') });
    currentArticle.value = null;
    showDetailDialog.value = false;
    loadArticles();
    loadCategories();
    loadStats();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
}

async function publishArticle(id) {
  try {
    await api.post(`/knowledge/articles/${id}/publish`);
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('knowledge.publish') });
    if (currentArticle.value?.id === id) currentArticle.value.is_published = true;
    loadArticles();
    loadStats();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
}

async function unpublishArticle(id) {
  try {
    await api.post(`/knowledge/articles/${id}/unpublish`);
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('knowledge.unpublish') });
    if (currentArticle.value?.id === id) currentArticle.value.is_published = false;
    loadArticles();
    loadStats();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
}

async function submitFeedback(helpful) {
  try {
    await api.post(`/knowledge/articles/${currentArticle.value.id}/feedback`, { helpful });
    feedbackSubmitted.value = true;
    if (helpful) currentArticle.value.helpful_count = (currentArticle.value.helpful_count || 0) + 1;
    else currentArticle.value.not_helpful_count = (currentArticle.value.not_helpful_count || 0) + 1;
  } catch {}
}

function resetCategoryForm() {
  editingCategory.value = null;
  categoryForm.value = { name: '', description: '', icon: 'pi pi-folder', color: '#0ea5e9' };
}

function editCategory(cat) {
  editingCategory.value = cat;
  let icon = cat.icon || 'pi pi-folder';
  if (icon && !icon.startsWith('pi ')) icon = 'pi ' + icon;
  categoryForm.value = { name: cat.name, description: cat.description || '', icon, color: cat.color || '#0ea5e9' };
}

async function saveCategory() {
  if (!categoryForm.value.name?.trim()) {
    toast.add({ severity: 'warn', summary: t('validation.error'), detail: t('validation.fillRequiredFields') });
    return;
  }
  savingCategory.value = true;
  try {
    if (editingCategory.value) {
      await api.put(`/knowledge/categories/${editingCategory.value.id}`, categoryForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('knowledge.categoryUpdated') });
    } else {
      await api.post('/knowledge/categories', categoryForm.value);
      toast.add({ severity: 'success', summary: t('common.success'), detail: t('knowledge.categoryCreated') });
    }
    resetCategoryForm();
    loadCategories();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail || t('common.error') });
  } finally {
    savingCategory.value = false;
  }
}

async function confirmDeleteCategory(cat) {
  if (!confirm(t('common.confirmDeleteItem'))) return;
  try {
    await api.delete(`/knowledge/categories/${cat.id}`);
    toast.add({ severity: 'success', summary: t('common.deleted'), detail: t('knowledge.categoryDeleted') });
    loadCategories();
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.error'), detail: e.response?.data?.detail });
  }
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadStats()]);
  loadArticles();
});

onUnmounted(() => {
  if (searchTimeout) {
    clearTimeout(searchTimeout);
    searchTimeout = null;
  }
});
</script>

<style scoped>
.knowledge-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 1rem;
}

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

.create-btn { flex-shrink: 0; }

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

.stat-chip:hover { border-color: var(--border-strong); }

.stat-chip.active {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: white !important;
}

.stat-chip.active .stat-chip-label,
.stat-chip.active .stat-chip-count { color: white !important; }

.stat-chip-label { color: var(--text-secondary); font-weight: 500; }
.stat-chip-count { color: var(--text-primary); font-weight: 700; }

.stat-chip--published:not(.active) { background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.3); }
.stat-chip--published:not(.active) .stat-chip-label,
.stat-chip--published:not(.active) .stat-chip-count { color: #22c55e; }

.stat-chip--draft:not(.active) { background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3); }
.stat-chip--draft:not(.active) .stat-chip-label,
.stat-chip--draft:not(.active) .stat-chip-count { color: #f59e0b; }

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

.toolbar .toolbar-filter :deep(.p-dropdown),
.toolbar .toolbar-filter :deep(.p-dropdown.p-component) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
  min-width: 100px;
  position: relative;
  padding: 0 !important;
}

.toolbar .toolbar-filter :deep(.p-dropdown.p-focus),
.toolbar .toolbar-filter :deep(.p-dropdown:focus),
.toolbar .toolbar-filter :deep(.p-dropdown:hover),
.toolbar .toolbar-filter :deep(.p-dropdown.p-component:hover),
.toolbar .toolbar-filter :deep(.p-dropdown.p-component.p-focus) {
  background: transparent !important;
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

.toolbar-spacer { flex: 1; min-width: 2rem; }

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
.empty-state i { font-size: 2.5rem; color: var(--text-muted); }
.empty-state h3 { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 0; }
.empty-state p { color: var(--text-secondary); margin: 0; font-size: 0.875rem; }

.tickets-list { display: flex; flex-direction: column; flex: 1; overflow-y: auto; }

.knowledge-header {
  display: grid;
  grid-template-columns: 1fr 140px 140px 80px 130px 24px;
  align-items: center;
  gap: 1rem;
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

.header-col { display: flex; align-items: center; gap: 0.375rem; }
.header-col--sortable { cursor: pointer; transition: color 0.15s ease; }
.header-col--sortable:hover { color: var(--primary); }
.header-col--sortable i { font-size: 0.625rem; }
.header-col--arrow { width: 24px; }

.knowledge-row {
  display: grid;
  grid-template-columns: 1fr 140px 140px 80px 130px 24px;
  align-items: center;
  gap: 1rem;
  padding: 0.875rem 1.5rem;
  border-bottom: 1px solid var(--border-default);
  cursor: pointer;
  transition: background 0.15s ease;
}

.knowledge-row:last-child { border-bottom: none; }
.knowledge-row:hover { background: var(--bg-hover); }

.knowledge-title-cell { min-width: 0; }
.knowledge-title-cell .ticket-title { font-size: 0.875rem; font-weight: 500; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.knowledge-title-cell .ticket-type-label { font-size: 0.75rem; color: var(--text-muted); }
.knowledge-category-cell .category-badge { font-size: 0.8125rem; color: var(--text-secondary); }
.knowledge-views { font-variant-numeric: tabular-nums; }
.status-published { font-size: 0.75rem; color: var(--text-muted); }
.ticket-tags { display: flex; gap: 0.375rem; flex-wrap: wrap; }
.ticket-date { font-size: 0.75rem; color: var(--text-muted); white-space: nowrap; }
.ticket-arrow { color: var(--text-muted); font-size: 0.75rem; transition: transform 0.15s ease, color 0.15s ease; }
.knowledge-row:hover .ticket-arrow { transform: translateX(3px); color: var(--primary); }

.pagination {
  display: flex;
  justify-content: center;
  padding: 0.75rem;
  border-top: 1px solid var(--border-default);
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.detail-content { display: flex; flex-direction: column; gap: 1.5rem; }
.detail-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}
.detail-info-grid--form { grid-template-columns: repeat(2, 1fr); }
.detail-section { padding-top: 1rem; border-top: 1px solid var(--border-default); }
.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 0.75rem;
}
.info-item { display: flex; flex-direction: column; gap: 0.25rem; }
.info-label { font-size: 0.75rem; color: var(--text-muted); }
.info-value { font-weight: 500; color: var(--text-primary); }
.required { color: #ef4444; }

.description-box.knowledge-content {
  padding: 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
}
.description-box.knowledge-content br { display: block; content: ''; margin-bottom: 0.25em; }

.feedback-actions { display: flex; gap: 0.5rem; }
.feedback-thanks { font-size: 0.875rem; color: var(--success); display: flex; align-items: center; gap: 0.5rem; }

.detail-actions { display: flex; justify-content: space-between; align-items: center; gap: 1rem; width: 100%; }
.action-buttons { display: flex; flex-wrap: wrap; gap: 0.5rem; }

.form-input-full.p-inputtext,
.form-input-full.p-textarea { width: 100%; background: var(--bg-secondary) !important; border: none !important; border-radius: var(--radius-lg) !important; padding: 1rem !important; font-size: 0.875rem; color: var(--text-primary); }
.form-input-full:focus { box-shadow: 0 0 0 2px var(--ring-color) !important; }

.info-dropdown:deep(.p-dropdown),
.info-item :deep(.info-dropdown) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  width: 100%;
  position: relative;
  padding: 0 !important;
}
.info-item :deep(.info-dropdown .p-dropdown-label) {
  padding: 0.25rem 3rem 0.25rem 0.75rem !important;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-primary);
  background: transparent !important;
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

/* Tags field - même esthétique que le reste de la page */
.tags-field {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  min-height: 2.75rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid transparent;
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}
.tags-field:focus-within {
  box-shadow: 0 0 0 2px var(--ring-color);
  border-color: var(--primary);
}
.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem 0.25rem 0.625rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-primary);
  background: var(--bg-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}
.tag-pill-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  padding: 0;
  margin: 0;
  border: none;
  background: transparent;
  color: var(--text-muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color var(--transition-fast), background var(--transition-fast);
}
.tag-pill-remove:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.tags-input {
  flex: 1;
  min-width: 120px;
  padding: 0.25rem 0;
  font-size: 0.875rem;
  color: var(--text-primary);
  background: transparent;
  border: none;
  outline: none;
}
.tags-input::placeholder {
  color: var(--text-muted);
}

.modal-footer-actions { display: flex; justify-content: flex-end; gap: 0.75rem; }

.category-form-section { border-top: none; padding-top: 0; }
.category-list-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-default);
}
.category-list-item .text-muted { color: var(--text-muted); }

/* Dark mode - Page */
:root.dark .page-header,
:root.dark .toolbar,
:root.dark .tickets-container {
  background: var(--bg-card-solid);
  border-color: var(--border-default);
}
:root.dark .page-title { color: #f1f5f9; }
:root.dark .page-subtitle { color: #94a3b8; border-color: rgba(255,255,255,0.1); }
:root.dark .filter-label,
:root.dark .my-tickets-toggle { color: #94a3b8; }
:root.dark .toolbar-search i { color: #64748b; }
:root.dark .toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-label) { color: #e2e8f0 !important; }
:root.dark .toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-label.p-placeholder) { color: #64748b !important; }
:root.dark .toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-trigger),
:root.dark .toolbar .toolbar-filter :deep(.p-dropdown .p-dropdown-clear-icon) { color: #64748b; }
:root.dark .knowledge-header { background: rgba(0,0,0,0.2); border-color: rgba(255,255,255,0.06); color: #64748b; }
:root.dark .knowledge-row { border-color: rgba(255,255,255,0.06); }
:root.dark .knowledge-row:hover { background: rgba(255,255,255,0.03); }
:root.dark .knowledge-title-cell .ticket-title { color: #f1f5f9; }
:root.dark .knowledge-title-cell .ticket-type-label { color: #64748b; }
:root.dark .knowledge-category-cell .category-badge { color: #cbd5e1; }
:root.dark .status-published,
:root.dark .ticket-date,
:root.dark .ticket-arrow { color: #64748b; }
:root.dark .stat-chip:not(.active) { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.08); }
:root.dark .stat-chip.active { background: var(--primary) !important; border-color: var(--primary) !important; }
:root.dark .stat-chip-label { color: #94a3b8; }
:root.dark .stat-chip-count { color: #e2e8f0; }
:root.dark .empty-state h3 { color: #f1f5f9; }
:root.dark .empty-state p { color: #94a3b8; }
:root.dark .loading-state span { color: #94a3b8; }

/* Dark mode - Article detail modal & form */
:root.dark .detail-content .detail-info-grid,
:root.dark .detail-content .description-box.knowledge-content {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
}
:root.dark .detail-content .section-title { color: var(--primary); }
:root.dark .detail-content .info-label { color: #64748b; }
:root.dark .detail-content .info-value { color: #e2e8f0; }
:root.dark .detail-content .description-box.knowledge-content {
  color: #cbd5e1;
}
:root.dark .detail-content .feedback-thanks { color: var(--success); }

/* Dark mode - Category management modal */
:root.dark .category-list-item {
  background: rgba(255,255,255,0.03);
  border-color: rgba(255,255,255,0.06);
}
:root.dark .category-list-item .font-medium { color: #e2e8f0; }
:root.dark .category-list-item .text-muted,
:root.dark .detail-content .text-muted { color: #64748b !important; }
:root.dark .category-form-section .section-title,
:root.dark .category-form-section .info-label { color: #94a3b8; }
:root.dark .category-form-section .form-input-full.p-inputtext { background: rgba(255,255,255,0.05) !important; color: #f1f5f9; border: 1px solid rgba(255,255,255,0.1); }
:root.dark .detail-section .form-input-full.p-inputtext,
:root.dark .detail-section .form-input-full.p-textarea {
  background: rgba(255,255,255,0.05) !important;
  color: #f1f5f9;
  border: 1px solid rgba(255,255,255,0.1);
}
:root.dark .detail-section .form-input-full::placeholder { color: #64748b; }

/* Dark mode - Chips in modals (PrimeVue Tag) */
:root.dark .detail-tags .p-tag { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.1); color: #e2e8f0; }

/* Dark mode - Boutons et cases (modal article) */
:root.dark .knowledge-page .create-btn.p-button,
:root.dark .knowledge-page .empty-state .p-button,
:root.dark .detail-content .modal-footer-actions .p-button {
  color: #f1f5f9 !important;
}
:root.dark .detail-section label,
:root.dark .detail-section label span {
  color: #e2e8f0 !important;
}
:root.dark .detail-section .p-checkbox .p-checkbox-box {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.2);
}
:root.dark .detail-section .p-checkbox.p-highlight .p-checkbox-box {
  background: var(--primary);
  border-color: var(--primary);
}

/* Dark mode - Tags field */
:root.dark .tags-field {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.1);
}
:root.dark .tags-field:focus-within { border-color: var(--primary); }
:root.dark .tag-pill {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.12);
  color: #e2e8f0;
}
:root.dark .tag-pill-remove { color: #94a3b8; }
:root.dark .tag-pill-remove:hover { color: #e2e8f0; background: rgba(255,255,255,0.08); }
:root.dark .tags-input { color: #f1f5f9; }
:root.dark .tags-input::placeholder { color: #64748b; }

/* Dark mode - Pagination (inside tickets-container) */
:root.dark .tickets-container .p-paginator {
  background: transparent;
  border-color: rgba(255,255,255,0.06);
  color: #94a3b8;
}
:root.dark .tickets-container .p-paginator .p-paginator-pages .p-highlight { background: var(--primary); color: white; }
:root.dark .tickets-container .p-paginator .p-link { color: #cbd5e1; }

@media (max-width: 1024px) {
  .knowledge-header { display: none; }
  .knowledge-row {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto auto;
    gap: 0.5rem 1rem;
    padding: 1rem 1.25rem;
  }
  .knowledge-row .knowledge-title-cell { grid-row: 1; grid-column: 1; }
  .knowledge-row .knowledge-category-cell { grid-row: 2; grid-column: 1; }
  .knowledge-row .ticket-tags { grid-row: 1; grid-column: 2; }
  .knowledge-row .knowledge-views { grid-row: 2; grid-column: 2; }
  .knowledge-row .ticket-date { grid-row: 3; grid-column: 1; }
  .knowledge-row .ticket-arrow { grid-row: 3; grid-column: 2; align-self: center; }
  .toolbar { flex-wrap: wrap; }
}
</style>
