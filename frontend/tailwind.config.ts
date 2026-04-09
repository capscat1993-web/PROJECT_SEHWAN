// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#6366f1",
        secondary: "#f43f5e",
        accent: "#facc15",
        "brand-bg": "#f0f2ff",
      },
      fontFamily: {
        headline: ["var(--font-bungee)", "cursive"],
        body: ["var(--font-noto)", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
