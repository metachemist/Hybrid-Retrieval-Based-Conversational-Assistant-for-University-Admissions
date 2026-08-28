'use client'

import { useEffect, useRef, useState } from 'react'

const SCRAMBLE_CHARS = '!<>-_\\/[]{}=+*^?01#'

const SNIPPETS = [
  `async def retrieve(query: str):
    bm25 = keyword_search(query, k=20)
    vec = embed(query, model="gemini-embedding-001")
    hits = rrf_fuse(bm25, vec, k=60)
    return rank(hits)[:5]`,
  `const chunks = await hybridSearch({
  query,
  topK: 10,
  weights: { bm25: 0.5, vector: 0.5 },
})
return citeSources(chunks)`,
  `class RRFRanker:
    def fuse(self, keyword, semantic):
        scores = {}
        for rank, doc in enumerate(keyword):
            scores[doc.id] = 1 / (60 + rank)
        return sorted(scores)`,
]

const KEYWORDS = /\b(async|def|return|const|await|class|import|from|for|in|new)\b/g
const STRINGS = /"[^"]*"|'[^']*'/g
const NUMBERS = /\b\d+(\.\d+)?\b/g

function tokenColors(text: string): string[] {
  const colors = new Array(text.length).fill('#a3a3a3')
  const mark = (re: RegExp, color: string) => {
    let m: RegExpExecArray | null
    re.lastIndex = 0
    while ((m = re.exec(text))) {
      for (let i = m.index; i < m.index + m[0].length; i++) colors[i] = color
      if (m[0].length === 0) re.lastIndex++
    }
  }
  mark(STRINGS, '#fdba74')
  mark(NUMBERS, '#7dd3fc')
  mark(KEYWORDS, '#dafa9c')
  return colors
}

interface CharState {
  target: string
  revealAt: number
  revealed: boolean
  /** while now < glitchUntil, show a scrambled glyph even though revealed —
   *  keeps the block visibly "alive" instead of sitting static between rewrites. */
  glitchUntil: number
}

/**
 * Code-editor-style block whose text continuously rewrites itself — each
 * character scrambles through random glyphs on its own randomized delay
 * before locking into place (rather than the block fading as a whole), and
 * a steady trickle of already-settled characters keep re-glitching so
 * there's never a dead, fully-static moment between snippets.
 */
export default function ScrambleCodeBlock({ className = '' }: { className?: string }) {
  const [display, setDisplay] = useState<string[]>([])
  const [colors, setColors] = useState<string[]>([])
  const rafRef = useRef(0)

  useEffect(() => {
    const state = { chars: [] as CharState[], snippetStart: 0, snippetIndex: -1 }

    function loadSnippet(now: number) {
      state.snippetIndex = (state.snippetIndex + 1) % SNIPPETS.length
      const target = SNIPPETS[state.snippetIndex]
      state.snippetStart = now
      state.chars = target.split('').map((ch, i) => ({
        target: ch,
        revealAt: /\s/.test(ch) ? 0 : i * 8 + Math.random() * 250,
        revealed: /\s/.test(ch),
        glitchUntil: 0,
      }))
      setColors(tokenColors(target))
    }

    let lastTick = 0
    function tick(now: number) {
      rafRef.current = requestAnimationFrame(tick)
      if (state.chars.length === 0) loadSnippet(now)

      const elapsed = now - state.snippetStart
      const maxReveal = state.chars.reduce((m, c) => Math.max(m, c.revealAt), 0)
      // Short buffer only — the glitch trickle below keeps things moving
      // in between, so this never reads as a frozen pause.
      if (elapsed > maxReveal + 900) loadSnippet(now)

      if (now - lastTick < 50) return
      lastTick = now

      setDisplay(state.chars.map(c => {
        if (!c.revealed && elapsed >= c.revealAt) c.revealed = true
        if (c.target === '\n') return c.target
        if (!c.revealed) return SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)]
        if (now < c.glitchUntil) return SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)]
        if (c.target !== ' ' && Math.random() < 0.0025) c.glitchUntil = now + 120 + Math.random() * 200
        return c.target
      }))
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [])

  return (
    <pre className={`font-mono whitespace-pre-wrap break-words ${className}`} aria-hidden="true">
      {display.map((ch, i) => (
        <span key={i} style={{ color: colors[i] || '#a3a3a3' }}>{ch}</span>
      ))}
    </pre>
  )
}
