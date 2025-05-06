from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from schemas import UserCreate, UserLogin
from passlib.context import CryptContext

router = APIRouter()

# 🔐 Create a password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ✅ Helper function to hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# ✅ Helper function to verify password during login
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 🧠 Get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ Signup route
@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_data = user.model_dump()
    user_data["password_hash"] = hash_password(user_data.pop("password"))  # 🔐 Securely hash password
    new_user = User(**user_data)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Signup successful"}

# ✅ Login route with password verification
# Login route
@router.post("/login")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {"message": "Login successful", "user_id": user.id, "name": user.full_name}
