// tailwind.config.js
module.exports = {
  content: [
    "./templates/**/*.html",            // se tiver uma pasta templates/ global
    "./**/templates/**/*.html",         // templates dentro dos apps
    "./**/*.js",
    "./**/*.ts",
    // opcional: se você gerar classes em .py ou usa componentes que injetam HTML
    // "./**/*.py",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
