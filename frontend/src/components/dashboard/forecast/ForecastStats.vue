<template>
  <div class="stats-row">
    <div class="stat-card">
      <span class="stat-label text-xs text-muted font-medium">Projected Net Worth ({{ endYear || startYear + 1 }})</span>
      <span class="stat-value text-xl font-bold">£{{ finalNetWorth }}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label text-xs text-muted font-medium">Total Contributions</span>
      <span class="stat-value text-xl font-bold text-secondary">£{{ totalContributions }}</span>
    </div>
    <div class="stat-card">
      <span class="stat-label text-xs text-muted font-medium">Compound Gains</span>
      <span class="stat-value text-xl font-bold text-positive">£{{ compoundGains }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  endYear: number
  startYear: number
  finalNetWorth: string
  totalContributions: string
  compoundGains: string
}>()
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

.stat-card {
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-label {
  letter-spacing: 0.02em;
}

.stat-value {
  color: var(--text-primary);
}

.text-secondary { color: #a855f7; }
.text-positive { color: var(--positive); }

@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
