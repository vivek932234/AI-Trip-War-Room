
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect
)
from typing import Dict, List
from jose import jwt, JWTError
from bson import ObjectId
from bson.errors import InvalidId

from app.database import db
from app.services.security import settings


router = APIRouter(tags=["Real-Time Collaboration"])

trips_collection = db["trips"]
members_collection = db["trip_members"]
users_collection = db["users"]


class ConnectionManager:

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, trip_id: str, websocket: WebSocket):
        await websocket.accept()

        self.active_connections.setdefault(trip_id, []).append(websocket)

    def disconnect(self, trip_id: str, websocket: WebSocket):
        connections = self.active_connections.get(trip_id, [])

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            self.active_connections.pop(trip_id, None)

    async def broadcast(self, trip_id: str, message: dict):
        connections = self.active_connections.get(trip_id, [])

        for connection in connections.copy():
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(trip_id, connection)


manager = ConnectionManager()


def authenticate_websocket(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id or not ObjectId.is_valid(user_id):
            return None

        user = users_collection.find_one({
            "_id": ObjectId(user_id)
        })

        if not user:
            return None

        user["id"] = str(user["_id"])

        return user

    except (JWTError, InvalidId):
        return None


def has_trip_access(trip_id: str, user: dict):

    try:
        trip_object_id = ObjectId(trip_id)
    except InvalidId:
        return False

    trip = trips_collection.find_one({
        "_id": trip_object_id
    })

    if not trip:
        return False

    is_creator = trip.get("created_by") == user["id"]

    is_member = members_collection.find_one({
        "trip_id": trip_id,
        "user_id": user["id"]
    })

    return is_creator or is_member is not None


@router.websocket("/ws/trips/{trip_id}")
async def trip_websocket(websocket: WebSocket, trip_id: str):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    current_user = authenticate_websocket(token)

    if not current_user:
        await websocket.close(code=1008, reason="Invalid token")
        return

    if not has_trip_access(trip_id, current_user):
        await websocket.close(code=1008, reason="Trip access denied")
        return

    await manager.connect(trip_id, websocket)

    try:
        await manager.broadcast(trip_id, {
            "event": "user_connected",
            "user": current_user["full_name"],
            "message": "A user joined the trip"
        })

        while True:
            data = await websocket.receive_json()

            await manager.broadcast(trip_id, {
                "event": "new_message",
                "trip_id": trip_id,
                "user": current_user["full_name"],
                "data": data
            })

    except WebSocketDisconnect:
        manager.disconnect(trip_id, websocket)

        await manager.broadcast(trip_id, {
            "event": "user_disconnected",
            "user": current_user["full_name"],
            "message": "A user left the trip"
        })
