import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        paper: "#f7f2e8",
        ink: "#1f2328",
        graphite: "#4b5563",
        sage: {
          DEFAULT: "#6d8a73",
          light: "#e8f0ea",
        },
        amber: {
          DEFAULT: "#d58c2f",
          light: "#fef3e2",
        },
      },
      boxShadow: {
        card: "0 10px 30px rgba(0,0,0,0.08)",
      },
      fontFamily: {
        sans: ["Inter", "Avenir Next", "Segoe UI", "sans-serif"],
        serif: ["Source Serif 4", "Iowan Old Style", "Georgia", "serif"],
        accent: ["Caveat", "cursive"],
      },
      borderRadius: {
        sketch: "12px 8px 14px 6px",
      },
      keyframes: {
        wiggle: {
          "0%, 100%": { transform: "rotate(0deg)" },
          "25%": { transform: "rotate(-0.5deg)" },
          "75%": { transform: "rotate(0.5deg)" },
        },
      },
      animation: {
        wiggle: "wiggle 0.3s ease-in-out",
      },
    },
  },
  plugins: [],
};

export default config;
