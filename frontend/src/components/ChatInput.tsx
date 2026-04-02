'use client'

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled: boolean
  placeholder?: string
}

export default function ChatInput({ onSendMessage, disabled, placeholder }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !disabled) {
      onSendMessage(input.trim())
      setInput('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 items-end">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || 'Type your message...'}
          disabled={disabled}
          rows={1}
          className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-xl 
                   focus:outline-none focus:ring-2 focus:ring-primary-500 
                   focus:border-transparent resize-none
                   disabled:bg-gray-100 disabled:cursor-not-allowed
                   transition-all duration-200"
          style={{ maxHeight: '200px' }}
        />
      </div>
      
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className="flex-shrink-0 p-3 bg-primary-600 text-white rounded-xl
                 hover:bg-primary-700 disabled:bg-gray-300 
                 disabled:cursor-not-allowed transition-colors
                 flex items-center justify-center"
      >
        <Send className="w-5 h-5" />
      </button>
    </form>
  )
}
