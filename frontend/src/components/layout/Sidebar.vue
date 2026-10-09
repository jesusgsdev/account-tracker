<template>
  <aside class="sidebar">
    <div class="sidebar-logo">
      <span class="logo-icon">📊</span>
      <span class="logo-text">FolioTrack</span>
    </div>

    <nav class="sidebar-nav">
      <RouterLink to="/" class="nav-item" :class="{ active: route.name === 'dashboard' }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
          <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
        </svg>
        <span>Dashboard</span>
      </RouterLink>

      <RouterLink to="/accounts" class="nav-item" :class="{ active: route.name === 'accounts' }">
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

      <RouterLink to="/property" class="nav-item" :class="{ active: route.name === 'property' }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        <span>Property</span>
      </RouterLink>

      <RouterLink to="/market-trackers" class="nav-item" :class="{ active: route.name === 'market-trackers' }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M23 6l-9.5 9.5-5-5L1 18"/>
          <polyline points="17 6 23 6 23 12"/>
        </svg>
        <span>Market Trackers</span>
      </RouterLink>

      <RouterLink to="/audit" class="nav-item" :class="{ active: route.name === 'audit' }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        <span>Audit Log</span>
      </RouterLink>

      <RouterLink to="/data" class="nav-item" :class="{ active: route.name === 'data' }">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>
        <span>Data</span>
      </RouterLink>
    </nav>

    <div class="sidebar-footer">
      <button class="btn-logout" @click="handleLogout">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        <span>Sign Out</span>
      </button>
      <div class="sidebar-version">v1.0 · Local First</div>
    </div>
  </aside>
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
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--sidebar-width);
  height: 100dvh;
  background: var(--bg-surface);
  border-right: 1px solid var(--bg-border);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6);
  border-bottom: 1px solid var(--bg-border);
}

.logo-icon { font-size: 1.5rem; }

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-light), var(--cat-savings));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-item svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.nav-item:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
}

.nav-item.active {
  color: var(--accent-light);
  background: var(--accent-glow);
}

.sidebar-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--bg-border);
}

.btn-logout {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  background: transparent;
  color: var(--text-secondary);
  border: none;
  padding: var(--space-2) 0;
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: color var(--transition-fast);
  margin-bottom: var(--space-2);
}
.btn-logout svg {
  width: 14px;
  height: 14px;
  stroke: currentColor;
}
.btn-logout:hover {
  color: var(--negative);
}

.sidebar-version {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .sidebar { display: none; }
}
</style>
