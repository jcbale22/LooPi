# --------------------------------------------------------------------------- #
#  display.py – Render fullscreen rotating slideshow of active graphics       #
#  • GET /display         → View all currently active images                  #
# --------------------------------------------------------------------------- #

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.services.metadata_service import load_metadata
from app.utils.context_helpers import inject_user_context  # ✅ Include user context

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# --------------------------------------------------------------------------- #
#  GET /display – Loop graphics based on start/end date in metadata           #
# --------------------------------------------------------------------------- #
@router.get("/display", response_class=HTMLResponse)
async def display_viewer(request: Request):
    """
    Shows all currently active images (based on date range in metadata).
    Used for fullscreen slideshow displays.
    """
    metadata = load_metadata()
    today = datetime.today().date()

    active_images = []

    for filename, meta in metadata.items():
        try:
            start = datetime.strptime(meta["start"], "%Y-%m-%d").date()
            end   = datetime.strptime(meta["end"], "%Y-%m-%d").date()

            # If file is active today, include it
            if start <= today <= end:
                active_images.append(filename)

        except Exception as e:
            print(f"[WARN] Error parsing date for {filename}: {e}")

    if not active_images:
        active_images = ["default.png"]

    return templates.TemplateResponse("display.html", inject_user_context(
        request,
        images=active_images
    ))
