import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Evals from './pages/Evals'
import EvalDetail from './pages/EvalDetail'
import RunDetail from './pages/RunDetail'
import Settings from './pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/evals" element={<Evals />} />
        <Route path="/evals/:id" element={<EvalDetail />} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
