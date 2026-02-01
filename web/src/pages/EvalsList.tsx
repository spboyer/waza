import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Play, Trash2, Search, FileText, Sparkles } from 'lucide-react'

interface EvalItem {
  id: string
  name: string
  skill: string
  version?: string
}

export default function EvalsList() {
  const [filter, setFilter] = useState('')

  const { data: evalData, isLoading } = useQuery({
    queryKey: ['evals'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/evals')
      return res.json() as Promise<{ evals: EvalItem[]; count: number }>
    },
  })

  const filteredEvals = evalData?.evals.filter(item =>
    item.name.toLowerCase().includes(filter.toLowerCase()) ||
    item.skill.toLowerCase().includes(filter.toLowerCase())
  ) || []

  const handleRun = async (evalId: string) => {
    try {
      const res = await fetch('http://localhost:8000/api/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ eval_id: evalId }),
      })
      
      const data = await res.json()
      alert(`Run started: ${data.run_id}`)
    } catch (error) {
      alert('Failed to start run')
    }
  }

  const handleDelete = async (evalId: string) => {
    if (!confirm('Are you sure you want to delete this eval?')) return

    try {
      await fetch(`http://localhost:8000/api/evals/${evalId}`, {
        method: 'DELETE',
      })
      window.location.reload()
    } catch (error) {
      alert('Failed to delete eval')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-400">Loading evals...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Eval Suites
        </h1>
        <p className="text-gray-400 text-lg">Manage and run your evaluation suites</p>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name or skill..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full pl-12 pr-4 py-4 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
        />
      </div>

      {/* Evals List */}
      {filteredEvals.length === 0 ? (
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-16 text-center shadow-xl">
          <div className="inline-block p-6 bg-gray-700/50 rounded-full mb-6">
            <FileText className="w-16 h-16 text-gray-500" />
          </div>
          <h3 className="text-2xl font-bold mb-3 text-gray-300">No eval suites found</h3>
          <p className="text-gray-400 mb-6">
            Get started by creating your first eval suite
          </p>
          <div className="inline-flex items-center space-x-2 bg-gray-700 px-6 py-3 rounded-lg">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <code className="text-blue-400 font-mono text-sm">waza init my-skill</code>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredEvals.map((item: EvalItem) => (
            <div
              key={item.id}
              className="group bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 hover:border-blue-500/50 rounded-xl p-6 transition-all hover:shadow-xl hover:shadow-blue-500/10"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <FileText className="w-5 h-5 text-blue-400" />
                    <h3 className="text-xl font-semibold group-hover:text-blue-300 transition-colors">{item.name}</h3>
                    {item.version && (
                      <span className="text-xs bg-gray-700 px-2 py-1 rounded-full text-gray-400">
                        v{item.version}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 mb-2">
                    <span className="text-gray-500">Skill:</span> {item.skill}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleRun(item.id)}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-all hover:scale-105 shadow-lg shadow-blue-500/30"
                  >
                    <Play className="w-4 h-4" />
                    <span>Run</span>
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="p-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-all border border-red-500/30"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats Footer */}
      <div className="text-center">
        <p className="text-sm text-gray-500">
          Showing <span className="text-blue-400 font-medium">{filteredEvals.length}</span> of{' '}
          <span className="text-blue-400 font-medium">{evalData?.count || 0}</span> eval suites
        </p>
      </div>
    </div>
  )
}
