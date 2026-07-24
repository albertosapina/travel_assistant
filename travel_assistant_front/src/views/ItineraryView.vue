<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'

// 1. Texto base inicial libre de errores de escape
const textoBase = `# 🗺️ Mi Itinerario de Viaje: Japón 2026

## 📅 Día 1: Llegada a Tokio
- **Tarde**: Llegada al hotel y check-in.
- **Noche**: Cena por Asakusa y vuelta al hotel a descansar.

## 📅 Día 2: Visita Asakusa
- Desayuno en el hotel.
- Visita al Templo Senso-ji.
- Paseo por la calle comercial Nakamise.`

// 2. Estados reactivos del editor
const markdownText = ref<string>(textoBase)
const ultimoTextoGuardado = ref<string>(textoBase)

const estaGuardando = ref<boolean>(false)
const guardadoExitoso = ref<boolean>(false)

// 3. Comprobación pasiva de cambios (Detecta si el usuario ha editado algo)
const hayCambiosSinGuardar = computed<boolean>(() => {
  return markdownText.value !== ultimoTextoGuardado.value
})

// 4. Transformación de Markdown a HTML puro
const htmlPreview = computed(() => {
  if (!markdownText.value) return ''
  return marked.parse(markdownText.value)
})

// 5. Función de guardado simulada para el backend
const guardarItinerario = async (): Promise<void> => {
  estaGuardando.value = true
  guardadoExitoso.value = false

  setTimeout(() => {
    estaGuardando.value = false
    guardadoExitoso.value = true
    
    // Sincronizamos el estado actual como guardado
    ultimoTextoGuardado.value = markdownText.value
    
    setTimeout(() => {
      guardadoExitoso.value = false
    }, 3000)
  }, 1200)
}
</script>

<template>
  <!-- Contenedor con estilos CSS nativos tradicionales directos para evitar fallos de renderizado -->
  <div style="max-width: 1200px; width: 100%; margin: 0 auto; padding: 20px; font-family: sans-serif;">
    
    <!-- Cabecera de la Sección -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 15px;">
      <div>
        <h1 style="margin: 0; font-size: 24px; color: #1a1a1a;">Editor de Itinerario</h1>
        <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">Este texto se mandará como contexto a la Inteligencia Artificial.</p>
      </div>
      
      <!-- Botón de Guardar y Avisos -->
      <div style="display: flex; align-items: center; gap: 15px;">
        <!-- ¡ALERTA ROJA SOLICITADA! Aparece si el texto actual cambia respecto al guardado -->
        <span v-if="hayCambiosSinGuardar && !estaGuardando" style="color: #e11d48; font-weight: bold; font-size: 14px; background: #fff1f2; padding: 6px 12px; border-radius: 6px; border: 1px solid #ffe4e6;">
          ⚠️ Tienes cambios sin guardar
        </span>

        <span v-if="guardadoExitoso" style="color: #16a34a; font-weight: bold; font-size: 14px; background: #f0fdf4; padding: 6px 12px; border-radius: 6px; border: 1px solid #dcfce7;">
          ¡Guardado correctamente! ✅
        </span>

        <button 
          @click="guardarItinerario"
          :disabled="estaGuardando"
          style="padding: 10px 20px; background: #059669; color: white; border: none; font-weight: bold; border-radius: 8px; cursor: pointer;"
        >
          {{ estaGuardando ? 'Guardando...' : 'Guardar Itinerario 💾' }}
        </button>
      </div>
    </div>

        <!-- Panel Dividido (Editor a la izquierda, Render a la derecha) -->
    <div class="panel-layout">
      
      <!-- Izquierda: Textarea -->
      <div>
        <textarea 
          v-model="markdownText"
          style="width: 100%; height: 500px; padding: 15px; background: #1e1e1e; color: #f4f4f4; font-family: monospace; font-size: 14px; border-radius: 8px; border: 1px solid #333; resize: none; box-sizing: border-box;"
        ></textarea>
      </div>

      <!-- Derecha: Vista Previa Renderizada (Añadimos la clase columna-preview) -->
      <div class="columna-preview" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #fff; height: 500px; overflow-y: auto; box-sizing: border-box;">
        <div v-html="htmlPreview" class="markdown-body"></div>
      </div>

    </div>

  </div>
</template>

<style scoped>
/* Configuración por defecto para ORDENADORES y pantallas grandes */
.panel-layout {
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 20px;
}

.columna-preview {
  display: block; /* Se muestra la vista previa */
}

/* 📱 CONFIGURACIÓN PARA SMARTPHONES (Pantallas menores de 768px de ancho) */
@media (max-width: 768px) {
  .panel-layout {
    grid-template-columns: 1fr; /* Pasa a ser una sola columna */
  }

  .columna-preview {
    display: none; /* ¡MAGIA! Oculta la vista previa por completo en móviles */
  }
}

/* Estilos de formato para el Markdown */
.markdown-body :deep(h1) { font-size: 22px; margin-top: 0; color: #111; border-bottom: 1px solid #eee; padding-bottom: 5px; }
.markdown-body :deep(h2) { font-size: 18px; margin-top: 15px; color: #222; }
.markdown-body :deep(ul) { padding-left: 20px; margin-bottom: 10px; }
.markdown-body :deep(li) { margin-bottom: 5px; color: #333; }
.markdown-body :deep(strong) { color: #000; font-weight: bold; }
</style>

