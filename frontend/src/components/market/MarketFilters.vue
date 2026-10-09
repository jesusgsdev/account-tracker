<template>
  <!-- Filter and Search Bar -->
  <div class="filters-card card">
    <div class="filters-row">
      <!-- Search -->
      <div class="search-box">
        <div class="input-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search ticker, name or account..."
            class="search-input"
          />
        </div>
      </div>

      <!-- Category Filter Tabs -->
      <div class="tab-filters">
        <button
          class="tab-btn"
          :class="{ active: activeCategory === 'ALL' }"
          @click="activeCategory = 'ALL'"
        >
          All Categories
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeCategory === 'INVESTMENTS' }"
          @click="activeCategory = 'INVESTMENTS'"
        >
          Investments
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeCategory === 'RETIREMENT' }"
          @click="activeCategory = 'RETIREMENT'"
        >
          Retirement
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CategoryFilter } from '@/composables/useMarketHoldings'

const searchQuery = defineModel<string>('searchQuery', { required: true })
const activeCategory = defineModel<CategoryFilter>('activeCategory', { required: true })
</script>

<style scoped>
.filters-card {
  padding: var(--space-4) var(--space-5);
  margin-bottom: var(--space-6);
}

.filters-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.search-box {
  flex: 1;
  min-width: 280px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: var(--space-3);
  width: 16px;
  height: 16px;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: var(--space-2) var(--space-3) var(--space-2) 36px;
  border-radius: var(--radius-md);
  border: 1px solid var(--bg-border);
  background: var(--bg-surface-2);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: all var(--transition-fast);
}

.search-input:focus {
  border-color: var(--accent-light);
  box-shadow: 0 0 0 2px var(--accent-glow);
}

.tab-filters {
  display: flex;
  background: var(--bg-surface-2);
  padding: 4px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--bg-border);
}

.tab-btn {
  background: transparent;
  border: none;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-surface);
  color: var(--accent-light);
  box-shadow: var(--shadow-sm);
}
</style>
