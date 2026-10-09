import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, apiErrorMessage, type AuditLog } from '@/api/client'

/** Skip refetching if data is younger than this (ms) unless forced. */
const STALE_MS = 30_000

export const useAuditStore = defineStore('audit', () => {
  const logs = ref<AuditLog[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastFetched = ref<number | null>(null)
  /** accountId the current `logs` were fetched for (undefined = all). */
  let fetchedFor: number | undefined
  let inflight: Promise<void> | null = null

  function invalidate() { lastFetched.value = null }

  async function fetchAll(accountId?: number, force = false) {
    const fresh = lastFetched.value !== null && Date.now() - lastFetched.value < STALE_MS
    if (!force && fresh && fetchedFor === accountId) return
    if (inflight) return inflight
    loading.value = true
    error.value = null
    inflight = (async () => {
      try {
        logs.value = await api.audit.list(accountId, 200)
        fetchedFor = accountId
        lastFetched.value = Date.now()
      } catch (e) {
        error.value = apiErrorMessage(e)
      } finally {
        loading.value = false
        inflight = null
      }
    })()
    return inflight
  }

  async function fetchHistory(accountId: number): Promise<AuditLog[]> {
    return api.audit.history(accountId)
  }

  function addLog(log: AuditLog) {
    logs.value.unshift(log)
  }

  return { logs, loading, error, lastFetched, invalidate, fetchAll, fetchHistory, addLog }
})
