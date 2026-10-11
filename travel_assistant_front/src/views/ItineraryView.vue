<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import api from '../services/api' 
import type { Itinerary } from '../types/itinerary'

// --- ESTADOS REACTIVOS GLOBALES ---
const listaItinerarios = ref<Itinerary[]>([])
const itinerarioSeleccionado = ref<Itinerary | null>(null)
const cargandoLista = ref<boolean>(false)

// --- ESTADOS REACTIVOS DEL EDITOR ---
const itineraryTitle = ref<string>('')
const markdownText = ref<string>('')
const ultimoTituloGuardado = ref<string>('')
const ultimoTextoGuardado = ref<string>('')

const estaGuardando = ref<boolean>(false)
const guardadoExitoso = ref<boolean>(false)

const cargandoDetalle = ref<boolean>(false)

// --- COMPREBACIÓN PASIVA DE CAMBIOS ---
const hayCambiosSinGuardar = computed<boolean>(() => {
  if (!itinerarioSeleccionado.value) return false
  return markdownText.value !== ultimoTextoGuardado.value || itineraryTitle.value !== ultimoTituloGuardado.value
})

// --- TRANSFORMACIÓN MARKDOWN A HTML ---
const htmlPreview = computed(() => {
  if (!markdownText.value) return ''
  return marked.parse(markdownText.value)
})

// --- ACCIONES DE LLAMADA AL BACKEND ---
const cargarItinerarios = async (): Promise<void> => {
  cargandoLista.value = true
  try {
    const response = await api.get<Itinerary[]>('/api/itinerary')
    listaItinerarios.value = response.data
  } catch (error) {
    console.error('Error cargando itinerarios:', error)
  } university: {
    cargandoLista.value = false
  }
}

const crearNuevoItinerario = async (): Promise<void> => {
  const nuevo: Partial<Itinerary> = {
    title: 'Nuevo Itinerario de Viaje ✈️',
    content: '# 🗺️ Mi Nuevo Plan de Viaje\n\n## 📅 Día 1\n- Escribe aquí tus planes...'
  }
  try {
    const response = await api.post<Itinerary>('/api/itinerary', nuevo)
    listaItinerarios.value.unshift(response.data)
    seleccionarItinerario(response.data)
  } catch (error) {
    console.error('Error al crear itinerario:', error)
  }
}

const seleccionarItinerario = async (itinerarioCorto: Itinerary): Promise<void> => {
  const id = itinerarioCorto._id || itinerarioCorto.id
  cargandoDetalle.value = true
  
  // Inicializamos la vista con los datos que ya tenemos para dar feedback inmediato de UI
  itinerarioSeleccionado.value = { ...itinerarioCorto, content: '' }
  itineraryTitle.value = itinerarioCorto.title

  try {
    // Petición asíncrona bajo demanda al endpoint de detalle
    const response = await api.get<Itinerary>(`/api/itinerary/${id}`)
    
    // Inyectamos el contenido pesado en nuestros estados reactivos del editor
    markdownText.value = response.data.content
    itinerarioSeleccionado.value.content = response.data.content
    
    // Sincronizamos buffers para el control pasivo de cambios (Dirty State)
    ultimoTituloGuardado.value = response.data.title
    ultimoTextoGuardado.value = response.data.content
  } catch (error) {
    console.error('Error al descargar el detalle del itinerario:', error)
    alert('No se pudo cargar el contenido del viaje.')
    volverAlListado()
  } finally {
    cargandoDetalle.value = false
  }
}

const guardarItinerario = async (): Promise<void> => {
  if (!itinerarioSeleccionado.value) return
  
  estaGuardando.value = true
  guardadoExitoso.value = false

  const id = itinerarioSeleccionado.value._id || itinerarioSeleccionado.value.id
  const payload = {
    title: itineraryTitle.value,
    content: markdownText.value
  }

  try {
    await api.put(`/api/itinerary/${id}`, payload)
    
    ultimoTituloGuardado.value = itineraryTitle.value
    ultimoTextoGuardado.value = markdownText.value
    guardadoExitoso.value = true
    
    if (itinerarioSeleccionado.value) {
      itinerarioSeleccionado.value.title = itineraryTitle.value
      itinerarioSeleccionado.value.content = markdownText.value
    }

    setTimeout(() => {
      guardadoExitoso.value = false
    }, 3000)
  } catch (error) {
    console.error('Error al guardar el itinerario:', error)
  } finally {
    estaGuardando.value = false
  }
}

