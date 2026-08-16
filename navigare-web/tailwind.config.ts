import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A0A0A",
        panel: "#FFFFFF",
        paper: "#F5F5F0",
        paperdark: "#E8E8E0",
        accent: "#D4380D",
        "accent-hover": "#B82E0A",
        bg: "#F5F5F0",
        text: "#0A0A0A",
        muted: "#6B6B6B",
        border: "#D0D0C8",
        surface: "#FFFFFF",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
        display: ['"Georgia"', '"Times New Roman"', "serif"],
        body: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
