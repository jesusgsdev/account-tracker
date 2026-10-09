import { ref, computed } from 'vue'
import type { LiveHolding } from '@/api/client'
import { useAccountsStore } from '@/stores/accounts'
import { useSharesStore } from '@/stores/shares'

export type CategoryFilter = 'ALL' | 'INVESTMENTS' | 'RETIREMENT'

export type MarketHolding = LiveHolding & {
  accountName: string
  accountCategory: string
  accountProvider: string | null
}

/** Flat, filterable list of holdings across all accounts, plus portfolio totals. */
export function useMarketHoldings() {
  const accountsStore = useAccountsStore()
  const sharesStore = useSharesStore()

  const searchQuery = ref('')
  const activeCategory = ref<CategoryFilter>('ALL')

  // Flat list of all holdings linked to their account metadata
  const allHoldings = computed<MarketHolding[]>(() => {
    const list: MarketHolding[] = []
    for (const accountId in sharesStore.portfolios) {
      const portfolio = sharesStore.portfolios[accountId]
      const account = accountsStore.accounts.find(a => a.id === Number(accountId))
      if (!account) continue

      for (const h of portfolio.holdings) {
        list.push({
          ...h,
          accountName: account.name,
          accountCategory: account.category,
          accountProvider: account.provider,
        })
      }
    }
    return list
  })

  const filteredHoldings = computed(() => {
    return allHoldings.value.filter(h => {
      if (activeCategory.value !== 'ALL' && h.accountCategory !== activeCategory.value) {
        return false
      }
      if (searchQuery.value) {
        const q = searchQuery.value.toLowerCase()
        const matchesTicker = h.ticker.toLowerCase().includes(q)
        const matchesName = (h.short_name || h.display_name || '').toLowerCase().includes(q)
        const matchesAccount = h.accountName.toLowerCase().includes(q)
        const matchesProvider = (h.accountProvider || '').toLowerCase().includes(q)
        return matchesTicker || matchesName || matchesAccount || matchesProvider
      }
      return true
    })
  })

  const totals = computed(() => {
    let totalValue = 0
    let totalCost = 0

    for (const h of filteredHoldings.value) {
      if (h.live_value_gbp != null) {
        totalValue += h.live_value_gbp
      }
      // Cost basis in GBP
      if (h.quantity && h.avg_cost != null) {
        const valueNative = h.quantity * h.avg_cost
        // Fallback rate if gbpusd_rate is not returned
        const rate = sharesStore.portfolios[h.account_id]?.gbpusd_rate || 1.30
        let valueGbp = 0
        if (h.currency === 'GBP') {
          valueGbp = valueNative
        } else if (h.currency === 'GBX') {
          valueGbp = valueNative / 100
        } else if (h.currency === 'USD') {
          valueGbp = valueNative / rate
        } else {
          // Other currencies: no exchange rate available, use the native value directly
          valueGbp = valueNative
        }
        totalCost += valueGbp
      }
    }

    const pnl = totalValue - totalCost
    const pnlPercent = totalCost > 0 ? (pnl / totalCost) * 100 : 0

    return {
      value: totalValue,
      cost: totalCost,
      pnl,
      pnlPercent,
      activeHoldings: filteredHoldings.value.length,
    }
  })

  return { searchQuery, activeCategory, allHoldings, filteredHoldings, totals }
}

export type MarketTotals = ReturnType<typeof useMarketHoldings>['totals']['value']
