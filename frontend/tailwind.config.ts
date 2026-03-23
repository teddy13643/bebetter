import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        heading: ["Outfit", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
      colors: {
        brand: {
          bg: "#0F172A",
          surface: "#1E293B",
          border: "#334155",
          muted: "#94A3B8",
          text: "#CBD5E1",
          accent: "#10B981",
          "accent-hover": "#34D399",
        },
      },
    },
  },
  plugins: [],
};

export default config;
