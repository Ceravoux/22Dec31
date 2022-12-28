from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticCollection
from dotenv import load_dotenv
from os import getenv
load_dotenv()

client = AsyncIOMotorClient(getenv("DB_KEY"), serverSelectionTimeoutMS=5000)
try:
    database: AgnosticCollection = client["project"]["project01"]
except Exception as e:
    print(f"{e}; Unable to connect to the server.")

# HACK: create TTL index