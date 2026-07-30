import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Cargamos las variables del archivo .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "travel_assistant")

# Inicializamos el cliente asíncrono de Motor
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def ping_database():
    """Función auxiliar para verificar que la conexión con Atlas está viva"""
    try:
        # El comando ping requiere una respuesta rápida de Atlas
        await db.command("ping")
        print(" Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ Error connecting to MongoDB Atlas: {e}")
