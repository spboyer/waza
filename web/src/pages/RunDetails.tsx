import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Activity, CheckCircle2, XCircle, Clock, MessageSquare, AlertCircle } from 'lucide-react'

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
      if (data?.status === 'running' || data?.status === 'queued') {
        return 2000
      }
      return false
    },
  })

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

  const getStatusConfig = (statusText: string) => {
    const configs = {
      completed: { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500/30' },
      running: { icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/30' },
      failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30' },
      queued: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/30' },
    }
    return configs[statusText as keyof typeof configs] || configs.queued
  }

  const statusConfig = getStatusConfig(status?.status || 'loading')
  const StatusIcon = statusConfig.icon

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Run Details
        </h1>
        <p className="text-gray-400 text-lg font-mono">{id}</p>
      </div>

      {/* Status Overview */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-8 shadow-xl">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <p className="text-sm font-semibold text-gray-400 mb-3">Status</p>
            <div className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg ${statusConfig.bg} ${statusConfig.border} border`}>
              <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
              <span className={`font-bold text-lg ${statusConfig.color}`}>
                {status?.status || 'Loading...'}
              </span>
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold text-gray-400 mb-3">Progress</p>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-300">{status?.progress || 0}%</span>
                <span className="text-gray-500">
                  {status?.completed_tasks || 0} / {status?.total_tasks || 0} tasks
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500 ease-out relative overflow-hidden"
                  style={{ width: `${status?.progress || 0}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                </div>
              </div>
            </div>
          </div>

          <div className="md:col-span-2">
            <p className="text-sm font-semibold text-gray-400 mb-3">Current Task</p>
            <div className="bg-gray-700/30 rounded-lg p-3 border border-gray-600/50">
              <p className="text-sm text-gray-300 truncate">
                {status?.current_task || 'None'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {status?.results && status.results.length > 0 && (
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-8 shadow-xl">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <CheckCircle2 className="w-6 h-6 mr-3 text-green-400" />
            Results
          </h2>
          <div className="space-y-3">
            {status.results.map((result: any, idx: number) => (
              <div
                key={idx}
                className="flex justify-between items-center bg-gray-700/30 rounded-lg p-4 border border-gray-600/50 hover:bg-gray-700/50 transition-all"
              >
                <span className="font-medium">{result.task}</span>
                <span className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-bold border ${
                  result.status === 'passed'
                    ? 'bg-green-500/20 text-green-400 border-green-500/30'
                    : 'bg-red-500/20 text-red-400 border-red-500/30'
                }`}>
                  {result.status === 'passed' ? (
                    <CheckCircle2 className="w-3 h-3" />
                  ) : (
                    <XCircle className="w-3 h-3" />
                  )}
                  <span>{result.status}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Transcript */}
      {runData?.transcript && (
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-8 shadow-xl">
          <h2 className="text-2xl font-bold mb-6 flex items-center">
            <MessageSquare className="w-6 h-6 mr-3 text-purple-400" />
            Transcript
          </h2>
          <div className="space-y-3 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
            {runData.transcript.map((turn: any, idx: number) => (
              <div key={idx} className={`p-4 rounded-lg border ${
                turn.role === 'user' ? 'bg-blue-900/20 border-blue-500/20' :
                turn.role === 'assistant' ? 'bg-green-900/20 border-green-500/20' :
                'bg-gray-700/20 border-gray-600/20'
              }`}>
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`text-xs font-bold px-2 py-1 rounded ${
                    turn.role === 'user' ? 'bg-blue-500/30 text-blue-300' :
                    turn.role === 'assistant' ? 'bg-green-500/30 text-green-300' :
                    'bg-gray-500/30 text-gray-300'
                  }`}>
                    {turn.role}
                  </span>
                </div>
                <p className="text-sm text-gray-300 leading-relaxed">{turn.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {status?.error && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-8 shadow-xl">
          <h2 className="text-xl font-bold text-red-400 mb-4 flex items-center">
            <AlertCircle className="w-6 h-6 mr-3" />
            Error
          </h2>
          <p className="text-sm text-gray-300 font-mono bg-gray-900/50 p-4 rounded-lg">{status.error}</p>
        </div>
      )}
    </div>
  )
}
