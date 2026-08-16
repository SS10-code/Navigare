import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1C1C3B",
        panel: "#FFFFFF",
        paper: "#F4F6FB",
        paperdark: "#E8EAF0",
        purple: "#423A8E",
        teal: "#423A8E",
        amber: "#F5A623",
        red: "#D32F2F",
        green: "#2E7D32",
        blue: "#1565C0",
        magenta: "#423A8E",
        bg: "#F4F6FB",
        text: "#1C1C3B",
        muted: "#5A5A7A",
        border: "#D8DCE8",
        surface: "#FFFFFF",
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
