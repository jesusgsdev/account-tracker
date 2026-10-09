import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, apiErrorMessage, type Property, type MortgagePart, type PropertyValueAuditLog, type MortgagePartAuditLog } from '@/api/client'

/** Skip refetching if data is younger than this (ms) unless forced. */
const STALE_MS = 30_000

export const useMortgageStore = defineStore('mortgage', () => {
  const properties = ref<Property[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastFetched = ref<number | null>(null)
  let inflight: Promise<void> | null = null

  const totalEquity = computed(() =>
    properties.value.reduce((sum, p) => sum + p.equity, 0)
  )
  const totalPropertyValueShare = computed(() =>
    properties.value.reduce((sum, p) => sum + p.property_value_share, 0)
  )
  const totalOutstandingShare = computed(() =>
    properties.value.reduce((sum, p) => sum + p.outstanding_share, 0)
  )

  // Alias for backward compatibility or simple renaming
  const mortgages = computed(() => properties.value)

  function invalidate() { lastFetched.value = null }

  /** Fetch properties; skipped when data is fresh (<30s) unless `force`. */
  async function fetchAll(force = false) {
    const fresh = lastFetched.value !== null && Date.now() - lastFetched.value < STALE_MS
    if (!force && fresh) return
    if (inflight) return inflight
    loading.value = true
    error.value = null
    inflight = (async () => {
      try {
        properties.value = await api.properties.list()
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

  async function createProperty(payload: Parameters<typeof api.properties.create>[0]) {
    const p = await api.properties.create(payload)
    properties.value.push(p)
    return p
  }

  async function updatePropertyValue(id: number, value: number, note?: string): Promise<PropertyValueAuditLog> {
    const log = await api.properties.updateValue(id, value, note)
    const updated = await api.properties.get(id)
    const idx = properties.value.findIndex(p => p.id === id)
    if (idx !== -1) properties.value[idx] = updated
    return log
  }

  async function updatePropertyMeta(id: number, payload: Parameters<typeof api.properties.updateMeta>[1]) {
    const updated = await api.properties.updateMeta(id, payload)
    const idx = properties.value.findIndex(p => p.id === id)
    if (idx !== -1) properties.value[idx] = updated
    return updated
  }

  async function deleteProperty(id: number) {
    await api.properties.delete(id)
    properties.value = properties.value.filter(p => p.id !== id)
  }

  // Mortgage Parts CRUD
  async function createPart(propertyId: number, payload: Parameters<typeof api.properties.createPart>[1]) {
    const part = await api.properties.createPart(propertyId, payload)
    const updated = await api.properties.get(propertyId)
    const idx = properties.value.findIndex(p => p.id === propertyId)
    if (idx !== -1) properties.value[idx] = updated
    return part
  }

  async function updatePartMeta(propertyId: number, partId: number, payload: Parameters<typeof api.properties.updatePartMeta>[1]) {
    const part = await api.properties.updatePartMeta(partId, payload)
    const updated = await api.properties.get(propertyId)
    const idx = properties.value.findIndex(p => p.id === propertyId)
    if (idx !== -1) properties.value[idx] = updated
    return part
  }

  async function updatePartBalance(propertyId: number, partId: number, balance: number, note?: string): Promise<MortgagePartAuditLog> {
    const log = await api.properties.updatePartBalance(partId, balance, note)
    const updated = await api.properties.get(propertyId)
    const idx = properties.value.findIndex(p => p.id === propertyId)
    if (idx !== -1) properties.value[idx] = updated
    return log
  }

  async function deletePart(propertyId: number, partId: number) {
    await api.properties.deletePart(partId)
    const updated = await api.properties.get(propertyId)
    const idx = properties.value.findIndex(p => p.id === propertyId)
    if (idx !== -1) properties.value[idx] = updated
  }

  return {
    properties, mortgages, loading, error, lastFetched, invalidate,
    totalEquity, totalPropertyValueShare, totalOutstandingShare,
    fetchAll, createProperty, updatePropertyValue, updatePropertyMeta, deleteProperty,
    createPart, updatePartMeta, updatePartBalance, deletePart,
  }
})
