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
      fontFamily: {
        sans: ['var(--font-dm-sans)', 'system-ui', 'sans-serif'],
        heading: ['var(--font-dm-sans)', 'system-ui', 'sans-serif'],
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // Akzentfarbe seit 04.11.2026: das Gold der Anmeldeseiten (#F59A08 aus
        // auth-neu.css im Dashboard). Der Name "akzent" bleibt, damit die 21
        // Dateien, die ihn nutzen, mit EINER Aenderung umziehen.
        //
        // Regel wie bisher: Gold traegt als FLAECHE mit dunkler Schrift darauf
        // (akzent-400/500 mit #161515 ueber 8:1). Als SCHRIFT auf Weiss nur die
        // dunklen Stufen: 600/700 = #A85F00 mit 4,8:1, 800 = 7,6:1, 900 = 11:1.
        // #F59A08 selbst liegt auf Weiss bei 2,2:1 und ist nie Schrift.
        // Das Logo bleibt cyan, es ist eine Bildmarke und kein UI-Ton.
        akzent: {
          50: "#FFF9EC",
          100: "#FEF0D0",
          200: "#FDDFA0",
          300: "#FCC95E",
          400: "#FBAE05",
          500: "#F59A08",
          600: "#A85F00",
          700: "#A85F00",
          800: "#7E4700",
          900: "#5A3300"
        },
        tinte: "#161515",
        complyo: {
          akzent: "#F59A08",
          purple: "#8b5cf6",
          dark: "#0f172a",
          slate: "#1e293b"
        }
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-glow": "pulseGlow 2s infinite",
        "float": "float 3s ease-in-out infinite"
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(245, 154, 8, 0.45)" },
          "50%": { boxShadow: "0 0 40px rgba(245, 154, 8, 0.7)" }
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" }
        }
      }
    },
  },
  plugins: [
    require("@tailwindcss/typography")
  ],
};

export default config;
