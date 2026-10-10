<template>
  <div class="income-card">
    <div class="income-head">
      <span class="text-xs text-muted font-medium">Expected Gross Income in {{ endYear }} (before tax)</span>
      <span class="text-xs text-muted">{{ adjusted ? "Today's £" : 'Future £' }}</span>
    </div>
    <div class="income-body">
      <div class="income-main">
        <div>
          <span class="income-value">£{{ income.annual }}</span>
          <span class="income-unit text-xs text-muted"> / year</span>
        </div>
        <div>
          <span class="income-value">£{{ income.monthly }}</span>
          <span class="income-unit text-xs text-muted"> / month</span>
        </div>
      </div>
      <div class="income-breakdown text-xs text-muted">
        <span>State Pension: £{{ income.pension }}<template v-if="!income.pensionActive"> (starts {{ pensionStartYear }})</template></span>
        <span>Pot drawdown ({{ withdrawalRate }}% of Investments + Retirement): £{{ income.drawdown }}</span>
      </div>
    </div>

    <div class="income-net">
      <div class="income-head">
        <span class="text-xs text-muted font-medium">Estimated Net Income (England, after income tax)</span>
        <span class="text-xs text-muted">Tax £{{ income.tax }} · {{ income.effectiveRate }}% effective</span>
      </div>
      <div class="income-body">
        <div class="income-main">
          <div>
            <span class="income-value net">£{{ income.netAnnual }}</span>
            <span class="income-unit text-xs text-muted"> / year</span>
          </div>
          <div>
            <span class="income-value net">£{{ income.netMonthly }}</span>
            <span class="income-unit text-xs text-muted"> / month</span>
          </div>
        </div>
        <div class="income-breakdown text-xs text-muted">
          <span>2025/26 rates and thresholds, raised each year by your inflation rate</span>
          <span>75% of Retirement drawdown taxed; Investments assumed ISA (tax-free); no NI</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  endYear: number
  adjusted: boolean
  pensionStartYear: number
  withdrawalRate: number
  income: {
    pensionActive: boolean; pension: string; drawdown: string; annual: string; monthly: string
    tax: string; netAnnual: string; netMonthly: string; effectiveRate: string
  }
}>()
</script>

<style scoped>
.income-card {
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.income-net { border-top: 1px solid var(--bg-border); padding-top: var(--space-2); display: flex; flex-direction: column; gap: var(--space-2); }
.income-value.net { color: var(--positive); }
.income-head { display: flex; justify-content: space-between; gap: var(--space-2); flex-wrap: wrap; }
.income-main { display: flex; gap: var(--space-8); flex-wrap: wrap; }
.income-value { font-size: var(--font-size-xl); font-weight: 700; color: var(--text-primary); }
.income-body { display: flex; align-items: center; justify-content: space-between; gap: var(--space-6); flex-wrap: wrap; }
.income-breakdown { display: flex; flex-direction: column; gap: 2px; text-align: right; }

@media (max-width: 600px) {
  .income-breakdown { text-align: left; }
}
</style>
