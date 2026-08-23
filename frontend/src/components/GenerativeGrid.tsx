'use client'

import { useEffect, useRef } from 'react'

// Layered sine/cosine hash sampled at a few different frequencies and phase
// speeds — smooth, spatially-continuous pseudo-noise without pulling in a
// real Perlin/Simplex library. Combining bands at different scales is what
// produces contiguous light/dark *regions* (not per-cell static), so the
// field reads as flowing bands rather than television snow.
function noise2D(x: number, y: number, t: number): number {
  const n1 = Math.sin(x * 0.035 + t * 0.35) * Math.cos(y * 0.045 - t * 0.25)
  const n2 = Math.sin((x + y) * 0.02 + t * 0.15)
  const n3 = Math.cos(x * 0.06 - y * 0.05 + t * 0.1)
  const n = (n1 * 1.2 + n2 * 0.9 + n3 * 0.5) / 2.6
  // push toward the extremes so mid-grey noise collapses into clear
  // black-or-dense regions instead of an even haze
  const shaped = Math.sign(n) * Math.pow(Math.abs(n), 0.6)
  return Math.min(1, Math.max(0, (shaped + 1) / 2))
}

/**
 * Preset for using the grid as page-level background texture. Heavy generative
 * detail belongs inside labeled panels; behind real content the field has to
 * stay sparse and light or drifting noise regions wash out the type.
 */
export const AMBIENT_FIELD = {
  chars: [' ', '.', '.', ':', '-', '+'],
  threshold: 0.72,
  minOpacity: 0.05,
  maxOpacity: 0.2,
  intervalMs: 130,
}

interface GenerativeGridProps {
  className?: string
  /** rgb triple, e.g. "218, 250, 156" */
  accent?: string
  /** density ramp, light -> heavy. Noise magnitude picks a glyph off this ramp
   *  (rather than a random one), so the field reads as organic light/dark
   *  regions instead of scattered flicker. */
  chars?: string[]
  cell?: number
  fontSize?: number
  minOpacity?: number
  maxOpacity?: number
  /** ms between full-field recomputes — lower = more frantic */
  intervalMs?: number
  /** max random px offset applied to each glyph, for a subtle vibrating /
   *  distorted feel rather than perfectly grid-locked text */
  jitter?: number
  /** probability a cell flashes a random ramp glyph instead of its mapped
   *  one — a light static-like flicker on top of the noise field */
  glitchChance?: number
  /** noise values below this are left blank, so empty regions read as true
   *  black instead of a uniform haze */
  threshold?: number
  /** horizontal opacity mask, as a fraction of canvas width (0-1) marking
   *  where the dense field fades down to `quietOpacity` — for keeping a
   *  content column (e.g. hero copy) calm while the rest of the canvas runs
   *  at full density, matching how the reference composites busy generative
   *  panels beside (not underneath) body text. Pass 0 to disable. */
  quietUntil?: number
  quietOpacity?: number
}

/**
 * Full-field generative character grid, driven by cheap procedural noise.
 * Recomputes and redraws the whole canvas on a throttled interval (not per
 * -character DOM nodes, not requestAnimationFrame-per-frame) so dense,
 * contiguous regions of glyphs stay cheap even across a large hero area.
 */
export default function GenerativeGrid({
  className = '',
  accent = '218, 250, 156', // primary-300 (#dafa9c)
  chars = [' ', '.', ':', '-', '+', '*', '#', '%', '@'],
  cell = 13,
  fontSize = 11,
  minOpacity = 0.07,
  maxOpacity = 0.65,
  intervalMs = 90,
  jitter = 1,
  glitchChance = 0.03,
  threshold = 0.48,
  quietUntil = 0,
  quietOpacity = 0.1,
}: GenerativeGridProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const parent = canvas?.parentElement
    const ctx = canvas?.getContext('2d')
    if (!canvas || !parent || !ctx) return

    let width = 0
    let height = 0
    let cols = 0
    let rows = 0
    let raf = 0
    let lastPaint = 0
    const start = performance.now()

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      width = parent!.clientWidth
      height = parent!.clientHeight
      canvas!.width = width * dpr
      canvas!.height = height * dpr
      canvas!.style.width = `${width}px`
      canvas!.style.height = `${height}px`
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx!.font = `${fontSize}px monospace`
      ctx!.textBaseline = 'middle'

      cols = Math.ceil(width / cell)
      rows = Math.ceil(height / cell)
    }

    function paint(now: number) {
      const t = (now - start) / 1000
      ctx!.clearRect(0, 0, width, height)

      const quietPx = width * quietUntil
      const bandPx = width * 0.12

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const n = noise2D(c, r, t)
          if (n < threshold) continue

          const strength = (n - threshold) / (1 - threshold)
          const rampIdx = Math.min(chars.length - 1, Math.floor(strength * chars.length))
          const glyph =
            Math.random() < glitchChance
              ? chars[Math.floor(Math.random() * chars.length)]
              : chars[rampIdx]
          if (glyph === ' ') continue

          let opacity = minOpacity + strength * (maxOpacity - minOpacity)

          if (quietUntil > 0) {
            const px = c * cell
            const edge = quietPx - bandPx / 2
            const mask =
              px < edge ? quietOpacity : px > edge + bandPx ? 1 : quietOpacity + ((px - edge) / bandPx) * (1 - quietOpacity)
            opacity *= mask
          }
          if (opacity <= 0.015) continue

          const dx = (Math.random() - 0.5) * jitter
          const dy = (Math.random() - 0.5) * jitter

          ctx!.fillStyle = `rgba(${accent}, ${opacity.toFixed(3)})`
          ctx!.fillText(glyph, c * cell + cell / 2 + dx, r * cell + cell / 2 + dy)
        }
      }
    }

    function tick(now: number) {
      raf = requestAnimationFrame(tick)
      if (now - lastPaint < intervalMs) return
      lastPaint = now
      paint(now)
    }

    resize()
    window.addEventListener('resize', resize)
    raf = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accent, cell, fontSize, minOpacity, maxOpacity, intervalMs, jitter, glitchChance, threshold, quietUntil, quietOpacity])

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />
}
