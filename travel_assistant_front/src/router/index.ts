import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import ItineraryView from '../views/ItineraryView.vue'
import LoginView from '../views/LoginView.vue' // <-- 1. Importamos la vista de Login

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/',
      name: 'chat',
      component: ChatView,
      meta: { requiresAuth: true } // <-- Indicamos que esta ruta requiere login
    },
    {
      path: '/itinerario',
      name: 'itinerary',
      component: ItineraryView,
      meta: { requiresAuth: true } // <-- Indicamos que esta ruta requiere login
    },
  ],
})

// --- 2. EL GUARDIÁN DE RUTAS (Navigation Guard) ---
router.beforeEach((to, from, next) => {
  // Buscamos si el token de acceso de Google está guardado en el navegador
  const isAuthenticated = !!localStorage.getItem('google_access_token')

  // Si la ruta requiere autenticación y el usuario NO está logueado...
  if (to.meta.requiresAuth && !isAuthenticated) {
    // Lo redirigimos a la fuerza a la pantalla de login
    next({ name: 'login' })
  } else if (to.name === 'login' && isAuthenticated) {
    // Si ya está logueado e intenta ir al login, lo mandamos al chat
    next({ name: 'chat' })
  } else {
    // En cualquier otro caso, le dejamos pasar libremente
    next()
  }
})

export default router
