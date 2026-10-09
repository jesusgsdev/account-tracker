<template>
  <div class="mortgage-card" :class="{ inactive: !property.is_active }">
    <!-- Header row -->
    <div class="card-top">
      <div class="card-badge badge badge-property">🏠 Property</div>
      <div class="card-actions">
        <button class="btn btn-xs btn-ghost" @click="$emit('edit', property)">Edit Details</button>
        <button class="btn btn-xs btn-secondary" @click="showUpdateValue = true">Update Value</button>
      </div>
    </div>

    <div class="card-name">{{ property.name }}</div>
    <div v-if="property.property_address" class="card-address text-sm text-muted">{{ property.property_address }}</div>

    <!-- Main equity display -->
    <div class="equity-block" :class="property.equity >= 0 ? 'positive' : 'negative'">
      <div class="equity-label text-xs">Your Equity</div>
      <div class="equity-value">
        {{ property.equity >= 0 ? '' : '-' }}{{ formatGBP(Math.abs(property.equity)) }}
      </div>
      <div v-if="property.ltv_percent !== null" class="ltv-badge" :class="ltvClass">
        LTV {{ property.ltv_percent.toFixed(1) }}%
      </div>
    </div>

    <!-- Property vs Debt breakdown -->
    <div class="breakdown-grid">
      <div class="breakdown-item">
        <span class="breakdown-label text-xs text-muted">Property Value</span>
        <span class="breakdown-value">{{ formatGBP(property.property_value, { decimals: 0 }) }}</span>
        <span v-if="property.ownership_percent < 100" class="breakdown-share text-xs text-muted">
          Your {{ property.ownership_percent }}% share: {{ formatGBP(property.property_value_share, { decimals: 0 }) }}
        </span>
      </div>
      <div class="breakdown-item">
        <span class="breakdown-label text-xs text-muted">Total Debt</span>
        <span class="breakdown-value negative-text">-{{ formatGBP(property.total_outstanding, { decimals: 0 }) }}</span>
        <span v-if="property.ownership_percent < 100" class="breakdown-share text-xs text-muted">
          Your share: -{{ formatGBP(property.outstanding_share, { decimals: 0 }) }}
        </span>
      </div>
    </div>

    <!-- Property gain vs original price -->
    <div v-if="property.property_gain !== null" class="gain-row" :class="property.property_gain >= 0 ? 'positive' : 'negative'">
      <span class="text-xs">{{ property.property_gain >= 0 ? '▲' : '▼' }} vs purchase price</span>
      <span class="gain-amount text-xs font-semibold">
        {{ property.property_gain >= 0 ? '+' : '' }}{{ formatGBP(Math.abs(property.property_gain), { decimals: 0 }) }}
        <span v-if="property.property_gain_percent !== null">({{ property.property_gain_percent >= 0 ? '+' : '' }}{{ property.property_gain_percent.toFixed(1) }}%)</span>
      </span>
    </div>



    <!-- Mortgage Parts Section -->
    <div class="parts-section">
      <div class="parts-header">
        <h4 class="text-xs font-bold text-muted uppercase tracking-wider">Mortgages ({{ property.mortgage_parts.length }})</h4>
        <button class="btn btn-xs btn-primary btn-add-part" @click="openAddPart">
          + Add Part
        </button>
      </div>

      <div v-if="property.mortgage_parts.length === 0" class="empty-parts text-sm text-muted text-center py-4">
        No active mortgages on this property.
      </div>
      <div v-else class="parts-list">
        <div v-for="part in property.mortgage_parts" :key="part.id" class="part-item">
          <div class="part-main">
            <div>
              <div class="part-name font-semibold text-sm">{{ part.name }}</div>
              <div class="part-lender text-xs text-muted">
                {{ part.lender || 'No Lender' }} • {{ part.mortgage_type === 'REPAYMENT' ? 'Repayment' : 'Interest Only' }}
              </div>
            </div>
            <div class="part-balance-block text-right">
              <div class="part-balance font-bold text-sm negative-text">-{{ formatGBP(part.outstanding_balance, { decimals: 0 }) }}</div>
              <div v-if="part.interest_rate !== null" class="part-rate text-xs text-muted">{{ part.interest_rate.toFixed(2) }}% APR</div>
            </div>
          </div>

          <div class="part-details text-xs text-muted">
            <span v-if="part.monthly_payment">
              Payment: {{ formatGBP(part.monthly_payment) }}/mo
              <span v-if="estPartPayment(part) !== null" class="est-detail text-muted opacity-80" style="margin-left: 4px;">
                (Est: {{ formatGBP(estPartPayment(part)) }}/mo)
              </span>
            </span>
            <span v-else-if="estPartPayment(part) !== null" class="est-payment-span">
              Est. Payment: {{ formatGBP(estPartPayment(part)) }}/mo
            </span>
            <span v-if="part.remaining_term_months !== null && part.remaining_term_months > 0" class="term-span">
              Term: {{ Math.floor(part.remaining_term_months / 12) }}y {{ part.remaining_term_months % 12 }}m left
            </span>
          </div>

          <div class="part-actions">
            <button class="btn btn-xs btn-ghost" @click="openEditPart(part)">Edit Part</button>
            <button class="btn btn-xs btn-primary" @click="openUpdateBalance(part)">Update Balance</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Info/Footer metadata -->
    <div class="card-meta">
      <span class="text-xs text-muted">
        Updated {{ updatedFormatted }}
      </span>
      <span v-if="totalEstPayment > 0" class="text-xs text-muted font-semibold" style="margin-left: var(--space-4);">
        Est. Total Payment: {{ formatGBP(totalEstPayment, { decimals: 0 }) }}/mo
      </span>
      <span v-if="property.weighted_avg_rate !== null" class="text-xs text-muted ml-auto font-semibold">
        Weighted Avg Rate: {{ property.weighted_avg_rate.toFixed(2) }}%
      </span>
    </div>

    <!-- Modals -->
    <UpdatePropertyValueModal
      v-model="showUpdateValue"
      :property="property"
      @saved="$emit('updated')"
    />

    <AddPartModal
      v-model="showAddPart"
      :property-id="property.id"
      :part="editingPart"
      @saved="$emit('updated')"
    />

    <UpdatePartBalanceModal
      v-model="showUpdateBalance"
      :property-id="property.id"
      :property-name="property.name"
      :part="updatingPart"
      :ownership-percent="property.ownership_percent"
      @saved="$emit('updated')"
    />
  </div>
