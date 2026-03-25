import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        abyss: "#040913",
        mist: "#c7dbff",
        glow: "#78d4ff",
        gold: "#ffcc80"
      },
      backgroundImage: {
        "space-shell":
          "radial-gradient(circle at top left, rgba(94,197,255,0.18), transparent 24%), radial-gradient(circle at 85% 10%, rgba(255,191,112,0.18), transparent 20%), linear-gradient(180deg, #050913 0%, #091423 42%, #050913 100%)"
      },
      boxShadow: {
        panel: "0 24px 80px rgba(0, 0, 0, 0.35)",
        glow: "0 0 40px rgba(120, 212, 255, 0.22)"
      },
      keyframes: {
        drift: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" }
        },
        sheen: {
          "0%, 100%": { transform: "translateX(-120%)" },
          "50%": { transform: "translateX(120%)" }
        },
        pulse: {
          "0%, 100%": { opacity: "0.45", transform: "scale(0.96)" },
          "50%": { opacity: "1", transform: "scale(1.04)" }
        }
      },
      animation: {
        drift: "drift 8s ease-in-out infinite",
        sheen: "sheen 7s ease-in-out infinite",
        pulse: "pulse 3s ease-in-out infinite"
      }
    }
  },
  plugins: []
};

export default config;
