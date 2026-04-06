'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { GraduationCap, ArrowRight, CheckCircle, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'

function ResetPasswordForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  // Redirect if no token present
  useEffect(() => {
    if (!token) router.replace('/forgot-password')
  }, [token, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirm) { setError('Passwords do not match.'); return }
    if (password.length < 8) { setError('Password must be at least 8 characters.'); return }

    setSubmitting(true)
    try {
      await api.resetPassword(token, password)
      setDone(true)
    } catch (err: any) {
      const msg: string = err.message || ''
      if (msg.includes('400')) setError('This reset link is invalid or has expired.')
      else setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  const inputClass = `w-full border border-slate-300 rounded-xl px-4 py-3 text-sm
                      text-slate-900 placeholder-slate-400
                      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                      transition-shadow`

  return (
    <div className="w-full max-w-sm">
      {/* Mobile logo */}
      <div className="lg:hidden flex items-center gap-2.5 mb-8">
        <div className="w-9 h-9 bg-slate-900 rounded-xl flex items-center justify-center">
          <GraduationCap className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900 leading-none">Admission Assistant</p>
          <p className="text-xs text-slate-500 leading-none mt-0.5">University of Karachi</p>
        </div>
      </div>

      {done ? (
        /* Success */
        <div className="text-center">
          <div className="w-14 h-14 bg-emerald-50 border border-emerald-200 rounded-2xl
                          flex items-center justify-center mx-auto mb-5">
            <CheckCircle className="w-7 h-7 text-emerald-600" />
          </div>
          <h2 className="font-serif-display text-2xl text-slate-900 mb-2">Password updated</h2>
          <p className="text-sm text-slate-500 mb-8">
            Your password has been reset successfully. You can now sign in.
          </p>
          <Link href="/login"
            className="inline-flex items-center gap-1.5 px-5 py-2.5 bg-slate-900 hover:bg-slate-800
                       text-white rounded-xl text-sm font-semibold transition-colors">
            Go to Sign in
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : !token ? (
        /* No token */
        <div className="text-center">
          <div className="w-14 h-14 bg-amber-50 border border-amber-200 rounded-2xl
                          flex items-center justify-center mx-auto mb-5">
            <AlertCircle className="w-7 h-7 text-amber-600" />
          </div>
          <h2 className="font-serif-display text-2xl text-slate-900 mb-2">Invalid link</h2>
          <p className="text-sm text-slate-500 mb-6">
            This password reset link is missing a token. Please request a new one.
          </p>
          <Link href="/forgot-password"
            className="text-sm font-semibold text-primary-600 hover:text-primary-700">
            Request a new link
          </Link>
        </div>
      ) : (
        /* Form */
        <>
          <h2 className="font-serif-display text-3xl text-slate-900 mb-1">Set new password</h2>
          <p className="text-sm text-slate-500 mb-8">Must be at least 8 characters.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1.5">
                New Password
              </label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                required minLength={8} className={inputClass} placeholder="Min. 8 characters" />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1.5">
                Confirm Password
              </label>
              <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)}
                required className={inputClass} placeholder="••••••••" />
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
              className="w-full bg-slate-900 hover:bg-slate-800 text-white py-3 px-4 rounded-xl
                         text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2 transition-colors"
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Updating…
                </>
              ) : (
                'Reset password'
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <Link href="/login"
              className="flex items-center justify-center gap-1 text-sm text-slate-500
                         hover:text-slate-700 transition-colors">
              <ArrowRight className="w-3.5 h-3.5 rotate-180" />
              Back to sign in
            </Link>
          </div>
        </>
      )}
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-5/12 bg-slate-950 flex-col items-center justify-center
                      relative overflow-hidden p-12 select-none">
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {[480, 360, 260, 170, 90].map((size, i) => (
            <div key={i} className="absolute rounded-full border border-white/[0.04]"
              style={{ width: size, height: size }} />
          ))}
          <div className="absolute w-32 h-32 rounded-full border border-amber-400/20" />
        </div>
        <div className="relative z-10 text-center">
          <div className="w-16 h-16 bg-white/10 backdrop-blur rounded-2xl flex items-center
                          justify-center mx-auto mb-8 border border-white/10">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="font-serif-display text-4xl text-white leading-tight mb-4">
            Secure your<br />account
          </h1>
          <p className="text-slate-500 text-sm leading-relaxed max-w-xs mx-auto">
            Choose a strong password that you haven&apos;t used before.
          </p>
        </div>
      </div>

      {/* Right panel — Suspense needed for useSearchParams */}
      <div className="flex-1 flex items-center justify-center bg-white px-8 py-12">
        <Suspense fallback={<div className="text-sm text-slate-400">Loading…</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  )
}
