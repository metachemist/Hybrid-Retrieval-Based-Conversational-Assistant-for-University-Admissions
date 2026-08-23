'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import ChartCard, { ChartTooltip } from './ChartCard'
import { SERIES_1, GRID, AXIS_TICK } from './chartTokens'

interface TopicStat {
  topic: string
  count: number
}

export default function TopicChart({ data }: { data: TopicStat[] }) {
  const formatted = data.map(d => ({
    ...d,
    label: d.topic.charAt(0).toUpperCase() + d.topic.slice(1),
  }))

  return (
    <ChartCard
      title="Topic breakdown"
      subtitle="What users are asking about"
      columns={['Topic', 'Queries']}
      rows={formatted.map(d => ({ label: d.label, value: d.count }))}
    >
      <ResponsiveContainer width="100%" height={200}>
        <BarChart
          layout="vertical"
          data={formatted}
          margin={{ top: 0, right: 12, left: 4, bottom: 0 }}
        >
          <CartesianGrid stroke={GRID} horizontal={false} />
          <XAxis
            type="number"
            tick={AXIS_TICK}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <YAxis
            type="category"
            dataKey="label"
            tick={AXIS_TICK}
            axisLine={false}
            tickLine={false}
            width={78}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: '#00000008' }} />
          {/* Single measure → single colour; the category is already on the axis. */}
          <Bar
            dataKey="count"
            name="Queries"
            fill={SERIES_1}
            radius={[0, 4, 4, 0]}
            maxBarSize={18}
          />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
