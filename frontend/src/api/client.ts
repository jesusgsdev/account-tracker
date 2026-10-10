// Typed API client for the FastAPI backend

const BASE = '/api'

export interface Account {
  id: number
  name: string
  account_type: string
  category: 'INVESTMENTS' | 'RETIREMENT' | 'SAVINGS'
  provider: string | null
  current_value: number
  initial_investment: number | null
  profit_amount: number | null      // current_value - initial_investment
  profit_percent: number | null     // percentage gain/loss vs initial
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AuditLog {
  id: number
  account_id: number | null
  account_name: string | null
  previous_value: number
  new_value: number
  change_amount: number
  change_percent: number | null
  note: string | null
  recorded_at: string
  /** Optional discriminator when lists from different audit tables are merged. */
  source?: string
}

export interface CategorySummary {
  category: string
  total_value: number
  account_count: number
  last_change_percent: number | null
}

export interface MortgageSummary {
  total_property_value_share: number
  total_outstanding_share: number
  total_equity: number
  mortgage_count: number
  total_property_value_raw: number
  total_outstanding_raw: number
}

export interface DashboardSummary {
  total_value: number
  accounts_total: number
  mortgage_equity: number
  categories: CategorySummary[]
  account_count: number
  mortgage_summary: MortgageSummary | null
  last_updated: string | null
}

export interface HistoryPoint {
  date: string
  total_value: number
  category: string | null
}

export interface DashboardHistory {
  points: HistoryPoint[]
}

export interface MortgagePart {
  id: number
  property_id: number
  name: string
  lender: string | null
  outstanding_balance: number
  interest_rate: number | null
  mortgage_type: 'REPAYMENT' | 'INTEREST_ONLY'
  term_years: number | null
  term_months: number | null
  monthly_payment: number | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  // Computed
  remaining_term_months: number | null
  monthly_interest: number | null
}

export interface Property {
  id: number
  name: string
  property_address: string | null
  original_price: number | null
  property_value: number
  ownership_percent: number
  notes: string | null
  purchase_date: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  mortgage_parts: MortgagePart[]
  // Computed
  total_outstanding: number
  equity: number
  property_value_share: number
  outstanding_share: number
  ltv_percent: number | null
  property_gain: number | null
  property_gain_percent: number | null
  weighted_avg_rate: number | null
  total_monthly_payment: number | null
}

export interface PropertyValueAuditLog {
  id: number
  property_id: number
  property_name: string | null
  previous_value: number
  new_value: number
  change_amount: number
  note: string | null
  recorded_at: string
}

export interface MortgagePartAuditLog {
  id: number
  part_id: number
  part_name: string | null
  property_name: string | null
  previous_value: number
  new_value: number
  change_amount: number
  note: string | null
  recorded_at: string
}

export interface ShareHolding {
  id: number
  account_id: number
  ticker: string
  display_name: string | null
  quantity: number
  avg_cost: number | null
  currency: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface LiveHolding {
  id: number
  account_id: number
  ticker: string
  display_name: string | null
  quantity: number
  avg_cost: number | null
  live_price: number | null
  currency: string | null
  live_value_native: number | null
  live_value_gbp: number | null
  cost_basis: number | null
  pnl_native: number | null
  pnl_percent: number | null
  short_name: string | null
  day_change_pct: number | null
  market_state: string | null
  price_error: string | null
  is_stale: boolean
  last_price_at: string | null
}

export interface PortfolioLive {
  account_id: number
  holdings: LiveHolding[]
  total_cost_basis_gbp: number | null
  total_live_value_gbp: number | null
  total_pnl_gbp: number | null
  total_pnl_percent: number | null
  gbpusd_rate: number | null
  gbpusd_rate_is_fallback?: boolean
  gbpusd_rate_stale?: boolean
  unpriced_tickers?: string[]
  last_refreshed: string
}

export interface ForecastSettings {
  end_year: number
  include_other: boolean
  return_rate_investments: number
  contrib_investments: number
  return_rate_retirement: number
  contrib_retirement: number
  inflation_rate: number
  adjust_inflation: boolean
  birth_year: number
  withdrawal_rate: number
}

// ── Data tools types ─────────────────────────────────────────────────────────

export interface SnapshotSkipped { account_id: number; name: string; reason: string }
export interface SnapshotRunResult {
  accounts_updated: number
  accounts_skipped: SnapshotSkipped[]
  ran_at: string
}
export interface SnapshotStatus {
  enabled: boolean
  hour_utc: number
  last_run_at: string | null
  last_result: SnapshotRunResult | null
}
export interface BackupFile { filename: string; size_bytes: number; created_at: string }

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Error thrown for any non-2xx API response. */
export class ApiError extends Error {
  status: number
  detail: string
  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function parseDetail(status: number, body: string): string {
  try {
    const detail = JSON.parse(body)?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d: any) => d?.msg ?? JSON.stringify(d)).join('; ')
  } catch { /* body wasn't JSON */ }
  return body.trim() || `Request failed (${status})`
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'same-origin',
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (res.status === 401 && !path.startsWith('/auth/')) {
    authState.checked = false
    authState.user = null
    if (window.location.pathname !== '/login') window.location.assign('/login')
  }
  if (!res.ok) {
    const body = await res.text()
    throw new ApiError(res.status, parseDetail(res.status, body))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

/** Human-readable message for any thrown value (ApiError, Error, string). */
export function apiErrorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.detail
  if (e instanceof Error) return e.message
  return String(e ?? 'Unknown error')
}

// ── Auth ─────────────────────────────────────────────────────────────────────

/** Cached auth state used by the router guard. */
export const authState: { checked: boolean; user: string | null } = { checked: false, user: null }

export const authApi = {
  /** Returns the username if the session cookie is valid, else null (cached after first check). */
  async check(force = false): Promise<string | null> {
    if (authState.checked && !force) return authState.user
    try {
      const res = await fetch(`${BASE}/auth/me`, { credentials: 'same-origin' })
      authState.user = res.ok ? (await res.json()).username : null
    } catch {
      authState.user = null
    }
    authState.checked = true
    return authState.user
  },
  async login(username: string, password: string): Promise<void> {
    const res = await fetch(`${BASE}/auth/login`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) {
      let detail = 'Login failed'
      try { detail = (await res.json()).detail || detail } catch { /* ignore */ }
      throw new Error(detail)
    }
    authState.user = username
    authState.checked = true
  },
  async logout(): Promise<void> {
    try {
      await fetch(`${BASE}/auth/logout`, { method: 'POST', credentials: 'same-origin' })
    } finally {
      authState.user = null
      authState.checked = true
    }
  },
}

// ── Accounts ─────────────────────────────────────────────────────────────────

export const api = {
  accounts: {
    list: (category?: string) =>
      request<Account[]>(`/accounts${category ? `?category=${category}` : ''}`),

    create: (payload: {
      name: string
      account_type: string
      category: string
      provider?: string
      current_value: number
      initial_investment?: number
      notes?: string
    }) => request<Account>('/accounts', { method: 'POST', body: JSON.stringify(payload) }),

    get: (id: number) => request<Account>(`/accounts/${id}`),

    updateValue: (id: number, new_value: number, note?: string) =>
      request<AuditLog>(`/accounts/${id}/value`, {
        method: 'PATCH',
        body: JSON.stringify({ new_value, note }),
      }),

    updateMeta: (id: number, payload: Partial<Pick<Account, 'name' | 'account_type' | 'category' | 'provider' | 'initial_investment' | 'notes'>>) =>
      request<Account>(`/accounts/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),

    delete: (id: number) => request<void>(`/accounts/${id}`, { method: 'DELETE' }),
  },

  audit: {
    list: (accountId?: number, limit = 100) =>
      request<AuditLog[]>(`/audit?limit=${limit}${accountId ? `&account_id=${accountId}` : ''}`),

    history: (accountId: number) =>
      request<AuditLog[]>(`/audit/${accountId}/history`),
  },

  dashboard: {
    summary: () => request<DashboardSummary>('/dashboard/summary'),
    history: (days = 365, category?: string) =>
      request<DashboardHistory>(`/dashboard/history?days=${days}${category ? `&category=${category}` : ''}`),
  },

  properties: {
    list: () => request<Property[]>('/properties'),

    create: (payload: {
      name: string
      property_address?: string
      original_price?: number
      property_value: number
      ownership_percent?: number
      notes?: string
      purchase_date?: string | null
    }) => request<Property>('/properties', { method: 'POST', body: JSON.stringify(payload) }),

    get: (id: number) => request<Property>(`/properties/${id}`),

    updateMeta: (id: number, payload: Partial<Pick<Property, 'name' | 'property_address' | 'original_price' | 'ownership_percent' | 'notes' | 'purchase_date'>>) =>
      request<Property>(`/properties/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),

    updateValue: (id: number, new_value: number, note?: string) =>
      request<PropertyValueAuditLog>(`/properties/${id}/value`, {
        method: 'PATCH',
        body: JSON.stringify({ new_value, note }),
      }),

    delete: (id: number) => request<void>(`/properties/${id}`, { method: 'DELETE' }),

    valueHistory: (id: number) => request<PropertyValueAuditLog[]>(`/properties/${id}/history`),

    // Mortgage Parts CRUD
    createPart: (propertyId: number, payload: {
      name: string
      lender?: string
      outstanding_balance: number
      interest_rate?: number
      mortgage_type: 'REPAYMENT' | 'INTEREST_ONLY'
      term_years?: number
      term_months?: number
      monthly_payment?: number
      notes?: string
    }) => request<MortgagePart>(`/properties/${propertyId}/parts`, { method: 'POST', body: JSON.stringify(payload) }),

    updatePartMeta: (partId: number, payload: Partial<Pick<MortgagePart, 'name' | 'lender' | 'interest_rate' | 'mortgage_type' | 'term_years' | 'term_months' | 'monthly_payment' | 'notes'>>) =>
      request<MortgagePart>(`/properties/parts/${partId}`, { method: 'PUT', body: JSON.stringify(payload) }),

    updatePartBalance: (partId: number, new_balance: number, note?: string) =>
      request<MortgagePartAuditLog>(`/properties/parts/${partId}/balance`, {
        method: 'PATCH',
        body: JSON.stringify({ new_balance, note }),
      }),

    deletePart: (partId: number) => request<void>(`/properties/parts/${partId}`, { method: 'DELETE' }),

    partHistory: (partId: number) => request<MortgagePartAuditLog[]>(`/properties/parts/${partId}/history`),
  },

  settings: {
    getForecast: () => request<ForecastSettings | null>('/settings/forecast'),
    saveForecast: (payload: ForecastSettings) =>
      request<ForecastSettings>('/settings/forecast', { method: 'PUT', body: JSON.stringify(payload) }),
  },

  snapshots: {
    status: () => request<SnapshotStatus>('/snapshots/status'),
    run: () => request<SnapshotRunResult>('/snapshots/run', { method: 'POST' }),
  },

  export: {
    // Downloads are same-origin anchor links; the session cookie authenticates them.
    accountsCsvUrl: () => `${BASE}/export/accounts.csv`,
    auditCsvUrl: (accountId?: number) =>
      `${BASE}/export/audit.csv${accountId ? `?account_id=${accountId}` : ''}`,
    propertiesCsvUrl: () => `${BASE}/export/properties.csv`,
    backupJsonUrl: () => `${BASE}/export/backup.json`,
    backups: () => request<BackupFile[]>('/export/backups'),
    runBackup: () => request<BackupFile>('/export/backups/run', { method: 'POST' }),
  },

  shares: {
    list: (accountId: number) =>
      request<ShareHolding[]>(`/shares/${accountId}`),

    create: (accountId: number, payload: {
      ticker: string
      display_name?: string
      quantity: number
      avg_cost?: number
      notes?: string
    }) => request<ShareHolding>(`/shares/${accountId}`, { method: 'POST', body: JSON.stringify(payload) }),

    update: (holdingId: number, payload: {
      ticker?: string
      display_name?: string
      quantity?: number
      avg_cost?: number
      notes?: string
    }) => request<ShareHolding>(`/shares/holding/${holdingId}`, { method: 'PUT', body: JSON.stringify(payload) }),

    delete: (holdingId: number) =>
      request<void>(`/shares/holding/${holdingId}`, { method: 'DELETE' }),

    live: (accountId: number) =>
      request<PortfolioLive>(`/shares/${accountId}/live`),

    allLive: (refresh = true) =>
      request<PortfolioLive[]>(`/shares/all-live${refresh ? '' : '?refresh=false'}`),

    sync: (accountId: number) =>
      request<{ previous_value: number; new_value: number; change_amount: number; tickers_synced: string[]; stale_tickers?: string[]; gbpusd_rate: number | null; gbpusd_rate_is_fallback?: boolean; gbpusd_rate_is_stale?: boolean; gbpusd_rate_fetched_at?: string | null }>(
        `/shares/${accountId}/sync`, { method: 'POST' }
      ),
  },
}
