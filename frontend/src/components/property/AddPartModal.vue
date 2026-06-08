<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <Transition name="slide-up">
          <div v-if="modelValue" class="modal modal-wide">
            <div class="modal-header">
              <h2 class="text-lg font-semibold">{{ isEdit ? 'Edit Mortgage Part' : 'Add Mortgage Part' }}</h2>
              <button class="btn btn-icon btn-ghost" @click="close">✕</button>
            </div>

            <div class="modal-body">
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="part-name">Part Name *</label>
                  <input id="part-name" v-model="form.name" type="text" class="form-input" placeholder="e.g. Fixed Rate Part" />
                </div>
                <div class="form-group">
                  <label class="form-label" for="part-lender">Lender</label>
                  <input id="part-lender" v-model="form.lender" type="text" class="form-input" placeholder="e.g. Halifax" />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="part-balance">Outstanding Balance (£) *</label>
                  <input
                    id="part-balance"
                    v-model.number="form.outstanding_balance"
                    type="number"
                    min="0"
                    step="1"
                    class="form-input"
                    placeholder="e.g. 150000"
                    :disabled="isEdit"
                  />
                  <p v-if="isEdit" class="text-xs text-muted mt-1">Outstanding balance is updated using the "Update Balance" button.</p>
                </div>
                <div class="form-group">
                  <label class="form-label" for="part-rate">Interest Rate (% APR)</label>
                  <input id="part-rate" v-model.number="form.interest_rate" type="number" min="0" max="100" step="0.01" class="form-input" placeholder="e.g. 4.75" />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="part-type">Mortgage Type *</label>
                  <select id="part-type" v-model="form.mortgage_type" class="form-input">
                    <option value="REPAYMENT">Repayment (Capital & Interest)</option>
                    <option value="INTEREST_ONLY">Interest Only</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label" for="part-payment">Monthly Payment (£)</label>
                  <input id="part-payment" v-model.number="form.monthly_payment" type="number" min="0" step="1" class="form-input" placeholder="Optional" />
                </div>
              </div>

              <div class="section-divider">
                <span>Remaining Term</span>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="part-years">Years Left</label>
                  <input id="part-years" v-model.number="form.term_years" type="number" min="0" max="100" step="1" class="form-input" placeholder="e.g. 20" />
                </div>
                <div class="form-group">
                  <label class="form-label" for="part-months">Months Left</label>
                  <input id="part-months" v-model.number="form.term_months" type="number" min="0" max="11" step="1" class="form-input" placeholder="0-11" />
                </div>
              </div>

              <div class="form-group">
                <label class="form-label" for="part-notes">Notes</label>
                <textarea id="part-notes" v-model="form.notes" class="form-textarea" rows="2" placeholder="Optional notes about this mortgage tranche…" />
              </div>
            </div>

            <div class="modal-footer">
              <button v-if="isEdit" class="btn btn-danger mr-auto" @click="handleDelete">Delete Part</button>
              <button class="btn btn-secondary" @click="close">Cancel</button>
              <button class="btn btn-primary" :disabled="!isValid || saving" @click="save">
                {{ saving ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Mortgage Part' }}
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
import type { MortgagePart } from '@/api/client'
import { useMortgageStore } from '@/stores/mortgage'

const props = defineProps<{
  modelValue: boolean
  propertyId: number
  part?: MortgagePart | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  saved: []
}>()

const store = useMortgageStore()
const isEdit = computed(() => !!props.part)
const saving = ref(false)

const defaultForm = () => ({
  name: '',
  lender: '',
  outstanding_balance: 0,
  interest_rate: null as number | null,
  mortgage_type: 'REPAYMENT' as 'REPAYMENT' | 'INTEREST_ONLY',
  term_years: null as number | null,
  term_months: null as number | null,
  monthly_payment: null as number | null,
  notes: '',
})

const form = ref(defaultForm())

watch(() => props.part, (p) => {
  if (p) {
    form.value = {
      name: p.name,
      lender: p.lender ?? '',
      outstanding_balance: p.outstanding_balance,
      interest_rate: p.interest_rate ?? null,
      mortgage_type: p.mortgage_type,
      term_years: p.term_years ?? null,
      term_months: p.term_months ?? null,
      monthly_payment: p.monthly_payment ?? null,
      notes: p.notes ?? '',
    }
  } else {
    form.value = defaultForm()
  }
}, { immediate: true })

const isValid = computed(() =>
  form.value.name.trim().length > 0 &&
  form.value.outstanding_balance >= 0 &&
  (form.value.term_months === null || (form.value.term_months >= 0 && form.value.term_months <= 11))
)

function close() {
  emit('update:modelValue', false)
}

async function save() {
  if (!isValid.value) return
  saving.value = true
  try {
    const payload = {
      name: form.value.name,
      lender: form.value.lender || undefined,
      outstanding_balance: form.value.outstanding_balance,
      interest_rate: form.value.interest_rate ?? undefined,
      mortgage_type: form.value.mortgage_type,
      term_years: form.value.term_years ?? undefined,
      term_months: form.value.term_months ?? undefined,
      monthly_payment: form.value.monthly_payment ?? undefined,
      notes: form.value.notes || undefined,
    }

    if (isEdit.value && props.part) {
      await store.updatePartMeta(props.propertyId, props.part.id, payload)
    } else {
      await store.createPart(props.propertyId, payload)
    }
    emit('saved')
    close()
  } catch (err: any) {
    alert(err.message)
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!props.part) return
  if (confirm(`Are you sure you want to delete mortgage part "${props.part.name}"?`)) {
    saving.value = true
    try {
      await store.deletePart(props.propertyId, props.part.id)
      emit('saved')
      close()
    } catch (err: any) {
      alert(err.message)
    } finally {
      saving.value = false
    }
  }
}
</script>

<style scoped>
.modal-wide {
  max-width: 620px;
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}
.section-divider {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin: var(--space-2) 0 0;
}
.section-divider::before,
.section-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--bg-border);
}
.form-textarea {
  resize: vertical;
  min-height: 60px;
}
.mr-auto {
  margin-right: auto;
}
.mt-1 {
  margin-top: 4px;
}
@media (max-width: 520px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
