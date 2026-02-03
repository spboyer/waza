import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { 
  ArrowLeft, 
  CheckCircle2, 
  XCircle, 
  Clock,
  ChevronDown,
  ChevronRight,
  MessageSquare
} from 'lucide-react'
import { getRun, streamRun } from '../api/client'
import type { Run, RunProgress, TaskResult } from '../types'

export default function RunDetail() {
  const { id } = useParams<{ id: string }>()
  const [progress, setProgress] = useState<RunProgress | null>(null)
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set())
  
  const { data: run, isLoading, refetch } = useQuery({
    queryKey: ['run', id],
    queryFn: () => getRun(id!),
    enabled: !!id,
    refetchInterval: (query) => 
      query.state.data?.status === 'running' ? 2000 : false,
  })
  
  // SSE streaming for live updates
  useEffect(() => {
    if (!id || run?.status !== 'running') return
    
    const cleanup = streamRun(id, (data) => {
      if ('current_task' in data) {
        setProgress(data)
      } else {
        // Results received, refetch
        refetch()
      }
    })
    
    return cleanup
  }, [id, run?.status, refetch])
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-waza-600" />
      </div>
    )
  }
  
  if (!run) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Run not found</p>
        <Link to="/evals" className="text-waza-600 hover:text-waza-700 mt-2 inline-block">
          Back to evals
        </Link>
      </div>
    )
  }
  
  const toggleTask = (taskId: string) => {
    setExpandedTasks(prev => {
      const next = new Set(prev)
      if (next.has(taskId)) {
        next.delete(taskId)
      } else {
        next.add(taskId)
      }
      return next
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link 
          to={`/evals/${run.eval_id}`}
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to eval
        </Link>
        <div className="flex items-center gap-4">
          <StatusBadge status={run.status} />
          <h1 className="text-2xl font-semibold text-gray-900">
            Run {run.id.slice(0, 8)}
          </h1>
        </div>
        <p className="text-sm text-gray-500 mt-1">
          {run.model} • {run.executor} • Started {new Date(run.started_at).toLocaleString()}
        </p>
      </div>
      
      {/* Progress bar for running */}
      {run.status === 'running' && progress && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">{progress.message}</span>
            <span className="text-sm text-gray-500">
              Task {progress.current_task}/{progress.total_tasks}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-waza-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(progress.current_task / progress.total_tasks) * 100}%` }}
            />
          </div>
        </div>
      )}
      
      {/* Results */}
      {run.results && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <SummaryCard 
              label="Pass Rate" 
              value={`${(run.results.pass_rate * 100).toFixed(0)}%`}
              color={run.results.pass_rate === 1 ? 'green' : run.results.pass_rate >= 0.5 ? 'yellow' : 'red'}
            />
            <SummaryCard label="Passed" value={run.results.passed} color="green" />
            <SummaryCard label="Failed" value={run.results.failed} color="red" />
            <SummaryCard label="Total" value={run.results.total_tasks} color="gray" />
          </div>
          
          {/* Task results */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Task Results</h2>
            </div>
            <div className="divide-y divide-gray-100">
              {run.results.tasks.map(task => (
                <TaskResultRow 
                  key={task.id}
                  task={task}
                  expanded={expandedTasks.has(task.id)}
                  onToggle={() => toggleTask(task.id)}
                />
              ))}
            </div>
          </div>
          
          {/* Suggestions */}
          {run.results.suggestions && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-yellow-800 mb-3">
                💡 Improvement Suggestions
              </h3>
              <div className="prose prose-sm prose-yellow max-w-none">
                <pre className="whitespace-pre-wrap text-yellow-900 bg-yellow-100 p-4 rounded">
                  {run.results.suggestions}
                </pre>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: Run['status'] }) {
  const styles = {
    pending: 'bg-gray-100 text-gray-700',
    running: 'bg-blue-100 text-blue-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  }
  
  return (
    <span className={`px-2.5 py-0.5 rounded-full text-sm font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}

function SummaryCard({ 
  label, 
  value, 
  color 
}: { 
  label: string
  value: string | number
  color: 'green' | 'yellow' | 'red' | 'gray'
}) {
  const colors = {
    green: 'border-green-200 bg-green-50',
    yellow: 'border-yellow-200 bg-yellow-50',
    red: 'border-red-200 bg-red-50',
    gray: 'border-gray-200 bg-gray-50',
  }
  
  return (
    <div className={`rounded-lg border p-4 ${colors[color]}`}>
      <div className="text-2xl font-semibold text-gray-900">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  )
}

function TaskResultRow({ 
  task, 
  expanded, 
  onToggle 
}: { 
  task: TaskResult
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors text-left"
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
        
        {task.status === 'passed' ? (
          <CheckCircle2 className="w-5 h-5 text-green-500" />
        ) : task.status === 'failed' ? (
          <XCircle className="w-5 h-5 text-red-500" />
        ) : (
          <Clock className="w-5 h-5 text-yellow-500" />
        )}
        
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 truncate">{task.name}</div>
          <div className="text-sm text-gray-500">
            {task.trials.length} trial(s) • Score: {task.score.toFixed(2)}
          </div>
        </div>
      </button>
      
      {expanded && (
        <div className="px-6 pb-4 space-y-4">
          {task.trials.map(trial => (
            <div key={trial.trial_id} className="ml-8 border-l-2 border-gray-200 pl-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Trial {trial.trial_id}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  trial.status === 'passed' ? 'bg-green-100 text-green-700' :
                  trial.status === 'failed' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {trial.status}
                </span>
                <span className="text-xs text-gray-400">
                  {trial.duration_ms}ms
                </span>
              </div>
              
              {/* Grader results */}
              {trial.grader_results && Object.entries(trial.grader_results).length > 0 && (
                <div className="mb-2">
                  <div className="text-xs font-medium text-gray-500 mb-1">Graders:</div>
                  <div className="space-y-1">
                    {Object.entries(trial.grader_results).map(([name, result]) => (
                      <div key={name} className="flex items-center gap-2 text-sm">
                        {result.passed ? (
                          <CheckCircle2 className="w-3 h-3 text-green-500" />
                        ) : (
                          <XCircle className="w-3 h-3 text-red-500" />
                        )}
                        <span className="font-medium">{name}:</span>
                        <span className="text-gray-600 truncate">{result.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Transcript preview */}
              {trial.transcript && trial.transcript.length > 0 && (
                <div>
                  <div className="text-xs font-medium text-gray-500 mb-1 flex items-center gap-1">
                    <MessageSquare className="w-3 h-3" />
                    Conversation ({trial.transcript.length} turns)
                  </div>
                  <div className="bg-gray-50 rounded p-2 text-xs space-y-1 max-h-40 overflow-y-auto">
                    {trial.transcript.slice(0, 6).map((entry, i) => (
                      <div key={i} className={`${
                        entry.role === 'user' ? 'text-blue-700' :
                        entry.role === 'assistant' ? 'text-green-700' :
                        'text-yellow-700'
                      }`}>
                        <span className="font-medium">{entry.role}:</span>{' '}
                        <span className="text-gray-600">{entry.content.slice(0, 100)}...</span>
                      </div>
                    ))}
                    {trial.transcript.length > 6 && (
                      <div className="text-gray-400">
                        ... and {trial.transcript.length - 6} more turns
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {trial.error && (
                <div className="text-sm text-red-600 bg-red-50 p-2 rounded mt-2">
                  Error: {trial.error}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
