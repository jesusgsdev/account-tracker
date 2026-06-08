<template>
  <div class="chart-card card">
    <div class="chart-header">
      <div>
        <h2 class="chart-title">Net Worth Over Time</h2>
        <p class="text-xs text-muted">Portfolio value tracked from audit history</p>
      </div>
      <div class="range-pills">
        <button
          v-for="r in ranges"
          :key="r.label"
          class="range-pill"
          :class="{ active: selectedDays === r.days }"
          @click="selectedDays = r.days; $emit('rangeChange', r.days)"
        >{{ r.label }}</button>
      </div>
    </div>
    <div class="chart-wrap">
      <Line v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else-if="loading" class="chart-empty skeleton" />
      <div v-else class="chart-empty text-muted text-sm">No history yet — start by updating an account value.</div>
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
import type { HistoryPoint } from '@/api/client'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const props = defineProps<{
  points: HistoryPoint[]
  loading: boolean
}>()

defineEmits<{ rangeChange: [days: number] }>()

const ranges = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: 'All', days: 3650 },
]
const selectedDays = ref(365)

const chartData = computed(() => {
  if (!props.points.length) return null
  return {
    labels: props.points.map(p =>
      new Date(p.date + 'Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
    ),
    datasets: [{
      label: 'Net Worth',
      data: props.points.map(p => p.total_value),
      borderColor: '#6c63ff',
      backgroundColor: 'rgba(108, 99, 255, 0.1)',
      borderWidth: 2.5,
      pointRadius: props.points.length > 60 ? 0 : 3,
      pointHoverRadius: 5,
      pointBackgroundColor: '#6c63ff',
      fill: true,
      tension: 0.4,
    }],
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1a2035',
      borderColor: 'rgba(255,255,255,0.08)',
      borderWidth: 1,
      titleColor: '#94a3b8',
      bodyColor: '#f1f5f9',
      callbacks: {
        label: (ctx: any) => ` £${ctx.raw.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`,
      },
    },
  },
  scales: {
    x: {
      grid: { color: 'rgba(255,255,255,0.04)' },
      ticks: { color: '#64748b', maxTicksLimit: 8, font: { size: 11 } },
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
.chart-card { overflow: hidden; }

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.chart-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--space-1);
}

.range-pills {
  display: flex;
  gap: var(--space-1);
  background: var(--bg-base);
  padding: 4px;
  border-radius: var(--radius-md);
}

.range-pill {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--text-muted);
  transition: all var(--transition-fast);
  cursor: pointer;
  background: none;
  border: none;
}
.range-pill:hover   { color: var(--text-primary); }
.range-pill.active  { background: var(--accent); color: white; }

.chart-wrap {
  height: 260px;
}

.chart-empty {
  height: 100%;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
