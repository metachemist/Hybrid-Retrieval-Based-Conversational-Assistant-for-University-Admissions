'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ChevronDown, ChevronRight, ArrowRight } from 'lucide-react'
import { useAuth } from '@/lib/auth'

/**
 * Registration, styled to the landing page's system rather than to a generic
 * SaaS auth screen: uppercase display headings, mono micro-labels with
 * negative tracking, squared surfaces, and the single lime accent. The dark
 * left panel reuses the hero's dotted rule grid so the two read as one site.
 */

/** What the dark panel advertises. Mirrors the landing page's numbered features. */
const HIGHLIGHTS = [
  { n: '01', title: 'Hybrid retrieval', body: 'Keyword and vector search, fused into one ranking.' },
  { n: '02', title: 'English + Roman Urdu', body: 'Ask the way you actually type.' },
  { n: '03', title: 'Cited sources', body: 'Every answer links back to the document it came from.' },
]

/** Mono micro-label above a field. Matches .label-mono, sized down for forms. */
function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <label className="mb-2 block font-mono text-[11px] uppercase tracking-tighter2 text-muted">
      {children}
    </label>
  )
}

export default function RegisterPage() {
  const { register, user, isLoading } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [adminKey, setAdminKey] = useState('')
  const [showAdminKey, setShowAdminKey] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!isLoading && user) {
      router.replace('/chat')
    }
  }, [user, isLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirm) { setError('Passwords do not match.'); return }
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return }

    setSubmitting(true)
    try {
      await register(email, password, adminKey || undefined)
      router.replace('/chat')
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  // Squared, hairline-bordered inputs. The border darkens on focus instead of
  // growing a coloured ring, which keeps the form quiet next to the accent.
  const inputClass = `w-full rounded-none border border-neutral-300 bg-white px-4 py-3
                      text-[15px] text-neutral-900 placeholder-neutral-400
                      transition-colors focus:border-neutral-900 focus:outline-none`

  return (
    <div className="flex min-h-screen">

      {/* ══ Left panel: dark, dotted rule grid, wordmark + statement ══ */}
      <div className="grid-lines-dark relative hidden select-none flex-col justify-between
                      overflow-hidden bg-ink p-12 text-white lg:flex lg:w-5/12 xl:p-14">

        {/* Wordmark + session meta, same pairing as the landing hero */}
        <div className="flex items-start justify-between gap-6">
          <Link href="/" className="display-lg text-[26px] transition-opacity hover:opacity-70">
            Rehnuma
          </Link>
          <div className="flex items-start gap-2.5 text-right text-[13px] leading-relaxed text-neutral-400">
            <span className="mt-[6px] h-2 w-2 shrink-0 bg-primary-300" />
            <span>
              Admissions 2026
              <br />
              University of Karachi
            </span>
          </div>
        </div>

        {/* Statement */}
        <div className="max-w-[22rem] py-14">
          <p className="label-mono mb-6">Create an account</p>
          <h1 className="display-xl text-[clamp(2.4rem,3.6vw,3.4rem)]">
            Start your
            <br />
            <span className="text-primary-300">journey.</span>
          </h1>
          <p className="mt-8 text-[15px] leading-[1.7] text-neutral-400">
            One account gives you the full assistant: ask about eligibility, fees, deadlines and
            required documents, and get answers pulled straight from official policy documents.
          </p>
        </div>

        {/* Numbered highlights, echoing the landing page's feature list */}
        <ul className="border-t border-white/15">
          {HIGHLIGHTS.map(({ n, title, body }) => (
            <li key={n} className="flex gap-5 border-b border-white/10 py-4">
              <span className="mt-[3px] font-mono text-[11px] tracking-tighter2 text-primary-300">
                {n}
              </span>
              <span>
                <span className="block text-[14px] font-medium text-white">{title}</span>
                <span className="mt-1 block text-[13px] leading-relaxed text-neutral-500">
                  {body}
                </span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* ══ Right panel: the form ═══════════════════════════════════ */}
      <div className="flex flex-1 items-center justify-center bg-white px-6 py-14 sm:px-10">
        <div className="w-full max-w-[26rem]">

          {/* Mobile wordmark, since the dark panel is hidden below lg */}
          <Link href="/" className="mb-12 flex items-center gap-3 lg:hidden">
            <span className="h-2.5 w-2.5 bg-primary-500" />
            <span className="display-lg text-[20px] text-neutral-900">Rehnuma</span>
          </Link>

          <p className="label-mono mb-5">Registration</p>
          <h2 className="display-lg text-[clamp(1.9rem,4vw,2.4rem)] text-neutral-900">
            Create account
          </h2>
          <p className="mt-4 text-[15px] leading-relaxed text-neutral-500">
            Already registered?{' '}
            <Link
              href="/login"
              className="border-b border-neutral-400 pb-[1px] font-medium text-neutral-900
                         transition-colors hover:border-primary-500 hover:text-primary-600"
            >
              Sign in instead
            </Link>
          </p>

          <form onSubmit={handleSubmit} className="mt-10 space-y-5">
            <div>
              <FieldLabel>Email</FieldLabel>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className={inputClass}
                placeholder="you@example.com"
              />
            </div>

            <div>
              <FieldLabel>Password</FieldLabel>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
                className={inputClass}
                placeholder="Minimum 8 characters"
              />
            </div>

            <div>
              <FieldLabel>Confirm password</FieldLabel>
              <input
                type="password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                required
                className={inputClass}
                placeholder="Repeat your password"
              />
            </div>

            {/* Admin key, kept collapsed: relevant to a handful of staff accounts */}
            <div className="border-t border-neutral-200 pt-5">
              <button
                type="button"
                onClick={() => setShowAdminKey(v => !v)}
                aria-expanded={showAdminKey}
                className="flex items-center gap-1.5 font-mono text-[11px] uppercase
                           tracking-tighter2 text-muted transition-colors hover:text-neutral-900"
              >
                {showAdminKey
                  ? <ChevronDown className="h-3.5 w-3.5" />
                  : <ChevronRight className="h-3.5 w-3.5" />}
                Admin registration key (optional)
              </button>
              {showAdminKey && (
                <input
                  type="password"
                  value={adminKey}
                  onChange={e => setAdminKey(e.target.value)}
                  className={`mt-3 ${inputClass}`}
                  placeholder="Enter admin key to register as admin"
                />
              )}
            </div>

            {error && (
              <div
                role="alert"
                className="border-l-2 border-red-500 bg-red-50 px-4 py-3 text-[14px] text-red-800"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="group flex w-full items-center justify-center gap-2 rounded
                         bg-primary-300 px-7 py-4 text-[15px] font-medium tracking-[0.01em]
                         text-neutral-900 transition-colors hover:bg-primary-200
                         disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-neutral-900/30 border-t-neutral-900" />
                  Creating account
                </>
              ) : (
                <>
                  Create account
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>
          </form>

          <Link
            href="/"
            className="mt-10 inline-flex items-center gap-2 font-mono text-[11px] uppercase
                       tracking-tighter2 text-muted transition-colors hover:text-neutral-900"
          >
            <ArrowRight className="h-3.5 w-3.5 rotate-180" />
            Back to home
          </Link>
        </div>
      </div>
    </div>
  )
}
