/**
 * UK (England / Wales / NI) income tax for a retired taxpayer, 2025/26 rules.
 * No National Insurance applies to pension or investment income past State Pension age.
 * Thresholds are scaled by `scale` to model inflation-linked thresholds.
 */
export const TAX_BASE_YEAR = 2025

const PERSONAL_ALLOWANCE = 12_570
const BASIC_BAND = 37_700            // taxable income taxed at 20%
const ADDITIONAL_THRESHOLD = 125_140 // taxable income above this is taxed at 45%
const TAPER_START = 100_000          // allowance falls £1 per £2 above this

/** Income tax on `taxableIncome` (income that counts toward tax; tax-free amounts excluded). */
export function incomeTax(taxableIncome: number, scale = 1): number {
  const income = Math.max(0, taxableIncome)
  const taperStart = TAPER_START * scale
  const allowance = Math.max(0, PERSONAL_ALLOWANCE * scale - Math.max(0, income - taperStart) / 2)
  const taxable = Math.max(0, income - allowance)

  const basicLimit = BASIC_BAND * scale
  const addLimit = ADDITIONAL_THRESHOLD * scale
  const basic = Math.min(taxable, basicLimit)
  const higher = Math.min(Math.max(taxable - basicLimit, 0), addLimit - basicLimit)
  const additional = Math.max(taxable - addLimit, 0)
  return basic * 0.2 + higher * 0.4 + additional * 0.45
}
