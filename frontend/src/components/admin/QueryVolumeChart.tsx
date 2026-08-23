'use client'

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import ChartCard, { ChartTooltip } from './ChartCard'
import { SERIES_1, GRID, SURFACE, AXIS_TICK } from './chartTokens'

interface Point {
  date: string
  count: number
}

const DAY_MS = 86_400_000

// Dates arrive as plain YYYY-MM-DD. Parsing those with `new Date(...)` yields
// UTC midnight, which formats as the *previous* day in any negative-offset
// timezone — so every key and label below stays explicitly in UTC.
const keyOf = (t: number) => new Date(t).toISOString().slice(0, 10)

const labelOf = (t: number) =>
  new Date(t).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })

/**
 * The API returns only the days that had traffic, so a 30-day window can come
 * back as 6 rows. Plotting those directly spaces them evenly, which makes a
 * 12-day gap look identical to a 1-day gap and lets the line interpolate
 * through days that had no queries at all.
 *
 * Filling the window makes the axis a real timeline: an absent day is a zero,
 * because we know it had no queries — that is a measurement, not a gap.
 */
function fillWindow(data: Point[], days: number) {
  const counts = new Map(data.map(d => [d.date, d.count]))
  const end = Date.UTC(
    new Date().getUTCFullYear(),
    new Date().getUTCMonth(),
    new Date().getUTCDate()
  )
  const start = end - (days - 1) * DAY_MS

  const series = []
  for (let t = start; t <= end; t += DAY_MS) {
    series.push({ date: keyOf(t), label: labelOf(t), count: counts.get(keyOf(t)) ?? 0 })
  }
  return series
}

export default function QueryVolumeChart({ data, days }: { data: Point[]; days: number }) {
  const series = fillWindow(data, days)

  return (
    <ChartCard
      title="Query volume"
      subtitle="Daily chatbot interactions over time"
      columns={['Date', 'Queries']}
      rows={series.map(d => ({ label: d.label, value: d.count }))}
    >
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={series} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis
            dataKey="label"
            tick={AXIS_TICK}
            axisLine={false}
            tickLine={false}
            // Let recharts drop labels that would collide rather than
            // cramming 30 of them edge to edge.
            minTickGap={44}
          />
          <YAxis tick={AXIS_TICK} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: GRID }} />
          {/* Linear, not monotone: these are daily counts that jump between 0
              and 8: a spline through them draws values that were never
              measured. */}
          <Area
            type="linear"
            dataKey="count"
            name="Queries"
            stroke={SERIES_1}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            fill={SERIES_1}
            fillOpacity={0.1}
            dot={false}
            // r=4 → an 8px marker, with a 2px surface ring so it stays legible
            // where it sits on the line
            activeDot={{ r: 4, fill: SERIES_1, stroke: SURFACE, strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
