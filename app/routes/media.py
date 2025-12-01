from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services import media_service, metadata_service
from uuid import uuid4

router = APIRouter()

@router.post("/media/upload")
async def upload_media(file: UploadFile = File(...)):
    # Generate unique key for Cloudflare R2
    key = f"{uuid4()}_{file.filename}"

    try:
        # Upload to R2
        await media_service.upload_media_to_r2(file.file, key)

        # Save metadata to DB
        await metadata_service.save_media_metadata(
            filename=file.filename,
            r2_key=key,
            content_type=file.content_type,
            size=file.spool_max_size  # Replace with actual size if available
        )

        return {"message": "Upload successful", "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))