import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  FileText,
  Play,
  Trash2,
  ChevronRight,
  FolderOpen,
  Sparkles
} from 'lucide-react'
import { listEvals, deleteEval, startRun } from '../api/client'
import { useState } from 'react'
import GenerateModal from '../components/GenerateModal'

export default function Evals() {
  const queryClient = useQueryClient()
  const [showGenerate, setShowGenerate] = useState(false)

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
          onClick={() => setShowGenerate(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 transition-colors"
        >
          <Sparkles className="w-4 h-4" />
          Generate Eval
        </button>
      </div>
      
      {/* Eval list */}
      {evals.length === 0 ? (
        <EmptyState onGenerate={() => setShowGenerate(true)} />
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
      
      {/* Generate modal */}
      {showGenerate && (
        <GenerateModal onClose={() => setShowGenerate(false)} />
      )}
    </div>
  )
}

function EmptyState({ onGenerate }: { onGenerate: () => void }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
      <div className="mx-auto w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mb-4">
        <FolderOpen className="w-6 h-6 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No evaluations yet</h3>
      <p className="text-sm text-gray-500 mb-6 max-w-sm mx-auto">
        Generate an eval from a SKILL.md file to get started
      </p>
      <button
        onClick={onGenerate}
        className="inline-flex items-center gap-2 px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 transition-colors"
      >
        <Sparkles className="w-4 h-4" />
        Generate Eval
      </button>
    </div>
  )
}
