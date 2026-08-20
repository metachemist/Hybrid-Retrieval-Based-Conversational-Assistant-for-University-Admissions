'use client'

import { Citation } from '@/app/chat/page'
import { FileText, ChevronDown, ChevronUp, Hash } from 'lucide-react'
import { useState } from 'react'

interface CitationCardProps {
  citation: Citation
}

export default function CitationCard({ citation }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div
      className={`rounded-xl border text-xs cursor-pointer transition-all duration-150
        ${isExpanded
          ? 'bg-primary-50 border-primary-200'
          : 'bg-neutral-50 border-neutral-200 hover:border-neutral-300 hover:bg-white'
        }`}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      {/* Header row */}
      <div className="flex items-start gap-2.5 px-3.5 py-3">
        <div className={`flex-shrink-0 w-6 h-6 rounded-lg flex items-center justify-center mt-0.5
          ${isExpanded ? 'bg-primary-200' : 'bg-neutral-200'}`}>
          <FileText className={`w-3 h-3 ${isExpanded ? 'text-primary-700' : 'text-neutral-500'}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className={`font-semibold leading-tight truncate ${isExpanded ? 'text-primary-800' : 'text-neutral-700'}`}>
              {citation.document_title}
            </p>
            {isExpanded
              ? <ChevronUp className="w-3.5 h-3.5 text-neutral-400 flex-shrink-0 mt-0.5" />
              : <ChevronDown className="w-3.5 h-3.5 text-neutral-400 flex-shrink-0 mt-0.5" />}
          </div>

          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-white/70 rounded-md
                             border border-neutral-200/80 text-neutral-500">
              <Hash className="w-2.5 h-2.5" />
              Ref {citation.index}
            </span>
            {citation.section_header && citation.section_header !== 'N/A' && (
              <span className="text-neutral-400 truncate max-w-[160px]">
                § {citation.section_header}
              </span>
            )}
            {citation.page_start > 0 && (
              <span className="text-neutral-400">
                p.{citation.page_start}
                {citation.page_end && citation.page_end !== citation.page_start
                  ? `–${citation.page_end}`
                  : ''}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Expanded preview */}
      {isExpanded && (
        <div className="px-3.5 pb-3.5 pt-0.5 border-t border-primary-200/60">
          <p className="text-neutral-600 italic leading-relaxed line-clamp-4">
            &ldquo;{citation.content_preview}&rdquo;
          </p>
        </div>
      )}
    </div>
  )
}
