import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Analysis from './pages/Analysis'
import Strategies from './pages/Strategies'
import Plans from './pages/Plans'
import Notifications from './pages/Notifications'
import Settings from './pages/Settings'
import Screener from './pages/Screener'
import Backtest from './pages/Backtest'
import DailyBrief from './pages/DailyBrief'
import Watchlist from './pages/Watchlist'
import Research from './pages/Research'
import CapitalFlow from './pages/CapitalFlow'
import IndustryChain from './pages/IndustryChain'
import Community from './pages/Community'
import Pricing from './pages/Pricing'
import Tokens from './pages/Tokens'
import QuantClassroom from './pages/QuantClassroom'

export default function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#FFF8EE' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg"
               style={{ background: 'linear-gradient(135deg, #C8963E, #E8A817)', boxShadow: '0 4px 20px rgba(200, 150, 62, 0.3)' }}>
            觅
          </div>
          <div className="w-6 h-6 border-2 rounded-full animate-spin" style={{ borderColor: '#C8963E', borderTopColor: 'transparent' }} />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ background: '#FFF8EE' }}>
      <Navbar />
      <main className={user ? "max-w-7xl mx-auto px-4 sm:px-6 py-6" : ""}>
        <Routes>
          <Route path="/" element={user ? <Dashboard /> : <Home />} />
          <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
          <Route path="/register" element={user ? <Navigate to="/" /> : <Register />} />
          <Route path="/analysis" element={user ? <Analysis /> : <Navigate to="/login" />} />
          <Route path="/analysis/:taskId" element={user ? <Analysis /> : <Navigate to="/login" />} />
          <Route path="/strategies" element={user ? <Strategies /> : <Navigate to="/login" />} />
          <Route path="/plans" element={user ? <Plans /> : <Navigate to="/login" />} />
          <Route path="/notifications" element={user ? <Notifications /> : <Navigate to="/login" />} />
          <Route path="/settings" element={user ? <Settings /> : <Navigate to="/login" />} />
          <Route path="/screener" element={user ? <Screener /> : <Navigate to="/login" />} />
          <Route path="/backtest" element={user ? <Backtest /> : <Navigate to="/login" />} />
          <Route path="/brief" element={user ? <DailyBrief /> : <Navigate to="/login" />} />
          <Route path="/watchlist" element={user ? <Watchlist /> : <Navigate to="/login" />} />
          <Route path="/research" element={user ? <Research /> : <Navigate to="/login" />} />
          <Route path="/capital" element={user ? <CapitalFlow /> : <Navigate to="/login" />} />
          <Route path="/chain" element={user ? <IndustryChain /> : <Navigate to="/login" />} />
          <Route path="/community" element={user ? <Community /> : <Navigate to="/login" />} />
          <Route path="/classroom" element={user ? <QuantClassroom /> : <Navigate to="/login" />} />
          <Route path="/tokens" element={user ? <Tokens /> : <Navigate to="/login" />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  )
}
