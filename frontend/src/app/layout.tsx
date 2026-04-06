import type { Metadata } from 'next'
import { Outfit, DM_Serif_Display } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/lib/auth'

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
})

const dmSerif = DM_Serif_Display({
  subsets: ['latin'],
  weight: '400',
  variable: '--font-dm-serif',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Admission Assistant — University of Karachi',
  description: 'Get instant answers about University of Karachi admission policies, requirements, and procedures.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${dmSerif.variable} ${outfit.className}`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
