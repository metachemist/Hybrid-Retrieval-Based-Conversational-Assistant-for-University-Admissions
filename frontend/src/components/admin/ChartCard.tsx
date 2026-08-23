'use client'

import { useId, useState } from 'react'

export interface TableRow {
  label: string
  value: number
}

interface ChartCardProps {
  title: string
  subtitle?: string
  /** Header labels for the table twin, e.g. ['Date', 'Queries'] */
  columns: [string, string]
  /** Same numbers the chart plots — the WCAG-clean equivalent view */
  rows: TableRow[]
  children: React.ReactNode
}

/**
 * Chart container that ships a table view alongside the plot. A tooltip may
 * enhance a chart but must never be the only route to a value, so every chart
 * here has a table twin the reader can switch to.
 */
export default function ChartCard({ title, subtitle, columns, rows, children }: ChartCardProps) {
  const [view, setView] = useState<'chart' | 'table'>('chart')
  const panelId = useId()

  const toggle = (target: 'chart' | 'table', label: string) => (
    <button
      key={target}
      onClick={() => setView(target)}
      aria-pressed={view === target}
      className={`rounded-sm px-2 py-1 font-mono text-[11px] uppercase tracking-tighter2 transition-colors ${
        view === target
          ? 'bg-neutral-900 text-white'
          : 'text-muted hover:bg-neutral-100 hover:text-neutral-900'
      }`}
    >
      {label}
    </button>
  )

  return (
    <div className="rounded-sm border border-neutral-200 bg-white">
      <div className="flex items-start justify-between gap-4 border-b border-neutral-100 px-5 py-4">
        <div>
          <h3 className="text-[15px] font-medium text-neutral-900">{title}</h3>
          {subtitle && <p className="label-mono mt-1">{subtitle}</p>}
        </div>
        <div className="flex flex-shrink-0 items-center gap-0.5">
          {toggle('chart', 'Chart')}
          {toggle('table', 'Table')}
        </div>
      </div>

      <div id={panelId} className="p-5">
        {view === 'chart' ? (
          children
        ) : (
          <div className="max-h-[240px] overflow-y-auto">
            <table className="w-full text-[13px]">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-neutral-200 text-left">
                  <th className="py-2 pr-4 font-mono text-[11px] font-medium uppercase tracking-tighter2 text-muted">
                    {columns[0]}
                  </th>
                  <th className="py-2 text-right font-mono text-[11px] font-medium uppercase tracking-tighter2 text-muted">
                    {columns[1]}
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map(row => (
                  <tr key={row.label} className="border-b border-neutral-100 last:border-0">
                    <td className="py-2 pr-4 text-neutral-700">{row.label}</td>
                    {/* tabular-nums here: a column of numbers that must align */}
                    <td className="py-2 text-right tabular-nums text-neutral-900">
                      {row.value.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

/** Squared, mono tooltip shared by every chart on the dashboard. */
export function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-sm bg-neutral-900 px-3 py-2 text-white">
      <p className="font-mono text-[11px] uppercase tracking-tighter2 text-neutral-400">{label}</p>
      <p className="mt-0.5 text-[13px] font-medium tabular-nums">
        {payload[0].value.toLocaleString()} queries
      </p>
    </div>
  )
}
