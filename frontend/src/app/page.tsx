'use client'

import Link from 'next/link'
import {
  GraduationCap,
  ArrowRight,
  Search,
  Languages,
  FileCheck,
  MessageCircle,
  Database,
  BadgeCheck,
  Sparkles,
} from 'lucide-react'
import ScrambleCodeBlock from '@/components/ScrambleCodeBlock'

const STATS = [
  { value: '2', label: 'Retrieval methods combined' },
  { value: '24/7', label: 'Available anytime' },
  { value: '100%', label: 'Answers cited' },
]

const FEATURES = [
  {
    icon: Search,
    title: 'Hybrid retrieval',
    body: 'Combines keyword search (BM25) with semantic vector search over official admission documents, so answers are grounded in the source text, not guesses.',
  },
  {
    icon: Languages,
    title: 'English + Roman Urdu',
    body: 'Ask your question in either language and get a response in kind — built for how students actually type.',
  },
  {
    icon: FileCheck,
    title: 'Cited sources',
    body: 'Every answer links back to the exact document, section, and page it came from, so you can verify it yourself.',
  },
]

const STEPS = [
  {
    n: '01',
    icon: MessageCircle,
    title: 'Ask your question',
    body: 'Eligibility, fees, deadlines, required documents — type it the way you’d ask a friend.',
  },
  {
    n: '02',
    icon: Database,
    title: 'We search the documents',
    body: 'The assistant retrieves the most relevant passages from official University of Karachi admission policies.',
  },
  {
    n: '03',
    icon: BadgeCheck,
    title: 'Get a cited answer',
    body: 'A concise, accurate response with links to the exact source material behind it.',
  },
]

/** Bordered decorative panel with corner "handles", echoing a design-tool selection frame. */
function CornerFrame({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`relative border border-white/15 ${className}`}>
      {[
        'top-0 left-0 -translate-x-1/2 -translate-y-1/2',
        'top-0 right-0 translate-x-1/2 -translate-y-1/2',
        'bottom-0 left-0 -translate-x-1/2 translate-y-1/2',
        'bottom-0 right-0 translate-x-1/2 translate-y-1/2',
      ].map(pos => (
        <span key={pos} className={`absolute ${pos} w-2 h-2 border border-primary-400 bg-[#111111]`} />
      ))}
      {children}
    </div>
  )
}

