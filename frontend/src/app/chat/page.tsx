'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import ChatMessage from '@/components/ChatMessage'
import ChatInput from '@/components/ChatInput'
import TypingIndicator from '@/components/TypingIndicator'
import { GraduationCap, LayoutDashboard, LogOut, Sparkles } from 'lucide-react'
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

export default function ChatPage() {
  const { user, logout, isLoading: authLoading } = useAuth()
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const loggingOutRef = useRef(false)

  useEffect(() => {
    if (!authLoading && !user && !loggingOutRef.current) {
      router.replace('/login')
    }
  }, [user, authLoading, router])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (authLoading || !user) {
    return (
      <main className="h-screen flex items-center justify-center bg-neutral-50">
        <span className="w-8 h-8 border-2 border-neutral-300 border-t-neutral-900 rounded-full animate-spin" />
      </main>
    )
  }

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
    <main className="flex flex-col h-screen bg-neutral-50 overflow-hidden">

      {/* ── Header ──────────────────────────────────────── */}
      <header className="flex-shrink-0 bg-neutral-50 px-3 pt-3 animate-in-down">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-4
                        rounded-full bg-neutral-900 text-white px-5 py-2.5 shadow-lg
                        border border-white/5">
          {/* Brand */}
          <div className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded-full bg-neutral-800 border border-white/10
                            flex items-center justify-center transition-transform duration-300
                            group-hover:rotate-12 group-hover:scale-110">
              <GraduationCap className="w-4.5 h-4.5 text-primary-400" strokeWidth={2} />
            </div>
            <div>
              <p className="text-sm font-semibold leading-none text-white">Admission Assistant</p>
              <p className="text-xs text-neutral-400 leading-none mt-0.5">University of Karachi</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1.5">
            {user.role === 'admin' && (
              <Link
                href="/admin"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                           text-neutral-300 hover:text-white hover:bg-white/5 transition-all
                           hover:scale-105 active:scale-95"
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                Dashboard
              </Link>
            )}
            <button
              onClick={() => {
                loggingOutRef.current = true
                logout()
                router.push('/')
              }}
              title={`Signed in as ${user.email}`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                         text-neutral-300 hover:text-white hover:bg-white/5 transition-all
                         hover:scale-105 active:scale-95"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* ── Messages ─────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          /* Empty state */
          <div className="dot-grid h-full flex items-center justify-center px-4 py-8">
            <div className="dot-grid-dark relative w-full max-w-2xl overflow-hidden rounded-3xl
                            bg-[#111111] border border-white/5 shadow-xl
                            px-8 py-14 text-center">
              <div className="relative z-10 max-w-lg mx-auto">
                {/* Icon */}
                <div className="relative inline-flex mb-6 animate-in-pop">
                  <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 backdrop-blur
                                  flex items-center justify-center animate-float">
                    <Sparkles className="w-7 h-7 text-primary-400" />
                  </div>
                  <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-primary-400
                                   border-2 border-[#111111] animate-pulse" />
                </div>

                {/* Heading */}
                <h2 className="font-display font-bold text-5xl sm:text-6xl mb-3
                               gradient-text animate-in-up stagger-1">
                  Ask me anything
                </h2>
                <p className="text-sm text-neutral-400 mb-8 leading-relaxed animate-in-up stagger-2">
                  I have access to official University of Karachi admission documents.
                  Try asking about eligibility, fees, deadlines, or required materials.
                </p>

                {/* Suggestion chips */}
                <div className="flex flex-wrap gap-2 justify-center">
                  {SUGGESTIONS.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q)}
                      style={{ animationDelay: `${0.3 + i * 0.08}s` }}
                      className="animate-in-up px-4 py-2 bg-white/5 border border-white/10 text-neutral-200
                                 rounded-full text-xs font-medium hover:border-primary-300
                                 hover:text-neutral-900 hover:bg-primary-300
                                 transition-all duration-150 hover:scale-105 active:scale-95"
                    >
                      {q}
                    </button>
                  ))}
                </div>
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
      <div className="flex-shrink-0 border-t border-neutral-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <ChatInput
            onSendMessage={sendMessage}
            disabled={isLoading}
            placeholder="Ask about admission requirements, deadlines, documents…"
          />
          <p className="text-center text-xs text-neutral-400 mt-2">
            Responses sourced from official admission documents · Always verify with the admissions office
          </p>
        </div>
      </div>
    </main>
  )
}
