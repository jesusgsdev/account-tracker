<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Market Trackers</h1>
        <p class="text-sm text-muted">A consolidated view of all stock & shares holdings across all accounts</p>
      </div>
      <div class="page-header-actions">
        <span v-if="sharesStore.lastRefreshedAt" class="refresh-timestamp text-xs text-muted">
          Last: {{ formatRefreshed }}
        </span>
        <button
          class="btn btn-sm btn-secondary refresh-all-btn"
          @click="handleRefreshAll"
          :disabled="sharesStore.loading"
          title="Fetch live prices for all holdings at once"
        >
          <span v-if="sharesStore.loading" class="btn-spinner" />
          <span v-else>🔄</span>
          Refresh Prices
        </button>
        <button
          class="btn btn-sm btn-secondary sync-all-btn"
          @click="handleRefreshAll"
          :disabled="sharesStore.loading"
          title="Synchronize all account balances with current live values"
        >
          <span v-if="sharesStore.loading" class="btn-spinner" />
          <span v-else>💾</span>
          Sync All
        </button>
      </div>
    </div>

    <PortfolioWarnings
      :portfolios="Object.values(sharesStore.portfolios)"
      :sync-error="sharesStore.syncError"
      :now="now"
    />
    <WarningBanner v-if="sharesStore.error" level="error">{{ friendlyError }}</WarningBanner>

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

    <!-- Filter and Search Bar -->
    <div class="filters-card card">
      <div class="filters-row">
        <!-- Search -->
        <div class="search-box">
          <div class="input-wrapper">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search ticker, name or account..."
              class="search-input"
            />
          </div>
        </div>

        <!-- Category Filter Tabs -->
        <div class="tab-filters">
          <button
            class="tab-btn"
            :class="{ active: activeCategory === 'ALL' }"
            @click="activeCategory = 'ALL'"
          >
            All Categories
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeCategory === 'INVESTMENTS' }"
            @click="activeCategory = 'INVESTMENTS'"
          >
            Investments
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeCategory === 'RETIREMENT' }"
            @click="activeCategory = 'RETIREMENT'"
          >
            Retirement
          </button>
        </div>
      </div>
    </div>

    <!-- Holdings Table -->
    <div v-if="sharesStore.loading && !allHoldings.length" class="skeleton-wrapper">
      <div v-for="i in 5" :key="i" class="skeleton skeleton-row" />
    </div>

    <template v-else>
      <div v-if="filteredHoldings.length > 0" class="table-wrapper card">
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
            <tr v-for="h in filteredHoldings" :key="h.id" class="holding-row">
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

      <!-- Empty State -->
      <div v-else class="empty-state-container card">
        <span class="empty-icon">📈</span>
        <h3 class="empty-title">No Holdings Tracked</h3>
        <p class="empty-desc">
          We couldn't find any holdings matching your criteria. To add stock holdings to your Investment or Retirement accounts, go to the Accounts view and click "Manage" on the card.
        </p>
        <RouterLink to="/accounts" class="btn btn-primary btn-sm">
          Go to Accounts
        </RouterLink>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useSharesStore } from '@/stores/shares'
import { apiErrorMessage } from '@/api/client'
import WarningBanner from '@/components/common/WarningBanner.vue'
import PortfolioWarnings from '@/components/common/PortfolioWarnings.vue'

const accountsStore = useAccountsStore()
const sharesStore = useSharesStore()

const searchQuery = ref('')
const activeCategory = ref<'ALL' | 'INVESTMENTS' | 'RETIREMENT'>('ALL')
const now = ref(new Date())
let relativeTimer: any = null

onMounted(async () => {
  await accountsStore.fetchAll()
  await sharesStore.refreshAll()
  
  relativeTimer = setInterval(() => {
    now.value = new Date()
  }, 10000)
})

onUnmounted(() => {
  if (relativeTimer) clearInterval(relativeTimer)
})

// Relative Refresh Clock
const formatRefreshed = computed(() => {
  const d = sharesStore.lastRefreshedAt
  if (!d) return ''
  const diffMs = now.value.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  const timeStr = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  if (diffMins < 1) {
    return `${timeStr} (just now)`
  }
  return `${timeStr} (${diffMins}m ago)`
})

const friendlyError = computed(() => apiErrorMessage(new Error(sharesStore.error ?? '')))

// Trigger a refresh of prices and accounts values
async function handleRefreshAll() {
  await sharesStore.refreshAll()
  await accountsStore.fetchAll()
}

