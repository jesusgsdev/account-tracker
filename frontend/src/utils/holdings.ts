import { formatGBP } from '@/utils/format'

/** GBP amount without the £ symbol. */
export function fmtGbp(v: number | null | undefined): string {
  return formatGBP(v, { noSymbol: true })
}

/** Price in its native currency (GBX is shown in pounds). */
export function fmtNative(price: number | undefined | null, currency: string | null | undefined): string {
  if (price == null) return '—'
  const divisor = currency === 'GBX' ? 100 : 1
  return formatGBP(price / divisor, { noSymbol: true })
}

/** Format a naive-UTC ISO string as a short en-GB date/time. */
export function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return ''
  return new Date(iso + (iso.endsWith('Z') ? '' : 'Z')).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

/** CSS class used to colour a ticker badge/chip by currency. */
export function currencyClass(currency: string | null | undefined): string {
  if (!currency) return ''
  if (currency === 'USD') return 'ticker-usd'
  if (currency === 'GBP' || currency === 'GBX') return 'ticker-gbp'
  return 'ticker-other'
}

/** "14:02:11 (3m ago)" style label for a last-refreshed timestamp. */
export function formatRefreshedLabel(d: Date | null | undefined, now: Date): string {
  if (!d) return ''
  const diffMins = Math.floor((now.getTime() - d.getTime()) / 60000)
  const timeStr = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  return diffMins < 1 ? `${timeStr} (just now)` : `${timeStr} (${diffMins}m ago)`
}
