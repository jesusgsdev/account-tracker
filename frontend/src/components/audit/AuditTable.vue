<template>
  <div class="audit-table-wrap">
    <table class="audit-table">
      <thead>
        <tr>
          <th>Date &amp; Time</th>
          <th>Account</th>
          <th>Previous</th>
          <th>New Value</th>
          <th>Change</th>
          <th>Note</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id" class="audit-row">
          <td class="td-date">
            <span class="date">{{ formatDate(log.recorded_at) }}</span>
            <span class="time text-xs text-muted">{{ formatTime(log.recorded_at) }}</span>
          </td>
          <td class="td-account">{{ log.account_name ?? `#${log.account_id}` }}</td>
          <td class="td-mono">£{{ log.previous_value.toLocaleString('en-GB', { minimumFractionDigits: 2 }) }}</td>
          <td class="td-mono font-semibold">£{{ log.new_value.toLocaleString('en-GB', { minimumFractionDigits: 2 }) }}</td>
          <td>
            <span class="change-pill" :class="log.change_amount >= 0 ? 'positive' : 'negative'">
              {{ log.change_amount >= 0 ? '+' : '' }}£{{ Math.abs(log.change_amount).toLocaleString('en-GB', { minimumFractionDigits: 2 }) }}
              <span v-if="log.change_percent !== null" class="pct">
                ({{ log.change_percent >= 0 ? '+' : '' }}{{ log.change_percent.toFixed(1) }}%)
              </span>
            </span>
          </td>
          <td class="td-note text-sm text-muted">{{ log.note ?? '—' }}</td>
        </tr>
        <tr v-if="!logs.length">
          <td colspan="6" class="empty-row">No audit entries found</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { AuditLog } from '@/api/client'

defineProps<{ logs: AuditLog[] }>()

function formatDate(dt: string) {
  return new Date(dt + 'Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}
function formatTime(dt: string) {
  return new Date(dt + 'Z').toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.audit-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid var(--bg-border);
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.audit-table th {
  background: var(--bg-surface-2);
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-size: var(--font-size-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  white-space: nowrap;
}

.audit-row td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--bg-border);
  vertical-align: middle;
}

.audit-row:hover td { background: var(--bg-surface-2); }

.td-date { display: flex; flex-direction: column; gap: 2px; white-space: nowrap; }
.td-mono { font-variant-numeric: tabular-nums; white-space: nowrap; }
.td-account { font-weight: 500; max-width: 160px; }
.td-note { max-width: 180px; }

.change-pill {
  display: inline-flex;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
  white-space: nowrap;
}
.change-pill.positive { background: var(--positive-bg); color: var(--positive); }
.change-pill.negative { background: var(--negative-bg); color: var(--negative); }

.empty-row {
  text-align: center;
  color: var(--text-muted);
  padding: var(--space-12) !important;
}
</style>
