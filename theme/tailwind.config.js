module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'cell-yellow': '#fed41f',
        'cell-black': '#000000',
      },
      fontFamily: {
        montserrat: ['Montserrat', 'sans-serif'],
        'source-sans': ['"Source Sans Pro"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
