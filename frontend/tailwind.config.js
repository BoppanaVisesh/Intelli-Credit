/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: '#F5F0E8',
        parchment: '#EDE5D4',
        'warm-white': '#FAF7F2',
        sienna: { DEFAULT: '#A0522D', light: '#C4693F' },
        terracotta: '#CB6E45',
        gold: { DEFAULT: '#B8860B', light: '#D4A017' },
        charcoal: '#2C2416',
        ink: '#3D3020',
        muted: '#7A6850',
        'warm-border': '#DDD4C0',
        'warm-border-dark': '#C9BCA8',
        forest: '#4D7C3A',
      },
      fontFamily: {
        serif: ['Playfair Display', 'serif'],
        sans: ['DM Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      boxShadow: {
        warm: '0 2px 16px rgba(0,0,0,0.04)',
        'warm-lg': '0 12px 32px rgba(0,0,0,0.08), 0 4px 8px rgba(160,82,45,0.12)',
      },
    },
  },
  plugins: [],
}