</template>

<script setup lang="ts">
import { formatGBP } from '@/utils/format'
import { parseApiDate } from '@/utils/date'
import { ref, computed } from 'vue'
import { api, type Property, type MortgagePart } from '@/api/client'
import UpdatePropertyValueModal from './UpdatePropertyValueModal.vue'
import AddPartModal from './AddPartModal.vue'
import UpdatePartBalanceModal from './UpdatePartBalanceModal.vue'

const props = defineProps<{ property: Property }>()
const emit = defineEmits<{
  edit: [p: Property]
  updated: []
}>()

const showUpdateValue = ref(false)
const showAddPart = ref(false)
const showUpdateBalance = ref(false)

const editingPart = ref<MortgagePart | null>(null)
const updatingPart = ref<MortgagePart | null>(null)

function estPartPayment(part: MortgagePart): number | null {
  const p = part.outstanding_balance
  const r = part.interest_rate
  const n = part.remaining_term_months
  
  if (p <= 0) return 0
  if (r === null || r === undefined) return null

  if (part.mortgage_type === 'INTEREST_ONLY') {
    return (p * (r / 100)) / 12
  } else {
    // REPAYMENT
    if (n === null || n === undefined || n <= 0) return null
    const monthlyRate = r / 100 / 12
    if (monthlyRate === 0) return p / n
    return (p * monthlyRate * Math.pow(1 + monthlyRate, n)) / (Math.pow(1 + monthlyRate, n) - 1)
  }
}

