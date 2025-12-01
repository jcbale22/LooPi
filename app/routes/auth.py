# app/routes/auth.py

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.utils.context_helpers import inject_user_context

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_view(request: Request):
    context = inject_user_context(request)
    return templates.TemplateResponse("profile.html", context)

@router.post("/profile/time-settings")
async def update_time_settings(
    request: Request,
    time_format: str = Form(...),
    timezone: str = Form(...)
):
    # Save time preferences using cookies
    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie("loopi_time_format", time_format, max_age=60*60*24*365)
    response.set_cookie("loopi_timezone", timezone, max_age=60*60*24*365)
    return response

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
