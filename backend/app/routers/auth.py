
from fastapi import APIRouter, HTTPException,Depends
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from fastapi.security import OAuth2PasswordRequestForm
from app.database import db
from app.schemas.user import UserRegister, UserLogin
from app.services.security import verify_password, create_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

# MongoDB users collection
users_collection = db["users"]

# Ensure email addresses are unique
users_collection.create_index("email", unique=True)


@router.post("/register", status_code=201)
def register_user(user: UserRegister):

    # Check if email already exists
    existing_user = users_collection.find_one({
        "email": user.email
    })

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = hash_password(user.password)

    # Prepare user document
    user_data = {
        "full_name": user.full_name,
        "email": user.email,
        "password": hashed_password,
        "role": "viewer",
        "created_at": datetime.now(timezone.utc)
    }

    try:
        result = users_collection.insert_one(user_data)

    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    return {
        "message": "User registered successfully",
        "user_id": str(result.inserted_id),
        "email": user.email,
        "role": "viewer"
    }




@router.post("/login")
def login_user(user: UserLogin):

    # Find user by email
    existing_user = users_collection.find_one({
        "email": user.email
    })

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Verify password
    password_valid = verify_password(
        user.password,
        existing_user["password"]
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Generate JWT token
    access_token = create_access_token({
        "sub": str(existing_user["_id"]),
        "role": existing_user["role"]
    })

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(existing_user["_id"]),
            "full_name": existing_user["full_name"],
            "email": existing_user["email"],
            "role": existing_user["role"]
        }
    }

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    existing_user = users_collection.find_one({
        "email": form_data.username
    })

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        form_data.password,
        existing_user["password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token({
        "sub": str(existing_user["_id"]),
        "role": existing_user["role"]
    })

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }