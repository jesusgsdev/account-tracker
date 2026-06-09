<template>
  <div class="forecast-card card">
    <div class="forecast-header">
      <div>
        <h2 class="forecast-title">Wealth Projection Forecast</h2>
        <p class="text-sm text-muted">Simulate compound growth and savings contributions over time</p>
      </div>
      
      <div class="header-controls">
        <!-- Inflation Adjustment Slide-Toggle -->
        <div class="toggle-slider-wrap">
          <span class="toggle-mode-label text-xs" :class="{ active: !adjustInflation }">Future £ (Nominal)</span>
          <label class="switch">
            <input type="checkbox" v-model="adjustInflation" />
            <span class="slider round"></span>
          </label>
          <span class="toggle-mode-label text-xs" :class="{ active: adjustInflation }">Today's £ (Adjusted)</span>
        </div>

        <div class="include-toggle">
          <label class="toggle-label text-xs font-semibold">
            <input type="checkbox" v-model="includeOther" />
            Include Savings & Property Equity (£{{ otherAssetsFormatted }})
          </label>
        </div>
      </div>
    </div>

    <div class="forecast-layout">
      <!-- Left: Simulation Controls -->
      <div class="controls-panel">
        <div class="control-group">
          <div class="control-label">
            <span class="text-sm font-semibold">Forecast End Year</span>
            <div class="manual-input-wrap year-badge">
              <input
                type="number"
                v-model.number="endYear"
                :min="startYear + 1"
                max="2100"
                class="manual-input"
              />
            </div>
          </div>
          <input
            type="range"
            v-model.number="endYear"
            :min="startYear + 1"
            :max="2080"
            step="1"
            class="slider-input"
          />
          <div class="slider-ticks text-xs text-muted">
            <span>{{ startYear + 1 }}</span>
            <span>2040</span>
            <span>2050</span>
            <span>2060</span>
            <span>2070</span>
            <span>2080</span>
          </div>
        </div>

        <!-- Inflation settings -->
        <div class="category-section inflation-section">
          <h3 class="section-title text-sm font-bold text-inflation">💸 Inflation</h3>
          <div class="control-item">
            <div class="control-label">
              <span class="text-xs font-medium text-secondary">Annual Inflation Rate</span>
              <div class="manual-input-wrap">
                <input
                  type="number"
                  v-model.number="inflationRate"
                  min="0"
                  max="50"
                  step="0.1"
                  class="manual-input"
                />
                <span class="input-suffix">%</span>
              </div>
            </div>
            <input
              type="range"
              v-model.number="inflationRate"
              min="0"
              max="10"
              step="0.1"
              class="slider-input"
            />
          </div>
        </div>

        <div class="category-section investments-section">
          <h3 class="section-title text-sm font-bold text-investments">📈 Investments</h3>
          <div class="starting-balance text-xs text-muted">
            Starting: £{{ startInvestments.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
          </div>

          <div class="control-item">
            <div class="control-label">
              <span class="text-xs font-medium text-secondary">Annual Return %</span>
              <div class="manual-input-wrap">
                <input
                  type="number"
                  v-model.number="returnRateInvestments"
                  min="0"
                  max="100"
                  step="0.1"
                  class="manual-input"
                />
                <span class="input-suffix">%</span>
              </div>
            </div>
            <input
              type="range"
              v-model.number="returnRateInvestments"
              min="0"
              max="15"
              step="0.5"
              class="slider-input"
            />
          </div>

          <div class="control-item">
            <div class="control-label">
              <span class="text-xs font-medium text-secondary">Monthly Contribution</span>
              <div class="manual-input-wrap">
                <span class="input-prefix">£</span>
                <input
                  type="number"
                  v-model.number="contribInvestments"
                  min="0"
                  step="10"
                  class="manual-input"
                />
              </div>
            </div>
            <input
              type="range"
              v-model.number="contribInvestments"
              min="0"
              max="5000"
              step="50"
              class="slider-input"
            />
          </div>
        </div>

        <div class="category-section retirement-section">
          <h3 class="section-title text-sm font-bold text-retirement">🛡️ Retirement</h3>
          <div class="starting-balance text-xs text-muted">
            Starting: £{{ startRetirement.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
          </div>

          <div class="control-item">
            <div class="control-label">
              <span class="text-xs font-medium text-secondary">Annual Return %</span>
              <div class="manual-input-wrap">
                <input
                  type="number"
                  v-model.number="returnRateRetirement"
                  min="0"
                  max="100"
                  step="0.1"
                  class="manual-input"
                />
                <span class="input-suffix">%</span>
              </div>
            </div>
            <input
              type="range"
              v-model.number="returnRateRetirement"
              min="0"
              max="15"
              step="0.5"
              class="slider-input"
            />
          </div>

          <div class="control-item">
            <div class="control-label">
              <span class="text-xs font-medium text-secondary">Monthly Contribution</span>
              <div class="manual-input-wrap">
                <span class="input-prefix">£</span>
                <input
                  type="number"
                  v-model.number="contribRetirement"
                  min="0"
                  step="10"
                  class="manual-input"
                />
              </div>
            </div>
            <input
              type="range"
              v-model.number="contribRetirement"
              min="0"
              max="5000"
              step="50"
              class="slider-input"
            />
          </div>
        </div>
      </div>

      <!-- Right: Interactive Chart & Stats Summary -->
      <div class="chart-panel">
        <!-- Summary Stats Card -->
        <div class="stats-row">
          <div class="stat-card">
            <span class="stat-label text-xs text-muted font-medium">Projected Net Worth ({{ endYear || startYear + 1 }})</span>
            <span class="stat-value text-xl font-bold">£{{ finalNetWorthFormatted }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label text-xs text-muted font-medium">Total Contributions</span>
            <span class="stat-value text-xl font-bold text-secondary">£{{ totalContributionsFormatted }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label text-xs text-muted font-medium">Compound Gains</span>
            <span class="stat-value text-xl font-bold text-positive">£{{ compoundGainsFormatted }}</span>
          </div>
        </div>

        <!-- Line Chart -->
        <div class="chart-wrap">
          <Line v-if="chartData" :data="chartData" :options="chartOptions" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import type { DashboardSummary } from '@/api/client'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps<{
  summary: DashboardSummary
}>()

// Current Year Baseline
const startYear = new Date().getFullYear()

// LocalStorage Keys
const STORAGE_KEYS = {
  END_YEAR: 'forecast_end_year',
  INCLUDE_OTHER: 'forecast_include_other',
  INV_RETURN: 'forecast_inv_return',
  INV_CONTRIB: 'forecast_inv_contrib',
  RET_RETURN: 'forecast_ret_return',
  RET_CONTRIB: 'forecast_ret_contrib',
  INFLATION_RATE: 'forecast_inflation_rate',
  ADJUST_INFLATION: 'forecast_adjust_inflation'
}

// Simulation Inputs (Read from localStorage with fallback defaults)
const endYear = ref<number>(
  Number(localStorage.getItem(STORAGE_KEYS.END_YEAR) || '2050')
)
const includeOther = ref<boolean>(
  localStorage.getItem(STORAGE_KEYS.INCLUDE_OTHER) !== 'false'
)
const returnRateInvestments = ref<number>(
  Number(localStorage.getItem(STORAGE_KEYS.INV_RETURN) || '7.0')
)
const contribInvestments = ref<number>(
  Number(localStorage.getItem(STORAGE_KEYS.INV_CONTRIB) || '500')
)
const returnRateRetirement = ref<number>(
  Number(localStorage.getItem(STORAGE_KEYS.RET_RETURN) || '6.0')
)
const contribRetirement = ref<number>(
  Number(localStorage.getItem(STORAGE_KEYS.RET_CONTRIB) || '300')
)
const inflationRate = ref<number>(
  Number(localStorage.getItem(STORAGE_KEYS.INFLATION_RATE) || '2.5')
)
const adjustInflation = ref<boolean>(
  localStorage.getItem(STORAGE_KEYS.ADJUST_INFLATION) === 'true' // defaults to false
)

// Watch changes to save to localStorage
watch(endYear, (val) => {
  if (val) localStorage.setItem(STORAGE_KEYS.END_YEAR, val.toString())
})
watch(includeOther, (val) => {
  localStorage.setItem(STORAGE_KEYS.INCLUDE_OTHER, val.toString())
})
watch(returnRateInvestments, (val) => {
  if (val !== undefined && val !== null) localStorage.setItem(STORAGE_KEYS.INV_RETURN, val.toString())
})
watch(contribInvestments, (val) => {
  if (val !== undefined && val !== null) localStorage.setItem(STORAGE_KEYS.INV_CONTRIB, val.toString())
})
watch(returnRateRetirement, (val) => {
  if (val !== undefined && val !== null) localStorage.setItem(STORAGE_KEYS.RET_RETURN, val.toString())
})
watch(contribRetirement, (val) => {
  if (val !== undefined && val !== null) localStorage.setItem(STORAGE_KEYS.RET_CONTRIB, val.toString())
})
watch(inflationRate, (val) => {
  if (val !== undefined && val !== null) localStorage.setItem(STORAGE_KEYS.INFLATION_RATE, val.toString())
})
watch(adjustInflation, (val) => {
  localStorage.setItem(STORAGE_KEYS.ADJUST_INFLATION, val.toString())
})

// starting points from category totals
const startInvestments = computed(() => {
  return props.summary.categories.find(c => c.category === 'INVESTMENTS')?.total_value ?? 0
})

const startRetirement = computed(() => {
  return props.summary.categories.find(c => c.category === 'RETIREMENT')?.total_value ?? 0
})

const startSavings = computed(() => {
  return props.summary.categories.find(c => c.category === 'SAVINGS')?.total_value ?? 0
})

const startPropertyEquity = computed(() => {
  return props.summary.mortgage_equity ?? 0
})

const otherAssetsValue = computed(() => {
  return startSavings.value + startPropertyEquity.value
})

const otherAssetsFormatted = computed(() => {
  return otherAssetsValue.value.toLocaleString('en-GB', { maximumFractionDigits: 0 })
})

// Run monthly simulation (nominal values & discount rate tracking)
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

  // Year 0
  points.push({
    year: startYear,
    investments: startInv,
    retirement: startRet,
    other: otherVal,
    total: startInv + startRet + otherVal,
    discount: 1
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

    // 12 months compounding
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
      discount: discount
    })
  }

  return points
})

// Apply inflation adjustment discount if requested
const adjustedProjectionData = computed(() => {
  const data = projectionData.value
  const applyInflation = adjustInflation.value

  return data.map(d => {
    const factor = applyInflation ? d.discount : 1
    return {
      year: d.year,
      investments: d.investments * factor,
      retirement: d.retirement * factor,
      other: d.other * factor,
      total: d.total * factor
    }
  })
})

// Statistics Computations
const finalPoint = computed(() => {
  return adjustedProjectionData.value[adjustedProjectionData.value.length - 1]
})

const finalNetWorthFormatted = computed(() => {
  return (finalPoint.value?.total ?? 0).toLocaleString('en-GB', { maximumFractionDigits: 0 })
})

const yearsCount = computed(() => {
  const targetYear = endYear.value || (startYear + 1)
  return Math.max(1, targetYear - startYear)
})

// Compute total contributions, potentially inflation discounted
const totalContributions = computed(() => {
  const cInv = contribInvestments.value || 0
  const cRet = contribRetirement.value || 0
  const annualContrib = (cInv + cRet) * 12

  if (!adjustInflation.value) {
    return annualContrib * yearsCount.value
  }

  // Sum inflation-discounted contributions year-by-year
  let total = 0
  const infRate = (inflationRate.value || 0) / 100
  for (let t = 1; t <= yearsCount.value; t++) {
    total += annualContrib * Math.pow(1 + infRate, -t)
  }
  return total
})

const totalContributionsFormatted = computed(() => {
  return totalContributions.value.toLocaleString('en-GB', { maximumFractionDigits: 0 })
})

const compoundGains = computed(() => {
  const endingTotal = finalPoint.value?.total ?? 0
  
  // Starting total
  const startingTotal = startInvestments.value + startRetirement.value + (includeOther.value ? otherAssetsValue.value : 0)
  
  // Gains = Ending adjusted total - Starting total - Adjusted contributions
  const gains = endingTotal - startingTotal - totalContributions.value
  return Math.max(0, gains)
})

const compoundGainsFormatted = computed(() => {
  return compoundGains.value.toLocaleString('en-GB', { maximumFractionDigits: 0 })
})

// Chart.js Data Configuration
const chartData = computed(() => {
  const data = adjustedProjectionData.value
  return {
    labels: data.map(d => d.year.toString()),
    datasets: [
      {
        label: 'Total Net Worth',
        data: data.map(d => d.total),
        borderColor: '#c084fc', // accent color style (purple/violet)
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
        borderColor: '#818cf8', // --cat-investments (indigo)
        borderWidth: 2.5,
        pointRadius: data.length > 30 ? 0 : 2,
        pointHoverRadius: 5,
        fill: false,
        tension: 0.25,
      },
      {
        label: 'Retirement',
        data: data.map(d => d.retirement),
        borderColor: '#fb923c', // --cat-retirement (amber)
        borderWidth: 2.5,
        pointRadius: data.length > 30 ? 0 : 2,
        pointHoverRadius: 5,
        fill: false,
        tension: 0.25,
      }
    ]
  }
})

// Chart.js Options Configuration
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      labels: {
        color: '#94a3b8',
        font: { size: 11, family: 'Inter' },
        boxWidth: 12,
        boxHeight: 12,
        padding: 15
      }
    },
    tooltip: {
      backgroundColor: '#1a2035',
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 1,
      titleColor: '#94a3b8',
      bodyColor: '#f1f5f9',
      callbacks: {
        label: (ctx: any) => ` ${ctx.dataset.label}: £${Math.round(ctx.raw).toLocaleString('en-GB')}`,
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#64748b', maxTicksLimit: 12, font: { size: 11 } },
      border: { color: 'transparent' },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: {
        color: '#64748b',
        font: { size: 11 },
        callback: (v: any) => `£${Number(v).toLocaleString('en-GB', { maximumFractionDigits: 0 })}`,
      },
      border: { color: 'transparent' },
    },
  },
}
</script>

<style scoped>
.forecast-card {
  margin-top: var(--space-8);
  overflow: hidden;
}

.forecast-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  border-bottom: 1px solid var(--bg-border);
  padding-bottom: var(--space-4);
}

