<template>
  <div class="account-card" :class="{ inactive: !account.is_active }">
    <div class="card-top">
      <div class="type-badge badge" :class="`badge-${account.category.toLowerCase()}`">
        {{ account.account_type.replace('_', ' ') }}
      </div>
      <div class="card-actions">
        <button
          v-if="['INVESTMENTS', 'RETIREMENT'].includes(account.category)"
          class="btn btn-sm btn-ghost holdings-toggle"
          :class="{ active: showHoldings }"
          @click="showHoldings = !showHoldings"
          :title="showHoldings ? 'Hide holdings' : 'Show share holdings'"
        >
          📊
        </button>
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
          {{ account.profit_amount! >= 0 ? '+' : '' }}{{ formatGBP(Math.abs(account.profit_amount!)) }}
        </span>
        <span class="profit-pct" v-if="account.profit_percent !== null">
          ({{ account.profit_percent! >= 0 ? '+' : '' }}{{ account.profit_percent!.toFixed(2) }}%)
        </span>
      </div>
      <div class="profit-initial">
        Initial: {{ formatGBP(account.initial_investment!) }}
      </div>
    </div>

    <div class="card-footer">
      <span class="text-xs text-muted">Updated {{ updatedFormatted }}</span>
    </div>

    <!-- Share Holdings Panel (INVESTMENTS & RETIREMENT) -->
    <transition name="panel-slide">
      <SharesPanel
        v-if="showHoldings && ['INVESTMENTS', 'RETIREMENT'].includes(account.category)"
        :account-id="account.id"
        :account-name="account.name"
        @synced="onSynced"
      />
    </transition>
  </div>
</template>

<script setup lang="ts">
import { formatGBP } from '@/utils/format'
import { parseApiDate } from '@/utils/date'
import { ref, computed } from 'vue'
import type { Account } from '@/api/client'
import SharesPanel from './SharesPanel.vue'

const props = defineProps<{ account: Account }>()
const emit = defineEmits<{
  updateValue: [account: Account]
  edit: [account: Account]
  refreshAccount: [id: number]
}>()

const showHoldings = ref(false)

const formattedValue = computed(() =>
  formatGBP(props.account.current_value, { decimals: 2, noSymbol: true })
)

const updatedFormatted = computed(() =>
  parseApiDate(props.account.updated_at).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
)

const showProfit = computed(() =>
  props.account.initial_investment !== null &&
  props.account.profit_amount !== null &&
  ['INVESTMENTS', 'RETIREMENT'].includes(props.account.category)
)

function onSynced(newValue: number) {
  // Notify parent so it can re-fetch the account and refresh the card value
  emit('refreshAccount', props.account.id)
}
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

.card-actions { display: flex; gap: var(--space-2); align-items: center; }

.holdings-toggle {
  padding: var(--space-1) var(--space-2);
  font-size: 1rem;
  line-height: 1;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  opacity: 0.5;
}
.holdings-toggle:hover,
.holdings-toggle.active {
  opacity: 1;
  background: var(--cat-investments-bg);
  color: var(--cat-investments);
}

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

/* Holdings panel slide animation */
.panel-slide-enter-active, .panel-slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.panel-slide-enter-from, .panel-slide-leave-to {
  opacity: 0;
  max-height: 0;
}
.panel-slide-enter-to, .panel-slide-leave-from {
  opacity: 1;
  max-height: 600px;
}
</style>
