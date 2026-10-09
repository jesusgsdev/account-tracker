<template>
  <div class="forecast-header">
    <div>
      <h2 class="forecast-title">Wealth Projection Forecast</h2>
      <p class="text-sm text-muted">Simulate compound growth and savings contributions over time</p>
    </div>

    <div class="header-controls">
      <!-- Inflation Adjustment Slide-Toggle -->
      <div class="toggle-slider-wrap">
        <span class="toggle-mode-label text-xs" :class="{ active: !adjustInflation }">Future £ (Nominal)</span>
        <label class="switch">
          <input type="checkbox" v-model="adjustInflation" />
          <span class="slider round"></span>
        </label>
        <span class="toggle-mode-label text-xs" :class="{ active: adjustInflation }">Today's £ (Adjusted)</span>
      </div>

      <div class="include-toggle">
        <label class="toggle-label text-xs font-semibold">
          <input type="checkbox" v-model="includeOther" />
          Include Savings & Property Equity (£{{ otherAssetsFormatted }})
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ otherAssetsFormatted: string }>()
const adjustInflation = defineModel<boolean>('adjustInflation', { required: true })
const includeOther = defineModel<boolean>('includeOther', { required: true })
</script>

<style scoped>
.forecast-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  border-bottom: 1px solid var(--bg-border);
  padding-bottom: var(--space-4);
}

.forecast-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-1);
}

.header-controls {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-wrap: wrap;
}

/* Inflation Slide-Toggle Styles */
.toggle-slider-wrap {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.toggle-mode-label {
  font-weight: 600;
  color: var(--text-muted);
  transition: color var(--transition-fast);
}

.toggle-mode-label.active {
  color: var(--text-primary);
}

/* Slide Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 38px;
  height: 22px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-elevated);
  border: 1px solid var(--bg-border);
  transition: .25s ease;
  border-radius: var(--radius-full);
}

.slider:before {
  position: absolute;
  content: "";
  height: 14px;
  width: 14px;
  left: 3px;
  bottom: 3px;
  background-color: var(--text-secondary);
  transition: .25s ease;
  border-radius: var(--radius-full);
}

input:checked + .slider {
  background-color: var(--accent-bg);
  border-color: var(--accent-border);
}

input:checked + .slider:before {
  transform: translateX(16px);
  background-color: var(--accent);
}

.include-toggle {
  display: flex;
  align-items: center;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.toggle-label input {
  accent-color: var(--accent);
  cursor: pointer;
  width: 16px;
  height: 16px;
}
</style>
