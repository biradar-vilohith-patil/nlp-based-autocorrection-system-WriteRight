/**
 * pages/Home.jsx
 * ──────────────
 * Root page. Wires TextEditor ↔ CorrectionPanel via local state.
 * Handles all async API calls and error toasting.
 */

import { useState, useCallback } from 'react'
import toast from 'react-hot-toast'

import TextEditor from '../components/TextEditor'
import CorrectionPanel from '../components/CorrectionPanel'
import { correctText, refineText } from '../services/api'

const HERO_TAGS = ['spaCy', 'SymSpell', 'T5 Transformer', 'FastAPI', 'React']

export default function Home() {
  // ── State ──────────────────────────────────────────────────────────────────
  const [correctionResult, setCorrectionResult] = useState(null)
  const [refineResult, setRefineResult]         = useState(null)
  const [correctionLoading, setCorrectionLoading] = useState(false)
  const [refineLoading, setRefineLoading]         = useState(false)

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleCorrect = useCallback(async (text, pipeline) => {
    setCorrectionResult(null)
    setRefineResult(null)
    setCorrectionLoading(true)

    try {
      const result = await correctText(text, pipeline)
      setCorrectionResult(result)

      const total = result.spell_fixed + result.grammar_fixed + result.homophone_fixed
      if (total === 0) {
        toast('No errors found — your text looks great!', {
          icon: '✓',
          style: {
            background: '#0f2a1a',
            color: '#34d399',
            border: '1px solid #34d39940',
            fontSize: '13px',
          },
        })
      }
    } catch (err) {
      toast.error(err.message || 'Correction failed. Is the backend running?', {
        style: { background: '#2a0f0f', color: '#f87171', border: '1px solid #f8717140' },
      })
    } finally {
      setCorrectionLoading(false)
    }
  }, [])

  const handleRefine = useCallback(async (style) => {
    if (!correctionResult?.corrected) return
    setRefineResult(null)
    setRefineLoading(true)

    try {
      const result = await refineText(correctionResult.corrected, style)
      setRefineResult(result)
    } catch (err) {
      toast.error(err.message || 'Refinement failed.', {
        style: { background: '#2a0f0f', color: '#f87171', border: '1px solid #f8717140' },
      })
    } finally {
      setRefineLoading(false)
    }
  }, [correctionResult])

  const handleClear = useCallback(() => {
    setCorrectionResult(null)
    setRefineResult(null)
  }, [])

  const handleUseRefined = useCallback((text) => {
    // Scroll back to the top so the user can see the text loaded in the editor
    window.scrollTo({ top: 0, behavior: 'smooth' })
    setCorrectionResult(null)
    setRefineResult(null)
    // The TextEditor manages its own value, so we send the new text via a
    // custom event that TextEditor listens to.
    window.dispatchEvent(new CustomEvent('wr:loadText', { detail: text }))
    toast('Refined text loaded into the editor.', {
      icon: '↑',
      style: {
        background: '#1a0f2a',
        color: '#c084fc',
        border: '1px solid #c084fc40',
        fontSize: '13px',
      },
    })
  }, [])

  const isLoading = correctionLoading || refineLoading
  const hasResult = Boolean(correctionResult)

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <main style={{ position: 'relative', zIndex: 1 }}>
      {/* Hero */}
      <div
        className="animate-fade-up"
        style={{
          textAlign: 'center',
          marginBottom: 48,
          animationDelay: '0.05s',
        }}
      >
        <h1
          style={{
            fontFamily: "'Playfair Display', serif",
            fontSize: 'clamp(1.9rem, 5vw, 3.2rem)',
            fontWeight: 700,
            lineHeight: 1.15,
            marginBottom: 14,
          }}
          className="gradient-text"
        >
          Intelligent Text<br />
          <em style={{ fontStyle: 'italic' }}>Correction &amp; Refinement</em>
        </h1>

        <p style={{ color: 'var(--muted2)', fontSize: 15, maxWidth: 500, margin: '0 auto 20px' }}>
          Context-aware spelling &amp; grammar correction powered by spaCy,
          SymSpell, and a T5 transformer — running entirely in your backend.
        </p>

        {/* Tech stack tags */}
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
          {HERO_TAGS.map((t) => (
            <span
              key={t}
              style={{
                padding: '3px 12px',
                borderRadius: 100,
                border: '1px solid var(--border2)',
                background: 'rgba(79,70,229,0.06)',
                fontSize: 11,
                fontWeight: 600,
                color: 'var(--muted2)',
                letterSpacing: '0.05em',
              }}
            >
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Editor */}
      <TextEditor
        onCorrect={handleCorrect}
        onRefine={handleRefine}
        onClear={handleClear}
        loading={isLoading}
        hasResult={hasResult}
      />

      {/* Results — always mounted, handles its own empty state */}
      <div style={{ marginTop: 28 }}>
        <CorrectionPanel
          correctionResult={correctionResult}
          refineResult={refineResult}
          correctionLoading={correctionLoading}
          refineLoading={refineLoading}
          onUseRefined={handleUseRefined}
        />
      </div>

      {/* Watermark */}
      <div
        className="animate-fade-in"
        style={{
          textAlign: 'center',
          marginTop: 64,
          fontSize: 12,
          color: 'var(--border2)',
          animationDelay: '1s',
        }}
      >
        CVR College of Engineering · CSE(DS) · NLP Auto-Corrector
      </div>
    </main>
  )
}
