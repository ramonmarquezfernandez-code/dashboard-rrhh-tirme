/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        tirme: {
          dark: '#0f2d30', // Tono oscuro corporativo para menús y barras
          green: '#28a745', // Verde corporativo para botones y elementos activos
          light: '#f4f6f8', // Fondo general suave
          card: '#ffffff', // Fondo blanco para tarjetas y tablas
        },
      },
    },
  },
  plugins: [],
};
