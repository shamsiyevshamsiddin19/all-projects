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
        space: {
          950: "#040711",
          900: "#080d1a",
          850: "#0e162b",
          800: "#141f3d",
          700: "#1e2e57",
        },
        cyber: {
          cyan: "#00f2fe",
          blue: "#4facfe",
          neon: "#00ffcc",
          purple: "#7928ca",
          amber: "#ffb703",
        },
      },
      backgroundImage: {
        "cyber-grid": "radial-gradient(rgba(0, 242, 254, 0.08) 1px, transparent 0)",
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
      boxShadow: {
        "cyan-glow": "0 0 25px -5px rgba(0, 242, 254, 0.4)",
        "neon-glow": "0 0 30px -5px rgba(0, 255, 204, 0.35)",
        "glass": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 25s linear infinite",
      },
    },
  },
  plugins: [],
};
export default config;
