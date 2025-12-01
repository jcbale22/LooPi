# --- FastAPI App Bootstrapper for LooPi MVP ---

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import datetime
from pathlib import Path

from app.utils.jinja_filters import datetimeformat
from app.routes import auth, content, home, upload, playlists, display, ui, media
from app.routes.devices import router as devices_router
from app.services.playlist_service import load_playlists

# --- Create FastAPI instance ---
app = FastAPI(title="LooPi MVP")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Base & Static Paths ---
# Ensure we're mounting static from the root project folder (not /app)
BASE_DIR = Path(__file__).resolve().parent.parent  # /LooPi
STATIC_DIR = BASE_DIR / "app" / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"

# --- Mount static asset folders ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# --- Jinja2 Templates with Custom Filters ---
templates = Jinja2Templates(directory="app/templates")

def datetimeformat(value, format="%m/%d/%Y"):
    if not value:
        return ""
    try:
        if isinstance(value, datetime):
            return value.strftime(format)
        if isinstance(value, str):
            return datetime.fromisoformat(value).strftime(format)
        return str(value)  # Fallback
    except Exception as e:
        return f"Invalid date"


# Register filter to Jinja2
templates.env.filters["datetimeformat"] = datetimeformat
app.templates = templates  # Make available globally

# --- Register Routers ---
app.include_router(home.router, tags=["Home"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(display.router, tags=["Display"])
app.include_router(content.router, prefix="/content", tags=["Content"])
app.include_router(playlists.router, prefix="/playlists", tags=["Playlists"])
app.include_router(auth.router, tags=["Auth"])
app.include_router(devices_router, tags=["Devices"])
app.include_router(media.router, tags=["Media"])


# --- Root Redirect ---
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/content")

# --- Startup Playlist Loader ---
@app.on_event("startup")
def load_playlists_into_state():
    app.state.playlists = load_playlists()