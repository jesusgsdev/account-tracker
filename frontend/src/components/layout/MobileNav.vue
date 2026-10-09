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
        <line x1="3" y1="22" x2="21" y2="22"/>
        <line x1="6" y1="18" x2="6" y2="11"/>
        <line x1="10" y1="18" x2="10" y2="11"/>
        <line x1="14" y1="18" x2="14" y2="11"/>
        <line x1="18" y1="18" x2="18" y2="11"/>
        <polygon points="12 2 2 7 22 7"/>
        <path d="M5 22v-4h14v4"/>
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

    <RouterLink to="/market-trackers" class="mobile-nav-item" :class="{ active: route.name === 'market-trackers' }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M23 6l-9.5 9.5-5-5L1 18"/>
        <polyline points="17 6 23 6 23 12"/>
      </svg>
      <span>Trackers</span>
    </RouterLink>

    <RouterLink to="/audit" class="mobile-nav-item" :class="{ active: route.name === 'audit' }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
      <span>Audit</span>
    </RouterLink>

    <RouterLink to="/data" class="mobile-nav-item" :class="{ active: route.name === 'data' }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>
      <span>Data</span>
    </RouterLink>

    <button class="mobile-nav-item btn-logout-mobile" @click="handleLogout">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
      </svg>
      <span>Sign Out</span>
    </button>
  </nav>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api/client'
const route = useRoute()
const router = useRouter()

async function handleLogout() {
  await authApi.logout()
  router.push('/login')
}
</script>

<style scoped>
.mobile-nav {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(var(--mobile-nav-height) + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: var(--bg-surface);
  border-top: 1px solid var(--bg-border);
  z-index: 100;
  padding-left: max(var(--space-4), env(safe-area-inset-left));
  padding-right: max(var(--space-4), env(safe-area-inset-right));
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

.btn-logout-mobile {
  background: transparent;
  border: none;
  cursor: pointer;
}
.btn-logout-mobile:hover {
  color: var(--negative) !important;
}

@media (max-width: 768px) {
  .mobile-nav { display: flex; }
}
</style>
