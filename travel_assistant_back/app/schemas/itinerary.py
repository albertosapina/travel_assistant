from datetime import datetime
from typing import Annotated, List

from pydantic import BaseModel, Field, BeforeValidator


PyObjectId = Annotated[str, BeforeValidator(str)]

class ItineraryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str

class ItineraryCreate(ItineraryBase):
    pass

class ItineraryUpdate(ItineraryBase):
    pass

# Esquema de respuesta para el cliente Vue 3
class ItineraryListItem(BaseModel):
    id: str = Field(..., alias="_id")
    title: str = Field(..., min_length=1, max_length=100)
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class ItineraryItem(BaseModel):
    id: str = Field(..., alias="_id")
    content: str
    users: List[str]
    title: str
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class AddUserPayload(BaseModel):
    """Modelo para validar el email que se desea invitar al itinerario"""
    email_to_add: str = Field(..., example="amigo@gmail.com")

