from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from bson import ObjectId

from app.database import db
from app.services.security import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

users_collection = db["users"]


def get_current_user(token: str = Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id or not ObjectId.is_valid(user_id):
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if user is None:
        raise credentials_exception

    user["id"] = str(user["_id"])
    return user