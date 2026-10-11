<script setup lang="ts">
import { useTokenClient } from 'vue3-google-signin'
import { useRouter } from 'vue-router'

const router = useRouter()

// Configuración unificada de Google: Solicita solo el email en flujo Access Token
const { login } = useTokenClient({
  onSuccess: (response) => {
    // Google nos devuelve response.access_token de forma limpia
    if (response.access_token) {
      localStorage.setItem('google_access_token', response.access_token)
      console.log('¡Token fresco de login guardado!')
      router.push('/')
    }
  },
  onError: (error) => {
    console.error('Error en el login de Google:', error)
  }
})
</script>

<template>
  <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; background: #f9fafb;">
    <div style="background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); text-align: center;">
      <h2 style="margin: 0 0 10px 0; color: #111;">Bienvenido a Travel Assistant</h2>
      <p style="margin: 0 0 20px 0; color: #666; font-size: 14px;">Inicia sesión para gestionar tus itinerarios con IA</p>
      
      <!-- BOTÓN PERSONALIZADO ASÍNCRONO -->
      <button 
        @click="() => login()" 
        style="padding: 12px 24px; background: #4285F4; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; display: inline-flex; align-items: center; gap: 10px;"
      >
        <span style="font-size: 18px;">🌐</span> Iniciar sesión con Google
      </button>
    </div>
  </div>
</template>
