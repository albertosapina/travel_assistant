from datetime import datetime

from pydantic import BaseModel, Field


class MongoBaseModel(BaseModel):
    """Clase Base abstracta. Todos los modelos que hereden de aquí
    tendrán fechas de auditoría automáticas."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)