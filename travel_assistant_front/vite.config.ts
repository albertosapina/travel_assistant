import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ command }) => {
  return {
    // Si ejecutas 'npm run build' (en GitHub Actions), usa tu repositorio.
    // Si ejecutas 'npm run dev' (en local), usa la raíz '/'
    base: command === 'build' ? '/travel_assistant/' : '/',
    
    plugins: [
      vue(),
      vueDevTools(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
