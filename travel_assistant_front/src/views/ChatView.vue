<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import api from '../services/api'
import type { Itinerary } from '../types/itinerary'
import MarkdownIt from 'markdown-it'

interface Message {
  id: string;
  sender: 'user' | 'ai';
  text: string;
}

// --- ESTADOS REACTIVOS DE CONTEXTO ---
const listaItinerarios = ref<Itinerary[]>([])
const idItinerarioActivo = ref<string>('')
const cargandoContexto = ref<boolean>(false)

// --- ESTADOS REACTIVOS DE MENSAJES Y STREAMING ---
const messages = ref<Message[]>([
  { id: 'welcome', sender: 'ai', text: '¡Hola! Soy tu Asistente de Viajes. Selecciona un itinerario arriba y pregúntame lo que quieras sobre tus planes.' }
])
const inputMessage = ref<string>('')
const estaEscribiendoIA = ref<boolean>(false)
const contenedorMensajes = ref<HTMLElement | null>(null)

// Formateador markdown
const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true
})

const ultimoMensajeId = computed(() => {
  return messages.value[messages.value.length - 1]?.id
})

// Cargar los itinerarios del usuario para el desplegable
const cargarItinerariosContexto = async (): Promise<void> => {
  cargandoContexto.value = true

  try {
    const response = await api.get<Itinerary[]>('/api/itinerary')
    listaItinerarios.value = response.data

    const predeterminado = response.data.find(item => item.is_default)
    const primero = response.data[0]
    const itinerarioSeleccionado = predeterminado ?? primero

    idItinerarioActivo.value = itinerarioSeleccionado
      ? String(itinerarioSeleccionado._id ?? itinerarioSeleccionado.id ?? '')
      : ''

  } catch (error) {
    console.error('Error al cargar itinerarios para el chat:', error)

  } finally {
    cargandoContexto.value = false
  }
}

// Actualizar la preferencia privada en el servidor al cambiar el desplegable
const cambiarItinerarioActivo = async (): Promise<void> => {
  if (!idItinerarioActivo.value) return
  try {
    await api.patch(`/api/itinerary/${idItinerarioActivo.value}/default`)
  } catch (error) {
    console.error('Error al actualizar el contexto del chat:', error)
  }
}

// Auto-scroll asíncrono hacia el fondo para ver el texto conforme brota
const hacerScrollAlFondo = async (): Promise<void> => {
  await nextTick()
  if (contenedorMensajes.value) {
    contenedorMensajes.value.scrollTop = contenedorMensajes.value.scrollHeight
  }
}

// --- CORE DEL FLUJO DE STREAMING SSE ---
// travel_assistant_front/src/views/ChatView.vue

