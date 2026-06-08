<template>
  <div class="history-card card">
    <h3 class="chart-title">{{ accountName }} — History</h3>
    <div class="chart-wrap">
      <Line v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else class="empty text-sm text-muted">No history available</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Filler,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import type { AuditLog } from '@/api/client'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

const props = defineProps<{
  logs: AuditLog[]
  accountName: string
  color?: string
}>()

const color = computed(() => props.color ?? '#6c63ff')

const chartData = computed(() => {
  if (!props.logs.length) return null
  return {
    labels: props.logs.map(l =>
      new Date(l.recorded_at + 'Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
    ),
    datasets: [{
      label: props.accountName,
      data: props.logs.map(l => l.new_value),
      borderColor: color.value,
      backgroundColor: color.value + '20',
      borderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 5,
      fill: true,
      tension: 0.4,
    }],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1a2035',
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 1,
      callbacks: {
        label: (ctx: any) => ` £${ctx.raw.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`,
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#64748b', font: { size: 11 } },
      border: { color: 'transparent' },
    },
    y: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: {
        color: '#64748b',
        font: { size: 11 },
        callback: (v: any) => `£${Number(v).toLocaleString('en-GB')}`,
      },
      border: { color: 'transparent' },
    },
  },
}
</script>

<style scoped>
.chart-title { font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-4); }
.chart-wrap { height: 180px; }
.empty { height: 100%; display: flex; align-items: center; justify-content: center; }
</style>
