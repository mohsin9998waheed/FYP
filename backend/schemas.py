from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    full_name: str

class UserCreate(UserBase):
    password: str
    phone_number: Optional[str] = None
    role: str = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    is_verified: bool
    created_at: datetime
    role: str
    
    class Config:
        orm_mode = True
