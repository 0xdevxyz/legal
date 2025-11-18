import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: 'class',
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        complyo: {
          blue: "#0ea5e9",        // Sky-500 - heller, moderner
          purple: "#a855f7",      // Purple-500 - eleganter
          indigo: "#6366f1",      // Indigo-500 - neu
          dark: "#0c0a09",        // Stone-950 - wärmer
          slate: "#18181b",       // Zinc-900 - moderner
          accent: "#14b8a6",      // Teal-500 - Akzentfarbe
          muted: "#27272a",       // Zinc-800 - für Cards
          border: "#3f3f46"       // Zinc-700 - subtile Borders
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-mesh': 'linear-gradient(135deg, #0c0a09 0%, #18181b 50%, #0c0a09 100%)',
        'glass-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.04) 100%)',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.18)',
        'glow-blue': '0 0 40px rgba(14, 165, 233, 0.3)',
        'glow-purple': '0 0 40px rgba(168, 85, 247, 0.3)',
        'inner-glow': 'inset 0 1px 2px 0 rgba(255, 255, 255, 0.05)',
      },
      animation: {
        "fade-in": "fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
        "slide-up": "slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "slide-down": "slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "scale-in": "scaleIn 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        "pulse-glow": "pulseGlow 3s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
        "gradient": "gradient 8s ease infinite",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        slideUp: {
          "0%": { transform: "translateY(16px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        },
        slideDown: {
          "0%": { transform: "translateY(-16px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" }
        },
        scaleIn: {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" }
        },
        pulseGlow: {
          "0%, 100%": { 
            boxShadow: "0 0 20px rgba(14, 165, 233, 0.2), 0 0 40px rgba(168, 85, 247, 0.2)" 
          },
          "50%": { 
            boxShadow: "0 0 30px rgba(14, 165, 233, 0.4), 0 0 60px rgba(168, 85, 247, 0.4)" 
          }
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" }
        },
        gradient: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" }
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" }
        }
      }
    },
  },
  plugins: [],
};

export default config;
