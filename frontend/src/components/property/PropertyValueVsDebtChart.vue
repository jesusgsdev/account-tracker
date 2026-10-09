<template>
  <div class="property-vs-debt-chart">
    <div class="chart-header-compact">
      <span class="text-xs font-semibold uppercase tracking-wider text-muted">Equity vs Debt Breakdown</span>
    </div>
    <div class="chart-wrap">
      <Doughnut :data="chartData" :options="chartOptions" />
      <div class="center-labels">
        <span class="total-label text-xs text-muted">Value Share</span>
        <span class="total-val font-bold">{{ formatGBP(Math.round(property.property_value_share), { decimals: 0 }) }}</span>
      </div>
    </div>
    <div class="legend-container">
      <div class="legend-item">
        <span class="legend-dot dot-equity" />
        <span class="text-xs text-secondary">Equity Share:</span>
        <span class="text-xs font-semibold value-positive">{{ formatGBP(Math.round(property.equity), { decimals: 0 }) }} ({{ equityPct }}%)</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot dot-debt" />
        <span class="text-xs text-secondary">Outstanding Debt:</span>
        <span class="text-xs font-semibold value-negative">{{ formatGBP(Math.round(property.outstanding_share), { decimals: 0 }) }} ({{ debtPct }}%)</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatGBP } from '@/utils/format'
import { computed } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import type { Property } from '@/api/client'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{ property: Property }>()

const total = computed(() => props.property.property_value_share)

const equityPct = computed(() => {
  if (total.value <= 0) return '0.0'
  return ((props.property.equity / total.value) * 100).toFixed(1)
})

const debtPct = computed(() => {
  if (total.value <= 0) return '0.0'
  return ((props.property.outstanding_share / total.value) * 100).toFixed(1)
})

const chartData = computed(() => {
  const p = props.property
  return {
    labels: ['Remaining Equity', 'Outstanding Debt'],
    datasets: [
      {
        data: [p.equity, p.outstanding_share],
        backgroundColor: [
          'rgba(34, 197, 94, 0.45)',  // Green
          'rgba(239, 68, 68, 0.45)'   // Red
        ],
        borderColor: '#111827',
        borderWidth: 2,
        hoverBorderWidth: 0,
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '75%',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1a2035',
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 1,
      titleColor: '#94a3b8',
      bodyColor: '#f1f5f9',
      callbacks: {
        label: (ctx: any) => ` ${ctx.label}: ${formatGBP(ctx.raw, { decimals: 0 })}`
      }
    }
  }
}
</script>

<style scoped>
.property-vs-debt-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  height: 100%;
}
.chart-header-compact {
  margin-bottom: var(--space-3);
  display: flex;
  justify-content: space-between;
}
.chart-wrap {
  height: 300px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.center-labels {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.total-label {
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 10px;
}
.total-val {
  font-size: var(--font-size-xl);
  color: var(--text-primary);
}

.legend-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  border-top: 1px solid var(--bg-border);
  padding-top: var(--space-3);
  margin-top: auto;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot-equity { background: var(--positive); }
.dot-debt { background: var(--negative); }
.legend-item span:last-child {
  margin-left: auto;
}
</style>
