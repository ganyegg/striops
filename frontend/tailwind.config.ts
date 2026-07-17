import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Cape Town coastal — ocean, fynbos, sunrise, sandstone
        ink: {
          950: "#061018",
          900: "#0a1a24",
          800: "#102636",
          700: "#1a3a4d",
        },
        helm: {
          ocean: "#0d9488",
          oceanDeep: "#0f766e",
          sky: "#38bdf8",
          accent: "#14b8a6",
          gold: "#f59e0b",
          sunrise: "#fb923c",
          sand: "#f5e6c8",
          fynbos: "#84cc16",
          good: "#34d399",
          warn: "#fbbf24",
          bad: "#f87171",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SF Mono", "Menlo", "monospace"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(20, 184, 166, 0.15)",
        card: "0 8px 32px rgba(0, 0, 0, 0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
