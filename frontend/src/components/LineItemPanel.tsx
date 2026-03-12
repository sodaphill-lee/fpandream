import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { LineItem, LineItemType } from '@/types/modeling'
import { lineItems as lineItemsApi } from '@/services/modeling'

interface Props {
  modelId: number
  items: LineItem[]
  onClose: () => void
}

export default function LineItemPanel({ modelId, items, onClose }: Props) {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['line_items', modelId] })

  const addMutation = useMutation({
    mutationFn: (payload: Partial<LineItem>) => lineItemsApi.create(modelId, payload),
    onSuccess: invalidate,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...payload }: Partial<LineItem> & { id: number }) =>
      lineItemsApi.update(modelId, id, payload),
    onSuccess: invalidate,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => lineItemsApi.delete(modelId, id),
    onSuccess: invalidate,
  })

  const addItem = (type: LineItemType) => {
    const maxOrder = items.length > 0 ? Math.max(...items.map(i => i.sort_order)) : -1
    addMutation.mutate({
      name: type === 'header' ? 'New Section' : 'New Line Item',
      item_type: type,
      sort_order: maxOrder + 1,
    })
  }

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl border-l flex flex-col z-20">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h2 className="font-semibold text-gray-800">Edit Line Items</h2>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
      </div>

      <div className="flex gap-2 px-4 py-2 border-b">
        <button
          onClick={() => addItem('input')}
          className="flex-1 text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
        >
          + Input
        </button>
        <button
          onClick={() => addItem('formula')}
          className="flex-1 text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
        >
          + Formula
        </button>
        <button
          onClick={() => addItem('header')}
          className="flex-1 text-xs px-2 py-1 bg-gray-100 rounded hover:bg-gray-200"
        >
          + Header
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {items.map(item => (
          <LineItemRow
            key={item.id}
            item={item}
            onUpdate={(payload) => updateMutation.mutate({ id: item.id, ...payload })}
            onDelete={() => deleteMutation.mutate(item.id)}
          />
        ))}
        {items.length === 0 && (
          <p className="text-center text-gray-400 text-sm mt-8">No line items yet.</p>
        )}
      </div>
    </div>
  )
}

function LineItemRow({
  item,
  onUpdate,
  onDelete,
}: {
  item: LineItem
  onUpdate: (payload: Partial<LineItem>) => void
  onDelete: () => void
}) {
  const [name, setName] = useState(item.name)
  const [formula, setFormula] = useState(item.formula ?? '')

  const typeColors: Record<LineItemType, string> = {
    input: 'bg-gray-100 text-gray-600',
    formula: 'bg-blue-100 text-blue-700',
    header: 'bg-gray-200 text-gray-700 font-bold',
  }

  return (
    <div className="px-4 py-3 border-b hover:bg-gray-50 group">
      <div className="flex items-center gap-2 mb-1">
        <span className={`text-xs px-1.5 py-0.5 rounded ${typeColors[item.item_type]}`}>
          {item.item_type}
        </span>
        <input
          value={name}
          onChange={e => setName(e.target.value)}
          onBlur={() => name !== item.name && onUpdate({ name })}
          className="flex-1 text-sm bg-transparent border-b border-transparent focus:border-gray-300 outline-none"
        />
        <button
          onClick={onDelete}
          className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 text-xs"
        >
          ✕
        </button>
      </div>

      {item.item_type === 'formula' && (
        <input
          value={formula}
          onChange={e => setFormula(e.target.value)}
          onBlur={() => formula !== (item.formula ?? '') && onUpdate({ formula })}
          placeholder="e.g. Revenue - COGS"
          className="w-full text-xs font-mono bg-blue-50 border border-blue-100 rounded px-2 py-1 outline-none focus:border-blue-300"
        />
      )}
    </div>
  )
}
