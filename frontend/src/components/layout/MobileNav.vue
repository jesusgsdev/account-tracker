<template>
  <nav class="mobile-nav">
    <RouterLink to="/" class="mobile-nav-item" :class="{ active: route.name === 'dashboard' }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
      </svg>
      <span>Dashboard</span>
    </RouterLink>

    <RouterLink to="/accounts" class="mobile-nav-item" :class="{ active: route.name === 'accounts' }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
      <span>Accounts</span>
    </RouterLink>

    <RouterLink to="/property" class="mobile-nav-item" :class="{ active: route.name === 'property' }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
      <span>Property</span>
    </RouterLink>

    <RouterLink to="/audit" class="mobile-nav-item" :class="{ active: route.name === 'audit' }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
      <span>Audit</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style scoped>
.mobile-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--mobile-nav-height);
  background: var(--bg-surface);
  border-top: 1px solid var(--bg-border);
  z-index: 100;
  padding: 0 var(--space-4);
  backdrop-filter: blur(12px);
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
  flex: 1;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 500;
  padding: var(--space-2);
  border-radius: var(--radius-md);
  transition: color var(--transition-fast);
}

.mobile-nav-item svg {
  width: 20px;
  height: 20px;
}

.mobile-nav-item.active { color: var(--accent-light); }
.mobile-nav-item:hover  { color: var(--text-primary); }

@media (max-width: 768px) {
  .mobile-nav { display: flex; }
}
</style>
