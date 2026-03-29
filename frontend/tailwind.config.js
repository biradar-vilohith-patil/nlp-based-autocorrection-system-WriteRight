/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './public/index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Playfair Display'", 'Georgia', 'serif'],
        body:    ["'Outfit'", 'sans-serif'],
        mono:    ["'JetBrains Mono'", 'monospace'],
      },
      colors: {
        bg:      '#080810',
        surface: '#0e0e1a',
        card:    '#131320',
        border:  '#1e1e32',
        border2: '#2e2e4a',
        accent:  '#818cf8',
        glow:    '#4f46e5',
        glow2:   '#06b6d4',
      },
      borderRadius: {
        '2xl': '20px',
        '3xl': '28px',
      },
      animation: {
        'fade-down': 'fadeDown 0.6s ease both',
        'fade-up':   'fadeUp   0.6s ease both',
        'slide-up':  'slideUp  0.5s ease both',
        'fade-in':   'fadeIn   0.5s ease both',
        'shimmer':   'shimmer  1.6s infinite',
        'spin-slow': 'spin     1.2s linear infinite',
      },
      keyframes: {
        fadeDown: {
          from: { opacity: 0, transform: 'translateY(-16px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        fadeUp: {
          from: { opacity: 0, transform: 'translateY(20px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: 0, transform: 'translateY(28px)' },
          to:   { opacity: 1, transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: 0 },
          to:   { opacity: 1 },
        },
        shimmer: {
          '0%':   { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
    },
  },
  plugins: [],
}
