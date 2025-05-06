from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Audiobook, User
from database import get_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/user_books")
def get_books_by_user(
    db: Session = Depends(get_db),
    user_id: int = None,  # This will be passed from the frontend
    is_admin: bool = False  # This will be passed from the frontend
):
    try:
        # If user is admin, return all books
        if is_admin:
            books = db.query(Audiobook).all()
            logger.info(f"Admin access - Found {len(books)} total books.")
            return books
            
        # For regular users, return only their books
        if user_id:
            books = db.query(Audiobook).filter(Audiobook.creator_id == user_id).all()
            logger.info(f"User {user_id} - Found {len(books)} books.")
            return books
            
        # If no user_id provided, return empty list
        logger.info("No user_id provided, returning empty list.")
        return []
        
    except Exception as e:
        logger.error(f"Error fetching books: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching books: {str(e)}"
        )
