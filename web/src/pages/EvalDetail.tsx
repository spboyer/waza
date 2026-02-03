import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, 
  Play, 
  Clock, 
  CheckCircle2, 
  XCircle,
  ChevronRight
} from 'lucide-react'
import { getEval, listRuns, startRun } from '../api/client'

export default function EvalDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const { data: evalData, isLoading: evalLoading } = useQuery({
    queryKey: ['eval', id],
    queryFn: () => getEval(id!),
    enabled: !!id,
  })
  
  const { data: runs = [] } = useQuery({
    queryKey: ['runs', id],
    queryFn: () => listRuns(id),
    enabled: !!id,
  })
  
  const runMutation = useMutation({
    mutationFn: () => startRun(id!),
    onSuccess: (run) => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      navigate(`/runs/${run.id}`)
    },
  })
  
  if (evalLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-waza-600" />
      </div>
    )
  }
  
  if (!evalData) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Eval not found</p>
        <Link to="/evals" className="text-waza-600 hover:text-waza-700 mt-2 inline-block">
          Back to evals
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link 
            to="/evals" 
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to evals
          </Link>
          <h1 className="text-2xl font-semibold text-gray-900">{evalData.name}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {evalData.skill} • {evalData.task_count} tasks
          </p>
        </div>
        <button
          onClick={() => runMutation.mutate()}
          disabled={runMutation.isPending}
          className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
        >
          <Play className="w-4 h-4" />
          {runMutation.isPending ? 'Starting...' : 'Run Eval'}
        </button>
      </div>
      
      {/* Run History */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Run History</h2>
        </div>
        
        {runs.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No runs yet. Click "Run Eval" to start!
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {runs.map(run => (
              <Link
                key={run.id}
                to={`/runs/${run.id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <StatusIcon status={run.status} />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900">
                    {new Date(run.started_at).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-500">
                    {run.model} • {run.executor}
                  </div>
                </div>
                {run.results && (
                  <div className={`text-sm font-medium ${
                    run.results.pass_rate === 1 ? 'text-green-600' : 
                    run.results.pass_rate >= 0.5 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {(run.results.pass_rate * 100).toFixed(0)}% passed
                  </div>
                )}
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'running':
      return <Clock className="w-5 h-5 text-yellow-500 animate-pulse" />
    case 'completed':
      return <CheckCircle2 className="w-5 h-5 text-green-500" />
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />
    default:
      return <Clock className="w-5 h-5 text-gray-400" />
  }
}
