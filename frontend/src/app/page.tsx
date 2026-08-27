'use client'

import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import ScrambleCodeBlock from '@/components/ScrambleCodeBlock'
import GenerativeGrid, { AMBIENT_FIELD } from '@/components/GenerativeGrid'
import SlideButton from '@/components/SlideButton'
import CursorSquare from '@/components/CursorSquare'
import Reveal from '@/components/Reveal'
import ArchitectureDiagram from '@/components/ArchitectureDiagram'
import EvaluationResults from '@/components/EvaluationResults'

// Measured figures, not marketing rounding: every value below is reported in
// THESIS_REPORT.md Ch. 6 and must be updated with it if the evaluation re-runs.
const STATS = [
  { value: '100%', label: 'Citation markers valid' },
  { value: '76.3%', label: 'Recall@5, hybrid retrieval' },
  { value: '3.8s', label: 'Average response time' },
  { value: '41', label: 'Benchmark queries evaluated' },
]

const SCOPE_INCLUDED = [
  'Official undergraduate admission prospectuses, fee schedules and merit notices',
  'Eligibility, required documents, fees, deadlines and merit procedure',
  'Questions asked in English, Roman Urdu, or a mix of both',
  'Every answer linked back to the source document, section and page',
]

const SCOPE_EXCLUDED = [
  'Predicting your admission chances or where a merit list will close',
  'Processing, filling or submitting an admission application',
  'Storing sensitive personal applicant data',
  'Replacing the admission office as the deciding authority',
]

const FEATURES = [
  {
    n: '01',
    title: 'Hybrid retrieval',
    body: 'Keyword search (BM25) and semantic vector search run together over official admission documents, then fuse into one ranking. Answers are grounded in source text, not guesses.',
  },
  {
    n: '02',
    title: 'English + Roman Urdu',
    body: 'Ask in either language and get a response in kind, built for how students in Karachi actually type rather than for how a form expects them to.',
  },
  {
    n: '03',
    title: 'Cited sources',
    body: 'Every answer links back to the exact document, section and page it came from, so you can verify it yourself instead of taking it on trust.',
  },
]

const STEPS = [
  {
    n: '01',
    title: 'Ask your question',
    body: 'Eligibility, fees, deadlines, required documents. Type it the way you would ask a friend.',
  },
  {
    n: '02',
    title: 'We search the documents',
    body: 'Rehnuma retrieves the most relevant passages from official University of Karachi admission policies.',
  },
  {
    n: '03',
    title: 'Get a cited answer',
    body: 'A concise, accurate response with links to the exact source material behind it.',
  },
]

/** Thin frame with corner "handles" — the reference's selection-marquee motif. */
function CornerFrame({
  children,
  className = '',
  handle = 'white',
  style,
}: {
  children: React.ReactNode
  className?: string
  handle?: 'white' | 'accent'
  style?: React.CSSProperties
}) {
  return (
    <div className={`relative border border-white/20 ${className}`} style={style}>
      {[
        'top-0 left-0 -translate-x-1/2 -translate-y-1/2',
        'top-0 right-0 translate-x-1/2 -translate-y-1/2',
        'bottom-0 left-0 -translate-x-1/2 translate-y-1/2',
        'bottom-0 right-0 translate-x-1/2 translate-y-1/2',
      ].map(pos => (
        <span
          key={pos}
          className={`absolute ${pos} w-[7px] h-[7px] ${
            handle === 'accent' ? 'bg-primary-300' : 'bg-white'
          }`}
        />
      ))}
      {children}
    </div>
  )
}

/** Mono file-tag that sits above a panel's top-left corner. */
function PanelTag({ children, tone = 'accent' }: { children: string; tone?: 'accent' | 'dark' }) {
  return (
    <span
      className={`inline-block px-2 py-[3px] font-mono text-[11px] font-medium tracking-tighter2 ${
        tone === 'accent' ? 'bg-primary-300 text-neutral-900' : 'bg-black text-neutral-300'
      }`}
    >
      {children}
    </span>
  )
}

