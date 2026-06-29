/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Pokemon brand colors
        'pokeball-red': '#EE1515',
        'pokeball-dark': '#CC0000',
        'pokeball-white': '#F0F0F0',
        'pokedex-blue': '#3B4CCA',
        'pokedex-light': '#4B6CF7',
        'pokemon-bg': '#fdf6f0',
        'pokemon-gold': '#FFD700',
        'pokemon-pink': '#F8A0B8',
        'pokemon-purple': '#A890F0',
        // Pokemon type colors
        'type-normal': '#A8A878',
        'type-fire': '#F08030',
        'type-water': '#6890F0',
        'type-electric': '#F8D030',
        'type-grass': '#78C850',
        'type-ice': '#98D8D8',
        'type-fighting': '#C03028',
        'type-poison': '#A040A0',
        'type-ground': '#E0C068',
        'type-flying': '#A890F0',
        'type-psychic': '#F85888',
        'type-bug': '#A8B820',
        'type-rock': '#B8A038',
        'type-ghost': '#705898',
        'type-dragon': '#7038F8',
        'type-dark': '#705848',
        'type-steel': '#B8B8D0',
        'type-fairy': '#EE99AC',
      }
    },
  },
  plugins: [],
}
