import { createApp } from 'vue'
import './assets/main.css'
import App from './App.vue'
import router from './router'
// 1. Importas la librería
import GoogleSignInPlugin from 'vue3-google-signin' 

const app = createApp(App)
const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

console.log('Google Client ID configurado:', Boolean(clientId));

app.use(GoogleSignInPlugin, {
  clientId: clientId,
})

app.use(router)

app.mount('#app')
