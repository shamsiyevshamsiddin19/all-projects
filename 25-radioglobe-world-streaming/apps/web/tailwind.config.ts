import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        void: {
          950: "#040406",
          900: "#08080c",
          850: "#0f0f15",
          800: "#161620",
          750: "#1e1e2b",
          700: "#272738",
        },
        crimson: {
          DEFAULT: "#ff1a35",
          bright: "#ff2a4b",
          glow: "#ff002b",
          dark: "#66000f",
          dim: "#330810",
        },
      },
      boxShadow: {
        "crimson-glow": "0 0 25px -3px rgba(255, 26, 53, 0.45)",
        "crimson-laser": "0 0 40px 0px rgba(255, 0, 43, 0.6)",
        "tactical-glass": "0 8px 32px 0 rgba(0, 0, 0, 0.75)",
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      animation: {
        "radar-sweep": "spin 8s linear infinite",
        "orbit-rotate": "spin 40s linear infinite",
        "pulse-crimson": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glitch-flicker": "ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite",
      },
    },
  },
  plugins: [],
};
export default config;
