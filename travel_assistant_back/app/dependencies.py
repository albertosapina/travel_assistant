# travel_assistant_back/app/dependencies.py
import httpx
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user_email(
        credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
        token_query: str = None
) -> str:
    """
    Valida el access_token de Google de forma 100% asíncrona.
    Soporta inyección automática vía cabeceras HTTP (REST) o invocación manual (POST body).
    """
    token = None

    # ⚡ SOLUCIÓN AL TYPEERROR (Duck Typing Senior):
    # Si credentials es un objeto real inyectado y tiene la propiedad 'credentials' (el string del token)
    if credentials and hasattr(credentials, "credentials"):
        token = credentials.credentials

    # Si se pasa explícitamente por el cuerpo del POST o Query String (Caso del Chat)
    if token_query:
        token = token_query

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación ausente o malformado"
        )

    # El resto de tu lógica asíncrona de httpx se queda exactamente igual
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                params={"access_token": token},
                timeout=5.0
            )

        if res.status_code == 200:
            data = res.json()
            email = data.get("email")
            if email:
                return email

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token de Google ha expirado o es inválido"
        )

    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Error de red asíncrono al conectar con Google Identity"
        )
