<template>
  <div class="data-tools">
    <!-- Daily snapshots -->
    <section class="card tool-card">
      <h2 class="tool-title">Daily snapshots</h2>
      <p v-if="snapLoading" class="text-sm text-muted">Loading…</p>
      <WarningBanner v-else-if="snapLoadError" level="warn">Snapshot status unavailable: {{ snapLoadError }}</WarningBanner>
      <template v-else-if="status">
        <p class="text-sm">
          <span class="pill" :class="status.enabled ? 'pill-on' : 'pill-off'">{{ status.enabled ? 'Enabled' : 'Disabled' }}</span>
          <span class="text-muted"> runs daily at {{ String(status.hour_utc).padStart(2, '0') }}:00 UTC</span>
        </p>
        <p v-if="!status.enabled" class="text-xs text-muted">Automatic snapshots are turned off. You can still run one manually.</p>
        <p class="text-sm">Last run: <strong>{{ status.last_run_at ? fmtDate(status.last_run_at) : 'never' }}</strong>
          <span v-if="status.last_run_at" class="text-muted"> ({{ timeAgo(status.last_run_at) }})</span></p>
        <div v-if="status.last_result" class="result-box text-sm">
          <div>{{ status.last_result.accounts_updated }} account(s) updated</div>
          <ul v-if="status.last_result.accounts_skipped.length" class="skipped">
            <li v-for="s in status.last_result.accounts_skipped" :key="s.account_id">
              <strong>{{ s.name }}</strong> skipped — <span class="text-muted">{{ s.reason }}</span>
            </li>
          </ul>
        </div>
      </template>
      <WarningBanner v-if="runError" level="error">{{ runError }}</WarningBanner>
      <button class="btn btn-sm btn-primary" :disabled="running" @click="runSnapshot">
        {{ running ? 'Running…' : 'Run now' }}
      </button>
    </section>

    <!-- Backups -->
    <section class="card tool-card">
      <h2 class="tool-title">Backups</h2>
      <p v-if="backupsLoading" class="text-sm text-muted">Loading…</p>
      <WarningBanner v-else-if="backupsError" level="warn">Backups unavailable: {{ backupsError }}</WarningBanner>
      <p v-else-if="!backups.length" class="text-sm text-muted">No automatic backups yet.</p>
      <ul v-else class="backup-list">
        <li v-for="b in backups.slice(0, 10)" :key="b.filename" class="text-sm">
          <span class="mono">{{ b.filename }}</span>
          <span class="text-muted">{{ fmtSize(b.size_bytes) }} · {{ fmtDate(b.created_at) }}</span>
        </li>
      </ul>
      <WarningBanner v-if="backupError" level="error">{{ backupError }}</WarningBanner>
      <div class="actions">
        <button class="btn btn-sm btn-primary" :disabled="backingUp" @click="runBackup">
          {{ backingUp ? 'Backing up…' : 'Back up now' }}
        </button>
        <a class="btn btn-sm btn-secondary" :href="api.export.backupJsonUrl()" download>Download full backup (JSON)</a>
      </div>
    </section>

    <!-- Export CSV -->
    <section class="card tool-card">
      <h2 class="tool-title">Export CSV</h2>
      <div class="actions">
        <a class="btn btn-sm btn-secondary" :href="api.export.accountsCsvUrl()" download>Accounts</a>
        <a class="btn btn-sm btn-secondary" :href="api.export.auditCsvUrl()" download>Audit log</a>
        <a class="btn btn-sm btn-secondary" :href="api.export.propertiesCsvUrl()" download>Properties</a>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, ApiError, apiErrorMessage, type SnapshotStatus, type BackupFile } from '@/api/client'
import { parseApiDate, timeAgo } from '@/utils/date'
import WarningBanner from '@/components/common/WarningBanner.vue'

const status = ref<SnapshotStatus | null>(null)
const snapLoading = ref(true)
const snapLoadError = ref<string | null>(null)
const running = ref(false)
const runError = ref<string | null>(null)

const backups = ref<BackupFile[]>([])
const backupsLoading = ref(true)
const backupsError = ref<string | null>(null)
const backingUp = ref(false)
const backupError = ref<string | null>(null)

function fmtDate(s: string) {
  return parseApiDate(s).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function fmtSize(n: number) {
  if (n >= 1048576) return `${(n / 1048576).toFixed(1)} MB`
  if (n >= 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${n} B`
}

async function loadStatus() {
  snapLoading.value = true
  snapLoadError.value = null
  try { status.value = await api.snapshots.status() }
  catch (e) { snapLoadError.value = apiErrorMessage(e) }
  finally { snapLoading.value = false }
}

async function loadBackups() {
  backupsLoading.value = true
  backupsError.value = null
  try { backups.value = await api.export.backups() }
  catch (e) { backupsError.value = apiErrorMessage(e) }
  finally { backupsLoading.value = false }
}

async function runSnapshot() {
  running.value = true
  runError.value = null
  try {
    await api.snapshots.run()
    await loadStatus()
  } catch (e) {
    const msg = apiErrorMessage(e)
    runError.value = (e instanceof ApiError && e.status === 409) || /already running/i.test(msg) ? 'A snapshot is already running — try again shortly.' : msg
  } finally {
    running.value = false
  }
}

async function runBackup() {
  backingUp.value = true
  backupError.value = null
  try {
    await api.export.runBackup()
    await loadBackups()
  } catch (e) {
    backupError.value = apiErrorMessage(e)
  } finally {
    backingUp.value = false
  }
}

onMounted(() => { loadStatus(); loadBackups() })
</script>

<style scoped>
.data-tools { display: grid; gap: var(--space-4); max-width: 760px; }
.tool-card { padding: var(--space-5); display: flex; flex-direction: column; gap: var(--space-3); align-items: flex-start; }
.tool-card > * { max-width: 100%; }
.tool-title { font-size: var(--font-size-lg); font-weight: 600; }
.pill { padding: 2px var(--space-2); border-radius: var(--radius-full); font-size: var(--font-size-xs); font-weight: 600; }
.pill-on { background: var(--positive-bg); color: var(--positive); }
.pill-off { background: var(--negative-bg); color: var(--negative); }
.result-box { background: var(--bg-elevated); border-radius: var(--radius-md); padding: var(--space-3) var(--space-4); }
.skipped { margin: var(--space-2) 0 0 var(--space-4); list-style: disc; }
.backup-list { list-style: none; display: flex; flex-direction: column; gap: var(--space-2); width: 100%; }
.backup-list li { display: flex; justify-content: space-between; gap: var(--space-3); flex-wrap: wrap; }
.mono { font-family: ui-monospace, Consolas, monospace; word-break: break-all; }
.actions { display: flex; gap: var(--space-3); flex-wrap: wrap; }
</style>
