'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { GraduationCap, LayoutDashboard, FileText, LogOut, ArrowLeft } from 'lucide-react'
import { useAuth } from '@/lib/auth'

const navItems = [
  { href: '/admin', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/admin/documents', label: 'Documents', icon: FileText },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading && (!user || user.role !== 'admin')) {
      router.replace('/login')
    }
  }, [user, isLoading, router])

  if (isLoading || !user || user.role !== 'admin') return null

  const initials = user.email.slice(0, 2).toUpperCase()

  return (
    <div className="flex min-h-screen bg-slate-50">

      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside className="w-60 bg-slate-950 flex flex-col flex-shrink-0 animate-in-down">

        {/* Logo */}
        <div className="px-5 py-5 border-b border-white/5">
          <div className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center shadow-inner
                            transition-transform duration-300 group-hover:rotate-12 group-hover:scale-110">
              <GraduationCap className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-xs font-semibold text-white leading-none">Admin Console</p>
              <p className="text-xs text-slate-500 leading-none mt-0.5">UoK Chatbot</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          <p className="px-3 mb-2 text-[10px] font-semibold text-slate-600 uppercase tracking-widest">
            Navigation
          </p>
          {navItems.map(({ href, label, icon: Icon }, i) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                style={{ animationDelay: `${i * 0.06}s` }}
                className={`animate-in-up flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium
                            transition-all hover:scale-[1.02] active:scale-[0.98] ${
                  active
                    ? 'bg-white/10 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className={`w-4 h-4 flex-shrink-0 ${active ? 'text-primary-400' : ''}`} />
                {label}
                {active && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-400 animate-pulse" />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Footer */}
        <div className="px-3 py-4 border-t border-white/5 space-y-0.5">
          <Link
            href="/"
            className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm
                       text-slate-500 hover:text-white hover:bg-white/5 transition-all
                       hover:scale-[1.02] active:scale-[0.98]"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Chatbot
          </Link>
          <button
            onClick={() => {
              logout()
              router.push('/login')
            }}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm
                       text-slate-500 hover:text-white hover:bg-white/5 transition-all
                       hover:scale-[1.02] active:scale-[0.98]"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>

          {/* User chip */}
          <div className="flex items-center gap-2.5 px-3 py-2 mt-2">
            <div className="w-7 h-7 rounded-lg bg-slate-700 flex items-center justify-center
                            text-xs font-bold text-white flex-shrink-0">
              {initials}
            </div>
            <p className="text-xs text-slate-500 truncate">{user.email}</p>
          </div>
        </div>
      </aside>

      {/* ── Main ────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto">
        {children}
      </div>
    </div>
  )
}