.forecast-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-wrap: wrap;
}

/* Inflation Slide-Toggle Styles */
.toggle-slider-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.toggle-mode-label {
  font-weight: 600;
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.toggle-mode-label.active {
  color: var(--text-primary);
}

/* Slide Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 38px;
  height: 22px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  transition: .25s ease;
  border-radius: var(--radius-full);
}

.slider:before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background-color: var(--text-secondary);
  transition: .25s ease;
  border-radius: var(--radius-full);
}

input:checked + .slider {
  background-color: var(--accent-bg);
  border-color: var(--accent-border);
}

input:checked + .slider:before {
  transform: translateX(16px);
  background-color: var(--accent);
}

.include-toggle {
  display: flex;
  align-items: center;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.toggle-label input {
  accent-color: var(--accent);
  cursor: pointer;
  width: 16px;
  height: 16px;
}

.forecast-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: var(--space-6);
}

.controls-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  background: var(--bg-surface-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--bg-border);
  padding: var(--space-4);
  max-height: 560px;
  overflow-y: auto;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.category-section {
  border-top: 1px solid var(--bg-border);
  padding-top: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.text-investments {
  color: var(--cat-investments);
}

.text-retirement {
  color: var(--cat-retirement);
}

.text-inflation {
  color: #f43f5e; /* Rose/Red erosion indicator */
}

