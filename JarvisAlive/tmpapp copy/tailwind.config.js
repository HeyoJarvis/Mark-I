/** @type {import('tailwindcss').Config} */
export default {
  theme: {
    extend: {
      colors: {
        sidebar: {
          bg: '#0B1220',
          card: '#111827',
        },
      },
    },
  },
  safelist: ["ring-[--vf-accent]","bg-[--vf-accent]","text-[--vf-accent]","border-[--vf-accent]"],
  plugins: [],
}

