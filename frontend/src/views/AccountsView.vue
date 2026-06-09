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
        <button class="btn btn-sm btn-primary add-account-btn" @click="showAdd = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Add Account
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="loading-grid">
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
          <span class="section-total">
            £{{ categoryTotal(category.key).toLocaleString('en-GB', { minimumFractionDigits: 2 }) }}
          </span>

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
import type { Account } from '@/api/client'

const store = useAccountsStore()
const auditStore = useAuditStore()
const sharesStore = useSharesStore()

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
  const log = await store.updateValue(selectedAccount.value.id, newValue, note)
  auditStore.addLog(log)
}

async function onAccountSaved(form: any) {
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
  await store.deleteAccount(editingAccount.value.id)
  showAdd.value = false
  editingAccount.value = null
}

async function onRefreshAccount(accountId: number) {
  await store.fetchAll()
}

async function handleRefreshAll() {
  await sharesStore.refreshAll()
  await store.fetchAll()
}

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

.section-total {
  margin-left: auto;
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-secondary);
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
