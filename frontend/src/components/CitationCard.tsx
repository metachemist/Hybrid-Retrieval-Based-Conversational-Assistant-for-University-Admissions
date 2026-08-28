'use client'

import { Citation } from '@/app/chat/page'
import { ChevronDown } from 'lucide-react'
import { useState } from 'react'

interface CitationCardProps {
  citation: Citation
}

/**
 * A retrieved source rendered as one of the reference's labeled technical
 * panels: mono ref tag, squared frame, expandable excerpt.
 */
export default function CitationCard({ citation }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const pages =
    citation.page_start > 0
      ? `p.${citation.page_start}${
          citation.page_end && citation.page_end !== citation.page_start
            ? `-${citation.page_end}`
            : ''
        }`
      : null
  const section =
    citation.section_header && citation.section_header !== 'N/A' ? citation.section_header : null

  return (
    <div
      className={`rounded-sm border transition-colors ${
        isExpanded
          ? 'border-primary-400 bg-primary-50'
          : 'border-neutral-200 bg-white hover:border-neutral-300'
      }`}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
        className="flex w-full items-start gap-3 px-3 py-2.5 text-left"
      >
        {/* Ref tag */}
        <span
          className={`mt-px flex-shrink-0 rounded-sm px-1.5 py-0.5 font-mono text-[10px] font-medium uppercase tracking-tighter2 ${
            isExpanded ? 'bg-primary-300 text-neutral-900' : 'bg-neutral-900 text-neutral-200'
          }`}
        >
          REF {String(citation.index).padStart(2, '0')}
        </span>

        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13px] font-medium text-neutral-800">
            {citation.document_title}
          </span>
          {(section || pages) && (
            <span className="mt-1 flex flex-wrap items-center gap-x-2.5 font-mono text-[11px] tracking-tighter2 text-muted">
              {section && <span className="truncate">§ {section}</span>}
              {pages && <span>{pages}</span>}
            </span>
          )}
        </span>

        <ChevronDown
          className={`mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-neutral-400 transition-transform duration-200 ${
            isExpanded ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isExpanded && (
        <div className="border-t border-primary-200 px-3 py-2.5">
          <p className="line-clamp-4 text-[13px] italic leading-[1.7] text-neutral-600">
            &ldquo;{citation.content_preview}&rdquo;
          </p>
        </div>
      )}
    </div>
  )
}
