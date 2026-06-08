<template>
  <div class="net-worth-card card">
    <div class="label text-sm text-secondary font-medium">Total Net Worth</div>
    <div class="value">
      <span class="currency">£</span>
      <span class="amount">{{ formattedValue }}</span>
    </div>

    <!-- Breakdown: accounts + property equity -->
    <div v-if="mortgageEquity !== 0" class="breakdown">
      <div class="breakdown-item">
        <span class="breakdown-dot dot-accounts" />
        <span class="text-xs text-muted">Financial accounts</span>
        <span class="text-xs font-medium">£{{ fmtShort(accountsTotal) }}</span>
      </div>
      <div class="breakdown-item">
        <span class="breakdown-dot dot-property" />
        <span class="text-xs text-muted">Property equity</span>
        <span class="text-xs font-medium" :class="mortgageEquity >= 0 ? 'value-positive' : 'value-negative'">
          {{ mortgageEquity >= 0 ? '+' : '-' }}£{{ fmtShort(Math.abs(mortgageEquity)) }}
        </span>
      </div>
    </div>

    <div v-if="lastUpdated" class="meta text-xs text-muted">
      Last updated {{ lastUpdatedFormatted }}
    </div>
    <div class="glow-ring" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  totalValue: number
  accountsTotal: number
  mortgageEquity: number
  lastUpdated: string | null
}>()

const formattedValue = computed(() =>
  props.totalValue.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
)

function fmtShort(v: number) {
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(2) + 'M'
  if (v >= 1_000) return (v / 1_000).toFixed(1) + 'k'
  return v.toLocaleString('en-GB', { minimumFractionDigits: 0 })
}

const lastUpdatedFormatted = computed(() => {
  if (!props.lastUpdated) return ''
  return new Date(props.lastUpdated + 'Z').toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
})
</script>

<style scoped>
.net-worth-card {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-surface-2) 100%);
  border: 1px solid rgba(108, 99, 255, 0.3);
}

.label { margin-bottom: var(--space-2); }

.value {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.currency {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  color: var(--text-secondary);
}

.amount {
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
  border: 1px solid var(--bg-border);
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.breakdown-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-accounts { background: var(--accent); }
.dot-property { background: #c084fc; }

.breakdown-item span:last-child { margin-left: auto; }

.glow-ring {
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(108, 99, 255, 0.15) 0%, transparent 70%);
  pointer-events: none;
}
</style>