const volverAlListado = (): void => {
  if (hayCambiosSinGuardar.value && !confirm('Tienes cambios sin guardar. ¿Deseas salir de todas formas?')) {
    return
  }
  itinerarioSeleccionado.value = null
}

const marcarComoPredeterminado = async (itinerario: Itinerary, event: Event): Promise<void> => {
  // Evitamos que al hacer clic en el botón se dispare también el clic de la tarjeta (seleccionar)
  event.stopPropagation()
  
  const id = itinerario._id || itinerario.id
  try {
    await api.patch(`/api/itinerary/${id}/default`)
    
    // Sincronizamos el estado reactivo local en memoria al instante
    listaItinerarios.value.forEach((item) => {
      item.is_default = (item._id === id || item.id === id)
    })
  } catch (error) {
    console.error('Error al establecer itinerario por defecto:', error)
    alert('No se pudo guardar la preferencia.')
  }
}

onMounted(() => {
  cargarItinerarios()
})
</script>

<template>
  <div style="max-width: 1200px; width: 100%; margin: 0 auto; padding: 20px; font-family: sans-serif; box-sizing: border-box;">
    
    <!-- ==================== VISTA 1: LISTADO DE ITINERARIOS ==================== -->
    <div v-if="!itinerarioSeleccionado">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; border-bottom: 1px solid #ccc; padding-bottom: 15px;">
        <div>
          <h1 style="margin: 0; font-size: 26px; color: #1a1a1a;">Mis Itinerarios</h1>
          <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">Selecciona un plan de viaje para editarlo o compartirlo.</p>
        </div>
        <button 
          @click="crearNuevoItinerario"
          style="padding: 12px 24px; background: #2563eb; color: white; border: none; font-weight: bold; border-radius: 8px; cursor: pointer;"
        >
          + Crear Itinerario 📝
        </button>
      </div>

      <div v-if="cargandoLista" style="text-align: center; padding: 40px; color: #666; font-size: 16px;">
        Cargando tus planes de viaje...⏳
      </div>

      <div v-else-if="listaItinerarios.length > 0" class="grid-itinerarios">
        <div 
          v-for="item in listaItinerarios" 
          :key="item._id || item.id"
          @click="seleccionarItinerario(item)"
          class="tarjeta-itinerario"
          :style="item.is_default ? 'border-color: #eab308; background: #fefce8;' : ''"
        >
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="font-size: 32px; margin-bottom: 10px;">🗺️</div>
            <!-- ⚡ INDICADOR ESTRELLA SI ES EL PREDETERMINADO -->
            <span v-if="item.is_default" style="font-size: 20px; title: 'Itinerario activo por defecto'">⭐</span>
          </div>

          <h3 style="margin: 0 0 8px 0; font-size: 18px; color: #111; word-break: break-word;">
            {{ item.title || 'Itinerario sin título 📝' }}
          </h3>
          
          <p style="margin: 0; font-size: 13px; color: #666; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
            {{ (item.content || '').replace(/[#*`]/g, '') || 'Sin descripción...' }}
          </p>
          
          <!-- CONTENEDOR DE ACCIONES INFERIORES DE LA TARJETA -->
          <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 11px; color: #999;">
              Usuarios: {{ item.users?.length || 0 }}
            </div>

            <!-- ⚡ BOTÓN DINÁMICO RECTIVO -->
            <button
              @click="(e) => marcarComoPredeterminado(item, e)"
              :disabled="item.is_default"
              :style="item.is_default 
                ? 'padding: 6px 12px; font-size: 12px; background: #eab308; color: white; border: none; border-radius: 6px; font-weight: bold;' 
                : 'padding: 6px 12px; font-size: 12px; background: #f3f4f6; color: #4b5563; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-weight: bold;'"
            >
              {{ item.is_default ? 'Activo ✓' : 'Fijar Principal 📌' }}
            </button>
          </div>
        </div>
      </div>

      <div v-else style="text-align: center; padding: 60px 20px; border: 2px dashed #ccc; border-radius: 12px; background: #fafafa; color: #666;">
        <p style="font-size: 18px; margin: 0 0 10px 0; font-weight: bold;">No tienes itinerarios creados</p>
        <p style="margin: 0 0 20px 0; font-size: 14px;">¡Crea tu primer plan de viaje para sincronizarlo con la IA!</p>
      </div>
    </div>

    <!-- ==================== VISTA 2: EDITOR Y DETALLE ==================== -->
    <div v-else>
  <!-- Cabecera del Editor (Se mantiene visible para poder volver atrás) -->
  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #ccc; padding-bottom: 15px; flex-wrap: wrap; gap: 15px;">
    <div style="display: flex; align-items: center; gap: 15px; flex: 1; min-width: 280px;">
      <button @click="volverAlListado" style="padding: 10px 14px; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; font-weight: bold;">
        ⬅️ Volver
      </button>
      <div style="flex: 1;">
        <input v-model="itineraryTitle" :disabled="cargandoDetalle" type="text" style="width: 100%; font-size: 22px; font-weight: bold; border: 1px dashed #ccc; padding: 4px 8px; border-radius: 6px; box-sizing: border-box; color: #1a1a1a;" placeholder="Título del itinerario"/>
      </div>
    </div>
    
    <div style="display: flex; align-items: center; gap: 10px;" v-if="!cargandoDetalle">
      <span v-if="hayCambiosSinGuardar && !estaGuardando" style="color: #e11d48; font-weight: bold; font-size: 13px; background: #fff1f2; padding: 6px 12px; border-radius: 6px; border: 1px solid #ffe4e6;">⚠️ Cambios sin guardar</span>
      <span v-if="guardadoExitoso" style="color: #16a34a; font-weight: bold; font-size: 13px; background: #f0fdf4; padding: 6px 12px; border-radius: 6px; border: 1px solid #dcfce7;">¡Guardado! ✅</span>
      <button @click="guardarItinerario" :disabled="estaGuardando" style="padding: 10px 20px; background: #059669; color: white; border: none; font-weight: bold; border-radius: 8px; cursor: pointer; min-width: 140px;">
        {{ estaGuardando ? 'Guardando...' : 'Guardar 💾' }}
      </button>
    </div>
  </div>

  <!-- 📥 ESTADO DE CARGA INTERNO DEL DETALLE -->
  <div v-if="cargandoDetalle" style="text-align: center; padding: 80px; color: #666; font-size: 16px;">
    Descargando mapas y planes de viaje... 📜✈️
  </div>

  <!-- Panel Dividido (Solo se renderiza cuando los datos de red están listos) -->
  <div v-else class="panel-layout">
    <div>
      <textarea v-model="markdownText" style="width: 100%; height: 500px; padding: 15px; background: #1e1e1e; color: #f4f4f4; font-family: monospace; font-size: 14px; border-radius: 8px; border: 1px solid #333; resize: none; box-sizing: border-box;"></textarea>
    </div>
    <div class="columna-preview" style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #fff; height: 500px; overflow-y: auto; box-sizing: border-box;">
      <div v-html="htmlPreview" class="markdown-body"></div>
    </div>
  </div>
</div>

  </div>
</template>

<style scoped>
.grid-itinerarios {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.tarjeta-itinerario {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.tarjeta-itinerario:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.panel-layout {
  display: grid; 
  grid-template-columns: 1fr 1fr; 
  gap: 20px;
}

.columna-preview {
  display: block;
}

@media (max-width: 768px) {
  .panel-layout {
    grid-template-columns: 1fr;
  }

  .columna-preview {
    display: none;
  }
}

.markdown-body :deep(h1) { font-size: 22px; margin-top: 0; color: #111; border-bottom: 1px solid #eee; padding-bottom: 5px; }
.markdown-body :deep(h2) { font-size: 18px; margin-top: 15px; color: #222; }
.markdown-body :deep(ul) { padding-left: 20px; margin-bottom: 10px; }
.markdown-body :deep(li) { margin-bottom: 5px; color: #333; }
.markdown-body :deep(strong) { color: #000; font-weight: bold; }
</style>
