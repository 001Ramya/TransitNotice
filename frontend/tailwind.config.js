/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17383b",
        mint: "#d7f5ed",
        teal: "#167d76",
        canvas: "#f4f8f6",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 8px 30px rgba(25, 60, 55, 0.045)",
      },
    },
  },
  plugins: [],
};
