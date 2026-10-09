<template>
  <div class="warning-banner" :class="`level-${level}`" :role="level === 'error' ? 'alert' : 'status'" aria-live="polite">
    <span class="wb-icon" aria-hidden="true">{{ level === 'error' ? '⛔' : '⚠️' }}</span>
    <div class="wb-body">
      <div v-if="title" class="wb-title">{{ title }}</div>
      <div class="wb-text"><slot /></div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ level?: 'warn' | 'error'; title?: string }>(), { level: 'warn' })
</script>

<style scoped>
.warning-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid;
  font-size: var(--font-size-xs);
  line-height: 1.5;
  margin-bottom: var(--space-3);
}
.level-warn {
  background: var(--cat-retirement-bg);
  border-color: var(--cat-retirement);
  color: var(--text-primary);
}
.level-error {
  background: var(--negative-bg);
  border-color: var(--negative);
  color: var(--text-primary);
}
.wb-title { font-weight: 600; margin-bottom: 2px; }
.wb-text { color: var(--text-secondary); }
</style>
