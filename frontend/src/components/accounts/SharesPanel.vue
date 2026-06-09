<template>
  <div class="shares-panel">
    <!-- Compact Summary (Inside the Card) -->
    <div class="summary-box">
      <div class="summary-top">
        <span class="summary-title text-xs font-semibold text-muted uppercase tracking-wider">📊 Holdings Summary</span>
        <button class="btn btn-xs btn-outline manage-btn" @click="showModal = true">
          ⚙️ Manage
        </button>
      </div>

      <div v-if="holdings.length === 0" class="empty-summary text-xs text-muted">
        No holdings tracked yet.
        <button class="btn btn-link btn-xs inline-add-link" @click="openManageAndAdd">
          + Add holdings
        </button>
      </div>

      <div v-else class="summary-details">
        <!-- Totals & P&L -->
        <div v-if="portfolio" class="summary-stats">
          <div class="stat-item">
            <span class="stat-lbl text-xs text-muted">Value:</span>
            <span class="stat-val font-semibold text-sm">£{{ fmtGbp(portfolio.total_live_value_gbp ?? 0) }}</span>
          </div>
          <div class="stat-item" v-if="portfolio.total_pnl_percent !== null">
            <span class="stat-lbl text-xs text-muted">PnL:</span>
            <span class="stat-val font-semibold text-sm" :class="portfolio.total_pnl_percent >= 0 ? 'pnl-pos' : 'pnl-neg'">
              {{ portfolio.total_pnl_percent >= 0 ? '+' : '' }}{{ portfolio.total_pnl_percent.toFixed(2) }}%
            </span>
          </div>
        </div>

        <!-- Chips of Tickers -->
        <div class="ticker-chips">
          <span
            v-for="h in displayHoldings"
            :key="h.id"
            class="summary-chip"
            :class="[currencyClass(h.currency), { 'stale-chip': h.is_stale }]"
            :title="`${h.short_name || h.display_name || ''} - ${h.quantity} shares`"
          >
            {{ h.ticker }} <span class="qty-sub">({{ h.quantity }})</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Modal Dialog for managing holdings -->
    <teleport to="body">
      <transition name="modal-fade">
        <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
          <div class="modal-container">
            <!-- Modal Header -->
            <div class="modal-header">
              <div class="modal-header-title">
                <span class="modal-icon">📊</span>
                <h3>Manage Holdings — {{ accountName || 'Account' }}</h3>
              </div>
              <button class="modal-close-btn" @click="showModal = false">✕</button>
            </div>

            <!-- Modal Content -->
            <div class="modal-body">
              <!-- Actions Row -->
              <div class="modal-actions-row">
                <button class="btn btn-sm btn-primary" @click="showAddForm = !showAddForm">
                  {{ showAddForm ? '✕ Close Add Form' : '➕ Add New Holding' }}
                </button>
                <div class="modal-secondary-actions">
                  <button
                    class="btn btn-sm btn-secondary"
                    @click="handleRefresh"
                    :disabled="isLoading || holdings.length === 0"
                    title="Refresh prices for this account"
                  >
                    <span v-if="isLoading" class="spinner" />
                    <span v-else>⟳ Refresh Prices</span>
                  </button>
                  <button
                    v-if="portfolio && portfolio.total_live_value_gbp !== null"
                    class="btn btn-sm btn-accent"
                    @click="syncAccountValue"
                    :disabled="syncing"
                    :title="`Set account value to £${fmtGbp(portfolio.total_live_value_gbp)}`"
                  >
                    <span v-if="syncing" class="spinner" />
                    <span v-else>💾 Sync Balance</span>
                  </button>
                </div>
              </div>

              <!-- Add Holding Form (Inside Modal) -->
              <transition name="slide">
                <div v-if="showAddForm" class="add-form">
                  <div class="form-row">
                    <div class="form-field">
                      <label class="field-label">Ticker *</label>
                      <input
                        v-model="form.ticker"
                        class="field-input ticker-input"
                        placeholder="e.g. JPM, TROW, HSBA.L"
                        @input="form.ticker = form.ticker.toUpperCase()"
                      />
                    </div>
                    <div class="form-field">
                      <label class="field-label">Name (optional)</label>
                      <input v-model="form.display_name" class="field-input" placeholder="e.g. JPMorgan Chase" />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-field">
                      <label class="field-label">Quantity *</label>
                      <input v-model.number="form.quantity" type="number" min="0" step="any" class="field-input" placeholder="10" />
                    </div>
                    <div class="form-field">
                      <label class="field-label">Avg Cost / Share</label>
                      <input v-model.number="form.avg_cost" type="number" min="0" step="any" class="field-input" placeholder="200.00" />
                    </div>
                  </div>
                  <div class="form-row">
                    <div class="form-field form-field-full">
                      <label class="field-label">Notes (optional)</label>
                      <input v-model="form.notes" class="field-input" placeholder="Optional note" />
                    </div>
                  </div>
                  <div class="form-footer">
                    <span v-if="addError" class="text-xs text-negative">{{ addError }}</span>
                    <button class="btn btn-sm btn-primary" @click="addHolding" :disabled="adding">
                      <span v-if="adding" class="spinner" />
                      <span v-else>Add Holding</span>
                    </button>
                  </div>
                </div>
              </transition>

              <!-- Error Banner -->
              <div v-if="localError" class="error-banner text-xs">⚠️ {{ localError }}</div>

              <!-- Empty State -->
              <div v-if="holdings.length === 0 && !showAddForm" class="empty-state text-sm text-muted">
                No holdings yet. Click <strong>➕ Add New Holding</strong> above to start tracking.
              </div>

              <!-- Holdings Table (Inside Modal) -->
              <div v-if="holdings.length > 0" class="holdings-table-container">
                <div class="holdings-table">
                  <div class="table-head">
                    <span>Ticker</span>
                    <span>Qty</span>
                    <span>Avg Cost</span>
                    <span>Live Price</span>
                    <span>Live Value</span>
                    <span>P&amp;L</span>
                    <span>Today</span>
                    <span class="cell-actions-header">Actions</span>
                  </div>

                  <div
                    v-for="h in displayHoldings"
                    :key="h.id"
                    class="table-row"
                    :class="{ 'row-error': !!h.price_error && !h.is_stale, 'row-editing': editingId === h.id, 'row-stale': h.is_stale }"
                  >
                    <!-- Ticker + name + error -->
                    <div class="cell-ticker">
                      <template v-if="editingId === h.id">
                        <input v-model="editForm.ticker" type="text" class="edit-input ticker-input" placeholder="Ticker" />
                        <input v-model="editForm.display_name" type="text" class="edit-input name-input text-xs" placeholder="Friendly Name" />
                      </template>
                      <template v-else>
                        <div class="ticker-top">
                          <span class="ticker-badge" :class="currencyClass(h.currency)">{{ h.ticker }}</span>
                          <span v-if="h.is_stale" class="stale-badge" :title="`Last fetched: ${fmtDateTime(h.last_price_at)}`">STALE</span>
                        </div>
                        <span class="ticker-name text-xs text-muted">{{ h.short_name || h.display_name || '' }}</span>
                        <span v-if="h.price_error && !h.is_stale" class="ticker-error text-xs">⚠ {{ h.price_error }}</span>
                        <span v-if="h.is_stale && h.last_price_at" class="ticker-stale-info text-xs">as of {{ fmtDateTime(h.last_price_at) }}</span>
                      </template>
                    </div>

                    <!-- Quantity -->
                    <div class="cell-num">
                      <template v-if="editingId === h.id">
                        <input v-model.number="editForm.quantity" type="number" min="0" step="any" class="edit-input" />
                      </template>
                      <template v-else>{{ h.quantity }}</template>
                    </div>

                    <!-- Average Cost -->
                    <div class="cell-num">
                      <template v-if="editingId === h.id">
                        <input v-model.number="editForm.avg_cost" type="number" min="0" step="any" class="edit-input" />
                      </template>
                      <template v-else-if="h.avg_cost != null">
                        <span :class="{ 'stale-value': h.is_stale }">{{ fmtNative(h.avg_cost, h.currency) }}</span>
                        <span class="currency-tag text-xs text-muted">{{ h.currency }}</span>
                      </template>
                      <template v-else>—</template>
                    </div>

                    <!-- Live Price -->
                    <div class="cell-num">
                      <template v-if="h.live_price != null">
                        <span class="live-price" :class="{ 'stale-value': h.is_stale }">{{ fmtNative(h.live_price, h.currency) }}</span>
                        <span class="currency-tag text-xs text-muted">{{ h.currency }}</span>
                      </template>
                      <template v-else-if="isLoading">
                        <span class="skeleton-inline" />
                      </template>
                      <template v-else>—</template>
                    </div>

                    <!-- Live Value (GBP) -->
                    <div class="cell-num">
                      <template v-if="h.live_value_gbp != null">
                        <span class="value-gbp font-semibold" :class="{ 'stale-value': h.is_stale }">£{{ fmtGbp(h.live_value_gbp) }}</span>
                      </template>
                      <template v-else-if="isLoading"><span class="skeleton-inline" /></template>
                      <template v-else>—</template>
                    </div>

                    <!-- P&L -->
                    <div class="cell-num">
                      <template v-if="h.pnl_percent != null">
                        <span class="pnl" :class="[h.pnl_percent! >= 0 ? 'pnl-pos' : 'pnl-neg', { 'stale-value': h.is_stale }]">
                          {{ h.pnl_percent! >= 0 ? '+' : '' }}{{ h.pnl_percent!.toFixed(2) }}%
                        </span>
                      </template>
                      <template v-else>—</template>
                    </div>

                    <!-- Day change -->
                    <div class="cell-num">
                      <template v-if="h.day_change_pct != null">
                        <span class="pnl" :class="h.day_change_pct! >= 0 ? 'pnl-pos' : 'pnl-neg'">
                          {{ h.day_change_pct! >= 0 ? '+' : '' }}{{ h.day_change_pct!.toFixed(2) }}%
                        </span>
                      </template>
                      <template v-else>—</template>
                    </div>

                    <!-- Actions -->
                    <div class="cell-actions">
                      <template v-if="editingId === h.id">
                        <button class="icon-btn text-positive" @click="saveEdit(h.id)" title="Save">✓</button>
                        <button class="icon-btn text-muted" @click="editingId = null" title="Cancel">✕</button>
                      </template>
                      <template v-else>
                        <button class="icon-btn text-muted" @click="startEdit(h)" title="Edit holding">✎</button>
                        <button class="icon-btn text-negative" @click="removeHolding(h.id)" title="Remove">✕</button>
                      </template>
                    </div>
                  </div>
                </div>

                <!-- Portfolio Totals Row -->
                <div v-if="portfolio" class="totals-row">
                  <span class="totals-label text-xs text-muted">Portfolio Total</span>
                  <span class="totals-value font-bold">£{{ fmtGbp(portfolio.total_live_value_gbp ?? 0) }}</span>
                  <span v-if="portfolio.total_pnl_percent !== null" class="pnl" :class="portfolio.total_pnl_percent >= 0 ? 'pnl-pos' : 'pnl-neg'">
                    {{ portfolio.total_pnl_percent >= 0 ? '+' : '' }}{{ portfolio.total_pnl_percent.toFixed(2) }}% overall
                  </span>
                </div>
              </div>
            </div>

            <!-- Modal Footer -->
            <div v-if="portfolio" class="modal-footer">
              <span v-if="portfolio.gbpusd_rate">GBP/USD: {{ portfolio.gbpusd_rate.toFixed(4) }} · </span>
              <span>Refreshed {{ refreshedAt }}</span>
            </div>
          </div>
        </div>
      </transition>
    </teleport>

    <ConfirmModal
      v-model="showDeleteConfirm"
      title="Remove Holding"
      message="Are you sure you want to remove this stock holding?"
      confirmText="Remove"
      @confirm="executeDeleteHolding"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api, type ShareHolding, type LiveHolding, type PortfolioLive } from '@/api/client'
