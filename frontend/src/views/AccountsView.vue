<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Accounts</h1>
        <p class="text-sm text-muted">{{ store.accounts.length }} account{{ store.accounts.length !== 1 ? 's' : '' }} tracked</p>
      </div>
      <button class="btn btn-primary" @click="showAdd = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Add Account
      </button>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAccountsStore } from '@/stores/accounts'
import { useAuditStore } from '@/stores/audit'
import AccountCard from '@/components/accounts/AccountCard.vue'
import EditValueModal from '@/components/accounts/EditValueModal.vue'
import AddAccountModal from '@/components/accounts/AddAccountModal.vue'
import type { Account } from '@/api/client'

const store = useAccountsStore()
const auditStore = useAuditStore()

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

async function onDeleteAccount() {
  if (!editingAccount.value) return
  if (confirm(`Delete "${editingAccount.value.name}"? This cannot be undone.`)) {
    await store.deleteAccount(editingAccount.value.id)
    showAdd.value = false
    editingAccount.value = null
  }
}

onMounted(() => store.fetchAll())
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
