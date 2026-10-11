# travel_assistant_back/app/routers/chat.py
import asyncio
import os

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from bson import ObjectId
from sse_starlette.sse import EventSourceResponse
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from app.services.gemini_fallback import (
    GEMINI_MODELS,
    es_error_cuota_diaria,
    es_error_temporal_503,
    marcar_agotado,
    modelo_agotado,
)

from app.database import db
from app.dependencies import get_current_user_email

router = APIRouter(prefix="/chat", tags=["Chat"])


# ⚡ ESQUEMA DE ENTRADA PARA EL CUERPO DEL POST
class ChatStreamRequest(BaseModel):
    message: str = Field(..., description="Mensaje o pregunta del usuario")
    token: str = Field(..., description="Access token de Google OAuth")
    itinerary_id: str = Field("", description="ID del itinerario activo como contexto")


@router.post("/stream")
async def chat_stream(payload: ChatStreamRequest):
    """
    Endpoint POST asíncrono definitivo y limpio. Inyecta el token dinámico del usuario
    directamente en las opciones HTTP de la llamada al modelo, sin instanciar clientes efímeros.
    """

    # 1. Validamos asíncronamente el token del usuario contra UserInfo de Google
    try:
        user_email = await get_current_user_email(token_query=payload.token)
    except HTTPException as ex:
        async def auth_error_generator():
            yield dict(data=f"Error de autenticación: {ex.detail}")
            yield dict(data="[DONE]")

        return EventSourceResponse(auth_error_generator())

    # 2. Empaquetamos el token del payload en un objeto Credentials legítimo para Google
    try:
        ai_client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )
    except Exception as ex:
        error_msg = str(ex)

        async def init_error_generator():
            yield dict(data=f"Error al procesar credenciales de Google: {error_msg}")
            yield dict(data="[DONE]")

        return EventSourceResponse(init_error_generator())

    # 3. Extracción asíncrona del contexto de viaje en MongoDB Atlas con Motor
    itinerary_content = ""
    itinerary_title = "Sin itinerario seleccionado"

    if payload.itinerary_id and ObjectId.is_valid(payload.itinerary_id):
        doc = await db.itinerary.find_one({
            "_id": ObjectId(payload.itinerary_id),
            "users": user_email
        })
        if doc:
            itinerary_title = doc.get("title", "Viaje")
            itinerary_content = doc.get("content", "")

    # 4. Generador de Eventos SSE asíncronos y no bloqueantes

    async def event_generator():
        try:
            system_instruction = (
                "Eres un Asistente de Viajes experto.\n"
                f"El usuario está consultando sobre su viaje titulado: '{itinerary_title}'.\n"
                "Utiliza el siguiente itinerario en formato Markdown como contexto absoluto para responder:\n\n"
                f"{itinerary_content}\n\n"
                "Responde siempre usando Markdown amigable para lectura."
            )

            config_llamada = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.5,
            )

            # Probamos los modelos por orden de prioridad.
            for modelo in GEMINI_MODELS:
                if modelo_agotado(modelo):
                    continue
                texto_emitido = False
                try:
                    response_stream = (
                        await ai_client.aio.models.generate_content_stream(
                            model=modelo,
                            contents=payload.message,
                            config=config_llamada,
                        )
                    )
                    async for chunk in response_stream:
                        if chunk.text:
                            texto_emitido = True
                            yield {"data": chunk.text}
                            await asyncio.sleep(0.01)
                    # El modelo terminó correctamente.
                    return
                except Exception as ex_ia:
                    if es_error_cuota_diaria(ex_ia):
                        marcar_agotado(modelo)
                        if not texto_emitido:
                            continue
                    elif es_error_temporal_503(ex_ia):
                        # Error temporal de disponibilidad:
                        # probamos el siguiente modelo, sin guardarlo
                        # en la caché diaria.
                        if not texto_emitido:
                            print(
                                f"Modelo {modelo} no disponible (503). "
                                "Probando el siguiente modelo."
                            )
                            continue

                    print(f"Error con el modelo {modelo}: {ex_ia}")
                    yield {
                        "data": (
                            "\n[No se ha podido completar la respuesta. "
                            "Inténtalo de nuevo más tarde.]"
                        )
                    }
                    return

            # Todos los modelos están marcados como agotados.
            yield {
                "data": (
                    "\nSe ha alcanzado la cuota diaria de los modelos "
                    "disponibles. Inténtalo de nuevo mañana."
                )
            }

        except Exception as ex_ia:
            print(f"Error en el generador del chat: {ex_ia}")
            yield {
                "data": "\n[Se ha producido un error al generar la respuesta.]"
            }

        finally:
            yield {"data": "[DONE]"}


    # Headers críticos para evitar que Render congele el streaming en búfer
    headers = {
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    return EventSourceResponse(event_generator(), headers=headers)
