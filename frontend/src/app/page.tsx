'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import ChatMessage from '@/components/ChatMessage'
import ChatInput from '@/components/ChatInput'
import TypingIndicator from '@/components/TypingIndicator'
import { BookOpen, Info, LayoutDashboard, LogIn, LogOut } from 'lucide-react'
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

export default function Home() {
  const { user, logout } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (query: string) => {
    if (!query.trim()) return

    setError(null)
    setIsLoading(true)

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const data = await api.chat({ query, top_k: 10, use_hybrid: true })

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        citations: data.citations,
        timestamp: new Date(),
        language: data.language,
        latency_ms: data.latency_ms,
        llm_provider: data.llm_provider,
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      console.error('Error sending message:', err)
      setError('Failed to get response. Please try again.')

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error while processing your request. Please try again later.",
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const suggestedQueries = [
    "What are the eligibility criteria for admission?",
    "Last date for form submission?",
    "Required documents for admission?",
    "Admission fee structure?",
  ]

  return (
    <main className="flex min-h-screen flex-col items-center justify-between">
      {/* Header */}
      <header className="w-full bg-primary-700 text-white py-4 px-6 shadow-lg">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="w-8 h-8" />
            <div>
              <h1 className="text-xl font-bold">Admission Policy Chatbot</h1>
              <p className="text-sm text-primary-200">University of Karachi</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => alert('This chatbot provides information based on official admission documents. Always verify with the admission office for critical decisions.')}
              className="p-2 hover:bg-primary-600 rounded-full transition-colors"
              title="About"
            >
              <Info className="w-5 h-5" />
            </button>

            {user?.role === 'admin' && (
              <Link
                href="/admin"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-600 hover:bg-primary-500
                           rounded-lg text-sm font-medium transition-colors"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
            )}

            {user ? (
              <button
                onClick={logout}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-600 hover:bg-primary-500
                           rounded-lg text-sm font-medium transition-colors"
                title={`Logged in as ${user.email}`}
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            ) : (
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-600 hover:bg-primary-500
                           rounded-lg text-sm font-medium transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Login
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="flex-1 w-full max-w-4xl mx-auto flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-20">
              <BookOpen className="w-16 h-16 text-primary-500 mb-4" />
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Welcome to Admission Policy Chatbot
              </h2>
              <p className="text-gray-600 mb-6 max-w-md">
                Ask me anything about University of Karachi admission policies,
                requirements, deadlines, and procedures.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
                {suggestedQueries.map((query, index) => (
                  <button
                    key={index}
                    onClick={() => sendMessage(query)}
                    className="px-4 py-2 bg-white border border-primary-300 text-primary-700
                             rounded-full text-sm hover:bg-primary-50 transition-colors
                             shadow-sm"
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                />
              ))}
              {isLoading && <TypingIndicator />}
              {error && (
                <div className="text-center text-red-600 bg-red-50 py-2 px-4 rounded-lg">
                  {error}
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="border-t bg-white p-4">
          <ChatInput
            onSendMessage={sendMessage}
            disabled={isLoading}
            placeholder="Ask about admission requirements, deadlines, documents..."
          />
          <p className="text-xs text-gray-500 text-center mt-2">
            Responses are generated from official admission documents.
            Verify critical information with the admission office.
          </p>
        </div>
      </div>
    </main>
  )
}
