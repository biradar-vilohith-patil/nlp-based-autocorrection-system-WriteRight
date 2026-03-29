/**
 * components/Navbar.jsx
 * ─────────────────────
 * Top navigation bar with logo, version badge, and live health indicator.
 */

import { useEffect, useState } from 'react'
import { getHealth } from '../services/api'

const MODEL_PILLS = [
  { key: 'spacy_loaded',    label: 'spaCy',    color: '#34d399' },
  { key: 'symspell_loaded', label: 'SymSpell', color: '#818cf8' },
  { key: 't5_loaded',       label: 'T5',       color: '#c084fc' },
]

export default function Navbar() {
  const [health, setHealth] = useState(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function check() {
      try {
        const data = await getHealth()
        if (!cancelled) setHealth(data)
      } catch {
        if (!cancelled) setHealth(null)
      } finally {
        if (!cancelled) setChecking(false)
      }
    }
    check()
    const interval = setInterval(check, 30_000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [])

  const isOnline = health?.status === 'ok'

  return (
    <nav
      className="animate-fade-down"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '28px 0 44px',
        flexWrap: 'wrap',
        gap: '16px',
      }}
    >
      {/* ── Logo ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: 'linear-gradient(135deg, #4f46e5, #06b6d4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
            boxShadow: '0 0 24px #4f46e550',
            flexShrink: 0,
          }}
        >
          ✦
        </div>
        <div>
          <div
            style={{
              fontFamily: "'Playfair Display', serif",
              fontSize: 20,
              fontWeight: 700,
              background: 'linear-gradient(90deg, #818cf8, #67e8f9)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            WriteRight
          </div>
          <div style={{ fontSize: 11, color: 'var(--muted)', letterSpacing: '0.05em', marginTop: 1 }}>
            NLP Auto-Corrector
          </div>
        </div>
      </div>

      {/* ── Right side: model pills + status ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        {/* Model status pills */}
        {!checking && health && MODEL_PILLS.map(({ key, label, color }) => (
          <div
            key={key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '4px 10px',
              borderRadius: 100,
              border: `1px solid ${color}30`,
              background: `${color}10`,
              fontSize: 11,
              fontWeight: 600,
              color: health[key] ? color : 'var(--muted)',
              letterSpacing: '0.05em',
            }}
          >
            <span
              style={{
                width: 5,
                height: 5,
                borderRadius: '50%',
                background: health[key] ? color : 'var(--muted)',
                boxShadow: health[key] ? `0 0 6px ${color}` : 'none',
              }}
            />
            {label}
          </div>
        ))}

        {/* API connectivity badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '5px 14px',
            borderRadius: 100,
            border: '1px solid',
            borderColor: checking
              ? 'var(--border2)'
              : isOnline
                ? '#34d39940'
                : '#f8717140',
            background: checking
              ? '#1a1a26'
              : isOnline
                ? '#0f2a1a'
                : '#2a0f0f',
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '0.07em',
            color: checking
              ? 'var(--muted2)'
              : isOnline
                ? 'var(--green)'
                : 'var(--red)',
            textTransform: 'uppercase',
          }}
        >
          {checking ? (
            <span className="spinner" style={{ width: 8, height: 8, borderWidth: 1.5 }} />
          ) : (
            <span
              style={{
                width: 5,
                height: 5,
                borderRadius: '50%',
                background: isOnline ? 'var(--green)' : 'var(--red)',
                boxShadow: isOnline ? '0 0 6px var(--green)' : 'none',
              }}
            />
          )}
          {checking ? 'Connecting…' : isOnline ? 'API Online' : 'Offline'}
        </div>
      </div>
    </nav>
  )
}