import { useSharesStore } from '@/stores/shares'
import ConfirmModal from '@/components/layout/ConfirmModal.vue'

const props = defineProps<{ 
  accountId: number
  accountName?: string
}>()
const emit  = defineEmits<{ synced: [newValue: number] }>()

const sharesStore = useSharesStore()

// Local state
const holdings    = ref<ShareHolding[]>([])
const syncing     = ref(false)
const showAddForm = ref(false)
const adding      = ref(false)
const addError    = ref<string | null>(null)
const localError  = ref<string | null>(null)
const editingId   = ref<number | null>(null)
const editForm    = ref({ ticker: '', display_name: '', quantity: 0, avg_cost: 0 })
const form        = ref({ ticker: '', display_name: '', quantity: null as number | null, avg_cost: null as number | null, notes: '' })
const showModal   = ref(false)
const showDeleteConfirm = ref(false)
const pendingDeleteId = ref<number | null>(null)

// Portfolio comes from the store (shared with global refresh)
const portfolio = computed<PortfolioLive | null>(() => sharesStore.portfolios[props.accountId] ?? null)
const isLoading = computed(() => sharesStore.loading)

// Merge holdings list with live data
const displayHoldings = computed((): (ShareHolding & Partial<LiveHolding>)[] => {
  if (!portfolio.value) return holdings.value
  const liveMap = Object.fromEntries(portfolio.value.holdings.map(h => [h.id, h]))
  return holdings.value.map(h => ({ ...h, ...liveMap[h.id] }))
})

