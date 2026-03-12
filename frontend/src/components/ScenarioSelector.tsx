import type { Scenario, ScenarioType } from '@/types/modeling'

const SCENARIO_LABELS: Record<ScenarioType, string> = {
  actual: 'Actual',
  budget: 'Budget',
  forecast: 'Forecast',
}

interface Props {
  scenarios: Scenario[]
  activeScenarioId: number | null
  onChange: (id: number) => void
  onAdd: (type: ScenarioType) => void
}

export default function ScenarioSelector({ scenarios, activeScenarioId, onChange, onAdd }: Props) {
  const types: ScenarioType[] = ['actual', 'budget', 'forecast']

  return (
    <div className="flex gap-1 border rounded overflow-hidden">
      {types.map(type => {
        const scenario = scenarios.find(s => s.scenario_type === type)
        const isActive = scenario && scenario.id === activeScenarioId

        return (
          <button
            key={type}
            onClick={() => scenario ? onChange(scenario.id) : onAdd(type)}
            className={`px-4 py-1.5 text-sm font-medium transition-colors ${
              isActive
                ? 'bg-blue-600 text-white'
                : scenario
                  ? 'bg-white text-gray-700 hover:bg-gray-50'
                  : 'bg-white text-gray-400 hover:bg-gray-50'
            }`}
          >
            {SCENARIO_LABELS[type]}
            {!scenario && <span className="ml-1 text-xs">+</span>}
          </button>
        )
      })}
    </div>
  )
}
