/**
 * components/TextEditor.jsx
 * ─────────────────────────
 * The main text input area with word/char counters,
 * pipeline toggle controls, and action buttons.
 */

import { useRef, useState } from 'react'

const MAX_CHARS = 4096

const PIPELINE_TOGGLES = [
  { key: 'runSpell',      label: 'Spell',      icon: '✎', color: '#34d399' },
  { key: 'runGrammar',    label: 'Grammar',    icon: '⊕', color: '#818cf8' },
  { key: 'runHomophones', label: 'Homophones', icon: '⇄', color: '#fbbf24' },
]

const STYLE_OPTIONS = ['professional', 'casual', 'academic', 'concise']

export default function TextEditor({
  onCorrect,
  onRefine,
  onClear,
  loading,
  hasResult,
}) {
  const [text, setText]     = useState('')
  const [focused, setFocused] = useState(false)
  const [pipeline, setPipeline] = useState({
    runSpell: true,
    runGrammar: true,
    runHomophones: true,
  })
  const [style, setStyle] = useState('professional')
  const textareaRef = useRef(null)

  const words = text.trim() ? text.trim().split(/\s+/).length : 0
  const chars = text.length
  const pct   = Math.min((chars / MAX_CHARS) * 100, 100)

  function handleChange(e) {
    if (e.target.value.length <= MAX_CHARS) setText(e.target.value)
  }

  function handleClear() {
    setText('')
    onClear()
    textareaRef.current?.focus()
  }

  function togglePipeline(key) {
    setPipeline((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  function handleCorrect() {
    if (!text.trim() || loading) return
    onCorrect(text, pipeline)
  }

  function handleRefine() {
    if (!hasResult || loading) return
    onRefine(style)
  }

  const charColor =
    chars > MAX_CHARS * 0.9
      ? 'var(--red)'
      : chars > MAX_CHARS * 0.7
        ? 'var(--yellow)'
        : 'var(--muted)'

  return (
    <div className="animate-fade-up" style={{ animationDelay: '0.15s' }}>
      {/* ── Input Card ── */}
      <div className={`glass-card ${focused ? 'focused' : ''} ${loading ? 'processing' : ''}`}>
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 20px 0',
          }}
        >
          <div className="section-label">
            <span className="dot" />
            Input Text
          </div>

          {/* Pipeline toggles */}
          <div style={{ display: 'flex', gap: 6 }}>
            {PIPELINE_TOGGLES.map(({ key, label, icon, color }) => (
              <button
                key={key}
                onClick={() => togglePipeline(key)}
                title={`${pipeline[key] ? 'Disable' : 'Enable'} ${label}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                  padding: '3px 9px',
                  borderRadius: 100,
                  border: `1px solid`,
                  borderColor: pipeline[key] ? `${color}50` : 'var(--border)',
                  background: pipeline[key] ? `${color}12` : 'transparent',
                  color: pipeline[key] ? color : 'var(--muted)',
                  fontSize: 11,
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  letterSpacing: '0.04em',
                  fontFamily: "'Outfit', sans-serif",
                }}
              >
                <span>{icon}</span>
                <span className="hidden sm:inline">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          className="nlp-textarea"
          value={text}
          onChange={handleChange}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Paste or type your text here… e.g. 'She dont know wher she goed yesterday, it were a compliceted situaton.'"
          rows={7}
          style={{ padding: '14px 20px 16px' }}
          disabled={loading}
        />

        {/* Char progress bar */}
        <div
          style={{
            height: 2,
            background: 'var(--border)',
            margin: '0 20px',
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${pct}%`,
              background:
                pct > 90
                  ? 'var(--red)'
                  : pct > 70
                    ? 'var(--yellow)'
                    : 'linear-gradient(90deg, #4f46e5, #06b6d4)',
              borderRadius: 2,
              transition: 'width 0.2s, background 0.3s',
            }}
          />
        </div>

        {/* Footer: counters + clear */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 20px',
          }}
        >
          <div style={{ display: 'flex', gap: 16 }}>
            <span style={{ fontSize: 12, color: 'var(--muted)' }}>
              Words: <strong style={{ color: 'var(--muted2)' }}>{words}</strong>
            </span>
            <span style={{ fontSize: 12, color: charColor }}>
              Chars: <strong>{chars}</strong>
              <span style={{ color: 'var(--border2)', marginLeft: 2 }}>/ {MAX_CHARS}</span>
            </span>
          </div>

          {text && (
            <button className="btn-danger" onClick={handleClear} disabled={loading}>
              ✕ Clear
            </button>
          )}
        </div>
      </div>

      {/* ── Action Row ── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginTop: 16,
          flexWrap: 'wrap',
        }}
      >
        {/* Correct button */}
        <button
          className="btn-primary"
          onClick={handleCorrect}
          disabled={!text.trim() || loading}
        >
          {loading ? (
            <span className="spinner" />
          ) : (
            <span>⚡</span>
          )}
          <span>{loading ? 'Analysing…' : 'Fix Spelling & Grammar'}</span>
        </button>

        {/* Refine button + style selector */}
        <div style={{ display: 'flex', gap: 0, alignItems: 'center' }}>
          <button
            className="btn-cyan"
            onClick={handleRefine}
            disabled={!hasResult || loading}
            style={{ borderRadius: '12px 0 0 12px' }}
          >
            {loading ? <span className="spinner" /> : <span>✦</span>}
            <span>Refine Text</span>
          </button>
          <select
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            disabled={!hasResult || loading}
            style={{
              padding: '10px 10px',
              borderRadius: '0 12px 12px 0',
              border: '1px solid #0891b2',
              borderLeft: 'none',
              background: '#0f1f26',
              color: hasResult ? '#67e8f9' : 'var(--muted)',
              fontSize: 13,
              fontFamily: "'Outfit', sans-serif",
              cursor: hasResult ? 'pointer' : 'not-allowed',
              outline: 'none',
              opacity: hasResult ? 1 : 0.5,
            }}
          >
            {STYLE_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  )
}
