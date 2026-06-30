import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar      from './components/Sidebar'
import LiveView     from './pages/LiveView'
import Playback     from './pages/Playback'
import MotionEvents from './pages/MotionEvents'
import Cameras      from './pages/Cameras'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <Sidebar />
      <main className="flex-1 overflow-y-auto min-w-0">
        <Routes>
          <Route path="/"        element={<LiveView />}     />
          <Route path="/playback" element={<Playback />}    />
          <Route path="/motion"   element={<MotionEvents />} />
          <Route path="/cameras"  element={<Cameras />}     />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
