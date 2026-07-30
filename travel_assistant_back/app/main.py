from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager  # <-- 1. Importación para el administrador de contexto
from app.routers import chat, itinerary
from app.database import ping_database


# --- 2. CONFIGURACIÓN DEL MANEJADOR LIFESPAN MODERNO ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Todo el código que pongas ANTES del 'yield' se ejecutará al ARRANCAR la API
    print("🚀 Iniciando el ciclo de vida de la aplicación...")
    await ping_database()

    yield  # <-- El servidor se queda aquí "escuchando" peticiones de Vue

    # Todo el código que pongas DESPUÉS del 'yield' se ejecutará al APAGAR el servidor
    print("🛑 Cerrando el ciclo de vida de la aplicación... Limpiando recursos.")


# --- 3. PASAMOS EL LIFESPAN AL INICIALIZAR FASTAPI ---
app = FastAPI(
    title="Travel Assistant API",
    description="Backend en FastAPI para el asistente de viajes inteligente",
    version="1.0.0",
    lifespan=lifespan  # <-- Vinculamos el gestor de ciclo de vida aquí
)

# Configuración de CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enrutadores modulares de la aplicación
app.include_router(chat.router, prefix="/api")
app.include_router(itinerary.router, prefix="/api")


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Servidor de Travel Assistant funcionando correctamente"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
