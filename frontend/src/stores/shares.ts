/**
 * Pinia store for share holdings live data.
 *
 * Holds one PortfolioLive per account_id.  The global "Refresh All" button
 * in AccountsView calls refreshAll() (force by default; pass false to honour the staleness window), which hits /api/shares/all-live — a
 * single backend call that batches all tickers in one yf.download() request.
 * Individual panels can still call refreshAccount(id) if needed.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, apiErrorMessage, type PortfolioLive } from '@/api/client'

/** refreshAll(false) skips if data is younger than this (ms). */
const STALE_MS = 30_000
/** ensureFresh() only pulls live prices when the stored ones are older than this (ms). */
const LIVE_MAX_AGE_MS = 24 * 60 * 60 * 1000

export const useSharesStore = defineStore('shares', () => {
  // Map of accountId → PortfolioLive
  const portfolios = ref<Record<number, PortfolioLive>>({})
  const loading    = ref(false)
  const error      = ref<string | null>(null)
  const lastRefreshedAt = ref<Date | null>(null)
  /** Local timestamp (ms) of the last successful refreshAll. */
  const lastFetched = ref<number | null>(null)
  let inflight: Promise<void> | null = null
  /** Last share-sync failure message (cleared on next successful sync). */
  const syncError   = ref<string | null>(null)

  const hasAnyHoldings = computed(() => Object.keys(portfolios.value).length > 0)

  /** Refresh all investment accounts at once — ONE backend call. */
  async function refreshAll(force = true, live = true) {
    if (!force && lastFetched.value !== null && Date.now() - lastFetched.value < STALE_MS) return
    if (inflight) return inflight
    loading.value = true
    error.value   = null
    inflight = (async () => {
    try {
      const results = await api.shares.allLive(live)
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
      if (live) lastFetched.value = Date.now()
    } catch (e) {
      error.value = apiErrorMessage(e)
    } finally {
      loading.value = false
      inflight = null
    }
    })()
    return inflight
  }

  /** Age (ms) of the oldest-known newest price across all holdings, or null if nothing was ever priced. */
  function priceAgeMs(): number | null {
    let newest = 0
    for (const p of Object.values(portfolios.value))
      for (const h of p.holdings)
        if (h.last_price_at) newest = Math.max(newest, new Date(h.last_price_at).getTime())
    return newest ? Date.now() - newest : null
  }

  /**
   * Show stored prices immediately, and only hit the live price source when the
   * stored ones are 24h+ old (or missing). Manual refresh always forces a live pull.
   */
  async function ensureFresh() {
    if (!hasAnyHoldings.value) await refreshAll(true, false)
    const age = priceAgeMs()
    if (age === null || age > LIVE_MAX_AGE_MS) await refreshAll(true, true)
  }

  /** Refresh a single account (called by individual panel Refresh button). */
  async function refreshAccount(accountId: number) {
    try {
      const result = await api.shares.live(accountId)
      portfolios.value = { ...portfolios.value, [accountId]: result }
      if (result.last_refreshed) {
        lastRefreshedAt.value = new Date(result.last_refreshed)
      }
    } catch (e) {
      error.value = apiErrorMessage(e)
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
    lastFetched,
    hasAnyHoldings,
    syncError,
    refreshAll,
    ensureFresh,
    refreshAccount,
    invalidateAccount,
  }
})
