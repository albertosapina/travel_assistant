<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-800">
    <!-- Menú Superior Fijo -->
    <header class="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
      <div class="flex items-center gap-2 font-bold text-xl text-slate-900">
        <span>✈️</span> Travel Assistant
      </div>
      <nav class="flex gap-2">
        <RouterLink to="/" class="px-4 py-2 rounded-lg font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" active-class="bg-slate-100 text-slate-900 !font-semibold">
          Chat IA
        </RouterLink>
        <RouterLink to="/itinerario" class="px-4 py-2 rounded-lg font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors" active-class="bg-slate-100 text-slate-900 !font-semibold">
          Itinerario
        </RouterLink>
      </nav>
    </header>

    <!-- Contenedor Principal ocupando el resto de la pantalla -->
    <main class="flex-1 flex flex-col min-h-0">
      <RouterView />
    </main>
  </div>
</template>
