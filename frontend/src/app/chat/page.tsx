'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import ChatMessage from '@/components/ChatMessage'
import ChatInput from '@/components/ChatInput'
import TypingIndicator from '@/components/TypingIndicator'
import GenerativeGrid, { AMBIENT_FIELD } from '@/components/GenerativeGrid'
import { GraduationCap, LayoutDashboard, LogOut, ArrowUpRight } from 'lucide-react'
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

const NAV_ACTION =
  'flex items-center gap-1.5 rounded px-2.5 py-1.5 font-mono text-[12px] uppercase tracking-tighter2 ' +
  'text-muted transition-colors hover:bg-neutral-100 hover:text-neutral-900'

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
      <main className="flex h-screen items-center justify-center bg-neutral-50">
        <span className="h-8 w-8 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-900" />
      </main>
    )
  }

  const sendMessage = async (query: string) => {
    if (!query.trim() || isLoading) return
    setError(null)
    setIsLoading(true)

    const assistantId = (Date.now() + 1).toString()
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: 'user', content: query, timestamp: new Date() },
      { id: assistantId, role: 'assistant', content: '', timestamp: new Date() },
    ])

    const patch = (fields: Partial<Message>) =>
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantId ? { ...m, ...fields } : m)),
      )

    try {
      let streamed = ''
      await api.chatStream(
        { query, top_k: 10, use_hybrid: true },
        {
          onMeta: ({ language, citations }) => patch({ language, citations }),
          onToken: (text) => {
            streamed += text
            patch({ content: streamed })
          },
          onDone: ({ latency_ms, llm_provider }) => patch({ latency_ms, llm_provider }),
          onError: (message) => {
            setError(message)
            patch({ content: streamed || 'The response could not be completed. Please try again.' })
          },
        },
      )
      // Guard against a stream that closed without emitting any text.
      if (!streamed) {
        patch({
          content:
            "I'm sorry, I couldn't produce a response. Please try rephrasing your question.",
        })
      }
    } catch (err) {
      console.error('Error sending message:', err)
      setError('Failed to get a response. Please try again.')
      patch({
        content:
          "I'm sorry, I encountered an error while processing your request. Please try again later.",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-white">
      {/* ══ Nav rail — squared, matching the landing header ══ */}
      <header className="flex-shrink-0 border-b border-neutral-200 bg-white">
        <div className="mx-auto flex h-14 max-w-4xl items-center justify-between px-4 sm:px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-neutral-900">
              <GraduationCap className="h-4 w-4 text-primary-300" strokeWidth={2} />
            </span>
            <span className="display-lg text-[15px] leading-none text-neutral-900">
              Rehnuma
            </span>
          </Link>

          <div className="flex items-center gap-1">
            {user.role === 'admin' && (
              <Link href="/admin" className={NAV_ACTION}>
                <LayoutDashboard className="h-3.5 w-3.5" />
                <span className="max-sm:hidden">Dashboard</span>
              </Link>
            )}
            <button
              onClick={() => {
                loggingOutRef.current = true
                logout()
                router.push('/')
              }}
              title={`Signed in as ${user.email}`}
              className={NAV_ACTION}
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="max-sm:hidden">Sign out</span>
            </button>
          </div>
        </div>
      </header>

      {/* ══ Messages ═════════════════════════════════════════ */}
      <div className={`flex-1 ${messages.length === 0 ? 'overflow-hidden' : 'overflow-y-auto'}`}>
        {messages.length === 0 ? (
          // h-full, not min-h-full: the panel sizes itself to the pane rather
          // than overflowing it. Everything inside scales with vh so it stays
          // whole on short viewports instead of producing a scrollbar.
          <div className="flex h-full items-center justify-center py-[clamp(0.5rem,2vh,1.5rem)]">
            {/* Same max-w + padding as the header and composer, so the panel's
                edges land on the one shared content column */}
            <div className="mx-auto w-full max-w-4xl px-4 sm:px-6">
              <div className="relative max-h-full overflow-hidden rounded-sm bg-ink text-white">
                <GenerativeGrid
                  className="pointer-events-none absolute inset-0 h-full w-full"
                  {...AMBIENT_FIELD}
                />

                <div className="relative z-10 px-7 py-[clamp(1.25rem,4vh,3rem)] sm:px-12">
                  <p className="label-mono mb-[clamp(0.5rem,2vh,1.25rem)]">Ready when you are</p>
                  <h2 className="display-xl text-[min(clamp(1.9rem,4.6vw,3rem),5.5vh)]">
                    Ask me anything.
                  </h2>
                  <p
                    className="mt-[clamp(0.5rem,2vh,1.25rem)] max-w-md text-[15px] leading-[1.7]
                             text-neutral-400 [@media(max-height:620px)]:hidden"
                  >
                    Rehnuma has access to official University of Karachi admission documents. Try
                    asking about eligibility, fees, deadlines, or required materials.
                  </p>

                  {/* Suggestions as a numbered index, not pills */}
                  <div className="mt-[clamp(1rem,3.2vh,2.25rem)] border-t border-white/15">
                    {SUGGESTIONS.map((q, i) => (
                      <button
                        key={q}
                        onClick={() => sendMessage(q)}
                        className="group flex w-full items-center gap-4 border-b border-white/15 text-left
                                 py-[clamp(0.5rem,1.7vh,0.875rem)]
                                 transition-colors hover:bg-white/[0.04]"
                      >
                        <span className="font-mono text-[12px] tracking-tighter2 text-primary-300">
                          0{i + 1}
                        </span>
                        <span className="flex-1 text-[14px] text-neutral-300 transition-colors group-hover:text-white">
                          {q}
                        </span>
                        <ArrowUpRight
                          className="h-4 w-4 flex-shrink-0 text-muted transition-all
                                   group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-primary-300"
                        />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-4xl space-y-7 px-4 py-8 sm:px-6">
            {messages
              .filter((m) => !(m.role === 'assistant' && m.content === ''))
              .map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
            {isLoading && messages[messages.length - 1]?.content === '' && <TypingIndicator />}
            {error && (
              <div className="flex justify-center">
                <p
                  className="rounded-sm border border-red-200 bg-red-50 px-3 py-2
                              font-mono text-[12px] uppercase tracking-tighter2 text-red-600"
                >
                  {error}
                </p>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ══ Composer ═════════════════════════════════════════ */}
      <div className="flex-shrink-0 border-t border-neutral-200 bg-white">
        <div className="mx-auto max-w-4xl px-4 py-4 sm:px-6">
          <ChatInput
            onSendMessage={sendMessage}
            disabled={isLoading}
            placeholder="Ask about admission requirements, deadlines, documents…"
          />
          <p className="label-mono mt-3 text-center text-[11px]">
            Sourced from official documents · Always verify with the admissions office
          </p>
        </div>
      </div>
    </main>
  )
}
