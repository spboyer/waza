import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { X, Loader2, Sparkles, FileText, AlertCircle } from 'lucide-react'
import { generatePreview, generateEval, type GeneratePreview } from '../api/client'

interface GenerateModalProps {
  onClose: () => void
}

export default function GenerateModal({ onClose }: GenerateModalProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [skillUrl, setSkillUrl] = useState('')
  const [name, setName] = useState('')
  const [assist, setAssist] = useState(false)
  const [preview, setPreview] = useState<GeneratePreview | null>(null)
  const [error, setError] = useState<string | null>(null)

  const previewMutation = useMutation({
    mutationFn: () => generatePreview(skillUrl),
    onSuccess: (data) => {
      setPreview(data)
      if (!name) {
        setName(data.skill_name)
      }
      setError(null)
    },
    onError: (err: Error) => {
      setError(err.message)
      setPreview(null)
    },
  })

  const generateMutation = useMutation({
    mutationFn: () => generateEval(skillUrl, name || undefined, assist),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['evals'] })
      navigate(`/evals/${data.eval_id}`)
      onClose()
    },
    onError: (err: Error) => {
      setError(err.message)
    },
  })

  const handlePreview = () => {
    if (!skillUrl.trim()) return
    setError(null)
    previewMutation.mutate()
  }

  const handleGenerate = () => {
    if (!skillUrl.trim()) return
    setError(null)
    generateMutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-waza-600" />
            <h2 className="text-lg font-medium text-gray-900">Generate Eval from SKILL.md</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* URL Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SKILL.md URL
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={skillUrl}
                onChange={(e) => setSkillUrl(e.target.value)}
                placeholder="https://github.com/org/repo/blob/main/skills/my-skill/SKILL.md"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-waza-500 focus:border-waza-500"
              />
              <button
                onClick={handlePreview}
                disabled={!skillUrl.trim() || previewMutation.isPending}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 flex items-center gap-2"
              >
                {previewMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <FileText className="w-4 h-4" />
                )}
                Preview
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Paste a GitHub URL to a SKILL.md file
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Preview */}
          {preview && (
            <div className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h3 className="font-medium text-gray-900 mb-2">{preview.skill_name}</h3>
              {preview.description && (
                <p className="text-sm text-gray-600 mb-3">{preview.description}</p>
              )}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Triggers:</span>
                  <span className="ml-2 font-medium">{preview.triggers_count}</span>
                </div>
                <div>
                  <span className="text-gray-500">Tasks to create:</span>
                  <span className="ml-2 font-medium">{preview.tasks_count}</span>
                </div>
              </div>
              {preview.tasks_preview.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-1">Sample tasks:</p>
                  <ul className="text-sm space-y-1">
                    {preview.tasks_preview.map((task, i) => (
                      <li key={i} className="text-gray-700 truncate">
                        • {task.name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Name Override */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Eval Name (optional)
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={preview?.skill_name || 'my-skill-eval'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-waza-500 focus:border-waza-500"
            />
          </div>

          {/* Assist Toggle */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="assist"
              checked={assist}
              onChange={(e) => setAssist(e.target.checked)}
              className="w-4 h-4 text-waza-600 border-gray-300 rounded focus:ring-waza-500"
            />
            <label htmlFor="assist" className="text-sm text-gray-700">
              Use LLM-assisted generation (better tasks, requires auth)
            </label>
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
            onClick={handleGenerate}
            disabled={!skillUrl.trim() || generateMutation.isPending}
            className="px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 disabled:opacity-50 flex items-center gap-2"
          >
            {generateMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Eval
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