const enviarMensaje = async (): Promise<void> => {
  const textoMensaje = inputMessage.value.trim()
  if (!textoMensaje || estaEscribiendoIA.value) return

  // 1. Añadimos el mensaje del usuario a la pantalla
  messages.value.push({
    id: `user-${Date.now()}`,
    sender: 'user',
    text: textoMensaje
  })
  
  inputMessage.value = ''
  estaEscribiendoIA.value = true
  await hacerScrollAlFondo()

  // 2. Insertamos el "esqueleto" reactivo de la IA donde irá cayendo el stream
  const aiMessageId = `ai-${Date.now()}`
  messages.value.push({
    id: aiMessageId,
    sender: 'ai',
    text: ''
  })

  // 3. Preparación de variables de entorno y URLs saneadas
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const token = localStorage.getItem('google_access_token') || ''
  const cleanBaseUrl = baseUrl.replace(/\/$/, '')

  try {
    // ⚡ CORRECCIÓN AQUÍ: Comentario cambiado a doble barra '//' para cumplir con TypeScript
    // 4. Lanzamos la petición POST asíncrona usando el fetch nativo del navegador
    const response = await fetch(`${cleanBaseUrl}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify({
        message: textoMensaje,
        token: token,
        itinerary_id: idItinerarioActivo.value
      })
    })

    if (!response.ok) {
      throw new Error(`Error de servidor: ${response.status}`)
    }

    // 5. Leemos el flujo binario (Stream) del body en tiempo real de forma no bloqueante
    const reader = response.body?.getReader()
    const decoder = new TextDecoder('utf-8')
    
    if (!reader) {
      throw new Error('No se pudo inicializar el lector de stream.')
    }

    
let textoAcumuladoBuffer = ''
let terminado = false

while (!terminado) {
  const { value, done } = await reader.read()

  if (done) {
    // Vacía el decodificador por si quedan bytes pendientes.
    textoAcumuladoBuffer += decoder.decode()
    break
  }

  // Normalizamos los finales de línea sin tocar los espacios del texto.
  const chunkTexto = decoder.decode(value, { stream: true })
  textoAcumuladoBuffer += chunkTexto.replace(/\r\n/g, '\n').replace(/\r/g, '\n')

  // SSE separa cada evento mediante una línea en blanco.
  const eventos = textoAcumuladoBuffer.split('\n\n')
  textoAcumuladoBuffer = eventos.pop() ?? ''

  for (const evento of eventos) {
    const lineas = evento.split('\n')

    // Un evento puede tener varias líneas data:.
    // Solo quitamos el prefijo SSE, nunca los espacios finales.
    const lineasData = lineas
      .filter(linea => linea.startsWith('data:'))
      .map(linea => {
        return linea.startsWith('data: ')
          ? linea.slice(6)
          : linea.slice(5)
      })

    if (lineasData.length === 0) continue

    const dataPura = lineasData.join('\n')

    if (dataPura === '[DONE]') {
      terminado = true
      estaEscribiendoIA.value = false
      break
    }

    const mensajeIA = messages.value.find(m => m.id === aiMessageId)

    if (mensajeIA) {
      mensajeIA.text += dataPura.replace(/\\n/g, '\n')
      await hacerScrollAlFondo()
    }
  }
}

estaEscribiendoIA.value = false


  } catch (error) {
    console.error('Error en el flujo de streaming POST:', error)
    estaEscribiendoIA.value = false
    
    const mensajeIA = messages.value.find(m => m.id === aiMessageId)
    if (mensajeIA && !mensajeIA.text) {
      mensajeIA.text = '⚠️ Hubo un error al conectar con el servidor de Inteligencia Artificial.'
    }
  }
}


onMounted(() => {
  cargarItinerariosContexto()
})
</script>

<template>
  <div style="max-width: 900px; width: 100%; margin: 0 auto; padding: 20px; font-family: sans-serif; display: flex; flex-direction: column; height: 92vh; box-sizing: border-box;">
    
    <!-- CABECERA: Desplegable de Contexto del Viaje -->
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 12px; margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 24px;">🤖</span>
        <div>
          <label style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280; font-weight: bold; display: block;">Contexto del Viaje</label>
          <span style="font-size: 13px; color: #374151; font-weight: 500;">Gemini responderá usando este itinerario:</span>
        </div>
      </div>

      <div style="min-width: 240px;">
        <span v-if="cargandoContexto" style="font-size: 13px; color: #9ca3af;">Sincronizando planes... ⏳</span>
        <select 
          v-else
          v-model="idItinerarioActivo"
          @change="cambiarItinerarioActivo"
          style="width: 100%; padding: 8px 12px; font-size: 14px; border-radius: 8px; border: 1px solid #d1d5db; background: white; color: #1f2937; font-weight: bold; cursor: pointer; outline: none;"
        >
          <option v-if="listaItinerarios.length === 0" value="">🚫 Sin itinerarios en tu cuenta</option>
          <option 
            v-for="item in listaItinerarios" 
            :key="item._id || item.id" 
            :value="item._id || item.id"
          >
            🗺️ {{ item.title }} {{ item.is_default ? '(Principal)' : '' }}
          </option>
        </select>
      </div>
    </div>

    <!-- AREA CENTRAL: Contenedor de Mensajes Estilo ChatGPT -->
    <div 
      ref="contenedorMensajes"
      style="flex: 1; border: 1px solid #e5e7eb; border-radius: 16px; margin-bottom: 15px; padding: 20px; overflow-y: auto; background: #ffffff; display: flex; flex-direction: column; gap: 15px;"
    >
      <div 
        v-for="msg in messages" 
        :key="msg.id"
        :style="msg.sender === 'user' ? 'align-self: flex-end; max-width: 75%;' : 'align-self: flex-start; max-width: 75%;'"
      >
        <!-- Globo de Mensaje -->
        <div
          :class="[
            'globo-mensaje',
            msg.sender === 'user' ? 'globo-usuario' : 'globo-ia'
          ]"
        >
          <!-- El mensaje del usuario sigue mostrándose como texto plano -->
          <template v-if="msg.sender === 'user'">
            {{ msg.text }}
          </template>

          <!-- Las respuestas de Gemini se representan como Markdown -->
          <div
            v-else
            class="markdown-contenido"
            v-html="md.render(msg.text)"
          ></div>

          <!-- Cursor de escritura mientras llega la respuesta -->
          <span
            v-if="estaEscribiendoIA && msg.text === '' && msg.id === ultimoMensajeId"
            class="cursor-parpadeo"
          >┃</span>
        </div>
        <!-- Remitente debajo del globo -->
        <div :style="msg.sender === 'user' ? 'text-align: right; margin-top: 4px; font-size: 11px; color: #9ca3af;' : 'text-align: left; margin-top: 4px; font-size: 11px; color: #9ca3af;'">
          {{ msg.sender === 'user' ? 'Tú' : 'Travel Assistant' }}
        </div>
      </div>
    </div>

    <!-- INFERIOR: Barra de Entrada del Mensaje -->
    <div style="display: flex; gap: 10px; align-items: center;">
      <input 
        v-model="inputMessage"
        @keyup.enter="enviarMensaje"
        type="text"
        :disabled="estaEscribiendoIA || listaItinerarios.length === 0"
        placeholder="Pregúntame algo sobre tu itinerario seleccionado..."
        style="flex: 1; padding: 14px 18px; border-radius: 12px; border: 1px solid #d1d5db; font-size: 15px; outline: none; box-sizing: border-box;"
      />
      <button 
        @click="enviarMensaje"
        :disabled="estaEscribiendoIA || !inputMessage.trim() || listaItinerarios.length === 0"
        style="padding: 14px 24px; background: #2563eb; color: white; border: none; font-weight: bold; border-radius: 12px; cursor: pointer; font-size: 15px; transition: background 0.2s;"
        :class="{'btn-deshabilitado': estaEscribiendoIA || !inputMessage.trim()}"
      >
        {{ estaEscribiendoIA ? 'Pensando...' : 'Enviar 🚀' }}
      </button>
    </div>

  </div>
</template>

<style scoped>
.btn-deshabilitado {
  background: #9ca3af !important;
  cursor: not-allowed !important;
}

.cursor-parpadeo {
  animation: blinker 1s linear infinite;
  font-weight: bold;
  color: #2563eb;
}

@keyframes blinker {
  50% { opacity: 0; }
}
.globo-mensaje {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.globo-usuario {
  background: #2563eb;
  color: white;
  white-space: pre-wrap;
  border-radius: 16px 16px 4px 16px;
}

.globo-ia {
  background: #f3f4f6;
  color: #1f2937;
  border-radius: 16px 16px 16px 4px;
}

.markdown-contenido :deep(p) {
  margin: 0 0 10px;
}

.markdown-contenido :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-contenido :deep(h1),
.markdown-contenido :deep(h2),
.markdown-contenido :deep(h3) {
  margin: 12px 0 8px;
  line-height: 1.3;
}

.markdown-contenido :deep(ul),
.markdown-contenido :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-contenido :deep(li) {
  margin-bottom: 5px;
}

.markdown-contenido :deep(strong) {
  font-weight: 700;
}

.markdown-contenido :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}

.markdown-contenido :deep(pre) {
  overflow-x: auto;
  padding: 10px;
  border-radius: 8px;
  background: #e5e7eb;
}

.markdown-contenido :deep(code) {
  overflow-wrap: anywhere;
}
</style>
