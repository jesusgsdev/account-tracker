<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Data</h1>
        <p class="text-sm text-muted">Snapshots, backups and exports</p>
      </div>
    </div>
    <DataToolsPanel />
  </div>
</template>

<script setup lang="ts">
import DataToolsPanel from '@/components/data/DataToolsPanel.vue'
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
