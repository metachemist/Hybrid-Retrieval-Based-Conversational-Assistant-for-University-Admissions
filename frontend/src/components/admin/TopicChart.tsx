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

interface TopicStat {
  topic: string
  count: number
}

const TOPIC_COLORS: Record<string, string> = {
  eligibility: '#2563eb',
  fees: '#f59e0b',
  documents: '#10b981',
  deadlines: '#ef4444',
  merit: '#8b5cf6',
  programs: '#06b6d4',
  application: '#f97316',
  general: '#94a3b8',
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-900 text-white text-xs px-3 py-2 rounded-lg shadow-xl">
      <p className="text-slate-400 mb-0.5">{label}</p>
      <p className="font-semibold">{payload[0].value} queries</p>
    </div>
  )
}

export default function TopicChart({ data }: { data: TopicStat[] }) {
  const formatted = data.map(d => ({
    ...d,
    label: d.topic.charAt(0).toUpperCase() + d.topic.slice(1),
  }))

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-800">Topic Breakdown</h3>
        <p className="text-xs text-slate-500 mt-0.5">What users are asking about</p>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart
          layout="vertical"
          data={formatted}
          margin={{ top: 0, right: 12, left: 4, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="label"
            tick={{ fontSize: 10, fill: '#64748b' }}
            axisLine={false}
            tickLine={false}
            width={72}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" name="Queries" radius={[0, 5, 5, 0]} maxBarSize={18}>
            {formatted.map((entry, i) => (
              <Cell key={i} fill={TOPIC_COLORS[entry.topic] ?? '#6366f1'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
