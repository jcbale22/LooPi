# --------------------------------------------------------------------------- #
#  admin.py – Admin dashboard routes for LooPi MVP                            #
#  • GET  /admin/        -> Render the HTML dashboard of uploaded files       #
#  • GET  /              -> Redirect root to /admin                           #
#  • POST /admin/delete  -> Delete an image + its metadata                    #
#  • POST /admin/update  -> Update start/end dates & playlists for a file     #
# --------------------------------------------------------------------------- #

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from datetime import datetime
from pathlib import Path

# --- Internal Services ---
from app.services.metadata_service import load_metadata, save_metadata
from app.services.playlist_service import load_playlists

# --- Context Utilities ---
from app.utils.context_helpers import inject_user_context  # ✅ NEW

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = Path("app/static/uploads")

# --------------------------------------------------------------------------- #
#  GET  /admin – Admin dashboard                                              #
# --------------------------------------------------------------------------- #
@router.get("/", response_class=HTMLResponse)
async def admin_panel(request: Request, msg: str = "", err: str = ""):
    """Render the admin dashboard showing all uploaded files & metadata."""
    metadata = load_metadata()

    files = [
        {
            "filename": fname,
            "start": data.get("start", ""),
            "end": data.get("end", ""),
            "playlists": data.get("playlists", [])
        }
        for fname, data in metadata.items()
    ]

    return templates.TemplateResponse("admin.html", inject_user_context(
        request,
        files=files,
        message=msg,
        error=err,
        playlists=load_playlists()
    ))  # ✅ UPDATED TO USE CONTEXT HELPER


# --------------------------------------------------------------------------- #
#  POST /admin/delete – Remove a file + its metadata                          #
# --------------------------------------------------------------------------- #
@router.post("/delete")
async def delete_file(filename: str = Form(...)):
    """Deletes the physical image file and removes its metadata entry."""
    file_path = UPLOAD_DIR / filename

    if file_path.exists():
        file_path.unlink()

    metadata = load_metadata()
    metadata.pop(filename, None)
    save_metadata(metadata)

    return RedirectResponse(url="/admin?msg=File+deleted", status_code=HTTP_302_FOUND)


# --------------------------------------------------------------------------- #
#  POST /admin/update – Edit dates & playlists for an image                   #
# --------------------------------------------------------------------------- #
@router.post("/update")
async def update_file(request: Request):
    """Updates start/end dates and playlist assignments for a single file."""
    form = await request.form()

    filename   = form.get("filename")
    start_date = form.get("start_date")
    end_date   = form.get("end_date")
    playlists  = form.getlist("playlists")

    # --- Validate dates ---
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end   = datetime.strptime(end_date,   "%Y-%m-%d").date()
        if end < start:
            raise HTTPException(status_code=400, detail="End date cannot precede start date.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format: use YYYY-MM-DD.")

    # --- Save changes ---
    metadata = load_metadata()
    if filename in metadata:
        metadata[filename]["start"]     = start_date
        metadata[filename]["end"]       = end_date
        metadata[filename]["playlists"] = playlists
        save_metadata(metadata)

    return RedirectResponse(url="/admin?msg=File+updated+successfully", status_code=HTTP_302_FOUND)
