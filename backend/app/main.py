
from fastapi import FastAPI
from app.database import client, db
from app.routers.auth import router as auth_router
from fastapi import Depends
from app.services.auth_service import get_current_user
from app.services.permissions import require_roles
from app.routers.trips import router as trips_router
from app.routers.members import router as members_router
from app.routers.itinerary import router as itinerary_router
from app.routers.websocket import router as websocket_router
from app.routers.ai_concierge import router as ai_concierge_router

app = FastAPI(
    title="Airbnb AI Trip War Room",
    description="Collaborative AI-powered trip planning platform",
    version="1.0.0"
)
app.include_router(auth_router)
app.include_router(trips_router)
app.include_router(members_router)
app.include_router(itinerary_router)
app.include_router(websocket_router)
app.include_router(ai_concierge_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to Airbnb AI Trip War Room",
        "status": "Backend is running"
    }


@app.get("/health")
def health():
    try:
        client.admin.command("ping")

        return {
            "status": "healthy",
            "database": "connected",
            "database_name": db.name
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/users/me")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Authenticated successfully",
        "user": {
            "id": current_user["id"],
            "full_name": current_user["full_name"],
            "email": current_user["email"],
            "role": current_user["role"]
        }
    }

@app.get("/planner/dashboard")
def planner_dashboard(
    current_user: dict = Depends(
        require_roles("planner", "leader", "admin")
    )
):
    return {
        "message": "Welcome to the Planner Dashboard",
        "user": current_user["full_name"],
        "role": current_user["role"]
    }

@app.get("/viewer/dashboard")
def viewer_dashboard(
    current_user: dict = Depends(
        require_roles("viewer", "planner", "leader", "admin")
    )
):
    return {
        "message": "Welcome to the Trip Dashboard",
        "user": current_user["full_name"],
        "role": current_user["role"]
    }