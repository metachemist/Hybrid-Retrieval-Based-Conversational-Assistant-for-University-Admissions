'use client'

import { Message, Citation } from '@/app/page'
import { User, Bot, Clock } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CitationCard from './CitationCard'
import { useState } from 'react'

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 message-enter ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
        ${isUser ? 'bg-primary-600' : 'bg-green-600'}`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-2xl px-4 py-3 shadow-sm
          ${isUser 
            ? 'bg-primary-600 text-white rounded-tr-sm' 
            : 'bg-white text-gray-800 rounded-tl-sm border border-gray-200'
          }`}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
              ul: ({node, ...props}) => <ul className="list-disc list-inside mb-2" {...props} />,
              ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-2" {...props} />,
              li: ({node, ...props}) => <li className="mb-1" {...props} />,
              strong: ({node, ...props}) => <strong className="font-bold" {...props} />,
              em: ({node, ...props}) => <em className="italic" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Metadata */}
        <div className={`flex items-center gap-2 mt-1 text-xs text-gray-500
          ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {!isUser && message.latency_ms && (
            <span>{message.latency_ms}ms</span>
          )}
          {!isUser && message.llm_provider && (
            <span className="px-2 py-0.5 bg-gray-100 rounded-full capitalize">
              {message.llm_provider}
            </span>
          )}
          {!isUser && message.language && (
            <span className="px-2 py-0.5 bg-primary-100 text-primary-700 rounded-full capitalize">
              {message.language === 'ur' ? 'Roman Urdu' : message.language === 'mixed' ? 'Mixed' : 'English'}
            </span>
          )}
        </div>

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              📚 {showCitations ? 'Hide' : 'Show'} sources ({message.citations.length})
            </button>
            
            {showCitations && (
              <div className="mt-2 space-y-2">
                {message.citations.map((citation) => (
                  <CitationCard
                    key={citation.index}
                    citation={citation}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
