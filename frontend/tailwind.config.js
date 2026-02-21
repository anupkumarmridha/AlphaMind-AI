/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        dark: {
          bg: '#0f172a',
          panel: 'rgba(30, 41, 59, 0.6)',
          border: 'rgba(255, 255, 255, 0.08)'
        },
        accent: {
          cyan: '#22d3ee',
          indigo: '#6366f1'
        }
      },
      backgroundImage: {
        'glow': 'radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.15), transparent 25%), radial-gradient(circle at 85% 30%, rgba(34, 211, 238, 0.15), transparent 25%)'
      }
    },
  },
  plugins: [],
}
