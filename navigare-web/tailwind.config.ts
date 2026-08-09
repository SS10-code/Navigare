import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111113",
        panel: "#17171B",
        paper: "#F2F0E9",
        paperdark: "#E5E2D8",
        purple: "#7C5CFF",
        teal: "#00FFC8",
        amber: "#FFB800",
        red: "#FF3B3B",
        green: "#00E676",
        blue: "#4DA3FF",
        magenta: "#FF2E88",
        bg: "#111113",
        text: "#F2F0E9",
        muted: "#8A8A93",
        border: "#2A2A30",
        surface: "#17171B",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
        display: ["Helvetica Neue", "Helvetica", "Arial", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
