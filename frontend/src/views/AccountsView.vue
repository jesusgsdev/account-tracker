<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Accounts</h1>
        <p class="text-sm text-muted">{{ store.accounts.length }} account{{ store.accounts.length !== 1 ? 's' : '' }} tracked</p>
      </div>
      <div class="page-header-actions">
        <span v-if="sharesStore.lastRefreshedAt" class="refresh-timestamp text-xs text-muted">
          Last: {{ formatRefreshed }}
        </span>
        <button
          class="btn btn-sm btn-secondary refresh-all-btn"
          @click="handleRefreshPrices"
          :disabled="sharesStore.loading || syncingAll"
          title="Fetch live prices for all holdings (display only, balances are not changed)"
        >
          <span v-if="sharesStore.loading" class="btn-spinner" />
          <span v-else>🔄</span>
          Refresh Prices
        </button>
        <button
          class="btn btn-sm btn-secondary sync-all-btn"
          @click="handleSyncAll"
          :disabled="sharesStore.loading || syncingAll"
          title="Synchronize all share-holding account balances with current live values"
        >
          <span v-if="syncingAll" class="btn-spinner" />
          <span v-else>💾</span>
          Sync All
        </button>
        <button class="btn btn-sm btn-primary add-account-btn" @click="showAdd = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Add Account
        </button>
      </div>
    </div>

    <div v-if="store.loading && !store.accounts.length" class="loading-grid">
      <div v-for="i in 6" :key="i" class="skeleton" style="height: 160px; border-radius: 16px;" />
    </div>

    <template v-else>
      <div v-for="category in CATEGORIES" :key="category.key" class="category-section">
        <div class="section-header">
          <span class="section-icon">{{ category.icon }}</span>
          <h2 class="section-title">{{ category.label }}</h2>
          <span class="section-count badge" :class="`badge-${category.key.toLowerCase()}`">
            {{ store.byCategory[category.key].length }}
          </span>
          <div class="section-metrics">
            <div class="metric-item">
              <span class="metric-label">Invested:</span>
              <span class="metric-value">{{ formatGBP(categoryInvested(category.key)) }}</span>
            </div>
            <div class="metric-divider">|</div>
            <div class="metric-item">
              <span class="metric-label">Current:</span>
              <span class="metric-value font-semibold">{{ formatGBP(categoryTotal(category.key)) }}</span>
            </div>
            <div v-if="categoryChange(category.key) !== null" class="change-badge" :class="categoryChange(category.key)! >= 0 ? 'change-up' : 'change-down'">
              {{ categoryChange(category.key)! >= 0 ? '▲' : '▼' }} {{ Math.abs(categoryChange(category.key)!).toFixed(1) }}%
            </div>
          </div>

        </div>

        <div v-if="store.byCategory[category.key].length" class="accounts-grid">
          <AccountCard
            v-for="account in store.byCategory[category.key]"
            :key="account.id"
            :account="account"
            @update-value="openEditValue"
            @edit="openEdit"
            @refresh-account="onRefreshAccount"
          />
        </div>
        <div v-else class="empty-category">
          <span class="text-sm text-muted">No {{ category.label.toLowerCase() }} accounts yet.</span>
          <button class="btn btn-ghost btn-sm" @click="preselectCategory = category.key; showAdd = true">+ Add one</button>
        </div>
      </div>
    </template>

    <!-- Edit Value Modal -->
    <EditValueModal
      v-model="showEditValue"
      :account="selectedAccount"
      @saved="onValueSaved"
    />

    <!-- Add / Edit Account Modal -->
    <AddAccountModal
      v-model="showAdd"
      :account="editingAccount"
      @saved="onAccountSaved"
      @delete="onDeleteAccount"
    />

    <ConfirmModal
      v-model="showDeleteConfirm"
      title="Delete Account"
      :message="`Delete &quot;${editingAccount?.name}&quot;? This cannot be undone.`"
      confirmText="Delete"
      @confirm="executeDeleteAccount"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useAuditStore } from '@/stores/audit'
import { useSharesStore } from '@/stores/shares'
import AccountCard from '@/components/accounts/AccountCard.vue'
import EditValueModal from '@/components/accounts/EditValueModal.vue'
import AddAccountModal from '@/components/accounts/AddAccountModal.vue'
import ConfirmModal from '@/components/layout/ConfirmModal.vue'
import { api, apiErrorMessage, type Account } from '@/api/client'
import { formatGBP } from '@/utils/format'
import { useToast } from '@/composables/useToast'
import { useRefetchOnFocus } from '@/composables/useRefetchOnFocus'

const store = useAccountsStore()
const auditStore = useAuditStore()
const sharesStore = useSharesStore()
const toast = useToast()

const CATEGORIES = [
  { key: 'INVESTMENTS', label: 'Investments', icon: '📈' },
  { key: 'RETIREMENT',  label: 'Retirement',  icon: '🏦' },
  { key: 'SAVINGS',     label: 'Savings',     icon: '💰' },
] as const

// Modals
const showEditValue = ref(false)
const selectedAccount = ref<Account | null>(null)
const showAdd = ref(false)
const editingAccount = ref<Account | null>(null)
const preselectCategory = ref('')
const showDeleteConfirm = ref(false)

function categoryTotal(cat: string) {
  return store.byCategory[cat as keyof typeof store.byCategory]
    .reduce((s, a) => s + a.current_value, 0)
}

