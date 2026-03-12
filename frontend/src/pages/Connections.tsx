import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { organisations, xero, myob } from '@/services/api'
import type { Connection } from '@/types'

const ORG_ID = 1 // TODO: replace with auth context

export default function Connections() {
  const queryClient = useQueryClient()

  const { data: connections = [], isLoading } = useQuery({
    queryKey: ['connections', ORG_ID],
    queryFn: () => organisations.connections(ORG_ID),
  })

  const syncMutation = useMutation({
    mutationFn: (conn: Connection) =>
      conn.provider === 'xero' ? xero.sync(conn.id) : myob.sync(conn.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['connections'] }),
  })

  const connectXero = async () => {
    const url = await xero.getAuthUrl(ORG_ID)
    window.location.href = url
  }

  const connectMyob = async () => {
    const url = await myob.getAuthUrl(ORG_ID)
    window.location.href = url
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Connections</h1>

      <div className="flex gap-4 mb-8">
        <button
          onClick={connectXero}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Connect Xero
        </button>
        <button
          onClick={connectMyob}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Connect MYOB
        </button>
      </div>

      {isLoading && <p className="text-gray-500">Loading...</p>}

      <div className="space-y-4">
        {connections.map(conn => (
          <div key={conn.id} className="border rounded p-4 flex items-center justify-between">
            <div>
              <p className="font-semibold capitalize">{conn.provider}</p>
              <p className="text-sm text-gray-600">{conn.provider_org_name}</p>
              {conn.last_synced_at && (
                <p className="text-xs text-gray-400">
                  Last synced: {new Date(conn.last_synced_at).toLocaleString()}
                </p>
              )}
            </div>
            <button
              onClick={() => syncMutation.mutate(conn)}
              disabled={syncMutation.isPending}
              className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200 text-sm"
            >
              {syncMutation.isPending ? 'Syncing...' : 'Sync Now'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