.starting-balance {
  margin-top: calc(-1 * var(--space-2));
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.control-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Compact Editable Badges */
.manual-input-wrap {
  display: flex;
  align-items: center;
  background: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-sm);
  padding: 2px 6px;
  transition: border-color var(--transition-fast);
}

.manual-input-wrap:focus-within {
  border-color: var(--accent);
}

.manual-input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  width: 54px;
  text-align: right;
  outline: none;
  font-family: inherit;
  padding: 0;
}

/* remove spinners */
.manual-input::-webkit-outer-spin-button,
.manual-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.manual-input[type=number] {
  -moz-appearance: textfield;
}

.input-prefix {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  font-weight: 600;
  margin-right: 2px;
}

.input-suffix {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  font-weight: 600;
  margin-left: 2px;
}

.year-badge .manual-input {
  width: 44px;
  text-align: center;
}

/* Slider Custom Styling */
.slider-input {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--bg-elevated);
  outline: none;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: var(--radius-full);
  background: var(--accent);
  border: 2px solid var(--text-primary);
  cursor: pointer;
  transition: transform var(--transition-fast), background var(--transition-fast);
}

.slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  background: var(--accent-light);
}

.slider-ticks {
  display: flex;
  justify-content: space-between;
  padding: 0 var(--space-1);
}

.chart-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  height: 100%;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

.stat-card {
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-label {
  letter-spacing: 0.02em;
}

.stat-value {
  color: var(--text-primary);
}

.text-secondary {
  color: #a855f7; /* secondary color badge/purple indicator */
}

.text-positive {
  color: var(--positive);
}

.chart-wrap {
  height: 380px;
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
}

@media (max-width: 900px) {
  .forecast-layout {
    grid-template-columns: 1fr;
  }
  
  .controls-panel {
    max-height: none;
  }
  
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
