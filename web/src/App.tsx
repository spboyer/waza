import { useState, useEffect } from 'react'
import './App.css'

interface EvalItem {
  id: string
  name: string
  skill: string
  path: string
}

interface EvalSummary {
  evals: EvalItem[]
  count: number
}

interface Config {
  model: string
  executor: string
  theme: string
  github_token: string | null
}

function App() {
  const [evalData, setEvalData] = useState<EvalSummary | null>(null)
  const [config, setConfig] = useState<Config | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [evalsRes, configRes] = await Promise.all([
          fetch('http://localhost:8000/api/evals'),
          fetch('http://localhost:8000/api/config')
        ])
        
        const evalsData = await evalsRes.json()
        const configData = await configRes.json()
        
        setEvalData(evalsData)
        setConfig(configData)
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">skill-eval Dashboard</h1>
          <p className="text-gray-400">Evaluate Agent Skills like you evaluate AI Agents</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Total Evals</h3>
            <p className="text-3xl font-bold">{evalData?.count || 0}</p>
          </div>
          
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Model</h3>
            <p className="text-lg font-medium">{config?.model || 'N/A'}</p>
          </div>
          
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Executor</h3>
            <p className="text-lg font-medium">{config?.executor || 'N/A'}</p>
          </div>
        </div>

        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h2 className="text-2xl font-bold mb-4">Eval Suites</h2>
          
          {evalData?.count === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400 mb-4">No eval suites found</p>
              <p className="text-sm text-gray-500">
                Create an eval suite with <code className="bg-gray-700 px-2 py-1 rounded">skill-eval init</code>
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {evalData?.evals.map((item, index) => (
                <div key={index} className="border border-gray-700 rounded-lg p-4">
                  <h3 className="font-medium">{item.name}</h3>
                  <p className="text-sm text-gray-400">{item.skill}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>API: http://localhost:8000 • Docs: <a href="http://localhost:8000/docs" className="text-blue-400 hover:underline">http://localhost:8000/docs</a></p>
        </div>
      </div>
    </div>
  )
}

export default App