export default function LandingPage() {
  return (
    <main className="bg-white">

      {/* ── Black block: nav + hero ──────────────────────── */}
      <div className="dot-grid-dark relative overflow-hidden bg-[#111111] text-white">
        <header className="px-6 sm:px-10 relative z-10">
          <div className="max-w-5xl mx-auto flex items-center justify-between h-16">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                <GraduationCap className="w-4.5 h-4.5 text-primary-400" strokeWidth={2} />
              </div>
              <div>
                <p className="text-sm font-semibold leading-none">Admission Assistant</p>
                <p className="text-xs text-neutral-500 leading-none mt-0.5">University of Karachi</p>
              </div>
            </div>
            <Link
              href="/login"
              className="px-4 py-1.5 rounded-full bg-primary-300 hover:bg-primary-200 text-neutral-900
                         text-xs font-semibold transition-all hover:scale-105 active:scale-95"
            >
              Sign in
            </Link>
          </div>
        </header>

        <section className="relative z-10 max-w-5xl mx-auto px-6 sm:px-10 pt-16 pb-24 sm:pt-24 sm:pb-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="text-xs font-medium uppercase tracking-widest text-neutral-500 mb-6 animate-in-up">
                &middot; University of Karachi &middot; Admissions 2026
              </p>

              <h1 className="font-display font-bold text-5xl sm:text-7xl leading-[0.95] tracking-tight mb-8 animate-in-up stagger-1">
                STOP GUESSING.
                <br />
                <span className="text-primary-400">ASK THE ASSISTANT.</span>
              </h1>

              <p className="text-neutral-400 text-base sm:text-lg leading-relaxed max-w-lg mb-10 animate-in-up stagger-2">
                Instant, cited answers about admissions — eligibility, fees, deadlines, and required
                documents — pulled straight from official policy documents.
              </p>

              <div className="flex flex-col sm:flex-row items-start gap-3 animate-in-up stagger-3">
                <Link
                  href="/login"
                  className="w-full sm:w-auto flex items-center justify-center gap-2 px-7 py-3.5 rounded-full
                             bg-primary-300 hover:bg-primary-200 text-neutral-900 font-semibold text-sm
                             transition-all hover:scale-105 active:scale-95"
                >
                  Take me to the chatbot
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/register"
                  className="w-full sm:w-auto flex items-center justify-center px-7 py-3.5 rounded-full
                             bg-white/5 hover:bg-white/10 border border-white/10 font-semibold text-sm
                             transition-all hover:scale-105 active:scale-95"
                >
                  Create an account
                </Link>
              </div>
            </div>

            {/* RAG.PY panel — right of the hero text */}
            <div className="hidden lg:block animate-in-up stagger-2">
              <span className="inline-block mb-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wide bg-primary-300 text-neutral-900">
                RAG.PY
              </span>
              <CornerFrame className="h-52 bg-white/[0.03] rounded-lg overflow-hidden p-5">
                <ScrambleCodeBlock className="text-sm leading-[1.7]" />
              </CornerFrame>
            </div>
          </div>
        </section>
      </div>

      {/* ── White block: stats + features ──────────────── */}
      <section className="max-w-5xl mx-auto px-6 sm:px-10 py-20">
        <div className="grid grid-cols-3 gap-6 mb-20">
          {STATS.map(({ value, label }) => (
            <div key={label}>
              <p className="font-display font-bold text-5xl sm:text-6xl text-neutral-900 mb-2">{value}</p>
              <p className="text-xs uppercase tracking-widest text-neutral-400">{label}</p>
            </div>
          ))}
        </div>

        <p className="text-xs font-semibold uppercase tracking-widest text-primary-600 mb-3">
          Why it&apos;s different
        </p>
        <h2 className="font-display font-bold text-3xl sm:text-4xl text-neutral-900 mb-14 max-w-lg">
          Built to be checked, not just trusted.
        </h2>

        <div className="grid sm:grid-cols-3 gap-x-8 gap-y-12">
          {FEATURES.map(({ icon: Icon, title, body }) => (
            <div key={title}>
              <Icon className="w-5 h-5 text-neutral-900 mb-4" strokeWidth={1.75} />
              <h3 className="font-semibold text-neutral-900 mb-2">{title}</h3>
              <p className="text-sm text-neutral-500 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Black block: how it works + CTA + footer ─────── */}
      <div className="dot-grid-dark bg-[#111111] text-white">
        <section className="max-w-5xl mx-auto px-6 sm:px-10 py-24">
          <p className="text-xs font-semibold uppercase tracking-widest text-primary-400 mb-3">
            How it works
          </p>

          <div className="grid sm:grid-cols-2 gap-10 items-center mb-16">
            <h2 className="font-display font-bold text-3xl sm:text-4xl leading-tight">
              Three steps to a sourced answer. No pre-written scripts — every answer is retrieved live.
            </h2>
            <CornerFrame className="bg-white/[0.02] rounded-2xl aspect-video flex items-center justify-center">
              <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center animate-float">
                <Sparkles className="w-7 h-7 text-primary-400" />
              </div>
            </CornerFrame>
          </div>

          <div className="grid sm:grid-cols-3 border-t border-white/20 pt-8">
            {STEPS.map(({ n, icon: Icon, title, body }, i) => (
              <div
                key={n}
                className={`px-0 sm:px-8 ${i > 0 ? 'sm:border-l border-white/20' : ''} ${i > 0 ? 'mt-8 sm:mt-0' : ''}`}
              >
                <div className="flex items-center gap-3 mb-4">
                  <span className="font-display font-bold text-2xl text-neutral-600">{n}.</span>
                  <Icon className="w-5 h-5 text-primary-400" strokeWidth={1.75} />
                </div>
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-sm text-neutral-400 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="border-t border-white/20">
          <div className="max-w-5xl mx-auto px-6 sm:px-10 py-24 text-center">
            <h2 className="font-display font-bold text-4xl sm:text-6xl mb-4">
              READY WHEN YOU ARE.
            </h2>
            <p className="text-neutral-400 mb-8 max-w-md mx-auto">
              Sign in or create a free account to start asking questions about admissions.
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full
                         bg-primary-300 hover:bg-primary-200 text-neutral-900 font-semibold text-sm
                         transition-all hover:scale-105 active:scale-95"
            >
              Take me to the chatbot
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>

        <footer className="border-t border-white/20 px-6 sm:px-10 py-8">
          <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3
                          text-xs text-neutral-500">
            <p>&copy; {new Date().getFullYear()} Admission Assistant &middot; University of Karachi</p>
            <p>Responses sourced from official admission documents &middot; Always verify with the admissions office</p>
          </div>
        </footer>
      </div>
    </main>
  )
}
