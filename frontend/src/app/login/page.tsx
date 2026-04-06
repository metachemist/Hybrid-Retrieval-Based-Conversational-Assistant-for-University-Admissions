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

  useEffect(() => {
    if (!isLoading && user) {
      router.replace(user.role === 'admin' ? '/admin' : '/')
    }
  }, [user, isLoading, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const profile = await login(email, password)
      router.replace(profile.role === 'admin' ? '/admin' : '/')
    } catch (err: any) {
      setError(err.message.includes('401') ? 'Invalid email or password.' : err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Left panel (decorative) ──────────────────────── */}
      <div className="hidden lg:flex lg:w-5/12 bg-slate-950 flex-col items-center justify-center
                      relative overflow-hidden p-12 select-none">
        {/* Concentric ring decorations */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {[480, 360, 260, 170, 90].map((size, i) => (
            <div
              key={i}
              className="absolute rounded-full border border-white/[0.04]"
              style={{ width: size, height: size }}
            />
          ))}
          {/* Amber accent ring */}
          <div className="absolute w-32 h-32 rounded-full border border-amber-400/20" />
        </div>

        {/* Content */}
        <div className="relative z-10 text-center">
          <div className="w-16 h-16 bg-white/10 backdrop-blur rounded-2xl flex items-center
                          justify-center mx-auto mb-8 border border-white/10">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="font-serif-display text-4xl text-white leading-tight mb-4">
            University of<br />Karachi
          </h1>
          <p className="text-slate-500 text-sm leading-relaxed max-w-xs mx-auto">
            AI-powered admission information — get instant, document-grounded answers to your queries.
          </p>

          {/* Stat pills */}
          <div className="flex gap-3 mt-10 justify-center flex-wrap">
            {['RAG-Powered', 'Roman Urdu Support', 'Cited Sources'].map(tag => (
              <span key={tag}
                className="px-3 py-1 rounded-full bg-white/5 border border-white/10
                           text-xs text-slate-400 font-medium">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right panel (form) ───────────────────────────── */}
      <div className="flex-1 flex items-center justify-center bg-white px-8 py-12">
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

          <h2 className="font-serif-display text-3xl text-slate-900 mb-1">Welcome back</h2>
          <p className="text-sm text-slate-500 mb-8">Sign in to your account to continue.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1.5">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full border border-slate-300 rounded-xl px-4 py-3 text-sm
                           text-slate-900 placeholder-slate-400
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                           transition-shadow"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wide mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="w-full border border-slate-300 rounded-xl px-4 py-3 text-sm
                           text-slate-900 placeholder-slate-400
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
              className="w-full bg-slate-900 hover:bg-slate-800 text-white py-3 px-4 rounded-xl
                         text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed
                         flex items-center justify-center gap-2 transition-colors mt-2"
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
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

          <div className="mt-6 pt-6 border-t border-slate-100 space-y-2 text-sm text-center">
            <p className="text-slate-500">
              Don&apos;t have an account?{' '}
              <Link href="/register" className="text-primary-600 hover:text-primary-700 font-semibold">
                Create one
              </Link>
            </p>
            <Link href="/" className="flex items-center justify-center gap-1 text-slate-400 hover:text-slate-600 transition-colors">
              <ArrowRight className="w-3.5 h-3.5 rotate-180" />
              Back to chatbot
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
