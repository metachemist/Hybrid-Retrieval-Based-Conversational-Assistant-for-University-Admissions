'use client'

import { useState } from 'react'
import Link from 'next/link'
import { GraduationCap, ArrowRight, Mail, CheckCircle } from 'lucide-react'
import { api } from '@/lib/api'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await api.forgotPassword(email)
      setSent(true)
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Left panel ───────────────────────────────────── */}
      <div className="dot-grid-dark hidden lg:flex lg:w-5/12 bg-[#111111] flex-col items-center justify-center
                      relative overflow-hidden p-12 select-none">
        <div className="relative z-10 text-center">
          <div className="w-16 h-16 bg-white/10 backdrop-blur rounded-2xl flex items-center
                          justify-center mx-auto mb-8 border border-white/10 animate-float">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="font-display font-bold text-6xl gradient-text leading-tight mb-4 animate-in-up">
            Password<br />Recovery
          </h1>
          <p className="text-neutral-500 text-sm leading-relaxed max-w-xs mx-auto animate-in-up stagger-1">
            Enter your email and we&apos;ll send you a link to reset your password.
            The link expires in 1 hour.
          </p>
        </div>
      </div>

      {/* ── Right panel ──────────────────────────────────── */}
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

          {sent ? (
            /* Success state */
            <div className="text-center">
              <div className="w-14 h-14 bg-emerald-50 border border-emerald-200 rounded-2xl
                              flex items-center justify-center mx-auto mb-5 animate-in-pop">
                <CheckCircle className="w-7 h-7 text-emerald-600" />
              </div>
              <h2 className="font-display font-bold text-2xl text-neutral-900 mb-2">Check your inbox</h2>
              <p className="text-sm text-neutral-500 mb-2 leading-relaxed">
                If <span className="font-medium text-neutral-700">{email}</span> is registered,
                you&apos;ll receive a reset link shortly.
              </p>
              <p className="text-xs text-neutral-400 mb-8">
                No email? Check your spam folder or{' '}
                <button onClick={() => setSent(false)}
                  className="text-primary-600 hover:underline">try again</button>.
              </p>
              <Link href="/login"
                className="flex items-center justify-center gap-1.5 text-sm font-semibold
                           text-neutral-700 hover:text-neutral-900 transition-colors">
                <ArrowRight className="w-4 h-4 rotate-180" />
                Back to sign in
              </Link>
            </div>
          ) : (
            /* Form state */
            <>
              <h2 className="font-display font-bold text-3xl text-neutral-900 mb-1">Forgot password?</h2>
              <p className="text-sm text-neutral-500 mb-8">
                We&apos;ll send a reset link to your email.
              </p>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1.5">
                    Email address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      required
                      className="w-full border border-neutral-300 rounded-xl pl-10 pr-4 py-3 text-sm
                                 text-neutral-900 placeholder-neutral-400
                                 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                                 transition-shadow"
                      placeholder="you@example.com"
                    />
                  </div>
                </div>

                {error && (
                  <div className="flex items-start gap-2 bg-red-50 border border-red-200
                                  text-red-700 px-4 py-3 rounded-xl text-sm">
                    <span className="mt-0.5">⚠</span>
                    <span>{error}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-primary-300 hover:bg-primary-200 text-neutral-900 py-3 px-4 rounded-full
                             text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed
                             flex items-center justify-center gap-2 transition-all
                             hover:scale-[1.02] active:scale-[0.98]"
                >
                  {submitting ? (
                    <>
                      <span className="w-4 h-4 border-2 border-neutral-900/30 border-t-neutral-900 rounded-full animate-spin" />
                      Sending…
                    </>
                  ) : (
                    'Send reset link'
                  )}
                </button>
              </form>

              <div className="mt-6 pt-6 border-t border-neutral-100 text-center">
                <Link href="/login"
                  className="flex items-center justify-center gap-1 text-sm text-neutral-500
                             hover:text-neutral-700 transition-colors">
                  <ArrowRight className="w-3.5 h-3.5 rotate-180" />
                  Back to sign in
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
