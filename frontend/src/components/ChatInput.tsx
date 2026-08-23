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
    <form onSubmit={handleSubmit}>
      <div
        className={`flex items-end gap-2 rounded-sm border bg-white transition-colors duration-150 ${
          disabled
            ? 'border-neutral-200 opacity-60'
            : 'border-neutral-300 focus-within:border-neutral-900'
        }`}
      >
        <textarea
          ref={textareaRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? 'Type your message…'}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent px-4 py-3.5 text-[15px] text-neutral-900
                     placeholder-neutral-400 focus:outline-none disabled:cursor-not-allowed"
          style={{ maxHeight: '180px' }}
        />
        <div className="flex-shrink-0 p-2">
          <button
            type="submit"
            disabled={!canSend}
            aria-label="Send message"
            className={`flex h-9 w-9 items-center justify-center rounded-sm transition-colors duration-150 ${
              canSend
                ? 'bg-primary-300 text-neutral-900 hover:bg-primary-400'
                : 'cursor-not-allowed bg-neutral-100 text-neutral-400'
            }`}
          >
            <ArrowUp className="h-4 w-4" strokeWidth={2.5} />
          </button>
        </div>
      </div>
    </form>
  )
}
