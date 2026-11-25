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



@router.get("/{trip_id}/my-role")
def get_my_trip_role(
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

    trip = trips_collection.find_one({
        "_id": object_id
    })

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    # Trip creator is treated as leader
    if trip["created_by"] == current_user["id"]:
        return {
            "trip_id": trip_id,
            "role": "leader",
            "can_edit": True
        }

    # Find the user's membership
    member = db["trip_members"].find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if not member:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this trip"
        )

    role = member.get("role", "viewer")

    return {
        "trip_id": trip_id,
        "role": role,
        "can_edit": role in ["planner", "leader"]
    }

@router.patch("/{trip_id}")
def update_trip(
    trip_id: str,
    trip_data: TripUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    # Find the trip
    existing_trip = trips_collection.find_one({
        "_id": object_id
    })

    if not existing_trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    # Only the Trip Leader (creator) can update trip details
    if existing_trip["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the Trip Leader can update trip details"
        )

    update_data = trip_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # Validate date changes
    start_date = update_data.get(
        "start_date",
        existing_trip["start_date"]
    )

    end_date = update_data.get(
        "end_date",
        existing_trip["end_date"]
    )

    # Convert stored ISO strings to date objects
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date).date()

    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date).date()

    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date"
        )

    # Convert updated dates into ISO strings for MongoDB

    # Validate existing itinerary activities against new trip dates
    new_start_date = start_date.isoformat()
    new_end_date = end_date.isoformat()

    conflicting_activities = db["itineraries"].find_one({
        "trip_id": trip_id,
        "$or": [
            {"activity_date": {"$lt": new_start_date}},
            {"activity_date": {"$gt": new_end_date}}
        ]
    })

    if conflicting_activities:
        raise HTTPException(
            status_code=400,
            detail=(
                "Trip dates cannot be changed because "
                "existing itinerary activities fall "
                "outside the new trip dates. "
                "Please update those activities first."
            )
        )

    # Convert updated dates into ISO strings for MongoDB
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
    current_user: dict = Depends(get_current_user)
):
    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    # Check whether the trip exists
    existing_trip = trips_collection.find_one({
        "_id": object_id
    })

    if not existing_trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    # Only the Trip Leader who created the trip can delete it
    if existing_trip["created_by"] != current_user["id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the Trip Leader can delete this trip"
        )

    trips_collection.delete_one({
        "_id": object_id
    })

    return {
        "message": "Trip deleted successfully",
        "trip_id": trip_id
    }
