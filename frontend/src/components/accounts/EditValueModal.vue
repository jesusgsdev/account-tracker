<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <Transition name="slide-up">
          <div v-if="modelValue" class="modal">
            <div class="modal-header">
              <div>
                <h2 class="text-lg font-semibold">Update Value</h2>
                <p class="text-sm text-muted">{{ account?.name }}</p>
              </div>
              <button class="btn btn-icon btn-ghost" @click="close">✕</button>
            </div>

            <div class="modal-body">
              <div class="current-value-display">
                <span class="text-sm text-muted">Current Value</span>
                <span class="text-2xl font-bold">£{{ formattedCurrent }}</span>
              </div>

              <div class="form-group">
                <label class="form-label" for="new-value">New Value (£)</label>
                <input
                  id="new-value"
                  v-model.number="newValue"
                  type="number"
                  min="0"
                  step="0.01"
                  class="form-input value-input"
                  placeholder="0.00"
                  autofocus
                />
              </div>

              <div v-if="newValue !== null && newValue !== account?.current_value" class="change-preview" :class="changeClass">
                <span>{{ changeAmount >= 0 ? '+' : '' }}{{ formatGBP(Math.abs(changeAmount)) }}</span>
                <span v-if="changePercent !== null">({{ changeAmount >= 0 ? '+' : '' }}{{ changePercent.toFixed(2) }}%)</span>
              </div>

              <div class="form-group">
                <label class="form-label" for="update-note">Note (optional)</label>
                <input id="update-note" v-model="note" type="text" class="form-input" placeholder="e.g. Monthly statement" />
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="close">Cancel</button>
              <button
                class="btn btn-primary"
                :disabled="newValue === null || newValue < 0 || saving"
                @click="save"
              >
                {{ saving ? 'Saving…' : 'Update' }}
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
import { useModalKeys } from '@/composables/useModalKeys'
import { ref, computed, watch } from 'vue'
import type { Account } from '@/api/client'

const props = defineProps<{
  modelValue: boolean
  account: Account | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  saved: [newValue: number, note: string | undefined]
}>()

const newValue = ref<number | null>(null)
const note = ref('')
const saving = ref(false)

watch(() => props.account, (a) => {
  newValue.value = a ? a.current_value : null
  note.value = ''
})

const formattedCurrent = computed(() =>
  formatGBP((props.account?.current_value ?? 0), { decimals: 2, noSymbol: true })
)

const changeAmount = computed(() =>
  newValue.value !== null && props.account ? newValue.value - props.account.current_value : 0
)

const changePercent = computed(() => {
  const prev = props.account?.current_value ?? 0
  if (prev === 0) return null
  return (changeAmount.value / prev) * 100
})

const changeClass = computed(() =>
  changeAmount.value >= 0 ? 'positive' : 'negative'
)

function close() {
  emit('update:modelValue', false)
}

async function save() {
  if (newValue.value === null || newValue.value < 0) return
  saving.value = true
  try {
    emit('saved', newValue.value, note.value || undefined)
    close()
  } finally {
    saving.value = false
  }
}

useModalKeys(toRef(props, 'modelValue'), close, () => { if (!saving.value) save() })
</script>

<style scoped>
.current-value-display {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
  background: var(--bg-base);
  border-radius: var(--radius-md);
  border: 1px solid var(--bg-border);
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
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 600;
}
.change-preview.positive { background: var(--positive-bg); color: var(--positive); }
.change-preview.negative { background: var(--negative-bg); color: var(--negative); }
</style>
