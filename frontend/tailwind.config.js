/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      colors: {
        surface: {
          DEFAULT: "var(--surface)",
          elevated: "var(--surface-elevated)",
          border: "var(--border)",
          hover: "var(--surface-hover)",
        },
        accent: {
          DEFAULT: "#7B61FF",
          hover: "#6C55F5",
          active: "#5D46E8",
          light: "#F4F0FF",
          "light-hover": "#EEE8FF",
          "light-active": "#E6DEFF",
          secondary: "#8B7CFF",
          text: "#5B42E0",
        },
        success: "#16a34a",
        warning: "#ca8a04",
        danger: "#dc2626",
        subtitle: "#707070",
      },
      borderRadius: {
        card: "12px",
        btn: "12px",
        input: "10px",
        mascot: "16px",
      },
      boxShadow: {
        card: "0 4px 12px rgba(0, 0, 0, 0.05)",
        mascot: "inset 0 1px 3px rgba(123, 97, 255, 0.08)",
      },
      minWidth: { app: "1200px" },
    },
  },
  plugins: [],
};
