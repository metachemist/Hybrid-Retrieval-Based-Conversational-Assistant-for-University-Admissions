'use client'

import { useEffect, useRef } from 'react'

/**
 * Small accent square that trails the pointer, echoing the reference's
 * "selection handle" motif. Purely decorative: it sits alongside the native
 * cursor (never replaces it) and is skipped entirely on touch/coarse
 * pointers and when the user has asked for reduced motion.
 */
export default function CursorSquare() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const fine = window.matchMedia('(pointer: fine)').matches
    const stillness = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!fine || stillness) return

    // target = live pointer, pos = eased follower
    let tx = -100
    let ty = -100
    let x = -100
    let y = -100
    let raf = 0

    function onMove(e: MouseEvent) {
      tx = e.clientX
      ty = e.clientY
      el!.style.opacity = '1'
    }
    function onLeave() {
      el!.style.opacity = '0'
    }

    function tick() {
      raf = requestAnimationFrame(tick)
      // critically-damped-ish follow; the lag is the whole effect
      x += (tx - x) * 0.14
      y += (ty - y) * 0.14
      el!.style.transform = `translate3d(${x - 5}px, ${y - 5}px, 0)`
    }

    window.addEventListener('mousemove', onMove, { passive: true })
    document.addEventListener('mouseleave', onLeave)
    raf = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseleave', onLeave)
    }
  }, [])

  return (
    <div
      ref={ref}
      aria-hidden="true"
      className="pointer-events-none fixed left-0 top-0 z-[60] h-2.5 w-2.5 bg-primary-300 opacity-0
                 transition-opacity duration-300 mix-blend-difference max-lg:hidden"
    />
  )
}
