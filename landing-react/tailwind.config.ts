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
        heading: ['var(--font-instrument-sans)', 'system-ui', 'sans-serif'],
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // Akzentfarbe aus dem complyo-Logo: #00FFF7 (HSL 178 100% 50%),
        // gemessen am Schild in public/logo-dark.png. Die Stufen halten den
        // Farbton und veraendern nur die Helligkeit.
        //
        // Die reine Logofarbe steht als akzent-400 und bleibt Dekoration:
        // auf Weiss kommt sie auf 1,26:1 und traegt damit weder Text noch
        // eine Flaeche mit weisser Schrift. Lesbares nimmt 600 aufwaerts.
        // Kontraste auf Weiss: 600 = 4,80:1, 700 = 5,94:1, 800 = 8,43:1,
        // 900 = 12,13:1 — das abgeloeste blue-600 lag bei 5,17:1,
        // blue-700 bei 7,00:1. Auf Dunkel ist es andersherum: dort traegt
        // akzent-400 (14,15:1 auf gray-900) mit dunkler Schrift.
        akzent: {
          50: "#EBFFFE",
          100: "#CCFFFD",
          200: "#9CFCF9",
          300: "#3DFFF9",
          400: "#00FFF7",
          500: "#00CCC5",
          600: "#00807B",
          700: "#00706C",
          800: "#005754",
          900: "#003D3B"
        },
        complyo: {
          akzent: "#00FFF7",
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
          "0%, 100%": { boxShadow: "0 0 20px rgba(0, 255, 247, 0.5)" },
          "50%": { boxShadow: "0 0 40px rgba(0, 255, 247, 0.8)" }
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
