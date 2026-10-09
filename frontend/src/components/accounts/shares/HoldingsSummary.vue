<template>
  <!-- Compact Summary (Inside the Card) -->
  <div class="summary-box">
    <div class="summary-top">
      <span class="summary-title text-xs font-semibold text-muted uppercase tracking-wider">📊 Holdings Summary</span>
      <button class="btn btn-xs btn-outline manage-btn" @click="emit('manage')">
        ⚙️ Manage
      </button>
    </div>

    <div v-if="holdings.length === 0" class="empty-summary text-xs text-muted">
      No holdings tracked yet.
      <button class="btn btn-link btn-xs inline-add-link" @click="emit('add')">
        + Add holdings
      </button>
    </div>

    <div v-else class="summary-details">
      <!-- Totals & P&L -->
      <div v-if="portfolio" class="summary-stats">
        <div class="stat-item">
          <span class="stat-lbl text-xs text-muted">Value:</span>
          <span class="stat-val font-semibold text-sm">£{{ fmtGbp(portfolio.total_live_value_gbp ?? 0) }}</span>
        </div>
        <div class="stat-item" v-if="portfolio.total_pnl_percent !== null">
          <span class="stat-lbl text-xs text-muted">PnL:</span>
          <span class="stat-val font-semibold text-sm" :class="portfolio.total_pnl_percent >= 0 ? 'pnl-pos' : 'pnl-neg'">
            {{ portfolio.total_pnl_percent >= 0 ? '+' : '' }}{{ portfolio.total_pnl_percent.toFixed(2) }}%
          </span>
        </div>
      </div>

      <PortfolioWarnings :portfolios="portfolio ? [portfolio] : []" :now="now" />

      <!-- Chips of Tickers -->
      <div class="ticker-chips">
        <span
          v-for="h in displayHoldings"
          :key="h.id"
          class="summary-chip"
          :class="[currencyClass(h.currency), { 'stale-chip': h.is_stale }]"
          :title="`${h.short_name || h.display_name || ''} - ${h.quantity} shares`"
        >
          {{ h.ticker }} <span class="qty-sub">({{ h.quantity }})</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ShareHolding, PortfolioLive } from '@/api/client'
import type { DisplayHolding } from '@/composables/useHoldingsManager'
import { fmtGbp, currencyClass } from '@/utils/holdings'
import PortfolioWarnings from '@/components/common/PortfolioWarnings.vue'

defineProps<{
  holdings: ShareHolding[]
  displayHoldings: DisplayHolding[]
  portfolio: PortfolioLive | null
  now: Date
}>()
const emit = defineEmits<{ manage: []; add: [] }>()
</script>

<style scoped>
.summary-box {
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.summary-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-title {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  letter-spacing: 0.05em;
  font-weight: 600;
}

.manage-btn {
  padding: 2px 8px;
  font-size: var(--font-size-xs);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
  border: 1px solid var(--bg-border);
  background: transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}
.manage-btn:hover {
  background: var(--bg-surface);
  color: var(--text-primary);
  border-color: var(--text-secondary);
}

.empty-summary {
  padding: var(--space-1) 0;
  font-size: var(--font-size-xs);
}

.inline-add-link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-left: 4px;
}
.inline-add-link:hover {
  text-decoration: underline;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.summary-stats {
  display: flex;
  gap: var(--space-4);
  align-items: center;
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.stat-lbl {
  color: var(--text-muted);
}

.stat-val {
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.ticker-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.summary-chip {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--bg-border);
  letter-spacing: 0.02em;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  transition: all 0.15s;
}

.qty-sub {
  font-weight: 500;
  opacity: 0.8;
}

.ticker-usd   { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.ticker-gbp   { background: rgba(52, 211, 153, 0.1); border-color: rgba(52, 211, 153, 0.2); color: #34d399; }
.ticker-other { background: var(--bg-elevated); border-color: var(--bg-border); color: var(--text-secondary); }
.stale-chip   { border-color: rgba(251,191,36,0.3); background: rgba(251,191,36,0.05); color: #fbbf24; }

.pnl-pos { color: var(--positive); }
.pnl-neg { color: var(--negative); }
</style>
