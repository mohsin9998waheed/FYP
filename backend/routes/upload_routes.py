from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Audiobook, Chapter
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from azure.storage.blob import BlobServiceClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create router
router = APIRouter()

# Initialize Azure Blob Service Client
connection_string = os.getenv("AZURE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME")

if not connection_string or not container_name:
    raise ValueError("Azure storage configuration is missing. Please check your .env file.")

logger.info("Initializing Azure Blob Service Client...")
try:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    logger.info(f"Connected to Azure container: {container_name}")
except Exception as e:
    logger.error(f"Failed to initialize Azure client: {str(e)}")
    raise

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", tags=["Audio Upload"])
async def upload_audio(
    title: str = Form(...),
    author: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    thumbnail: UploadFile = File(None),
    audio: UploadFile = File(...),
    existing_book_id: int = Form(None),  # Optional parameter for existing book
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"Starting upload process for title: {title}")
        logger.info(f"Audio file: {audio.filename}, Content-Type: {audio.content_type}")
        if thumbnail:
            logger.info(f"Thumbnail file: {thumbnail.filename}, Content-Type: {thumbnail.content_type}")

        # Validate required fields
        if not title or not author or not category_id:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: title, author, or category_id"
            )

        # Define file extensions based on MIME type
        mime_to_extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/ogg": ".ogg"
        }

        # Upload audio file
        audio_ext = mime_to_extension.get(audio.content_type, ".mp3")  # Default to .mp3 if unknown MIME type
        audio_blob_name = f"audiobooks/{datetime.now().timestamp()}_{audio.filename}"
        audio_blob_client = container_client.get_blob_client(audio_blob_name)

        # Read audio file content and upload
        audio_file_content = await audio.read()
        logger.info(f"Uploading audio file to Azure as {audio_blob_name}...")
        audio_blob_client.upload_blob(audio_file_content, overwrite=True)
        audio_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{audio_blob_name}"
        logger.info(f"Audio uploaded successfully. URL: {audio_url}")

        # Upload thumbnail (if present)
        thumbnail_url = None
        if thumbnail:
            thumbnail_ext = mime_to_extension.get(thumbnail.content_type, ".jpg")  # Default to .jpg
            thumbnail_blob_name = f"thumbnails/{datetime.now().timestamp()}_{thumbnail.filename}"
            thumbnail_blob_client = container_client.get_blob_client(thumbnail_blob_name)

            # Read thumbnail content and upload
            thumbnail_file_content = await thumbnail.read()
            logger.info(f"Uploading thumbnail file to Azure as {thumbnail_blob_name}...")
            thumbnail_blob_client.upload_blob(thumbnail_file_content, overwrite=True)
            thumbnail_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{thumbnail_blob_name}"
            logger.info(f"Thumbnail uploaded successfully. URL: {thumbnail_url}")

        if existing_book_id:
            # If existing book ID is provided, add a new chapter to the existing audiobook
            existing_book = db.query(Audiobook).filter(Audiobook.id == existing_book_id).first()
            if not existing_book:
                raise HTTPException(status_code=404, detail="Audiobook not found")

            chapter_count = db.query(Chapter).filter(Chapter.audiobook_id == existing_book_id).count()
            new_chapter = Chapter(
                audiobook_id=existing_book_id,
                title=f"{existing_book.title} - Chapter {chapter_count + 1}",
                audio_url=audio_url,
                thumbnail_url=thumbnail_url,  # Set chapter thumbnail (can be None)
                order=chapter_count + 1
            )
            db.add(new_chapter)
            db.commit()
            logger.info(f"New chapter added to existing book {existing_book_id}")
            return {"message": "Chapter added successfully", "chapter_id": new_chapter.id}

        # If no existing book, create a new audiobook
        new_book = Audiobook(
            title=title,
            author=author,
            description=description,
            category_id=category_id,
            creator_id=1,  # Static for now
            is_public=True,
            created_at=datetime.utcnow()
        )
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        logger.info(f"New audiobook created successfully: {new_book.id}")

        # Add first chapter to the newly created book
        first_chapter = Chapter(
            audiobook_id=new_book.id,
            title=f"{title} - Chapter 1",
            audio_url=audio_url,
            thumbnail_url=thumbnail_url,  # Set chapter thumbnail
            order=1
        )
        db.add(first_chapter)
        db.commit()
        logger.info(f"First chapter added to new audiobook {new_book.id}")

        return {
            "message": "Audiobook uploaded successfully",
            "book_id": new_book.id,
            "chapter_id": first_chapter.id
        }

    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error during upload: {str(e)}"
        )

@router.get("/user_books")
async def get_user_books(db: Session = Depends(get_db)):
    try:
        # For now, we'll get all books since we don't have user authentication yet
        books = db.query(Audiobook).all()
        return books
    except Exception as e:
        logger.error(f"Error fetching user books: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching user books: {str(e)}"
        )
