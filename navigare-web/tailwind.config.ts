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
        accent: "#E04500",
        "accent-hover": "#C73E00",
        bg: "#F5F5F0",
        text: "#0A0A0A",
        muted: "#5A5A5A",
        border: "#C8C8C0",
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
