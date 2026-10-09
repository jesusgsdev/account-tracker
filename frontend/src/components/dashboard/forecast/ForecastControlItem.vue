<template>
  <div class="control-item">
    <div class="control-label">
      <span class="text-xs font-medium text-secondary">{{ label }}</span>
      <div class="manual-input-wrap">
        <span v-if="prefix" class="input-prefix">{{ prefix }}</span>
        <input
          type="number"
          v-model.number="value"
          :min="inputMin"
          :max="inputMax"
          :step="inputStep"
          class="manual-input"
        />
        <span v-if="suffix" class="input-suffix">{{ suffix }}</span>
      </div>
    </div>
    <input
      type="range"
      v-model.number="value"
      :min="rangeMin"
      :max="rangeMax"
      :step="rangeStep"
      class="slider-input"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  prefix?: string
  suffix?: string
  inputMin: number
  inputMax?: number
  inputStep: number
  rangeMin: number
  rangeMax: number
  rangeStep: number
}>()
const value = defineModel<number>({ required: true })
</script>

<style scoped>
.control-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.control-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-secondary {
  color: #a855f7;
}

.manual-input-wrap {
  display: flex;
  align-items: center;
  background: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  border-radius: var(--radius-sm);
  padding: 2px 6px;
  transition: border-color var(--transition-fast);
}

.manual-input-wrap:focus-within {
  border-color: var(--accent);
}

.manual-input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: var(--font-size-xs);
  font-weight: 600;
  width: 54px;
  text-align: right;
  outline: none;
  font-family: inherit;
  padding: 0;
}

.manual-input::-webkit-outer-spin-button,
.manual-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.manual-input[type=number] {
  -moz-appearance: textfield;
}

.input-prefix {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  font-weight: 600;
  margin-right: 2px;
}

.input-suffix {
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  font-weight: 600;
  margin-left: 2px;
}

.slider-input {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--bg-elevated);
  outline: none;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: var(--radius-full);
  background: var(--accent);
  border: 2px solid var(--text-primary);
  cursor: pointer;
  transition: transform var(--transition-fast), background var(--transition-fast);
}

.slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  background: var(--accent-light);
}
</style>
