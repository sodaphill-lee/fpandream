import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from '@/pages/Dashboard'
import Connections from '@/pages/Connections'
import Models from '@/pages/Models'
import ModelDetail from '@/pages/ModelDetail'

const queryClient = new QueryClient()

function Nav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-2 rounded ${isActive ? 'bg-blue-600 text-white' : 'text-gray-700 hover:bg-gray-100'}`

  return (
    <nav className="border-b px-6 py-3 flex items-center gap-4">
      <span className="font-bold text-lg mr-6">FP&A Dream</span>
      <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
      <NavLink to="/models" className={linkClass}>Models</NavLink>
      <NavLink to="/connections" className={linkClass}>Connections</NavLink>
    </nav>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Nav />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/models" element={<Models />} />
            <Route path="/models/:modelId" element={<ModelDetail />} />
            <Route path="/connections" element={<Connections />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
