import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { models as modelsApi, scenarios as scenariosApi, lineItems as lineItemsApi, grid } from '@/services/modeling'
import type { ScenarioType } from '@/types/modeling'
import ScenarioSelector from '@/components/ScenarioSelector'
import ModelGrid from '@/components/ModelGrid'
import LineItemPanel from '@/components/LineItemPanel'

export default function ModelDetail() {
  const { modelId } = useParams<{ modelId: string }>()
  const id = Number(modelId)
  const queryClient = useQueryClient()

  const [activeScenarioId, setActiveScenarioId] = useState<number | null>(null)
  const [showPanel, setShowPanel] = useState(false)

  const { data: model } = useQuery({
    queryKey: ['model', id],
    queryFn: () => modelsApi.get(id),
    enabled: !!id,
  })

  const scenarios = model?.scenarios ?? []

  // Auto-select first scenario
  const effectiveScenarioId = activeScenarioId ?? scenarios[0]?.id ?? null

  const { data: items = [] } = useQuery({
    queryKey: ['line_items', id],
    queryFn: () => lineItemsApi.list(id),
    enabled: !!id,
  })

  const { data: gridData, isFetching: gridLoading } = useQuery({
    queryKey: ['grid', id, effectiveScenarioId],
    queryFn: () => grid.get(id, effectiveScenarioId!),
    enabled: !!effectiveScenarioId,
  })

  const calculateMutation = useMutation({
    mutationFn: () => grid.calculate(id, effectiveScenarioId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grid', id, effectiveScenarioId] }),
  })

  const addScenarioMutation = useMutation({
    mutationFn: (type: ScenarioType) =>
      scenariosApi.create(id, { name: type.charAt(0).toUpperCase() + type.slice(1), scenario_type: type }),
    onSuccess: (newScenario) => {
      queryClient.invalidateQueries({ queryKey: ['model', id] })
      setActiveScenarioId(newScenario.id)
    },
  })

  if (!model) {
    return <div className="p-8 text-gray-400">Loading model...</div>
  }

  return (
    <div className="flex flex-col h-[calc(100vh-48px)]">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-6 py-3 border-b bg-white">
        <h1 className="text-lg font-bold text-gray-800">{model.name}</h1>
        <div className="flex items-center gap-4">
          <ScenarioSelector
            scenarios={scenarios}
            activeScenarioId={effectiveScenarioId}
            onChange={setActiveScenarioId}
            onAdd={(type) => addScenarioMutation.mutate(type)}
          />
          <button
            onClick={() => setShowPanel(p => !p)}
            className="px-3 py-1.5 text-sm border rounded hover:bg-gray-50"
          >
            Edit Line Items
          </button>
          <button
            onClick={() => calculateMutation.mutate()}
            disabled={!effectiveScenarioId || calculateMutation.isPending}
            className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {calculateMutation.isPending ? 'Calculating...' : 'Calculate'}
          </button>
        </div>
      </div>

      {/* Grid area */}
      <div className="flex-1 overflow-hidden">
        {!effectiveScenarioId ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            Add a scenario to get started.
          </div>
        ) : gridLoading ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            Loading grid...
          </div>
        ) : gridData ? (
          <ModelGrid data={gridData} />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            Click Calculate to compute the model.
          </div>
        )}
      </div>

      {/* Line item panel */}
      {showPanel && (
        <LineItemPanel
          modelId={id}
          items={items}
          onClose={() => setShowPanel(false)}
        />
      )}
    </div>
  )
}
