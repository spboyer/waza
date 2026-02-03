import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Save, Loader2, AlertCircle } from 'lucide-react'
import { createTask, updateTask } from '../api/client'
import type { Task } from '../types'

interface TaskEditorProps {
  evalId: string
  task?: Task | null  // null = create new, Task = edit existing
  onClose: () => void
}

const DEFAULT_TASK_YAML = `name: New Task
prompt: |
  Your task prompt here. Be specific about what you want the skill to do.

expected_behavior:
  - Description of expected behavior

graders:
  contains_text:
    type: regex
    pattern: "expected output"
    message: "Output should contain expected text"
`

export default function TaskEditor({ evalId, task, onClose }: TaskEditorProps) {
  const queryClient = useQueryClient()
  const [name, setName] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState<string | null>(null)

  const isEditing = !!task

  useEffect(() => {
    if (task) {
      setName(task.name)
      setContent(task.raw || '')
    } else {
      setName('')
      setContent(DEFAULT_TASK_YAML)
    }
  }, [task])

  const createMutation = useMutation({
    mutationFn: () => createTask(evalId, { name, content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', evalId] })
      onClose()
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: () => updateTask(evalId, task!.id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', evalId] })
      queryClient.invalidateQueries({ queryKey: ['task', evalId, task!.id] })
      onClose()
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const handleSave = () => {
    setError(null)
    if (isEditing) {
      updateMutation.mutate()
    } else {
      if (!name.trim()) {
        setError('Task name is required')
        return
      }
      createMutation.mutate()
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">
            {isEditing ? `Edit Task: ${task.name}` : 'Create New Task'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Name (only for new tasks) */}
          {!isEditing && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Task Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="my-task-name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-waza-500 focus:border-waza-500"
              />
              <p className="mt-1 text-xs text-gray-500">
                Used as the task filename (e.g., my-task-name.yaml)
              </p>
            </div>
          )}

          {/* YAML Editor */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Task YAML
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={20}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-waza-500 focus:border-waza-500 resize-none"
              placeholder="Enter task YAML..."
            />
            <p className="mt-1 text-xs text-gray-500">
              Define the task prompt, expected behavior, and graders in YAML format
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isPending || (!isEditing && !name.trim())}
            className="px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                {isEditing ? 'Save Changes' : 'Create Task'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
