# app/routes/upload.py

from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
from pathlib import Path
from typing import List
import shutil

from app.services.metadata_service import load_metadata, save_metadata
from app.services.playlist_service import load_playlists, save_playlists
from app.utils.context_helpers import inject_user_context

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# === Constants ===
UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# === GET: Upload Form ===
@router.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    """
    Render the upload form with current playlists.
    """
    playlists = load_playlists()
    return templates.TemplateResponse("upload.html", inject_user_context(
        request,
        playlists=playlists
    ))

# === POST: Handle Upload ===
@router.post("/upload", response_class=HTMLResponse, summary="Upload an image and assign playlists/dates")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    playlists: List[str] = Form(default=[]),
    new_playlist: str = Form(default=None),
    new_color: str = Form(default=None)
):
    # ✅ 1. Validate dates
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        if end < start:
            raise HTTPException(status_code=400, detail="End date must be after start date.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # ✅ 2. Add new playlist if supplied
    all_playlists = load_playlists()
    if new_playlist:
        sanitized = new_playlist.strip()
        if sanitized and sanitized not in all_playlists:
            all_playlists[sanitized] = new_color or "#cccccc"
            save_playlists(all_playlists)
            playlists.append(sanitized)

    # ✅ 3. Save uploaded file
    filepath = UPLOAD_DIR / file.filename
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ✅ 4. Update metadata.json
    metadata = load_metadata()
    metadata[file.filename] = {
        "start": start_date,
        "end": end_date,
        "playlists": playlists
    }
    save_metadata(metadata)

    # ✅ 5. Build playlist pill summary for UI
    playlist_pills = [
        {"name": name, "color": all_playlists.get(name, "#cccccc")}
        for name in playlists
    ]

    return templates.TemplateResponse("upload_success.html", inject_user_context(
        request,
        filename=file.filename,
        start_date=start_date,
        end_date=end_date,
        playlist_pills=playlist_pills
    ))
