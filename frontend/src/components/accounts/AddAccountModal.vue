<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <Transition name="slide-up">
          <div v-if="modelValue" class="modal modal-wide">
            <div class="modal-header">
              <h2 class="text-lg font-semibold">{{ isEdit ? 'Edit Account' : 'Add Account' }}</h2>
              <button class="btn btn-icon btn-ghost" @click="close">✕</button>
            </div>

            <div class="modal-body">
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="acc-name">Account Name *</label>
                  <input id="acc-name" v-model="form.name" type="text" class="form-input" placeholder="e.g. Vanguard S&S ISA" />
                </div>
                <div class="form-group">
                  <label class="form-label" for="acc-provider">Provider</label>
                  <input id="acc-provider" v-model="form.provider" type="text" class="form-input" placeholder="e.g. Vanguard" />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="acc-type">Account Type *</label>
                  <select id="acc-type" v-model="form.account_type" class="form-select">
                    <option value="">Select type…</option>
                    <optgroup label="ISA & Tax Wrappers">
                      <option value="SS_ISA">Stocks &amp; Shares ISA</option>
                      <option value="CASH_ISA">Cash ISA</option>
                      <option value="LISA">Lifetime ISA (LISA)</option>
                      <option value="ISA">Other ISA</option>
                    </optgroup>
                    <optgroup label="Pensions">
                      <option value="SIPP">SIPP</option>
                      <option value="WORKPLACE_PENSION">Workplace Pension</option>
                    </optgroup>
                    <optgroup label="Investments">
                      <option value="GIA">GIA (General Investment)</option>
                    </optgroup>
                    <optgroup label="Savings">
                      <option value="SAVINGS">Savings Account</option>
                      <option value="PREMIUM_BONDS">Premium Bonds</option>
                      <option value="FIXED_BOND">Fixed-Term Bond</option>
                      <option value="CURRENT">Current Account</option>
                    </optgroup>
                    <option value="OTHER">Other</option>
                  </select>
                </div>

                <div class="form-group">
                  <label class="form-label" for="acc-category">Category *</label>
                  <select id="acc-category" v-model="form.category" class="form-select">
                    <option value="">Select category…</option>
                    <option value="INVESTMENTS">📈 Investments</option>
                    <option value="RETIREMENT">🏦 Retirement</option>
                    <option value="SAVINGS">💰 Savings</option>
                  </select>
                </div>
              </div>

              <div v-if="!isEdit" class="form-group">
                <label class="form-label" for="acc-value">Current Value (£)</label>
                <input id="acc-value" v-model.number="form.current_value" type="number" min="0" step="0.01" class="form-input" placeholder="0.00" />
              </div>

              <!-- Initial Investment — only for Investments / Retirement -->
              <Transition name="slide-up">
                <div v-if="showInitialInvestment" class="form-group initial-investment-field">
                  <label class="form-label" for="acc-initial">
                    Initial Investment (£)
                    <span class="field-hint">Used to calculate profit/loss</span>
                  </label>
                  <input
                    id="acc-initial"
                    v-model.number="form.initial_investment"
                    type="number"
                    min="0"
                    step="0.01"
                    class="form-input"
                    placeholder="e.g. 5000.00"
                  />
                  <div v-if="profitPreview !== null" class="profit-preview" :class="profitPreview >= 0 ? 'positive' : 'negative'">
                    <span>{{ profitPreview >= 0 ? '▲ Profit' : '▼ Loss' }}:</span>
                    <span class="font-semibold">
                      {{ profitPreview >= 0 ? '+' : '' }}£{{ Math.abs(form.current_value - (form.initial_investment ?? 0)).toLocaleString('en-GB', { minimumFractionDigits: 2 }) }}
                    </span>
                    <span>({{ profitPreview >= 0 ? '+' : '' }}{{ profitPreview.toFixed(2) }}%)</span>
                  </div>
                </div>
              </Transition>

              <div class="form-group">
                <label class="form-label" for="acc-notes">Notes</label>
                <textarea id="acc-notes" v-model="form.notes" class="form-textarea" rows="2" placeholder="Optional notes…" />
              </div>
            </div>

            <div class="modal-footer">
              <button v-if="isEdit" class="btn btn-danger mr-auto" @click="$emit('delete')">Delete Account</button>
              <button class="btn btn-secondary" @click="close">Cancel</button>
              <button class="btn btn-primary" :disabled="!isValid || saving" @click="save">
                {{ saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Account' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Account } from '@/api/client'

const props = defineProps<{
  modelValue: boolean
  account?: Account | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  saved: [form: any]
  delete: []
}>()

const isEdit = computed(() => !!props.account)
const saving = ref(false)

const defaultForm = () => ({
  name: '',
  account_type: '',
  category: '',
  provider: '',
  current_value: 0,
  initial_investment: null as number | null,
  notes: '',
})

const form = ref(defaultForm())

const showInitialInvestment = computed(() =>
  ['INVESTMENTS', 'RETIREMENT'].includes(form.value.category)
)

const profitPreview = computed(() => {
  if (!showInitialInvestment.value) return null
  const init = form.value.initial_investment
  if (init === null || init <= 0) return null
  return ((form.value.current_value - init) / init) * 100
})

// Clear initial_investment when switching to SAVINGS
watch(() => form.value.category, (cat) => {
  if (!['INVESTMENTS', 'RETIREMENT'].includes(cat)) {
    form.value.initial_investment = null
  }
})

watch(() => props.account, (a) => {
  if (a) {
    form.value = {
      ...defaultForm(),
      ...a,
      provider: a.provider ?? '',
      notes: a.notes ?? '',
      initial_investment: a.initial_investment ?? null,
    }
  } else {
    form.value = defaultForm()
  }
}, { immediate: true })

const isValid = computed(() => form.value.name && form.value.account_type && form.value.category)

function close() { emit('update:modelValue', false) }

async function save() {
  if (!isValid.value) return
  saving.value = true
  try {
    emit('saved', {
      ...form.value,
      provider: form.value.provider || undefined,
      notes: form.value.notes || undefined,
      initial_investment: showInitialInvestment.value ? (form.value.initial_investment ?? undefined) : undefined,
    })
    close()
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-wide { max-width: 600px; }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.form-textarea { resize: vertical; min-height: 70px; }

.mr-auto { margin-right: auto; }

.initial-investment-field {
  background: var(--bg-base);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
}

.field-hint {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  font-weight: 400;
  margin-left: var(--space-2);
}

.profit-preview {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
}
.profit-preview.positive { background: var(--positive-bg); color: var(--positive); }
.profit-preview.negative { background: var(--negative-bg); color: var(--negative); }

@media (max-width: 520px) {
  .form-row { grid-template-columns: 1fr; }
}
</style>
