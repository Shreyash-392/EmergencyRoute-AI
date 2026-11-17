/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Strict Brand Palette
        charcoal: {
          DEFAULT: '#1E1E1C',
          950: '#141413',
          900: '#1E1E1C',
          850: '#262624',
          800: '#2E2E2B',
          700: '#3D3D39',
          600: '#52524D',
          500: '#6E6E67',
        },
        sand: {
          DEFAULT: '#D8CBB3',
          50: '#FAF8F4',
          100: '#F4EFE6',
          200: '#E8DFD0',
          300: '#D8CBB3',
          400: '#C5B598',
          500: '#B09E7E',
          600: '#948162',
          700: '#75654B',
          800: '#5A4D39',
        },
        electric: {
          DEFAULT: '#2B6BFF',
          50: '#EEF4FF',
          100: '#DCE7FF',
          200: '#BCD1FF',
          300: '#8EB3FF',
          400: '#5B8EFF',
          500: '#2B6BFF', // Strict Brand Electric Blue
          600: '#1A55E0',
          700: '#0E3FB8',
          800: '#0B3394',
          glow: 'rgba(43, 107, 255, 0.35)',
        },
      },
      boxShadow: {
        'electric': '0 0 24px rgba(43, 107, 255, 0.35)',
        'electric-lg': '0 0 35px rgba(43, 107, 255, 0.5)',
        'charcoal': '0 10px 30px -5px rgba(30, 30, 28, 0.25)',
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
      },
    },
  },
  plugins: [],
}



