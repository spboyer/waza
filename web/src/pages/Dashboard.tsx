import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { TrendingUp, Play, Settings as SettingsIcon, FileText, Activity } from 'lucide-react'

interface EvalItem {
  version?: string
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
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-5xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-gray-400 text-lg">Evaluate Agent Skills like you evaluate AI Agents</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Evals"
          value={evalData?.count || 0}
          icon={<FileText className="w-6 h-6 text-blue-400" />}
          trend="+0%"
        />
        <MetricCard
          title="Total Runs"
          value={runs?.count || 0}
          icon={<Activity className="w-6 h-6 text-green-400" />}
          trend="+0%"
        />
        <MetricCard
          title="Model"
          value={config?.model?.split('-')[0] || 'N/A'}
          subtitle={config?.model || ''}
          icon={<TrendingUp className="w-6 h-6 text-purple-400" />}
        />
        <MetricCard
          title="Executor"
          value={config?.executor || 'N/A'}
          icon={<Play className="w-6 h-6 text-orange-400" />}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <div className="lg:col-span-1">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6 shadow-xl">
            <h2 className="text-2xl font-bold mb-6 flex items-center">
              <span className="w-2 h-2 bg-blue-400 rounded-full mr-3 animate-pulse"></span>
              Quick Actions
            </h2>
            <div className="space-y-3">
              <ActionButton
                to="/evals"
                icon={<FileText className="w-5 h-5" />}
                label="View All Evals"
                primary
              />
              <ActionButton
                to="/settings"
                icon={<SettingsIcon className="w-5 h-5" />}
                label="Configure Settings"
              />
            </div>
          </div>
        </div>

        {/* Recent Runs */}
        <div className="lg:col-span-2">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6 shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold flex items-center">
                <Activity className="w-6 h-6 mr-3 text-green-400" />
                Recent Runs
              </h2>
              {runs && runs.count > 0 && (
                <Link to="/runs" className="text-sm text-blue-400 hover:text-blue-300">
                  View all →
                </Link>
              )}
            </div>
            {runs?.count === 0 ? (
              <div className="text-center py-12">
                <Activity className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                <p className="text-gray-400 mb-2">No runs yet</p>
                <p className="text-sm text-gray-500">Start your first eval to see results here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {runs?.runs.slice(0, 5).map((run: any, idx: number) => (
                  <Link
                    key={idx}
                    to={`/runs/${run.run_id}`}
                    className="block bg-gray-700/50 hover:bg-gray-700 rounded-lg p-4 transition-all hover:scale-[1.02] border border-gray-600/50"
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-medium">{run.name || run.run_id}</span>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(run.timestamp || Date.now()).toLocaleString()}
                        </p>
                      </div>
                      <StatusBadge status={run.status || 'pending'} />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Eval Suites Grid */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold flex items-center">
            <FileText className="w-6 h-6 mr-3 text-blue-400" />
            Eval Suites
          </h2>
          <Link to="/evals" className="text-blue-400 hover:text-blue-300 text-sm font-medium">
            View All →
          </Link>
        </div>
        
        {evalData?.count === 0 ? (
          <div className="text-center py-16">
            <div className="inline-block p-4 bg-gray-700/50 rounded-full mb-4">
              <FileText className="w-12 h-12 text-gray-500" />
            </div>
            <p className="text-gray-300 mb-3 text-lg font-medium">No eval suites found</p>
            <p className="text-sm text-gray-500 mb-6">
              Get started by creating your first eval suite
            </p>
            <code className="inline-block bg-gray-700 px-4 py-2 rounded-lg text-blue-400 font-mono text-sm">
              waza init my-skill
            </code>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {evalData?.evals.slice(0, 6).map((item: EvalItem) => (
              <Link
                key={item.id}
                to={`/evals`}
                className="group bg-gray-700/30 hover:bg-gray-700/60 border border-gray-600/50 hover:border-blue-500/50 rounded-lg p-5 transition-all hover:scale-[1.02] hover:shadow-lg hover:shadow-blue-500/10"
              >
                <div className="flex items-start justify-between mb-3">
                  <FileText className="w-5 h-5 text-blue-400 group-hover:text-blue-300" />
                  <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">v{item.version || '1.0'}</span>
                </div>
                <h3 className="font-semibold mb-2 group-hover:text-blue-300 transition-colors">{item.name}</h3>
                <p className="text-sm text-gray-400">Skill: {item.skill}</p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// Metric Card Component
function MetricCard({ title, value, subtitle, icon, trend }: {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  trend?: string
}) {
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-xl p-6 shadow-xl hover:shadow-2xl transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="p-2 bg-gray-700/50 rounded-lg">
          {icon}
        </div>
        {trend && (
          <span className="text-xs text-green-400 font-medium">{trend}</span>
        )}
      </div>
      <h3 className="text-sm font-medium text-gray-400 mb-2">{title}</h3>
      <p className="text-3xl font-bold mb-1">{value}</p>
      {subtitle && <p className="text-xs text-gray-500 truncate">{subtitle}</p>}
    </div>
  )
}

// Action Button Component
function ActionButton({ to, icon, label, primary }: {
  to: string
  icon: React.ReactNode
  label: string
  primary?: boolean
}) {
  const className = primary
    ? "flex items-center justify-center space-x-3 w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white rounded-lg font-semibold transition-all hover:scale-[1.02] shadow-lg shadow-blue-500/30"
    : "flex items-center justify-center space-x-3 w-full px-6 py-4 bg-gray-700/50 hover:bg-gray-700 text-gray-300 rounded-lg font-medium transition-all hover:scale-[1.02] border border-gray-600"
  
  return (
    <Link to={to} className={className}>
      {icon}
      <span>{label}</span>
    </Link>
  )
}

// Status Badge Component
function StatusBadge({ status }: { status: string }) {
  const styles = {
    passed: 'bg-green-500/20 text-green-400 border-green-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    running: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    pending: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  }[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'

  return (
    <span className={`text-xs px-3 py-1 rounded-full font-medium border ${styles}`}>
      {status}
    </span>
  )
}
