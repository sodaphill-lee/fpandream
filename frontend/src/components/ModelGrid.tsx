import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { GridResponse, GridCell, LineItem } from '@/types/modeling'
import { buildCellIndex } from '@/types/modeling'
import GridCellComponent from './GridCell'
import { grid } from '@/services/modeling'

interface Props {
  data: GridResponse
}

export default function ModelGrid({ data }: Props) {
  const queryClient = useQueryClient()
  const [selectedCell, setSelectedCell] = useState<GridCell | undefined>()
  const cellIndex = buildCellIndex(data.cells)

  const editMutation = useMutation({
    mutationFn: (payload: { line_item_id: number; time_period_id: number; value: number }) =>
      grid.updateCell(data.model_id, {
        ...payload,
        scenario_id: data.scenario_id,
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['grid', data.model_id, data.scenario_id] }),
  })

  const formulaBarText = selectedCell?.formula_text
    ? `= ${selectedCell.formula_text}`
    : ''

  return (
    <div>
      {/* Formula bar */}
      <div className="h-8 flex items-center px-3 bg-gray-50 border-b text-sm text-gray-500 font-mono">
        {formulaBarText || (selectedCell ? 'Input cell' : 'Select a cell')}
        {selectedCell?.is_override && (
          <span className="ml-3 text-xs text-yellow-600">(manually overridden)</span>
        )}
      </div>

      {/* Grid */}
      <div className="overflow-auto">
        <table className="border-collapse text-sm w-full">
          <thead>
            <tr className="bg-gray-100">
              <th className="border-r border-b px-3 py-2 text-left font-semibold text-gray-700 min-w-48 sticky left-0 bg-gray-100 z-10">
                Line Item
              </th>
              {data.time_periods.map(p => (
                <th key={p.id} className="border-r border-b px-2 py-2 text-right font-medium text-gray-600 min-w-28">
                  {p.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.line_items.map(li => (
              <LineItemRow
                key={li.id}
                lineItem={li}
                timePeriods={data.time_periods}
                cellIndex={cellIndex}
                selectedCell={selectedCell}
                onSelect={setSelectedCell}
                onEdit={(periodId, value) =>
                  editMutation.mutate({ line_item_id: li.id, time_period_id: periodId, value })
                }
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function LineItemRow({
  lineItem,
  timePeriods,
  cellIndex,
  selectedCell,
  onSelect,
  onEdit,
}: {
  lineItem: LineItem
  timePeriods: GridResponse['time_periods']
  cellIndex: ReturnType<typeof buildCellIndex>
  selectedCell: GridCell | undefined
  onSelect: (cell: GridCell | undefined) => void
  onEdit: (periodId: number, value: number) => void
}) {
  if (lineItem.item_type === 'header') {
    return (
      <tr className="bg-gray-200">
        <td
          colSpan={timePeriods.length + 1}
          className="px-3 py-1.5 font-bold text-gray-700 text-xs uppercase tracking-wide"
        >
          {lineItem.name}
        </td>
      </tr>
    )
  }

  const isFormula = lineItem.item_type === 'formula'

  return (
    <tr className="hover:bg-gray-50">
      <td className={`border-r border-b px-3 py-1 sticky left-0 bg-white z-10 ${isFormula ? 'font-medium' : ''}`}>
        {lineItem.section && <span className="text-gray-400 text-xs mr-2">{lineItem.section}</span>}
        {lineItem.name}
        {isFormula && <span className="ml-1 text-blue-400 text-xs">ƒ</span>}
      </td>
      {timePeriods.map(period => {
        const cell = cellIndex[`${lineItem.id}:${period.id}`]
        return (
          <GridCellComponent
            key={period.id}
            cell={cell}
            isSelected={selectedCell?.line_item_id === lineItem.id && selectedCell?.time_period_id === period.id}
            onSelect={onSelect}
            onEdit={(value) => onEdit(period.id, value)}
          />
        )
      })}
    </tr>
  )
}