/**
 * Where each hero panel sits and how large it is.
 *
 * Every panel is absolutely positioned inside the stage, so these are the only
 * values that place it: move one and nothing else shifts. Tweak them freely.
 *
 *   top     px from the top of the stage. Positions the panel's file tag; the
 *           bordered frame starts roughly 27px below that (tag + 6px gap).
 *   height  px, the frame only -- it does not include the tag above it.
 *   left    % of stage width, so the collage stays fluid between lg and xl.
 *   width   % of stage width.
 *
 * STAGE_HEIGHT has to clear the lowest panel (its top + ~27 + its height), or
 * the hero column crops it.
 */
const STAGE_HEIGHT = 392

const HERO_PANELS = {
  retrieve: { top: 0, left: '0%', width: '100%', height: 180 },
  index: { top: 211, left: '0%', width: '61%', height: 150 },
  rank: { top: 211, left: '65%', width: '35%', height: 120 },
}

type PanelPlacement = { top: number; left: string; width: string; height: number }

/** One free-floating panel: file tag, bordered frame, and whatever fills it. */
function FloatingPanel({
  place,
  tag,
  tone = 'accent',
  handle = 'white',
  frameClassName = '',
  children,
}: {
  place: PanelPlacement
  tag: string
  tone?: 'accent' | 'dark'
  handle?: 'white' | 'accent'
  /** Styling for the frame itself: background, padding, overflow, layout. */
  frameClassName?: string
  children: React.ReactNode
}) {
  return (
    <div className="absolute" style={{ top: place.top, left: place.left, width: place.width }}>
      <PanelTag tone={tone}>{tag}</PanelTag>
      <CornerFrame
        handle={handle}
        className={`mt-1.5 ${frameClassName}`}
        style={{ height: place.height }}
      >
        {children}
      </CornerFrame>
    </div>
  )
}

