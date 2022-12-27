from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection
from dotenv import load_dotenv
from os import getenv
load_dotenv()

client = AsyncIOMotorClient(getenv("DB_KEY"), serverSelectionTimeoutMS=5000)
try:
    DATABASE: Collection = client["project"]["project01"]
except Exception as e:
    print(f"{e}: Unable to connect to the server.")