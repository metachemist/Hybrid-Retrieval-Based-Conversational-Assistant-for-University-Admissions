'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import ChartCard, { ChartTooltip } from './ChartCard'
import { SERIES_1, GRID, AXIS_TICK } from './chartTokens'

interface LanguageStat {
  language: string
  count: number
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
    <ChartCard
      title="Language distribution"
      subtitle="Queries by detected language"
      columns={['Language', 'Queries']}
      rows={formatted.map(d => ({ label: d.label, value: d.count }))}
    >
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={formatted} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis dataKey="label" tick={AXIS_TICK} axisLine={false} tickLine={false} />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: '#00000008' }} />
          {/* One measure → one colour for every bar. Per-category hues here would
              re-encode bar length as colour on categories with no natural order. */}
          <Bar
            dataKey="count"
            name="Queries"
            fill={SERIES_1}
            radius={[4, 4, 0, 0]}
            maxBarSize={24}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
