'use client'

export default function TypingIndicator() {
  return (
    <div className="message-enter">
      <p className="mb-2 font-mono text-[11px] uppercase tracking-tighter2 text-primary-600">
        Assistant
      </p>
      <div className="flex justify-start">
        <div className="rounded-sm border border-neutral-200 border-l-2 border-l-primary-400 bg-neutral-50 px-4 py-4">
          <div className="flex items-center gap-1.5">
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-neutral-400" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-neutral-400" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-neutral-400" />
          </div>
        </div>
      </div>
    </div>
  )
}
