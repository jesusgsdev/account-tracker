<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="text-sm text-muted">Your UK financial snapshot</p>
      </div>
      <div class="header-actions">
        <span v-if="summary?.last_updated" class="text-xs text-muted">
          As of {{ lastUpdatedFormatted }}
        </span>
      </div>
    </div>

    <!-- Error banner -->
    <div v-if="error" class="error-banner">
      ⚠️ Could not connect to backend. Make sure the Python server is running on port 8000.
    </div>

    <!-- Net Worth Hero -->
    <div class="hero-section">
      <NetWorthCard
        :total-value="summary?.total_value ?? 0"
        :accounts-total="summary?.accounts_total ?? 0"
        :mortgage-equity="summary?.mortgage_equity ?? 0"
        :mortgage-summary="summary?.mortgage_summary ?? null"
        :last-updated="summary?.last_updated ?? null"
        :price-warning="priceWarning"
      />
    </div>

    <!-- Category Cards -->
    <div class="category-grid">
      <CategoryBreakdown
        v-for="cat in summary?.categories ?? []"
        :key="cat.category"
        :category="cat.category"
        :total-value="cat.total_value"
        :account-count="cat.account_count"
        :change-percent="cat.last_change_percent"
        :total-portfolio="summary?.total_value ?? 1"
      />
      <!-- Property Equity Card -->
      <div v-if="summary?.mortgage_summary" class="category-card card cat-property">
        <div class="cat-header">
          <div class="cat-icon">🏠</div>
          <span class="badge badge-property">Property Equity</span>
        </div>
        <div class="cat-value">{{ formatGBP(summary.mortgage_equity) }}</div>
        <div class="cat-meta">
          <span class="text-xs text-muted">
            {{ summary.mortgage_summary.mortgage_count }} propert{{ summary.mortgage_summary.mortgage_count !== 1 ? 'ies' : 'y' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Charts -->
    <div class="charts-grid">
      <NetWorthChart
        :points="history?.points ?? []"
        :loading="historyLoading"
        :initial-days="chartDays"
        class="chart-main"
        @range-change="onRangeChange"
      />
      <AllocationPie :categories="summary?.categories ?? []" class="chart-pie" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { parseApiDate } from '@/utils/date'
import { ref, computed, onMounted } from 'vue'
import { api, type DashboardSummary, type DashboardHistory } from '@/api/client'
import { useLocalStorage } from '@vueuse/core'
import { useRefetchOnFocus } from '@/composables/useRefetchOnFocus'
import { formatGBP } from '@/utils/format'
import { useSharesStore } from '@/stores/shares'
import NetWorthCard from '@/components/dashboard/NetWorthCard.vue'
import CategoryBreakdown from '@/components/dashboard/CategoryBreakdown.vue'
import NetWorthChart from '@/components/dashboard/NetWorthChart.vue'
import AllocationPie from '@/components/dashboard/AllocationPie.vue'

const sharesStore = useSharesStore()

// Uses only already-fetched share state (populated when Accounts / Trackers were visited)
const priceWarning = computed(() => {
  if (sharesStore.syncError) return 'Last share sync failed'
  const ps = Object.values(sharesStore.portfolios)
  const stale = ps.reduce((n, p) => n + p.holdings.filter(h => h.is_stale || h.live_value_gbp == null).length, 0)
  if (stale) return `${stale} holding${stale === 1 ? '' : 's'} with stale or missing prices`
  if (ps.some(p => p.gbpusd_rate_is_fallback)) return 'Using fallback GBP/USD rate'
  return null
})

/** Remembered net-worth chart range (days). */
const chartDays = useLocalStorage('foliotrack.nwChartDays', 365)

const summary = ref<DashboardSummary | null>(null)
const history = ref<DashboardHistory | null>(null)
const historyLoading = ref(false)
const error = ref(false)

const lastUpdatedFormatted = computed(() => {
  if (!summary.value?.last_updated) return ''
  return parseApiDate(summary.value.last_updated).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
})

async function loadSummary() {
  try {
    summary.value = await api.dashboard.summary()
    error.value = false
  } catch {
    error.value = true
  }
}

async function loadHistory(days = 365) {
  historyLoading.value = true
  try {
    history.value = await api.dashboard.history(days)
  } finally {
    historyLoading.value = false
  }
}

function onRangeChange(days: number) {
  chartDays.value = days
  loadHistory(days)
}

useRefetchOnFocus(() => { loadSummary(); loadHistory(chartDays.value) })

onMounted(() => {
  loadSummary()
  loadHistory(chartDays.value)
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}

.error-banner {
  background: var(--negative-bg);
  border: 1px solid rgba(239,68,68,0.3);
  color: var(--negative);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  margin-bottom: var(--space-6);
}

.hero-section { margin-bottom: var(--space-6); }

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: var(--space-4);
}

/* Property card styling in dashboard */
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
.badge-property { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
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
}

@media (max-width: 1024px) {
  .charts-grid { grid-template-columns: 1fr; }
  .category-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .category-grid { grid-template-columns: 1fr; }
}

</style>
