/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        surface: {
          0: '#09090b',
          1: '#111113',
          2: '#18181b',
          3: '#1f1f23',
          4: '#27272a',
        },
        accent: {
          DEFAULT: '#10b981',
          dim: '#065f46',
          bright: '#34d399',
        },
        danger: '#ef4444',
        warn: '#f59e0b',
        info: '#3b82f6',
      },
      animation: {
        'pulse-dot': 'pulse-dot 2s ease-in-out infinite',
      },
      keyframes: {
        'pulse-dot': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
      },
    },
  },
  plugins: [],
};
