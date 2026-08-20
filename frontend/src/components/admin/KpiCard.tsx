interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
}

export default function KpiCard({ label, value, sub }: KpiCardProps) {
  return (
    <div className="bg-white rounded-xl border border-neutral-200 border-l-4 border-l-primary-400
                    p-5 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200
                    animate-in-up">
      <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-2">
        {label}
      </p>
      <p className="font-display text-3xl font-bold text-neutral-900 leading-none tabular-nums">
        {value}
      </p>
      {sub && (
        <p className="mt-2 text-xs text-neutral-400 font-medium">{sub}</p>
      )}
    </div>
  )
}
