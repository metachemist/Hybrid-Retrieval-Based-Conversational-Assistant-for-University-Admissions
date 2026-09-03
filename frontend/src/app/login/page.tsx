'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { GraduationCap, LogIn, ArrowRight } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export default function LoginPage() {
  const { login, user, isLoading } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Everyone lands on the chatbot after signing in. An admin then reaches the
  // dashboard via the Dashboard button that only shows for them in the chat header.
  useEffect(() => {
    if (!isLoading && user) {
      router.replace('/chat')
    }
  }, [user, isLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
      router.replace('/chat')
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Left panel (decorative) ──────────────────────── */}
      <div className="dot-grid-dark hidden lg:flex lg:w-5/12 bg-[#111111] flex-col items-center justify-center
                      relative overflow-hidden p-12 select-none">
        {/* Content */}
        <div className="relative z-10 text-center">
          <div className="w-16 h-16 bg-white/10 backdrop-blur rounded-2xl flex items-center
                          justify-center mx-auto mb-8 border border-white/10 animate-float">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="display-xl text-6xl text-primary-300 mb-4 animate-in-up">
            University of<br />Karachi
          </h1>
          <p className="text-neutral-500 text-sm leading-relaxed max-w-xs mx-auto animate-in-up stagger-1">
            AI-powered admission information: get instant, document-grounded answers to your queries.
          </p>

          {/* Stat pills */}
          <div className="flex gap-3 mt-10 justify-center flex-wrap">
            {['RAG-Powered', 'Roman Urdu Support', 'Cited Sources'].map((tag, i) => (
              <span key={tag}
                style={{ animationDelay: `${0.3 + i * 0.08}s` }}
                className="animate-in-up px-3 py-1 rounded-full bg-white/5 border border-white/10
                           text-xs text-neutral-400 font-medium hover:border-primary-400/40
                           hover:text-primary-300 transition-colors">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right panel (form) ───────────────────────────── */}
      <div className="flex-1 flex items-center justify-center bg-white px-8 py-12">
        <div className="w-full max-w-sm animate-in-up">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2.5 mb-8">
            <div className="w-9 h-9 bg-neutral-900 rounded-xl flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-neutral-900 leading-none">Rehnuma</p>
              <p className="text-xs text-neutral-500 leading-none mt-0.5">University of Karachi</p>
            </div>
          </div>

          <h2 className="display-lg text-3xl text-neutral-900 mb-1">Admin sign in</h2>
          <p className="text-sm text-neutral-500 mb-8">
            Staff only. The chatbot itself needs no account &mdash;{' '}
            <Link href="/chat" className="text-primary-600 hover:text-primary-700 font-medium">
              open Rehnuma
            </Link>
            .
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label-mono block mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full border border-neutral-300 rounded-xl px-4 py-3 text-sm
                           text-neutral-900 placeholder-neutral-400
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                           transition-shadow"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="label-mono">
                  Password
                </label>
                <Link href="/forgot-password"
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium">
                  Forgot password?
                </Link>
              </div>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="w-full border border-neutral-300 rounded-xl px-4 py-3 text-sm
                           text-neutral-900 placeholder-neutral-400
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                           transition-shadow"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700
                              px-4 py-3 rounded-xl text-sm">
                <span className="mt-0.5">⚠</span>
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-primary-300 hover:bg-primary-200 text-neutral-900 py-3 px-4 rounded-full
                         text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2 transition-all mt-2
                         hover:scale-[1.02] active:scale-[0.98]"
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-neutral-900/30 border-t-neutral-900 rounded-full animate-spin" />
                  Signing in…
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  Sign in
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-neutral-100 text-sm text-center">
            <Link href="/" className="flex items-center justify-center gap-1 text-neutral-400 hover:text-neutral-600 transition-colors">
              <ArrowRight className="w-3.5 h-3.5 rotate-180" />
              Back to home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
