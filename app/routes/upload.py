# app/routes/upload.py
"""
Route group: /upload
Purpose    : Handle media uploads + (MVP) playlist creation / assignment.
Updates:
  • When a file is uploaded, we ALSO append the filename to the
    playlists.json entry for each selected playlist, making the
    new accordion + drag-and-drop UI work.
"""

from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
from pathlib import Path
from typing import List
import shutil

# Internal services
from app.services.metadata_service import load_metadata, save_metadata
from app.services.playlist_service import load_playlists, save_playlists
from app.utils.context_helpers import inject_user_context

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ---------- Constants ---------------------------------------------------
UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ---------- GET: Render the upload form --------------------------------
@router.get("/upload", response_class=HTMLResponse)
async def upload(request: Request):
    """
    Render upload.html with the current playlist list.
    """
    playlists = load_playlists()
    return templates.TemplateResponse(
        "upload.html",
        inject_user_context(request, playlists=playlists)
    )

# ---------- POST: Handle an upload -------------------------------------
@router.post(
    "/upload",
    response_class=HTMLResponse,
    summary="Upload an image and assign playlists + dates",
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    playlists: List[str] = Form(default=[]),
    new_playlist: str = Form(default=None),
    new_color: str = Form(default=None),
):
    # 1️⃣ Validate date range ------------------------------------------------
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        if end < start:
            raise HTTPException(
                status_code=400, detail="End date must not precede start date."
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD).")

    # 2️⃣ Load playlists.json -------------------------------------------------
    all_playlists = load_playlists()

    # 3️⃣ Optionally create a new playlist from the form ----------------------
    if new_playlist:
        pname = new_playlist.strip()
        if pname and pname not in all_playlists:
            # Create entry in modern structure: {color, images, devices}
            all_playlists[pname] = {
                "color": new_color or "#cccccc",
                "images": [],
                "devices": [],
            }
            playlists.append(pname)  # auto-select the new playlist

    # 4️⃣ Persist uploaded file to /uploads ----------------------------------
    filepath = UPLOAD_DIR / file.filename
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 5️⃣ Update metadata.json (date + playlist tags only) -------------------
    metadata = load_metadata()
    metadata[file.filename] = {
        "start": start_date,
        "end": end_date,
        "playlists": playlists,
    }
    save_metadata(metadata)

    # 6️⃣ Back-fill playlists.json with the image ----------------------------
    for pl in playlists:
        entry = all_playlists.get(pl)

        # ▶ Legacy entry is just a color string
        if isinstance(entry, str):
            all_playlists[pl] = entry = {
                "color": entry,
                "images": [],
                "devices": [],
            }

        # Ensure keys exist
        entry.setdefault("images", [])
        entry.setdefault("devices", [])

        # Append filename if not already present
        if file.filename not in entry["images"]:
            entry["images"].append(file.filename)

    # Persist playlists.json after mutation
    save_playlists(all_playlists)

    # 7️⃣ Build pill data for the success page -------------------------------
    playlist_pills = [
        {"name": name, "color": all_playlists.get(name, {}).get("color", "#cccccc")}
        for name in playlists
    ]

    # 8️⃣ Render upload_success.html -----------------------------------------
    return templates.TemplateResponse(
        "upload_success.html",
        inject_user_context(
            request,
            filename=file.filename,
            start_date=start_date,
            end_date=end_date,
            playlist_pills=playlist_pills,
        ),
    )
