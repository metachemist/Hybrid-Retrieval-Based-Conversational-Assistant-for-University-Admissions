/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Lime/chartreuse accent — vivid tints (50-400) for badges, borders,
        // and hero highlights; darker shades (600+) double as functional
        // text/button colors that keep AA contrast on white.
        primary: {
          50: '#f7fee7',
          100: '#ecfccb',
          200: '#d9f99d',
          300: '#bef264',
          400: '#a3e635',
          500: '#84cc16',
          600: '#4d7c0f',
          700: '#3f6212',
          800: '#365314',
          900: '#1a2e05',
        },
      },
    },
  },
  plugins: [],
}
