/**
 * services/api.js
 * ─────────────────
 * Typed Axios wrapper for all WriteRight backend endpoints.
 * Centralises base URL, error normalisation, and request shaping.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor — normalise errors ───────────────────────────────────
http.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      'Unknown error'
    return Promise.reject(new Error(message))
  }
)

// ── API methods ───────────────────────────────────────────────────────────────

/**
 * POST /api/correct
 * Full spell + homophone + grammar correction pipeline.
 *
 * @param {string}  text
 * @param {object}  [opts]
 * @param {boolean} [opts.runSpell=true]
 * @param {boolean} [opts.runGrammar=true]
 * @param {boolean} [opts.runHomophones=true]
 * @returns {Promise<CorrectionResponse>}
 */
export async function correctText(text, opts = {}) {
  const { runSpell = true, runGrammar = true, runHomophones = true } = opts
  const { data } = await http.post('/api/correct', {
    text,
    run_spell: runSpell,
    run_grammar: runGrammar,
    run_homophones: runHomophones,
  })
  return data
}

/**
 * POST /api/refine
 * Generate a polished rewrite of the corrected text.
 *
 * @param {string} text
 * @param {string} [style='professional']  professional | casual | academic | concise
 * @returns {Promise<RefineResponse>}
 */
export async function refineText(text, style = 'professional') {
  const { data } = await http.post('/api/refine', { text, style })
  return data
}

/**
 * GET /api/health
 * Check if the backend and all models are ready.
 *
 * @returns {Promise<HealthResponse>}
 */
export async function getHealth() {
  const { data } = await http.get('/api/health')
  return data
}

/**
 * GET /api/stats
 * Pipeline aggregate statistics.
 *
 * @returns {Promise<StatsResponse>}
 */
export async function getStats() {
  const { data } = await http.get('/api/stats')
  return data
}

// ── JSDoc typedefs ─────────────────────────────────────────────────────────────

/**
 * @typedef {Object} DiffEntry
 * @property {string} original
 * @property {string} corrected
 * @property {'spell'|'grammar'|'homophone'} type
 * @property {number} position
 */

/**
 * @typedef {Object} CorrectionResponse
 * @property {string}      original
 * @property {string}      corrected
 * @property {number}      spell_fixed
 * @property {number}      grammar_fixed
 * @property {number}      homophone_fixed
 * @property {number}      confidence
 * @property {DiffEntry[]} diffs
 * @property {number}      processing_ms
 */

/**
 * @typedef {Object} RefineResponse
 * @property {string}   original
 * @property {string}   refined
 * @property {string[]} improvements
 * @property {number}   processing_ms
 */

/**
 * @typedef {Object} HealthResponse
 * @property {string}  status
 * @property {boolean} spacy_loaded
 * @property {boolean} symspell_loaded
 * @property {boolean} t5_loaded
 * @property {string}  version
 */
