/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{js,ts,tsx}", "./components/**/*.{js,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#000000",
        secondary: "#111111",
        accent: "#ffffff",
        muted: "#888888",
      },
    },
  },
  plugins: [],
}