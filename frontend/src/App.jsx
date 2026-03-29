/**
 * App.jsx
 * ────────
 * Root component: background canvas, navbar, page wrapper.
 */

import { Toaster } from 'react-hot-toast'
import Navbar from './components/Navbar'
import Home from './pages/Home'

export default function App() {
  return (
    <>
      {/* ── Animated background ── */}
      <div className="bg-canvas">
        <div className="bg-mesh" />
        <div className="grid-lines" />
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      {/* ── Page content ── */}
      <div
        style={{
          position: 'relative',
          zIndex: 1,
          maxWidth: 920,
          margin: '0 auto',
          padding: '0 20px 80px',
        }}
      >
        <Navbar />
        <Home />
      </div>

      {/* ── Toast notifications ── */}
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 2400,
          style: {
            fontFamily: "'Outfit', sans-serif",
            fontSize: 13,
          },
        }}
      />
    </>
  )
}
