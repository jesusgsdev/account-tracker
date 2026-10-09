<template>
  <div class="holdings-table-container">
    <div class="holdings-table">
      <div class="table-head">
        <span>Ticker</span>
        <span>Qty</span>
        <span>Avg Cost</span>
        <span>Live Price</span>
        <span>Live Value</span>
        <span>P&amp;L</span>
        <span>Today</span>
        <span class="cell-actions-header">Actions</span>
      </div>

      <div
        v-for="h in holdings"
        :key="h.id"
        class="table-row"
        :class="{ 'row-error': !!h.price_error && !h.is_stale, 'row-editing': editingId === h.id, 'row-stale': h.is_stale }"
      >
        <!-- Ticker + name + error -->
        <div class="cell-ticker">
          <template v-if="editingId === h.id">
            <input v-model="editForm.ticker" type="text" class="edit-input ticker-input" placeholder="Ticker" />
            <input v-model="editForm.display_name" type="text" class="edit-input name-input text-xs" placeholder="Friendly Name" />
          </template>
          <template v-else>
            <div class="ticker-top">
              <span class="ticker-badge" :class="currencyClass(h.currency)">{{ h.ticker }}</span>
              <span v-if="h.is_stale" class="stale-badge" :title="`Last fetched: ${fmtDateTime(h.last_price_at)}`">STALE</span>
            </div>
            <span class="ticker-name text-xs text-muted">{{ h.short_name || h.display_name || '' }}</span>
            <span v-if="h.price_error && !h.is_stale" class="ticker-error text-xs">⚠ {{ h.price_error }}</span>
            <span v-if="h.is_stale && h.last_price_at" class="ticker-stale-info text-xs">as of {{ fmtDateTime(h.last_price_at) }}</span>
          </template>
        </div>

        <!-- Quantity -->
        <div class="cell-num">
          <template v-if="editingId === h.id">
            <input v-model.number="editForm.quantity" type="number" min="0" step="any" class="edit-input" />
          </template>
          <template v-else>{{ h.quantity }}</template>
        </div>

        <!-- Average Cost -->
        <div class="cell-num">
          <template v-if="editingId === h.id">
            <input v-model.number="editForm.avg_cost" type="number" min="0" step="any" class="edit-input" />
          </template>
          <template v-else-if="h.avg_cost != null">
            <span :class="{ 'stale-value': h.is_stale }">{{ fmtNative(h.avg_cost, h.currency) }}</span>
            <span class="currency-tag text-xs text-muted">{{ h.currency }}</span>
          </template>
          <template v-else>—</template>
        </div>

        <!-- Live Price -->
        <div class="cell-num">
          <template v-if="h.live_price != null">
            <span class="live-price" :class="{ 'stale-value': h.is_stale }">{{ fmtNative(h.live_price, h.currency) }}</span>
            <span class="currency-tag text-xs text-muted">{{ h.currency }}</span>
          </template>
          <template v-else-if="isLoading">
            <span class="skeleton-inline" />
          </template>
          <template v-else>—</template>
        </div>

        <!-- Live Value (GBP) -->
        <div class="cell-num">
          <template v-if="h.live_value_gbp != null">
            <span class="value-gbp font-semibold" :class="{ 'stale-value': h.is_stale }">£{{ fmtGbp(h.live_value_gbp) }}</span>
          </template>
          <template v-else-if="isLoading"><span class="skeleton-inline" /></template>
          <template v-else>—</template>
        </div>

        <!-- P&L -->
        <div class="cell-num">
          <template v-if="h.pnl_percent != null">
            <span class="pnl" :class="[h.pnl_percent! >= 0 ? 'pnl-pos' : 'pnl-neg', { 'stale-value': h.is_stale }]">
              {{ h.pnl_percent! >= 0 ? '+' : '' }}{{ h.pnl_percent!.toFixed(2) }}%
            </span>
          </template>
          <template v-else>—</template>
        </div>

        <!-- Day change -->
        <div class="cell-num">
          <template v-if="h.day_change_pct != null">
            <span class="pnl" :class="h.day_change_pct! >= 0 ? 'pnl-pos' : 'pnl-neg'">
              {{ h.day_change_pct! >= 0 ? '+' : '' }}{{ h.day_change_pct!.toFixed(2) }}%
            </span>
          </template>
          <template v-else>—</template>
        </div>

        <!-- Actions -->
        <div class="cell-actions">
          <template v-if="editingId === h.id">
            <button class="icon-btn text-positive" @click="emit('save', h.id)" title="Save">✓</button>
            <button class="icon-btn text-muted" @click="emit('cancel-edit')" title="Cancel">✕</button>
          </template>
          <template v-else>
            <button class="icon-btn text-muted" @click="emit('edit', h)" title="Edit holding">✎</button>
            <button class="icon-btn text-negative" @click="emit('remove', h.id)" title="Remove">✕</button>
          </template>
        </div>
      </div>
    </div>

    <!-- Portfolio Totals Row -->
    <div v-if="portfolio" class="totals-row">
      <span class="totals-label text-xs text-muted">Portfolio Total</span>
      <span class="totals-value font-bold">£{{ fmtGbp(portfolio.total_live_value_gbp ?? 0) }}</span>
      <span v-if="portfolio.total_pnl_percent !== null" class="pnl" :class="portfolio.total_pnl_percent >= 0 ? 'pnl-pos' : 'pnl-neg'">
        {{ portfolio.total_pnl_percent >= 0 ? '+' : '' }}{{ portfolio.total_pnl_percent.toFixed(2) }}% overall
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PortfolioLive } from '@/api/client'
import type { DisplayHolding, EditHoldingForm } from '@/composables/useHoldingsManager'
import { fmtGbp, fmtNative, fmtDateTime, currencyClass } from '@/utils/holdings'

