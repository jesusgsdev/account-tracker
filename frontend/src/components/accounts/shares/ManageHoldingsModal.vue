<template>
  <!-- Modal Dialog for managing holdings -->
  <teleport to="body">
    <transition name="modal-fade">
      <div v-if="modelValue" class="modal-backdrop" @click.self="close">
        <div class="modal-container">
          <!-- Modal Header -->
          <div class="modal-header">
            <div class="modal-header-title">
              <span class="modal-icon">📊</span>
              <h3>Manage Holdings — {{ accountName || 'Account' }}</h3>
            </div>
            <button class="modal-close-btn" @click="close">✕</button>
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
                  @click="emit('refresh')"
                  :disabled="isLoading || holdings.length === 0"
                  title="Refresh prices for this account"
                >
                  <span v-if="isLoading" class="spinner" />
                  <span v-else>⟳ Refresh Prices</span>
                </button>
                <button
                  v-if="portfolio && portfolio.total_live_value_gbp !== null"
                  class="btn btn-sm btn-accent"
                  @click="emit('sync')"
                  :disabled="syncing"
                  :title="`Set account value to £${fmtGbp(portfolio.total_live_value_gbp)}`"
                >
                  <span v-if="syncing" class="spinner" />
                  <span v-else>💾 Sync Balance</span>
                </button>
              </div>
            </div>

            <!-- Add Holding Form -->
            <transition name="slide">
              <AddHoldingForm
                v-if="showAddForm"
                :form="form"
                :adding="adding"
                :error="addError"
                @submit="emit('add')"
              />
            </transition>

            <!-- Error Banner -->
            <WarningBanner v-if="localError" level="error">{{ localError }}</WarningBanner>

            <!-- Empty State -->
            <div v-if="holdings.length === 0 && !showAddForm" class="empty-state text-sm text-muted">
              No holdings yet. Click <strong>➕ Add New Holding</strong> above to start tracking.
            </div>

            <!-- Holdings Table -->
            <HoldingsTable
              v-if="holdings.length > 0"
              :holdings="displayHoldings"
              :portfolio="portfolio"
              :is-loading="isLoading"
              :editing-id="editingId"
              :edit-form="editForm"
              @edit="emit('edit', $event)"
              @save="emit('save', $event)"
              @cancel-edit="emit('cancel-edit')"
              @remove="emit('remove', $event)"
            />
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
</template>

<script setup lang="ts">
import type { ShareHolding, PortfolioLive } from '@/api/client'
import type { DisplayHolding, NewHoldingForm, EditHoldingForm } from '@/composables/useHoldingsManager'
import { fmtGbp } from '@/utils/holdings'
import WarningBanner from '@/components/common/WarningBanner.vue'
import AddHoldingForm from './AddHoldingForm.vue'
import HoldingsTable from './HoldingsTable.vue'

defineProps<{
  accountName?: string
  holdings: ShareHolding[]
  displayHoldings: DisplayHolding[]
  portfolio: PortfolioLive | null
  isLoading: boolean
  syncing: boolean
  adding: boolean
  addError: string | null
  localError: string | null
  editingId: number | null
  editForm: EditHoldingForm
  form: NewHoldingForm
  refreshedAt: string
}>()

const modelValue = defineModel<boolean>({ required: true })
const showAddForm = defineModel<boolean>('showAddForm', { required: true })

const emit = defineEmits<{
  refresh: []
  sync: []
  add: []
  edit: [holding: DisplayHolding]
  save: [id: number]
  'cancel-edit': []
  remove: [id: number]
}>()

function close() {
  modelValue.value = false
}
</script>

<style scoped>
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

.spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
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
