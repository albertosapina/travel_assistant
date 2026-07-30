from fastapi import APIRouter, HTTPException, status, Query
from bson import ObjectId
from typing import List
from app.database import db

from datetime import datetime

from app.schemas.itinerary import ItineraryDetail, ItineraryCreate, ItineraryListItem, ItineraryUpdate, AddUserPayload

router = APIRouter(prefix="/itinerary", tags=["Itineraries"])


@router.post("/", response_model=ItineraryDetail, status_code=status.HTTP_201_CREATED)
async def create_itinerary(payload: ItineraryCreate):
    """Crea un nuevo itinerario transformando el email del creador en una lista en la BD"""
    itinerary_dict = payload.model_dump()

    # Extraemos el email del creador y lo transformamos en la lista inicial de usuarios
    creador = itinerary_dict.pop("creator_email")
    itinerary_dict["users"] = [creador]

    ahora = datetime.utcnow()
    itinerary_dict["created_at"] = ahora
    itinerary_dict["updated_at"] = ahora

    # Guardamos en la colección 'itinerary' (ya renombrada)
    result = await db["itinerary"].insert_one(itinerary_dict)

    new_itinerary = await db["itinerary"].find_one({"_id": result.inserted_id})
    return new_itinerary


@router.get("/", response_model=List[ItineraryListItem])
async def list_itineraries(user_email: str = Query(..., description="Email del usuario para filtrar sus viajes")):
    """Devuelve los itinerarios (ID y Título) donde el email del usuario esté autorizado"""
    # Usamos el operador nativo de Mongo. Si 'users' es una lista,
    # Mongo busca de forma automática si el 'user_email' coincide con algún elemento de ella.
    cursor = db["itinerary"].find({"users": user_email}, {"title": 1})
    itineraries = await cursor.to_list(length=100)
    return itineraries


@router.get("/{itinerary_id}", response_model=ItineraryDetail)
async def get_itinerary_detail(itinerary_id: str,
                               user_email: str = Query(..., description="Email para validar acceso")):
    """Devuelve el detalle de un itinerario validando previamente que el usuario tenga acceso"""
    if not ObjectId.is_valid(itinerary_id):
        raise HTTPException(status_code=400, detail="El formato del ID de MongoDB no es válido")

    itinerary = await db["itinerary"].find_one({"_id": ObjectId(itinerary_id)})
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerario no encontrado")

    # 🔒 CAPA DE SEGURIDAD INTERNA DEL BACKEND
    # Verificamos si el email que solicita el viaje se encuentra dentro de la lista 'users'
    if user_email not in itinerary.get("users", []):
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este itinerario")

    return itinerary


@router.put("/{itinerary_id}", response_model=ItineraryDetail)
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
    return updated_itinerary

@router.put("/{itinerary_id}/share", response_model=ItineraryDetail)
async def share_itinerary(
    itinerary_id: str,
    payload: AddUserPayload,
    user_email: str = Query(..., description="Email del usuario que realiza la acción de compartir")
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
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    # 4. Devolvemos el itinerario actualizado con los nuevos miembros de la lista
    updated_itinerary = await db["itinerary"].find_one({"_id": ObjectId(itinerary_id)})
    return updated_itinerary
