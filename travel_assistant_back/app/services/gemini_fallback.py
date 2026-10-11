
# app/services/gemini_fallback.py

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from google.genai import errors

# Ajusta los modelos a los que estén disponibles en tu proyecto.
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.0-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash"
    "gemini-2.5-flash-lite",
]

PACIFIC = ZoneInfo("America/Los_Angeles")

# Caché local: fecha de cuota -> modelos con cuota diaria agotada.
_fecha_cache = None
_modelos_agotados: set[str] = set()

def es_error_temporal_503(error: Exception) -> bool:
    return getattr(error, "code", None) == 503


def _actualizar_dia() -> None:
    """Vacía la caché cuando cambia el día en horario del Pacífico."""
    global _fecha_cache, _modelos_agotados

    hoy = datetime.now(PACIFIC).date()

    if _fecha_cache != hoy:
        _fecha_cache = hoy
        _modelos_agotados = set()


def modelo_agotado(modelo: str) -> bool:
    _actualizar_dia()
    return modelo in _modelos_agotados


def marcar_agotado(modelo: str) -> None:
    _actualizar_dia()
    _modelos_agotados.add(modelo)


def modelos_disponibles() -> list[str]:
    _actualizar_dia()
    return [
        modelo for modelo in GEMINI_MODELS
        if modelo not in _modelos_agotados
    ]


def es_error_cuota_diaria(error: Exception) -> bool:
    """Clasifica errores 429 como diarios solo con indicios suficientes."""
    codigo = getattr(error, "code", None)
    mensaje = str(error).lower()

    if codigo != 429:
        return False

    indicios_diarios = (
        "quota_exceeded",
        "per day",
        "per_day",
        "daily quota",
        "requests per day",
        "perday",
    )

    return any(indicio in mensaje for indicio in indicios_diarios)


def es_error_temporal_de_limite(error: Exception) -> bool:
    """Reconoce indicios de límites por minuto/segundo."""
    codigo = getattr(error, "code", None)
    mensaje = str(error).lower()

    if codigo != 429:
        return False

    indicios_temporales = (
        "rate_limit_exceeded",
        "too_many_requests",
        "per minute",
        "per second",
        "per_minute",
        "retry after",
    )

    return any(indicio in mensaje for indicio in indicios_temporales)