function categoryInvested(cat: string) {
  return store.byCategory[cat as keyof typeof store.byCategory]
    .reduce((s, a) => s + (a.initial_investment !== null ? a.initial_investment : a.current_value), 0)
}

function categoryChange(cat: string) {
  const invested = categoryInvested(cat)
  const current = categoryTotal(cat)
  if (invested === 0) return null
  return ((current - invested) / invested) * 100
}

function openEditValue(account: Account) {
  selectedAccount.value = account
  showEditValue.value = true
}

function openEdit(account: Account) {
  editingAccount.value = account
  showAdd.value = true
}

async function onValueSaved(newValue: number, note?: string) {
  if (!selectedAccount.value) return
  try {
    const log = await store.updateValue(selectedAccount.value.id, newValue, note)
    auditStore.addLog(log)
    toast.success('Value updated')
  } catch (e) {
    toast.error(`Could not update value: ${apiErrorMessage(e)}`)
  }
}

async function onAccountSaved(form: any) {
  const editing = !!editingAccount.value
  try {
    await saveAccount(form)
    toast.success(editing ? 'Account updated' : 'Account created')
  } catch (e) {
    toast.error(`Could not save account: ${apiErrorMessage(e)}`)
  }
}

async function saveAccount(form: any) {
  if (editingAccount.value) {
    await store.updateMeta(editingAccount.value.id, {
      name: form.name,
      account_type: form.account_type,
      category: form.category,
      provider: form.provider,
      notes: form.notes,
    })
    editingAccount.value = null
  } else {
    await store.createAccount({
      name: form.name,
      account_type: form.account_type,
      category: preselectCategory.value || form.category,
      provider: form.provider,
      current_value: form.current_value ?? 0,
      initial_investment: form.initial_investment ?? undefined,
      notes: form.notes,
    })
    preselectCategory.value = ''
  }
}

function onDeleteAccount() {
  if (!editingAccount.value) return
  showDeleteConfirm.value = true
}

async function executeDeleteAccount() {
  if (!editingAccount.value) return
  try {
    await store.deleteAccount(editingAccount.value.id)
    toast.success('Account deleted')
    showAdd.value = false
    editingAccount.value = null
  } catch (e) {
    toast.error(`Could not delete account: ${apiErrorMessage(e)}`)
  }
}

async function onRefreshAccount(_accountId: number) {
  await store.fetchAll(true)
}

/** Fetch live prices only (display); account balances are NOT modified. */
async function handleRefreshPrices() {
  await sharesStore.refreshAll()
  focus.touch()
  if (sharesStore.error) toast.error(`Price refresh failed: ${sharesStore.error}`)
  else toast.success('Prices refreshed')
}

const syncingAll = ref(false)
const SYNC_CONCURRENCY = 3

/** Persist live share values into each share-holding account's balance via /shares/{id}/sync. */
async function handleSyncAll() {
  if (syncingAll.value) return
  syncingAll.value = true
  try {
    // Always reload so we know every account that holds shares.
    await sharesStore.refreshAll()
    const ids = Object.values(sharesStore.portfolios)
      .filter(p => p.holdings.length > 0)
      .map(p => p.account_id)
    if (!ids.length) {
      if (sharesStore.error) toast.error(`Could not load holdings: ${sharesStore.error}`)
      else toast.info('No share-holding accounts to sync')
      return
    }

    const failures: string[] = []
    let synced = 0
    const queue = [...ids]
    const nameOf = (id: number) => store.accounts.find(a => a.id === id)?.name ?? `Account ${id}`
    const worker = async () => {
      while (queue.length) {
        const id = queue.shift()!
        try {
          await api.shares.sync(id)
          synced++
        } catch (e) {
          failures.push(`${nameOf(id)}: ${apiErrorMessage(e)}`)
        }
      }
    }
    await Promise.all(Array.from({ length: Math.min(SYNC_CONCURRENCY, ids.length) }, worker))

    auditStore.invalidate()
    await Promise.all([store.fetchAll(true), sharesStore.refreshAll()])
    focus.touch()

    if (failures.length) {
      toast.error(`Synced ${synced} of ${ids.length}. Failed:\n${failures.join('\n')}`, 10000)
    } else {
      toast.success(`Synced ${synced} account${synced === 1 ? '' : 's'}`)
    }
  } finally {
    syncingAll.value = false
  }
}

// Re-fetch live prices + accounts when the tab regains focus (throttled).
const focus = useRefetchOnFocus(() => {
  sharesStore.refreshAll()
  store.fetchAll(true)
})

const now = ref(new Date())
let relativeTimer: any = null

onMounted(() => {
  store.fetchAll()
  relativeTimer = setInterval(() => {
    now.value = new Date()
  }, 10000)
})

onUnmounted(() => {
  if (relativeTimer) clearInterval(relativeTimer)
})

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

.add-account-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}

.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.category-section { margin-bottom: var(--space-10); }

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--bg-border);
}

.section-icon { font-size: 1.25rem; }

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.section-metrics {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
}

.metric-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
}

.metric-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  opacity: 0.8;
  margin-right: 4px;
}

.metric-value {
  color: var(--text-primary);
}

.metric-divider {
  color: var(--bg-border);
  user-select: none;
}

.change-badge {
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 2px;
}

.change-up {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.change-down {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.header-actions {
  display: flex;
  gap: var(--space-2);
  align-items: center;
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

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.empty-category {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px dashed var(--bg-border);
  border-radius: var(--radius-lg);
}
</style>
