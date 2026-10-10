<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Forecast</h1>
        <p class="text-sm text-muted">Project your wealth forward from today's balances</p>
      </div>
    </div>

    <WealthForecast v-if="summary" :summary="summary" />
    <div v-else-if="error" class="text-sm text-muted">Could not load your balances. Try again shortly.</div>
    <div v-else class="skeleton" style="height: 420px; border-radius: 16px;" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type DashboardSummary } from '@/api/client'
import { useRefetchOnFocus } from '@/composables/useRefetchOnFocus'
import WealthForecast from '@/components/dashboard/WealthForecast.vue'

const summary = ref<DashboardSummary | null>(null)
const error = ref(false)

async function loadSummary() {
  try {
    summary.value = await api.dashboard.summary()
    error.value = false
  } catch {
    error.value = true
  }
}

useRefetchOnFocus(loadSummary)
onMounted(loadSummary)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-8);
}
.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}
</style>
