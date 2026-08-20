'use client'

import { Message } from '@/app/chat/page'
import { User, Sparkles, BookOpen } from 'lucide-react'
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

export default function ChatMessage({ message }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 message-enter ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>

      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center shadow-sm
        ${isUser
          ? 'bg-neutral-900'
          : 'bg-neutral-800 border border-neutral-700'
        }`}>
        {isUser
          ? <User className="w-4 h-4 text-white" />
          : <Sparkles className="w-4 h-4 text-primary-400" />
        }
      </div>

      {/* Bubble + meta */}
      <div className={`flex flex-col gap-1.5 max-w-[78%] ${isUser ? 'items-end' : 'items-start'}`}>

        {/* Role label */}
        <p className="text-[10px] font-semibold text-neutral-400 uppercase tracking-widest px-1">
          {isUser ? 'You' : 'Assistant'}
        </p>

        {/* Message bubble */}
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? 'bg-neutral-900 text-white rounded-tr-sm'
            : 'bg-white text-neutral-800 rounded-tl-sm border border-neutral-200 border-l-2 border-l-primary-400 shadow-sm'
          }`}>
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p:      ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                ul:     ({ node, ...props }) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
                ol:     ({ node, ...props }) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
                li:     ({ node, ...props }) => <li className="text-neutral-700" {...props} />,
                strong: ({ node, ...props }) => <strong className="font-semibold text-neutral-900" {...props} />,
                em:     ({ node, ...props }) => <em className="italic text-neutral-600" {...props} />,
                code:   ({ node, ...props }) => (
                  <code className="bg-neutral-100 text-neutral-800 px-1.5 py-0.5 rounded text-xs font-mono" {...props} />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Metadata row */}
        <div className={`flex items-center gap-2 flex-wrap px-1 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="text-[10px] text-neutral-400">
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {!isUser && message.latency_ms && (
            <span className="text-[10px] text-neutral-400">{message.latency_ms}ms</span>
          )}
          {!isUser && message.llm_provider && (
            <span className="px-1.5 py-0.5 bg-neutral-100 text-neutral-500 rounded-full text-[10px] font-medium capitalize">
              {message.llm_provider}
            </span>
          )}
          {!isUser && message.language && (
            <span className="px-1.5 py-0.5 bg-primary-50 text-primary-600 rounded-full text-[10px] font-medium">
              {LANG_LABEL[message.language] ?? message.language}
            </span>
          )}
        </div>

        {/* Citations toggle */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="w-full">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="flex items-center gap-1.5 text-[11px] font-medium text-neutral-500
                         hover:text-primary-600 transition-colors px-1"
            >
              <BookOpen className="w-3 h-3" />
              {showCitations ? 'Hide' : 'Show'} {message.citations.length} source{message.citations.length !== 1 ? 's' : ''}
            </button>
            {showCitations && (
              <div className="mt-2 space-y-2">
                {message.citations.map(citation => (
                  <CitationCard key={citation.index} citation={citation} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
