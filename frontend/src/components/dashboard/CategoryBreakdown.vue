<template>
  <div class="category-card card" :class="`cat-${category.toLowerCase()}`">
    <div class="cat-header">
      <div class="cat-icon">{{ ICONS[category] }}</div>
      <span class="badge" :class="`badge-${category.toLowerCase()}`">{{ category }}</span>
    </div>
    <div class="cat-value">£{{ formattedValue }}</div>
    <div class="cat-meta">
      <span class="text-xs text-muted">{{ accountCount }} account{{ accountCount !== 1 ? 's' : '' }}</span>
      <span v-if="changePercent !== null" class="change-pill" :class="changePercent >= 0 ? 'positive' : 'negative'">
        {{ changePercent >= 0 ? '▲' : '▼' }} {{ Math.abs(changePercent).toFixed(1) }}%
      </span>
    </div>
    <div class="cat-bar">
      <div class="cat-bar-fill" :style="{ width: `${barWidth}%` }" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  category: string
  totalValue: number
  accountCount: number
  changePercent: number | null
  totalPortfolio: number
}>()

const ICONS: Record<string, string> = {
  INVESTMENTS: '📈',
  RETIREMENT: '🏦',
  SAVINGS: '💰',
}

const formattedValue = computed(() =>
  props.totalValue.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
)

const barWidth = computed(() =>
  props.totalPortfolio > 0 ? Math.min(100, (props.totalValue / props.totalPortfolio) * 100) : 0
)
</script>

<style scoped>
.category-card {
  position: relative;
  overflow: hidden;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}
.category-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.cat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.cat-icon { font-size: 1.5rem; }

.cat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-2);
}

.cat-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.change-pill {
  font-size: var(--font-size-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.change-pill.positive { background: var(--positive-bg); color: var(--positive); }
.change-pill.negative { background: var(--negative-bg); color: var(--negative); }

.cat-bar {
  height: 4px;
  background: var(--bg-base);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.cat-bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.8s ease;
}

.cat-investments .cat-bar-fill { background: var(--cat-investments); }
.cat-retirement  .cat-bar-fill { background: var(--cat-retirement); }
.cat-savings     .cat-bar-fill { background: var(--cat-savings); }
</style>
