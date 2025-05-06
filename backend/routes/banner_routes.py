from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from database import get_db
from models import Banner
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create router
router = APIRouter()

# Initialize Azure Blob Service Client
connection_string = os.getenv("AZURE_CONNECTION_STRING")
container_name = os.getenv("AZURE_CONTAINER_NAME")
account_name = os.getenv("AZURE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_ACCOUNT_KEY")

if not all([connection_string, container_name, account_name, account_key]):
    raise ValueError("Azure storage configuration is missing. Please check your .env file.")

logger.info("Initializing Azure Blob Service Client...")
try:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    logger.info(f"Connected to Azure container: {container_name}")
except Exception as e:
    logger.error(f"Failed to initialize Azure client: {str(e)}")
    raise

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
        if 'thumb_' in blob_name or 'thumbnails' in blob_name:
            # This is a thumbnail image
            if not blob_name.startswith('audiobooks/'):
                blob_name = f'audiobooks/{blob_name}'
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

@router.post("/upload", tags=["Banners"])
async def upload_banner(
    banner: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Starting banner upload process for user: {user_id}")
        logger.info(f"Banner file: {banner.filename}, Content-Type: {banner.content_type}")

        # Define file extensions based on MIME type
        mime_to_extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp"
        }

        # Upload banner file
        banner_ext = mime_to_extension.get(banner.content_type, ".jpg")
        banner_blob_name = f"banners/{datetime.now().timestamp()}_{banner.filename}"
        banner_blob_client = container_client.get_blob_client(banner_blob_name)

        # Read banner file content and upload
        banner_file_content = await banner.read()
        logger.info(f"Uploading banner file to Azure as {banner_blob_name}...")
        banner_blob_client.upload_blob(banner_file_content, overwrite=True)
        
        # Generate SAS URL for the banner
        banner_url = generate_sas_url(banner_blob_name)
        logger.info(f"Banner uploaded successfully. URL with SAS: {banner_url}")

        # Create banner record in database
        new_banner = Banner(
            image_url=banner_url,
            uploader_id=user_id
        )
        
        db.add(new_banner)
        db.commit()
        db.refresh(new_banner)
        
        logger.info(f"Banner record created successfully. ID: {new_banner.id}")
        return {
            "message": "Banner uploaded successfully",
            "banner_id": new_banner.id,
            "banner_url": banner_url
        }
        
    except Exception as e:
        logger.error(f"Error uploading banner: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading banner: {str(e)}"
        )

@router.get("/list", tags=["Banners"])
async def list_banners(db: Session = Depends(get_db)):
    try:
        # Get all banners ordered by creation date
        banners = db.query(Banner).order_by(Banner.created_at.desc()).all()
        formatted_banners = []
        
        # Generate SAS URLs for each banner
        for banner in banners:
            try:
                if banner.image_url:
                    # Extract the blob name from the URL
                    if 'blob.core.windows.net' in banner.image_url:
                        blob_name = banner.image_url.split(container_name + '/')[1].split('?')[0]
                        # Generate SAS URL
                        sas_token = generate_blob_sas(
                            account_name=account_name,
                            container_name=container_name,
                            blob_name=blob_name,
                            account_key=account_key,
                            permission=BlobSasPermissions(read=True),
                            expiry=datetime.utcnow() + timedelta(hours=24)
                        )
                        sas_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
                        formatted_banners.append({
                            "id": banner.id,
                            "image_url": sas_url,
                            "created_at": banner.created_at
                        })
            except Exception as e:
                logger.error(f"Error processing banner {banner.id}: {str(e)}")
                continue
                
        logger.info(f"Successfully formatted {len(formatted_banners)} banners")
        return formatted_banners
    except Exception as e:
        logger.error(f"Error fetching banners: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching banners: {str(e)}"
        )
