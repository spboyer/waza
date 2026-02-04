import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Save, Loader2, AlertCircle } from 'lucide-react'
import Editor from '@monaco-editor/react'
import { updateEval } from '../api/client'
import type { Eval } from '../types'

interface EvalEditorProps {
  evalData: Eval
  onClose: () => void
}

export default function EvalEditor({ evalData, onClose }: EvalEditorProps) {
  const queryClient = useQueryClient()
  const [content, setContent] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Convert the eval content back to YAML-like format for editing
    if (evalData.raw) {
      setContent(evalData.raw)
    } else if (evalData.content) {
      // If no raw content, construct from content object
      const yaml = Object.entries(evalData.content)
        .map(([key, value]) => {
          if (typeof value === 'string') {
            if (value.includes('\n')) {
              return `${key}: |\n  ${value.split('\n').join('\n  ')}`
            }
            return `${key}: ${value}`
          }
          return `${key}: ${JSON.stringify(value)}`
        })
        .join('\n')
      setContent(yaml)
    }
  }, [evalData])

  const updateMutation = useMutation({
    mutationFn: () => updateEval(evalData.id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['eval', evalData.id] })
      queryClient.invalidateQueries({ queryKey: ['evals'] })
      onClose()
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const handleSave = () => {
    setError(null)
    updateMutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">
            Edit Eval: {evalData.name}
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

          {/* Info */}
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-700">
              Edit the eval configuration. Common fields include <code className="bg-blue-100 px-1 rounded">name</code>,{' '}
              <code className="bg-blue-100 px-1 rounded">skill</code>,{' '}
              <code className="bg-blue-100 px-1 rounded">description</code>, and{' '}
              <code className="bg-blue-100 px-1 rounded">context_dir</code>.
            </p>
          </div>

          {/* YAML Editor with Monaco */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Eval YAML
            </label>
            <div className="border border-gray-300 rounded-lg overflow-hidden">
              <Editor
                height="400px"
                defaultLanguage="yaml"
                value={content}
                onChange={(value) => setContent(value || '')}
                theme="vs-light"
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  wrappingIndent: 'indent',
                  automaticLayout: true,
                  tabSize: 2,
                  insertSpaces: true,
                }}
              />
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Changes to eval.yaml will be saved immediately. Task definitions are managed separately.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-start justify-between gap-4">
          {/* Hints */}
          <div className="text-xs text-gray-500 max-w-md">
            <details className="mb-2">
              <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
                Available Graders
              </summary>
              <ul className="mt-1 ml-4 space-y-0.5 text-gray-500">
                <li><code className="bg-gray-100 px-1 rounded">regex</code> — Match output against a pattern</li>
                <li><code className="bg-gray-100 px-1 rounded">contains_text</code> — Check for specific text</li>
                <li><code className="bg-gray-100 px-1 rounded">code</code> — Custom Python assertions</li>
                <li><code className="bg-gray-100 px-1 rounded">llm</code> — LLM-based evaluation</li>
                <li><code className="bg-gray-100 px-1 rounded">file_exists</code> — Verify file creation</li>
                <li><code className="bg-gray-100 px-1 rounded">json_schema</code> — Validate JSON structure</li>
              </ul>
            </details>
            <details>
              <summary className="cursor-pointer text-gray-600 hover:text-gray-800 font-medium">
                Available Metrics
              </summary>
              <ul className="mt-1 ml-4 space-y-0.5 text-gray-500">
                <li><code className="bg-gray-100 px-1 rounded">task_completion</code> — Did the skill accomplish the task?</li>
                <li><code className="bg-gray-100 px-1 rounded">trigger_accuracy</code> — Is it invoked on right prompts?</li>
                <li><code className="bg-gray-100 px-1 rounded">behavior_quality</code> — Tool usage and best practices</li>
              </ul>
            </details>
          </div>
          
          {/* Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 disabled:opacity-50 flex items-center gap-2"
            >
              {updateMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
