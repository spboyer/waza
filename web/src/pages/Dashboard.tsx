import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  Activity, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ArrowRight,
  FileText
} from 'lucide-react'
import { listEvals, listRuns, getHealth } from '../api/client'

export default function Dashboard() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
  })
  
  const { data: evals = [] } = useQuery({
    queryKey: ['evals'],
    queryFn: listEvals,
  })
  
  const { data: runs = [] } = useQuery({
    queryKey: ['runs'],
    queryFn: () => listRuns(),
  })
  
  const recentRuns = runs.slice(0, 5)
  const runningCount = runs.filter(r => r.status === 'running').length
  const passedCount = runs.filter(r => r.results?.pass_rate === 1).length
  const failedCount = runs.filter(r => r.results?.pass_rate !== undefined && r.results.pass_rate < 1).length

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard 
          icon={FileText} 
          label="Evals" 
          value={evals.length} 
          color="blue"
        />
        <StatCard 
          icon={Activity} 
          label="Running" 
          value={runningCount} 
          color="yellow"
        />
        <StatCard 
          icon={CheckCircle2} 
          label="Passed" 
          value={passedCount} 
          color="green"
        />
        <StatCard 
          icon={XCircle} 
          label="Failed" 
          value={failedCount} 
          color="red"
        />
      </div>
      
      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link 
            to="/evals"
            className="inline-flex items-center gap-2 px-4 py-2 bg-waza-600 text-white rounded-lg hover:bg-waza-700 transition-colors"
          >
            <FileText className="w-4 h-4" />
            View Evals
          </Link>
        </div>
      </div>
      
      {/* Recent Runs */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Recent Runs</h2>
          <Link 
            to="/evals" 
            className="text-sm text-waza-600 hover:text-waza-700 flex items-center gap-1"
          >
            View all <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        
        {recentRuns.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No runs yet. Start by running an eval!
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {recentRuns.map(run => (
              <Link 
                key={run.id}
                to={`/runs/${run.id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <StatusIcon status={run.status} />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 truncate">
                    {run.eval_name || run.eval_id || 'Unknown'}
                  </div>
                  <div className="text-sm text-gray-500">
                    {run.timestamp ? new Date(run.timestamp).toLocaleString() : 'No date'}
                  </div>
                </div>
                {run.pass_rate !== undefined && (
                  <div className="text-sm font-medium">
                    {(run.pass_rate * 100).toFixed(0)}%
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
      
      {/* Version */}
      {health && (
        <div className="text-center text-sm text-gray-400">
          waza v{health.version}
        </div>
      )}
    </div>
  )
}

function StatCard({ 
  icon: Icon, 
  label, 
  value, 
  color 
}: { 
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number
  color: 'blue' | 'green' | 'yellow' | 'red'
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
  }
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <div className="text-2xl font-semibold text-gray-900">{value}</div>
          <div className="text-sm text-gray-500">{label}</div>
        </div>
      </div>
    </div>
  )
}

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case 'running':
      return <Clock className="w-5 h-5 text-yellow-500 animate-pulse" />
    case 'completed':
      return <CheckCircle2 className="w-5 h-5 text-green-500" />
    case 'failed':
      return <XCircle className="w-5 h-5 text-red-500" />
    default:
      return <Clock className="w-5 h-5 text-gray-400" />
  }
}
