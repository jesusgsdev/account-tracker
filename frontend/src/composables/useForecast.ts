import { ref, computed } from 'vue'
import { api, apiErrorMessage, type DashboardSummary, type ForecastSettings } from '@/api/client'
import { formatGBP } from '@/utils/format'

const STORAGE_KEYS = {
  END_YEAR: 'forecast_end_year',
  INCLUDE_OTHER: 'forecast_include_other',
  INV_RETURN: 'forecast_inv_return',
  INV_CONTRIB: 'forecast_inv_contrib',
  RET_RETURN: 'forecast_ret_return',
  RET_CONTRIB: 'forecast_ret_contrib',
  INFLATION_RATE: 'forecast_inflation_rate',
  ADJUST_INFLATION: 'forecast_adjust_inflation',
  BIRTH_YEAR: 'forecast_birth_year',
  WITHDRAWAL_RATE: 'forecast_withdrawal_rate',
}

/** UK State Pension age assumed by the forecast. */
export const STATE_PENSION_AGE = 68
/** Full new State Pension for 2025/26: £230.25/week × 52. Inflated from this tax year. */
export const STATE_PENSION_2025_26 = 11_973
const STATE_PENSION_BASE_YEAR = 2025

/** Wealth projection state, persistence and derived figures. */
export function useForecast(summary: () => DashboardSummary) {
  const startYear = new Date().getFullYear()

  // Simulation inputs. Defaults here; the server copy is applied by load(). Values a
  // previous version kept in this browser's localStorage seed the defaults and are
  // migrated to the server once if nothing is saved there yet.
  const hadLegacyLocal = localStorage.getItem(STORAGE_KEYS.END_YEAR) !== null
  const endYear = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.END_YEAR) || '2050'))
  const includeOther = ref<boolean>(localStorage.getItem(STORAGE_KEYS.INCLUDE_OTHER) !== 'false')
  const returnRateInvestments = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.INV_RETURN) || '7.0'))
  const contribInvestments = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.INV_CONTRIB) || '500'))
  const returnRateRetirement = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.RET_RETURN) || '6.0'))
  const contribRetirement = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.RET_CONTRIB) || '300'))
  const inflationRate = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.INFLATION_RATE) || '2.5'))
  const adjustInflation = ref<boolean>(localStorage.getItem(STORAGE_KEYS.ADJUST_INFLATION) === 'true')

  // Retirement income inputs. The State Pension is the 2025/26 full amount, grown
  // with the forecast's annual inflation rate.
  const birthYear = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.BIRTH_YEAR) || '1989'))
  const withdrawalRate = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.WITHDRAWAL_RATE) || '4'))
  // Edits are a draft: nothing is stored until save() is called,
  // so you can experiment freely and discard() back to the last saved values.
  type Draft = {
    endYear: number; includeOther: boolean; returnRateInvestments: number; contribInvestments: number
    returnRateRetirement: number; contribRetirement: number; inflationRate: number
    adjustInflation: boolean; birthYear: number; withdrawalRate: number
  }
  const readDraft = (): Draft => ({
    endYear: endYear.value, includeOther: includeOther.value,
    returnRateInvestments: returnRateInvestments.value, contribInvestments: contribInvestments.value,
    returnRateRetirement: returnRateRetirement.value, contribRetirement: contribRetirement.value,
    inflationRate: inflationRate.value, adjustInflation: adjustInflation.value,
    birthYear: birthYear.value, withdrawalRate: withdrawalRate.value,
  })
  const saved = ref<Draft>(readDraft())
  const isDirty = computed(() => JSON.stringify(readDraft()) !== JSON.stringify(saved.value))

  const loaded = ref(false)
  const saving = ref(false)

  const toSettings = (d: Draft): ForecastSettings => ({
    end_year: d.endYear, include_other: d.includeOther,
    return_rate_investments: d.returnRateInvestments, contrib_investments: d.contribInvestments,
    return_rate_retirement: d.returnRateRetirement, contrib_retirement: d.contribRetirement,
    inflation_rate: d.inflationRate, adjust_inflation: d.adjustInflation,
    birth_year: d.birthYear, withdrawal_rate: d.withdrawalRate,
  })

  function apply(d: Draft) {
    endYear.value = d.endYear; includeOther.value = d.includeOther
    returnRateInvestments.value = d.returnRateInvestments; contribInvestments.value = d.contribInvestments
    returnRateRetirement.value = d.returnRateRetirement; contribRetirement.value = d.contribRetirement
    inflationRate.value = d.inflationRate; adjustInflation.value = d.adjustInflation
    birthYear.value = d.birthYear; withdrawalRate.value = d.withdrawalRate
  }

  /** Load the saved settings from the server (shared across devices). */
  async function load() {
    try {
      const r = await api.settings.getForecast()
      if (r) {
        const d: Draft = {
          endYear: r.end_year, includeOther: r.include_other,
          returnRateInvestments: r.return_rate_investments, contribInvestments: r.contrib_investments,
          returnRateRetirement: r.return_rate_retirement, contribRetirement: r.contrib_retirement,
          inflationRate: r.inflation_rate, adjustInflation: r.adjust_inflation,
          birthYear: r.birth_year, withdrawalRate: r.withdrawal_rate,
        }
        apply(d)
        saved.value = d
      } else if (hadLegacyLocal) {
        // One-off migration of settings previously kept only in this browser.
        await api.settings.saveForecast(toSettings(readDraft())).catch(() => {})
        saved.value = readDraft()
      }
      loaded.value = true
    } catch (e) {
      loadError.value = apiErrorMessage(e)
    }
  }
  const loadError = ref<string | null>(null)

  /** Save to the server. Returns an error message, or null on success. */
  async function save(): Promise<string | null> {
    const d = readDraft()
    // Half-typed inputs can be empty/NaN; refuse to persist those.
    if (Object.values(d).some(v => typeof v !== 'boolean' && (v === ('' as unknown) || !Number.isFinite(Number(v))))
        || !d.endYear || !d.birthYear) return 'Some inputs are empty or invalid, so nothing was saved'
    saving.value = true
    try {
      await api.settings.saveForecast(toSettings(d))
      saved.value = d
      return null
    } catch (e) {
      return apiErrorMessage(e)
    } finally {
      saving.value = false
    }
  }

  function discard() { apply(saved.value) }

  // Starting points from category totals
  const categoryTotal = (cat: string) => summary().categories.find(c => c.category === cat)?.total_value ?? 0
  const startInvestments = computed(() => categoryTotal('INVESTMENTS'))
  const startRetirement = computed(() => categoryTotal('RETIREMENT'))
  const startSavings = computed(() => categoryTotal('SAVINGS'))
  const startPropertyEquity = computed(() => summary().mortgage_equity ?? 0)
  const otherAssetsValue = computed(() => startSavings.value + startPropertyEquity.value)
  const otherAssetsFormatted = computed(() => formatGBP(otherAssetsValue.value, { decimals: 0, noSymbol: true }))

  // Monthly simulation (nominal values & discount factor tracking)
  const projectionData = computed(() => {
    const points: {
      year: number
      investments: number
      retirement: number
      other: number
      total: number
      discount: number
    }[] = []

    const startInv = startInvestments.value
    const startRet = startRetirement.value
    const otherVal = includeOther.value ? otherAssetsValue.value : 0

    points.push({
      year: startYear,
      investments: startInv,
      retirement: startRet,
      other: otherVal,
      total: startInv + startRet + otherVal,
      discount: 1,
    })

    let currentInv = startInv
    let currentRet = startRet

    // Handle inputs gracefully during manual text modification
    const rInv = (returnRateInvestments.value || 0) / 100
    const rRet = (returnRateRetirement.value || 0) / 100
    const cInv = contribInvestments.value || 0
    const cRet = contribRetirement.value || 0
    const targetYear = endYear.value || (startYear + 1)
    const infRate = (inflationRate.value || 0) / 100

    for (let year = startYear + 1; year <= targetYear; year++) {
      const t = year - startYear
      const discount = Math.pow(1 + infRate, -t)

      for (let m = 0; m < 12; m++) {
        currentInv = currentInv * (1 + rInv / 12) + cInv
        currentRet = currentRet * (1 + rRet / 12) + cRet
      }
      points.push({
        year,
        investments: currentInv,
        retirement: currentRet,
        other: otherVal,
        total: currentInv + currentRet + otherVal,
        discount,
      })
    }

    return points
  })

  // Apply inflation adjustment discount if requested
  const adjustedProjectionData = computed(() => {
    const applyInflation = adjustInflation.value
    return projectionData.value.map(d => {
      const factor = applyInflation ? d.discount : 1
      return {
        year: d.year,
        investments: d.investments * factor,
        retirement: d.retirement * factor,
        other: d.other * factor,
        total: d.total * factor,
      }
    })
  })

  const finalPoint = computed(() => adjustedProjectionData.value[adjustedProjectionData.value.length - 1])
  const finalNetWorthFormatted = computed(() =>
    formatGBP(finalPoint.value?.total ?? 0, { decimals: 0, noSymbol: true }))

  const yearsCount = computed(() => {
    const targetYear = endYear.value || (startYear + 1)
    return Math.max(1, targetYear - startYear)
  })

  // Total contributions, potentially inflation discounted
  const totalContributions = computed(() => {
    const cInv = contribInvestments.value || 0
    const cRet = contribRetirement.value || 0
    const annualContrib = (cInv + cRet) * 12

    if (!adjustInflation.value) return annualContrib * yearsCount.value

    let total = 0
    const infRate = (inflationRate.value || 0) / 100
    for (let t = 1; t <= yearsCount.value; t++) {
      total += annualContrib * Math.pow(1 + infRate, -t)
    }
    return total
  })
  const totalContributionsFormatted = computed(() =>
    formatGBP(totalContributions.value, { decimals: 0, noSymbol: true }))

  const compoundGains = computed(() => {
    const endingTotal = finalPoint.value?.total ?? 0
    const startingTotal = startInvestments.value + startRetirement.value + (includeOther.value ? otherAssetsValue.value : 0)
    // Gains = Ending adjusted total - Starting total - Adjusted contributions
    return Math.max(0, endingTotal - startingTotal - totalContributions.value)
  })
  const compoundGainsFormatted = computed(() =>
    formatGBP(compoundGains.value, { decimals: 0, noSymbol: true }))

  // ── Retirement income at the forecast end year (gross, before tax) ─────────
  const statePensionStartYear = computed(() => (birthYear.value || 0) + STATE_PENSION_AGE)

  const incomeAtEnd = computed(() => {
    const targetYear = endYear.value || (startYear + 1)
    const infRate = (inflationRate.value || 0) / 100
    // 2025/26 amount inflated to the end year (nominal) or to today (today's £).
    const pensionYear = adjustInflation.value ? startYear : targetYear
    const pensionActive = targetYear >= statePensionStartYear.value
    const pension = pensionActive
      ? STATE_PENSION_2025_26 * Math.pow(1 + infRate, pensionYear - STATE_PENSION_BASE_YEAR)
      : 0
    const pots = (finalPoint.value?.investments ?? 0) + (finalPoint.value?.retirement ?? 0)
    const drawdown = pots * ((withdrawalRate.value || 0) / 100)
    const annual = pension + drawdown
    return { pensionActive, pension, drawdown, annual, monthly: annual / 12 }
  })
  const fmt0 = (v: number) => formatGBP(v, { decimals: 0, noSymbol: true })
  const income = computed(() => ({
    pensionActive: incomeAtEnd.value.pensionActive,
    pension: fmt0(incomeAtEnd.value.pension),
    drawdown: fmt0(incomeAtEnd.value.drawdown),
    annual: fmt0(incomeAtEnd.value.annual),
    monthly: fmt0(incomeAtEnd.value.monthly),
  }))

  // Chart.js data
  const chartData = computed(() => {
    const data = adjustedProjectionData.value
    return {
      labels: data.map(d => d.year.toString()),
      datasets: [
        {
          label: 'Total Net Worth',
          data: data.map(d => d.total),
          borderColor: '#c084fc',
          backgroundColor: 'rgba(192, 132, 252, 0.05)',
          borderWidth: 3,
          pointRadius: data.length > 30 ? 0 : 3,
          pointHoverRadius: 6,
          fill: true,
          tension: 0.25,
        },
        {
          label: 'Investments',
          data: data.map(d => d.investments),
          borderColor: '#818cf8',
          borderWidth: 2.5,
          pointRadius: data.length > 30 ? 0 : 2,
          pointHoverRadius: 5,
          fill: false,
          tension: 0.25,
        },
        {
          label: 'Retirement',
          data: data.map(d => d.retirement),
          borderColor: '#fb923c',
          borderWidth: 2.5,
          pointRadius: data.length > 30 ? 0 : 2,
          pointHoverRadius: 5,
          fill: false,
          tension: 0.25,
        },
      ],
    }
  })

  return {
    startYear, endYear, includeOther, returnRateInvestments, contribInvestments,
    returnRateRetirement, contribRetirement, inflationRate, adjustInflation,
    startInvestments, startRetirement, otherAssetsFormatted,
    finalNetWorthFormatted, totalContributionsFormatted, compoundGainsFormatted,
    birthYear, withdrawalRate, statePensionStartYear, income,
    isDirty, save, discard, load, loaded, saving, loadError,
    chartData,
  }
}
