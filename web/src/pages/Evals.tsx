import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  FileText, 
  Play, 
  Trash2, 
  ChevronRight,
  Plus,
  FolderOpen
} from 'lucide-react'
import { listEvals, deleteEval, startRun } from '../api/client'
import { useState } from 'react'

export default function Evals() {
  const queryClient = useQueryClient()
  const [importing, setImporting] = useState(false)
  
  const { data: evals = [], isLoading } = useQuery({
    queryKey: ['evals'],
    queryFn: listEvals,
  })
  
  const deleteMutation = useMutation({
    mutationFn: deleteEval,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evals'] })
    },
  })
  
  const runMutation = useMutation({
    mutationFn: (evalId: string) => startRun(evalId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
    },
  })
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-waza-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Evaluations</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage and run your skill evaluations
          </p>
        </div>
        <button
          onClick={() => setImporting(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Import Eval
        </button>
      </div>
      
      {/* Eval list */}
      {evals.length === 0 ? (
        <EmptyState onImport={() => setImporting(true)} />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-100">
          {evals.map(evalItem => (
            <div 
              key={evalItem.id}
              className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              <div className="p-2 bg-waza-50 rounded-lg">
                <FileText className="w-5 h-5 text-waza-600" />
              </div>
              
              <div className="flex-1 min-w-0">
                <Link 
                  to={`/evals/${evalItem.id}`}
                  className="font-medium text-gray-900 hover:text-waza-600 truncate block"
                >
                  {evalItem.name}
                </Link>
                <div className="text-sm text-gray-500 flex items-center gap-2 mt-0.5">
                  <span>{evalItem.skill}</span>
                  <span>•</span>
                  <span>{evalItem.task_count} tasks</span>
                  {evalItem.last_run && (
                    <>
                      <span>•</span>
                      <span>
                        Last run: {new Date(evalItem.last_run.started_at).toLocaleDateString()}
                      </span>
                    </>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => runMutation.mutate(evalItem.id)}
                  disabled={runMutation.isPending}
                  className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                  title="Run eval"
                >
                  <Play className="w-4 h-4" />
                </button>
                <button
                  onClick={() => {
                    if (confirm('Delete this eval?')) {
                      deleteMutation.mutate(evalItem.id)
                    }
                  }}
                  disabled={deleteMutation.isPending}
                  className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Delete eval"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <Link
                  to={`/evals/${evalItem.id}`}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Import modal placeholder */}
      {importing && (
        <ImportModal onClose={() => setImporting(false)} />
      )}
    </div>
  )
}

function EmptyState({ onImport }: { onImport: () => void }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
      <div className="mx-auto w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
        <FolderOpen className="w-6 h-6 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No evaluations yet</h3>
      <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
        Import an eval from your local machine or generate one from a SKILL.md file
      </p>
      <button
        onClick={onImport}
        className="inline-flex items-center gap-2 px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Import Eval
      </button>
    </div>
  )
}

function ImportModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Import Evaluation</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ×
          </button>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-500 mb-4">
            To import an eval, use the CLI:
          </p>
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
            waza generate &lt;SKILL.md&gt; -o ./my-eval
          </pre>
          <p className="text-sm text-gray-500 mt-4">
            Then restart the server to see your eval.
          </p>
        </div>
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
