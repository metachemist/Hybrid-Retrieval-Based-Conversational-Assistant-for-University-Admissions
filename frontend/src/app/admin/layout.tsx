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

const FOOTER_LINK =
  'flex w-full items-center gap-2.5 rounded-sm px-3 py-2 font-mono text-[12px] uppercase ' +
  'tracking-tighter2 text-muted transition-colors hover:bg-white/5 hover:text-white'

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
    <div className="flex min-h-screen bg-neutral-50">
      {/* ══ Sidebar ══════════════════════════════════════════ */}
      {/* Sticky, viewport-tall: the page itself is the scroller, so without this
          the nav scrolls away and leaves an empty column beside the content. */}
      <aside className="sticky top-0 flex h-screen w-60 flex-shrink-0 flex-col bg-ink">
        <div className="border-b border-white/10 px-5 py-4">
          <Link href="/admin" className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-sm bg-primary-300">
              <GraduationCap className="h-4 w-4 text-neutral-900" strokeWidth={2} />
            </span>
            <span className="display-lg text-[14px] leading-none text-white">Admin Console</span>
          </Link>
        </div>

        <nav className="flex-1 px-3 py-5">
          <p className="label-mono mb-3 px-3">Navigation</p>
          <div className="space-y-0.5">
            {navItems.map(({ href, label, icon: Icon }) => {
              const active = pathname === href
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={active ? 'page' : undefined}
                  className={`flex items-center gap-2.5 rounded-sm px-3 py-2.5 text-[14px] transition-colors ${
                    active
                      ? 'bg-white/10 font-medium text-white'
                      : 'text-neutral-400 hover:bg-white/5 hover:text-white'
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 flex-shrink-0 ${active ? 'text-primary-300' : ''}`}
                    strokeWidth={1.75}
                  />
                  {label}
                  {active && <span className="ml-auto h-1.5 w-1.5 bg-primary-300" />}
                </Link>
              )
            })}
          </div>
        </nav>

        <div className="space-y-0.5 border-t border-white/10 px-3 py-4">
          <Link href="/chat" className={FOOTER_LINK}>
            <ArrowLeft className="h-4 w-4" />
            Back to chatbot
          </Link>
          <button
            onClick={() => {
              logout()
              router.push('/')
            }}
            className={FOOTER_LINK}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>

          <div className="mt-3 flex items-center gap-2.5 border-t border-white/10 px-3 pt-4">
            <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-sm bg-white/10 font-mono text-[11px] font-medium text-white">
              {initials}
            </span>
            <p className="truncate font-mono text-[11px] tracking-tighter2 text-muted">
              {user.email}
            </p>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">{children}</div>
    </div>
  )
}
