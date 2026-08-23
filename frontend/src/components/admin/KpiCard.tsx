interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
}

/**
 * Stat tile: label · value · sub.
 *
 * The value uses the body sans with the font's default proportional figures —
 * a display face reads as off-brand decoration on a figure, and `tabular-nums`
 * gives every digit the width of a `0`, which makes a number like 121 look
 * loose at this size. Tabular figures are for columns that align vertically.
 */
export default function KpiCard({ label, value, sub }: KpiCardProps) {
  return (
    <div className="rounded-sm border border-neutral-200 border-l-2 border-l-primary-600 bg-white p-5">
      <p className="label-mono">{label}</p>
      <p className="mt-3 text-[32px] font-semibold leading-none text-neutral-900">{value}</p>
      {sub && <p className="mt-2.5 text-[13px] text-neutral-500">{sub}</p>}
    </div>
  )
}
