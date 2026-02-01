import { Link, useLocation } from 'react-router-dom'
import { type ReactNode } from 'react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  
  const isActive = (path: string) => {
    return location.pathname === path
  }
  
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              <Link to="/" className="text-xl font-bold">
                skill-eval
              </Link>
              <nav className="flex space-x-4">
                <Link to="/" className={`px-3 py-2 rounded ${isActive('/') ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
                  Dashboard
                </Link>
                <Link to="/evals" className={`px-3 py-2 rounded ${isActive('/evals') ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
                  Evals
                </Link>
                <Link to="/settings" className={`px-3 py-2 rounded ${isActive('/settings') ? 'bg-gray-700' : 'hover:bg-gray-700'}`}>
                  Settings
                </Link>
              </nav>
            </div>
            <div>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-sm text-gray-400 hover:text-white">
                API Docs
              </a>
            </div>
          </div>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}
