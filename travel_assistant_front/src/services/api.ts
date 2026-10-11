// travel_assistant_front/src/services/api.ts
import axios from 'axios'
import router from '../router'

const api = axios.create({
  baseURL: (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, ''),
})

// Variables de control para evitar bucles infinitos si el refresco falla de verdad
let estaRefrescandoToken = false
let peticionesEnEspera: any[] = []

const procesarPeticionesEnEspera = (token: string | null) => {
  peticionesEnEspera.forEach((callback) => callback(token))
  peticionesEnEspera = []
}

// 1. Interceptor de Petición (Inyecta el token actual si existe)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('google_access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

// 2. Interceptor de Respuesta (Captura el 401 y refresca en segundo plano)
api.interceptors.response.use(
  (response) => response, // Si la petición va bien (200 OK), pasa directo
  async (error) => {
    const originalRequest = error.config

    // Si el back devuelve 401 y no es una petición que ya se haya reintentado
    if (error.response?.status === 401 && !originalRequest._retry) {
      
      // Si la petición fallida era el propio login, no reintentamos para evitar bucles
      if (originalRequest.url?.includes('/login')) {
        return Promise.reject(error)
      }

      if (estaRefrescandoToken) {
        // Si ya hay una petición de refresco en marcha, encolamos esta petición hasta que termine
        return new Promise((resolve) => {
          peticionesEnEspera.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(api(originalRequest))
          })
        })
      }

      // Marcamos que iniciamos el proceso de refresco
      originalRequest._retry = true
      estaRefrescandoToken = true

      try {
        // Solicitamos a Google un nuevo token de forma silenciosa mediante su SDK nativo global
        const nuevoToken = await ejecutarRefrescoSilenciosoGoogle()
        
        if (nuevoToken) {
          localStorage.setItem('google_access_token', nuevoToken)
          
          // Desbloqueamos las peticiones que se quedaron esperando en la cola
          procesarPeticionesEnEspera(nuevoToken)
          
          // Reejecutamos la petición original fallida con el token fresco
          originalRequest.headers.Authorization = `Bearer ${nuevoToken}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        console.error('El refresco silencioso de Google ha fallado:', refreshError)
        
        // Si el refresco falla de verdad (ej. el usuario revocó permisos), limpiamos y mandamos a login
        localStorage.removeItem('google_access_token')
        router.push('/login')
      } finally {
        estaRefrescandoToken = false
      }
    }

    return Promise.reject(error)
  }
)

/**
 * Utiliza el SDK de Google de la ventana global para pedir un token nuevo
 * sin levantar ventanas emergentes (pop-ups) si el usuario ya concedió acceso.
 */
function ejecutarRefrescoSilenciosoGoogle(): Promise<string | null> {
  return new Promise((resolve, reject) => {
    
    // Función interna para lanzar la petición a Google
    const solicitarToken = () => {
      try {
        const tokenClient = (window as any).google.accounts.oauth2.initTokenClient({
          client_id: 'TU_CLIENT_ID_DE_://googleusercontent.com', // Reemplaza con tu Client ID real
          scope: 'email email profile https://www.googleapis.com/auth/cloud-platform',
          prompt: 'none', // Invisible para el usuario
          callback: (response: any) => {
            if (response.error) {
              reject(response);
            } else if (response.access_token) {
              resolve(response.access_token);
            } else {
              resolve(null);
            }
          },
        });
        tokenClient.requestAccessToken();
      } catch (e) {
        reject(e);
      }
    };

    // Comprobamos si el SDK ya se descargó e instanció
    if ((window as any).google?.accounts?.oauth2) {
      solicitarToken();
    } else {
      // Si el script aún está descargándose, esperamos un instante y reintentamos
      let intentos = 0;
      const interval = setInterval(() => {
        intentos++;
        if ((window as any).google?.accounts?.oauth2) {
          clearInterval(interval);
          solicitarToken();
        } else if (intentos > 10) { // Si pasa más de un segundo, fallamos
          clearInterval(interval);
          reject(new Error('SDK de Google no disponible tras esperar descarga'));
        }
      }, 100);
    }
  });
}


export default api
