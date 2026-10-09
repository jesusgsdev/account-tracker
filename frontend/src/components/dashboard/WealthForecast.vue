<template>
  <div class="forecast-card card">
    <ForecastHeader
      v-model:adjust-inflation="adjustInflation"
      v-model:include-other="includeOther"
      :other-assets-formatted="otherAssetsFormatted"
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
        :start-year="startYear"
        :start-investments="startInvestments"
        :start-retirement="startRetirement"
      />

      <!-- Right: Interactive Chart & Stats Summary -->
      <div class="chart-panel">
        <ForecastStats
          :end-year="endYear"
          :start-year="startYear"
          :final-net-worth="finalNetWorthFormatted"
          :total-contributions="totalContributionsFormatted"
          :compound-gains="compoundGainsFormatted"
        />
        <ForecastChart :chart-data="chartData" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DashboardSummary } from '@/api/client'
import { useForecast } from '@/composables/useForecast'
import ForecastHeader from './forecast/ForecastHeader.vue'
import ForecastControls from './forecast/ForecastControls.vue'
import ForecastStats from './forecast/ForecastStats.vue'
import ForecastChart from './forecast/ForecastChart.vue'

const props = defineProps<{
  summary: DashboardSummary
}>()

const {
  startYear, endYear, includeOther, returnRateInvestments, contribInvestments,
  returnRateRetirement, contribRetirement, inflationRate, adjustInflation,
  startInvestments, startRetirement, otherAssetsFormatted,
  finalNetWorthFormatted, totalContributionsFormatted, compoundGainsFormatted,
  chartData,
} = useForecast(() => props.summary)
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
