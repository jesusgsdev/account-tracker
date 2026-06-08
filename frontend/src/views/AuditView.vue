<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit Log</h1>
        <p class="text-sm text-muted">Every value change, recorded forever</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary btn-sm" @click="exportCsv">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export CSV
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters card">
      <div class="filter-row">
        <div class="form-group filter-field">
          <label class="form-label" for="filter-account">Filter by Account</label>
          <select id="filter-account" v-model="filterAccountId" class="form-select">
            <option :value="null">All accounts</option>
            <option v-for="acc in accountsStore.accounts" :key="acc.id" :value="acc.id">
              {{ acc.name }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Account history chart (shown when filtering by account) -->
    <Transition name="slide-up">
      <AccountHistoryChart
        v-if="filterAccountId && accountHistory.length"
        :logs="accountHistory"
        :account-name="selectedAccountName"
        :color="selectedAccountColor"
        class="history-chart"
      />
    </Transition>

    <!-- Audit table -->
    <AuditTable :logs="filteredLogs" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useAuditStore } from '@/stores/audit'
import { useAccountsStore } from '@/stores/accounts'
import AuditTable from '@/components/audit/AuditTable.vue'
import AccountHistoryChart from '@/components/audit/AccountHistoryChart.vue'

const auditStore = useAuditStore()
const accountsStore = useAccountsStore()

const filterAccountId = ref<number | null>(null)
const accountHistory = ref<any[]>([])

const CATEGORY_COLORS: Record<string, string> = {
  INVESTMENTS: '#818cf8',
  RETIREMENT:  '#fb923c',
  SAVINGS:     '#34d399',
}

const filteredLogs = computed(() => {
  if (!filterAccountId.value) return auditStore.logs
  return auditStore.logs.filter(l => l.account_id === filterAccountId.value)
})

const selectedAccountName = computed(() => {
  const acc = accountsStore.accounts.find(a => a.id === filterAccountId.value)
  return acc?.name ?? ''
})

const selectedAccountColor = computed(() => {
  const acc = accountsStore.accounts.find(a => a.id === filterAccountId.value)
  return acc ? (CATEGORY_COLORS[acc.category] ?? '#6c63ff') : '#6c63ff'
})

watch(filterAccountId, async (id) => {
  if (id) {
    accountHistory.value = await auditStore.fetchHistory(id)
  } else {
    accountHistory.value = []
  }
})

function exportCsv() {
  const logs = filteredLogs.value
  const header = 'Date,Account,Previous Value,New Value,Change,Change %,Note'
  const rows = logs.map(l =>
    [
      new Date(l.recorded_at + 'Z').toISOString(),
      `"${l.account_name ?? l.account_id}"`,
      l.previous_value,
      l.new_value,
      l.change_amount,
      l.change_percent?.toFixed(2) ?? '',
      `"${l.note ?? ''}"`,
    ].join(',')
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `audit-log-${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  auditStore.fetchAll()
  accountsStore.fetchAll()
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

.filters {
  margin-bottom: var(--space-4);
  padding: var(--space-4) var(--space-5);
}

.filter-row {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.filter-field { min-width: 200px; flex: 1; }

.history-chart { margin-bottom: var(--space-4); }
</style>
