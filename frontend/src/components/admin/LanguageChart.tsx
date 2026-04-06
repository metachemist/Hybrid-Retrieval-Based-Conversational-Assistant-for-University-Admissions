'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface LanguageStat {
  language: string
  count: number
}

const COLORS: Record<string, string> = {
  en: '#4f46e5',
  ur: '#10b981',
  mixed: '#f59e0b',
}

const LABELS: Record<string, string> = {
  en: 'English',
  ur: 'Roman Urdu',
  mixed: 'Mixed',
}

export default function LanguageChart({ data }: { data: LanguageStat[] }) {
  const formatted = data.map(d => ({
    ...d,
    label: LABELS[d.language] ?? d.language,
  }))

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">Queries by Language</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={formatted} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#6b7280' }} />
          <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} allowDecimals={false} />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
          />
          <Bar dataKey="count" name="Queries" radius={[4, 4, 0, 0]}>
            {formatted.map((entry, i) => (
              <Cell key={i} fill={COLORS[entry.language] ?? '#6366f1'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
