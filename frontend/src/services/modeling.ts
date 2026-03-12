import axios from 'axios'
import type {
  Model, Scenario, TimePeriod, LineItem, GridResponse,
} from '@/types/modeling'

const api = axios.create({ baseURL: '/api' })

export const models = {
  list: (orgId: number) =>
    api.get<Model[]>('/models/', { params: { organisation_id: orgId } }).then(r => r.data),
  create: (payload: { name: string; description?: string; organisation_id: number }) =>
    api.post<Model>('/models/', payload).then(r => r.data),
  get: (id: number) =>
    api.get<Model>(`/models/${id}`).then(r => r.data),
  delete: (id: number) =>
    api.delete(`/models/${id}`),
}

export const scenarios = {
  list: (modelId: number) =>
    api.get<Scenario[]>(`/models/${modelId}/scenarios/`).then(r => r.data),
  create: (modelId: number, payload: { name: string; scenario_type: string }) =>
    api.post<Scenario>(`/models/${modelId}/scenarios/`, payload).then(r => r.data),
  delete: (modelId: number, scenarioId: number) =>
    api.delete(`/models/${modelId}/scenarios/${scenarioId}`),
}

export const timePeriods = {
  list: (modelId: number) =>
    api.get<TimePeriod[]>(`/models/${modelId}/time_periods/`).then(r => r.data),
  create: (modelId: number, payload: Omit<TimePeriod, 'id' | 'model_id'>) =>
    api.post<TimePeriod>(`/models/${modelId}/time_periods/`, payload).then(r => r.data),
  delete: (modelId: number, periodId: number) =>
    api.delete(`/models/${modelId}/time_periods/${periodId}`),
}

export const lineItems = {
  list: (modelId: number) =>
    api.get<LineItem[]>(`/models/${modelId}/line_items/`).then(r => r.data),
  create: (modelId: number, payload: Partial<LineItem>) =>
    api.post<LineItem>(`/models/${modelId}/line_items/`, payload).then(r => r.data),
  update: (modelId: number, itemId: number, payload: Partial<LineItem>) =>
    api.patch<LineItem>(`/models/${modelId}/line_items/${itemId}`, payload).then(r => r.data),
  delete: (modelId: number, itemId: number) =>
    api.delete(`/models/${modelId}/line_items/${itemId}`),
}

export const grid = {
  calculate: (modelId: number, scenarioId: number) =>
    api.post<GridResponse>(`/models/${modelId}/calculate`, null, {
      params: { scenario_id: scenarioId },
    }).then(r => r.data),
  get: (modelId: number, scenarioId: number) =>
    api.get<GridResponse>(`/models/${modelId}/grid`, {
      params: { scenario_id: scenarioId },
    }).then(r => r.data),
  updateCell: (modelId: number, payload: {
    line_item_id: number
    scenario_id: number
    time_period_id: number
    value: number
  }) => api.patch(`/models/${modelId}/cells/`, payload).then(r => r.data),
  clearOverride: (modelId: number, payload: {
    line_item_id: number
    scenario_id: number
    time_period_id: number
  }) => api.delete(`/models/${modelId}/cells/override`, { data: payload }).then(r => r.data),
}
