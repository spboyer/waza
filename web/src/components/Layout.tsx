import { NavLink, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  FileText, 
  Settings,
  FlaskConical,
  Menu,
  X 
} from 'lucide-react'
import { useState } from 'react'

interface LayoutProps {
  children: React.ReactNode
}

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/evals', icon: FileText, label: 'Evals' },
  { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-screen flex">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 bg-white border-r border-gray-200
        transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <FlaskConical className="w-6 h-6 text-waza-600" />
            <span className="text-xl font-semibold text-gray-900">waza</span>
          </div>
          <button 
            className="lg:hidden p-1 hover:bg-gray-100 rounded"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <nav className="p-4 space-y-1">
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium
                transition-colors
                ${isActive 
                  ? 'bg-waza-50 text-waza-700' 
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }
              `}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      
      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center px-4 lg:px-6">
          <button 
            className="lg:hidden p-2 -ml-2 mr-2 hover:bg-gray-100 rounded-lg"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>
          
          <h1 className="text-lg font-medium text-gray-900">
            {navItems.find(n => n.path === location.pathname)?.label || 'waza'}
          </h1>
        </header>
        
        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
