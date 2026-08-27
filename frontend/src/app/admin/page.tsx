'use client'

import { useEffect, useState } from 'react'
import {
  api,
  AnalyticsOverview,
  QueryVolumePoint,
  LanguageStat,
  TopicStat,
  TopQuery,
} from '@/lib/api'
import KpiCard from '@/components/admin/KpiCard'
import QueryVolumeChart from '@/components/admin/QueryVolumeChart'
import LanguageChart from '@/components/admin/LanguageChart'
import TopicChart from '@/components/admin/TopicChart'
import { formatLatency } from '@/lib/format'

const RANGE_OPTIONS = [
  { label: '7d', value: 7 },
  { label: '30d', value: 30 },
  { label: '90d', value: 90 },
]

export default function AdminDashboard() {
  const [days, setDays] = useState(30)
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [volume, setVolume] = useState<QueryVolumePoint[]>([])
  const [languages, setLanguages] = useState<LanguageStat[]>([])
  const [topics, setTopics] = useState<TopicStat[]>([])
  const [topQueries, setTopQueries] = useState<TopQuery[]>([])
  // Skeletons are for the first paint only. On a range change the previous
  // render is held at reduced opacity instead, so the page never jumps.
  const [firstLoad, setFirstLoad] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      setRefreshing(true)
      setError(null)
      try {
        const [ov, vol, lang, top, tq] = await Promise.all([
          api.getAnalyticsOverview(days),
          api.getQueryVolume(days),
          api.getLanguageStats(days),
          api.getTopicStats(days),
          api.getTopQueries(days, 10),
        ])
        if (cancelled) return
        setOverview(ov)
        setVolume(vol)
        setLanguages(lang)
        setTopics(top)
        setTopQueries(tq)
      } catch (err: any) {
        if (!cancelled) setError(err.message || 'Failed to load analytics')
      } finally {
        if (!cancelled) {
          setRefreshing(false)
          setFirstLoad(false)
        }
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [days])

  return (
    <div className="min-h-full p-6 sm:p-10">
      {/* ══ Page header ══════════════════════════════════════ */}
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="label-mono mb-3">Admin console</p>
          <h1 className="display-lg text-[clamp(1.75rem,3.2vw,2.5rem)] text-neutral-900">
            Analytics
          </h1>
        </div>

        {/* One filter row above everything it scopes */}
        <div
          role="group"
          aria-label="Date range"
          className="flex items-center gap-0.5 rounded-sm border border-neutral-200 bg-white p-1"
        >
          {RANGE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setDays(opt.value)}
              aria-pressed={days === opt.value}
              className={`rounded-sm px-3.5 py-1.5 font-mono text-[12px] uppercase tracking-tighter2 transition-colors ${
                days === opt.value
                  ? 'bg-neutral-900 text-white'
                  : 'text-muted hover:bg-neutral-100 hover:text-neutral-900'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mt-8 rounded-sm border border-red-200 bg-red-50 px-4 py-3 text-[14px] text-red-700">
          {error}
        </div>
      )}

      <div
        className={`mt-8 space-y-5 transition-opacity duration-200 ${
          refreshing && !firstLoad ? 'opacity-50' : 'opacity-100'
        }`}
      >
        {/* ══ KPI row ════════════════════════════════════════ */}
        {firstLoad ? (
          <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="animate-pulse rounded-sm border border-neutral-200 bg-white p-5">
                <div className="mb-5 h-2.5 w-24 rounded-sm bg-neutral-100" />
                <div className="mb-3 h-8 w-20 rounded-sm bg-neutral-100" />
                <div className="h-2 w-16 rounded-sm bg-neutral-100" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-5 lg:grid-cols-4">
            <KpiCard
              label="Total queries"
              value={overview?.total_queries?.toLocaleString() ?? '—'}
              sub={`Last ${days} days`}
            />
            <KpiCard
              label="Avg response time"
              value={overview ? formatLatency(overview.avg_latency_ms) : '—'}
              sub="End-to-end latency"
            />
            <KpiCard
              label="Cache hit rate"
              value={overview ? `${overview.cache_hit_rate_pct.toFixed(1)}%` : '—'}
              sub="Responses from cache"
            />
            <KpiCard
              label="Success rate"
              value={overview ? `${overview.success_rate_pct.toFixed(1)}%` : '—'}
              sub="Answered from documents"
            />
          </div>
        )}

        {!firstLoad && (
          <>
            <QueryVolumeChart data={volume} days={days} />

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <LanguageChart data={languages} />
              <TopicChart data={topics} />
            </div>

            {/* ══ Top questions ══════════════════════════════ */}
            {topQueries.length > 0 && (
              <div className="overflow-hidden rounded-sm border border-neutral-200 bg-white">
                <div className="border-b border-neutral-100 px-5 py-4">
                  <h3 className="text-[15px] font-medium text-neutral-900">Top questions</h3>
                  <p className="label-mono mt-1">Most frequently asked queries</p>
                </div>
                <table className="w-full text-[14px]">
                  <thead>
                    <tr className="border-b border-neutral-200 text-left">
                      <th className="w-12 px-5 py-2.5 font-mono text-[11px] font-medium uppercase tracking-tighter2 text-muted">
                        #
                      </th>
                      <th className="px-3 py-2.5 font-mono text-[11px] font-medium uppercase tracking-tighter2 text-muted">
                        Query
                      </th>
                      <th className="px-5 py-2.5 text-right font-mono text-[11px] font-medium uppercase tracking-tighter2 text-muted">
                        Count
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {topQueries.map((q, i) => (
                      <tr
                        key={i}
                        className="border-b border-neutral-100 transition-colors last:border-0 hover:bg-neutral-50"
                      >
                        <td className="px-5 py-3 font-mono text-[12px] tabular-nums text-muted">
                          {String(i + 1).padStart(2, '0')}
                        </td>
                        <td className="px-3 py-3 pr-8 text-neutral-700">{q.query}</td>
                        <td className="px-5 py-3 text-right tabular-nums text-neutral-900">
                          {q.count.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
