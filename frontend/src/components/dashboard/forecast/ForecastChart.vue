<template>
  <div class="chart-wrap">
    <Line v-if="chartData" :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup lang="ts">
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler,
  type ChartData,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { formatGBP } from '@/utils/format'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

defineProps<{ chartData: ChartData<'line'> }>()

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
        padding: 15,
      },
    },
    tooltip: {
      backgroundColor: '#1a2035',
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 1,
      titleColor: '#94a3b8',
      bodyColor: '#f1f5f9',
      callbacks: {
        label: (ctx: any) => ` ${ctx.dataset.label}: ${formatGBP(Math.round(ctx.raw), { decimals: 0 })}`,
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
        callback: (v: any) => `${formatGBP(Number(v), { decimals: 0 })}`,
      },
      border: { color: 'transparent' },
    },
  },
}
</script>

<style scoped>
.chart-wrap {
  height: 380px;
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
}
</style>
