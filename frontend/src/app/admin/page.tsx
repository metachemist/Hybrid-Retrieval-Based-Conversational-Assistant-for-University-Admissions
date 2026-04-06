'use client'

import { useEffect, useState } from 'react'
import { api, AnalyticsOverview, QueryVolumePoint, LanguageStat, TopicStat, TopQuery } from '@/lib/api'
import KpiCard from '@/components/admin/KpiCard'
import QueryVolumeChart from '@/components/admin/QueryVolumeChart'
import LanguageChart from '@/components/admin/LanguageChart'
import TopicChart from '@/components/admin/TopicChart'

const RANGE_OPTIONS = [
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last 90 days', value: 90 },
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
    <div className="p-6 space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Analytics Dashboard</h1>
          <p className="text-sm text-gray-500">Chatbot usage insights</p>
        </div>

        {/* Date range selector */}
        <div className="flex items-center gap-1 bg-white border border-gray-200 rounded-lg p-1">
          {RANGE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setDays(opt.value)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                days === opt.value
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-4 animate-pulse">
              <div className="h-3 bg-gray-200 rounded w-24 mb-3" />
              <div className="h-7 bg-gray-200 rounded w-16" />
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard
              label="Total Queries"
              value={overview?.total_queries?.toLocaleString() ?? '—'}
              sub={`Last ${days} days`}
            />
            <KpiCard
              label="Avg Response Time"
              value={overview ? `${Math.round(overview.avg_latency_ms)} ms` : '—'}
              sub="End-to-end latency"
            />
            <KpiCard
              label="Cache Hit Rate"
              value={overview ? `${overview.cache_hit_rate_pct.toFixed(1)}%` : '—'}
              sub="Responses from cache"
            />
            <KpiCard
              label="Query Success Rate"
              value={overview ? `${overview.success_rate_pct.toFixed(1)}%` : '—'}
              sub="Answered from documents"
            />
          </div>

          {/* Charts row 1: full-width line chart */}
          <QueryVolumeChart data={volume} />

          {/* Charts row 2: language + topic side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <LanguageChart data={languages} />
            <TopicChart data={topics} />
          </div>

          {/* Top queries table */}
          {topQueries.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Top Questions</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                    <th className="pb-2 font-medium">#</th>
                    <th className="pb-2 font-medium">Query</th>
                    <th className="pb-2 font-medium text-right">Count</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {topQueries.map((q, i) => (
                    <tr key={i}>
                      <td className="py-2 text-gray-400 w-8">{i + 1}</td>
                      <td className="py-2 text-gray-700 pr-4">{q.query}</td>
                      <td className="py-2 text-gray-800 font-medium text-right">{q.count}</td>
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
