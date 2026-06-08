<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="modal-overlay" @click.self="close">
        <Transition name="slide-up">
          <div v-if="modelValue" class="modal">
            <div class="modal-header">
              <div>
                <h2 class="text-lg font-semibold">Update Property Value</h2>
                <p class="text-sm text-muted">{{ property?.name }}</p>
              </div>
              <button class="btn btn-icon btn-ghost" @click="close">✕</button>
            </div>

            <div class="modal-body">
              <div class="current-display">
                <span class="text-sm text-muted">Current Value</span>
                <span class="text-2xl font-bold">£{{ currentFormatted }}</span>
              </div>

              <div class="form-group">
                <label class="form-label" for="new-value">New Property Value (£)</label>
                <input
                  id="new-value"
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
                <span>{{ changeAmount >= 0 ? '▲ Value increase' : '▼ Value decrease' }}</span>
                <span class="font-semibold">
                  {{ changeAmount >= 0 ? '+' : '' }}£{{ Math.abs(changeAmount).toLocaleString('en-GB', { minimumFractionDigits: 0 }) }}
                </span>
                <span v-if="equityImpact !== null" class="equity-impact">
                  Equity {{ equityImpact >= 0 ? '▲' : '▼' }} £{{ Math.abs(equityImpact).toLocaleString('en-GB', { minimumFractionDigits: 0 }) }}
                </span>
              </div>

              <div class="form-group">
                <label class="form-label" for="val-note">Note (optional)</label>
                <input id="val-note" v-model="note" type="text" class="form-input" placeholder="e.g. Annual valuation, Zoopla estimate" />
              </div>
            </div>

            <div class="modal-footer">
              <button class="btn btn-secondary" @click="close">Cancel</button>
              <button class="btn btn-primary" :disabled="newValue === null || newValue <= 0 || saving" @click="save">
                {{ saving ? 'Saving…' : 'Update Value' }}
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
import type { Property } from '@/api/client'
import { useMortgageStore } from '@/stores/mortgage'

const props = defineProps<{
  modelValue: boolean
  property: Property | null
}>()

const emit = defineEmits<{
  'update:modelValue': [v: boolean]
  saved: []
}>()

const store = useMortgageStore()
const newValue = ref<number | null>(null)
const note = ref('')
const saving = ref(false)

watch(() => props.property, (p) => {
  if (p) {
    newValue.value = p.property_value
  }
  note.value = ''
}, { immediate: true })

const currentFormatted = computed(() =>
  props.property ? props.property.property_value.toLocaleString('en-GB', { minimumFractionDigits: 0 }) : '0'
)

const changeAmount = computed(() => {
  if (newValue.value === null || !props.property) return null
  if (newValue.value === props.property.property_value) return null
  return newValue.value - props.property.property_value
})

const equityImpact = computed(() => {
  if (changeAmount.value === null || !props.property) return null
  const share = props.property.ownership_percent / 100
  return changeAmount.value * share
})

const previewClass = computed(() => {
  if (changeAmount.value === null) return ''
  return changeAmount.value >= 0 ? 'positive' : 'negative'
})

function close() {
  emit('update:modelValue', false)
}

async function save() {
  if (newValue.value === null || newValue.value <= 0 || !props.property) return
  saving.value = true
  try {
    await store.updatePropertyValue(props.property.id, newValue.value, note.value || undefined)
    emit('saved')
    close()
  } catch (err: any) {
    alert(err.message)
  } finally {
    saving.value = false
  }
}
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
