import { ref, computed, onMounted } from 'vue'
import { api, apiErrorMessage, type ShareHolding, type LiveHolding, type PortfolioLive } from '@/api/client'
import { useSharesStore } from '@/stores/shares'
import { formatGBP } from '@/utils/format'
import { useToast } from '@/composables/useToast'

export type DisplayHolding = ShareHolding & Partial<LiveHolding>

export interface NewHoldingForm {
  ticker: string
  display_name: string
  quantity: number | null
  avg_cost: number | null
  notes: string
}

export interface EditHoldingForm {
  ticker: string
  display_name: string
  quantity: number
  avg_cost: number
}

const emptyForm = (): NewHoldingForm => ({ ticker: '', display_name: '', quantity: null, avg_cost: null, notes: '' })

/** State + actions for managing the share holdings of one account. */
export function useHoldingsManager(accountId: () => number, onSynced: (newValue: number) => void) {
  const toast = useToast()
  const sharesStore = useSharesStore()

  const holdings = ref<ShareHolding[]>([])
  const syncing = ref(false)
  const showAddForm = ref(false)
  const adding = ref(false)
  const addError = ref<string | null>(null)
  const localError = ref<string | null>(null)
  const editingId = ref<number | null>(null)
  const editForm = ref<EditHoldingForm>({ ticker: '', display_name: '', quantity: 0, avg_cost: 0 })
  const form = ref<NewHoldingForm>(emptyForm())
  const showModal = ref(false)
  const showDeleteConfirm = ref(false)
  const pendingDeleteId = ref<number | null>(null)

  // Portfolio comes from the store (shared with global refresh)
  const portfolio = computed<PortfolioLive | null>(() => sharesStore.portfolios[accountId()] ?? null)
  const isLoading = computed(() => sharesStore.loading)

  // Merge holdings list with live data
  const displayHoldings = computed((): DisplayHolding[] => {
    if (!portfolio.value) return holdings.value
    const liveMap = Object.fromEntries(portfolio.value.holdings.map(h => [h.id, h]))
    return holdings.value.map(h => ({ ...h, ...liveMap[h.id] }))
  })

  function emitSyncedFromPortfolio() {
    if (portfolio.value?.total_live_value_gbp != null) {
      onSynced(portfolio.value.total_live_value_gbp)
    }
  }

  // Fetch the holdings list (cheap — no prices)
  async function fetchHoldings() {
    try {
      holdings.value = await api.shares.list(accountId())
    } catch (e: any) {
      localError.value = apiErrorMessage(e)
    }
  }

  // Individual account refresh
  async function handleRefresh() {
    localError.value = null
    try {
      await sharesStore.refreshAccount(accountId())
      emitSyncedFromPortfolio()
    } catch (e: any) {
      localError.value = apiErrorMessage(e)
    }
  }

  async function addHolding() {
    addError.value = null
    if (!form.value.ticker.trim()) { addError.value = 'Ticker is required'; return }
    if (!form.value.quantity || form.value.quantity <= 0) { addError.value = 'Quantity must be > 0'; return }

    adding.value = true
    try {
      const h = await api.shares.create(accountId(), {
        ticker: form.value.ticker.trim(),
        display_name: form.value.display_name || undefined,
        quantity: form.value.quantity,
        avg_cost: form.value.avg_cost ?? undefined,
        notes: form.value.notes || undefined,
      })
      holdings.value.push(h)
      toast.success(`Added ${h.ticker}`)
      form.value = emptyForm()
      showAddForm.value = false
      sharesStore.invalidateAccount(accountId())
      await sharesStore.refreshAccount(accountId())
      emitSyncedFromPortfolio()
    } catch (e: any) {
      addError.value = apiErrorMessage(e)
    } finally {
      adding.value = false
    }
  }

  // Inline edit
  function startEdit(h: DisplayHolding) {
    editingId.value = h.id
    editForm.value = {
      ticker: h.ticker,
      display_name: h.display_name || '',
      quantity: h.quantity,
      avg_cost: h.avg_cost ?? 0,
    }
  }

  async function saveEdit(holdingId: number) {
    try {
      const updated = await api.shares.update(holdingId, {
        ticker: editForm.value.ticker.trim() || undefined,
        display_name: editForm.value.display_name.trim() || '',
        quantity: editForm.value.quantity,
        avg_cost: editForm.value.avg_cost || undefined,
      })
      const idx = holdings.value.findIndex(h => h.id === holdingId)
      if (idx !== -1) holdings.value[idx] = updated
      editingId.value = null
      toast.success('Holding updated')
      await sharesStore.refreshAccount(accountId())
      emitSyncedFromPortfolio()
    } catch (e: any) {
      localError.value = apiErrorMessage(e)
    }
  }

  function removeHolding(holdingId: number) {
    pendingDeleteId.value = holdingId
    showDeleteConfirm.value = true
  }

  async function executeDeleteHolding() {
    if (pendingDeleteId.value === null) return
    const holdingId = pendingDeleteId.value
    pendingDeleteId.value = null
    try {
      await api.shares.delete(holdingId)
      holdings.value = holdings.value.filter(h => h.id !== holdingId)
      toast.success('Holding removed')
      sharesStore.invalidateAccount(accountId())
      if (holdings.value.length > 0) {
        await sharesStore.refreshAccount(accountId())
        emitSyncedFromPortfolio()
      } else {
        onSynced(0)
      }
    } catch (e: any) {
      localError.value = apiErrorMessage(e)
    }
  }

  // Sync account value
  async function syncAccountValue() {
    syncing.value = true
    localError.value = null
    try {
      const result = await api.shares.sync(accountId())
      sharesStore.syncError = null
      toast.success(`Account synced to £${formatGBP(result.new_value, { noSymbol: true })}`)
      onSynced(result.new_value)
    } catch (e: any) {
      const msg = apiErrorMessage(e)
      sharesStore.syncError = msg
      localError.value = `Sync failed: ${msg}`
      toast.error(`Sync failed: ${msg}`)
    } finally {
      syncing.value = false
    }
  }

  function openManageAndAdd() {
    showModal.value = true
    showAddForm.value = true
  }

  onMounted(async () => {
    await fetchHoldings()
    if (holdings.value.length > 0 && !portfolio.value) {
      await sharesStore.refreshAccount(accountId())
    }
  })

  return {
    holdings, syncing, showAddForm, adding, addError, localError, editingId, editForm, form,
    showModal, showDeleteConfirm, portfolio, isLoading, displayHoldings, lastRefreshedAt: computed(() => sharesStore.lastRefreshedAt),
    handleRefresh, addHolding, startEdit, saveEdit, removeHolding, executeDeleteHolding,
    syncAccountValue, openManageAndAdd,
  }
}
