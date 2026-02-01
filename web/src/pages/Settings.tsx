import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Github, Save, Info, Cpu, Zap, LogOut, LogIn, Search, Sparkles } from 'lucide-react'

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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Settings
        </h1>
        <p className="text-gray-400 text-lg">Configure your waza preferences</p>
      </div>

      {/* GitHub Authentication */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-8 shadow-xl">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-gray-700/50 rounded-lg">
            <Github className="w-6 h-6 text-gray-300" />
          </div>
          <h2 className="text-2xl font-bold">GitHub Authentication</h2>
        </div>
        
        {authStatus?.authenticated ? (
          <div>
            <div className="flex items-center space-x-4 p-4 bg-gray-700/30 rounded-lg mb-6 border border-green-500/20">
              {authStatus.user?.avatar_url && (
                <img
                  src={authStatus.user.avatar_url}
                  alt={authStatus.user.name}
                  className="w-16 h-16 rounded-full border-2 border-green-500"
                />
              )}
              <div className="flex-1">
                <p className="font-semibold text-lg">{authStatus.user?.name || authStatus.user?.login}</p>
                <p className="text-sm text-gray-400">@{authStatus.user?.login}</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {authStatus.scopes?.map((scope: string) => (
                    <span key={scope} className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded border border-green-500/30">
                      {scope}
                    </span>
                  ))}
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-all border border-red-500/30"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="p-6 bg-gray-700/20 rounded-lg border border-gray-600">
            <p className="text-gray-300 mb-4 font-medium">
              Unlock advanced features with GitHub OAuth
            </p>
            <ul className="space-y-2 text-sm text-gray-400 mb-6">
              <li className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-yellow-400" />
                <span>Run evals with copilot-sdk executor</span>
              </li>
              <li className="flex items-center space-x-2">
                <Search className="w-4 h-4 text-blue-400" />
                <span>Scan GitHub repos for skills</span>
              </li>
              <li className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span>LLM-assisted eval generation</span>
              </li>
            </ul>
            <button
              onClick={handleLogin}
              className="flex items-center justify-center space-x-2 w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white rounded-lg font-semibold transition-all shadow-lg shadow-blue-500/30"
            >
              <LogIn className="w-5 h-5" />
              <span>Login with GitHub</span>
            </button>
          </div>
        )}
      </div>

      {/* Model Configuration */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-8 shadow-xl">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-gray-700/50 rounded-lg">
            <Cpu className="w-6 h-6 text-purple-400" />
          </div>
          <h2 className="text-2xl font-bold">Model Configuration</h2>
        </div>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-3">
              Model
            </label>
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            >
              <option value="claude-sonnet-4-20250514">Claude Sonnet 4</option>
              <option value="claude-opus-4.5">Claude Opus 4.5</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="gpt-4">GPT-4</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-3">
              Executor
            </label>
            <select
              value={executor}
              onChange={(e) => setExecutor(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={executor === 'copilot-sdk' && !authStatus?.authenticated}
            >
              <option value="mock">Mock (no authentication required)</option>
              <option value="copilot-sdk">
                Copilot SDK {!authStatus?.authenticated && '(requires GitHub login)'}
              </option>
            </select>
          </div>

          <button
            onClick={handleSave}
            disabled={updateConfig.isPending}
            className="flex items-center justify-center space-x-2 w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/30"
          >
            <Save className="w-5 h-5" />
            <span>{updateConfig.isPending ? 'Saving...' : 'Save Changes'}</span>
          </button>
        </div>
      </div>

      {/* System Information */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-8 shadow-xl">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-gray-700/50 rounded-lg">
            <Info className="w-6 h-6 text-blue-400" />
          </div>
          <h2 className="text-2xl font-bold">System Information</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoItem label="API Endpoint" value="http://localhost:8000" />
          <InfoItem label="Storage Location" value="~/.waza/" />
          <InfoItem label="Current Model" value={config?.model || 'Loading...'} />
          <InfoItem label="Current Executor" value={config?.executor || 'Loading...'} />
        </div>
      </div>
    </div>
  )
}

// Info Item Component
function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-4 bg-gray-700/30 rounded-lg border border-gray-600/50">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className="font-mono text-sm text-gray-200 truncate">{value}</p>
    </div>
  )
}
