
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Load environment variables from .env
load_dotenv()

# Use Atlas in production and local MongoDB during development
MONGO_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://127.0.0.1:27017"
)

# Create MongoDB client
client = MongoClient(
    MONGO_URL,
    server_api=ServerApi("1"),
    serverSelectionTimeoutMS=5000
)

# Connect to project database
db = client["airbnb_trip_db"]

# Test database connection
try:
    client.admin.command("ping")
    print("MongoDB Connected Successfully!")

except Exception as e:
    print("MongoDB Connection Failed:", e)
