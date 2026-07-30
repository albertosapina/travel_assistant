from typing import Optional, Annotated, List

from pydantic import BaseModel, Field, BeforeValidator

from app.schemas.mongo_base_model import MongoBaseModel


PyObjectId = Annotated[str, BeforeValidator(str)]

class ItineraryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, example="Mi viaje a París")
    content: str = Field(..., example="# Detalles del viaje...")
    # Recibe el string del email del creador desde el Frontend de Vue
    creator_email: str = Field(..., example="creador@gmail.com")

class ItineraryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = None
    # Permite en el futuro añadir o modificar la lista de usuarios con acceso
    users: Optional[List[str]] = None

class ItineraryListItem(BaseModel):
    id: PyObjectId = Field(alias="_id")
    title: str

    class Config:
        populate_by_name = True

class ItineraryDetail(MongoBaseModel):
    id: PyObjectId = Field(alias="_id")
    title: str
    content: str
    # La respuesta detallada ahora incluye la lista completa de emails autorizados
    users: List[str] = Field(default_factory=[])

    class Config:
        populate_by_name = True

class AddUserPayload(BaseModel):
    """Modelo para validar el email que se desea invitar al itinerario"""
    email_to_add: str = Field(..., example="amigo@gmail.com")

