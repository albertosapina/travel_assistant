import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite' // <-- 1. Añade esta importación aquí arriba

// https://vite.dev
export default defineConfig(({ command }) => {
  return {
    base: command === 'build' ? '/travel_assistant/' : '/',
    plugins: [
      vue(),
      vueDevTools(),
      tailwindcss(), // <-- 2. Activa el plugin aquí dentro junto a los de Vue
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
