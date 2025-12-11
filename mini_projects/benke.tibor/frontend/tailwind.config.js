/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'dark': '#0d0d0d',
        'darker': '#1a1a1a',
        'accent': '#10a37f',
      },
    },
  },
  plugins: [],
}
