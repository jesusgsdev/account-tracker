<template>
  <div class="net-worth-card card">
    <div class="net-worth-grid" :class="{ 'has-property': mortgageSummary }">
      <!-- Left side: Standard Net Worth (Share-based) -->
      <div class="net-worth-main">
        <div class="label text-sm text-secondary font-medium">Standard Net Worth (Share-based)</div>
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
            <span class="text-xs text-muted">Property equity (Your share)</span>
            <span class="text-xs font-medium" :class="mortgageEquity >= 0 ? 'value-positive' : 'value-negative'">
              {{ mortgageEquity >= 0 ? '+' : '-' }}£{{ fmtShort(Math.abs(mortgageEquity)) }}
            </span>
          </div>
        </div>
        <div v-if="lastUpdated" class="meta text-xs text-muted">
          Last updated {{ lastUpdatedFormatted }}
        </div>
      </div>

      <!-- Vertical Divider -->
      <div v-if="mortgageSummary" class="card-divider" />

      <!-- Right side: Real Net Worth (Asset / Equity based) -->
      <div v-if="mortgageSummary" class="net-worth-real">
        <div class="label text-sm text-secondary font-medium flex items-center gap-1">
          Real Net Worth
          <span 
            class="info-trigger text-xs cursor-pointer select-none" 
            title="We calculate two interpretations of your formula:
1. Full Equity Model: Accounts + 100% House Equity - Your % of Debt
2. Full Asset Model: Accounts + 100% House Value - Your % of Debt"
          >
            ℹ️
          </span>
        </div>

        <div class="real-worth-options">
          <!-- Option 1: Full Equity Model -->
          <div class="real-worth-option border-bottom pb-2">
            <div class="option-title text-xs text-muted flex items-center justify-between">
              <span>Full Equity Model</span>
              <span class="formula-tooltip text-xxs font-mono" title="Accounts + 100% House Equity - Your share of Debt">
                [Accounts + House Equity - {{ ownershipPercent }}% Debt]
              </span>
            </div>
            <div class="option-value mt-1">
              <span class="currency-small">£</span>
              <span class="amount-small">{{ formattedRealEquityBased }}</span>
            </div>
          </div>

          <!-- Option 2: Full Asset Model -->
          <div class="real-worth-option pt-2">
            <div class="option-title text-xs text-muted flex items-center justify-between">
              <span>Full Asset Model</span>
              <span class="formula-tooltip text-xxs font-mono" title="Accounts + 100% House Value - Your share of Debt">
                [Accounts + House Value - {{ ownershipPercent }}% Debt]
              </span>
            </div>
            <div class="option-value mt-1">
              <span class="currency-small">£</span>
              <span class="amount-small">{{ formattedRealAssetBased }}</span>
            </div>
          </div>
        </div>

        <!-- Breakdown values for math check -->
        <div class="real-breakdown mt-3">
          <div class="breakdown-label text-xxs text-muted font-medium uppercase tracking-wider mb-1">Calculation Baseline</div>
          <div class="text-xxs text-muted breakdown-rows">
            <div>• 100% House Value: <span class="font-medium">£{{ fmtShort(mortgageSummary.total_property_value_raw) }}</span></div>
            <div>• 100% House Equity: <span class="font-medium">£{{ fmtShort(mortgageSummary.total_property_value_raw - mortgageSummary.total_outstanding_raw) }}</span></div>
            <div>• Your share of Debt ({{ ownershipPercent }}%): <span class="font-medium">-£{{ fmtShort(mortgageSummary.total_outstanding_share) }}</span></div>
          </div>
        </div>
      </div>
    </div>
    <div class="glow-ring" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MortgageSummary } from '@/api/client'

const props = defineProps<{
  totalValue: number
  accountsTotal: number
  mortgageEquity: number
  mortgageSummary: MortgageSummary | null
  lastUpdated: string | null
}>()

const formattedValue = computed(() =>
  props.totalValue.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
)

// Calculate ownership percent dynamically from values
const ownershipPercent = computed(() => {
  if (!props.mortgageSummary || props.mortgageSummary.total_property_value_raw === 0) return 100
  return Math.round((props.mortgageSummary.total_property_value_share / props.mortgageSummary.total_property_value_raw) * 100)
})

// Option 1: Accounts + 100% House Equity - Your % of Debt
// Total equity (100%) = total_property_value_raw - total_outstanding_raw
const realEquityBasedVal = computed(() => {
  if (!props.mortgageSummary) return 0
  const fullEquity = props.mortgageSummary.total_property_value_raw - props.mortgageSummary.total_outstanding_raw
  return props.accountsTotal + fullEquity - props.mortgageSummary.total_outstanding_share
})

const formattedRealEquityBased = computed(() =>
  realEquityBasedVal.value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
)

// Option 2: Accounts + 100% House Value - Your % of Debt
const realAssetBasedVal = computed(() => {
  if (!props.mortgageSummary) return 0
  return props.accountsTotal + props.mortgageSummary.total_property_value_raw - props.mortgageSummary.total_outstanding_share
})

const formattedRealAssetBased = computed(() =>
  realAssetBasedVal.value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
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

.net-worth-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-4);
}

@media (min-width: 768px) {
  .net-worth-grid.has-property {
    grid-template-columns: 1fr auto 1fr;
  }
}

.net-worth-main {
  display: flex;
  flex-direction: column;
}

.card-divider {
  display: none;
}

@media (min-width: 768px) {
  .card-divider {
    display: block;
    width: 1px;
    background: var(--bg-border);
    align-self: stretch;
    margin: var(--space-1) 0;
  }
}

.net-worth-real {
  display: flex;
  flex-direction: column;
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
  font-size: clamp(1.8rem, 4vw, 3rem);
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
  padding: var(--space-2) var(--space-3);
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

.real-worth-options {
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.15);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--bg-border);
}

.border-bottom {
  border-bottom: 1px solid var(--bg-border);
}

.real-worth-option {
  display: flex;
  flex-direction: column;
}

.currency-small {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-secondary);
  margin-right: 2px;
}

.amount-small {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--text-primary);
}

.info-trigger {
  opacity: 0.7;
  transition: opacity 0.2s;
}

.info-trigger:hover {
  opacity: 1;
}

.formula-tooltip {
  opacity: 0.5;
  cursor: help;
}

.formula-tooltip:hover {
  opacity: 0.8;
  color: var(--accent-light);
}

.real-breakdown {
  padding-left: var(--space-2);
  border-left: 2px solid var(--bg-border);
}

.glow-ring {
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(108, 99, 255, 0.12) 0%, transparent 70%);
  pointer-events: none;
}

.breakdown-rows {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
</style>
