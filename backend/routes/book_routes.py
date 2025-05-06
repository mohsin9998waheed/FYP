from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Audiobook, Chapter
import logging
from datetime import datetime, timedelta
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

router = APIRouter()

# Get Azure credentials
account_name = os.getenv("AZURE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_CONTAINER_NAME")

def generate_sas_url(blob_name: str) -> str:
    """Generate a SAS URL for a blob that expires in 24 hours"""
    if not blob_name:
        return None
    try:
        # Extract blob name if it's a full URL
        if 'blob.core.windows.net' in blob_name:
            # Split by container name to get the path after it
            parts = blob_name.split(container_name + '/')
            if len(parts) > 1:
                blob_name = parts[1].split('?')[0]  # Remove any existing query parameters
            else:
                # If we can't find the container name, just take the last part
                blob_name = blob_name.split('/')[-1].split('?')[0]
        
        # Replace backslashes with forward slashes
        blob_name = blob_name.replace('\\', '/')
        
        # Handle different types of blob paths
        if 'thumb_' in blob_name:
            # This is a thumbnail image
            # Extract just the filename and put it in audiobooks directory
            filename = blob_name.split('/')[-1]  # Get just the filename
            blob_name = f'audiobooks/{filename}'
            logger.info(f"Processed thumbnail path: {blob_name}")
        elif 'audio_' in blob_name:
            # This is an audio file
            if not blob_name.startswith('audiobooks/'):
                blob_name = f'audiobooks/{blob_name}'
        elif 'banner' in blob_name:
            # This is a banner
            if not blob_name.startswith('banners/'):
                blob_name = f'banners/{blob_name}'
            
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=24)
        )
        
        # Ensure the URL is properly formatted
        url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        logger.info(f"Generated SAS URL for blob: {blob_name}")
        return url
    except Exception as e:
        logger.error(f"Error generating SAS URL for {blob_name}: {str(e)}")
        return None

@router.get("/all", tags=["Books"])
async def get_all_books(db: Session = Depends(get_db)):
    try:
        # Fetch all books with their first chapters
        books = db.query(Audiobook).all()
        logger.info(f"Found {len(books)} books in database")
        
        # Format the response
        formatted_books = []
        for book in books:
            try:
                # Get the first chapter for this book
                first_chapter = db.query(Chapter).filter(
                    Chapter.audiobook_id == book.id,
                    Chapter.order == 1
                ).first()
                
                # Generate SAS URLs for the stored blob paths
                cover_image_url = generate_sas_url(book.cover_image_url) if book.cover_image_url else None
                first_chapter_url = generate_sas_url(first_chapter.audio_url) if first_chapter and first_chapter.audio_url else None
                
                formatted_books.append({
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "description": book.description,
                    "cover_image_url": cover_image_url,  # Use SAS URL
                    "created_at": book.created_at,
                    "first_chapter_url": first_chapter_url,  # Use SAS URL
                    "total_chapters": len(book.chapters) if book.chapters else 0
                })
            except Exception as e:
                logger.error(f"Error processing book {book.id}: {str(e)}")
                continue
        
        logger.info(f"Successfully formatted {len(formatted_books)} books")
        return formatted_books
        
    except Exception as e:
        logger.error(f"Error fetching books: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching books: {str(e)}"
        ) 
