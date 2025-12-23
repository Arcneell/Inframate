<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
    <div class="text-center p-8">
      <div class="mb-8">
        <div class="w-24 h-24 mx-auto rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-6">
          <i class="pi pi-lock text-red-500 text-5xl"></i>
        </div>
        <h1 class="text-4xl font-bold text-gray-800 dark:text-white mb-2">403</h1>
        <h2 class="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-4">{{ t('unauthorizedTitle').value }}</h2>
        <p class="text-lg text-gray-600 dark:text-gray-400 mb-2">{{ t('unauthorizedSubtitle').value }}</p>
        <p class="text-sm text-gray-500 dark:text-gray-500">{{ t('unauthorizedMessage').value }}</p>
      </div>

      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <Button
          :label="t('goBack').value"
          icon="pi pi-arrow-left"
          class="p-button-outlined"
          @click="goBack"
        />
        <Button
          :label="t('goHome').value"
          icon="pi pi-home"
          @click="goHome"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { t } from '../i18n';

const router = useRouter();

const goBack = () => {
  router.go(-1);
};

const goHome = () => {
  router.push('/');
};
</script>
