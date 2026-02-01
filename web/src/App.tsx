import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import EvalsList from './pages/EvalsList'
import RunDetails from './pages/RunDetails'
import Settings from './pages/Settings'
import './App.css'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/evals" element={<EvalsList />} />
        <Route path="/runs/:id" element={<RunDetails />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
