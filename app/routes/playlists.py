# app/routes/playlists.py

"""
Route: /playlists
Purpose: Playlist management interface (view, add, delete, update color)
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND

from app.services.playlist_service import (
    load_playlists,
    save_playlists,
    add_playlist,
    update_playlist_color,
    delete_playlist,
    backfill_playlists_from_metadata
)
from app.services.metadata_service import load_metadata
from app.utils.context_helpers import inject_user_context  # ✅ For user nav context

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

# === GET: Playlist Management Screen ===
@router.get("/", response_class=HTMLResponse)
async def view_playlists(request: Request):
    metadata = load_metadata()
    backfill_playlists_from_metadata(metadata)
    playlists = load_playlists()

    return templates.TemplateResponse("playlists.html", inject_user_context(
        request,
        playlists=playlists,
        message=request.query_params.get("msg"),
        error=request.query_params.get("err")
    ))

# === POST: Add a New Playlist ===
@router.post("/add")
async def add_new_playlist(name: str = Form(...), color: str = Form(...)):
    try:
        add_playlist(name, color)
        return RedirectResponse(url="/playlists?msg=Playlist+added", status_code=HTTP_302_FOUND)
    except Exception as e:
        return RedirectResponse(url=f"/playlists?err=Failed+to+add:+{str(e)}", status_code=HTTP_302_FOUND)

# === POST: Update the Color of an Existing Playlist ===
@router.post("/update")
async def update_existing_playlist(name: str = Form(...), color: str = Form(...)):
    playlists = load_playlists()
    if name in playlists:
        update_playlist_color(name, color)
    return RedirectResponse(url="/playlists?msg=Playlist+updated", status_code=HTTP_302_FOUND)

# === POST: Delete a Playlist ===
@router.post("/delete")
async def delete_existing_playlist(name: str = Form(...)):
    try:
        delete_playlist(name)
        return RedirectResponse(url="/playlists?msg=Playlist+deleted", status_code=HTTP_302_FOUND)
    except Exception as e:
        return RedirectResponse(url=f"/playlists?err=Failed+to+delete:+{str(e)}", status_code=HTTP_302_FOUND)
