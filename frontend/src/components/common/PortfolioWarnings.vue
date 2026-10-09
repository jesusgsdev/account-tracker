<template>
  <div v-if="warnings.length" class="portfolio-warnings">
    <WarningBanner v-for="w in warnings" :key="w.key" :level="w.level" :title="w.title">{{ w.text }}</WarningBanner>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioLive } from '@/api/client'
import { timeAgo } from '@/utils/date'
import WarningBanner from '@/components/common/WarningBanner.vue'

const props = defineProps<{
  portfolios: PortfolioLive[]
  syncError?: string | null
  /** Optional ticker label prefix, e.g. when several accounts are combined */
  now?: Date
}>()

const warnings = computed(() => {
  const out: { key: string; level: 'warn' | 'error'; title?: string; text: string }[] = []
  const ps = props.portfolios
  if (props.syncError) {
    out.push({ key: 'sync', level: 'error', title: 'Sync failed', text: props.syncError })
  }
  if (ps.some(p => p.gbpusd_rate_is_fallback)) {
    out.push({ key: 'fallback', level: 'warn', text: 'GBP/USD is a built-in fallback rate — USD values may be inaccurate.' })
  } else if (ps.some(p => p.gbpusd_rate_stale)) {
    out.push({ key: 'fxstale', level: 'warn', text: 'The GBP/USD rate is stale — USD values may be slightly out of date.' })
  }
  const stale = ps.flatMap(p => p.holdings).filter(h => h.is_stale)
  if (stale.length) {
    const list = stale.map(h => `${h.ticker} (${timeAgo(h.last_price_at, props.now)})`).join(', ')
    out.push({ key: 'stale', level: 'warn', title: 'Stale prices', text: `Using last known price for: ${list}.` })
  }
  const unpriced = new Set<string>()
  for (const p of ps) {
    ;(p.unpriced_tickers ?? []).forEach(t => unpriced.add(t))
    p.holdings.filter(h => h.live_value_gbp == null).forEach(h => unpriced.add(h.ticker))
  }
  if (unpriced.size) {
    out.push({ key: 'unpriced', level: 'warn', title: 'Excluded from totals', text: `No price or FX rate available for: ${[...unpriced].join(', ')}. These holdings are excluded from totals.` })
  }
  return out
})
</script>
