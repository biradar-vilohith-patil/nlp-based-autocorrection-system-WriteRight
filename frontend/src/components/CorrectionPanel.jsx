/**
 * components/CorrectionPanel.jsx
 * ───────────────────────────────
 * Renders correction + refinement results.
 * Handles:
 *   - Skeleton loading state
 *   - Word-level diff rendering (spell / grammar / homophone)
 *   - Metric chips (fixes count, confidence, ms)
 *   - Copy-to-clipboard per card
 *   - "Use as Input" callback for refinement output
 */

import { useMemo } from 'react'
import toast from 'react-hot-toast'

// ── Diff renderer ──────────────────────────────────────────────────────────────

/**
 * Renders an HTML string with <span> diff markers from the diff array
 * returned by the backend.
 */
function renderDiff(original, diffs) {
  if (!diffs || diffs.length === 0) {
    return <span>{original}</span>
  }

  // Build a word-index lookup of changes
  const changeMap = {}
  for (const d of diffs) {
    if (d.original || d.corrected) {
      changeMap[d.position] = d
    }
  }

  const words = original.split(/(\s+)/)
  let wordIdx = 0
  const nodes = []

  for (let i = 0; i < words.length; i++) {
    const token = words[i]
    const isWhitespace = /^\s+$/.test(token)

    if (isWhitespace) {
      nodes.push(token)
      continue
    }

    const change = changeMap[wordIdx]
    if (change) {
      const cls =
        change.type === 'spell'
          ? 'diff-del'
          : change.type === 'homophone'
            ? 'diff-hom'
            : 'diff-del'

      nodes.push(
        <span key={`del-${i}`} className={cls}>
          {change.original || token}
        </span>
      )
      if (change.corrected) {
        nodes.push(' ')
        nodes.push(
          <span key={`ins-${i}`} className="diff-ins">
            {change.corrected}
          </span>
        )
      }
    } else {
      nodes.push(token)
    }
    wordIdx++
  }

  return <>{nodes}</>
}

// ── Skeleton ───────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div style={{ padding: '20px' }}>
      {[90, 75, 85, 55, 70].map((w, i) => (
        <div
          key={i}
          className="skeleton"
          style={{ width: `${w}%`, height: 14, marginBottom: 12 }}
        />
      ))}
    </div>
  )
}

// ── Copy helper ────────────────────────────────────────────────────────────────

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    toast.success('Copied to clipboard', {
      style: {
        background: '#0f2a1a',
        color: '#34d399',
        border: '1px solid #34d39940',
        fontSize: '13px',
      },
    })
  })
}

// ── Confidence badge ───────────────────────────────────────────────────────────

function ConfidenceBadge({ value }) {
  const pct = Math.round(value * 100)
  const color =
    pct >= 85 ? 'var(--green)' : pct >= 65 ? 'var(--yellow)' : 'var(--red)'
  return (
    <span
      style={{
        fontSize: 12,
        fontWeight: 600,
        color,
        padding: '2px 8px',
        border: `1px solid ${color}40`,
        borderRadius: 100,
        background: `${color}10`,
      }}
    >
      {pct}% confidence
    </span>
  )
}

// ── Card wrapper ───────────────────────────────────────────────────────────────

function ResultCard({ children, animationDelay = 0 }) {
  return (
    <div
      className="glass-card animate-slide-up"
      style={{ animationDelay: `${animationDelay}s`, overflow: 'hidden' }}
    >
      {children}
    </div>
  )
}

