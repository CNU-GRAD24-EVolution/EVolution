/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{tsx,ts,jsx,js}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Pretendard", "sans-serif"],
      },

      colors: {
        "gray-light": "#ECECEC",
        "black-light": "#535353",
      },

      animation: {
        show: "showIn .1s ease-in-out",
        hide: "showOut .1s ease-in-out",
        appearFromBottom: "appearBottom .1s ease forwards",
        hideFromTop: "hideTop .1s ease forwards",
      },

      keyframes: {
        showIn: {
          from: { scale: "0%" },
          to: { scale: "100%" },
        },

        showOut: {
          from: { scale: "100%" },
          to: { scale: "0%" },
        },

        appearBottom: {
          from: {
            top: "100%",
            opacity: 0,
          },
          to: {
            top: "0px",
            opacity: 1,
          },
        },

        hideTop: {
          from: {
            top: "0px",
            opacity: 1,
          },
          to: {
            top: "100%",
            opacity: 1,
          },
        },
      },
    },
  },
  plugins: [],
};
