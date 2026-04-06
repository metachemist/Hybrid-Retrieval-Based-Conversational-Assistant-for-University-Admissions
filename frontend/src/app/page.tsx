'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import ChatMessage from '@/components/ChatMessage'
import ChatInput from '@/components/ChatInput'
import TypingIndicator from '@/components/TypingIndicator'
import { GraduationCap, LayoutDashboard, LogIn, LogOut, Sparkles } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  timestamp: Date
  language?: string
  latency_ms?: number
  llm_provider?: string
}

export interface Citation {
  index: number
  document_title: string
  section_header: string
  page_start: number
  page_end: number
  content_preview: string
}

const SUGGESTIONS = [
  'Eligibility criteria for undergraduate?',
  'Last date for form submission?',
  'Required documents for admission?',
  'Fee structure for this year?',
]

export default function Home() {
  const { user, logout } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (query: string) => {
    if (!query.trim()) return
    setError(null)
    setIsLoading(true)

    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    }])

    try {
      const data = await api.chat({ query, top_k: 10, use_hybrid: true })
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        citations: data.citations,
        timestamp: new Date(),
        language: data.language,
        latency_ms: data.latency_ms,
        llm_provider: data.llm_provider,
      }])
    } catch (err) {
      console.error('Error sending message:', err)
      setError('Failed to get a response. Please try again.')
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error while processing your request. Please try again later.",
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="flex flex-col h-screen bg-slate-50 overflow-hidden">

      {/* ── Header ──────────────────────────────────────── */}
      <header className="flex-shrink-0 bg-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-5 py-3.5 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center shadow-inner">
              <GraduationCap className="w-4.5 h-4.5 text-white" strokeWidth={2} />
            </div>
            <div>
              <p className="text-sm font-semibold leading-none text-white">Admission Assistant</p>
              <p className="text-xs text-slate-400 leading-none mt-0.5">University of Karachi</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1.5">
            {user?.role === 'admin' && (
              <Link
                href="/admin"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                           text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                Dashboard
              </Link>
            )}
            {user ? (
              <button
                onClick={logout}
                title={`Signed in as ${user.email}`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                           text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign out
              </button>
            ) : (
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
                           bg-primary-600 hover:bg-primary-500 text-white transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* ── Messages ─────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          /* Empty state */
          <div className="dot-grid h-full flex items-center justify-center px-4">
            <div className="text-center max-w-lg">
              {/* Icon */}
              <div className="relative inline-flex mb-6">
                <div className="w-16 h-16 rounded-2xl bg-white border border-slate-200 shadow-md
                                flex items-center justify-center">
                  <Sparkles className="w-7 h-7 text-primary-600" />
                </div>
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-400
                                 border-2 border-white" />
              </div>

              {/* Heading */}
              <h2 className="font-serif-display text-3xl text-slate-900 mb-2">
                Ask me anything
              </h2>
              <p className="text-sm text-slate-500 mb-8 leading-relaxed">
                I have access to official University of Karachi admission documents.
                Try asking about eligibility, fees, deadlines, or required materials.
              </p>

              {/* Suggestion chips */}
              <div className="flex flex-wrap gap-2 justify-center">
                {SUGGESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    className="px-4 py-2 bg-white border border-slate-200 text-slate-700
                               rounded-full text-xs font-medium hover:border-primary-400
                               hover:text-primary-700 hover:bg-primary-50
                               shadow-sm transition-all duration-150"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto px-4 py-6 space-y-5">
            {messages.map(message => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && <TypingIndicator />}
            {error && (
              <div className="flex justify-center">
                <p className="text-xs text-red-600 bg-red-50 border border-red-200
                              px-4 py-2 rounded-full">
                  {error}
                </p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ── Input ────────────────────────────────────────── */}
      <div className="flex-shrink-0 border-t border-slate-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <ChatInput
            onSendMessage={sendMessage}
            disabled={isLoading}
            placeholder="Ask about admission requirements, deadlines, documents…"
          />
          <p className="text-center text-xs text-slate-400 mt-2">
            Responses sourced from official admission documents · Always verify with the admissions office
          </p>
        </div>
      </div>
    </main>
  )
}
