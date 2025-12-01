# app/routes/playlists.py

"""
Route: /playlists
Purpose: Playlist management interface (view, add, delete, update color, reorder images)
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
from typing import List

from app.services.playlist_service import (
    add_playlist,
    update_playlist_color,
    delete_playlist,
    backfill_playlists_from_metadata,
    get_playlist_images,
    set_playlist_images,
    remove_image_from_playlist,
    sync_playlists_to_state,
    get_assigned_devices_by_playlist,
    load_playlists
)
from app.services.metadata_service import load_metadata
from app.services.device_service import load_devices
from app.utils.context_helpers import inject_user_context

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

# === GET: Playlist Management Screen ===
@router.get("/", response_class=HTMLResponse)
async def view_playlists(request: Request):
    metadata = load_metadata()
    backfill_playlists_from_metadata(metadata)
    sync_playlists_to_state()  # Ensure app.state.playlists is current

    # Load devices and compute assigned devices
    devices = load_devices()
    assigned_devices = get_assigned_devices_by_playlist(devices)

    playlists = load_playlists()
    for pl_name in playlists:
        playlists[pl_name]["devices"] = assigned_devices.get(pl_name, [])

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

# === POST: Reorder Images in a Playlist (Drag and Drop) ===
@router.post("/reorder")
async def reorder_playlist(name: str = Form(...), order: str = Form(...)):
    try:
        image_list = [f.strip() for f in order.split(",") if f.strip()]
        set_playlist_images(name, image_list)
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)})

# === POST: Remove Image from Playlist ===
@router.post("/remove-image/{playlist}/{filename}")
async def remove_image(playlist: str, filename: str):
    try:
        remove_image_from_playlist(playlist, filename)
        return JSONResponse(content={"success": True})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)})
