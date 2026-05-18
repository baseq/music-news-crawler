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
        bg:       "#0f0f0f",
        surface:  "#1a1a1a",
        border:   "#2a2a2a",
        muted:    "#666",
        subtle:   "#888",
        body:     "#bbb",
        heading:  "#e8e8e8",
        accent:   "#0f3460",
        "accent-light": "#3b82f6",
      },
      fontFamily: {
        sans: ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
