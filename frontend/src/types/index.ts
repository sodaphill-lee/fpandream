export interface Organisation {
  id: number
  name: string
  created_at: string
}

export interface Connection {
  id: number
  organisation_id: number
  provider: 'xero' | 'myob'
  provider_org_name: string | null
  last_synced_at: string | null
  created_at: string
}

export interface Account {
  id: number
  code: string | null
  name: string
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | null
  description: string | null
}

export interface Transaction {
  id: number
  date: string
  description: string | null
  amount: number
  currency: string
  account_id: number | null
}
