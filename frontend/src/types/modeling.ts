export type ScenarioType = 'actual' | 'budget' | 'forecast'
export type LineItemType = 'input' | 'formula' | 'header'
export type Granularity = 'month' | 'quarter' | 'year'

export interface Model {
  id: number
  name: string
  description: string | null
  organisation_id: number
  created_at: string
  scenarios: Scenario[]
}

export interface Scenario {
  id: number
  model_id: number
  name: string
  scenario_type: ScenarioType
  created_at: string
}

export interface TimePeriod {
  id: number
  model_id: number
  label: string
  start_date: string
  end_date: string
  granularity: Granularity
  sort_order: number
}

export interface LineItem {
  id: number
  model_id: number
  name: string
  section: string | null
  item_type: LineItemType
  formula: string | null
  account_id: number | null
  sort_order: number
}

export interface GridCell {
  line_item_id: number
  time_period_id: number
  scenario_id: number
  value: number | null
  is_formula: boolean
  is_override: boolean
  formula_text: string | null
  error_message: string | null
}

export interface GridResponse {
  model_id: number
  scenario_id: number
  time_periods: TimePeriod[]
  line_items: LineItem[]
  cells: GridCell[]
}

// O(1) cell lookup: `${line_item_id}:${time_period_id}`
export type CellIndex = Record<string, GridCell>

export function buildCellIndex(cells: GridCell[]): CellIndex {
  const index: CellIndex = {}
  for (const cell of cells) {
    index[`${cell.line_item_id}:${cell.time_period_id}`] = cell
  }
  return index
}
