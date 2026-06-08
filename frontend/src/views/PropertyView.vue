<template>
  <div class="page-content">
    <div class="page-header">
      <div>
        <h1 class="page-title">Property</h1>
        <p class="text-sm text-muted">Mortgage tracking &amp; property equity</p>
      </div>
      <button class="btn btn-primary" @click="openAdd">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Add Property
      </button>
    </div>

    <!-- Summary cards -->
    <div v-if="store.properties.length" class="summary-grid">
      <div class="summary-card card">
        <div class="summary-label text-xs text-muted">Total Property Value (Your Share)</div>
        <div class="summary-value">£{{ fmt(store.totalPropertyValueShare) }}</div>
      </div>
      <div class="summary-card card negative-card">
        <div class="summary-label text-xs text-muted">Total Outstanding Debt (Your Share)</div>
        <div class="summary-value negative-text">-£{{ fmt(store.totalOutstandingShare) }}</div>
      </div>
      <div class="summary-card card" :class="store.totalEquity >= 0 ? 'equity-card' : 'negative-card'">
        <div class="summary-label text-xs text-muted">Total Equity</div>
        <div class="summary-value" :class="store.totalEquity >= 0 ? 'positive-text' : 'negative-text'">
          {{ store.totalEquity >= 0 ? '' : '-' }}£{{ fmt(Math.abs(store.totalEquity)) }}
        </div>
      </div>
    </div>

    <!-- Loading skeletons -->
    <div v-if="store.loading" class="loading-grid">
      <div v-for="i in 2" :key="i" class="skeleton" style="height: 320px; border-radius: 16px;" />
    </div>

    <!-- Empty state -->
    <div v-else-if="!store.properties.length" class="empty-state card">
      <div class="empty-icon">🏠</div>
      <h2 class="text-lg font-semibold">No properties tracked</h2>
      <p class="text-sm text-muted">Add your property and mortgage details to include equity in your net worth.</p>
      <button class="btn btn-primary" @click="openAdd">Add Property</button>
    </div>

    <!-- Property Dashboards (2-Column Layout) -->
    <div v-else class="property-dashboard-grid">
      <!-- Column 1: Property Card & Mortgage parts -->
      <div class="property-details-col">
        <MortgageCard
          v-for="p in store.properties"
          :key="p.id"
          :property="p"
          @edit="openEdit"
          @updated="onPropertyUpdated"
        />
      </div>

      <!-- Column 2: Valuation History Chart (Full remaining width) -->
      <div class="property-chart-card card">
        <div class="chart-header">
          <h2 class="chart-title">Valuation History</h2>
          <p class="text-xs text-muted">Estimated value compared to purchase price baseline</p>
        </div>
        
        <div class="chart-wrap">
          <div v-if="loadingHistory" class="skeleton" style="height: 100%; min-height: 300px; border-radius: var(--radius-md);" />
          <PropertyValueChart v-else :history="historyData" :original-price="store.properties[0].original_price" />
        </div>
      </div>
    </div>

    <!-- Add / Edit Property Modal -->
    <AddPropertyModal
      v-model="showAdd"
      :property="editingProperty"
      @saved="onSaved"
      @delete="onDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMortgageStore } from '@/stores/mortgage'
import { api, type Property, type PropertyValueAuditLog } from '@/api/client'
import MortgageCard from '@/components/property/MortgageCard.vue'
import AddPropertyModal from '@/components/property/AddPropertyModal.vue'
import PropertyValueChart from '@/components/property/PropertyValueChart.vue'

const store = useMortgageStore()

const showAdd = ref(false)
const editingProperty = ref<Property | null>(null)
const historyData = ref<PropertyValueAuditLog[]>([])
const loadingHistory = ref(false)

function fmt(v: number) {
  return v.toLocaleString('en-GB', { minimumFractionDigits: 2 })
}

function openAdd() {
  editingProperty.value = null
  showAdd.value = true
}

function openEdit(p: Property) {
  editingProperty.value = p
  showAdd.value = true
}

async function loadHistoryForProperties() {
  if (store.properties.length > 0) {
    loadingHistory.value = true
    try {
      const pId = store.properties[0].id
      historyData.value = await api.properties.valueHistory(pId)
    } catch (err) {
      console.error(err)
    } finally {
      loadingHistory.value = false
    }
  }
}

async function onPropertyUpdated() {
  await store.fetchAll()
  await loadHistoryForProperties()
}

async function onSaved(form: any) {
  try {
    if (editingProperty.value) {
      await store.updatePropertyMeta(editingProperty.value.id, {
        name: form.name,
        property_address: form.property_address,
        original_price: form.original_price,
        ownership_percent: form.ownership_percent,
        notes: form.notes,
      })
      editingProperty.value = null
    } else {
      await store.createProperty({
        name: form.name,
        property_address: form.property_address,
        original_price: form.original_price,
        property_value: form.property_value,
        ownership_percent: form.ownership_percent,
        notes: form.notes,
      })
    }
    await onPropertyUpdated()
  } catch (err: any) {
    alert(err.message)
  }
}

async function onDelete() {
  if (!editingProperty.value) return
  if (confirm(`Are you sure you want to remove "${editingProperty.value.name}"? This will delete the property and all its mortgage parts.`)) {
    try {
      await store.deleteProperty(editingProperty.value.id)
      showAdd.value = false
      editingProperty.value = null
      await onPropertyUpdated()
    } catch (err: any) {
      alert(err.message)
    }
  }
}

onMounted(async () => {
  await store.fetchAll()
  await loadHistoryForProperties()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-8);
  flex-wrap: wrap;
  gap: var(--space-4);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}

.summary-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.summary-card { overflow: hidden; }
.summary-label { margin-bottom: var(--space-2); }
.summary-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.equity-card  { border-color: rgba(34, 197, 94, 0.3); }
.negative-card { border-color: rgba(239, 68, 68, 0.2); }
.positive-text { color: var(--positive); }
.negative-text { color: var(--negative); }

.loading-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(720px, 1fr));
  gap: var(--space-4);
}

/* Property Dashboard Grid */
.property-dashboard-grid {
  display: grid;
  grid-template-columns: 1.2fr 2fr;
  gap: var(--space-4);
  align-items: stretch;
}
.property-details-col {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.property-chart-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  height: 100%;
}
.chart-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.chart-title {
  font-size: var(--font-size-base);
  font-weight: 600;
}
.chart-wrap {
  flex: 1;
  min-height: 300px;
  position: relative;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-12);
  text-align: center;
}
.empty-icon { font-size: 3rem; }

@media (max-width: 1400px) {
  .property-dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid { grid-template-columns: 1fr; }
}
</style>
