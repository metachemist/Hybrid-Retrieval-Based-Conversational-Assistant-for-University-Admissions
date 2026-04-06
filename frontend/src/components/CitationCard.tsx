'use client'

import { Citation } from '@/app/page'
import { FileText, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface CitationCardProps {
  citation: Citation
}

export default function CitationCard({ citation }: CitationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div 
      className="bg-gray-50 border border-gray-200 rounded-lg p-3 hover:border-primary-300 transition-colors cursor-pointer"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="flex items-start gap-2">
        <FileText className="w-4 h-4 text-gray-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-700">
              [{citation.index}] {citation.document_title}
            </span>
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </div>
          
          <div className="text-xs text-gray-500 mt-1">
            {citation.section_header !== 'N/A' && (
              <span>Section: {citation.section_header}</span>
            )}
            {citation.page_start > 0 && (
              <span className="ml-2">
                Page {citation.page_start}
                {citation.page_end && citation.page_end !== citation.page_start 
                  ? `-${citation.page_end}` 
                  : ''}
              </span>
            )}
          </div>

          {isExpanded && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="text-xs text-gray-600 italic">
                &quot;{citation.content_preview}&quot;
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
