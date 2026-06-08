<template>
  <div class="account-card" :class="{ inactive: !account.is_active }">
    <div class="card-top">
      <div class="type-badge badge" :class="`badge-${account.category.toLowerCase()}`">
        {{ account.account_type.replace('_', ' ') }}
      </div>
      <div class="card-actions">
        <button class="btn btn-sm btn-secondary" @click="$emit('edit', account)">Edit</button>
        <button class="btn btn-sm btn-primary" @click="$emit('updateValue', account)">Update Value</button>
      </div>
    </div>

    <div class="card-name">{{ account.name }}</div>
    <div v-if="account.provider" class="card-provider text-sm text-muted">{{ account.provider }}</div>

    <div class="card-value">
      <span class="value-currency">£</span>
      <span class="value-amount">{{ formattedValue }}</span>
    </div>

    <!-- Profit / Loss block — only shown when initial_investment is set -->
    <div v-if="showProfit" class="profit-block" :class="account.profit_amount! >= 0 ? 'profit' : 'loss'">
      <div class="profit-row">
        <span class="profit-label">{{ account.profit_amount! >= 0 ? '▲ Profit' : '▼ Loss' }}</span>
        <span class="profit-amount">
          {{ account.profit_amount! >= 0 ? '+' : '' }}£{{ Math.abs(account.profit_amount!).toLocaleString('en-GB', { minimumFractionDigits: 2 }) }}
        </span>
        <span class="profit-pct" v-if="account.profit_percent !== null">
          ({{ account.profit_percent! >= 0 ? '+' : '' }}{{ account.profit_percent!.toFixed(2) }}%)
        </span>
      </div>
      <div class="profit-initial">
        Initial: £{{ account.initial_investment!.toLocaleString('en-GB', { minimumFractionDigits: 2 }) }}
      </div>
    </div>

    <div class="card-footer">
      <span class="text-xs text-muted">Updated {{ updatedFormatted }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Account } from '@/api/client'

const props = defineProps<{ account: Account }>()
defineEmits<{
  updateValue: [account: Account]
  edit: [account: Account]
}>()

const formattedValue = computed(() =>
  props.account.current_value.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
)

const updatedFormatted = computed(() =>
  new Date(props.account.updated_at + 'Z').toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
)

const showProfit = computed(() =>
  props.account.initial_investment !== null &&
  props.account.profit_amount !== null &&
  ['INVESTMENTS', 'RETIREMENT'].includes(props.account.category)
)
</script>

<style scoped>
.account-card {
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast), border-color var(--transition-fast);
}

.account-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: rgba(255,255,255,0.1);
}

.account-card.inactive { opacity: 0.5; }

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}

.card-actions { display: flex; gap: var(--space-2); }

.card-name {
  font-size: var(--font-size-base);
  font-weight: 600;
}

.card-provider { margin-top: -var(--space-1); }

.card-value {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
  margin: var(--space-2) 0;
}

.value-currency {
  font-size: var(--font-size-lg);
  font-weight: 500;
  color: var(--text-secondary);
}

.value-amount {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.card-footer {
  border-top: 1px solid var(--bg-border);
  padding-top: var(--space-2);
  margin-top: var(--space-1);
}

.profit-block {
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  margin: var(--space-1) 0;
}
.profit-block.profit {
  background: var(--positive-bg);
  border: 1px solid rgba(34, 197, 94, 0.2);
}
.profit-block.loss {
  background: var(--negative-bg);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.profit-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.profit-label {
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.profit-block.profit .profit-label { color: var(--positive); }
.profit-block.loss .profit-label  { color: var(--negative); }

.profit-amount {
  font-size: var(--font-size-sm);
  font-weight: 700;
}
.profit-block.profit .profit-amount { color: var(--positive); }
.profit-block.loss  .profit-amount  { color: var(--negative); }

.profit-pct {
  font-size: var(--font-size-xs);
  opacity: 0.8;
}
.profit-block.profit .profit-pct { color: var(--positive); }
.profit-block.loss  .profit-pct  { color: var(--negative); }

.profit-initial {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-top: var(--space-1);
}
</style>
