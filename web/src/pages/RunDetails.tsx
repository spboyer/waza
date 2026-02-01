import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'

export default function RunDetails() {
  const { id } = useParams<{ id: string }>()
  const [liveStatus, setLiveStatus] = useState<any>(null)

  const { data: runData } = useQuery({
    queryKey: ['run', id],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/api/runs/${id}`)
      return res.json()
    },
    refetchInterval: (data: any) => {
      // Refetch every 2s if run is still active
      if (data?.status === 'running' || data?.status === 'queued') {
        return 2000
      }
      return false
    },
  })

  // Connect to SSE for real-time updates
  useEffect(() => {
    if (!id) return

    const eventSource = new EventSource(`http://localhost:8000/api/runs/${id}/stream`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setLiveStatus(data)
      } catch (error) {
        console.error('Failed to parse SSE data:', error)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
    }

    return () => {
      eventSource.close()
    }
  }, [id])

  const status = liveStatus || runData

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Run Details</h1>
        <p className="text-gray-400">Run ID: {id}</p>
      </div>

      {/* Status Card */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">Status</h3>
            <p className={`text-lg font-bold ${
              status?.status === 'completed' ? 'text-green-400' :
              status?.status === 'running' ? 'text-blue-400' :
              status?.status === 'failed' ? 'text-red-400' :
              'text-gray-400'
            }`}>
              {status?.status || 'Loading...'}
            </p>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">Progress</h3>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${status?.progress || 0}%` }}
                />
              </div>
              <span className="text-sm font-medium">{status?.progress || 0}%</span>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">Tasks</h3>
            <p className="text-lg font-medium">
              {status?.completed_tasks || 0} / {status?.total_tasks || 0}
            </p>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">Current Task</h3>
            <p className="text-sm truncate">
              {status?.current_task || 'None'}
            </p>
          </div>
        </div>
      </div>

      {/* Results */}
      {status?.results && status.results.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Results</h2>
          <div className="space-y-2">
            {status.results.map((result: any, idx: number) => (
              <div
                key={idx}
                className="flex justify-between items-center bg-gray-700 rounded p-3"
              >
                <span>{result.task}</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  result.status === 'passed' ? 'bg-green-600' : 'bg-red-600'
                }`}>
                  {result.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transcript */}
      {runData?.transcript && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Transcript</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {runData.transcript.map((turn: any, idx: number) => (
              <div key={idx} className={`p-3 rounded ${
                turn.role === 'user' ? 'bg-blue-900/30' :
                turn.role === 'assistant' ? 'bg-green-900/30' :
                'bg-gray-700'
              }`}>
                <div className="text-xs text-gray-400 mb-1">{turn.role}</div>
                <div className="text-sm">{turn.content}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {status?.error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-6 mt-6">
          <h2 className="text-xl font-bold text-red-400 mb-2">Error</h2>
          <p className="text-sm">{status.error}</p>
        </div>
      )}
    </div>
  )
}
