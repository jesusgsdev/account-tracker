<template>
  <div class="property-chart-container">
    <div class="chart-header-compact">
      <span class="text-xs font-semibold uppercase tracking-wider text-muted">Valuation History vs Purchase Price</span>
    </div>
    <div class="chart-wrap-compact">
      <Line v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else class="chart-empty text-muted text-xs">No valuation history log found.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatGBP } from '@/utils/format'
import { computed } from 'vue'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import type { PropertyValueAuditLog } from '@/api/client'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps<{
  history: PropertyValueAuditLog[]
  originalPrice: number | null
}>()

function parseDate(dStr: string) {
  if (!dStr) return new Date()
  if (dStr.endsWith('Z') || dStr.includes('+') || dStr.indexOf('T') !== -1) {
    return new Date(dStr)
  }
  return new Date(dStr.replace(' ', 'T') + 'Z')
}

const chartData = computed(() => {
  if (!props.history.length) return null

  // Ensure history is sorted by date ascending for the graph
  const sortedHistory = [...props.history].sort((a, b) => 
    parseDate(a.recorded_at).getTime() - parseDate(b.recorded_at).getTime()
  )

  const labels = sortedHistory.map(h =>
    parseDate(h.recorded_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  )

  const datasets: any[] = [
    {
      label: 'Property Value',
      data: sortedHistory.map(h => h.new_value),
      borderColor: '#c084fc', // Property theme color
      backgroundColor: 'rgba(168, 85, 247, 0.08)',
      borderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: '#c084fc',
      fill: true,
      tension: 0.2,
    }
  ]

  if (props.originalPrice !== null) {
    datasets.push({
      label: 'Original Price',
      data: sortedHistory.map(() => props.originalPrice!),
      borderColor: '#ef4444', // Red for original price line
      backgroundColor: 'transparent',
      borderWidth: 1.5,
      borderDash: [5, 5],
      pointRadius: 0,
      pointHoverRadius: 0,
      fill: false,
      tension: 0,
    })
  }

  return { labels, datasets }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: {
      display: true,
      labels: { color: '#64748b', boxWidth: 12, font: { size: 10 } }
    },
    tooltip: {
      backgroundColor: '#1a2035',
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 1,
      titleColor: '#94a3b8',
      bodyColor: '#f1f5f9',
      callbacks: {
        label: (ctx: any) => ` ${ctx.dataset.label}: ${formatGBP(ctx.raw, { decimals: 0 })}`,
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.02)' },
      ticks: { color: '#64748b', maxTicksLimit: 6, font: { size: 9 } },
      border: { color: 'transparent' },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: {
        color: '#64748b',
        font: { size: 9 },
        callback: (v: any) => `${formatGBP(Number(v), { decimals: 0 })}`,
      },
      border: { color: 'transparent' },
    },
  },
}
</script>

<style scoped>
.property-chart-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.chart-header-compact {
  margin-bottom: var(--space-3);
  display: flex;
  justify-content: space-between;
}
.chart-wrap-compact {
  flex: 1;
  min-height: 0;
}
.chart-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
