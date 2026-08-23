import type { Metadata } from 'next'
import { Outfit, Archivo, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/lib/auth'

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
})

// Display face for the oversized uppercase headlines. A grotesque (rather than
// an ultra-condensed poster face) is what lets the reference's signature
// treatment work: huge size, near-solid line-height, negative tracking.
const archivo = Archivo({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-display',
  display: 'swap',
})

// Micro-labels, eyebrows and code blocks.
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '700'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Rehnuma | University of Karachi Admissions',
  description: 'Rehnuma is your guide to University of Karachi admissions. Get instant, cited answers about admission policies, requirements, and procedures in English and Roman Urdu.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${archivo.variable} ${jetbrainsMono.variable} ${outfit.className}`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}