// `editForm` is a shared reactive object owned by the parent; fields are edited in place.
defineProps<{
  holdings: DisplayHolding[]
  portfolio: PortfolioLive | null
  isLoading: boolean
  editingId: number | null
  editForm: EditHoldingForm
}>()
const emit = defineEmits<{
  edit: [holding: DisplayHolding]
  save: [id: number]
  'cancel-edit': []
  remove: [id: number]
}>()
</script>

<style scoped>
.holdings-table-container {
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.holdings-table {
  display: flex;
  flex-direction: column;
  background: var(--bg-surface-2);
}

.table-head {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 1fr 1fr 1.2fr 1fr 1fr 0.8fr;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid var(--bg-border);
  background: var(--bg-elevated);
}

.cell-actions-header {
  text-align: right;
}

.table-row {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 1fr 1fr 1.2fr 1fr 1fr 0.8fr;
  gap: var(--space-2);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--bg-border);
  transition: background var(--transition-fast);
  background: var(--bg-surface);
}
.table-row:last-child {
  border-bottom: none;
}
.table-row:hover {
  background: var(--bg-surface-2);
}

.row-error { opacity: 0.75; }
.row-editing { background: var(--bg-surface-2); }
.row-stale { background: rgba(251, 191, 36, 0.02); }

.cell-ticker {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ticker-top {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.ticker-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.04em;
  width: fit-content;
}

.ticker-usd   { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.ticker-gbp   { background: rgba(52, 211, 153, 0.1); border-color: rgba(52, 211, 153, 0.2); color: #34d399; }
.ticker-other { background: var(--bg-elevated); border-color: var(--bg-border); color: var(--text-secondary); }

.stale-badge {
  font-size: 8px;
  font-weight: 700;
  padding: 1px 3px;
  border-radius: var(--radius-sm);
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.25);
  cursor: help;
}

.ticker-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.ticker-error {
  color: var(--negative);
  font-size: 10px;
  margin-top: 2px;
}

.ticker-stale-info {
  color: #fbbf24;
  font-size: 10px;
  margin-top: 2px;
}

.cell-num {
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.currency-tag {
  color: var(--text-muted);
  font-size: 9px;
}

.stale-value {
  opacity: 0.6;
}

.pnl {
  font-weight: 600;
}
.pnl-pos { color: var(--positive); }
.pnl-neg { color: var(--negative); }

.cell-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: var(--font-size-sm);
  padding: 4px 6px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.icon-btn:hover {
  background: var(--bg-surface-2);
}

.text-positive { color: var(--positive); }
.text-negative { color: var(--negative); }

.edit-input {
  background: var(--bg-elevated);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  padding: var(--space-1) var(--space-2);
  width: 75px;
}
.ticker-input {
  text-transform: uppercase;
  font-weight: 700;
  width: 90px;
}
.name-input {
  width: 130px;
  margin-top: 4px;
}

.skeleton-inline {
  display: inline-block;
  width: 60px;
  height: 14px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  animation: pulse 1.5s ease-in-out infinite;
}

.totals-row {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 1fr 1fr 1.2fr 1fr 1fr 0.8fr;
  gap: var(--space-2);
  align-items: center;
  padding: var(--space-4) var(--space-4);
  background: var(--bg-elevated);
  font-weight: 700;
  border-top: 1px solid var(--bg-border);
}
.totals-label {
  grid-column: 1 / 5;
}
</style>
