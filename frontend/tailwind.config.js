/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-outfit)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      colors: {
        // Lime/chartreuse accent — vivid tints (50-400) for badges, borders,
        // and hero highlights; darker shades (600+) double as functional
        // text/button colors that keep AA contrast on white.
        // 300 is the exact accent color sampled from builderstable.net's
        // .button-bg (#dafa9c) — surrounding tints are scaled from it.
        primary: {
          50: '#f9fdf0',
          100: '#f0fbd8',
          200: '#e8fcbe',
          300: '#dafa9c',
          400: '#c0f06a',
          500: '#9fd93f',
          600: '#6fa61f',
          700: '#537d17',
          800: '#3c5a11',
          900: '#1f2f09',
        },
        // Neutrals sampled from the same reference, so dark surfaces and
        // muted label text sit at the tones the layout was designed around.
        ink: {
          DEFAULT: '#111111', // page-level dark
          raised: '#191919', // slightly lifted dark surface
          line: '#1f1f1f', // secondary button / hairline fills
        },
        muted: '#737776', // label + secondary copy grey
      },
      letterSpacing: {
        // Display tracking from the reference: −2% at hero scale, −3% for the
        // largest statement type and the mono micro-labels.
        display: '-0.02em',
        tighter2: '-0.03em',
      },
      maxWidth: {
        shell: '1240px',
      },
    },
  },
  plugins: [],
}
