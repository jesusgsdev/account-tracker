<template>
  <div class="pie-card card">
    <h2 class="chart-title">Allocation</h2>
    <div class="chart-wrap">
      <Doughnut v-if="hasData" :data="chartData" :options="chartOptions" />
      <div v-else class="empty text-muted text-sm">No data yet</div>
    </div>
    <div class="legend">
      <div v-for="item in legendItems" :key="item.label" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color }" />
        <span class="text-sm text-secondary">{{ item.label }}</span>
        <span class="text-sm font-medium">{{ item.pct }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'vue-chartjs'
import type { CategorySummary } from '@/api/client'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{
  categories: CategorySummary[]
}>()

const COLORS: Record<string, string> = {
  INVESTMENTS: '#818cf8',
  RETIREMENT:  '#fb923c',
  SAVINGS:     '#34d399',
}

const total = computed(() => props.categories.reduce((s, c) => s + c.total_value, 0))
const hasData = computed(() => total.value > 0)

const chartData = computed(() => ({
  labels: props.categories.map(c => c.category),
  datasets: [{
    data: props.categories.map(c => c.total_value),
    backgroundColor: props.categories.map(c => COLORS[c.category] ?? '#6c63ff'),
    borderColor: '#111827',
    borderWidth: 3,
    hoverBorderWidth: 0,
  }],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
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
}

const legendItems = computed(() =>
  props.categories.map(c => ({
    label: c.category.charAt(0) + c.category.slice(1).toLowerCase(),
    color: COLORS[c.category] ?? '#6c63ff',
    pct: total.value > 0 ? ((c.total_value / total.value) * 100).toFixed(1) : '0.0',
  }))
)
</script>

<style scoped>
.pie-card { display: flex; flex-direction: column; gap: var(--space-4); }

.chart-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
}

.chart-wrap {
  height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty { text-align: center; }

.legend { display: flex; flex-direction: column; gap: var(--space-2); }

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-item span:last-child { margin-left: auto; }
</style>
