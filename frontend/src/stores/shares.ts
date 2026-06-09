/**
 * Pinia store for share holdings live data.
 *
 * Holds one PortfolioLive per account_id.  The global "Refresh All" button
 * in AccountsView calls refreshAll(), which hits /api/shares/all-live — a
 * single backend call that batches all tickers in one yf.download() request.
 * Individual panels can still call refreshAccount(id) if needed.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, type PortfolioLive } from '@/api/client'

export const useSharesStore = defineStore('shares', () => {
  // Map of accountId → PortfolioLive
  const portfolios = ref<Record<number, PortfolioLive>>({})
  const loading    = ref(false)
  const error      = ref<string | null>(null)
  const lastRefreshedAt = ref<Date | null>(null)

  const hasAnyHoldings = computed(() => Object.keys(portfolios.value).length > 0)

  /** Refresh all investment accounts at once — ONE backend call. */
  async function refreshAll() {
    loading.value = true
    error.value   = null
    try {
      const results = await api.shares.allLive()
      const map: Record<number, PortfolioLive> = {}
      let maxRefreshed: Date | null = null
      for (const p of results) {
        map[p.account_id] = p
        if (p.last_refreshed) {
          const d = new Date(p.last_refreshed)
          if (!maxRefreshed || d > maxRefreshed) {
            maxRefreshed = d
          }
        }
      }
      portfolios.value   = map
      if (maxRefreshed) {
        lastRefreshedAt.value = maxRefreshed
      }
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  /** Refresh a single account (called by individual panel Refresh button). */
  async function refreshAccount(accountId: number) {
    try {
      const result = await api.shares.live(accountId)
      portfolios.value = { ...portfolios.value, [accountId]: result }
      if (result.last_refreshed) {
        lastRefreshedAt.value = new Date(result.last_refreshed)
      }
    } catch (e: any) {
      error.value = e.message
    }
  }

  /** Called when an account's holdings list changes (add / delete). */
  function invalidateAccount(accountId: number) {
    const updated = { ...portfolios.value }
    delete updated[accountId]
    portfolios.value = updated
  }

  return {
    portfolios,
    loading,
    error,
    lastRefreshedAt,
    hasAnyHoldings,
    refreshAll,
    refreshAccount,
    invalidateAccount,
  }
})
