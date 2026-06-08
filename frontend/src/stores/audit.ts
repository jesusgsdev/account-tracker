import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, type AuditLog } from '@/api/client'

export const useAuditStore = defineStore('audit', () => {
  const logs = ref<AuditLog[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(accountId?: number) {
    loading.value = true
    error.value = null
    try {
      logs.value = await api.audit.list(accountId, 200)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchHistory(accountId: number): Promise<AuditLog[]> {
    return api.audit.history(accountId)
  }

  function addLog(log: AuditLog) {
    logs.value.unshift(log)
  }

  return { logs, loading, error, fetchAll, fetchHistory, addLog }
})