// Flat list of all holdings linked to their account metadata
const allHoldings = computed(() => {
  const list = []
  for (const accountId in sharesStore.portfolios) {
    const portfolio = sharesStore.portfolios[accountId]
    const account = accountsStore.accounts.find(a => a.id === Number(accountId))
    if (!account) continue
    
    for (const h of portfolio.holdings) {
      list.push({
        ...h,
        accountName: account.name,
        accountCategory: account.category,
        accountProvider: account.provider,
      })
    }
  }
  return list
})

// Filtered holdings list
const filteredHoldings = computed(() => {
  return allHoldings.value.filter(h => {
    // Category filter
    if (activeCategory.value !== 'ALL' && h.accountCategory !== activeCategory.value) {
      return false
    }

    // Search query filter
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const matchesTicker = h.ticker.toLowerCase().includes(q)
      const matchesName = (h.short_name || h.display_name || '').toLowerCase().includes(q)
      const matchesAccount = h.accountName.toLowerCase().includes(q)
      const matchesProvider = (h.accountProvider || '').toLowerCase().includes(q)
      return matchesTicker || matchesName || matchesAccount || matchesProvider
    }

    return true
  })
})

// Totals Calculation
const totals = computed(() => {
  let totalValue = 0
  let totalCost = 0
  
  for (const h of filteredHoldings.value) {
    if (h.live_value_gbp != null) {
      totalValue += h.live_value_gbp
    }
    // Calculate cost basis in GBP
    if (h.quantity && h.avg_cost != null) {
      const divisor = h.currency === 'GBX' ? 100 : 1
      const valueNative = h.quantity * h.avg_cost
      // Fallback rate if gbpusd_rate is not returned
      const rate = sharesStore.portfolios[h.account_id]?.gbpusd_rate || 1.30
      let valueGbp = 0
      if (h.currency === 'GBP') {
        valueGbp = valueNative
      } else if (h.currency === 'GBX') {
        valueGbp = valueNative / 100
      } else if (h.currency === 'USD') {
        valueGbp = valueNative / rate
      } else {
        // Fallback for other currencies (default to direct conversion if we don't have exchange rates)
        valueGbp = valueNative
      }
      totalCost += valueGbp
    }
  }
  
  const pnl = totalValue - totalCost
  const pnlPercent = totalCost > 0 ? (pnl / totalCost) * 100 : 0
  
  return {
    value: totalValue,
    cost: totalCost,
    pnl,
    pnlPercent,
    activeHoldings: filteredHoldings.value.length,
  }
})

// Formatting Helpers
function fmtGbp(v: number | null | undefined) {
  if (v == null) return '—'
  return v.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtNative(price: number | undefined, currency: string | null | undefined) {
  if (price == null) return '—'
  const divisor = currency === 'GBX' ? 100 : 1
  return (price / divisor).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtDateTime(iso: string | null | undefined) {
  if (!iso) return ''
  return new Date(iso + (iso.endsWith('Z') ? '' : 'Z')).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

function currencyClass(currency: string | null | undefined) {
  if (!currency) return ''
  if (currency === 'USD') return 'ticker-usd'
  if (currency === 'GBP' || currency === 'GBX') return 'ticker-gbp'
  return 'ticker-other'
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.refresh-all-btn, .sync-all-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  white-space: nowrap;
}

.btn-spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin-global 0.6s linear infinite;
}
@keyframes spin-global { to { transform: rotate(360deg); } }

.refresh-timestamp {
  white-space: nowrap;
  opacity: 0.7;
}

/* Metrics Dashboard Grid */
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

/* Filters Card */
.filters-card {
  padding: var(--space-4) var(--space-5);
  margin-bottom: var(--space-6);
}

.filters-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 280px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--space-2) var(--space-3) var(--space-2) 36px;
  border-radius: var(--radius-md);
  border: 1px solid var(--bg-border);
  background: var(--bg-surface-2);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: all var(--transition-fast);
}

.search-input:focus {
  border-color: var(--accent-light);
  box-shadow: 0 0 0 2px var(--accent-glow);
}

.tab-filters {
  display: flex;
  background: var(--bg-surface-2);
  padding: 4px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--bg-border);
}

.tab-btn {
  background: transparent;
  border: none;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-surface);
  color: var(--accent-light);
  box-shadow: var(--shadow-sm);
}

/* Table Design */
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

/* Empty State Styling */
.empty-state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  text-align: center;
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  margin-bottom: var(--space-2);
}

.empty-desc {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  max-width: 460px;
  margin-bottom: var(--space-6);
  line-height: 1.5;
}

/* Skeleton Loading layout */
.skeleton-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.skeleton-row {
  height: 52px;
  border-radius: var(--radius-md);
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
