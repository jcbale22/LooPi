# --------------------------------------------------------------------------- #
#  content.py – Content dashboard routes for LooPi MVP                        #
#  • GET  /content/        -> Render the dashboard of uploaded media files   #
#  • POST /content/delete  -> Delete an image + its metadata                 #
#  • POST /content/update  -> Update start/end dates & playlists for a file  #
# --------------------------------------------------------------------------- #

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from datetime import datetime, date
from pathlib import Path
from fastapi.templating import Jinja2Templates
from app.utils.jinja_filters import datetimeformat

# --- Internal Services ---
from app.services.metadata_service import load_metadata, save_metadata
from app.services.playlist_service import load_playlists

# --- Context Utilities ---
from app.utils.context_helpers import inject_user_context

# --- FastAPI Config ---
router = APIRouter()
UPLOAD_DIR = Path("app/static/uploads")

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["datetimeformat"] = datetimeformat


# --------------------------------------------------------------------------- #
#  GET /content – Content Dashboard                                           #
# --------------------------------------------------------------------------- #
@router.get("/", response_class=HTMLResponse)
async def content_dashboard(request: Request, msg: str = "", err: str = ""):
    """
    Render the content dashboard with uploaded files and associated metadata.
    Adds 'is_expired' flag to each file and sorts active files above expired.
    """
    metadata = load_metadata()
    playlists = load_playlists()
    today = date.today()

    files = []
    for fname, data in metadata.items():
        # Determine if the file has expired based on its end date
        try:
            end = datetime.strptime(data.get("end", ""), "%Y-%m-%d").date()
            is_expired = end < today
        except Exception:
            is_expired = False  # Default to active if date parsing fails

        files.append({
            "filename": fname,
            "start": data.get("start", ""),
            "end": data.get("end", ""),
            "playlists": data.get("playlists", []),
            "is_expired": is_expired
        })

    # Sort files: Active (False) before Expired (True)
    files.sort(key=lambda f: f["is_expired"])

    return templates.TemplateResponse("content.html", inject_user_context(
        request,
        files=files,
        message=msg,
        error=err,
        playlists=playlists
    ))


# --------------------------------------------------------------------------- #
#  POST /content/delete – Remove a file + its metadata                        #
# --------------------------------------------------------------------------- #
@router.post("/delete")
async def delete_file(filename: str = Form(...)):
    """
    Deletes the physical image file and its metadata entry.
    """
    file_path = UPLOAD_DIR / filename

    if file_path.exists():
        file_path.unlink()

    metadata = load_metadata()
    metadata.pop(filename, None)
    save_metadata(metadata)

    return RedirectResponse(url="/content?msg=File+deleted", status_code=HTTP_302_FOUND)


# --------------------------------------------------------------------------- #
#  POST /content/update – Edit dates & playlists for an image                #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
#  POST /content/update – Edit dates & playlists for an image                #
# --------------------------------------------------------------------------- #
@router.post("/update")
async def update_file(request: Request):
    """
    Updates start/end dates and playlist associations for an uploaded file.
    Also syncs playlist membership by updating playlists.json.
    """
    form = await request.form()

    filename   = form.get("filename") or form.get("original_filename")
    start_date = form.get("start_date")
    end_date   = form.get("end_date")
    new_playlists = form.getlist("playlists")

    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename for update.")

    # --- Validate date formats ---
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end   = datetime.strptime(end_date, "%Y-%m-%d").date()
        if end < start:
            raise HTTPException(status_code=400, detail="End date cannot precede start date.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format: use YYYY-MM-DD.")

    # --- Update metadata ---
    metadata = load_metadata()
    if filename in metadata:
        metadata[filename]["start"]     = start_date
        metadata[filename]["end"]       = end_date
        metadata[filename]["playlists"] = new_playlists
        save_metadata(metadata)

    # --- Sync playlist membership in playlists.json ---
    from app.services.playlist_service import load_playlists, save_playlists
    playlists = load_playlists()

    # Remove image from all playlists it's currently in
    for name, pl in playlists.items():
        if filename in pl["images"]:
            pl["images"].remove(filename)

    # Add image to newly selected playlists
    for pl_name in new_playlists:
        if pl_name in playlists:
            if filename not in playlists[pl_name]["images"]:
                playlists[pl_name]["images"].append(filename)

    save_playlists(playlists)

    return RedirectResponse(url="/content?msg=File+updated+successfully", status_code=HTTP_302_FOUND)

    # --- Validate date formats ---
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        if end < start:
            raise HTTPException(status_code=400, detail="End date cannot precede start date.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format: use YYYY-MM-DD.")

    # --- Save updated metadata ---
    metadata = load_metadata()
    if filename in metadata:
        metadata[filename]["start"] = start_date
        metadata[filename]["end"] = end_date
        metadata[filename]["playlists"] = playlists
        save_metadata(metadata)

    return RedirectResponse(url="/content?msg=File+updated+successfully", status_code=HTTP_302_FOUND)
