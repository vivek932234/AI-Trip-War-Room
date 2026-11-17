from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.database import db
from app.schemas.trip import TripCreate, TripUpdate
from app.services.auth_service import get_current_user
from app.services.permissions import require_roles


from bson import ObjectId
from bson.errors import InvalidId

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

@router.get("/")
def get_all_trips(
    current_user: dict = Depends(get_current_user)
):
    # Find all trips where the user is a member
    memberships = db["trip_members"].find({
        "user_id": current_user["id"]
    })

    member_trip_ids = [
        membership["trip_id"]
        for membership in memberships
    ]

    # Retrieve trips created by the user OR shared with the user
    trips = list(
        trips_collection.find({
            "$or": [
                {"created_by": current_user["id"]},
                {"_id": {"$in": [
                    ObjectId(trip_id)
                    for trip_id in member_trip_ids
                ]}}
            ]
        })
    )

    for trip in trips:
        trip["id"] = str(trip["_id"])
        del trip["_id"]
        trip.pop("created_by", None)

    return {
        "message": "Trips retrieved successfully",
        "total_trips": len(trips),
        "trips": trips
    }

@router.get("/{trip_id}")
def get_trip_by_id(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    

    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    # Check whether the user created the trip
    is_creator = trips_collection.find_one({
        "_id": object_id,
        "created_by": current_user["id"]
    })

    # Check whether the user is an invited member
    is_member = db["trip_members"].find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if not is_creator and not is_member:
        raise HTTPException(
            status_code=404,
            detail="Trip not found or you do not have access"
        )

    trip = trips_collection.find_one({
        "_id": object_id
    })

    trip["id"] = str(trip["_id"])
    del trip["_id"]
    trip.pop("created_by", None)

    return {
        "message": "Trip retrieved successfully",
        "trip": trip
    }

@router.patch("/{trip_id}")
def update_trip(
    trip_id: str,
    trip_data: TripUpdate,
    current_user: dict = Depends(
        require_roles("planner", "leader", "admin")
    )
):

    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    existing_trip = trips_collection.find_one({
        "_id": object_id,
        "created_by": current_user["id"]
    })

    if not existing_trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    update_data = trip_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    start_date = update_data.get(
        "start_date", existing_trip["start_date"]
    )
    end_date = update_data.get(
        "end_date", existing_trip["end_date"]
    )

    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date"
        )

    for field in ["start_date", "end_date"]:
        if field in update_data:
            update_data[field] = update_data[field].isoformat()

    trips_collection.update_one(
        {"_id": object_id},
        {"$set": update_data}
    )

    return {
        "message": "Trip updated successfully",
        "trip_id": trip_id,
        "updated_fields": list(update_data.keys())
    }

@router.delete("/{trip_id}")
def delete_trip(
    trip_id: str,
    current_user: dict = Depends(
        require_roles("planner", "leader", "admin")
    )
):
    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    result = trips_collection.delete_one({
        "_id": object_id,
        "created_by": current_user["id"]
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    return {
        "message": "Trip deleted successfully",
        "trip_id": trip_id
    }