'use client'

import Link from 'next/link'

type Variant = 'accent' | 'outline' | 'dark'

interface SlideButtonProps {
  href: string
  children: string
  variant?: Variant
  className?: string
  icon?: React.ReactNode
}

const VARIANTS: Record<Variant, string> = {
  accent: 'bg-primary-300 hover:bg-primary-200 text-neutral-900',
  outline: 'bg-ink-line hover:bg-[#262626] text-white border border-muted/60',
  dark: 'bg-neutral-900 hover:bg-neutral-800 text-white',
}

/**
 * Button whose label rides upward on hover while an identical copy rises
 * into its place — the reference's signature control interaction. The label
 * is duplicated in the DOM, so the second copy is hidden from screen readers
 * to avoid announcing it twice.
 */
export default function SlideButton({
  href,
  children,
  variant = 'accent',
  className = '',
  icon,
}: SlideButtonProps) {
  return (
    <Link
      href={href}
      className={`group inline-flex items-center justify-center gap-2 rounded overflow-hidden
                  px-7 py-4 text-[15px] font-medium tracking-[0.01em]
                  transition-colors duration-300 ${VARIANTS[variant]} ${className}`}
    >
      {/* Fixed-height viewport: copy #1 slides out the top as copy #2 arrives */}
      <span className="relative block h-[1.15em] overflow-hidden">
        <span
          className="block transition-transform duration-[450ms] ease-[cubic-bezier(0.16,1,0.3,1)]
                     group-hover:-translate-y-full"
        >
          {children}
        </span>
        <span
          aria-hidden="true"
          className="absolute inset-x-0 top-full block transition-transform duration-[450ms]
                     ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:-translate-y-full"
        >
          {children}
        </span>
      </span>
      {icon && (
        <span className="transition-transform duration-300 group-hover:translate-x-1">{icon}</span>
      )}
    </Link>
  )
}
