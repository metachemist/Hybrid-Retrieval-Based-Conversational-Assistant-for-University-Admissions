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
  en: '#2563eb',
  ur: '#f59e0b',
  mixed: '#10b981',
}

const LABELS: Record<string, string> = {
  en: 'English',
  ur: 'Roman Urdu',
  mixed: 'Mixed',
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-neutral-900 text-white text-xs px-3 py-2 rounded-lg shadow-xl">
      <p className="text-neutral-400 mb-0.5">{label}</p>
      <p className="font-semibold">{payload[0].value} queries</p>
    </div>
  )
}

export default function LanguageChart({ data }: { data: LanguageStat[] }) {
  const formatted = data.map(d => ({
    ...d,
    label: LABELS[d.language] ?? d.language,
  }))

  return (
    <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-5">
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-neutral-800">Language Distribution</h3>
        <p className="text-xs text-neutral-500 mt-0.5">Queries by detected language</p>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={formatted} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" name="Queries" radius={[5, 5, 0, 0]} maxBarSize={52}>
            {formatted.map((entry, i) => (
              <Cell key={i} fill={COLORS[entry.language] ?? '#6366f1'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
