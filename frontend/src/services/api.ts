import axios from 'axios'
import type { Organisation, Connection } from '@/types'

const api = axios.create({ baseURL: '/api' })

export const organisations = {
  list: () => api.get<Organisation[]>('/organisations/').then(r => r.data),
  create: (name: string) => api.post<Organisation>('/organisations/', { name }).then(r => r.data),
  get: (id: number) => api.get<Organisation>(`/organisations/${id}`).then(r => r.data),
  connections: (id: number) => api.get<Connection[]>(`/organisations/${id}/connections`).then(r => r.data),
}

export const xero = {
  getAuthUrl: (orgId: number) =>
    api.get<{ auth_url: string }>(`/xero/connect/${orgId}`).then(r => r.data.auth_url),
  sync: (connectionId: number) =>
    api.post(`/xero/sync/${connectionId}`).then(r => r.data),
}

export const myob = {
  getAuthUrl: (orgId: number) =>
    api.get<{ auth_url: string }>(`/myob/connect/${orgId}`).then(r => r.data.auth_url),
  sync: (connectionId: number) =>
    api.post(`/myob/sync/${connectionId}`).then(r => r.data),
}
