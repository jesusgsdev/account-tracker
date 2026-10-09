<template>
  <div class="add-form">
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
      <span v-if="error" class="text-xs text-negative">{{ error }}</span>
      <button class="btn btn-sm btn-primary" @click="emit('submit')" :disabled="adding">
        <span v-if="adding" class="spinner" />
        <span v-else>Add Holding</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NewHoldingForm } from '@/composables/useHoldingsManager'

// `form` is a shared reactive object owned by the parent; fields are edited in place.
defineProps<{
  form: NewHoldingForm
  adding: boolean
  error: string | null
}>()
const emit = defineEmits<{ submit: [] }>()
</script>

<style scoped>
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
  width: 90px; /* matches the original cascade (later .ticker-input rule won over .field-input) */
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: var(--space-3);
}

.text-negative { color: var(--negative); }

.spinner {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
