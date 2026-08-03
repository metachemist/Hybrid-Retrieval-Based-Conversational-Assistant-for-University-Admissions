import type { Metadata } from 'next'
import { Outfit, Big_Shoulders_Display } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/lib/auth'

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
})

const bigShoulders = Big_Shoulders_Display({
  subsets: ['latin'],
  weight: ['600', '700', '900'],
  variable: '--font-display',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Admission Assistant for University of Karachi',
  description: 'Get instant answers about University of Karachi admission policies, requirements, and procedures.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${bigShoulders.variable} ${outfit.className}`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
