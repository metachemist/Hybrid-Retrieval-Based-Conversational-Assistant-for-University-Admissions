interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
}

export default function KpiCard({ label, value, sub }: KpiCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 border-l-4 border-l-amber-400
                    p-5 shadow-sm hover:shadow-md transition-shadow">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
        {label}
      </p>
      <p className="text-3xl font-bold text-slate-900 leading-none tabular-nums">
        {value}
      </p>
      {sub && (
        <p className="mt-2 text-xs text-slate-400 font-medium">{sub}</p>
      )}
    </div>
  )
}
