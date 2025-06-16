# app/services/file_service.py

from pathlib import Path
import shutil
import json
from typing import Dict
from datetime import datetime
from fastapi import UploadFile, HTTPException

from app.schemas.models import FileMetadata


# === Configuration Paths ===
UPLOADS_DIR = Path("static/uploads")
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

METADATA_PATH = Path("storage/metadata.json")
if not METADATA_PATH.exists():
    METADATA_PATH.write_text(json.dumps({}, indent=2))


# === Load all metadata entries from disk ===
def load_metadata() -> Dict[str, FileMetadata]:
    with open(METADATA_PATH, "r") as f:
        return json.load(f)


# === Save all metadata entries to disk ===
def save_metadata(metadata: Dict[str, FileMetadata]):
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)


# === Save uploaded image to disk ===
def save_uploaded_file(file: UploadFile) -> Path:
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Only PNG, JPG, and JPEG files are allowed.")
    
    destination = UPLOADS_DIR / file.filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return destination


# === Validate and parse dates from form ===
def validate_dates(start_date: str, end_date: str):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        if end < start:
            raise ValueError("End date must not be before start date.")
        return start, end
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Add or update a file's metadata ===
def update_file_metadata(filename: str, start: str, end: str, playlists: list[str]):
    metadata = load_metadata()
    metadata[filename] = {
        "start": start,
        "end": end,
        "playlists": playlists
    }
    save_metadata(metadata)


# === Delete image and associated metadata ===
def delete_file(filename: str):
    filepath = UPLOADS_DIR / filename
    if filepath.exists():
        filepath.unlink()
    
    metadata = load_metadata()
    if filename in metadata:
        del metadata[filename]
        save_metadata(metadata)
