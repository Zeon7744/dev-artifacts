/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#6366f1',
        'primary-hover': '#818cf8',
        dark: { DEFAULT: '#0a0a0f', card: '#1a1a2e', border: '#27272a' },
      },
    },
  },
  plugins: [],
}
