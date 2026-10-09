<template>
  <div class="table-wrapper card">
    <table class="holdings-table">
      <thead>
        <tr>
          <th>Ticker / Holding</th>
          <th>Account</th>
          <th>Category</th>
          <th class="text-right">Quantity</th>
          <th class="text-right">Avg Cost</th>
          <th class="text-right">Live Price</th>
          <th class="text-right">Market Value</th>
          <th class="text-right">P&amp;L</th>
          <th class="text-right">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="h in holdings" :key="h.id" class="holding-row">
          <!-- Ticker and Name -->
          <td class="td-ticker">
            <div class="ticker-badge-wrap">
              <span class="ticker-badge" :class="currencyClass(h.currency)">{{ h.ticker }}</span>
              <span v-if="h.is_stale" class="badge-stale" :title="`Stale fallback: ${fmtDateTime(h.last_price_at)}`">STALE</span>
            </div>
            <div class="ticker-name text-xs text-muted">{{ h.short_name || h.display_name || '—' }}</div>
          </td>

          <!-- Account Name -->
          <td class="td-account">
            <span class="account-name font-medium">{{ h.accountName }}</span>
            <span class="account-provider text-xs text-muted block">{{ h.accountProvider }}</span>
          </td>

          <!-- Category Badge -->
          <td>
            <span class="badge" :class="`badge-${h.accountCategory.toLowerCase()}`">
              {{ h.accountCategory }}
            </span>
          </td>

          <!-- Quantity -->
          <td class="text-right td-mono font-medium">{{ h.quantity }}</td>

          <!-- Avg Cost -->
          <td class="text-right td-mono">
            <template v-if="h.avg_cost != null">
              {{ fmtNative(h.avg_cost, h.currency) }}
              <span class="currency-tag text-xs text-muted">{{ h.currency }}</span>
            </template>
            <template v-else>—</template>
          </td>

          <!-- Live Price -->
          <td class="text-right td-mono">
            <template v-if="h.live_price != null">
              <span :class="{ 'dimmed-value': h.is_stale }">{{ fmtNative(h.live_price, h.currency) }}</span>
              <span class="currency-tag text-xs text-muted">{{ h.currency }}</span>
            </template>
            <template v-else>—</template>
          </td>

          <!-- Market Value (GBP) -->
          <td class="text-right td-mono font-semibold">
            <template v-if="h.live_value_gbp != null">
              <span :class="{ 'dimmed-value': h.is_stale }">£{{ fmtGbp(h.live_value_gbp) }}</span>
            </template>
            <template v-else>—</template>
          </td>

          <!-- P&L -->
          <td class="text-right td-mono">
            <span v-if="h.pnl_percent != null" class="pnl-pill" :class="h.pnl_percent >= 0 ? 'positive' : 'negative'">
              {{ h.pnl_percent >= 0 ? '+' : '' }}{{ h.pnl_percent.toFixed(2) }}%
            </span>
            <span v-else>—</span>
          </td>

          <!-- Status -->
          <td class="text-right text-xs">
            <span v-if="h.price_error && !h.is_stale" class="status-error" :title="h.price_error">⚠ Error</span>
            <span v-else-if="h.is_stale && h.last_price_at" class="status-date text-muted" :title="`Cached value`">
              As of {{ fmtDateTime(h.last_price_at) }}
            </span>
            <span v-else class="status-ok">● Live</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { MarketHolding } from '@/composables/useMarketHoldings'
import { fmtGbp, fmtNative, fmtDateTime, currencyClass } from '@/utils/holdings'

defineProps<{ holdings: MarketHolding[] }>()
</script>

<style scoped>
.table-wrapper {
  overflow-x: auto;
  padding: 0;
  border: 1px solid var(--bg-border);
}

.holdings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.holdings-table th {
  background: var(--bg-surface-2);
  padding: var(--space-4) var(--space-5);
  text-align: left;
  font-size: var(--font-size-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--bg-border);
  white-space: nowrap;
}

.holding-row td {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--bg-border);
  vertical-align: middle;
}

.holding-row:hover td {
  background: var(--bg-surface-2);
}

.td-ticker {
  min-width: 160px;
}

.ticker-badge-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: 2px;
}

.ticker-badge {
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.ticker-usd {
  background: rgba(129, 140, 248, 0.15);
  color: var(--accent-light);
  border: 1px solid rgba(129, 140, 248, 0.3);
}

.ticker-gbp {
  background: rgba(52, 211, 153, 0.15);
  color: var(--cat-savings);
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.ticker-other {
  background: rgba(251, 146, 60, 0.15);
  color: var(--cat-retirement);
  border: 1px solid rgba(251, 146, 60, 0.3);
}

.badge-stale {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
}

.td-account {
  min-width: 180px;
}

.account-name {
  color: var(--text-primary);
  display: block;
}

.block {
  display: block;
}

.pnl-pill {
  display: inline-block;
  padding: 2px var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
  text-align: right;
}

.pnl-pill.positive {
  background: var(--positive-bg);
  color: var(--positive);
}

.pnl-pill.negative {
  background: var(--negative-bg);
  color: var(--negative);
}

.dimmed-value {
  color: var(--text-muted);
  opacity: 0.8;
}

.status-ok {
  color: var(--positive);
  font-weight: 600;
}

.status-error {
  color: var(--negative);
  font-weight: 600;
}

.status-date {
  font-size: var(--font-size-xs);
}

.currency-tag {
  margin-left: 2px;
}

.td-mono {
  font-variant-numeric: tabular-nums;
}

.text-right {
  text-align: right;
}
</style>
