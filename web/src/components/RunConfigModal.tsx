import { useState } from 'react'
import { X, Play, Beaker, Cpu } from 'lucide-react'

interface RunConfigModalProps {
  evalName: string
  onClose: () => void
  onRun: (config: { executor: string; model: string }) => void
  isRunning: boolean
}

const MODELS = {
  anthropic: [
    { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4 (Latest)', default: true },
    { id: 'claude-sonnet-4', name: 'Claude Sonnet 4' },
    { id: 'claude-opus-4', name: 'Claude Opus 4' },
    { id: 'claude-haiku-4', name: 'Claude Haiku 4' },
  ],
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
    { id: 'o1', name: 'o1' },
    { id: 'o1-mini', name: 'o1 Mini' },
    { id: 'o3-mini', name: 'o3 Mini' },
  ],
}

export default function RunConfigModal({ evalName, onClose, onRun, isRunning }: RunConfigModalProps) {
  const [executor, setExecutor] = useState<'mock' | 'copilot-sdk'>('mock')
  const [model, setModel] = useState('claude-sonnet-4-20250514')

  const handleRun = () => {
    onRun({ executor, model })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Run Eval</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-4">
          <p className="text-sm text-gray-600">
            Configure how to run <span className="font-medium text-gray-900">{evalName}</span>
          </p>

          {/* Executor Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Executor
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setExecutor('mock')}
                className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-colors ${
                  executor === 'mock'
                    ? 'border-waza-500 bg-waza-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Beaker className={`w-5 h-5 ${executor === 'mock' ? 'text-waza-600' : 'text-gray-400'}`} />
                <div className="text-left">
                  <div className={`font-medium ${executor === 'mock' ? 'text-waza-700' : 'text-gray-700'}`}>
                    Mock
                  </div>
                  <div className="text-xs text-gray-500">Fast testing</div>
                </div>
              </button>
              <button
                onClick={() => setExecutor('copilot-sdk')}
                className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-colors ${
                  executor === 'copilot-sdk'
                    ? 'border-waza-500 bg-waza-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Cpu className={`w-5 h-5 ${executor === 'copilot-sdk' ? 'text-waza-600' : 'text-gray-400'}`} />
                <div className="text-left">
                  <div className={`font-medium ${executor === 'copilot-sdk' ? 'text-waza-700' : 'text-gray-700'}`}>
                    Copilot SDK
                  </div>
                  <div className="text-xs text-gray-500">Real LLM</div>
                </div>
              </button>
            </div>
          </div>

          {/* Model Selection (only for copilot-sdk) */}
          {executor === 'copilot-sdk' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model
              </label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-waza-500 focus:border-waza-500"
              >
                <optgroup label="Anthropic">
                  {MODELS.anthropic.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </optgroup>
                <optgroup label="OpenAI">
                  {MODELS.openai.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </optgroup>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Select the LLM to use for evaluation
              </p>
            </div>
          )}

          {/* Info box */}
          <div className={`p-3 rounded-lg ${executor === 'mock' ? 'bg-blue-50' : 'bg-amber-50'}`}>
            <p className={`text-sm ${executor === 'mock' ? 'text-blue-700' : 'text-amber-700'}`}>
              {executor === 'mock' ? (
                <>
                  <strong>Mock executor</strong> returns simulated responses instantly. 
                  Great for testing your eval setup and graders.
                </>
              ) : (
                <>
                  <strong>Copilot SDK</strong> will make real LLM calls. 
                  This may take longer and incur API costs.
                </>
              )}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={isRunning}
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className="inline-flex items-center gap-2 px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            {isRunning ? 'Starting...' : 'Start Run'}
          </button>
        </div>
      </div>
    </div>
  )
}
