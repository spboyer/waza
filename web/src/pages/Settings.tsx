import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, RefreshCw } from 'lucide-react'
import { getConfig, updateConfig } from '../api/client'
import { useState, useEffect } from 'react'

// Supported models
const MODELS = [
  { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4 (Default)', provider: 'Anthropic' },
  { value: 'claude-sonnet-4', label: 'Claude Sonnet 4', provider: 'Anthropic' },
  { value: 'claude-opus-4', label: 'Claude Opus 4', provider: 'Anthropic' },
  { value: 'claude-haiku-4', label: 'Claude Haiku 4', provider: 'Anthropic' },
  { value: 'gpt-4o', label: 'GPT-4o', provider: 'OpenAI' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini', provider: 'OpenAI' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', provider: 'OpenAI' },
  { value: 'o1', label: 'o1', provider: 'OpenAI' },
  { value: 'o1-mini', label: 'o1 Mini', provider: 'OpenAI' },
  { value: 'o3-mini', label: 'o3 Mini', provider: 'OpenAI' },
]

export default function Settings() {
  const queryClient = useQueryClient()
  
  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: getConfig,
  })
  
  const [model, setModel] = useState('')
  const [executor, setExecutor] = useState('')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  
  useEffect(() => {
    if (config) {
      setModel(config.model || 'claude-sonnet-4-20250514')
      setExecutor(config.executor || 'mock')
      setTheme(config.theme || 'light')
    }
  }, [config])
  
  const mutation = useMutation({
    mutationFn: () => updateConfig({ model, executor, theme }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
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
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">
          Configure default options for waza
        </p>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
        {/* Model */}
        <div className="p-6">
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Default Model
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-waza-500 focus:border-waza-500"
          >
            <optgroup label="Anthropic">
              {MODELS.filter(m => m.provider === 'Anthropic').map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </optgroup>
            <optgroup label="OpenAI">
              {MODELS.filter(m => m.provider === 'OpenAI').map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </optgroup>
          </select>
          <p className="mt-1.5 text-sm text-gray-500">
            The LLM model to use for eval execution
          </p>
        </div>
        
        {/* Executor */}
        <div className="p-6">
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Default Executor
          </label>
          <select
            value={executor}
            onChange={(e) => setExecutor(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-waza-500 focus:border-waza-500"
          >
            <option value="mock">Mock (Testing)</option>
            <option value="copilot-sdk">Copilot SDK (Real)</option>
          </select>
          <p className="mt-1.5 text-sm text-gray-500">
            Mock is faster for testing, Copilot SDK uses real LLM
          </p>
        </div>
        
        {/* Theme */}
        <div className="p-6">
          <label className="block text-sm font-medium text-gray-900 mb-2">
            Theme
          </label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-waza-500 focus:border-waza-500"
          >
            <option value="light">Light</option>
            <option value="dark">Dark (coming soon)</option>
          </select>
        </div>
      </div>
      
      {/* Save button */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="inline-flex items-center gap-2 px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 transition-colors disabled:opacity-50"
        >
          {mutation.isPending ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Settings
        </button>
        
        {mutation.isSuccess && (
          <span className="text-sm text-green-600">Settings saved!</span>
        )}
      </div>
      
      {/* CLI Info */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
        <h3 className="text-sm font-medium text-gray-900 mb-2">CLI Configuration</h3>
        <p className="text-sm text-gray-500 mb-3">
          You can also configure waza using CLI flags:
        </p>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
{`# Run with specific model
waza run eval.yaml --model gpt-4o

# Use mock executor for testing
waza run eval.yaml --executor mock

# Start web UI on custom port
waza serve --port 3000`}
        </pre>
      </div>
    </div>
  )
}
