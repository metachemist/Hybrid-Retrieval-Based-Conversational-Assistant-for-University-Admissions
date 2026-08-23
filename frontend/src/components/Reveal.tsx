'use client'

import { useEffect, useRef, useState } from 'react'

interface RevealProps {
  children: React.ReactNode
  className?: string
  /** ms to hold before animating in — for staggering siblings */
  delay?: number
  /** how far into the viewport the element must come before firing */
  threshold?: number
  as?: 'div' | 'section' | 'li' | 'header'
}

/**
 * Fades + lifts its children into place the first time they scroll into
 * view. One IntersectionObserver per instance, disconnected on first hit,
 * so nothing keeps running once a section has been revealed.
 */
export default function Reveal({
  children,
  className = '',
  delay = 0,
  threshold = 0.15,
  as: Tag = 'div',
}: RevealProps) {
  const ref = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    // Anything already on screen at mount (the hero) should animate straight
    // away rather than wait for a scroll that may never come.
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold, rootMargin: '0px 0px -8% 0px' },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [threshold])

  return (
    <Tag
      ref={ref as never}
      className={`reveal ${visible ? 'is-visible' : ''} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </Tag>
  )
}
