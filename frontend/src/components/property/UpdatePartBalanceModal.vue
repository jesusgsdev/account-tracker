<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <Transition name="slide-up">
          <div v-if="modelValue" class="modal">
            <div class="modal-header">
              <div>
                <h2 class="text-lg font-semibold">Update Mortgage Balance</h2>
                <p class="text-sm text-muted">{{ propertyName }} — {{ part?.name }}</p>
              </div>
              <button class="btn btn-icon btn-ghost" @click="close">✕</button>
            </div>

            <div class="modal-body">
              <div class="current-display">
                <span class="text-sm text-muted">Current Balance</span>
                <span class="text-2xl font-bold">-£{{ currentFormatted }}</span>
              </div>

              <div class="form-group">
                <label class="form-label" for="new-balance">New Outstanding Balance (£)</label>
                <input
                  id="new-balance"
                  v-model.number="newValue"
                  type="number"
                  min="0"
                  step="1"
                  class="form-input value-input"
                  placeholder="0"
                  autofocus
                />
              </div>

              <div v-if="changeAmount !== null" class="change-preview" :class="previewClass">
                <span>{{ changeAmount < 0 ? '▼ Paid off' : '▲ Increased' }}</span>
                <span class="font-semibold">
                  {{ changeAmount >= 0 ? '+' : '' }}{{ formatGBP(Math.abs(changeAmount), { decimals: 0 }) }}
                </span>
                <span v-if="equityImpact !== null" class="equity-impact">
                  Equity {{ equityImpact >= 0 ? '▲' : '▼' }} {{ formatGBP(Math.abs(equityImpact), { decimals: 0 }) }}
                </span>
              </div>

              <div class="form-group">
                <label class="form-label" for="bal-note">Note (optional)</label>
                <input id="bal-note" v-model="note" type="text" class="form-input" placeholder="e.g. Monthly repayment, Lump sum payment" />
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="close">Cancel</button>
              <button class="btn btn-primary" :disabled="newValue === null || newValue < 0 || saving" @click="save">
                {{ saving ? 'Saving…' : 'Update Balance' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { formatGBP } from '@/utils/format'
import { toRef } from 'vue'
import { useToast } from '@/composables/useToast'
import { apiErrorMessage } from '@/api/client'
import { useModalKeys } from '@/composables/useModalKeys'
import { ref, computed, watch } from 'vue'
import type { MortgagePart } from '@/api/client'
import { useMortgageStore } from '@/stores/mortgage'

const props = defineProps<{
  modelValue: boolean
  propertyId: number
  propertyName: string
  part: MortgagePart | null
  ownershipPercent: number
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  saved: []
}>()

const store = useMortgageStore()
const newValue = ref<number | null>(null)
const note = ref('')
const saving = ref(false)

watch(() => props.part, (p) => {
  if (p) {
    newValue.value = p.outstanding_balance
  }
  note.value = ''
}, { immediate: true })

const currentFormatted = computed(() =>
props.part ? formatGBP(props.part.outstanding_balance, { decimals: 0, noSymbol: true }) : '0'
)

const changeAmount = computed(() => {
  if (newValue.value === null || !props.part) return null
  if (newValue.value === props.part.outstanding_balance) return null
  return newValue.value - props.part.outstanding_balance
})

const equityImpact = computed(() => {
  if (changeAmount.value === null) return null
  const share = props.ownershipPercent / 100
  // balance increases -> equity decreases (negative impact)
  // balance decreases -> equity increases (positive impact)
  return -changeAmount.value * share
})

const previewClass = computed(() => {
  if (changeAmount.value === null) return ''
  return changeAmount.value <= 0 ? 'positive' : 'negative' // balance reduction is good (positive)
})

function close() {
  emit('update:modelValue', false)
}

async function save() {
  if (newValue.value === null || newValue.value < 0 || !props.part) return
  saving.value = true
  try {
    await store.updatePartBalance(props.propertyId, props.part.id, newValue.value, note.value || undefined)
    toast.success('Balance updated')
    emit('saved')
    close()
  } catch (err: any) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

const toast = useToast()
useModalKeys(toRef(props, 'modelValue'), close, () => { if (!saving.value) save() })
</script>

<style scoped>
.current-display {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
  background: var(--bg-base);
  border-radius: var(--radius-md);
  border: 1px solid var(--bg-border);
  margin-bottom: var(--space-4);
}
.value-input {
  font-size: var(--font-size-xl);
  font-weight: 600;
  text-align: right;
}
.change-preview {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  flex-wrap: wrap;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  margin-bottom: var(--space-4);
}
.change-preview.positive { background: var(--positive-bg); color: var(--positive); }
.change-preview.negative { background: var(--negative-bg); color: var(--negative); }
.equity-impact {
  margin-left: auto;
  font-size: var(--font-size-xs);
  opacity: 0.85;
}
</style>
