from pydantic import BaseModel, EmailStr


class AddMember(BaseModel):
    email: EmailStr
    role: str = "viewer"