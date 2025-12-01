from fastapi import APIRouter, Request, Form, UploadFile, File, Depends
from fastapi.responses import RedirectResponse
from models.user import User  # Adjust if needed
from services.auth import get_current_user
from services.db import update_user_preferences  # Assumes a utility for prefs

router = APIRouter()

@router.get("/profile")
async def profile(request: Request, user: User = Depends(get_current_user)):
    return request.app.templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "message": request.session.pop("message", None),
        "error": request.session.pop("error", None),
    })

@router.post("/profile/time-settings")
async def update_time_settings(
    request: Request,
    time_format: str = Form(...),
    timezone: str = Form(...),
    user: User = Depends(get_current_user)
):
    try:
        update_user_preferences(user, time_format, timezone)
        request.session["message"] = "Preferences updated."
    except Exception as e:
        request.session["error"] = f"Error updating preferences: {e}"
    return RedirectResponse("/profile", status_code=303)

@router.post("/profile/update-email")
async def update_email(
    request: Request,
    email: str = Form(...),
    user: User = Depends(get_current_user)
):
    try:
        # Stub – replace with actual DB call when ready
        user.email = email
        request.session["message"] = "Email updated successfully."
    except Exception as e:
        request.session["error"] = f"Error updating email: {e}"
    return RedirectResponse("/profile", status_code=303)

@router.post("/profile/avatar-upload")
async def avatar_upload(
    request: Request,
    avatar: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    try:
        # Stub – process the avatar file, store it, and update user.avatar_url
        request.session["message"] = "Avatar uploaded."
    except Exception as e:
        request.session["error"] = f"Avatar upload failed: {e}"
    return RedirectResponse("/profile", status_code=303)
