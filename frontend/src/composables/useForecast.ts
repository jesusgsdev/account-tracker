import { ref, computed, watch, type Ref } from 'vue'
import type { DashboardSummary } from '@/api/client'
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
}

/** Persist a numeric ref to localStorage (skips empty values from half-typed inputs). */
function persistNumber(source: Ref<number>, key: string, skipFalsy = false) {
  watch(source, (val) => {
    if (skipFalsy ? val : (val !== undefined && val !== null)) localStorage.setItem(key, val.toString())
  })
}

/** Wealth projection state, persistence and derived figures. */
export function useForecast(summary: () => DashboardSummary) {
  const startYear = new Date().getFullYear()

  // Simulation inputs (read from localStorage with fallback defaults)
  const endYear = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.END_YEAR) || '2050'))
  const includeOther = ref<boolean>(localStorage.getItem(STORAGE_KEYS.INCLUDE_OTHER) !== 'false')
  const returnRateInvestments = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.INV_RETURN) || '7.0'))
  const contribInvestments = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.INV_CONTRIB) || '500'))
  const returnRateRetirement = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.RET_RETURN) || '6.0'))
  const contribRetirement = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.RET_CONTRIB) || '300'))
  const inflationRate = ref<number>(Number(localStorage.getItem(STORAGE_KEYS.INFLATION_RATE) || '2.5'))
  const adjustInflation = ref<boolean>(localStorage.getItem(STORAGE_KEYS.ADJUST_INFLATION) === 'true')

  persistNumber(endYear, STORAGE_KEYS.END_YEAR, true)
  persistNumber(returnRateInvestments, STORAGE_KEYS.INV_RETURN)
  persistNumber(contribInvestments, STORAGE_KEYS.INV_CONTRIB)
  persistNumber(returnRateRetirement, STORAGE_KEYS.RET_RETURN)
  persistNumber(contribRetirement, STORAGE_KEYS.RET_CONTRIB)
  persistNumber(inflationRate, STORAGE_KEYS.INFLATION_RATE)
  watch(includeOther, (val) => { localStorage.setItem(STORAGE_KEYS.INCLUDE_OTHER, val.toString()) })
  watch(adjustInflation, (val) => { localStorage.setItem(STORAGE_KEYS.ADJUST_INFLATION, val.toString()) })

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
    chartData,
  }
}
