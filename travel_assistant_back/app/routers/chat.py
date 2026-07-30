import asyncio
from fastapi import APIRouter, Query, HTTPException
from sse_starlette.sse import EventSourceResponse
from google.genai import client
from google.oauth2.credentials import Credentials

router = APIRouter()


@router.get("/chat/stream")
async def chat_stream(
        mensaje: str = Query(..., description="Consulta del usuario"),
        token: str = Query(..., description="Token de acceso OAuth2 de Google")
):
    if not token:
        raise HTTPException(status_code=401, detail="Se requiere el token de Google para consumir tu cuota")

    async def generador_gemini():
        try:
            # 1. Empaquetamos el token de la Cloud Platform en el objeto de credenciales
            user_credentials = Credentials(token=token)

            # 2. Inicializamos el cliente oficial pasándole los permisos del usuario de forma directa
            ai_client = client.Client(credentials=user_credentials)

            # 3. Solicitamos el streaming a Gemini usando el token del cliente
            response_stream = ai_client.models.generate_content_stream(
                model='gemini-2.5-flash',
                contents=mensaje
            )

            # 4. Inyectamos las palabras en tiempo real al chat de Vue
            for chunk in response_stream:
                if chunk.text:
                    yield f"{chunk.text}"
                await asyncio.sleep(0.01)

            # Token de cierre que programamos en el Front
            yield "[DONE]"

        except Exception as e:
            yield f"⚠️ Error en tu cuota de Google Cloud / Gemini API: {str(e)}"
            yield "[DONE]"

    headers = {
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    return EventSourceResponse(generador_gemini(), headers=headers)
