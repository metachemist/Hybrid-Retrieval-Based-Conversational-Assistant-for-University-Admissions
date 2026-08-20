'use client'

import { useState, useRef, useEffect } from 'react'
import { ArrowUp } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled: boolean
  placeholder?: string
}

export default function ChatInput({ onSendMessage, disabled, placeholder }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`
    }
  }, [input])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const canSend = input.trim().length > 0 && !disabled

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className={`flex items-end gap-2 rounded-3xl border transition-all duration-150 bg-neutral-50
        ${disabled
          ? 'border-neutral-200 opacity-60'
          : 'border-neutral-300 focus-within:border-primary-400 focus-within:ring-2 focus-within:ring-primary-500/10 focus-within:bg-white'
        }`}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? 'Type your message…'}
          disabled={disabled}
          rows={1}
          className="flex-1 bg-transparent px-4 py-3.5 text-sm text-neutral-900
                     placeholder-neutral-400 resize-none focus:outline-none
                     disabled:cursor-not-allowed"
          style={{ maxHeight: '180px' }}
        />
        <div className="flex-shrink-0 p-2">
          <button
            type="submit"
            disabled={!canSend}
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-150 ${
              canSend
                ? 'bg-neutral-900 hover:bg-neutral-700 text-white shadow-sm hover:scale-110 active:scale-90'
                : 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
            }`}
          >
            <ArrowUp className={`w-4 h-4 transition-transform ${canSend ? '-translate-y-px' : ''}`} strokeWidth={2.5} />
          </button>
        </div>
      </div>
    </form>
  )
}
