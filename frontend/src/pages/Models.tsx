import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { models as modelsApi } from '@/services/modeling'

const ORG_ID = 1 // TODO: replace with auth context

export default function Models() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')

  const { data: modelList = [], isLoading } = useQuery({
    queryKey: ['models', ORG_ID],
    queryFn: () => modelsApi.list(ORG_ID),
  })

  const createMutation = useMutation({
    mutationFn: () => modelsApi.create({ name, organisation_id: ORG_ID }),
    onSuccess: (model) => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
      setShowForm(false)
      setName('')
      navigate(`/models/${model.id}`)
    },
  })

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Financial Models</h1>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
        >
          + New Model
        </button>
      </div>

      {showForm && (
        <div className="mb-6 p-4 border rounded bg-gray-50 flex gap-3 items-center">
          <input
            autoFocus
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && createMutation.mutate()}
            placeholder="Model name (e.g. FY2026 Budget)"
            className="flex-1 border rounded px-3 py-1.5 text-sm outline-none focus:border-blue-400"
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={!name.trim() || createMutation.isPending}
            className="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            Create
          </button>
          <button onClick={() => setShowForm(false)} className="text-gray-500 hover:text-gray-700 text-sm">
            Cancel
          </button>
        </div>
      )}

      {isLoading && <p className="text-gray-400">Loading...</p>}

      <div className="grid gap-4">
        {modelList.map(model => (
          <div
            key={model.id}
            onClick={() => navigate(`/models/${model.id}`)}
            className="p-4 border rounded hover:border-blue-400 hover:shadow-sm cursor-pointer transition-all"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-gray-800">{model.name}</h2>
                {model.description && (
                  <p className="text-sm text-gray-500 mt-0.5">{model.description}</p>
                )}
              </div>
              <div className="flex gap-2">
                {model.scenarios.map(s => (
                  <span
                    key={s.id}
                    className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 capitalize"
                  >
                    {s.scenario_type}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}

        {!isLoading && modelList.length === 0 && (
          <p className="text-center text-gray-400 py-12">
            No models yet. Create one to get started.
          </p>
        )}
      </div>
    </div>
  )
}
