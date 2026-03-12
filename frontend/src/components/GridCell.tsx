import { useState, useRef, useEffect } from 'react'
import type { GridCell as GridCellType } from '@/types/modeling'

interface Props {
  cell: GridCellType | undefined
  onEdit: (value: number) => void
  onSelect: (cell: GridCellType | undefined) => void
  isSelected: boolean
}

function formatValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return ''
  return value.toLocaleString('en-AU', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

export default function GridCellComponent({ cell, onEdit, onSelect, isSelected }: Props) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editing])

  const startEdit = () => {
    if (!cell || cell.is_formula && !cell.is_override) {
      // formula cells: only editable to override
    }
    setDraft(cell?.value !== null && cell?.value !== undefined ? String(cell.value) : '')
    setEditing(true)
  }

  const commitEdit = () => {
    setEditing(false)
    const num = parseFloat(draft)
    if (!isNaN(num)) {
      onEdit(num)
    }
  }

  const cancelEdit = () => {
    setEditing(false)
  }

  const bgClass = cell?.error_message
    ? 'bg-red-50'
    : cell?.is_override
      ? 'bg-yellow-50'
      : cell?.is_formula
        ? 'bg-blue-50'
        : ''

  if (editing) {
    return (
      <td className={`border-r border-b px-2 py-1 ${bgClass}`}>
        <input
          ref={inputRef}
          value={draft}
          onChange={e => setDraft(e.target.value)}
          onBlur={commitEdit}
          onKeyDown={e => {
            if (e.key === 'Enter') commitEdit()
            if (e.key === 'Escape') cancelEdit()
          }}
          className="w-full text-right text-sm bg-transparent outline outline-1 outline-blue-400 rounded px-1"
        />
      </td>
    )
  }

  return (
    <td
      className={`border-r border-b px-2 py-1 text-right text-sm cursor-pointer select-none
        ${bgClass}
        ${isSelected ? 'outline outline-2 outline-blue-500' : ''}
        hover:bg-blue-50`}
      onClick={() => onSelect(cell)}
      onDoubleClick={startEdit}
      title={cell?.error_message ?? undefined}
    >
      {cell?.error_message
        ? <span className="text-red-500 text-xs">ERR</span>
        : <span className={cell?.is_override ? 'italic' : ''}>
            {formatValue(cell?.value)}
          </span>
      }
    </td>
  )
}
