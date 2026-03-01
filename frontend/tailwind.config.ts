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
        background: "var(--background)",
        foreground: "var(--foreground)",
        accent: "var(--accent)",
        "card": "var(--card)",
        "card-border": "var(--card-border)",
      },
      animation: {
        "blob-float": "blob-float 15s infinite",
      },
      keyframes: {
        "blob-float": {
          "0%, 100%": { transform: "translatey(0) scale(1)", opacity: "0.2" },
          "50%": { transform: "translatey(-10px) scale(1.1)", opacity: "1" },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
export default config;