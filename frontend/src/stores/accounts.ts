import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, apiErrorMessage, type Account } from '@/api/client'
import { useAuditStore } from '@/stores/audit'

/** Skip refetching if data is younger than this (ms) unless forced. */
const STALE_MS = 30_000

export const useAccountsStore = defineStore('accounts', () => {
  const accounts = ref<Account[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastFetched = ref<number | null>(null)
  let inflight: Promise<void> | null = null

  // Grouped by category
  const byCategory = computed(() => ({
    INVESTMENTS: accounts.value.filter(a => a.category === 'INVESTMENTS'),
    RETIREMENT:  accounts.value.filter(a => a.category === 'RETIREMENT'),
    SAVINGS:     accounts.value.filter(a => a.category === 'SAVINGS'),
  }))

  const totalValue = computed(() =>
    accounts.value.reduce((sum, a) => sum + a.current_value, 0)
  )

  function isFresh() {
    return lastFetched.value !== null && Date.now() - lastFetched.value < STALE_MS
  }

  function invalidate() { lastFetched.value = null }

  /** Fetch accounts; skipped when data is fresh (<30s) unless `force`. */
  async function fetchAll(force = false) {
    if (!force && isFresh()) return
    if (inflight) return inflight
    loading.value = true
    error.value = null
    inflight = (async () => {
      try {
        accounts.value = await api.accounts.list()
        lastFetched.value = Date.now()
      } catch (e) {
        error.value = apiErrorMessage(e)
      } finally {
        loading.value = false
        inflight = null
      }
    })()
    return inflight
  }

  async function createAccount(payload: Parameters<typeof api.accounts.create>[0]) {
    const account = await api.accounts.create(payload)
    accounts.value.push(account)
    useAuditStore().invalidate()
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
    useAuditStore().invalidate()
  }

  return { accounts, loading, error, lastFetched, invalidate, byCategory, totalValue, fetchAll, createAccount, updateValue, updateMeta, deleteAccount }
})