function CardHeader({ title, tag, tagClass, actions }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 20px',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(255,255,255,0.018)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 13, fontWeight: 600, letterSpacing: '0.02em' }}>
          {title}
        </span>
        <span className={`tag ${tagClass}`}>{tag}</span>
      </div>
      <div style={{ display: 'flex', gap: 8 }}>{actions}</div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function CorrectionPanel({
  correctionResult,
  refineResult,
  correctionLoading,
  refineLoading,
  onUseRefined,
}) {
  const showCorrection = correctionLoading || correctionResult
  const showRefinement = refineLoading || refineResult

  // Memoise the diff JSX so it doesn't rerender on every keystroke
  const diffNode = useMemo(() => {
    if (!correctionResult) return null
    return renderDiff(correctionResult.original, correctionResult.diffs)
  }, [correctionResult])

  if (!showCorrection && !showRefinement) {
    return (
      <div
        className="animate-fade-in"
        style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--muted)' }}
      >
        <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.35 }}>⌨</div>
        <p style={{ fontSize: 14 }}>
          Enter your text above and click{' '}
          <strong style={{ color: 'var(--muted2)' }}>Fix Spelling &amp; Grammar</strong>{' '}
          to begin.
        </p>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* ── Divider ── */}
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 12 }}
        className="animate-fade-in"
      >
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        <span
          style={{
            fontSize: 11,
            letterSpacing: '0.08em',
            color: 'var(--muted)',
            textTransform: 'uppercase',
          }}
        >
          Analysis Results
        </span>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
      </div>

      {/* ── Correction card ── */}
      {showCorrection && (
        <ResultCard animationDelay={0}>
          {correctionLoading ? (
            <>
              <CardHeader
                title="Spell & Grammar Correction"
                tag="Processing…"
                tagClass="tag-proc"
                actions={null}
              />
              <Skeleton />
            </>
          ) : (
            <>
              <CardHeader
                title="Spell & Grammar Correction"
                tag="✓ Fixed"
                tagClass="tag-spell"
                actions={[
                  <button
                    key="copy"
                    className="btn-ghost"
                    style={{ padding: '5px 12px', fontSize: 12 }}
                    onClick={() => copyToClipboard(correctionResult.corrected)}
                  >
                    ⎘ Copy
                  </button>,
                ]}
              />

              {/* Metric chips */}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', padding: '12px 20px 0' }}>
                {correctionResult.spell_fixed > 0 && (
                  <span className="chip chip-spell">
                    <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor' }} />
                    {correctionResult.spell_fixed} spelling fix{correctionResult.spell_fixed !== 1 ? 'es' : ''}
                  </span>
                )}
                {correctionResult.grammar_fixed > 0 && (
                  <span className="chip chip-gram">
                    <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor' }} />
                    {correctionResult.grammar_fixed} grammar fix{correctionResult.grammar_fixed !== 1 ? 'es' : ''}
                  </span>
                )}
                {correctionResult.homophone_fixed > 0 && (
                  <span className="chip chip-hom">
                    <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor' }} />
                    {correctionResult.homophone_fixed} homophone fix{correctionResult.homophone_fixed !== 1 ? 'es' : ''}
                  </span>
                )}
                <ConfidenceBadge value={correctionResult.confidence} />
                <span style={{ fontSize: 12, color: 'var(--muted)', marginLeft: 'auto' }}>
                  {correctionResult.processing_ms}ms
                </span>
              </div>

              {/* Diff body */}
              <div
                style={{
                  padding: '16px 20px 20px',
                  fontSize: 15,
                  lineHeight: 1.9,
                  borderTop: '1px solid var(--border)',
                  marginTop: 12,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {diffNode}
              </div>

              {/* Corrected clean copy */}
              <div
                style={{
                  padding: '0 20px 16px',
                  fontSize: 13,
                  color: 'var(--muted)',
                  fontStyle: 'italic',
                }}
              >
                ✓ &nbsp;
                <span style={{ color: 'var(--muted2)' }}>{correctionResult.corrected}</span>
              </div>
            </>
          )}
        </ResultCard>
      )}

      {/* ── Refinement card ── */}
      {showRefinement && (
        <ResultCard animationDelay={0.08}>
          {refineLoading ? (
            <>
              <CardHeader
                title="Refined Text"
                tag="Generating…"
                tagClass="tag-proc"
                actions={null}
              />
              <Skeleton />
            </>
          ) : (
            <>
              <CardHeader
                title="Refined Text"
                tag="✦ Complete"
                tagClass="tag-refine"
                actions={[
                  <button
                    key="copy"
                    className="btn-ghost"
                    style={{ padding: '5px 12px', fontSize: 12 }}
                    onClick={() => copyToClipboard(refineResult.refined)}
                  >
                    ⎘ Copy
                  </button>,
                ]}
              />

              {/* Improvements list */}
              {refineResult.improvements?.length > 0 && (
                <div style={{ padding: '12px 20px 0', display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {refineResult.improvements.map((imp, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, fontSize: 12.5, color: 'var(--muted2)' }}>
                      <span style={{ color: 'var(--purple)', flexShrink: 0 }}>✦</span>
                      {imp}
                    </div>
                  ))}
                </div>
              )}

              {/* Refined body */}
              <div
                style={{
                  padding: '16px 20px 20px',
                  fontSize: 15,
                  lineHeight: 1.9,
                  borderTop: '1px solid var(--border)',
                  marginTop: 12,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {refineResult.refined}
              </div>

              {/* Timing + use-as-input */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 20px',
                  borderTop: '1px solid var(--border)',
                }}
              >
                <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                  {refineResult.processing_ms}ms
                </span>
                <button
                  className="btn-ghost"
                  style={{ padding: '6px 14px', fontSize: 12 }}
                  onClick={() => onUseRefined(refineResult.refined)}
                >
                  ↑ Use as Input
                </button>
              </div>
            </>
          )}
        </ResultCard>
      )}
    </div>
  )
}
