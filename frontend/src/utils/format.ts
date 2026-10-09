/** Shared number/currency formatting (en-GB). Intl.NumberFormat instances are cached. */

export interface FormatGBPOptions {
  /** Fraction digits (min = max). Default 2. */
  decimals?: number
  /** Compact notation, e.g. £1.2M. Overrides decimals (max 1 dp). */
  compact?: boolean
  /** Prefix positive values with '+'. */
  sign?: boolean
  /** Omit the £ symbol. */
  noSymbol?: boolean
}

const cache = new Map<string, Intl.NumberFormat>()

function getFormatter(decimals: number, compact: boolean): Intl.NumberFormat {
  const key = `${decimals}|${compact}`
  let f = cache.get(key)
  if (!f) {
    f = compact
      ? new Intl.NumberFormat('en-GB', { notation: 'compact', maximumFractionDigits: 1 })
      : new Intl.NumberFormat('en-GB', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
    cache.set(key, f)
  }
  return f
}

/** Format a number as GBP, e.g. £1,234.56 / -£1,234 / +£12.00. Nullish -> '—'. */
export function formatGBP(value: number | null | undefined, opts: FormatGBPOptions = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  const { decimals = 2, compact = false, sign = false, noSymbol = false } = opts
  const body = getFormatter(decimals, compact).format(Math.abs(value))
  const isNeg = value < 0 && Number(body.replace(/[^0-9.]/g, '')) !== 0
  const prefix = isNeg ? '-' : sign && value > 0 ? '+' : ''
  return `${prefix}${noSymbol ? '' : '£'}${body}`
}