const now = ref(new Date())
let relativeTimer: any = null

onMounted(() => {
  relativeTimer = setInterval(() => {
    now.value = new Date()
  }, 10000)
})

onUnmounted(() => {
  if (relativeTimer) clearInterval(relativeTimer)
})

const refreshedAt = computed(() => {
  const d = sharesStore.lastRefreshedAt
  if (!d) return ''
  const diffMs = now.value.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const timeStr = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  if (diffMins < 1) {
    return `${timeStr} (just now)`
  }
  return `${timeStr} (${diffMins}m ago)`
})

// Fetch the holdings list (cheap — no prices)
async function fetchHoldings() {
  try {
    holdings.value = await api.shares.list(props.accountId)
  } catch (e: any) {
    localError.value = e.message
  }
}

// Individual account refresh
async function handleRefresh() {
  localError.value = null
  try {
    await sharesStore.refreshAccount(props.accountId)
    if (portfolio.value?.total_live_value_gbp != null) {
      emit('synced', portfolio.value.total_live_value_gbp)
    }
  } catch (e: any) {
    localError.value = e.message
  }
}

// Add new holding
async function addHolding() {
  addError.value = null
  if (!form.value.ticker.trim()) { addError.value = 'Ticker is required'; return }
  if (!form.value.quantity || form.value.quantity <= 0) { addError.value = 'Quantity must be > 0'; return }

  adding.value = true
  try {
    const h = await api.shares.create(props.accountId, {
      ticker: form.value.ticker.trim(),
      display_name: form.value.display_name || undefined,
      quantity: form.value.quantity,
      avg_cost: form.value.avg_cost ?? undefined,
      notes: form.value.notes || undefined,
    })
    holdings.value.push(h)
    form.value = { ticker: '', display_name: '', quantity: null, avg_cost: null, notes: '' }
    showAddForm.value = false
    sharesStore.invalidateAccount(props.accountId)
    await sharesStore.refreshAccount(props.accountId)
    if (portfolio.value?.total_live_value_gbp != null) {
      emit('synced', portfolio.value.total_live_value_gbp)
    }
  } catch (e: any) {
    addError.value = e.message
  } finally {
    adding.value = false
  }
}

