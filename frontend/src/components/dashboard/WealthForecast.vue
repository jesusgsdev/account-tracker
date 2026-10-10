<template>
  <div class="forecast-card card">
    <ForecastHeader
      v-model:adjust-inflation="adjustInflation"
      v-model:include-other="includeOther"
      :other-assets-formatted="otherAssetsFormatted"
      :dirty="isDirty && loaded"
      :saving="saving"
      @save="onSave"
      @discard="discard"
    />

    <div class="forecast-layout">
      <!-- Left: Simulation Controls -->
      <ForecastControls
        v-model:end-year="endYear"
        v-model:inflation-rate="inflationRate"
        v-model:return-rate-investments="returnRateInvestments"
        v-model:contrib-investments="contribInvestments"
        v-model:return-rate-retirement="returnRateRetirement"
        v-model:contrib-retirement="contribRetirement"
        v-model:contrib-retirement-growth="contribRetirementGrowth"
        :start-year="startYear"
        :start-investments="startInvestments"
        :start-retirement="startRetirement"
        :state-pension-start-year="statePensionStartYear"
        v-model:birth-year="birthYear"
        v-model:withdrawal-rate="withdrawalRate"
      />

      <!-- Right: Interactive Chart & Stats Summary -->
      <div class="chart-panel">
        <ForecastStats
          :end-year="endYear"
          :start-year="startYear"
          :birth-year="birthYear"
          :final-net-worth="finalNetWorthFormatted"
          :total-contributions="totalContributionsFormatted"
          :compound-gains="compoundGainsFormatted"
          :compound-gains-percent="compoundGainsPercentFormatted"
        />
        <ForecastIncome
          :end-year="endYear"
          :adjusted="adjustInflation"
          :pension-start-year="statePensionStartYear"
          :withdrawal-rate="withdrawalRate"
          :income="income"
        />
        <ForecastChart :chart-data="chartData" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import type { DashboardSummary } from '@/api/client'
import { useForecast } from '@/composables/useForecast'
import { useToast } from '@/composables/useToast'
import ForecastHeader from './forecast/ForecastHeader.vue'
import ForecastControls from './forecast/ForecastControls.vue'
import ForecastStats from './forecast/ForecastStats.vue'
import ForecastIncome from './forecast/ForecastIncome.vue'
import ForecastChart from './forecast/ForecastChart.vue'

const props = defineProps<{
  summary: DashboardSummary
}>()

const {
  startYear, endYear, includeOther, returnRateInvestments, contribInvestments,
  returnRateRetirement, contribRetirement, contribRetirementGrowth, inflationRate, adjustInflation,
  startInvestments, startRetirement, otherAssetsFormatted,
  finalNetWorthFormatted, totalContributionsFormatted, compoundGainsFormatted, compoundGainsPercentFormatted,
  birthYear, withdrawalRate, statePensionStartYear, income,
  isDirty, save, discard, load, loaded, saving, loadError,
  chartData,
} = useForecast(() => props.summary)

const toast = useToast()

async function onSave() {
  const err = await save()
  if (err) toast.error(err)
  else toast.success('Forecast settings saved')
}

onMounted(async () => {
  await load()
  if (loadError.value) toast.error(`Could not load saved forecast settings: ${loadError.value}`)
})
</script>

<style scoped>
.forecast-card {
  margin-top: var(--space-8);
  overflow: hidden;
}

.forecast-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: var(--space-6);
}

.chart-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  height: 100%;
}

@media (max-width: 900px) {
  .forecast-layout {
    grid-template-columns: 1fr;
  }
}
</style>
