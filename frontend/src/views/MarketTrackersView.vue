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

    <MarketMetrics :totals="totals" />

    <MarketFilters v-model:search-query="searchQuery" v-model:active-category="activeCategory" />

    <!-- Holdings Table -->
    <div v-if="sharesStore.loading && !allHoldings.length" class="skeleton-wrapper">
      <div v-for="i in 5" :key="i" class="skeleton skeleton-row" />
    </div>

    <template v-else>
      <MarketHoldingsTable v-if="filteredHoldings.length > 0" :holdings="filteredHoldings" />
      <MarketEmptyState v-else />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useSharesStore } from '@/stores/shares'
import { useRefetchOnFocus } from '@/composables/useRefetchOnFocus'
import { useNow } from '@/composables/useNow'
import { useMarketHoldings } from '@/composables/useMarketHoldings'
import { formatRefreshedLabel } from '@/utils/holdings'
import WarningBanner from '@/components/common/WarningBanner.vue'
import PortfolioWarnings from '@/components/common/PortfolioWarnings.vue'
import MarketMetrics from '@/components/market/MarketMetrics.vue'
import MarketFilters from '@/components/market/MarketFilters.vue'
import MarketHoldingsTable from '@/components/market/MarketHoldingsTable.vue'
import MarketEmptyState from '@/components/market/MarketEmptyState.vue'

const accountsStore = useAccountsStore()
const sharesStore = useSharesStore()

const { searchQuery, activeCategory, allHoldings, filteredHoldings, totals } = useMarketHoldings()
const now = useNow()

onMounted(async () => {
  await accountsStore.fetchAll()
  await sharesStore.ensureFresh()
})

// Relative refresh clock
const formatRefreshed = computed(() => formatRefreshedLabel(sharesStore.lastRefreshedAt, now.value))

const friendlyError = computed(() => sharesStore.error ?? '')

// Trigger a refresh of prices and accounts values
async function handleRefreshAll() {
  await sharesStore.refreshAll()
  await accountsStore.fetchAll(true)
  focus.touch()
}

// Refetch live prices when the tab regains focus (throttled)
const focus = useRefetchOnFocus(() => { sharesStore.ensureFresh(); accountsStore.fetchAll(true) })
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
