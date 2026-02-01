import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

interface EvalItem {
  id: string
  name: string
  skill: string
}

interface Config {
  model: string
  executor: string
}

export default function Dashboard() {
  const { data: evalData } = useQuery({
    queryKey: ['evals'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/evals')
      return res.json() as Promise<{ evals: EvalItem[]; count: number }>
    },
  })

  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/config')
      return res.json() as Promise<Config>
    },
  })

  const { data: runs } = useQuery({
    queryKey: ['runs'],
    queryFn: async () => {
      const res = await fetch('http://localhost:8000/api/runs')
      return res.json() as Promise<{ runs: any[]; count: number }>
    },
  })

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
        <p className="text-gray-400">Evaluate Agent Skills like you evaluate AI Agents</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Total Evals</h3>
          <p className="text-3xl font-bold">{evalData?.count || 0}</p>
        </div>
        
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Total Runs</h3>
          <p className="text-3xl font-bold">{runs?.count || 0}</p>
        </div>
        
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Model</h3>
          <p className="text-lg font-medium truncate">{config?.model || 'N/A'}</p>
        </div>
        
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Executor</h3>
          <p className="text-lg font-medium">{config?.executor || 'N/A'}</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              to="/evals"
              className="block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded text-center"
            >
              View All Evals
            </Link>
            <Link
              to="/settings"
              className="block bg-gray-700 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded text-center"
            >
              Configure Settings
            </Link>
          </div>
        </div>

        {/* Recent Runs */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Recent Runs</h2>
          {runs?.count === 0 ? (
            <p className="text-gray-400 text-sm">No runs yet</p>
          ) : (
            <div className="space-y-2">
              {runs?.runs.slice(0, 5).map((run: any, idx: number) => (
                <Link
                  key={idx}
                  to={`/runs/${run.run_id}`}
                  className="block bg-gray-700 hover:bg-gray-600 rounded p-3"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium truncate">{run.name || run.run_id}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      run.status === 'passed' ? 'bg-green-600' : 'bg-red-600'
                    }`}>
                      {run.status || 'pending'}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Eval Suites Preview */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Eval Suites</h2>
          <Link to="/evals" className="text-blue-400 hover:text-blue-300 text-sm">
            View All →
          </Link>
        </div>
        
        {evalData?.count === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-4">No eval suites found</p>
            <p className="text-sm text-gray-500">
              Create an eval suite with <code className="bg-gray-700 px-2 py-1 rounded">waza init</code>
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {evalData?.evals.slice(0, 6).map((item: EvalItem) => (
              <Link
                key={item.id}
                to={`/evals`}
                className="border border-gray-700 rounded-lg p-4 hover:bg-gray-700"
              >
                <h3 className="font-medium mb-1">{item.name}</h3>
                <p className="text-sm text-gray-400">{item.skill}</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
