import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  ArrowLeft,
  Play,
  Clock,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Plus,
  Edit,
  Copy,
  Trash2,
  FileText
} from 'lucide-react'
import { getEval, listRuns, startRun, listTasks, duplicateTask, deleteTask, getTask } from '../api/client'
import TaskEditor from '../components/TaskEditor'
import EvalEditor from '../components/EvalEditor'
import type { Task } from '../types'

export default function EvalDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [editingTask, setEditingTask] = useState<Task | null | undefined>(undefined) // undefined = closed, null = new, Task = edit
  const [editingEval, setEditingEval] = useState(false)

  const { data: evalData, isLoading: evalLoading } = useQuery({
    queryKey: ['eval', id],
    queryFn: () => getEval(id!),
    enabled: !!id,
  })

  const { data: tasks = [], isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks', id],
    queryFn: () => listTasks(id!),
    enabled: !!id,
  })

  const { data: runs = [] } = useQuery({
    queryKey: ['runs', id],
    queryFn: () => listRuns(id),
    enabled: !!id,
  })

  const runMutation = useMutation({
    mutationFn: () => startRun(id!),
    onSuccess: (data: { run_id: string; status: string }) => {
      queryClient.invalidateQueries({ queryKey: ['runs'] })
      navigate(`/runs/${data.run_id}`)
    },
  })

  const duplicateMutation = useMutation({
    mutationFn: (taskId: string) => duplicateTask(id!, taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', id] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (taskId: string) => deleteTask(id!, taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', id] })
    },
  })

  const handleEditTask = async (task: Task) => {
    // Fetch full task content
    const fullTask = await getTask(id!, task.id)
    setEditingTask(fullTask)
  }

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
            {evalData.content?.skill as string || evalData.skill} • {tasks.length} tasks
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

      {/* Configuration */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Configuration</h2>
          <button
            onClick={() => setEditingEval(true)}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:text-waza-600 hover:bg-waza-50 rounded-lg"
          >
            <Edit className="w-4 h-4" />
            Edit
          </button>
        </div>
        <div className="px-6 py-4">
          <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Name</dt>
              <dd className="font-medium text-gray-900 mt-0.5">
                {(evalData.content?.name as string) || evalData.name || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Skill</dt>
              <dd className="font-medium text-gray-900 mt-0.5">
                {(evalData.content?.skill as string) || evalData.skill || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Version</dt>
              <dd className="font-medium text-gray-900 mt-0.5">
                {(evalData.content?.version as string) || '—'}
              </dd>
            </div>
            {typeof evalData.content?.description === 'string' && evalData.content.description && (
              <div className="sm:col-span-2 lg:col-span-3">
                <dt className="text-gray-500">Description</dt>
                <dd className="font-medium text-gray-900 mt-0.5">
                  {evalData.content.description}
                </dd>
              </div>
            )}
            {/* Config section */}
            {typeof evalData.content?.config === 'object' && evalData.content.config && (
              <>
                <div>
                  <dt className="text-gray-500">Trials per Task</dt>
                  <dd className="font-medium text-gray-900 mt-0.5">
                    {String((evalData.content.config as Record<string, unknown>).trials_per_task ?? 1)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Timeout</dt>
                  <dd className="font-medium text-gray-900 mt-0.5">
                    {String((evalData.content.config as Record<string, unknown>).timeout_seconds ?? 300)}s
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">Executor</dt>
                  <dd className="font-medium text-gray-900 mt-0.5">
                    {String((evalData.content.config as Record<string, unknown>).executor ?? 'mock')}
                  </dd>
                </div>
              </>
            )}
            {typeof evalData.content?.context_dir === 'string' && evalData.content.context_dir && (
              <div className="sm:col-span-2 lg:col-span-3">
                <dt className="text-gray-500">Context Directory</dt>
                <dd className="font-mono text-gray-900 mt-0.5 text-xs">
                  {evalData.content.context_dir}
                </dd>
              </div>
            )}
            {/* Metrics summary */}
            {Array.isArray(evalData.content?.metrics) && (evalData.content.metrics as unknown[]).length > 0 && (
              <div className="sm:col-span-2 lg:col-span-3">
                <dt className="text-gray-500">Metrics</dt>
                <dd className="mt-1 flex flex-wrap gap-1.5">
                  {(evalData.content.metrics as Array<{name: string}>).map((m, i) => (
                    <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {m.name}
                    </span>
                  ))}
                </dd>
              </div>
            )}
            {/* Graders summary */}
            {Array.isArray(evalData.content?.graders) && (evalData.content.graders as unknown[]).length > 0 && (
              <div className="sm:col-span-2 lg:col-span-3">
                <dt className="text-gray-500">Graders</dt>
                <dd className="mt-1 flex flex-wrap gap-1.5">
                  {(evalData.content.graders as Array<{type: string; name?: string}>).map((g, i) => (
                    <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                      {g.name || g.type}
                    </span>
                  ))}
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Tasks */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Tasks</h2>
          <button
            onClick={() => setEditingTask(null)}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm bg-waza-600 text-white rounded-lg hover:bg-waza-700"
          >
            <Plus className="w-4 h-4" />
            Add Task
          </button>
        </div>

        {tasksLoading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-waza-600 mx-auto" />
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p>No tasks yet. Add a task to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {tasks.map(task => (
              <div
                key={task.id}
                className="flex items-center gap-4 px-6 py-3 hover:bg-gray-50"
              >
                <FileText className="w-4 h-4 text-gray-400" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900">{task.name}</div>
                  {task.prompt && (
                    <div className="text-sm text-gray-500 truncate">{task.prompt}</div>
                  )}
                  {task.graders && task.graders.length > 0 && (
                    <div className="text-xs text-gray-400 mt-0.5">
                      Graders: {task.graders.join(', ')}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleEditTask(task)}
                    className="p-1.5 text-gray-400 hover:text-waza-600 hover:bg-waza-50 rounded"
                    title="Edit task"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => duplicateMutation.mutate(task.id)}
                    disabled={duplicateMutation.isPending}
                    className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                    title="Duplicate task"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Delete task "${task.name}"?`)) {
                        deleteMutation.mutate(task.id)
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                    title="Delete task"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
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
                    {run.timestamp ? new Date(run.timestamp).toLocaleString() : 'No date'}
                  </div>
                  <div className="text-sm text-gray-500">
                    {run.status} {run.pass_rate !== undefined ? `• ${(run.pass_rate * 100).toFixed(0)}%` : ''}
                  </div>
                </div>
                {run.pass_rate !== undefined && (
                  <div className={`text-sm font-medium ${
                    run.pass_rate === 1 ? 'text-green-600' :
                    run.pass_rate >= 0.5 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {(run.pass_rate * 100).toFixed(0)}% passed
                  </div>
                )}
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Task Editor Modal */}
      {editingTask !== undefined && (
        <TaskEditor
          evalId={id!}
          task={editingTask}
          onClose={() => setEditingTask(undefined)}
        />
      )}

      {/* Eval Editor Modal */}
      {editingEval && (
        <EvalEditor
          evalData={evalData}
          onClose={() => setEditingEval(false)}
        />
      )}
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
