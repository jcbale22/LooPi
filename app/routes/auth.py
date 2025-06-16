# app/routes/auth.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.utils.context_helpers import inject_user_context

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_view(request: Request):
    context = inject_user_context(request)
    return templates.TemplateResponse("profile.html", context)

@router.get("/login", include_in_schema=False)
async def login_placeholder():
    return {"message": "Login page coming soon."}

@router.get("/logout", include_in_schema=False)
async def logout_placeholder():
    return {"message": "Logout functionality coming soon."}

@router.get("/subscription", response_class=HTMLResponse)
async def subscription_view(request: Request):
    context = inject_user_context(request)
    return templates.TemplateResponse("subscription.html", context)
