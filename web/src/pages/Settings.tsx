import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

interface Config {
  model: string
  executor: string
  theme: string
  github_token: string | null
}

export default function Settings() {
  const queryClient = useQueryClient()
  const [model, setModel] = useState('')
  const [executor, setExecutor] = useState('')

  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/config')
      const data = await res.json() as Config
      setModel(data.model)
      setExecutor(data.executor)
      return data
    },
  })

  const { data: authStatus } = useQuery({
    queryKey: ['auth'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/auth/status')
      return res.json()
    },
  })

  const updateConfig = useMutation({
    mutationFn: async (updates: Partial<Config>) => {
      const res = await fetch('http://localhost:8000/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      })
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] })
      alert('Settings saved successfully')
    },
  })

  const handleSave = () => {
    updateConfig.mutate({ model, executor })
  }

  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/api/auth/login'
  }

  const handleLogout = async () => {
    await fetch('http://localhost:8000/api/auth/logout', { method: 'POST' })
    queryClient.invalidateQueries({ queryKey: ['auth'] })
    alert('Logged out successfully')
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Settings</h1>
        <p className="text-gray-400">Configure your waza preferences</p>
      </div>

      {/* GitHub Authentication */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4">GitHub Authentication</h2>
        
        {authStatus?.authenticated ? (
          <div>
            <div className="flex items-center space-x-4 mb-4">
              {authStatus.user?.avatar_url && (
                <img
                  src={authStatus.user.avatar_url}
                  alt={authStatus.user.name}
                  className="w-12 h-12 rounded-full"
                />
              )}
              <div>
                <p className="font-medium">{authStatus.user?.name || authStatus.user?.login}</p>
                <p className="text-sm text-gray-400">@{authStatus.user?.login}</p>
              </div>
            </div>
            <p className="text-sm text-gray-400 mb-4">
              Scopes: {authStatus.scopes?.join(', ') || 'None'}
            </p>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded font-medium"
            >
              Logout
            </button>
          </div>
        ) : (
          <div>
            <p className="text-gray-400 mb-4">
              Login with GitHub to unlock advanced features:
            </p>
            <ul className="list-disc list-inside text-sm text-gray-400 mb-4 space-y-1">
              <li>Run evals with copilot-sdk executor</li>
              <li>Scan GitHub repos for skills</li>
              <li>LLM-assisted eval generation</li>
              <li>Import from GitHub URLs</li>
            </ul>
            <button
              onClick={handleLogin}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
            >
              Login with GitHub
            </button>
          </div>
        )}
      </div>

      {/* Model Configuration */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
        <h2 className="text-2xl font-bold mb-4">Model Configuration</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Model
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
            >
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
              <option value="claude-opus-4.5">Claude Opus 4.5</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4">GPT-4</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Executor
            </label>
            <select
              value={executor}
              onChange={(e) => setExecutor(e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
            >
              <option value="mock">Mock (no authentication required)</option>
              <option value="copilot-sdk" disabled={!authStatus?.authenticated}>
                Copilot SDK {!authStatus?.authenticated && '(requires GitHub login)'}
              </option>
            </select>
          </div>

          <button
            onClick={handleSave}
            disabled={updateConfig.isPending}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium disabled:opacity-50"
          >
            {updateConfig.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* System Info */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-4">System Information</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">API Endpoint:</span>
            <span>http://localhost:8000</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Storage Location:</span>
            <span>~/.waza/</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Current Model:</span>
            <span>{config?.model || 'Loading...'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Current Executor:</span>
            <span>{config?.executor || 'Loading...'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
