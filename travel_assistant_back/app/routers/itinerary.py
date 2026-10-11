from fastapi import APIRouter, HTTPException, status, Query, Depends
from bson import ObjectId
from typing import List
from app.database import db

from datetime import datetime

from app.dependencies import get_current_user_email
from app.schemas.itinerary import ItineraryItem, ItineraryListItem, ItineraryCreate, ItineraryUpdate, AddUserPayload

router = APIRouter(prefix="/itinerary", tags=["Itineraries"], dependencies=[Depends(get_current_user_email)] )


@router.post("", response_model=ItineraryItem, status_code=status.HTTP_201_CREATED)
async def create_itinerary(payload: ItineraryCreate, creator_email: str = Depends(get_current_user_email)):
    """Crea un nuevo itinerario transformando el email del creador en una lista en la BD"""
    ahora = datetime.now()

    # Construimos el documento asumiendo la herencia de auditoría requerida
    nuevo_itinerario = {
        "title": payload.title,
        "content": payload.content,
        "users": [creator_email],  # El back transforma el string del creador en lista atómica
        "is_default": False,
        "created_at": ahora,
        "updated_at": ahora
    }

    # Inserción asíncrona no bloqueante mediante Motor
    result = await db.itinerary.insert_one(nuevo_itinerario)

    # Adjuntamos el ID generado para retornar el objeto completo al cliente Vue
    nuevo_itinerario["_id"] = str(result.inserted_id)
    return nuevo_itinerario


@router.get("", response_model=List[ItineraryListItem])
async def list_itineraries(user_email: str = Depends(get_current_user_email)):
    """Devuelve los itinerarios (ID y Título) donde el email del usuario esté autorizado"""
    pref = await db.user_preferences.find_one({"user_email": user_email})
    default_id = str(pref.get("default_itinerary_id")) if pref else None

    cursor = db.itinerary.find({"users": user_email}, {"content": 0})
    itinerarios = []

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["is_default"] = (doc["_id"] == default_id)
        itinerarios.append(doc)

    return itinerarios


@router.get("/{itinerary_id}", response_model=ItineraryItem)
async def get_itinerary_detail(itinerary_id: str,
                               user_email: str = Depends(get_current_user_email)):
    """Devuelve el detalle de un itinerario validando previamente que el usuario tenga acceso"""
    if not ObjectId.is_valid(itinerary_id):
        raise HTTPException(status_code=400, detail="El formato del ID de MongoDB no es válido")

    itinerary = await db["itinerary"].find_one({"_id": ObjectId(itinerary_id)})
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")
    itinerary["_id"] = str(itinerary["_id"])

    # 🔒 CAPA DE SEGURIDAD INTERNA DEL BACKEND
    # Verificamos si el email que solicita el viaje se encuentra dentro de la lista 'users'
    if user_email not in itinerary.get("users", []):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este itinerario")

    return itinerary


@router.put("/{itinerary_id}", response_model=ItineraryItem)
async def update_itinerary(itinerary_id: str, payload: ItineraryUpdate):
    """Actualiza los campos del itinerario y renueva su 'updated_at'"""
    if not ObjectId.is_valid(itinerary_id):
        raise HTTPException(status_code=400, detail="El formato del ID de MongoDB no es válido")

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No se enviaron campos válidos para actualizar")

    update_data["updated_at"] = datetime.utcnow()

    result = await db["itinerary"].update_one(
        {"_id": ObjectId(itinerary_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    updated_itinerary = await db["itinerary"].find_one({"_id": ObjectId(itinerary_id)})
    updated_itinerary["_id"] = str(updated_itinerary["_id"])
    return updated_itinerary

@router.put("/{itinerary_id}/share", response_model=ItineraryItem)
async def share_itinerary(
    itinerary_id: str,
    payload: AddUserPayload,
    user_email: str = Depends(get_current_user_email)
):
    """Añade un nuevo email a la lista 'users' del itinerario si el solicitante tiene permisos"""
    if not ObjectId.is_valid(itinerary_id):
        raise HTTPException(status_code=400, detail="El formato del ID de MongoDB no es válido")

    # 1. Buscamos el itinerario para verificar si existe y comprobar los permisos
    itinerary = await db["itinerary"].find_one({"_id": ObjectId(itinerary_id)})
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    # 2. 🔒 Validación de Seguridad: Solo un usuario ya autorizado puede invitar a otros
    if user_email not in itinerary.get("users", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para compartir este itinerario"
        )

    # 3. Modificamos el documento en Mongo Atlas
    # '$addToSet' añade el email a la lista como si fuera un conjunto (Set), garantizando que no haya duplicados
    # '$set' actualiza la fecha de auditoría obligatoria de tu base de datos
    result = await db["itinerary"].update_one(
        {"_id": ObjectId(itinerary_id)},
        {
            "$addToSet": {"users": payload.email_to_add},
            "$set": {"updated_at": datetime.now()}
        }
    )

    # 4. Devolvemos el itinerario actualizado con los nuevos miembros de la lista
    updated_itinerary = await db["itinerary"].find_one({"_id": ObjectId(itinerary_id)})
    updated_itinerary["_id"] = str(updated_itinerary["_id"])
    return updated_itinerary

@router.patch("/{itinerary_id}/default")
async def set_default_itinerary(
    itinerary_id: str,
    user_email: str = Depends(get_current_user_email)
):
    if not ObjectId.is_valid(itinerary_id):
        raise HTTPException(status_code=400, detail="ID de itinerario inválido")

    # Validamos que el itinerario al que apunta realmente tiene acceso el usuario
    itinerario = await db.itinerary.find_one({
        "_id": ObjectId(itinerary_id),
        "users": user_email
    })
    if not itinerario:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado o sin acceso")

    ahora = datetime.now()

    # ⚡ OPERACIÓN ATÓMICA DE PREFERENCIAS:
    # Guarda una única fila por usuario. Si no existe, la crea (upsert=True)
    await db.user_preferences.update_one(
        {"user_email": user_email},
        {
            "$set": {
                "default_itinerary_id": itinerary_id,
                "updated_at": ahora
            }
        },
        upsert=True
    )

    return {"status": "success", "message": "Tu itinerario predeterminado privado ha sido actualizado"}
