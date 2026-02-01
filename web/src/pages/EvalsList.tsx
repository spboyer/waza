import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

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
    return <div className="text-center py-12">Loading evals...</div>
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Eval Suites</h1>
        <p className="text-gray-400">Manage and run your evaluation suites</p>
      </div>

      {/* Filter */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Filter by name or skill..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="w-full md:w-96 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Evals List */}
      {filteredEvals.length === 0 ? (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-12 text-center">
          <p className="text-gray-400 mb-4">No eval suites found</p>
          <p className="text-sm text-gray-500">
            Create an eval suite with <code className="bg-gray-700 px-2 py-1 rounded">waza init my-skill</code>
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredEvals.map((item: EvalItem) => (
            <div
              key={item.id}
              className="bg-gray-800 border border-gray-700 rounded-lg p-6"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-xl font-medium mb-2">{item.name}</h3>
                  <p className="text-gray-400 mb-1">Skill: {item.skill}</p>
                  {item.version && (
                    <p className="text-sm text-gray-500">Version: {item.version}</p>
                  )}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleRun(item.id)}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
                  >
                    Run
                  </button>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      <div className="mt-8 text-center text-sm text-gray-500">
        Showing {filteredEvals.length} of {evalData?.count || 0} eval suites
      </div>
    </div>
  )
}
