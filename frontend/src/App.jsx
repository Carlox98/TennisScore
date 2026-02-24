import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import PlayerPage from './pages/PlayerPage'
import H2HPage from './pages/H2HPage'
import ModelStats from './pages/ModelStats'

const NAV_ITEMS = [
  { path: '/', label: 'Predictions' },
  { path: '/h2h', label: 'Head-to-Head' },
  { path: '/model', label: 'Model Stats' },
]

function Navbar() {
  const location = useLocation()
  return (
    <header className="border-b border-slate-700/50 bg-tennis-bg/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold">
          <span className="text-2xl">🎾</span>
          <span className="bg-gradient-to-r from-tennis-green to-tennis-yellow bg-clip-text text-transparent">
            Tennis Predictor
          </span>
        </Link>
        <nav className="flex gap-1">
          {NAV_ITEMS.map(({ path, label }) => (
            <Link
              key={path}
              to={path}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === path
                  ? 'bg-tennis-green/20 text-tennis-green'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-tennis-bg">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/player/:id" element={<PlayerPage />} />
            <Route path="/h2h" element={<H2HPage />} />
            <Route path="/model" element={<ModelStats />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}
