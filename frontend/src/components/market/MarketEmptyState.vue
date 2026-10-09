<template>
  <div class="empty-state-container card">
    <span class="empty-icon">📈</span>
    <h3 class="empty-title">No Holdings Tracked</h3>
    <p class="empty-desc">
      We couldn't find any holdings matching your criteria. To add stock holdings to your Investment or Retirement accounts, go to the Accounts view and click "Manage" on the card.
    </p>
    <RouterLink to="/accounts" class="btn btn-primary btn-sm">
      Go to Accounts
    </RouterLink>
  </div>
</template>

<style scoped>
.empty-state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  text-align: center;
  background: var(--bg-surface);
  border: 1px solid var(--bg-border);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--font-size-lg);
  font-weight: 700;
  margin-bottom: var(--space-2);
}

.empty-desc {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  max-width: 460px;
  margin-bottom: var(--space-6);
  line-height: 1.5;
}
</style>
