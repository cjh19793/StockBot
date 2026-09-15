/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#0B0E14",
        "bg-raised": "#12161F",
        "bg-card": "#151A24",
        border: "#232937",
        ink: "#E8EAED",
        "ink-dim": "#8891A3",
        "ink-faint": "#545E70",
        amber: "#FFB454",
        "amber-dim": "#8A6428",
        up: "#3DDC84",
        down: "#FF6B6B",
        info: "#58A6FF",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "-apple-system", "Pretendard", "Apple SD Gothic Neo", "sans-serif"],
        mono: ["var(--font-mono)", "SF Mono", "Consolas", "monospace"],
      },
      backgroundImage: {
        grid: "linear-gradient(#232937 1px, transparent 1px), linear-gradient(90deg, #232937 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "64px 64px",
      },
    },
  },
  plugins: [],
};