const totalEstPayment = computed(() => {
  return props.property.mortgage_parts.reduce((sum, part) => {
    const est = estPartPayment(part)
    return sum + (est || 0)
  }, 0)
})

const updatedFormatted = computed(() =>
  parseApiDate(props.property.updated_at).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
)

const ltvClass = computed(() => {
  const ltv = props.property.ltv_percent ?? 0
  if (ltv > 90) return 'ltv-danger'
  if (ltv > 75) return 'ltv-warn'
  return 'ltv-ok'
})

function openAddPart() {
  editingPart.value = null
  showAddPart.value = true
}

function openEditPart(part: MortgagePart) {
  editingPart.value = part
  showAddPart.value = true
}

function openUpdateBalance(part: MortgagePart) {
  updatingPart.value = part
  showUpdateBalance.value = true
}
</script>

<style scoped>
.mortgage-card {
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}
.mortgage-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.mortgage-card.inactive { opacity: 0.5; }

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.card-actions { display: flex; gap: var(--space-2); flex-wrap: wrap; }

.badge-property { background: rgba(168, 85, 247, 0.15); color: #c084fc; }

.card-name { font-size: var(--font-size-base); font-weight: 600; }
.card-address { color: var(--text-muted); }

/* Equity block */
.equity-block {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  flex-wrap: wrap;
}
.equity-block.positive { background: var(--positive-bg); border: 1px solid rgba(34,197,94,0.2); }
.equity-block.negative { background: var(--negative-bg); border: 1px solid rgba(239,68,68,0.2); }

.equity-label { color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.equity-value {
  font-size: var(--font-size-2xl);
  font-weight: 800;
  letter-spacing: -0.02em;
}
.equity-block.positive .equity-value { color: var(--positive); }
.equity-block.negative .equity-value { color: var(--negative); }

.ltv-badge {
  margin-left: auto;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 700;
}
.ltv-ok     { background: var(--positive-bg); color: var(--positive); }
.ltv-warn   { background: rgba(251,146,60,0.15); color: var(--cat-retirement); }
.ltv-danger { background: var(--negative-bg); color: var(--negative); }

/* Breakdown */
.breakdown-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.breakdown-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3);
  background: var(--bg-base);
  border-radius: var(--radius-md);
}
.breakdown-value { font-size: var(--font-size-base); font-weight: 600; }
.negative-text { color: var(--negative); }

/* Gain row */
.gain-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
}
.gain-row.positive { background: var(--positive-bg); color: var(--positive); }
.gain-row.negative { background: var(--negative-bg); color: var(--negative); }

/* Parts Section */
.parts-section {
  border-top: 1px solid var(--bg-border);
  padding-top: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.parts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-1);
}
.btn-add-part {
  background: rgba(108, 99, 255, 0.15);
  color: var(--accent-light);
  border: 1px solid rgba(108, 99, 255, 0.3);
}
.btn-add-part:hover {
  background: var(--accent-light);
  color: #fff;
}
.parts-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.part-item {
  background: var(--bg-base);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.part-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.part-balance {
  font-size: var(--font-size-sm);
}
.part-details {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.term-span {
  background: rgba(251, 146, 60, 0.1);
  color: #fbd38d;
  padding: 1px 6px;
  border-radius: 4px;
}
.part-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
  border-top: 1px dashed var(--bg-border);
  padding-top: var(--space-2);
  margin-top: 2px;
}

/* Meta row */
.card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  border-top: 1px solid var(--bg-border);
  padding-top: var(--space-2);
}
.ml-auto { margin-left: auto; }

/* Chart Toggle Styles */
.chart-toggle-row {
  display: flex;
  justify-content: center;
  margin: var(--space-2) 0;
}
.btn-toggle-chart {
  color: var(--accent-light);
  background: rgba(108, 99, 255, 0.05);
  cursor: pointer;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(139, 133, 255, 0.15);
  transition: all var(--transition-fast);
}
.btn-toggle-chart:hover {
  background: var(--accent-glow);
  border-color: var(--accent-light);
  color: #fff;
}
</style>
