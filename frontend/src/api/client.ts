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

// ── Helpers ──────────────────────────────────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
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

    updateMeta: (id: number, payload: Partial<Omit<Account, 'id' | 'created_at' | 'updated_at' | 'current_value'>>) =>
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
}
