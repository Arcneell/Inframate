<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-900">
    <div class="text-center p-8">
      <div class="mb-8">
        <div class="w-24 h-24 mx-auto rounded-full bg-red-900/30 flex items-center justify-center mb-6">
          <i class="pi pi-lock text-red-500 text-5xl"></i>
        </div>
        <h1 class="text-4xl font-bold text-white mb-2">403</h1>
        <h2 class="text-2xl font-semibold text-gray-300 mb-4">{{ t('unauthorized.title') }}</h2>
        <p class="text-lg text-gray-400 mb-2">{{ t('unauthorized.subtitle') }}</p>
        <p class="text-sm text-gray-500">{{ t('unauthorized.message') }}</p>
      </div>

      <div class="flex flex-col sm:flex-row gap-4 justify-center">
        <Button
          :label="t('unauthorized.goBack')"
          icon="pi pi-arrow-left"
          class="p-button-outlined"
          @click="goBack"
        />
        <Button
          :label="t('unauthorized.goHome')"
          icon="pi pi-home"
          @click="goHome"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const router = useRouter();

const goBack = () => {
  router.go(-1);
};

const goHome = () => {
  router.push('/');
};
</script>
