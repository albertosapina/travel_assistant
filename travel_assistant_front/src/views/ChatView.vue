<script setup lang="ts">
import { ref, nextTick } from 'vue'

// Definición de tipos para TypeScript
interface Mensaje {
  id: number
  role: 'user' | 'assistant'
  text: string
}

const nuevoMensaje = ref<string>('')
const chatContainer = ref<HTMLDivElement | null>(null)

// Historial inicial del chat
const mensajes = ref<Mensaje[]>([
  { id: 1, role: 'assistant', text: '¡Hola! Soy tu asistente de viajes inteligente. ¿A qué ciudad te gustaría viajar?' }
])

// Función principal para enviar el mensaje y abrir el canal SSE
const enviarMensaje = async (): Promise<void> => {
  if (!nuevoMensaje.value.trim()) return

  const textoUsuario = nuevoMensaje.value.trim()
  
  // 1. Añadimos el mensaje del usuario a la pantalla
  mensajes.value.push({
    id: Date.now(),
    role: 'user',
    text: textoUsuario
  })

  nuevoMensaje.value = '' // Limpiamos el input de inmediato
  await scrollAlFinal()

  // 2. Creamos el objeto del mensaje del asistente por separado
  const nuevoMensajeAsistente: Mensaje = {
    id: Date.now() + 1,
    role: 'assistant',
    text: '' // Empieza vacío
  }

  // Lo insertamos en el array reactivo
  mensajes.value.push(nuevoMensajeAsistente)

  // 3. Conexión SSE con FastAPI utilizando la variable de entorno
  const urlBackend = `${import.meta.env.VITE_API_URL}/api/chat/stream?mensaje=${encodeURIComponent(textoUsuario)}`
  const eventSource = new EventSource(urlBackend)

  // Escuchamos los fragmentos de texto enviados por FastAPI
  eventSource.onmessage = async (event) => {
    if (event.data === '[DONE]') {
      eventSource.close()
      return
    }

    // Al modificar directamente la referencia del objeto 'nuevoMensajeAsistente',
    // Vue actualiza la interfaz automáticamente sin necesidad de buscar índices en el array.
    const fragmentoTexto = event.data.replace(/\\n/g, '\n')
    nuevoMensajeAsistente.text += fragmentoTexto
    
    await scrollAlFinal()
  }

  // Gestión de errores en la conexión
  eventSource.onerror = () => {
    eventSource.close()
    
    // Si la conexión se cae y no ha llegado a escribir nada, mostramos el aviso de error
    if (!nuevoMensajeAsistente.text) {
      nuevoMensajeAsistente.text = '⚠️ Error de conexión con el servidor. Por favor, asegúrate de que el backend está corriendo.'
    }
  }
}


// Función auxiliar para forzar el scroll al fondo
const scrollAlFinal = async (): Promise<void> => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}
</script>


<template>
  <!-- Contenedor general del chat que ocupa el 100% del espacio disponible -->
  <div class="flex-1 flex flex-col max-w-4xl w-full mx-auto bg-white border-x border-slate-200 min-h-0">
    
    <!-- Zona de Mensajes (Scrollable) -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto p-6 space-y-4">
      <div 
        v-for="msg in mensajes" 
        :key="msg.id" 
        class="flex w-full"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <!-- Burbuja de mensaje -->
        <div 
          class="max-w-[75%] px-4 py-3 rounded-2xl shadow-sm text-sm leading-relaxed"
          :class="msg.role === 'user' 
            ? 'bg-blue-600 text-white rounded-br-none' 
            : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200'"
        >
          <!-- Identificador de quién habla -->
          <p class="text-[10px] font-bold uppercase tracking-wider mb-1 opacity-70">
            {{ msg.role === 'user' ? 'Tú' : 'Asistente IA' }}
          </p>
          <!-- Texto del mensaje -->
          <p class="whitespace-pre-line">{{ msg.text }}</p>
        </div>
      </div>
    </div>

    <!-- Barra Inferior de Entrada de Texto -->
    <div class="p-4 border-t border-slate-200 bg-slate-50">
      <form @submit.prevent="enviarMensaje" class="flex gap-2 max-w-3xl mx-auto">
        <input 
          v-model="nuevoMensaje"
          type="text" 
          placeholder="Escribe tu destino, presupuesto o preguntas aquí..." 
          class="flex-1 px-4 py-3 bg-white border border-slate-300 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
        />
        <button 
          type="submit" 
          class="px-5 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-md transition-colors text-sm flex items-center gap-1"
        >
          Enviar 🚀
        </button>
      </form>
    </div>
  </div>
</template>
