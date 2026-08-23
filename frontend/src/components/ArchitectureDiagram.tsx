/**
 * The five-layer system architecture from the thesis (Section 4.1), redrawn as
 * a responsive stack rather than the report's ASCII block. Each tier is a
 * bordered plate on the dark surface; connectors are hairlines rather than
 * arrowheads, so the diagram reads as a schematic and not as flowchart clip art.
 *
 * Deliberately static markup, not SVG: the layer contents are text that has to
 * reflow and stay selectable/searchable at mobile widths, which a fixed-viewBox
 * SVG would fight.
 */

/** Mono tag identifying a tier, sitting on the plate's top-left corner. */
function LayerTag({ children, tone = 'dark' }: { children: string; tone?: 'accent' | 'dark' }) {
  return (
    <span
      className={`inline-block px-2 py-[3px] font-mono text-[11px] font-medium tracking-tighter2 ${
        tone === 'accent' ? 'bg-primary-300 text-neutral-900' : 'bg-white/10 text-neutral-300'
      }`}
    >
      {children}
    </span>
  )
}

/** One horizontal tier of the stack. */
function Plate({
  tag,
  tone = 'dark',
  title,
  children,
  className = '',
}: {
  tag: string
  tone?: 'accent' | 'dark'
  title: string
  children?: React.ReactNode
  className?: string
}) {
  return (
    <div className={`border border-white/20 bg-white/[0.03] p-5 sm:p-6 ${className}`}>
      <LayerTag tone={tone}>{tag}</LayerTag>
      <p className="mt-3 text-[15px] font-medium text-white">{title}</p>
      {children}
    </div>
  )
}

/** Vertical hairline between tiers, with the edge protocol labelled. */
function Connector({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center py-3" aria-hidden="true">
      <span className="h-5 w-px bg-white/25" />
      {label && (
        <span className="my-1 font-mono text-[10px] tracking-tighter2 text-muted">{label}</span>
      )}
      <span className="h-5 w-px bg-white/25" />
    </div>
  )
}

/** Comma-separated detail line under a plate title. */
function Detail({ children }: { children: React.ReactNode }) {
  return <p className="mt-2 font-mono text-[12px] leading-[1.75] tracking-tighter2 text-neutral-400">{children}</p>
}

export default function ArchitectureDiagram() {
  return (
    <div className="mx-auto max-w-3xl">
      <Plate tag="01 · CLIENT" tone="accent" title="Next.js 14 (TypeScript, Tailwind)">
        <Detail>chat UI · auth pages · admin analytics dashboard</Detail>
      </Plate>

      <Connector label="REST / fetch" />

      <Plate tag="02 · API" title="FastAPI (Python 3.11+)">
        <Detail>
          /api/chat · /api/documents · /api/auth · /api/admin · /api/health
          <br />
          JWT optional on /chat, required on /admin and document writes
        </Detail>
      </Plate>

      <Connector />

      {/* Three services fan out in parallel from the API layer */}
      <div className="grid gap-3 sm:grid-cols-3">
        <Plate tag="03 · RETRIEVAL" title="Hybrid search">
          <Detail>
            PostgreSQL full-text
            <br />
            + pgvector cosine
            <br />
            fused by RRF (k=60)
          </Detail>
        </Plate>
        <Plate tag="04 · GENERATION" title="Cited answers">
          <Detail>
            RAG prompt builder
            <br />
            provider chain: OpenAI,
            <br />
            Gemini, Claude, Ollama
          </Detail>
        </Plate>
        <Plate tag="05 · ROMAN URDU" title="Language layer">
          <Detail>
            LanguageDetector
            <br />
            + Normalizer
            <br />
            spelling, not translation
          </Detail>
        </Plate>
      </div>

      <Connector />

      <Plate tag="06 · DATA" title="Neon PostgreSQL + pgvector">
        <Detail>
          documents · chunks (768-dim embedding) · users · query_logs
        </Detail>
      </Plate>

      <Connector label="OFFLINE" />

      <Plate tag="07 · INGESTION" title="Document pipeline">
        <Detail>
          PyMuPDF parse, clean, section-split, table-aware chunk, embed, index
        </Detail>
      </Plate>
    </div>
  )
}
