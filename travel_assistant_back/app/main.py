import os
from http.client import HTTPException
from typing import Optional

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager  # <-- 1. Importación para el administrador de contexto

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette import status

from app.routers import chat, itinerary
from app.database import ping_database

security = HTTPBasic()


def verificar_credenciales_docs(credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    """
    Dependencia inteligente: Si NO existen las variables en el entorno (.env),
    se salta la seguridad (ideal para desarrollo local). En producción (Render),
    exige usuario y contraseña obligatorios.
    """
    correct_username = os.getenv("DOCS_USERNAME")
    correct_password = os.getenv("DOCS_PASSWORD")

    if not correct_username or not correct_password:
        return "development_mode"

    if credentials is None or credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos para acceder a la documentación",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

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
    lifespan=lifespan,  # <-- Vinculamos el gestor de ciclo de vida aquí
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Configuración de CORS
origins = [
    frontend_url,
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

# --- 🔒 ENDPOINTS PROTEGIDOS DE DOCUMENTACIÓN CORREGIDOS ---

@app.get("/docs", include_in_schema=False)
async def get_documentation(_: str = Depends(verificar_credenciales_docs)): # <-- Cambiado 'username' por '_'
    """Muestra la interfaz de Swagger pidiendo primero usuario y contraseña"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI"
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(_: str = Depends(verificar_credenciales_docs)): # <-- Cambiado 'username' por '_'
    """Protege también el archivo JSON interno que estructura el mapa de las APIs"""
    return get_openapi(title=app.title, version=app.version, routes=app.routes)




@app.get("/")
def read_root():
    return {"status": "ok", "message": "Servidor de Travel Assistant funcionando correctamente"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
