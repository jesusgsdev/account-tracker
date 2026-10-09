<template>
  <div class="toast-container" aria-live="polite">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast" :class="`toast-${t.kind}`" role="status" @click="dismiss(t.id)">
        <span class="toast-icon">{{ t.kind === 'success' ? '✓' : t.kind === 'error' ? '!' : 'i' }}</span>
        <span class="toast-msg">{{ t.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'
const { toasts, dismiss } = useToast()
</script>

<style scoped>
.toast-container {
  position: fixed;
  right: 16px;
  bottom: 80px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: min(380px, calc(100vw - 32px));
  pointer-events: none;
}
.toast {
  pointer-events: auto;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: var(--bg-card, #1e1e2a);
  color: var(--text-primary, #fff);
  border: 1px solid var(--bg-border, #333);
  border-left-width: 4px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  font-size: 0.875rem;
  cursor: pointer;
}
.toast-success { border-left-color: #22c55e; }
.toast-error { border-left-color: #ef4444; }
.toast-info { border-left-color: #3b82f6; }
.toast-icon { font-weight: 700; }
.toast-success .toast-icon { color: #4ade80; }
.toast-error .toast-icon { color: #f87171; }
.toast-info .toast-icon { color: #60a5fa; }
.toast-msg { white-space: pre-line; word-break: break-word; }
.toast-enter-active, .toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(20px); }
</style>
