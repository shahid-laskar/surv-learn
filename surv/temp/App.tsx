import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar         from './components/Sidebar'
import ProtectedRoute  from './components/ProtectedRoute'
import Login            from './pages/Login'
import LiveView         from './pages/LiveView'
import Playback         from './pages/Playback'
import MotionEvents     from './pages/MotionEvents'
import Cameras          from './pages/Cameras'

function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar />
      <main className="flex-1 overflow-y-auto min-w-0">
        <Routes>
          <Route path="/"         element={<LiveView />}     />
          <Route path="/playback" element={<Playback />}     />
          <Route path="/motion"   element={<MotionEvents />} />
          <Route path="/cameras"  element={<Cameras />}      />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/*" element={<AppShell />} />
      </Route>
    </Routes>
  )
}