// Inline edit
function startEdit(h: ShareHolding & Partial<LiveHolding>) {
  editingId.value = h.id
  editForm.value  = {
    ticker: h.ticker,
    display_name: h.display_name || '',
    quantity: h.quantity,
    avg_cost: h.avg_cost ?? 0
  }
}

async function saveEdit(holdingId: number) {
  try {
    const updated = await api.shares.update(holdingId, {
      ticker: editForm.value.ticker.trim() || undefined,
      display_name: editForm.value.display_name.trim() || '',
      quantity: editForm.value.quantity,
      avg_cost: editForm.value.avg_cost || undefined,
    })
    const idx = holdings.value.findIndex(h => h.id === holdingId)
    if (idx !== -1) holdings.value[idx] = updated
    editingId.value = null
    await sharesStore.refreshAccount(props.accountId)
    if (portfolio.value?.total_live_value_gbp != null) {
      emit('synced', portfolio.value.total_live_value_gbp)
    }
  } catch (e: any) {
    localError.value = e.message
  }
}

// Remove holding
function removeHolding(holdingId: number) {
  pendingDeleteId.value = holdingId
  showDeleteConfirm.value = true
}

async function executeDeleteHolding() {
  if (pendingDeleteId.value === null) return
  const holdingId = pendingDeleteId.value
  pendingDeleteId.value = null
  try {
    await api.shares.delete(holdingId)
    holdings.value = holdings.value.filter(h => h.id !== holdingId)
    sharesStore.invalidateAccount(props.accountId)
    if (holdings.value.length > 0) {
      await sharesStore.refreshAccount(props.accountId)
      if (portfolio.value?.total_live_value_gbp != null) {
        emit('synced', portfolio.value.total_live_value_gbp)
      }
    } else {
      emit('synced', 0)
    }
  } catch (e: any) {
    localError.value = e.message
  }
}

