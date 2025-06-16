# --- FastAPI App Bootstrapper for LooPi MVP ---

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.routes import auth
from app.routes import home

# --- Import modular route files ---
from app.routes import upload, display, admin, playlists

# --- Create FastAPI instance ---
app = FastAPI(title="LooPi MVP")

# --- CORS Middleware (optional for frontend dev) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount static directories ---
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/uploads", StaticFiles(directory="app/static/uploads"), name="uploads")

# --- Jinja2 templates directory (optional but common) ---
templates = Jinja2Templates(directory="app/templates")

# --- Register routers ---
app.include_router(home.router, tags=["Home"])
app.include_router(upload.router, tags=["Upload"])
app.include_router(display.router, tags=["Display"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(playlists.router, prefix="/playlists", tags=["Playlists"])
app.include_router(auth.router, tags=["Auth"])



# --- Redirect bare "/" to admin dashboard ---
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/admin")
