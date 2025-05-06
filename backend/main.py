from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from models import Base
from database import engine
from routes.upload_routes import router as upload_router
from routes.category_routes import router as category_router
from routes.user_books_routes import router as user_books_router
from routes.banner_routes import router as banner_router
from routes.book_routes import router as book_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create all tables on startup
Base.metadata.create_all(bind=engine)

# Create the FastAPI app
app = FastAPI(
    title="Darati API",
    description="API for the Darati audiobook platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers with explicit prefixes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload_router, prefix="/api/audio", tags=["Upload"])
app.include_router(category_router, prefix="/api", tags=["Categories"])
app.include_router(user_books_router, prefix="/api", tags=["User Books"])
app.include_router(banner_router, prefix="/api/banners", tags=["Banners"])
app.include_router(book_router, prefix="/api/books", tags=["Books"])

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Darati API"}

@app.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

# Log all registered routes
@app.on_event("startup")
async def log_routes():
    logger.info("Registered routes:")
    for route in app.routes:
        logger.info(f"{route.methods} {route.path}")