// Sync account value
async function syncAccountValue() {
  syncing.value    = true
  localError.value = null
  try {
    const result = await api.shares.sync(props.accountId)
    emit('synced', result.new_value)
  } catch (e: any) {
    localError.value = `Sync failed: ${e.message}`
  } finally {
    syncing.value = false
  }
}

function openManageAndAdd() {
  showModal.value = true
  showAddForm.value = true
}

// Formatting
function fmtGbp(v: number | null | undefined) {
  if (v == null) return '—'
  return v.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtNative(price: number | undefined, currency: string | null | undefined) {
  if (price == null) return '—'
  const divisor = currency === 'GBX' ? 100 : 1
  return (price / divisor).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtDateTime(iso: string | null | undefined) {
  if (!iso) return ''
  return new Date(iso + (iso.endsWith('Z') ? '' : 'Z')).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}
function currencyClass(currency: string | null | undefined) {
  if (!currency) return ''
  if (currency === 'USD') return 'ticker-usd'
  if (currency === 'GBP' || currency === 'GBX') return 'ticker-gbp'
  return 'ticker-other'
}

onMounted(async () => {
  await fetchHoldings()
  if (holdings.value.length > 0 && !portfolio.value) {
    await sharesStore.refreshAccount(props.accountId)
  }
})
</script>

<style scoped>
.shares-panel {
  border-top: 1px solid var(--bg-border);
  padding-top: var(--space-3);
  margin-top: var(--space-2);
}

/* ── Inline Summary Box ──────────────────────────────────────────────────────── */
.summary-box {
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.summary-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-title {
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  letter-spacing: 0.05em;
  font-weight: 600;
}

.manage-btn {
  padding: 2px 8px;
  font-size: var(--font-size-xs);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
  border: 1px solid var(--bg-border);
  background: transparent;
  cursor: pointer;
  transition: all 0.15s ease;
}
.manage-btn:hover {
  background: var(--bg-surface);
  color: var(--text-primary);
  border-color: var(--text-secondary);
}

.empty-summary {
  padding: var(--space-1) 0;
  font-size: var(--font-size-xs);
}

.inline-add-link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-left: 4px;
}
.inline-add-link:hover {
  text-decoration: underline;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.summary-stats {
  display: flex;
  gap: var(--space-4);
  align-items: center;
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.stat-lbl {
  color: var(--text-muted);
}

.stat-val {
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.ticker-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.summary-chip {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--bg-border);
  letter-spacing: 0.02em;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  transition: all 0.15s;
}

.qty-sub {
  font-weight: 500;
  opacity: 0.8;
}

.ticker-usd   { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.ticker-gbp   { background: rgba(52, 211, 153, 0.1); border-color: rgba(52, 211, 153, 0.2); color: #34d399; }
.ticker-other { background: var(--bg-elevated); border-color: var(--bg-border); color: var(--text-secondary); }
.stale-chip   { border-color: rgba(251,191,36,0.3); background: rgba(251,191,36,0.05); color: #fbbf24; }

/* ── Modal Dialog ───────────────────────────────────────────────────────────── */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-container {
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 850px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.modal-header {
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--bg-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-surface-2);
}

.modal-header-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.modal-icon {
  font-size: 1.25rem;
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: 700;
  color: var(--text-primary);
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s;
}
.modal-close-btn:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  background: var(--bg-surface);
}

.modal-actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  padding-bottom: var(--space-1);
}

.modal-secondary-actions {
  display: flex;
  gap: var(--space-2);
}

.btn-accent {
  background: var(--accent);
  color: white;
  border: none;
}
.btn-accent:hover:not(:disabled) {
  opacity: 0.9;
}

/* Forms inside modal */
.add-form {
  background: var(--bg-surface-2);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field-full {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-input {
  background: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  width: 100%;
  box-sizing: border-box;
}
.field-input:focus {
  outline: none;
  border-color: var(--accent);
}

.ticker-input {
  text-transform: uppercase;
  font-weight: 700;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-3);
}

.error-banner {
  background: var(--negative-bg);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: var(--negative);
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-3);
}

/* Modal Table formatting */
.holdings-table-container {
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.holdings-table {
  display: flex;
  flex-direction: column;
  background: var(--bg-surface-2);
}

.table-head {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 1fr 1fr 1.2fr 1fr 1fr 0.8fr;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid var(--bg-border);
  background: var(--bg-elevated);
}

.cell-actions-header {
  text-align: right;
}

.table-row {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 1fr 1fr 1.2fr 1fr 1fr 0.8fr;
  gap: var(--space-2);
  align-items: center;
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--bg-border);
  transition: background var(--transition-fast);
  background: var(--bg-surface);
}
.table-row:last-child {
  border-bottom: none;
}
.table-row:hover {
  background: var(--bg-surface-2);
}

.row-error { opacity: 0.75; }
.row-editing { background: var(--bg-surface-2); }
.row-stale { background: rgba(251, 191, 36, 0.02); }

.cell-ticker {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ticker-top {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.ticker-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.04em;
  width: fit-content;
}

.stale-badge {
  font-size: 8px;
  font-weight: 700;
  padding: 1px 3px;
  border-radius: var(--radius-sm);
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.25);
  cursor: help;
}

.ticker-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.ticker-error {
  color: var(--negative);
  font-size: 10px;
  margin-top: 2px;
}

.ticker-stale-info {
  color: #fbbf24;
  font-size: 10px;
  margin-top: 2px;
}

.cell-num {
  font-size: var(--font-size-sm);
  font-variant-numeric: tabular-nums;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.currency-tag {
  color: var(--text-muted);
  font-size: 9px;
}

.stale-value {
  opacity: 0.6;
}

.pnl {
  font-weight: 600;
}
.pnl-pos { color: var(--positive); }
.pnl-neg { color: var(--negative); }

.cell-actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: var(--font-size-sm);
  padding: 4px 6px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}
.icon-btn:hover {
  background: var(--bg-surface-2);
}

.text-positive { color: var(--positive); }
.text-negative { color: var(--negative); }

.edit-input {
  background: var(--bg-elevated);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  padding: var(--space-1) var(--space-2);
  width: 75px;
}
.ticker-input {
  width: 90px;
}
.name-input {
  width: 130px;
  margin-top: 4px;
}

.skeleton-inline {
  display: inline-block;
  width: 60px;
  height: 14px;
  background: var(--bg-elevated);
  border-radius: var(--radius-sm);
  animation: pulse 1.5s ease-in-out infinite;
}

.spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.totals-row {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 1fr 1fr 1.2fr 1fr 1fr 0.8fr;
  gap: var(--space-2);
  align-items: center;
  padding: var(--space-4) var(--space-4);
  background: var(--bg-elevated);
  font-weight: 700;
  border-top: 1px solid var(--bg-border);
}
.totals-label {
  grid-column: 1 / 5;
}

.modal-footer {
  padding: var(--space-3) var(--space-6);
  background: var(--bg-surface-2);
  border-top: 1px solid var(--bg-border);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  display: flex;
  justify-content: flex-end;
}

/* Animations */
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.25s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-active .modal-container,
.modal-fade-leave-active .modal-container {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-fade-enter-from .modal-container {
  transform: scale(0.96) translateY(10px);
}
.modal-fade-leave-to .modal-container {
  transform: scale(0.96) translateY(10px);
}

.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-8px); }

@keyframes spin { to { transform: rotate(360deg); } }
</style>
