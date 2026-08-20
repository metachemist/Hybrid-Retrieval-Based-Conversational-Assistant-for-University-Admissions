'use client'

import { useEffect, useState } from 'react'
import { api, AnalyticsOverview, QueryVolumePoint, LanguageStat, TopicStat, TopQuery } from '@/lib/api'
import KpiCard from '@/components/admin/KpiCard'
import QueryVolumeChart from '@/components/admin/QueryVolumeChart'
import LanguageChart from '@/components/admin/LanguageChart'
import TopicChart from '@/components/admin/TopicChart'

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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const [ov, vol, lang, top, tq] = await Promise.all([
          api.getAnalyticsOverview(days),
          api.getQueryVolume(days),
          api.getLanguageStats(days),
          api.getTopicStats(days),
          api.getTopQueries(days, 10),
        ])
        setOverview(ov)
        setVolume(vol)
        setLanguages(lang)
        setTopics(top)
        setTopQueries(tq)
      } catch (err: any) {
        setError(err.message || 'Failed to load analytics')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [days])

  return (
    <div className="p-8 space-y-7 min-h-full">

      {/* ── Page header ─────────────────────────────────── */}
      <div className="flex items-center justify-between animate-in-down">
        <div>
          <h1 className="font-display font-bold text-2xl text-neutral-900">Analytics Dashboard</h1>
          <p className="text-sm text-neutral-500 mt-0.5">Chatbot usage insights</p>
        </div>

        {/* Date range toggle */}
        <div className="flex items-center gap-1 bg-white border border-neutral-200 rounded-xl p-1 shadow-sm">
          {RANGE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setDays(opt.value)}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                days === opt.value
                  ? 'bg-neutral-900 text-white shadow-sm'
                  : 'text-neutral-500 hover:text-neutral-800 hover:bg-neutral-50'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
          {error}
        </div>
      )}

      {/* ── KPI Cards ───────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-neutral-200 p-5 animate-pulse">
              <div className="h-2.5 bg-neutral-100 rounded-full w-24 mb-4" />
              <div className="h-8 bg-neutral-100 rounded-lg w-20 mb-2" />
              <div className="h-2 bg-neutral-100 rounded-full w-16" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="Total Queries"
            value={overview?.total_queries?.toLocaleString() ?? '-'}
            sub={`Last ${days} days`}
          />
          <KpiCard
            label="Avg Response Time"
            value={overview ? `${Math.round(overview.avg_latency_ms)} ms` : '-'}
            sub="End-to-end latency"
          />
          <KpiCard
            label="Cache Hit Rate"
            value={overview ? `${overview.cache_hit_rate_pct.toFixed(1)}%` : '-'}
            sub="Responses from cache"
          />
          <KpiCard
            label="Success Rate"
            value={overview ? `${overview.success_rate_pct.toFixed(1)}%` : '-'}
            sub="Answered from documents"
          />
        </div>
      )}

      {!loading && (
        <>
          {/* ── Volume chart ───────────────────────────── */}
          <QueryVolumeChart data={volume} />

          {/* ── Language + Topic charts ─────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <LanguageChart data={languages} />
            <TopicChart data={topics} />
          </div>

          {/* ── Top queries table ──────────────────────── */}
          {topQueries.length > 0 && (
            <div className="bg-white rounded-xl border border-neutral-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-neutral-100">
                <h3 className="text-sm font-semibold text-neutral-800">Top Questions</h3>
                <p className="text-xs text-neutral-500 mt-0.5">Most frequently asked queries</p>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b border-neutral-100 bg-neutral-50/60">
                    <th className="px-6 py-3 text-xs font-semibold text-neutral-500 w-10">#</th>
                    <th className="px-3 py-3 text-xs font-semibold text-neutral-500">Query</th>
                    <th className="px-6 py-3 text-xs font-semibold text-neutral-500 text-right">Count</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-50">
                  {topQueries.map((q, i) => (
                    <tr key={i} className="hover:bg-neutral-50/80 transition-colors">
                      <td className="px-6 py-3">
                        <span className="inline-flex items-center justify-center w-5 h-5
                                         rounded-full bg-neutral-100 text-neutral-500 text-xs font-medium">
                          {i + 1}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-neutral-700 pr-8">{q.query}</td>
                      <td className="px-6 py-3 text-right">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full
                                         bg-primary-50 text-primary-700 text-xs font-semibold">
                          {q.count}
                        </span>
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
  )
}
