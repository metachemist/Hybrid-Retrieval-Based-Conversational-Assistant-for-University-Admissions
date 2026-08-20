'use client'

import { useEffect, useRef } from 'react'

// Lightweight layered-sine hash — smooth, spatially-continuous pseudo-noise
// without pulling in a real Perlin/Simplex library for a decorative effect.
function noise2D(x: number, y: number, t: number): number {
  const n =
    Math.sin(x * 0.12 + t * 0.6) * Math.cos(y * 0.1 - t * 0.4) +
    Math.sin((x + y) * 0.07 - t * 0.3) * 0.6
  return (n + 1.6) / 3.2
}

interface GenerativeGridProps {
  className?: string
  /** rgb triple, e.g. "218, 250, 156" */
  accent?: string
  chars?: string[]
  cell?: number
  fontSize?: number
  /** fraction of the grid considered for mutation on each pass */
  mutateFraction?: number
  minOpacity?: number
  maxOpacity?: number
  /** ms between mutation passes — lower = more frantic */
  intervalMs?: number
}

/**
 * Canvas of mutating characters, driven by cheap procedural noise. Repaints
 * only the handful of cells that change each tick (no full-canvas redraw, no
 * per-character DOM nodes) so it stays light even across a large hero area.
 */
export default function GenerativeGrid({
  className = '',
  accent = '218, 250, 156', // primary-300 (#dafa9c)
  chars = ['+', '+', '+', '-', '.', '0', '1'],
  cell = 16,
  fontSize = 11,
  mutateFraction = 0.015,
  minOpacity = 0.08,
  maxOpacity = 0.3,
  intervalMs = 70,
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
    let cells: { char: string; opacity: number }[] = []
    let raf = 0
    let lastMutate = 0
    const start = performance.now()

    function paintCell(c: number, r: number) {
      const cellData = cells[r * cols + c]
      const x = c * cell
      const y = r * cell
      ctx!.clearRect(x, y, cell, cell)
      if (cellData.opacity <= 0.01) return
      ctx!.fillStyle = `rgba(${accent}, ${cellData.opacity.toFixed(3)})`
      ctx!.fillText(cellData.char, x + cell / 2, y + cell / 2)
    }

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
      cells = Array.from({ length: cols * rows }, () => ({ char: chars[0], opacity: 0 }))
    }

    function tick(now: number) {
      raf = requestAnimationFrame(tick)
      if (now - lastMutate < intervalMs) return
      lastMutate = now
      const t = (now - start) / 1000

      const mutateCount = Math.max(4, Math.floor(cols * rows * mutateFraction))
      for (let i = 0; i < mutateCount; i++) {
        const c = Math.floor(Math.random() * cols)
        const r = Math.floor(Math.random() * rows)
        const n = noise2D(c, r, t)
        const cellData = cells[r * cols + c]
        if (n > 0.55) {
          cellData.char = chars[Math.floor(Math.random() * chars.length)]
          cellData.opacity = minOpacity + n * (maxOpacity - minOpacity)
        } else {
          cellData.opacity = Math.max(0, cellData.opacity - 0.05)
        }
        paintCell(c, r)
      }
    }

    resize()
    window.addEventListener('resize', resize)
    raf = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accent, cell, fontSize, mutateFraction, minOpacity, maxOpacity, intervalMs])

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />
}