export default function LandingPage() {
  return (
    <main className="bg-white">
      <CursorSquare />

      {/* ══ Dark block: nav + hero ═══════════════════════════ */}
      <div className="grid-lines-dark relative overflow-hidden bg-ink text-white">
        <GenerativeGrid
          className="absolute inset-0 h-full w-full pointer-events-none"
          {...AMBIENT_FIELD}
        />

        {/* Nav rail */}
        <header className="relative z-10 border-b border-white/10">
          <div className="mx-auto flex h-14 max-w-shell items-center justify-between px-6 sm:px-10">
            <nav className="flex items-center gap-7 text-[13px]">
              <span className="border-b-2 border-white pb-[3px] font-medium text-white">
                Rehnuma
              </span>
              <Link href="#how" className="text-muted transition-colors hover:text-white">
                How it works
              </Link>
              <Link
                href="#architecture"
                className="text-muted transition-colors hover:text-white max-sm:hidden"
              >
                Architecture
              </Link>
              <Link href="#results" className="text-muted transition-colors hover:text-white">
                Results
              </Link>
            </nav>
            <Link
              href="/login"
              className="rounded bg-primary-300 px-4 py-1.5 text-[13px] font-medium text-neutral-900
                         transition-colors hover:bg-primary-200"
            >
              Sign in
            </Link>
          </div>
        </header>

        <section className="relative z-10 mx-auto max-w-shell px-6 pb-28 pt-14 sm:px-10 sm:pb-36 sm:pt-20">
          {/* Wordmark + session meta */}
          <Reveal className="mb-16 flex flex-col gap-6 sm:mb-24 sm:flex-row sm:items-start sm:justify-between">
            <p className="display-lg text-[26px] sm:text-[30px]">Rehnuma</p>
            <div className="flex items-start gap-2.5 text-[15px] leading-relaxed text-neutral-300">
              <span className="mt-[7px] h-2 w-2 shrink-0 bg-primary-300" />
              <span>
                Admissions 2026
                <br />
                University of Karachi
              </span>
            </div>
          </Reveal>

          <div className="grid items-start gap-14 lg:grid-cols-[1.22fr_0.78fr] lg:gap-12">
            {/* ── Headline column ── */}
            <div>
              <Reveal delay={30}>
                <h1 className="display-xl text-[clamp(2.2rem,4.6vw,4rem)]">
                  Stop asking relatives.
                  <br />
                  <span className="text-primary-300">Ask Rehnuma.</span>
                </h1>
              </Reveal>

              <Reveal delay={140}>
                <p className="mt-9 max-w-[30rem] text-[17px] leading-[1.65] text-neutral-400">
                  Instant, cited answers about admissions: eligibility, fees, deadlines and
                  required documents, pulled straight from official policy documents.
                </p>
              </Reveal>

              <Reveal delay={220}>
                <div className="mt-11 flex flex-col items-stretch gap-3 sm:flex-row sm:items-start">
                  <SlideButton href="/login" icon={<ArrowRight className="h-4 w-4" />}>
                    Take me to Rehnuma
                  </SlideButton>
                  <SlideButton href="/register" variant="outline">
                    Create an account
                  </SlideButton>
                </div>
              </Reveal>
            </div>

            {/* ── Generative panel collage ──
                Three independent panels on one stage. Each is placed solely by
                its entry in HERO_PANELS above, so any of them can be moved or
                resized without disturbing the other two. ── */}
            <Reveal delay={180} className="hidden lg:block">
              <div className="relative" style={{ height: STAGE_HEIGHT }}>
                <FloatingPanel
                  place={HERO_PANELS.retrieve}
                  tag="RETRIEVE.PY"
                  frameClassName="overflow-hidden rounded-sm bg-[#0b0b0b] p-7"
                >
                  <ScrambleCodeBlock className="text-[13px] leading-[1.7]" />
                </FloatingPanel>

                <FloatingPanel
                  place={HERO_PANELS.index}
                  tag="INDEX.VEC"
                  tone="dark"
                  frameClassName="overflow-hidden rounded-sm bg-black"
                >
                  <GenerativeGrid
                    className="h-full w-full"
                    cell={2}
                    fontSize={8}
                    maxOpacity={0.75}
                    minOpacity={0.25}
                    intervalMs={50}
                  />
                </FloatingPanel>

                <FloatingPanel
                  place={HERO_PANELS.rank}
                  tag="RANK.OUT"
                  tone="dark"
                  handle="accent"
                  frameClassName="flex items-end rounded-sm bg-primary-300 p-3"
                >
                  <span className="font-mono text-[11px] leading-tight tracking-tighter2 text-neutral-900">
                    top_k = 5
                    <br />
                    rrf_k = 60
                  </span>
                </FloatingPanel>
              </div>
            </Reveal>
          </div>
        </section>
      </div>

      {/* ══ Dark inset: the problem ═══════════════════════════ */}
      <section id="problem" className="px-4 pb-24 pt-16 sm:px-8 sm:pt-24">
        <div className="dot-grid-dark relative overflow-hidden rounded-sm bg-ink text-white">
          <div className="mx-auto max-w-shell px-6 py-24 sm:px-10 sm:py-32">
            <div className="grid items-start gap-12 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
              <Reveal>
                <p className="label-mono mb-7">The problem</p>
                <h2 className="display-xl max-w-[14ch] text-[clamp(2.4rem,5.4vw,4.6rem)]">
                  Even phoppo can get it wrong.
                </h2>
                <p className="mt-8 max-w-[34rem] text-[17px] leading-[1.7] text-neutral-400">
                  Every family has one — the mamu, phoppo or chacha who&apos;s &quot;been through
                  this&quot; and always has an answer, whether or not it&apos;s still true.
                </p>
                <p className="mt-4 max-w-[34rem] text-[17px] leading-[1.7] text-neutral-400">
                  The real one is sitting in the prospectus the whole time. It&apos;s just long,
                  scattered, and hard to search — so the question passes through four or five
                  people before it&apos;s answered, and by then it&apos;s often wrong.
                </p>
              </Reveal>

              <Reveal delay={140}>
                <div className="mx-auto max-w-sm space-y-3">
                  {[
                    ['MAMU', '5,000 hoga, form ke sath jama karado'],
                    ['PHOPPO', 'Fee to hamesha se yehi tha, 8 hazar ke qareeb'],
                    ['CHACHA', '10,000 se zyada nahi hoga, main dekh k aya tha'],
                  ].map(([who, quote]) => (
                    <div key={who} className="flex flex-col items-start gap-1.5">
                      <span className="ml-1 font-mono text-[10px] tracking-tighter2 text-neutral-500">
                        {who}
                      </span>
                      <div className="max-w-[82%] rounded-2xl rounded-tl-sm bg-white/10 px-4 py-2.5 text-[14px] leading-[1.5] text-neutral-300">
                        {quote}
                      </div>
                    </div>
                  ))}

                  <div className="flex flex-col items-end gap-1.5 pt-3">
                    <span className="mr-1 font-mono text-[10px] tracking-tighter2 text-primary-300">
                      REHNUMA
                    </span>
                    <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-primary-300 px-4 py-2.5 text-[14px] leading-[1.5] text-neutral-900">
                      Registration / Admission Fee is Rs. 12,000, one-time.
                    </div>
                    <span className="mr-1 font-mono text-[11px] tracking-tighter2 text-neutral-500">
                      KUBS Prospectus 2024 · Fee Structure · p.46
                    </span>
                  </div>
                </div>
              </Reveal>
            </div>
          </div>
        </div>
      </section>

      {/* ══ Light block: statement + stats ═══════════════════ */}
      <section className="mx-auto max-w-shell px-6 py-28 sm:px-10 sm:py-36">
        <div className="grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:gap-20">
          <Reveal>
            <p className="label-mono mb-7">Why it&apos;s different</p>
            <h2 className="display-lg max-w-[16ch] text-[clamp(2rem,4.2vw,3.4rem)] text-neutral-900">
              Built to be checked, not just trusted.
            </h2>
          </Reveal>

          <Reveal delay={120} className="lg:pt-16">
            <p className="text-[17px] leading-[1.7] text-neutral-500">
              Admission rules change, and a wrong answer costs a student a deadline. So every
              response is assembled from passages retrieved out of the official documents at the
              moment you ask, never from pre-written scripts, and every claim carries a link back
              to where it came from.
            </p>
            <div className="mt-9">
              <SlideButton href="/login" icon={<ArrowRight className="h-4 w-4" />}>
                Ask a question
              </SlideButton>
            </div>
          </Reveal>
        </div>

        {/* Stat row — oversized figures, mono labels */}
        <div className="mt-28 grid grid-cols-2 gap-x-8 gap-y-14 sm:mt-36 lg:grid-cols-4">
          {STATS.map(({ value, label }, i) => (
            <Reveal key={label} delay={i * 90}>
              <p className="display-lg text-[clamp(3rem,6.5vw,5.6rem)] text-neutral-900">{value}</p>
              <p className="label-mono mt-4">{label}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ══ Dark inset block: how it works ═══════════════════ */}
      <section id="how" className="px-4 pb-24 sm:px-8">
        <div className="dot-grid-dark relative overflow-hidden rounded-sm bg-ink text-white">
          <div className="mx-auto max-w-shell px-6 py-24 sm:px-10 sm:py-32">
            <Reveal>
              <p className="label-mono mb-7">How Rehnuma works</p>
              <h2 className="display-xl max-w-[14ch] text-[clamp(2.4rem,5.4vw,4.6rem)]">
                Everyone starts from the source.
              </h2>
              <p className="mt-8 max-w-[38rem] text-[17px] leading-[1.7] text-neutral-400">
                No pre-written answers and no canned FAQ. Each question runs a fresh retrieval pass
                over the admission policy documents, and what comes back is what you get.
              </p>
            </Reveal>

            <div className="mt-20 grid gap-y-12 border-t border-white/20 pt-10 sm:grid-cols-3 sm:gap-x-10">
              {STEPS.map(({ n, title, body }, i) => (
                <Reveal
                  key={n}
                  delay={i * 110}
                  className={i > 0 ? 'sm:border-l sm:border-white/20 sm:pl-10' : ''}
                >
                  <p className="font-mono text-[13px] tracking-tighter2 text-primary-300">{n}</p>
                  <h3 className="mt-5 text-lg font-medium">{title}</h3>
                  <p className="mt-3 text-[15px] leading-[1.7] text-neutral-400">{body}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══ Light block: feature detail ══════════════════════ */}
      <section className="mx-auto max-w-shell px-6 pb-28 sm:px-10 sm:pb-36">
        <Reveal>
          <p className="label-mono mb-7">What you get</p>
        </Reveal>
        <div className="grid gap-y-14 border-t border-neutral-200 pt-12 sm:grid-cols-3 sm:gap-x-10">
          {FEATURES.map(({ n, title, body }, i) => (
            <Reveal
              key={n}
              delay={i * 110}
              className={i > 0 ? 'sm:border-l sm:border-neutral-200 sm:pl-10' : ''}
            >
              <p className="font-mono text-[13px] tracking-tighter2 text-primary-600">{n}</p>
              <h3 className="mt-5 text-lg font-medium text-neutral-900">{title}</h3>
              <p className="mt-3 text-[15px] leading-[1.7] text-neutral-500">{body}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ══ Dark inset: architecture ═════════════════════════ */}
      <section id="architecture" className="px-4 pb-24 sm:px-8">
        <div className="dot-grid-dark relative overflow-hidden rounded-sm bg-ink text-white">
          <div className="mx-auto max-w-shell px-6 py-24 sm:px-10 sm:py-32">
            <Reveal>
              <p className="label-mono mb-7">System architecture</p>
              <h2 className="display-xl max-w-[15ch] text-[clamp(2.4rem,5.4vw,4.6rem)]">
                Five layers, one answer.
              </h2>
              <p className="mt-8 max-w-[38rem] text-[17px] leading-[1.7] text-neutral-400">
                Retrieval, generation and language handling are separate services behind one API,
                so a weak result in any one of them can be measured and replaced without touching
                the others. Documents are parsed, chunked and indexed offline, ahead of any query.
              </p>
            </Reveal>

            <Reveal delay={120} className="mt-20">
              <ArchitectureDiagram />
            </Reveal>
          </div>
        </div>
      </section>

      {/* ══ Light block: Roman Urdu ══════════════════════════ */}
      <section className="mx-auto max-w-shell px-6 pb-28 sm:px-10 sm:pb-36">
        <div className="grid gap-12 lg:grid-cols-[0.95fr_1.05fr] lg:gap-20">
          <Reveal>
            <p className="label-mono mb-7">Multilingual by design</p>
            <h2 className="display-lg max-w-[13ch] text-[clamp(2rem,4.2vw,3.4rem)] text-neutral-900">
              Ask it how you actually type.
            </h2>
            <p className="mt-9 max-w-[32rem] text-[17px] leading-[1.7] text-neutral-500">
              Roman Urdu has no standard spelling. The same word turns up three or four ways in the
              same inbox. Rehnuma standardises the spelling and then searches, rather than
              translating your question into English first, so nothing is lost in a translation step
              before the search even starts.
            </p>
          </Reveal>

          <Reveal delay={120}>
            <div className="rounded-sm bg-ink p-6 text-white sm:p-8">
              <p className="label-mono">Query as typed</p>
              <p className="mt-4 font-mono text-[14px] leading-[1.7] tracking-tighter2 text-primary-300">
                admission ke liye kya documents chahiye?
              </p>

              <div className="mt-8 border-t border-white/15 pt-8">
                <p className="label-mono">Spelling normalised</p>
                <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2 font-mono text-[14px] tracking-tighter2">
                  <span className="text-neutral-500 line-through">chaiye</span>
                  <span className="text-neutral-500 line-through">chiye</span>
                  <span className="text-muted" aria-hidden="true">
                    &rarr;
                  </span>
                  <span className="text-white">chahiye</span>
                </div>
              </div>

              <div className="mt-8 border-t border-white/15 pt-8">
                <p className="label-mono">Answer returned in</p>
                <p className="mt-4 text-[15px] text-white">Roman Urdu, the language you asked in</p>
              </div>

              <p className="mt-8 text-[13px] leading-[1.7] text-neutral-500">
                Short tokens that are ambiguous between the two languages (or, to, main, par, he)
                are deliberately left out of the dictionary, so genuinely English and code-mixed
                questions are never corrupted on the way in.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ══ Dark inset: evaluation ═══════════════════════════ */}
      <section id="results" className="px-4 pb-24 sm:px-8">
        <div className="relative overflow-hidden rounded-sm bg-ink text-white">
          <GenerativeGrid
            className="pointer-events-none absolute inset-0 h-full w-full"
            {...AMBIENT_FIELD}
          />
          <div className="relative z-10 mx-auto max-w-shell px-6 py-24 sm:px-10 sm:py-32">
            <Reveal>
              <p className="label-mono mb-7">Evaluation</p>
              <h2 className="display-xl max-w-[13ch] text-[clamp(2.4rem,5.4vw,4.6rem)]">
                Measured, not claimed.
              </h2>
              <p className="mt-8 max-w-[38rem] text-[17px] leading-[1.7] text-neutral-400">
                Rehnuma was benchmarked against 41 realistic admission questions in English, Roman
                Urdu and mixed phrasing, each labelled by hand with the documents that genuinely
                answer it. Keyword-only, semantic-only and fused retrieval were run separately over
                the same set so the three could be compared directly.
              </p>
            </Reveal>

            <Reveal delay={120} className="mt-20">
              <EvaluationResults />
            </Reveal>
          </div>
        </div>
      </section>

      {/* ══ Light block: scope ═══════════════════════════════ */}
      <section className="mx-auto max-w-shell px-6 pb-28 sm:px-10 sm:pb-36">
        <Reveal>
          <p className="label-mono mb-7">Scope</p>
          <h2 className="display-lg max-w-[16ch] text-[clamp(2rem,4.2vw,3.4rem)] text-neutral-900">
            What it does. What it will not.
          </h2>
        </Reveal>

        <div className="mt-16 grid gap-y-12 border-t border-neutral-200 pt-12 sm:grid-cols-2 sm:gap-x-14">
          <Reveal delay={80}>
            <p className="font-mono text-[13px] tracking-tighter2 text-primary-600">IN SCOPE</p>
            <ul className="mt-6 space-y-4">
              {SCOPE_INCLUDED.map(item => (
                <li key={item} className="flex gap-4">
                  <span
                    className="mt-[7px] h-2 w-2 shrink-0 bg-primary-400"
                    aria-hidden="true"
                  />
                  <span className="text-[15px] leading-[1.7] text-neutral-600">{item}</span>
                </li>
              ))}
            </ul>
          </Reveal>

          <Reveal delay={180} className="sm:border-l sm:border-neutral-200 sm:pl-14">
            <p className="font-mono text-[13px] tracking-tighter2 text-muted">OUT OF SCOPE</p>
            <ul className="mt-6 space-y-4">
              {SCOPE_EXCLUDED.map(item => (
                <li key={item} className="flex gap-4">
                  <span
                    className="mt-[7px] h-2 w-2 shrink-0 border border-neutral-400"
                    aria-hidden="true"
                  />
                  <span className="text-[15px] leading-[1.7] text-neutral-500">{item}</span>
                </li>
              ))}
            </ul>
          </Reveal>
        </div>

        <Reveal delay={240}>
          <p className="mt-14 max-w-[46rem] text-[15px] leading-[1.75] text-neutral-500">
            Rehnuma is a supplementary aid, not a replacement for the University of Karachi
            admission office. Always confirm anything that affects a deadline or a payment with the
            office directly.
          </p>
        </Reveal>
      </section>

      {/* ══ Dark block: closing CTA + footer ═════════════════ */}
      <div className="relative overflow-hidden bg-ink text-white">
        <GenerativeGrid
          className="absolute inset-0 h-full w-full pointer-events-none"
          {...AMBIENT_FIELD}
        />

        <section className="relative z-10 mx-auto max-w-shell px-6 py-32 text-center sm:px-10 sm:py-44">
          <Reveal>
            <h2 className="display-xl mx-auto max-w-[13ch] text-[clamp(2.6rem,6.4vw,5.4rem)]">
              Ready when you are.
            </h2>
            <p className="mx-auto mt-8 max-w-md text-[17px] leading-[1.7] text-neutral-400">
              Sign in or create a free account to start asking questions about admissions.
            </p>
            <div className="mt-11 flex justify-center">
              <SlideButton href="/login" icon={<ArrowRight className="h-4 w-4" />}>
                Take me to the Rehnuma
              </SlideButton>
            </div>
          </Reveal>
        </section>

        <footer className="relative z-10 border-t border-white/15">
          <div
            className="mx-auto flex max-w-shell flex-col items-start justify-between gap-3 px-6 py-8
                       font-mono text-[12px] tracking-tighter2 text-muted sm:flex-row sm:items-center sm:px-10"
          >
            <p>© {new Date().getFullYear()} Rehnuma · University of Karachi</p>
            <p>Sourced from official documents · Always verify with the admissions office</p>
          </div>
        </footer>
      </div>
    </main>
  )
}
