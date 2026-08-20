'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface Point {
  date: string
  count: number
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

export default function QueryVolumeChart({ data }: { data: Point[] }) {
  const formatted = data.map(d => ({
    ...d,
    label: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }))

  return (
    <div className="bg-white rounded-xl border border-neutral-200 shadow-sm p-5">
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-neutral-800">Query Volume</h3>
        <p className="text-xs text-neutral-500 mt-0.5">Daily chatbot interactions over time</p>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={formatted} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
          <defs>
            <linearGradient id="queryGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#2563eb" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#94a3b8' }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="count"
            name="Queries"
            stroke="#2563eb"
            strokeWidth={2}
            fill="url(#queryGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#2563eb', strokeWidth: 0 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
