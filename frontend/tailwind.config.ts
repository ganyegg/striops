import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#070a12",
          900: "#0b1020",
          800: "#111a2e",
          700: "#1b2740",
        },
        helm: {
          accent: "#5b8cff",
          gold: "#e8c37a",
          good: "#4ade80",
          warn: "#fbbf24",
          bad: "#f87171",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica", "Arial"],
      },
    },
  },
  plugins: [],
};

export default config;
