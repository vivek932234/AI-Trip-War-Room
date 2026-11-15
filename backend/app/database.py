
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection URL
MONGO_URL = "mongodb://127.0.0.1:27017"

# Create MongoDB client
client = MongoClient(
    MONGO_URL,
    server_api=ServerApi("1")
)

# Connect to our project database
db = client["airbnb_trip_db"]

# Test database connection
try:
    client.admin.command("ping")
    print("MongoDB Connected Successfully!")

except Exception as e:
    print("MongoDB Connection Failed:", e)
