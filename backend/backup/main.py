from fastapi import FastAPI
from auth import router as auth_router
from models import Base
from database import engine

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Create the FastAPI app
app = FastAPI()

# Include authentication routes
app.include_router(auth_router)
