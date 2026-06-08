import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type Account } from '@/api/client'

export const useAccountsStore = defineStore('accounts', () => {
  const accounts = ref<Account[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Grouped by category
  const byCategory = computed(() => ({
    INVESTMENTS: accounts.value.filter(a => a.category === 'INVESTMENTS'),
    RETIREMENT:  accounts.value.filter(a => a.category === 'RETIREMENT'),
    SAVINGS:     accounts.value.filter(a => a.category === 'SAVINGS'),
  }))

  const totalValue = computed(() =>
    accounts.value.reduce((sum, a) => sum + a.current_value, 0)
  )

  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      accounts.value = await api.accounts.list()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createAccount(payload: Parameters<typeof api.accounts.create>[0]) {
    const account = await api.accounts.create(payload)
    accounts.value.push(account)
    return account
  }

  async function updateValue(id: number, newValue: number, note?: string) {
    const log = await api.accounts.updateValue(id, newValue, note)
    const idx = accounts.value.findIndex(a => a.id === id)
    if (idx !== -1) {
      accounts.value[idx] = { ...accounts.value[idx], current_value: newValue, updated_at: log.recorded_at }
    }
    return log
  }

  async function updateMeta(id: number, payload: Parameters<typeof api.accounts.updateMeta>[1]) {
    const updated = await api.accounts.updateMeta(id, payload)
    const idx = accounts.value.findIndex(a => a.id === id)
    if (idx !== -1) accounts.value[idx] = updated
    return updated
  }

  async function deleteAccount(id: number) {
    await api.accounts.delete(id)
    accounts.value = accounts.value.filter(a => a.id !== id)
  }

  return { accounts, loading, error, byCategory, totalValue, fetchAll, createAccount, updateValue, updateMeta, deleteAccount }
})
