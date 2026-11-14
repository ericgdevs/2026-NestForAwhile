/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sage: {
          50: '#f1f8f2',
          100: '#dcefe0',
          200: '#bddfc5',
          300: '#91c8a0',
          500: '#4e9a6d',
          600: '#397f58',
          700: '#2f7856',
          800: '#276047',
          950: '#183229',
        },
      },
    },
  },
  plugins: [],
}

