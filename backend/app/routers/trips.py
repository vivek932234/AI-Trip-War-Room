from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.database import db
from app.schemas.trip import TripCreate
from app.services.auth_service import get_current_user
from app.services.permissions import require_roles

router = APIRouter(prefix="/trips", tags=["Trips"])

trips_collection = db["trips"]


@router.post("/", status_code=201)
def create_trip(
    trip: TripCreate,
    current_user: dict = Depends(
        require_roles("planner", "leader", "admin")
    )
):
    if trip.end_date < trip.start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date"
        )

    trip_data = trip.model_dump()

    trip_data["start_date"] = trip_data["start_date"].isoformat()
    trip_data["end_date"] = trip_data["end_date"].isoformat()

    trip_data["created_by"] = current_user["id"]
    trip_data["created_at"] = datetime.now(timezone.utc)

    result = trips_collection.insert_one(trip_data)

    return {
        "message": "Trip created successfully",
        "trip_id": str(result.inserted_id),
        "title": trip.title,
        "destination": trip.destination,
        "created_by": current_user["full_name"]
    }