from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.database import db
from app.schemas.member import AddMember
from app.services.auth_service import get_current_user
from app.services.permissions import require_roles


from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter(prefix="/trips", tags=["Trip Members"])

trips_collection = db["trips"]
users_collection = db["users"]


@router.post("/{trip_id}/members")
def add_member(
    trip_id: str,
    member: AddMember,
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

    trip = trips_collection.find_one({
        "_id": object_id,
        "created_by": current_user["id"]
    })

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found or you are not the creator"
        )

    new_user = users_collection.find_one({
        "email": member.email
    })

    if not new_user:
        raise HTTPException(
            status_code=404,
            detail="User is not registered"
        )

    if member.role not in ["viewer", "planner"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid member role"
        )

    if new_user["role"] == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin cannot be added as a trip member"
        )

    if new_user["_id"] == current_user.get("_id"):
        raise HTTPException(
            status_code=400,
            detail="You are already the trip creator"
        )

    existing_member = db["trip_members"].find_one({
        "trip_id": trip_id,
        "user_id": str(new_user["_id"])
    })

    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="User is already a trip member"
        )

    db["trip_members"].insert_one({
        "trip_id": trip_id,
        "user_id": str(new_user["_id"]),
        "email": new_user["email"],
        "role": member.role,
        "added_by": current_user["id"],
        "added_at": datetime.now(timezone.utc)
    })

    return {
        "message": "Member added successfully",
        "trip_id": trip_id,
        "member_email": new_user["email"],
        "role": member.role
    }