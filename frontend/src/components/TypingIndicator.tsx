'use client'

import { Sparkles } from 'lucide-react'

export default function TypingIndicator() {
  return (
    <div className="flex gap-3 message-enter">
      {/* Avatar matches assistant style */}
      <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-slate-800 border border-slate-700
                      flex items-center justify-center">
        <Sparkles className="w-4 h-4 text-amber-400" />
      </div>

      <div className="flex flex-col gap-1.5">
        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest px-1">
          Assistant
        </p>
        <div className="bg-white border border-slate-200 border-l-2 border-l-primary-400
                        rounded-2xl rounded-tl-sm px-4 py-3.5 shadow-sm">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot" />
            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot" />
            <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot" />
          </div>
        </div>
      </div>
    </div>
  )
}
