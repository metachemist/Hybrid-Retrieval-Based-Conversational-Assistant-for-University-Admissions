'use client'

import { Message } from '@/app/chat/page'
import { BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CitationCard from './CitationCard'
import { useState } from 'react'

interface ChatMessageProps {
  message: Message
}

const LANG_LABEL: Record<string, string> = {
  en: 'English',
  ur: 'Roman Urdu',
  mixed: 'Mixed',
}

/** Small mono chip used across the metadata row. */
function MetaChip({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-sm bg-neutral-100 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-tighter2 text-neutral-500">
      {children}
    </span>
  )
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className="message-enter">
      {/* Role label — mono, negative tracking, sitting above the block */}
      <p
        className={`mb-2 font-mono text-[11px] uppercase tracking-tighter2 ${
          isUser ? 'text-right text-neutral-400' : 'text-primary-600'
        }`}
      >
        {isUser ? 'You' : 'Assistant'}
      </p>

      <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
        <div className={`max-w-[85%] ${isUser ? 'items-end' : 'w-full items-start'}`}>
          {/* Body */}
          <div
            className={`rounded-sm px-4 py-3 text-[15px] leading-[1.7] ${
              isUser
                ? 'bg-neutral-900 text-white'
                : 'border border-neutral-200 border-l-2 border-l-primary-400 bg-neutral-50 text-neutral-800'
            }`}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({ node, ...props }) => <p className="mb-3 last:mb-0" {...props} />,
                  ul: ({ node, ...props }) => (
                    <ul className="mb-3 list-inside list-disc space-y-1.5 last:mb-0" {...props} />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol className="mb-3 list-inside list-decimal space-y-1.5 last:mb-0" {...props} />
                  ),
                  li: ({ node, ...props }) => <li className="text-neutral-700" {...props} />,
                  strong: ({ node, ...props }) => (
                    <strong className="font-semibold text-neutral-900" {...props} />
                  ),
                  em: ({ node, ...props }) => <em className="italic text-neutral-600" {...props} />,
                  code: ({ node, ...props }) => (
                    <code
                      className="rounded-sm bg-neutral-200/70 px-1.5 py-0.5 font-mono text-[13px] text-neutral-800"
                      {...props}
                    />
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {/* Metadata */}
          <div
            className={`mt-2 flex flex-wrap items-center gap-1.5 ${
              isUser ? 'justify-end' : 'justify-start'
            }`}
          >
            <span className="font-mono text-[10px] uppercase tracking-tighter2 text-neutral-400">
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
            {!isUser && message.latency_ms && <MetaChip>{message.latency_ms}ms</MetaChip>}
            {!isUser && message.llm_provider && <MetaChip>{message.llm_provider}</MetaChip>}
            {!isUser && message.language && (
              <span className="rounded-sm bg-primary-100 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-tighter2 text-primary-700">
                {LANG_LABEL[message.language] ?? message.language}
              </span>
            )}
          </div>

          {/* Sources */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="mt-3">
              <button
                onClick={() => setShowCitations(!showCitations)}
                className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-tighter2
                           text-muted transition-colors hover:text-primary-600"
              >
                <BookOpen className="h-3 w-3" />
                {showCitations ? 'Hide' : 'Show'} {message.citations.length} source
                {message.citations.length !== 1 ? 's' : ''}
              </button>
              {showCitations && (
                <div className="mt-3 space-y-2">
                  {message.citations.map(citation => (
                    <CitationCard key={citation.index} citation={citation} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
