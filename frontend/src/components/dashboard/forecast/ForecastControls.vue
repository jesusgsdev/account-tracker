<template>
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
      <ForecastControlItem
        v-model="inflationRate"
        label="Annual Inflation Rate"
        suffix="%"
        :input-min="0" :input-max="50" :input-step="0.1"
        :range-min="0" :range-max="10" :range-step="0.1"
      />
    </div>

    <div class="category-section investments-section">
      <h3 class="section-title text-sm font-bold text-investments">📈 Investments</h3>
      <div class="starting-balance text-xs text-muted">
        Starting: {{ formatGBP(startInvestments) }}
      </div>
      <ForecastControlItem
        v-model="returnRateInvestments"
        label="Annual Return %"
        suffix="%"
        :input-min="0" :input-max="100" :input-step="0.1"
        :range-min="0" :range-max="15" :range-step="0.5"
      />
      <ForecastControlItem
        v-model="contribInvestments"
        label="Monthly Contribution"
        prefix="£"
        :input-min="0" :input-step="10"
        :range-min="0" :range-max="5000" :range-step="50"
      />
    </div>

    <div class="category-section pension-section">
      <h3 class="section-title text-sm font-bold text-pension">🏛️ State Pension &amp; Income</h3>
      <div class="starting-balance text-xs text-muted">
        State Pension: £{{ pensionBase }}/yr (2025/26), grown by the inflation rate. Starts {{ statePensionStartYear }} (age {{ pensionAge }})
      </div>
      <div class="control-label">
        <span class="text-xs font-medium text-pension">Birth Year</span>
        <div class="manual-input-wrap">
          <input
            type="text"
            inputmode="numeric"
            maxlength="4"
            v-model.number="birthYear"
            class="manual-input"
          />
        </div>
      </div>
      <ForecastControlItem
        v-model="withdrawalRate"
        label="Pot Drawdown Rate"
        suffix="%"
        :input-min="0" :input-max="20" :input-step="0.1"
        :range-min="0" :range-max="10" :range-step="0.1"
      />
    </div>

    <div class="category-section retirement-section">
      <h3 class="section-title text-sm font-bold text-retirement">🛡️ Retirement</h3>
      <div class="starting-balance text-xs text-muted">
        Starting: {{ formatGBP(startRetirement) }}
      </div>
      <ForecastControlItem
        v-model="returnRateRetirement"
        label="Annual Return %"
        suffix="%"
        :input-min="0" :input-max="100" :input-step="0.1"
        :range-min="0" :range-max="15" :range-step="0.5"
      />
      <ForecastControlItem
        v-model="contribRetirement"
        label="Monthly Contribution"
        prefix="£"
        :input-min="0" :input-step="10"
        :range-min="0" :range-max="5000" :range-step="50"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatGBP } from '@/utils/format'
import { STATE_PENSION_AGE as pensionAge, STATE_PENSION_2025_26 } from '@/composables/useForecast'
import ForecastControlItem from './ForecastControlItem.vue'

const pensionBase = STATE_PENSION_2025_26.toLocaleString('en-GB')

defineProps<{
  startYear: number
  startInvestments: number
  startRetirement: number
  statePensionStartYear: number
}>()
const endYear = defineModel<number>('endYear', { required: true })
const inflationRate = defineModel<number>('inflationRate', { required: true })
const returnRateInvestments = defineModel<number>('returnRateInvestments', { required: true })
const contribInvestments = defineModel<number>('contribInvestments', { required: true })
const returnRateRetirement = defineModel<number>('returnRateRetirement', { required: true })
const contribRetirement = defineModel<number>('contribRetirement', { required: true })
const birthYear = defineModel<number>('birthYear', { required: true })
const withdrawalRate = defineModel<number>('withdrawalRate', { required: true })
</script>

<style scoped>
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

.text-investments { color: var(--cat-investments); }
.text-retirement { color: var(--cat-retirement); }
.text-inflation { color: #f43f5e; }
.text-pension { color: #38bdf8; }

.starting-balance {
  margin-top: calc(-1 * var(--space-2));
}

.control-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

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

.manual-input::-webkit-outer-spin-button,
.manual-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.manual-input[type=number] {
  -moz-appearance: textfield;
}

.year-badge .manual-input {
  width: 44px;
  text-align: center;
}

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

@media (max-width: 900px) {
  .controls-panel {
    max-height: none;
  }
}
</style>
