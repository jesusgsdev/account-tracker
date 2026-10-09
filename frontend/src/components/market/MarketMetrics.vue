<template>
  <!-- Summary Metrics Cards -->
  <div class="metrics-grid">
    <div class="metric-card card val-card">
      <div class="metric-info">
        <span class="metric-label">Total Portfolio Value</span>
        <span class="metric-value font-semibold">£{{ fmtGbp(totals.value) }}</span>
      </div>
      <div class="metric-badge-wrap">
        <span class="metric-subtext">across {{ totals.activeHoldings }} holdings</span>
      </div>
    </div>

    <div class="metric-card card cost-card">
      <div class="metric-info">
        <span class="metric-label">Total Cost Basis</span>
        <span class="metric-value font-semibold">£{{ fmtGbp(totals.cost) }}</span>
      </div>
      <div class="metric-badge-wrap">
        <span class="metric-subtext">capital invested</span>
      </div>
    </div>

    <div class="metric-card card pnl-card" :class="totals.pnl >= 0 ? 'pos-trend' : 'neg-trend'">
      <div class="metric-info">
        <span class="metric-label">Total Return (P&amp;L)</span>
        <span class="metric-value font-semibold">
          {{ totals.pnl >= 0 ? '+' : '' }}£{{ fmtGbp(totals.pnl) }}
        </span>
      </div>
      <div class="metric-badge-wrap">
        <span class="trend-badge">
          {{ totals.pnl >= 0 ? '▲' : '▼' }} {{ totals.pnlPercent.toFixed(2) }}%
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MarketTotals } from '@/composables/useMarketHoldings'
import { fmtGbp } from '@/utils/holdings'

defineProps<{ totals: MarketTotals }>()
</script>

<style scoped>
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.metric-card {
  padding: var(--space-5) var(--space-6);
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  position: relative;
  overflow: hidden;
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
}

.metric-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.metric-label {
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.metric-value {
  font-size: var(--font-size-2xl);
  color: var(--text-primary);
  line-height: 1.1;
}

.metric-badge-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.metric-subtext {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.trend-badge {
  padding: 4px var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
}

/* Specific Card themes */
.val-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--accent-light);
}

.pnl-card.pos-trend::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--positive);
}

.pnl-card.neg-trend::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--negative);
}

.pnl-card.pos-trend .trend-badge {
  background: var(--positive-bg);
  color: var(--positive);
}

.pnl-card.neg-trend .trend-badge {
  background: var(--negative-bg);
  color: var(--negative);
}
</style>
